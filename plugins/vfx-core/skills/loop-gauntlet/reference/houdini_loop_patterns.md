# Houdini patterns for the loop

Distilled from this workspace's Houdini MCP facts (`.claude/rules/houdini.md`,
memory `project_houdini_mcp.md` and `technical_houdini_nuke_patterns.md`),
the fxhoudinimcp tool descriptions, and the first Houdini legs of the loop
(Houdini 21.0.596 live through fxhoudinimcp 2.25; refreshed 2026-10-10).
Items marked VERIFIED or "measured" were exercised on that build. Anything
still unconfirmed is flagged UNVERIFIED at the point it comes up, and again
in the list at the end - do not invent an API name to fill a gap. All
snippets are Python (HOM, the `hou` module), ASCII, raw-string Windows
paths, and assume the working folder and view list come from the spec.

## 1. Scene layout and the version-save ritual

- **Up axis and units are stated by the human in the brief, never chosen
  by the builder.** Houdini is +Y up, floors in the XZ plane, metres. A
  builder told only to "report which up axis you used" built a whole
  scene Z-up in a Y-up DCC and lost two iterations to it. The rendered
  comparison cannot catch this - a scene and a camera built on the same
  wrong axis render exactly like a correct pair - so read it back as a
  value every iteration: the ground object's bounding-box min y is about
  0 and the tallest object's extent lies along y (per-object read-back in
  section 5).
- One `/obj` geo node per object in the build, named for what it is
  (`/obj/PLINTH`, `/obj/DRUM_INNER`), never `geo1`, `geo2`. Inside each geo
  node, a SOP chain that reads top to bottom as a plan: a source primitive,
  then modifiers, ending in an `output` node with the display and render
  flags set. Name SOPs for their job (`source_grid`, `deform_relief`,
  `output`), not their type-plus-number default.
- Read state back before creating, same rule as Blender: `hou.node(path)`
  first; if it returns an object, update its parameters rather than
  creating a sibling (older fxhoudinimcp suffixed `_1`; 2.23+ refuses a
  taken name - see section 5). `build_network` in
  fxhoudinimcp takes a whole planned graph in one call and is the atomic
  equivalent of the Blender timer-queue pattern - it validates every node
  type and parameter name against the running Houdini before touching the
  scene when called with `dry_run=True`, so use `dry_run` first for any
  node type not already used this session.
- **Version-save ritual: save a NEW increment before every render or heavy
  operation, scratch renders included.** Never a plain
  `hou.hipFile.save()`: the current hip is usually the increment the last
  iteration render was launched from, so a plain save writes the
  post-iteration edits into that render's snapshot and the iteration can
  no longer be reopened as rendered. husk reads the scene from disk, so
  never render from an untitled or unsaved hip either. Order per
  iteration: build, save vNNN, render, poll, read back.

  ```python
  import hou
  from pathlib import Path

  WORK = Path(r"D:/work/my_loop")          # from the spec
  NAME = "my_scene"                         # from the spec
  hip_dir = WORK / "houdini"
  hip_dir.mkdir(parents=True, exist_ok=True)

  existing = sorted(hip_dir.glob(NAME + "_v*.hip"))
  next_n = len(existing) + 1
  out = hip_dir / (NAME + "_v%03d.hip" % next_n)
  if out.exists():
      raise RuntimeError("version file already exists: " + str(out))
  hou.hipFile.save(str(out))               # positional path; VERIFIED on 21.0
  # read back: the path Houdini itself now reports
  assert Path(hou.hipFile.path()) == out, "save did not update the current hip path"
  ```

  VERIFIED (21.0.596): `hou.hipFile.save(path)` with a positional path
  saves AND switches the current hip to that path, which is why the
  assert reads `hou.hipFile.path()` back. The `file_name=` keyword form
  was not tested - use the positional form.
