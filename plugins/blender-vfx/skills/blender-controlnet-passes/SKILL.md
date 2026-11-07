---
name: blender-controlnet-passes
description: "Renders ControlNet conditioning passes from a Blender scene for AI image and video generation - grey clay, normalized depth, cryptomatte EXR, optional wireframe. Use when preparing depth, edge or clay inputs for video models, or crypto mattes for comp."
---

# Blender ControlNet Passes

**Version:** 1.1.2 | **Last Updated:** 2026-10-30 | **Blender:** 5.x (1.1.2: gotchas 12, 15, 16 - obs 240, 241)

One parameterized script replaces the per-project pass-render scripts:
`scripts/setup_controlnet_passes.py` (relative to this skill directory)

Outputs per shot: `<root>/<shot>/grey/` (16-bit PNG clay), `<root>/<shot>/depth/`
(16-bit PNG, near=white/far=black, fixed normalization), `<root>/<shot>/crypto/`
(multilayer EXR: Combined + CryptoObject layers), optional grey MP4, and a
`<shot>_manifest.json`.

## Script vs MCP-interactive setup

- **Use the script** for anything repeatable: full sequences, batch/CLI
  background renders, half-speed re-renders, or when a scene needs the
  standard grey/depth/crypto setup from scratch. Import it via MCP too --
  do not re-derive the compositor graph by hand.
- **Use MCP-interactive** only for scene-specific prep the script cannot
  know about: hiding locator meshes, switching shot collections/cameras,
  inspecting why a render looks wrong. Then call the script's functions.

### CLI (background render)

```
blender -b shot.blend -P setup_controlnet_passes.py -- --shot SHOT_0010 --output-root "X:/renders" --test-slice
blender -b shot.blend -P setup_controlnet_passes.py -- --shot SHOT_0010 --output-root "X:/renders" --render --speed 0.5 --mp4
```

### MCP (execute_blender_code)

```python
import sys
sys.path.append(r"<workspace>/Blender/scripts")
import setup_controlnet_passes as scp
setup = scp.setup_scene(shot_name="SHOT_0010", output_root=r"X:/renders")
scp.render_sequence(setup, test_slice=10)   # verify first
scp.render_sequence(setup)                   # then full range
```

With no action flag the CLI does **setup only** (no rendering). `--test-slice`
renders N frames (default 10) into a sibling `<shot>_TEST` folder; `--render`
does the full range.

## Parameters

| Param (CLI / setup_scene) | Default | Meaning |
|---|---|---|
| `--shot` / `shot_name` | SHOT_0010 | file prefix + shot folder name |
| `--output-root` / `output_root` | `controlnet/` next to .blend | base output dir |
| `--passes` / `passes` | grey,depth,crypto | subset of the three passes |
| `--frame-start` `--frame-end` | scene range | render range |
| `--speed` | 1.0 | 0.5 = half speed via `frame_set(f, subframe=)` sub-frame interpolation (for video-model minimum durations) |
| `--min-duration` | 0 | seconds; tail-hold pad the last frame to reach it |
| `--wireframe` + `--wire-pixel-size` | off / 1.0 px | wireframe overlay on clay |
| `--grey-value` `--roughness` | 0.5 / 0.75 | clay material |
| `--depth-max` / `depth_max` | 100.0 | distance mapped to black (compositor-side) |
| `--crypto-depth` | 6 | cryptomatte depth; EXR layers = ceil(depth/2) |
| `--depth-writer` | auto | file_output (background-safe) or viewer (interactive) |
| `--taa-samples` `--motion-blur` | untouched | optional EEVEE stability overrides |
| `--mp4` / `make_mp4` | off | ffmpeg encode of grey PNGs at SCENE fps |
| `--test-slice [N]` / `test_slice` | off | render first N frames to `<shot>_TEST` |

## GOTCHAS (production-earned; do not relearn these)

