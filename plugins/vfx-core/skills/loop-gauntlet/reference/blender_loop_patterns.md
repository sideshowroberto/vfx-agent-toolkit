# Blender patterns for the loop

Distilled from the first run (Blender 5.1, official Blender MCP, live
session). All snippets are bpy, ASCII, raw-string paths, and assume the
working folder and view list come from the spec.

## 1. Non-blocking render queue on a timer

An MCP execute call that renders six views inline exceeds the tool timeout
and leaves the session in an unknown state. Register a timer that renders
one camera per tick and writes a status JSON the caller polls.

```python
import bpy, json, time, traceback
from pathlib import Path

ROOT = Path(r"D:/work/my_loop")          # from the spec
VIEWS = ["hero", "detail"]               # from the spec
TAG = globals().get("RENDER_TAG", "iter01")
ENGINE = globals().get("RENDER_ENGINE", "BLENDER_EEVEE")
SIZE = (1376, 768)

prev = bpy.app.driver_namespace.get("LOOP_RENDER_JOB")
if prev and prev["state"] == "running":
    raise RuntimeError("a render job is already running; inspect before resubmitting")
job = {"tag": TAG, "engine": ENGINE, "state": "running", "index": 0, "completed": [], "started": time.time()}
bpy.app.driver_namespace["LOOP_RENDER_JOB"] = job
status = ROOT / "renders" / (TAG + "_status.json")

def write_status():
    status.write_text(json.dumps(job, indent=2), encoding="ascii")

def step():
    try:
        s = bpy.context.scene
        if job["index"] >= len(VIEWS):
            job["state"] = "complete"; job["elapsed"] = time.time() - job["started"]; write_status(); return None
        view = VIEWS[job["index"]]
        out = ROOT / "renders" / (TAG + "_" + view + ".png")
        if out.exists():
            raise RuntimeError("output already exists: " + str(out))   # never overwrite evidence
        s.camera = bpy.data.objects["CAM_" + view]
        s.render.engine = ENGINE
        s.render.resolution_x, s.render.resolution_y = SIZE
        s.render.resolution_percentage = 100
        if ENGINE == "CYCLES":
            s.cycles.samples = 256; s.cycles.use_denoising = True
        s.render.filepath = str(out)
        bpy.ops.wm.save_mainfile(incremental=True)      # increment BEFORE the render
        t0 = time.time(); bpy.ops.render.render(write_still=True)
        st = out.stat()
        job["completed"].append({"view": view, "path": str(out), "bytes": st.st_size, "modified": st.st_mtime, "seconds": time.time() - t0})
        job["index"] += 1; write_status()
        return 1.0
    except Exception:
        job["state"] = "failed"; job["error"] = traceback.format_exc(); write_status(); return None

write_status()
bpy.app.timers.register(step, first_interval=1.0)
```

Poll `renders/<tag>_status.json` until `state` is `complete` or `failed`.
The `output already exists` guard is deliberate: a re-run must get a new
tag, so no iteration's evidence is overwritten.

## 2. Generated image pixels that vanish

Symptom: a relief or bump texture renders flat black; the loop scored it
as "band missing" for three iterations. Cause: assigning `colorspace_settings`
AFTER writing `image.pixels` cleared the data, and an unpacked generated
image does not survive save/reopen.

```python
img = bpy.data.images.new("TEX_relief", w, h, alpha=False, float_buffer=False)
img.colorspace_settings.name = "Non-Color"    # BEFORE pixels
img.pixels.foreach_set(flat_rgba)
img.pack()
# verify after save: reopen the file, then
px = bpy.data.images["TEX_relief"].pixels
assert any(px[i] for i in range(0, len(px), 997)), "texture is all zero"
```

Read the pixels back after the save, not after the assignment.

## 3. Scene hygiene the loop depends on

- Read state before creating: `bpy.data.objects.get(name)` then update, never
  `bpy.ops.mesh.primitive_*` again for an object that exists.
- One collection per zone plus CAMERAS and LIGHTS; every object named
  `<ZONE>_<thing>` so a listing reads as a plan.
- Cameras `CAM_<view>` with sensor width fixed (36 mm) so the focal length
  in the log means one thing.
- Verification the first run used at the end: no default names
  (`Cube`, `Camera`, `Light`), no `.001` suffixes, a ray cast along each
  circulation route at head height to prove the zones connect, and a
  reopen of the saved file in the same session to prove packed data
  survived.

## 4. Engines

EEVEE for every loop render (seconds per view). Cycles only for the final
labelled pass, and expect it to change lighting: the first run's corridor
shafts largely disappeared under Cycles. That is a finding, not a polish.