- **When the build is an HDA, version the HDA files too.** A hip increment
  REFERENCES the asset, it does not contain it: editing the asset rewrites
  the library file in place (`updateFromNode`), so an intact old hip reopens
  with the NEW asset. At every iteration render, after the definition has
  been saved to its file, copy each library to `otls/history/<name>_<tag>.hda`
  (copy, never overwrite):

  ```python
  import shutil
  import hou
  from pathlib import Path

  def snapshot_hdas(work, tag):
      """Copy every HDA library under <work>/otls to otls/history/<name>_<tag><ext>."""
      otls = (Path(work) / "otls").absolute()
      hist = otls / "history"
      hist.mkdir(parents=True, exist_ok=True)
      copied = []
      for lib in hou.hda.loadedFiles():
          src = Path(lib).absolute()
          if src.parent != otls:            # only this build's own libraries
              continue
          dst = hist / (src.stem + "_" + tag + src.suffix)
          if dst.exists():
              raise RuntimeError("history copy already exists: " + str(dst))
          shutil.copy2(str(src), str(dst))
          assert dst.stat().st_size == src.stat().st_size, "copy size mismatch"
          copied.append(str(dst))
      return copied
  ```

  Read back: the returned list must name every library the hip
  instantiates; an empty list for an HDA build means the filter missed the
  libraries - stop and look.

## 2. Matched cameras

- One camera object per view, `/obj/CAM_<view>`, matching the Blender
  convention exactly so a spec's `camera` field (`CAM_<view>`) needs no
  per-DCC translation.
- Houdini camera focal length and aperture are separate parameters on the
  `cam` object node (`focal` in mm, `aperture` in mm for the horizontal
  sensor width) rather than Blender's single sensor-width-plus-focal-length
  pair - read both back after setting either, the way the Blender file
  reads back sensor width for the same reason (so the number in the log
  means one thing):

  ```python
  cam = hou.node("/obj/CAM_hero")
  cam.parmTuple("t").set((0, 1.6, 8))     # position, metres
  cam.parmTuple("r").set((0, 180, 0))     # rotation, degrees
  cam.parm("focal").set(35)
  cam.parm("aperture").set(36)
  # read back
  focal = cam.parm("focal").eval()
  aperture = cam.parm("aperture").eval()
  print("CAM_hero focal=%s aperture=%s" % (focal, aperture))
  ```

- Setting a camera from a reference framing: estimate the horizontal field
  of view the reference implies from its aspect and any known real-world
  anchor in frame (the same anchor-derived-scale approach the brief already
  requires), convert to a focal length at the chosen aperture with
  `focal = aperture / (2 * tan(hfov / 2))`, place the camera, then verify
  with the same camera-projection fit method the Blender file uses in its
  "fit before render" section (project a known reference point through the
  camera, or equivalently build the same `u, v` formula from the camera's
  world transform, `focal`, and `aperture`) rather than trusting the
  estimate from a single render. VEX `toNDC()` is a verified route for
  projecting a point through a Houdini camera (section 8).
  UNVERIFIED: the exact HOM method name for reading a camera's projection
  matrix in this Houdini version - query it with `get_node_card` /
  `search_help("camera projection")` before writing the fit script rather
  than guessing a method name.

## 3. The render call for loop views

- Loop views render through Karma. The workspace's own Houdini rules file
  documents Karma being invoked from `/out` (a ROP network) or a Solaris
  stage, and that a Solaris/LOP scene renders correctly only when its
  materials live in the LOP network, not left behind in `/obj`. Use
  `create_render_node` (or `create_lop_node` for a Solaris path) to build a
  Karma ROP, then `set_parameters` for its resolution, sample count and
  output path in one batched call rather than one `set_parameter` per
  field.