1. **Depth clip_end trap.** Never tighten `camera.data.clip_end` to shape the
   depth map. Clip range clips geometry out of ALL passes -- background
   buildings vanished from the grey render in production, twice. Depth range
   is shaped in the compositor only: `Depth -> Math(MIN depth_max) ->
   Math(DIVIDE depth_max) -> Invert`. Fixed mapping, no per-frame Normalize
   (per-frame min/max flickers over an animation).
2. **Trailing-dot file naming.** File Output nodes append the scene frame
   number to `file_name`. `name_0001` + frame 276 becomes `name_00010276`
   (the 960000-range frames bug). Always end `file_name` with `.` --
   `name_0001.` writes `name_0001.exr`. The script does this everywhere.

   **This applies to `file_name` ONLY, and it still holds on 5.1.2** (verified
   headless 2026-08-17: `shot_depth_0001.` round-trips unchanged). Do not
   extend the trailing dot to `file_output_items` names -- those ARE sanitised,
   so an item named `depth.` silently becomes `depth_`. The script names its
   items `Depth` / `Combined` / crypto layer names, which is correct. If you
   ever set an item name, read it back.
3. **Blender 5.x compositor access.** `scene.node_tree` is gone. Use
   `scene.compositing_node_group`; create it with
   `bpy.data.node_groups.new(name, type='CompositorNodeTree')`. There is no
   Composite node; the main output comes from `scene.render.filepath`.
   Details: `references/blender5_api_notes.md`.
4. **File Output items.** The node starts with zero `file_output_items` and
   silently writes nothing. Add items (`socket_type` FLOAT/RGBA/VECTOR),
   then connect by input INDEX, not name.
5. **FPS from the scene.** Duration math and MP4 encode use
   `scene.render.fps / scene.render.fps_base`. Never assume 24.
6. **Test-slice discipline.** Always render ~10 frames and inspect them
   before a full render. A wasted session re-rendered 4 x 216 frames chasing
   settings; change ONE variable per re-render.
7. **Wireframe for temporal consistency.** A mesh-locked wireframe overlay
   acts like a built-in Canny reference and stabilizes video-model output.
   Do NOT use a world-space grid (it slides across animated objects). Some
   models leak wireframe lines into output -- test with the target model.
8. **Depth writer mode.** Viewer-node extraction is the proven interactive
   path but Viewer images may not update in `blender -b`. The script
   auto-selects a File Output PNG node in background mode (`--depth-writer`
   overrides). If background depth PNGs come out empty, verify this first.
   **Fixed 2026-08-21:** this path crashed on every 5.1.x headless run
   (`TypeError: enum "PNG" not found in ('OPEN_EXR_MULTILAYER')`) because a
   fresh File Output node's `format.media_type` is `MULTI_LAYER_IMAGE`. The
   script now sets `media_type = 'IMAGE'` first; in IMAGE mode the item name
   is appended (`shot_depth_0001.Depth.png`) and the script renames to the
   canonical `shot_depth_0001.png` after each frame. Verified headless on
   5.1.2 (16-bit `I;16` PNGs, 1363 distinct values on the test scene).
9. **Verify pixel CONTENT, never just file existence.** A render that wrote
   4 KB of PNG is not a render that shows anything. Two traps caught a
   headless run on 2026-08-16: a clay pass came out a single flat value
   (uniform frame - and a uniform frame passes an "R=G=B within 1 LSB" grey
   check trivially, so the check awards a free point), and the depth pass
   came out uniformly 0.0 because the normalization range was INVENTED
   (30-80 m) for objects actually sitting 2-15 m from camera. Measure the
   real object distances (`(ob.location - cam.location).length`) and derive
   the range from them; then assert the written frame has more than a
   couple of distinct values before calling the pass good.
10. **EEVEE temporal jitter.** TAA sub-pixel jitter shows up as noise in
   tracking curves; `taa_render_samples=1` kills jitter but looks aliased
   and was judged worse in production. Leave scene sampling alone unless
   testing deliberately (`--taa-samples`, `--motion-blur` exist for that).
