# Houdini patterns for the loop

Not yet exercised by a real run (no Houdini leg of loop-gauntlet has happened
as of this writing). Distilled instead from this workspace's Houdini MCP
facts (`.claude/rules/houdini.md`, memory `project_houdini_mcp.md` and
`technical_houdini_nuke_patterns.md`) and from the fxhoudinimcp tool
descriptions themselves. All snippets are Python (HOM, the `hou` module),
ASCII, raw-string Windows paths, and assume the working folder and view list
come from the spec. Anything not confirmed by those sources is flagged
UNVERIFIED at the point it comes up, and again in the list at the end -
do not invent an API name to fill a gap.

## 1. Scene layout and the version-save ritual

- One `/obj` geo node per object in the build, named for what it is
  (`/obj/PLINTH`, `/obj/DRUM_INNER`), never `geo1`, `geo2`. Inside each geo
  node, a SOP chain that reads top to bottom as a plan: a source primitive,
  then modifiers, ending in an `output` node with the display and render
  flags set. Name SOPs for their job (`source_grid`, `deform_relief`,
  `output`), not their type-plus-number default.
- Read state back before creating, same rule as Blender: `hou.node(path)`
  first; if it returns an object, update its parameters rather than
  creating a sibling that Houdini will suffix `_1`. `build_network` in
  fxhoudinimcp takes a whole planned graph in one call and is the atomic
  equivalent of the Blender timer-queue pattern - it validates every node
  type and parameter name against the running Houdini before touching the
  scene when called with `dry_run=True`, so use `dry_run` first for any
  node type not already used this session.