- Sample count: the spec's `render_size` is honored on the ROP's resolution
  override; use a low sample count for loop iterations (64 samples,
  matching the "64 samples-equivalent for the loop" the brief calls for -
  a rough parity with Blender EEVEE's fast-iteration role, not a claim that
  the two engines' sample semantics are equivalent) and a materially higher
  count (256+, matching the Blender file's Cycles final of 256) only for
  the labelled final pass, never for a loop iteration.
- Output: `renders/<tag>_<view>.png`, one file per view per iteration,
  matching the Blender convention so `compare_views.py` needs no per-DCC
  branching.
- **Engine and device - VERIFIED (21.0.596): Karma XPU renders without
  falling back to CPU** (measured: 752x1344, 64 samples). Use XPU as the
  loop setting. On a new machine, still read the first scratch frame's ROP
  log or `get_node_errors_detailed` for a fallback-to-CPU warning; if one
  shows, fall back to Karma CPU at a reduced sample count and record the
  choice in SCENE_BRIEF.md rather than silently eating the slower render
  time every iteration.
- **PNG output - VERIFIED: the ROP's `picture` parameter accepts a `.png`
  path under the working folder** and writes it there. (The workspace's
  own viewport render tools write JPG to `C:/temp/`; that is those tools,
  not the ROP.)
- **Resolution: set `override_camerares` as well as `resolutionx/y`**,
  otherwise the ROP renders at the camera's own resolution. The one-call
  path is the MCP `setup_render(renderer="karma", camera=...,
  resolution=[w, h])` (fxhoudinimcp 2.24.1+): it sets `override_camerares`,
  `resolutionx/y` and `camera` and names `picture` as the output parameter
  (read back from the node, not itself render-tested). Either way the
  proof is the image dimensions read back after the render (snippet
  below), not the parameter values.
- **The `/out` Karma ROP's `render()` is NON-BLOCKING.** It launches husk
  and returns at once (measured: 0.49 s, with the PNG not yet on disk; the
  file appeared about 4 s later). A caller that reads the file on return
  reads nothing. Poll the output file until it exists, is non-empty and its
  size is unchanged across 2 successive polls, THEN read it back. The
  size check cannot see a writer that stalls for longer than polls x
  interval (a test writer pausing 1.5 s between chunks passed a 1 s window
  at half its final size), so the decode in the read-back below is the
  second line of defence: a truncated PNG fails to decode and a wrong size
  fails the dimension assert.
- Render call, poll and read-back:

  ```python
  import hou, time
  from pathlib import Path

  ROP = "/out/karma_loop"                  # or a LOP-network path
  TAG = "iter01"                            # from the loop
  VIEW = "hero"                             # from the spec
  W, H = 1376, 768                          # from the spec
  OUT = Path(r"D:/work/my_loop/renders") / (TAG + "_" + VIEW + ".png")
  if OUT.exists():
      raise RuntimeError("output already exists: " + str(OUT))   # never overwrite evidence

  def wait_stable(path, polls=2, interval=1.0, timeout=100.0):
      """Wait for a file written by a background process. Returns its size once
      it is non-empty and unchanged across `polls` successive polls."""
      p = Path(path)
      deadline = time.time() + timeout
      last, same = -1, 0
      while time.time() < deadline:
          size = p.stat().st_size if p.exists() else 0
          if size > 0 and size == last:
              same += 1
              if same >= polls:
                  return size
          else:
              same = 0
          last = size
          time.sleep(interval)
      raise TimeoutError("render output never settled: " + str(path))

  rop = hou.node(ROP)
  rop.parm("camera").set("/obj/CAM_" + VIEW)
  rop.parm("override_camerares").set(1)     # without it the camera's resolution wins
  rop.parm("resolutionx").set(W)
  rop.parm("resolutiony").set(H)
  rop.parm("picture").set(str(OUT))
  rop.render()                              # returns at once; husk writes in the background
  size = wait_stable(OUT)
  print("bytes=%s mtime=%s" % (size, OUT.stat().st_mtime))
  ```

- **The timeout risk is the poll, not the render.** The Blender file's
  whole first pattern exists because an inline render of six views through
  the MCP execute call exceeds the tool timeout. A Karma ROP `render()`
  returns at once, so no timer queue is needed here, but keep each poll
  loop shorter than the MCP call timeout (the `timeout` argument above),
  render one view per call, and for a view that needs longer poll from
  separate calls (one `stat` each). The MCP `start_render` tool is the
  other path: it holds inside Houdini until the render is done - wait for
  it, call nothing else meanwhile.
- **Read-back after the render, not after the call returns.** No
  exception from `rop.render()` is a launch signal, not a correctness
  signal (operating rule 2). Read the file back: size, dimensions, and
  pixel content.

  ```python
  from PIL import Image
  im = Image.open(str(OUT)).convert("RGB")
  w, h = im.size
  assert (w, h) == (W, H), "rendered %sx%s, asked %sx%s" % (w, h, W, H)
  colors = im.getcolors(maxcolors=w * h)
  unique_values = len(colors) if colors else "many"
  print("size=%sx%s unique_values=%s" % (w, h, unique_values))
  ```

  A flat or black frame (few unique values) means the active camera was
  wrong, the ROP's display path pointed at the wrong node, or the render
  never actually ran through Karma - the same suspect-blank check
  `compare_views.py` already runs on the read-back PNG. A wrong size means
  the camera's resolution won (`override_camerares` is off).

## 4. Materials

- MaterialX is the Karma-native shading network type; a Houdini
  "Principled Shader" MaterialX subnet (built with `create_material` /
  `create_material_network` in fxhoudinimcp) is the direct analogue of
  Blender's Principled BSDF for blockout and loop materials - simple
  shaders in the right value and hue family, refined only after geometry
  and cameras match, exactly as the contract requires.
- Image textures: an `mtlximage` node (or the equivalent texture node the
  MaterialX Principled build produces) pointed at a file on disk. A
  Polyhaven download placed on disk under the working folder's texture
  folder is used the same way as any other image texture - point the node
  at the local path, never a URL, and confirm the file exists before
  wiring it in (`Path(tex_path).exists()`), the same read-before-use
  discipline as the scene-hygiene rule below.
- Displacement for engraving: a height/bump texture wired into the
  MaterialX Principled shader's displacement input (or a `mtlxdisplacement`
  node) drives micro-relief the same way a bump/displacement setup would in
  Blender. UNVERIFIED: the exact MaterialX displacement node name and
  whether Karma XPU supports true displacement (vs. bump-only) in this
  Houdini version - confirm with `get_node_card` on the material network
  and `search_help("displacement karma")` before committing an engraving
  plan to true geometric displacement rather than a bump map.

## 5. Scene hygiene read-backs

- **No default node names.** A `find_nodes` or `list_children` sweep of
  the network should show zero nodes still named `geo1`, `box1`,
  `mountain1`; every SOP and object node is named for its role.
- **No auto-numbered duplicates.** The read-state-back rule again: a
  second `geo1_1`/`box2` appearing means a creation script ran twice
  without checking `hou.node(path)` first. fxhoudinimcp 2.23+ refuses
  `create_node` with a taken name ("'x' is already taken in ... Rename or
  delete that node first"), so the failure now surfaces as a tool error
  instead of a silent duplicate. That error means READ STATE BACK (what is
  there, is it a leftover of this build?) - renaming around it recreates the
  very duplicate the rule guards against.
- **Part counts and bounding boxes.** Seed a union box from the first
  box, never from an empty `hou.BoundingBox()`: the default box is a zero
  box AT THE ORIGIN, not an empty one, so `enlargeToContain` on it silently
  drags every part's measured extent to (0, 0, 0) (measured: every part
  read down to y = 0, a sill of 0.0 and a ledge 0.75 m thick). Or take
  `geo.boundingBox()` on a blasted subset.

  ```python
  import hou

  def union_bbox(boxes):
      """Union of hou.BoundingBox objects, seeded from the first one."""
      boxes = list(boxes)
      if not boxes:
          return None                       # no measurement: a FAIL downstream, not a zero box
      mn, mx = boxes[0].minvec(), boxes[0].maxvec()
      bb = hou.BoundingBox(mn[0], mn[1], mn[2], mx[0], mx[1], mx[2])
      for b in boxes[1:]:
          bb.enlargeToContain(b)
      return bb

  node = hou.node("/obj/DRUM_INNER/output")
  geo = node.geometry()
  bbox = geo.boundingBox()
  print("points=%s prims=%s bbox_min=%s bbox_max=%s" %
        (geo.intrinsicValue("pointcount"), geo.intrinsicValue("primitivecount"),
         bbox.minvec(), bbox.maxvec()))
  ```

  Compare against the human-scale anchors in the brief (bench 0.45 m,
  door 2.1 m) the same way the Blender file expects a raycast to confirm
  circulation routes connect - a bounding box in the wrong units (Houdini
  defaults to metres already, but an imported asset may not) is caught
  here, not at render time. Tool-test every read-back instrument like this
  one on a throwaway tag (a box of known size) before the first scored
  iteration: the origin trap above was caught that way, before any score
  depended on it.
- **Force-cook every output, not just the displayed one.** Houdini cooks
  lazily, so an output nothing displays or reads never compiles: a wrapper
  wrangle with a VEX compile error sat in a delivered asset for iterations
  because the loop rendered and scored output 0 only, and was found a day
  later by the next leg's pre-change check. For a delivered HDA, cook
  outputs 0..N-1 and every member node on purpose and record the point and
  prim counts, or the error, per output. An output listed in the delivery
  record without a measured count is a FAIL.

  ```python
  import hou

  def force_cook_report(asset, n_outputs):
      """Per-output and per-member cook result. Every entry carries a count or an error."""
      report = {"outputs": [], "members": []}
      for i in range(n_outputs):
          row = {"index": i}
          try:
              asset.cook(force=True)
              geo = asset.geometry(i)              # hou.SopNode.geometry(output_index) - verified live, Houdini 21.0
              row.update(points=geo.intrinsicValue("pointcount"),
                         prims=geo.intrinsicValue("primitivecount"))
          except Exception as exc:
              row["error"] = str(exc)
          report["outputs"].append(row)
      for member in asset.allSubChildren():
          row = {"node": member.path()}
          try:
              member.cook(force=True)
              row["errors"] = list(member.errors())
              row["warnings"] = list(member.warnings())
          except Exception as exc:
              row["error"] = str(exc)
          report["members"].append(row)
      return report
  ```

  Read back: every output row has `points`/`prims` or `error`; any `error`
  is a FAIL naming the node, and a zero count on an output the record
  describes as geometry is a FAIL too. In VEX, type a `point()`/`prim()`
  read into a local of the right type before passing it to an overloaded
  setter (an untyped call made `setprimattrib()` ambiguous), and spell
  `removepoint`, not `removepoints`. Also note that a forced cook of an
  HDA instance alone sets `hou.hipFile.hasUnsavedChanges()` True with no
  parameter change - read that flag BEFORE cooking, or record it; never
  gate on it afterwards.
- **Final-state per-object read-back.** In the FINAL scene (not only per
  iteration) read back, for every object that belongs to the delivery:
  node path, prim count, point count, bounding-box size in metres and
  world translation. This is the one independent record a consumer can
  re-measure to settle which `/obj` nodes belong to which asset when one
  hip holds several (helper nulls, probes, backdrops, lights, cameras,
  superseded parts and render-only duplicates sit next to the deliverable):
  the members' prim counts must sum to the leg's own totals. Record it
  together with `up` (+Y), `front`, `units` (metres), `ground` (the plane
  the object rests on) and the excluded helpers with a reason; the field
  names are the ones in `templates/final_delivery.example.json`, which is
  the authority. Generate the record from the final scene, never type it.

  ```python
  import hou

  def object_readback(path):
      """Prims, points, bounding box and world position of one geo object."""
      obj = hou.node(path)
      geo = obj.displayNode().geometry()
      bb = geo.boundingBox()
      return {
          "node": path,
          "prims": geo.intrinsicValue("primitivecount"),
          "points": geo.intrinsicValue("pointcount"),
          "bbox_size_m": [round(v, 4) for v in bb.sizevec()],
          "bbox_min": [round(v, 4) for v in bb.minvec()],
          "world_t": [round(v, 4) for v in obj.worldTransform().extractTranslates()],
      }
  ```
- **Camera matrices:** read `cam.worldTransform()` (or
  `cam.parmTuple("t").eval()` plus `cam.parmTuple("r").eval()`) for every
  `CAM_<view>` and log it next to the focal/aperture read-back in section 2
  - a camera silently nudged by a later script call is a composition bug
  that a render alone will not explain.

## 6. Fit-before-render and the scratch-test rule

- **Fit before render, Houdini version.** The Blender file's camera-
  projection method (project candidate points through the camera's own
  matrix, score against a mask extracted from the reference, before
  spending a render on a repeat count or orientation) carries over exactly:
  replace Blender's `matrix_world` inverse with the Houdini camera's own
  transform (`cam.worldTransform().inverted()`) and the aperture/focal pair
  from section 2 in place of Blender's sensor width. The same rule applies:
  materials and lighting still require a real render to judge, but geometry
  fit against a frozen camera does not.
- **Scratch-test any render-pipeline change before the iteration render.**
  Under the evidence rule an iteration's renders are never overwritten, so
  a render broken by a Karma ROP setting, a MaterialX network change, or a
  color-management change still burns a full iteration. After any change
  to the render pipeline - ROP settings, a new material network, a
  displacement change, an XPU/CPU switch - render a small scratch frame
  (a low resolution override on the same ROP, output to the scratchpad, not
  `renders\`) and read back a handful of named pixel boxes (background,
  hero surface, each light source) before submitting the real iteration
  render. A scratch render obeys the section 1 save rule: save a new
  increment first. This is the same discipline as the Blender file's
  section 10, just without Blender-specific compositor facts to carry over -
  Karma's own color management (ACES/OCIO on the ROP, if configured) is a
  candidate place for the same kind of silent-wrong-output trap the Blender
  compositor produced, and is UNVERIFIED here: confirm the ROP's color
  space setting before trusting a render's apparent exposure.
- **Thin negative features get a measured contrast before the iteration
  render.** A groove, wall joint, seam, panel gap or inlay line can be
  modelled exactly right (the geometry read-back matches to a fraction of a
  pixel) and still be invisible to the comparison, because its faces carry
  the same grey as the neighbouring surface: one build showed a 2.2-level
  dip out of 255 where the reference joint was 97-123 levels darker, and
  the scorer could only mark the element "present but weak" from geometry
  alone. In the scratch step, for each rubric element that is a thin
  negative feature, sample a column- (or row-) averaged profile across the
  element at its expected position in BOTH the scratch render and the
  reference, and log the two dips side by side. A render dip that is a
  small fraction of the reference's is reported as "not visible" up front,
  and the element gets its own darker grey in the value study.

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

  Compare `dip(render_profile)` with `dip(reference_profile)` for the same
  band; the band must include a few columns either side of the feature so
  the median is the neighbouring surface.

## 7. Traps known from this workspace

- **Launch Houdini from PowerShell, not Git Bash, for anything the MCP
  will depend on.** With `HOME` set by Git Bash, Houdini resolves prefs to
  `%USERPROFILE%\houdini21.0` (the Git Bash HOME) and never scans
  `Documents\houdini21.0\packages`, so the fxhoudinimcp package (and the
  auto-started bridge) never loads. This is a launch-time trap, not a
  runtime one - it will not surface as an error, just as "the tools never
  connect."
- **Query-first, always.** `get_node_card(node_type, context)` returns the
  real connector labels, parameter names, defaults and menus for the
  version of Houdini actually running, and is cheaper than guessing and
  then debugging a `hou.OperationFailed` on a misspelled parm name (the
  workspace's own older pattern, "query then set," is the same rule under
  an earlier tool's name).
- **One call per network.** Every fxhoudinimcp call is a roughly 50 ms
  main-thread hop (HOM is main-thread-only); building ten nodes one call
  at a time measured about twelve times slower than the same ten nodes in
  one `build_network` call. Batch node creation, parameter sets
  (`set_parameters` over repeated `set_parameter`) and connections
  (`connect_nodes_batch` over repeated `connect_nodes`) for the same
  reason the Blender file batches renders onto a timer.
- **`verify_network` for read-back**, not a poll of individual nodes - one
  call that confirms the whole network matches what `build_network` was
  asked to create, the direct equivalent of the Blender file's end-of-run
  scene-hygiene verification pass.
- **hython for headless, if the live session is unavailable.** fxhoudinimcp
  only auto-starts inside the interactive Houdini GUI (its autostart hook
  is `python3.11libs/uiready.py`, which never runs under hython/batch), so
  a loop leg that must run without a GUI session cannot reach it through
  MCP at all - it needs a `hython` script driving `hou` directly, with no
  MCP bridge in the loop. This is a materially different execution path
  (no `get_node_card`, no `build_network`, no `verify_network` - plain HOM
  calls with query-first parameter lookups done by hand via
  `node.parms()`/`node.parmTemplateGroup()`), and should only be used when
  the contract's "live DCC session so the operator can watch" requirement
  is explicitly waived for that leg.

## 8. Karma camera, light and ROP facts (measured on 21.0.596)

Each was measured or read back from the node, not taken from docs.

- **Camera vertical shift:** `winy` is in frame-HEIGHT units and +winy
  moves the horizon DOWN the frame (VEX `toNDC()`: winy = -0.2062 put the
  horizon at row 226 of 768, +0.2062 at row 542). Project known points
  through a shifted camera before trusting it in a render.
- **An orthographic top camera of an interior sees only the roof.** A plan
  section needs the camera's near clip (`near`) set to cut at the wanted
  height.
- **HScript `max()`/`min()` take exactly two arguments.** A three-argument
  call in a parameter expression surfaced as "Expression stack error" on
  every node that read the parameter; nest the calls.
- **An environment light lights the scene but is invisible to the camera**
  until `light_contribprimary` ("Render Light Geometry") is on. An emissive
  sky-cap disc used instead is opaque geometry: it shadowed the sun and the
  environment light for the whole interior (frame mean fell from 35 to 30
  while the opening region still matched). Use a camera-only sky or the
  light's own visibility, not a lit disc.
- **Light parameter to USD mapping** (cone angle and softness, distance-
  squared falloff whatever `atten_type` says, double-sided area lights,
  intensities x 2 pi): the table with the read-back method is in the
  houdini-solaris-usd skill, `houdini-solaris-usd/reference/karma_lights.md` (houdini-vfx plugin). Read it before
  fitting a spot cone or lighting a surface with an area light.
- **ROP defaults:** `causticsenable` off, `diffuselimit` 3, `volumelimit`
  0, and a `denoiser` menu (off / optix / oidn). OptiX at 128 samples cut
  flat-region noise from 4.69 to 0.14 and kept box means within 2.8 luma of
  the undenoised prediction - a denoised scratch frame is a fair luminance
  read.
- **Fresh-session proof:** a fresh `hython` that loads the saved hip and
  calls the Karma ROP's `render()` renders the textured scene (344x192, 16
  samples) in about 6 s - a cheap "renders from a fresh session" check.
  Poll the output as in section 3 and gate it on content (section 9),
  never on the file existing.

## 9. Control test and hygiene read-back

A read-back harness written by the builder can only confirm what the
builder thought of. Derive the lists from the asset's own interface and
from the consumer's own rules, and have the scorer diff the two. Before
the first scored iteration, tool-test the harness itself on a throwaway
tag (section 5).

- **Generate the extreme test; do not type it.** Enumerate the asset's
  parameter templates (name, min, max) at run time, drive every
  non-read-only slider to its min and then to its max AT ONCE, and record
  which parameters were driven and which were skipped and why. A hand-typed
  list of 18 against an asset with 21 sliders never drove the bend or the
  two preview sliders, and a top score on a "controls" criterion says "every
  slider". The scorer diffs the recorded list against the asset's interface
  before accepting a top score.

  ```python
  import hou

  def extreme_plan(node, which):
      """{parm_name: value} driving every numeric slider to its 'min' or 'max'.
      Returns (plan, skipped) so a scorer can diff both against the interface."""
      plan, skipped = {}, []
      for p in node.parms():
          pt = p.parmTemplate()
          if pt.type() not in (hou.parmTemplateType.Float, hou.parmTemplateType.Int):
              continue
          if pt.isHidden() or p.isLocked() or p.keyframes():
              skipped.append((p.name(), "hidden, locked or animated"))
              continue
          plan[p.name()] = pt.minValue() if which == "min" else pt.maxValue()
      return plan, skipped
  ```

- **The sweep restores in a `finally` block, from a snapshot taken before
  the first change.** The test that drives every slider is the one most
  likely to fail while they are driven; without `finally` one exception
  leaves the asset at its extremes with the originals only in a local
  variable. Return the snapshot in the result.

  ```python
  def sweep(node, plan, check):
      """Drive `plan`, run `check(node)`, always restore. check() must itself return
      a FAIL entry for any measurement it could not take."""
      snapshot = {n: node.parm(n).eval() for n in plan}      # before the first change
      results = None
      try:
          for n, v in plan.items():
              node.parm(n).set(v)
          node.cook(force=True)
          results = check(node)
      finally:
          for n, v in snapshot.items():
              node.parm(n).set(v)
      return snapshot, results

  def check_le(label, value, limit):
      """A missing measurement is a FAIL, never a default PASS."""
      if value is None:
          return {"check": label, "pass": False, "why": "no measurement"}
      return {"check": label, "pass": value <= limit, "value": value, "limit": limit}
  ```

- **Every check FAILS when its measurement is missing**, and each guard the
  extreme test exists to prove gets a named assertion (not just "cooks and
  has parts"). A "parts do not overlap" check that read the gap between two
  slots defaulted to PASS when one slot became an entrance or did not exist
  in the extreme case; it passed vacuously and was caught by the scorer,
  not the author.
- **The agent that runs the sweep records its own baseline first.** The
  script's own `restored_ok` compares against a snapshot the script took
  at its own start, so a scene left modified by an earlier aborted run would
  be "restored" to the wrong values and still report ok. The sub-agent reads
  the watched parameters BEFORE the run (Step 0) and COMPARES the post-run
  read against that record - printing them is not a check.
- **Pre-flight the evidence file and read the script first.** The evidence
  file must not exist and its folder must, before any change is made;
  hold the results in memory and print them even if the write fails (a
  sweep that writes only at the end and refuses to overwrite loses every
  result to a bad path). Read the script for scene-level calls - save,
  open, clear, file moves - before running it in a live session.
- **Check each export by the importer's rules, with a measured value:**
  - USD: `defaultPrim` resolves to an existing prim (an exporter left
    `defaultPrim` naming a write node while the only prim had another name,
    so a reference without a prim path could not resolve it), plus
    `upAxis` and `metersPerUnit`.

    ```python
    from pxr import Usd, UsdGeom

    stage = Usd.Stage.Open(r"D:/work/my_loop/export/my_asset.usd")
    dp = stage.GetDefaultPrim()
    assert dp and dp.IsValid(), "defaultPrim does not resolve to an existing prim"
    print("defaultPrim=%s up=%s metersPerUnit=%s" % (
        dp.GetPath(), UsdGeom.GetStageUpAxis(stage), UsdGeom.GetStageMetersPerUnit(stage)))
    ```

  - FBX: read the file's `UnitScaleFactor` and compare it with the
    magnitude of a known dimension. `UnitScaleFactor` 1 means 1 unit = 1 cm,
    so metre-valued vertices (a trim with max y 5.62) under 1 read 100x too
    small in an importer that honours the header.
  - Fresh-scene reload: load the asset into an empty scene and report cook
    errors and warnings. A top score on a hygiene criterion usually
    hinges on this entry, so it needs a measured line in the read-back.
- **Every render-producing check reports a content gate, never existence
  alone.** A fresh-session render "proved" by its PNG existing is the
  existence evidence operating rule 3 forbids - a blank frame is a valid
  PNG. Gate on unique grey levels, mean and correlation with a known-good
  frame: one harness gated on unique grey >= 8 and correlation with the live
  iteration render >= 0.9 (read back afterwards: 223 grey levels, mean 95.9,
  correlation 0.991). Those thresholds are that run's, not a standard -
  set yours in the brief.

## UNVERIFIED

Confirm each of these against the running Houdini (via `get_node_card`,
`search_help`, or a scratch test) before trusting it in a real loop run:

- The exact HOM method for reading a camera's projection/world-to-screen
  matrix (used for the fit-before-render method in sections 2 and 6). VEX
  `toNDC()` is the verified route.
- That `override_camerares` alone makes the ROP honour the requested
  resolution - read back from `setup_render`, not yet confirmed by a
  measured render of its own; the dimension assert in section 3 is the
  proof each time.
- The exact MaterialX displacement node name and whether Karma XPU
  supports true displacement versus bump-only.
- Whether the ROP's color management (ACES/OCIO) is configured at all on
  this machine, and what it defaults to if not.