11. **Long MCP-driven render loops can hang Blender with runaway memory.**
    A 118-frame grey render through the MCP crept from 4.5s to 58s/frame
    and wedged Blender at 28 GB RAM on frame 116 (large arena crowd scene).
    Mitigations: chunk `render_sequence` calls (20-40 frames per call via
    `frame_start`/`frame_end` -- seq numbering is derived from the full
    range so chunks stay consistent only if you pass the SAME full range
    and use `skip_existing=True`), or recover after a crash by re-running
    with `skip_existing=True` (renders only missing frames). Straight
    beauty/pass renders with no subframe/speed tricks are safer via
    Blender's native animation render (`INVOKE_DEFAULT`), which held
    steady for 118-frame 4K renders in the same sessions.
12. **Dark scenes render near-black clay; an UNLIT scene renders flat clay.**
    The override preserves scene lighting; a dark stage/arena scene that HAS
    lights gives an unreadable conditioning frame. Temporarily set the world
    Background to flat grey (color 0.5 / strength 1.0), render, restore. But a
    scene with NO lights (the asset's lights sit in excluded collections) under
    that flat world came out 137-170 of 255 over the whole frame: seat backs,
    pans and background within about 30 levels, forms barely readable, while
    the not-blank and not-uniform checks passed. For such a scene add an
    in-memory soft SUN (angle 12 deg, strength 3, from high behind the camera,
    direction (0, 0.6, -0.8)) and drop the world to 0.25: 99-179 with readable
    forms and contact shadows, render time unchanged. Apply it in the render
    session only (a sun from behind/above camera minimises cast-shadow
    confusion). Add a READABILITY gate next to gotcha 9: p5-p95 spread of the
    grey pass above 50 levels, judged on a CG-only preview too.
13. **ffmpeg on Windows.** `encode_mp4` calls plain "ffmpeg"; if Blender's
    environment lacks it the script warns and leaves PNGs. A working copy
    often hides at `C:\Program Files\ImageMagick-*\ffmpeg.exe`. Also
    ensure the `grey_mp4` directory exists before an external encode --
    ffmpeg does not create missing output directories.
14. **Multilayer EXRs are multi-part - check ALL parts before calling one
    hollow.** Blender 5.x writes one EXR part per layer. The OpenEXR python
    module's `File.channels()` / `File.header()` show part 0 only, so an
    intact crypto EXR reads as "Combined RGBA and nothing else". On
    2026-08-21 this produced a confident, wrong "5.1.x File Output drops all
    but the first item" diagnosis against 312 production frames (and a
    merge-based rewrite of this script that was reverted). Instrument:
    `python scripts/merge_exr_layers.py --inspect <file.exr>` lists
    every part; the script's `verify_crypto_exr()` does the same on frame
    0001 when the calling python has OpenEXR (Blender's bundled python does
    not - it prints a skip notice, never a false PASS). Rule 8 in action:
    a too-clean "only Combined" result is the instrument, not the file.
15. **Passes that go back into comp over a plate need the plate's frame
    numbers.** `render_sequence()` names outputs by a sequential counter
    (`_0001`...), so a plate shot running 981-1396 comes out 0001-0416 and
    renaming 416 x 2 files afterwards is a MOVE.
16. **Never point a script that renames its own outputs at a no-move
    (write-only) share.** The depth path writes `<name>.Depth.png` and then
    renames it to the canonical name; that rename happens inside Blender, where
    a path hook does not see it, so it silently breaks a no-move/no-delete rule
    when the output root is on such a share. Render to a LOCAL drive (naming each
    frame with its plate frame number up front, not renaming later), then copy
    to the share.

17. **Prove a flat colour-ID pass before a paid reskin.** Key the palette on the
    asset id, colour every non-target subject one flat colour, and run
    `scripts/check_id_pass.py`: every key has pixels, no other-subject or unknown
    flat colour, predicted feature positions, depth, and edges on the grey render.

## References

- `references/blender5_api_notes.md` -- Blender 5.x API details (compositor
  node group, File Output API, layered Actions, removed nodes).