- Version-save ritual, same house rule as Blender ("DCC can hang under
  agent control"): save an increment before every render or heavy
  operation.

  ```python
  import hou
  from pathlib import Path

  WORK = Path(r"D:/work/my_loop")          # from the spec
  NAME = "museum_props"                     # from the spec
  hip_dir = WORK / "houdini"
  hip_dir.mkdir(parents=True, exist_ok=True)

  existing = sorted(hip_dir.glob(NAME + "_v*.hip"))
  next_n = len(existing) + 1
  out = hip_dir / (NAME + "_v%03d.hip" % next_n)
  if out.exists():
      raise RuntimeError("version file already exists: " + str(out))
  hou.hipFile.save(file_name=str(out))
  # read back: reopen the path Houdini itself now reports
  assert hou.hipFile.path() == str(out), "save did not update the current hip path"
  ```

  UNVERIFIED: whether `hou.hipFile.save()` accepts a `file_name` keyword or
  a positional argument in the Houdini version this workspace runs (21.0) -
  confirm with `get_node_card`/`get_help_page` on `hom/hou.hipFile` before
  relying on the call shape above; the pattern (increment, then read
  `hou.hipFile.path()` back) is the part to keep regardless of the exact
  signature.

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
  camera's `hou.Camera.worldToCamera()`/perspective matrix, or equivalently
  build the same `u, v` formula from `matrix_world`, `focal`, and
  `aperture`) rather than trusting the estimate from a single render.
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
- Engine and device: **XPU vs CPU is UNVERIFIED on this machine.** The
  workspace's Houdini rules file documents `render_specific_camera(...,
  render_engine="karma", karma_engine="cpu")` as a working call through the
  legacy tool set, but does not confirm Karma XPU availability, a working
  XPU device string, or which GPU (if any) Karma XPU would target here.
  Before trusting an XPU render as the loop's fast path: submit one small
  scratch frame with XPU requested, read the ROP's own render log or
  `get_render_progress`/`get_node_errors_detailed` for a fallback-to-CPU
  warning, and only then adopt XPU as the loop setting. If XPU is
  unavailable or unconfirmed, fall back to Karma CPU at a reduced sample
  count and record that choice in SCENE_BRIEF.md rather than silently
  eating the slower render time every iteration.
- PNG output from a ROP is also UNVERIFIED here: the workspace's own render
  tools (`render_single_view`, `render_specific_camera`, the legacy MCP)
  are documented as writing JPG to `C:/temp/`, not PNG to a caller-chosen
  path. Before relying on `renders/<tag>_<view>.png` existing at all,
  confirm the Karma ROP's own output-picture parameter accepts a `.png`
  extension and writes to the working folder's `renders\` directory (query
  the ROP's parameters with `get_node_card` rather than assuming a
  `vm_picture` -style name is still current in this Houdini version), and
  do a one-frame scratch render to prove it before the first real
  iteration render.
- Render call and read-back:

  ```python
  import hou
  from pathlib import Path

  ROP = "/out/karma_loop"                  # or a LOP-network path
  TAG = "iter01"                            # from the loop
  VIEW = "hero"                             # from the spec
  OUT = Path(r"D:/work/my_loop/renders") / (TAG + "_" + VIEW + ".png")
  if OUT.exists():
      raise RuntimeError("output already exists: " + str(OUT))   # never overwrite evidence

  rop = hou.node(ROP)
  rop.parm("camera").set("/obj/CAM_" + VIEW)
  rop.parm("picture").set(str(OUT))         # UNVERIFIED parm name - confirm via get_node_card
  rop.parm("resolutionx").set(1376)
  rop.parm("resolutiony").set(768)
  rop.render()                              # blocking; see the timeout note below

  st = OUT.stat()                           # raises if the file was never written
  print("bytes=%s mtime=%s" % (st.st_size, st.st_mtime))
  ```

- **Timeout risk carries over from Blender.** The Blender file's whole
  first pattern exists because an inline render of six views through the
  MCP execute call exceeds the tool timeout. `hou.node(...).render()` is
  just as blocking in HOM; render one view per MCP call rather than a loop
  of views in a single call, and if a single view still risks the timeout
  at final-pass sample counts, use the same non-blocking pattern (a
  `hou.ui.addEventLoopCallback` or a background `hython` subprocess writing
  a status JSON the caller polls) rather than assuming HOM has a built-in
  async render call - it does not.
- **Read-back after the render, not after the call returns.** A `0`
  return or no exception from `rop.render()` is a completion signal, not a
  correctness signal (operating rule 2). Read the file back: size, mtime,
  and pixel content.

  ```python
  from PIL import Image
  im = Image.open(str(OUT)).convert("RGB")
  w, h = im.size
  colors = im.getcolors(maxcolors=w * h)
  unique_values = len(colors) if colors else "many"
  print("size=%sx%s unique_values=%s" % (w, h, unique_values))
  ```

  A flat or black frame (few unique values) means the active camera was
  wrong, the ROP's display path pointed at the wrong node, or the render
  never actually ran through Karma - the same suspect-blank check
  `compare_views.py` already runs on the read-back PNG.

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
  without checking `hou.node(path)` first.
- **Part counts and bounding boxes:**

  ```python
  node = hou.node("/obj/DRUM_INNER/output")
  geo = node.geometry()
  bbox = geo.boundingBox()
  print("points=%s prims=%s bbox_min=%s bbox_max=%s" %
        (len(geo.points()), len(geo.prims()), bbox.minvec(), bbox.maxvec()))
  ```

  Compare against the human-scale anchors in the brief (bench 0.45 m,
  door 2.1 m) the same way the Blender file expects a raycast to confirm
  circulation routes connect - a bounding box in the wrong units (Houdini
  defaults to metres already, but an imported asset may not) is caught
  here, not at render time.
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
  render. This is the same discipline as the Blender file's section 10,
  just without Blender-specific compositor facts to carry over - Karma's
  own color management (ACES/OCIO on the ROP, if configured) is a candidate
  place for the same kind of silent-wrong-output trap the Blender
  compositor produced, and is UNVERIFIED here: confirm the ROP's color
  space setting before trusting a render's apparent exposure.

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

## UNVERIFIED

Confirm each of these against the running Houdini (via `get_node_card`,
`search_help`, or a scratch test) before trusting it in a real loop run -
none of them is confirmed by the files read for this reference or by the
fxhoudinimcp tool descriptions alone:

- Karma XPU availability, device selection, and whether it silently falls
  back to CPU on this machine.
- Whether a Karma ROP can write PNG directly (the workspace's documented
  render tools write JPG to `C:/temp/`, not a caller-chosen PNG path).
- The exact `hou.hipFile.save()` call shape used for version increments in
  this Houdini version.
- The exact HOM method for reading a camera's projection/world-to-screen
  matrix (used for the fit-before-render method in section 2 and 6).
- The exact MaterialX displacement node name and whether Karma XPU
  supports true displacement versus bump-only.
- Whether the ROP's color management (ACES/OCIO) is configured at all on
  this machine, and what it defaults to if not.
- SAVE BEFORE EVERY RENDER (Rob, 2026-09-12): the hip must be saved to its
  versioned path before a Karma ROP render is launched; never render from an
  untitled or unsaved hip. husk reads the scene from disk, so an unsaved
  scene renders stale or missing state. Order per iteration: build, save
  vNNN, render, poll, read back.
