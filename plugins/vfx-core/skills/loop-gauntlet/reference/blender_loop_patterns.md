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

def verify_scene():
    """The iteration's geometry read-back. Return a list of fault strings (empty = pass).
    Fill it from the spec: routes connect, zone volumes inside tolerance, nothing below
    the floor, every object the plan names exists. Left unwritten it raises, on purpose:
    a gate that cannot fail is not a gate."""
    raise NotImplementedError("write the geometry read-back for this build before queuing renders")

def step():
    try:
        s = bpy.context.scene
        if job["index"] >= len(VIEWS):
            job["state"] = "complete"; job["elapsed"] = time.time() - job["started"]; write_status(); return None
        faults = verify_scene() if job["index"] == 0 else []   # once per job, before the first render
        if faults:
            raise RuntimeError("geometry read-back faults, not rendering: " + "; ".join(faults))
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

**Gate the queue on the geometry read-back.** The matched views are a
narrow window on a scene that is delivered whole, and the evidence rule
forbids overwriting, so a render spent on a faulty scene burns the tag.
Never send a rebuild and the render queue in one call without the read-back
in between: in one run the read-back that came back with the combined call
showed two quadrants were solid blocks (56 route faults, zone volume 2
percent over), the tag was already burnt, and the re-run had to take a new
tag. The queue above runs `verify_scene()` itself and REFUSES to render on
any fault. Prove the gate once by feeding it a known fault on a throwaway
copy of the scene and reading the `failed` status JSON's `error`.

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

- **Up axis and units are stated in the brief, not chosen by the builder.**
  Blender is +Z up, floors in the XY plane, metres. The rendered comparison
  cannot catch a wrong axis (a scene and a camera built on the same wrong
  axis render like a correct pair; earlier Blender legs only matched by
  coincidence of the native convention), so read it back as a value each
  iteration: the ground object's lowest z is about 0 and the tallest
  object's extent lies along z (per-object read-back below).
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
- **Assign material slots BEFORE `bm.to_mesh`, not after.** In the idempotent
  `set_obj` helper, `me.materials.clear()` followed by re-appending slots
  resets every polygon's `material_index` to 0 - a two-material drum
  (travertine inside, walnut outside) rendered all one material for seven
  iterations before this was caught. Assign slots on the bmesh (or set them
  on the mesh) before `to_mesh`, and for any multi-material object add the
  standard verification: read back evaluated polygons grouped by
  `material_index` (and radius, or whatever axis separates the materials)
  and confirm the counts match the plan - do not judge material assignment
  from a render, where lighting can hide the wrong material.
- **Procedural textures on parametric geometry: use Texture Coordinate >
  Object, not Generated.** A Noise texture on default Generated coordinates
  stretched into streaks on 120-segment arc rings and long boxes; switching
  the Vector input to Texture Coordinate > Object gave metric, isotropic
  relief because all objects share the world origin.
- **Brick texture is planar XY - use a Z-based course mask for walls of
  mixed orientation.** A Brick texture reads the X/Y of its input vector, so
  on a wall lying in the YZ plane it produced blotches instead of coursing.
  Horizontal coursing from object-space Z (SeparateXYZ > multiply > fract >
  less-than > bump) works on every wall orientation and lines up scene-wide.
- **`me.materials.clear()` after `bpy.data.meshes.new_from_object`.** The
  copy made from an evaluated boolean host carries the host's EMPTY slot 0
  and every polygon points at it, so the whole object renders default
  white - four towers did for twelve iterations while the builder explained
  the white as sunlight. Clear, append the materials you intend, then set
  `polygon.material_index` explicitly (clear and re-append resets the
  indexes, see the material-slot bullet above). Read back: polygon counts grouped by
  `material_index`, and `slot.material is not None` for every slot in use -
  not a pixel sample, where lighting can hide the wrong material.
- **A scripted boolean carve can fail silently two ways; the DCC reports
  success either way.** (1) *Excluded collection:* a host created inside a
  collection a previous run left EXCLUDED from the view layer evaluates
  WITHOUT its modifiers - 386 polygons in, 386 out, zero seconds - and
  `view_layer.update()` does not help. (2) *Inside-out cutters:*
  `bmesh.ops.recalc_face_normals` on a freshly built closed solid returned
  inside-out cutters for some parameter values (same code, different radii),
  and an inside-out cutter makes the EXACT solver return an EMPTY mesh for a
  DIFFERENCE; with a collection operand one bad cutter empties the whole
  result. Checks:

  ```python
  import bpy, bmesh

  def walk(lc):
      for child in lc.children:
          yield child
          yield from walk(child)

  root = bpy.context.view_layer.layer_collection
  was_excluded = [lc.name for lc in walk(root) if lc.exclude]
  for lc in walk(root):
      lc.exclude = False                      # un-exclude BEFORE creating or evaluating the host
  # ... create host and cutters, add the Boolean modifier, evaluate ...
  for lc in walk(root):
      if lc.name in was_excluded:
          lc.exclude = True                   # restore afterwards

  def assert_cutter_ok(bm, name):
      """Wind faces explicitly (profile CCW: side quads a[j], a[j+1], b[j+1], b[j];
      start cap reversed, end cap forward) - do not rely on recalc_face_normals."""
      vol = bm.calc_volume(signed=True)
      if vol <= 0:
          raise RuntimeError("%s: signed volume %.6f (inside-out)" % (name, vol))
      bad = [e for e in bm.edges if not e.is_manifold]
      if bad:
          raise RuntimeError("%s: %d non-manifold edges" % (name, len(bad)))

  POLY_FLOOR = 1000                           # from the plan: fewer polygons than this = carve failed
  host_eval = host.evaluated_get(bpy.context.evaluated_depsgraph_get())
  if len(host_eval.data.polygons) < POLY_FLOOR:
      raise RuntimeError("carve produced %d polygons" % len(host_eval.data.polygons))
  ```

  The poly-count floor raises instead of continuing. When it trips, test the
  cutters ONE AT A TIME with an Object operand (set the modifier's
  `operand_type = 'OBJECT'` and its `object` to each cutter in turn, evaluate,
  read the polygon count, restore the modifier in a `finally`): the cutter
  whose count collapses names itself. Every procedural build step needs a
  produced-something assertion of its own (polygon count, signed volume).
- **Per-object read-back in the FINAL state, not only per iteration.** For
  every object that belongs to the delivery record its name, evaluated
  polygon count, bounding-box size in metres, world location and whether it
  is hidden. It is the one independent record a consumer can re-measure to
  decide which objects are the deliverable (the members' counts must sum to
  the leg's own totals) and which hidden helpers, superseded parts or
  render-only duplicates to leave out, and it carries the axis check above.
  Record it with `up` (+Z), `front`, `units` (metres), `ground` and the
  excluded helpers with a reason; the field names are the ones in
  `templates/final_delivery.example.json`, which is the authority. Generate
  it from the final scene, never type it.

  ```python
  import json, bpy

  dg = bpy.context.evaluated_depsgraph_get()
  rows = []
  for ob in bpy.data.objects:
      if ob.type != 'MESH':
          continue
      ev = ob.evaluated_get(dg)
      rows.append({
          "object": ob.name,
          "polys": len(ev.data.polygons),
          "size_m": [round(v, 4) for v in ev.dimensions],
          "location_m": [round(v, 4) for v in ob.matrix_world.translation],
          "hidden_render": bool(ob.hide_render),
      })
  print(json.dumps(rows, indent=1))
  ```

## 4. Engines

EEVEE for every loop render (seconds per view). Cycles only for the final
labelled pass, and expect it to change lighting: the first run's corridor
shafts largely disappeared under Cycles. That is a finding, not a polish.

## 5. Lighting budget before iteration one

- **Emissive meshes light nothing in EEVEE.** The warm LED coves in the
  reference are emissive meshes; in EEVEE Next they render bright but
  illuminate no other surface. Place a real area light per glowing cove
  (chamber disk 150-350 W, hall rectangles 30-120 W, ring squares 80 W) -
  even 8 x 250 W rectangles barely registered against sunlit stone
  (measured right-third mean 58.6 -> 56.4), so budget generously and
  re-measure.
- **Light-probe volume bake is a no-op from the MCP execute context.**
  `bpy.ops.object.lightprobe_cache_bake(subset='ALL')` returns `{'FINISHED'}`
  in under a second even after a 60 s wait, and `bpy.app.is_job_running` has
  no `LIGHT_BAKE` enum to poll. An A/B render of the same camera with the
  probe object hidden vs visible measured mean pixel 0.204 vs 0.196 -
  effectively identical. Verify any indirect-light change with a probe
  on/off A/B render before scoring it, and keep plain placed lights as the
  fallback rather than trusting the bake.
- **Volume density low, anisotropy high, so the beam reads without a
  veil.** A beam spot plus Principled Volume haze at density 0.014 with a
  3.2e6 W spot raised the chamber mean from 96 to 128 and read as fog over
  the whole room. The window that worked was density 0.006, anisotropy
  0.65, and a 1.3e6 W, 12-degree spot: the beam shows, the walls behind it
  do not wash out.
- **Write the reference mean luminance per view next to the render mean in
  the readback.** A two-line PIL snippet (mean of the reference image, mean
  of the render) turns exposure into a number instead of an eye judgement,
  and surfaces zones whose references disagree on brightness (one run
  needed the same room darker for two views and brighter for a third -
  that is a plan problem to settle in the brief, not something one lighting
  rig can serve). The per-view luminance read and its thresholds are in
  `reference/lighting_match.md`; the scratch script is
  `scripts/scratch_luminance.py` (section 10).
- **A world light cannot be zoned - it enters every opening.** In a scene
  that mixes an enclosed room with open corridors, keep the world low and
  fill each zone with its own area lights placed high in its openings, and
  give the camera a separate dim sky (Light Path > Is Camera Ray) so a
  visible sky does not dominate the luminance read of an exterior-facing
  view. Measured: raising the world strength 0.35 -> 0.85 to lift dark
  corridors poured light through the roof opening into the enclosed room
  (+19 mean luminance) and blew the corridor frames (+32, +52); corridor
  fills of 600 W gave +20 / +34 / +52 against the references, 220 W gave
  +3 / -4 / +28 (hero view -8.5), and the iteration render then reproduced
  the scratch numbers exactly.

## 6. Moving an EEVEE loop scene to Cycles

An EEVEE-tuned rig is full of fakes (bounce-fill lights, over-bright
emission strips) that must come out before Cycles renders true bounce
light on top of them.

1. **Hide every bounce-fake fill first.** A scene with 13 area fills faking
   bounce plus emission-40 LED strips rendered at chamber mean 133 in
   Cycles against a reference of 56 - hide the fakes before touching a
   single real light.
2. **Divide strip emission by about 8 and re-measure.** The strip emission
   that reads as a clean bright line in EEVEE floods a room in Cycles; the
   final values were 5 for chamber strips and 12 for corridor coves, down
   from 40.
3. **Use Cycles light linking per zone, not a light per problem.**
   `obj.light_linking.receiver_collection` (Blender 4.0+) lets one scene
   carry a chamber-only near-vertical sun as the oculus beam, a
   lantern-only point light for a drum interior, a hallway-only steeper
   sun, and view-only fills - the linking collection does not need to be in
   the view layer and may hold child collections.
4. **VIEW_ONLY render-queue pattern, with reset-before-save.** Per-view
   dressing (a closed end wall for one camera, a wash for another) is
   handled by a `VIEW_ONLY` dict in the timer render queue that toggles
   `hide_render` per camera. Caveat: `VIEW_ONLY` objects keep the state of
   the LAST rendered view in the saved file - reset them to their default
   visibility before the final save.

## 7. Image-plate rule

Before rendering a new image plate onto a band that already carries an
accepted plate, match its luminance mean and standard deviation to the
accepted plate (a two-line PIL script) - two extra relief plates with
greyscale means of 126 and 172 against an accepted plate's 181 rendered as
dark grey stone (hallway frieze 46 against a reference of 83) and cost an
iteration before the level-match. Assign photo-derived plates only to bands
whose nearest matched camera is several metres away: a photo's stone grain
drives the bump channel and reads as rough bark at close range (2 m); keep
the smoothest (generated) plate for close-up bands.

## 8. Letterbox math for a padded reference

With a 2:1 reference padded into a 16:9 render, the vertical mapping is:

```
y_render = 0.057 + 0.886 * y_ref
```

Match the render's HORIZONTAL field of view to the reference; vertical
positions then land automatically from the formula above. Confirm any
composition read against this math or against a luminance row profile
(section on measurement in SKILL.md step 3) rather than from the
downsized three-panel comparison alone.

## 9. Fit before render: fit detail layout by camera projection

With a frozen camera, an oriented or repeated detail (a seam layout on a
sphere, a rim-loop count on a net, row spacing on a wall) does not have to
be guessed one render at a time. Project candidate geometry through the
camera's own matrix onto a mask extracted from the reference and score the
fit numerically before a single render is spent:

```
u = W * (0.5 + f * x / (-z) / sensor - shift_x)
v = W * (0.5 - (f * y / (-z) / sensor - shift_y))
```

where `(x, y, z)` is the candidate point in camera space (transform world
points by the camera's inverse `matrix_world`), `f` is the lens focal
length, `sensor` is the sensor width, `shift_x`/`shift_y` are the camera's
lens shift, and `W` is the render width (use the render height and the
matching formula for `v` against sensor height if the camera is not
sensor-fit-horizontal).

Build the mask before trusting any fit score: for a matte-on-polished
feature (seam tape on a saturated gold surface), threshold on low
saturation AND exclude the near-white specular highlight with a value gate
(for example `value < 0.92`) - a mask built without the highlight gate can
score well while pulling the fit toward the wrong topology, so look at the
mask overlay before believing the optimizer's number. Score candidates with
a distance-transform (or simple pixel-residual) comparison between the
projected points and the mask's measured feature pixels (knots, apexes,
edges); the correct count or orientation is the one with the lowest
residual, not the one that looks plausible by eye.

This turns a repeat count or an orientation named in a brief into something
you verify in seconds instead of guessing over several iterations - and it
applies to anything a frozen camera can see: only materials and lighting
still require an actual render to judge.

## 10. Scratch-test any render-pipeline change before the iteration render

Under the evidence rule an iteration's renders are never overwritten, so a
render broken by the builder's own pipeline change (not by the scene) still
burns a full iteration and can count against the stall streak. After ANY
change to the render pipeline - film settings, the compositor, the view
transform, engine settings, a new emissive object or a light-linking
change - render a small scratch frame (128 px is enough) to the scratchpad
and read back a handful of named pixel boxes (background, hero surface,
each light source) converted to sRGB, before submitting the real iteration
render.

**Any light, world, exposure or emission change counts, including "just a
world strength".** Scratch-render ALL matched views, and before the
iteration tag is spent read each view's render mean luminance against its
reference mean as a signed difference. `scripts/scratch_luminance.py` takes
the scratch tag and prints, per view, render mean / reference mean / signed
difference; the method and the thresholds are in
`reference/lighting_match.md`. A lighting value is a guess until a scratch
frame has been measured against the reference; measured first, the
iteration render is a confirmation, not an experiment (skipping this for a
world-strength tweak regressed three views at once, section 5).

**A scratch render saves a NEW increment first, like any render.** A plain
save (or Ctrl-S) after an iteration render writes the post-iteration edits
into that iteration's render snapshot, and the iteration can no longer be
reopened as rendered: call `bpy.ops.wm.save_mainfile(incremental=True)`
before the scratch render, exactly as the queue in section 1 does.

**Thin negative features get a measured contrast here too.** A groove, wall
joint, seam, panel gap or inlay can be modelled exactly right and still be
invisible to the comparison, because its faces share the neighbouring
surface's grey (one build: a 2.2-level dip out of 255 where the reference
joint was 97-123 levels darker, so the scorer could only mark it "present
but weak"). In the scratch step, for each rubric element that is a thin
negative feature, sample a column- (or row-) averaged profile across the
element at its expected position in BOTH the scratch render and the
reference and log the two dips side by side; a render dip that is a small
fraction of the reference's is reported as "not visible" up front, and the
element gets its own darker grey in the value study.

```python
from PIL import Image

def column_profile(png, x0, x1, y0, y1):
    """Column-averaged luma over the band [x0,x1) x [y0,y1): one value per column.
    For a horizontal feature, crop a band of rows and resize to (1, y1-y0) instead."""
    band = Image.open(png).convert("L").crop((x0, y0, x1, y1))
    return list(band.resize((x1 - x0, 1), Image.BOX).getdata())

def dip(profile):
    """How far the darkest column sits below the median of the band (levels of 255)."""
    s = sorted(profile)
    return s[len(s) // 2] - s[0]
```

Compare `dip(render_profile)` with `dip(reference_profile)` for the same band;
include a few columns either side of the feature so the median is the
neighbouring surface.

Blender 5.1 compositor facts worth knowing before debugging this blind:
there is no `scene.node_tree` any more - the compositor lives at
`scene.compositing_node_group`, a node group whose output is a
`NodeGroupOutput` with an Image interface socket (`CompositorNodeComposite`
is not defined in 5.1). The Alpha Over node's sockets are named
Background / Foreground / Factor - wiring a render into Factor by mistake
produces a silent black frame, not an error. Object texture coordinates on
a SCALED object are in that object's LOCAL space (a 400 m floor plane
scaled up from a small mesh will emit or texture as if it were still small)
- use Geometry > Position for anything that needs to gate in world space.

## 11. Solve camera and room from repeated elements

Repetition in a reference is measurement data: equal elements at known
ratios over-determine the camera and the room, so solve them BEFORE
iteration one instead of discovering the numbers by render. Use it whenever
a matched view shows a regular repeated element on a circle or a line
(niches, columns, ribs, windows). Record the solve in the brief.

1. **Tabulate landmarks per visible element** (centre x, top y, foot y, and
   BOTH edge x, so the width is a column too) from the reference at full
   size.
2. **Solve in closed form first.** Centre offset over height per element
   gives `R * sin(k * delta) / H`, so `sin(3d) / sin(d)` fixes the slot
   angle and with it the count and the radius; the centre-to-edge height
   ratio fixes the camera distance; the centre height fixes the focal
   length; the floor-curvature sign change fixes the camera height; the
   horizon row fixes the lens shift. Project two elements through the
   result: they should land within about 2 percent of frame height on the
   first rebuild.
3. **Put every measurable and every line the rubric scores in the fit.**
   Centres and heights alone are under-constrained - foreshortening carries
   the wall angle, and that lives in the WIDTHS - and so are the elements
   alone when the rubric also scores another line (an opening's edge, the
   wall-to-ceiling line). Two measured cases:
   - A fit on centres and heights agreed with its own verification
     instrument to 0.5 percent for eleven iterations while the reference's
     edge elements were 21 percent wider than the build. Adding widths to
     the cost moved the answer (radius 8.06 -> 9.0 m, 26 -> 30 slots, camera
     from outside the room to 8.55 m behind the centre, inside it; widths
     within 4 percent, centres within 2-5 percent), and both "findings for
     the human" the first solve had reported (camera outside the room,
     entrances in frame) disappeared - they were artefacts of the
     under-constrained fit.
   - A pre-solve from the repeated elements alone gave a clean camera
     (31 px RMS) whose first render matched the element band and put a
     large opening off-frame; adding 11 samples of that opening's rim showed
     the concept is not one consistent circle, and no camera satisfies both.
4. **Verify with an instrument that measures something the solve did NOT
   fit** (widths when the solve fitted centres and heights; an unfitted
   line). A solve and an instrument built from the same measurements agree
   by construction. Keep one plain reference-over-render pair at full size
   every few iterations next to the multi-panel; it is how the 21 percent
   error was finally seen.
5. **When the constraints cannot all fit, report the trade-off with renders
   and do not choose silently.** Render each candidate (element-weighted,
   rim-weighted, a blend) and put the residuals and the frames in front of
   the human - in the second case above the element-weighted camera left
   the opening hundreds of pixels off, the rim-weighted one left the element
   tops 144 px off, and a 0.4 blend was worse on both. Two findings a solve
   can return that only the human may settle: a camera position outside the
   room, and a plan feature that cannot be hidden from the view.

Read-back that proves it: a per-element residual table (pixels or percent of
frame height) at the fitted camera, plus the verification instrument's
numbers for the quantity the fit did not use.
