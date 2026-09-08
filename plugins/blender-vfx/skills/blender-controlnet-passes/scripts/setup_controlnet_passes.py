"""
setup_controlnet_passes.py -- Blender ControlNet / AI-conditioning pass renderer.

Sets up (and optionally renders) the standard conditioning passes used to
drive AI image/video generation (depth-conditioned, edge-conditioned, or
video models such as Kling / Seedance / Veo):

  grey   - grey clay render (PNG 16-bit). View layer material override,
           world/sky lighting is preserved. Optional wireframe overlay for
           temporal consistency in video models.
  depth  - normalized depth map (PNG 16-bit, near=white / far=black).
           Normalization happens IN THE COMPOSITOR (clamp + divide).
           The camera clip range is NEVER modified -- shrinking clip_end
           clips geometry out of ALL passes, not just depth.
  crypto - multilayer EXR with Combined + CryptoObject layers for
           downstream matte extraction (Nuke Cryptomatte).

           Blender 5.x writes this as a MULTI-PART EXR: one part per
           layer (part 0 = Combined, part 1 = CryptoObject00, ...), each
           carrying the Cryptomatte manifest in its header. Nuke reads
           parts as layers. BEWARE when verifying with the OpenEXR python
           module: File.channels() / File.header() report PART 0 ONLY,
           so a perfectly good file looks like "Combined only". Iterate
           File.parts (see verify_crypto_exr below, or
           merge_exr_layers.py --inspect). A 2026-08-21 "hollow EXR"
           false alarm came from exactly this misreading.

Targets Blender 5.x APIs:
  - scene.compositing_node_group (scene.node_tree no longer exists)
  - File Output node: directory / file_name / file_output_items
  - format.media_type: a fresh File Output node defaults to
    'MULTI_LAYER_IMAGE', which LOCKS format.file_format to
    OPEN_EXR_MULTILAYER (assigning 'PNG' raises TypeError - this crashed
    every headless depth render until 2026-08-21). Set
    media_type = 'IMAGE' first for any non-EXR output. In IMAGE mode the
    item name is appended to the file name ("<name>.<Item>.png"), so the
    depth PNG is renamed to the canonical name after the render.
  - Trailing-dot file_name convention (prevents the scene frame number
    being concatenated onto the sequential counter)

Usage (CLI, background render):
  blender -b shot.blend -P setup_controlnet_passes.py -- --shot SHOT_0010 ^
      --output-root "X:/renders" --test-slice
  blender -b shot.blend -P setup_controlnet_passes.py -- --shot SHOT_0010 ^
      --output-root "X:/renders" --render --speed 0.5 --mp4

Usage (interactive / MCP execute_blender_code):
  import sys
  sys.path.append(r"<path to this scripts directory>")
  import setup_controlnet_passes as scp
  setup = scp.setup_scene(shot_name="SHOT_0010", output_root=r"X:/renders",
                          wireframe=True)
  scp.render_sequence(setup, test_slice=10)   # ALWAYS test-slice first
  scp.render_sequence(setup)                   # then the full range

Default behavior with no action flag is SETUP ONLY (no rendering).
Pass --test-slice to render a short verification slice, --render for the
full range. Render a test slice and check it before every full render.
"""

import bpy
import os
import sys
import json
import math
import time
import argparse
import subprocess

# ---------------------------------------------------------------------------
# Defaults (all overridable via CLI args or setup_scene() kwargs)
# ---------------------------------------------------------------------------

DEFAULT_SHOT_NAME = "SHOT_0010"
DEFAULT_PASSES = ("grey", "depth", "crypto")
DEFAULT_DEPTH_MAX = 100.0        # meters mapped to black in the depth PNG
DEFAULT_GREY_VALUE = 0.5         # clay base color (linear)
DEFAULT_ROUGHNESS = 0.75
DEFAULT_WIRE_PIXEL_SIZE = 1.0    # wireframe line width in pixels
DEFAULT_WIRE_VALUE = 0.08        # wireframe line color (dark grey)
DEFAULT_CRYPTO_DEPTH = 6         # cryptomatte depth -> ceil(depth/2) layers
DEFAULT_TEST_SLICE = 10          # frames rendered by a test slice

OVERRIDE_MAT_NAME = "CN_Grey_Override"
COMP_TREE_NAME = "CN_Compositor"
FO_CRYPTO_NAME = "CN File Output Crypto"
FO_DEPTH_NAME = "CN File Output Depth"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_scene_fps(scene):
    """Effective FPS from the scene. Never assume 24 -- always read this."""
    return scene.render.fps / scene.render.fps_base


def build_frame_list(start, end, speed):
    """Build (frame_int, subframe) tuples for the given speed multiplier.

    speed=1.0 renders each scene frame once. speed=0.5 doubles the output
    frame count using sub-frame interpolation (frame_set(f, subframe=0.5)),
    which gives smooth in-between motion -- useful when a video model has a
    minimum-duration constraint and the shot is too short at 1x.
    """
    if speed <= 0:
        raise ValueError("speed must be > 0")
    frame_count = end - start + 1
    output_count = int(round(frame_count / speed))
    frames = []
    for i in range(output_count):
        anim_time = start + i * speed
        frame_int = int(anim_time)
        subframe = anim_time - frame_int
        frames.append((frame_int, subframe))
    return frames


# ---------------------------------------------------------------------------
# Scene setup
# ---------------------------------------------------------------------------

def ensure_clay_material(grey_value=DEFAULT_GREY_VALUE,
                         roughness=DEFAULT_ROUGHNESS,
                         wireframe=False,
                         wire_pixel_size=DEFAULT_WIRE_PIXEL_SIZE,
                         wire_value=DEFAULT_WIRE_VALUE):
    """Create (or rebuild) the grey clay override material.

    The material is applied as a view layer material override, so it only
    replaces object materials -- the world shader (sky / HDRI lighting)
    still renders normally.

    wireframe=True mixes a Wireframe node over the clay. Mesh-locked
    wireframe lines act like a built-in edge (Canny-style) reference and
    improve temporal consistency for video models. A world-space grid was
    tried for the same purpose and rejected: it slides across animated
    objects. Note: some video models can leak visible wireframe lines into
    the generated output -- test with your target model first.
    """
    mat = bpy.data.materials.get(OVERRIDE_MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(name=OVERRIDE_MAT_NAME)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Base Color'].default_value = (grey_value, grey_value,
                                               grey_value, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = 0.0

    if wireframe:
        wire = nodes.new('ShaderNodeWireframe')
        wire.location = (-200, -150)
        wire.use_pixel_size = True
        wire.inputs['Size'].default_value = wire_pixel_size

        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.location = (0, 0)
        mix.inputs['A'].default_value = (grey_value, grey_value,
                                         grey_value, 1.0)
        mix.inputs['B'].default_value = (wire_value, wire_value,
                                         wire_value, 1.0)
        links.new(wire.outputs['Fac'], mix.inputs['Factor'])
        links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


def enable_passes(view_layer, need_depth, need_crypto,
                  crypto_depth=DEFAULT_CRYPTO_DEPTH):
    """Enable the view layer passes required by the compositor."""
    if need_depth:
        view_layer.use_pass_z = True
    if need_crypto:
        view_layer.use_pass_cryptomatte_object = True
        view_layer.pass_cryptomatte_depth = crypto_depth


def setup_compositor(scene, need_depth, need_crypto, depth_max,
                     crypto_depth=DEFAULT_CRYPTO_DEPTH,
                     depth_writer="auto"):
    """Build the compositor tree (Blender 5.x API).

    Depth chain:  Depth -> Math(MINIMUM depth_max) -> Math(DIVIDE depth_max)
                  -> Invert -> output
    This is a FIXED normalization (clamp + divide), so the mapping is
    identical on every frame -- a per-frame Normalize node re-scales to the
    frame's own min/max and flickers over an animation. The camera clip
    range is never touched: clip_end also clips geometry out of the grey
    and crypto passes (this caused missing background geometry in
    production, twice).

    depth_writer:
      "file_output" - depth PNG via a dedicated File Output node (works in
                      background/CLI renders).
      "viewer"      - depth via Viewer node + save_render() (proven in
                      interactive sessions; Viewer may not update in
                      background mode).
      "auto"        - file_output when bpy.app.background, else viewer.

    Returns dict of node references used at render time.
    """
    scene.render.use_compositing = True

    comp = scene.compositing_node_group
    if comp is None:
        # Blender 5.x: no scene.node_tree -- create a compositor node group.
        comp = bpy.data.node_groups.new(COMP_TREE_NAME,
                                        type='CompositorNodeTree')
        scene.compositing_node_group = comp
    comp.nodes.clear()

    rl = comp.nodes.new('CompositorNodeRLayers')
    rl.location = (0, 0)

    refs = {"tree": comp, "render_layers": rl,
            "fo_crypto": None, "fo_depth": None, "viewer": None,
            "depth_writer": None}

    if need_depth:
        if depth_writer == "auto":
            depth_writer = "file_output" if bpy.app.background else "viewer"
        refs["depth_writer"] = depth_writer

        # Clamp: min(depth, depth_max). ShaderNodeMath is shared with the
        # compositor in 5.x (CompositorNodeMapRange was removed).
        clamp = comp.nodes.new('ShaderNodeMath')
        clamp.operation = 'MINIMUM'
        clamp.inputs[1].default_value = depth_max
        clamp.location = (300, -50)

        divide = comp.nodes.new('ShaderNodeMath')
        divide.operation = 'DIVIDE'
        divide.inputs[1].default_value = depth_max
        divide.location = (500, -50)

        invert = comp.nodes.new('CompositorNodeInvert')
        invert.location = (700, -50)

        comp.links.new(rl.outputs['Depth'], clamp.inputs[0])
        comp.links.new(clamp.outputs[0], divide.inputs[0])
        comp.links.new(divide.outputs[0], invert.inputs['Color'])

        if depth_writer == "viewer":
            viewer = comp.nodes.new('CompositorNodeViewer')
            viewer.location = (950, -50)
            comp.links.new(invert.outputs['Color'], viewer.inputs['Image'])
            refs["viewer"] = viewer
        else:
            fo_depth = comp.nodes.new('CompositorNodeOutputFile')
            fo_depth.name = FO_DEPTH_NAME
            fo_depth.label = 'Depth PNG'
            fo_depth.location = (950, -50)
            # 5.x: media_type gates file_format. The default
            # 'MULTI_LAYER_IMAGE' rejects 'PNG' with a TypeError.
            fo_depth.format.media_type = 'IMAGE'
            fo_depth.format.file_format = 'PNG'
            fo_depth.format.color_depth = '16'
            fo_depth.format.color_mode = 'BW'
            for item in list(fo_depth.file_output_items):
                fo_depth.file_output_items.remove(item)
            fo_depth.file_output_items.new(socket_type='FLOAT', name='Depth')
            comp.links.new(invert.outputs['Color'], fo_depth.inputs[0])
            refs["fo_depth"] = fo_depth

    if need_crypto:
        fo = comp.nodes.new('CompositorNodeOutputFile')
        fo.name = FO_CRYPTO_NAME
        fo.label = 'Crypto EXR'
        fo.location = (300, -400)
        # One node, N items -> ONE multi-part EXR (one part per item).
        # Verified on 5.1.0 beta + 5.1.2 by reading every part back.
        fo.format.media_type = 'MULTI_LAYER_IMAGE'
        fo.format.file_format = 'OPEN_EXR_MULTILAYER'
        fo.format.color_depth = '32'
        fo.format.exr_codec = 'ZIPS'

        # The node starts with zero file_output_items and silently writes
        # NOTHING until items exist. Socket types: FLOAT, RGBA, VECTOR.
        for item in list(fo.file_output_items):
            fo.file_output_items.remove(item)
        fo.file_output_items.new(socket_type='RGBA', name='Combined')
        comp.links.new(rl.outputs['Image'], fo.inputs[0])

        n_layers = math.ceil(crypto_depth / 2)
        idx = 1
        for layer_i in range(n_layers):
            out_name = "CryptoObject%02d" % layer_i
            if out_name in rl.outputs:
                fo.file_output_items.new(socket_type='RGBA', name=out_name)
                # Connect by index -- name-based input lookup on the File
                # Output node is unreliable in Blender 5.1.x.
                comp.links.new(rl.outputs[out_name], fo.inputs[idx])
                idx += 1
        refs["fo_crypto"] = fo

    return refs


def setup_scene(shot_name=DEFAULT_SHOT_NAME,
                output_root=None,
                passes=DEFAULT_PASSES,
                wireframe=False,
                wire_pixel_size=DEFAULT_WIRE_PIXEL_SIZE,
                grey_value=DEFAULT_GREY_VALUE,
                roughness=DEFAULT_ROUGHNESS,
                depth_max=DEFAULT_DEPTH_MAX,
                crypto_depth=DEFAULT_CRYPTO_DEPTH,
                depth_writer="auto",
                taa_samples=None,
                motion_blur_shutter=None,
                scene=None):
    """Configure the scene for ControlNet pass rendering. No rendering here.

    Returns a setup dict to pass to render_sequence().

    Parameters
      shot_name           prefix for all output files and the shot folder
      output_root         base output directory. Default: a "controlnet"
                          folder next to the .blend file.
      passes              iterable subset of ("grey", "depth", "crypto")
      wireframe           overlay mesh wireframe on the clay material
      wire_pixel_size     wireframe line width in pixels
      grey_value          clay base grey (0-1 linear)
      roughness           clay roughness
      depth_max           distance (in scene units) mapped to black in the
                          depth PNG. Compositor-side only -- camera clip is
                          never modified.
      crypto_depth        cryptomatte depth (layers written = ceil(depth/2))
      depth_writer        "auto" | "file_output" | "viewer" (see
                          setup_compositor docstring)
      taa_samples         if not None, override EEVEE taa_render_samples
      motion_blur_shutter if not None, enable motion blur with this shutter
      scene               scene to configure (default: bpy.context.scene)
    """
    scene = scene or bpy.context.scene
    passes = tuple(p.strip().lower() for p in passes)
    for p in passes:
        if p not in ("grey", "depth", "crypto"):
            raise ValueError("Unknown pass '%s' (grey, depth, crypto)" % p)
    if not passes:
        raise ValueError("At least one pass is required")

    if output_root is None:
        blend_dir = os.path.dirname(bpy.data.filepath)
        if not blend_dir:
            raise ValueError("Blend file not saved -- pass output_root "
                             "explicitly")
        output_root = os.path.join(blend_dir, "controlnet")

    shot_dir = os.path.join(output_root, shot_name)
    dirs = {"shot": shot_dir}
    for p in passes:
        dirs[p] = os.path.join(shot_dir, p)
        os.makedirs(dirs[p], exist_ok=True)
    if "grey" in passes:
        dirs["grey_mp4"] = os.path.join(shot_dir, "grey_mp4")

    vl = scene.view_layers[0]

    # Grey clay override. Only object materials are replaced -- world/sky
    # lighting renders normally.
    mat = ensure_clay_material(grey_value=grey_value, roughness=roughness,
                               wireframe=wireframe,
                               wire_pixel_size=wire_pixel_size)
    vl.material_override = mat

    enable_passes(vl, "depth" in passes, "crypto" in passes,
                  crypto_depth=crypto_depth)

    comp_refs = setup_compositor(scene,
                                 need_depth="depth" in passes,
                                 need_crypto="crypto" in passes,
                                 depth_max=depth_max,
                                 crypto_depth=crypto_depth,
                                 depth_writer=depth_writer)

    # Still-image render settings for the main (grey) output.
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_depth = '16'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.use_sequencer = False
    scene.render.use_compositing = True

    # Optional temporal-stability overrides. Left untouched by default;
    # see the skill notes before changing these on a working scene.
    if taa_samples is not None and hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = taa_samples
    if motion_blur_shutter is not None:
        scene.render.use_motion_blur = True
        scene.render.motion_blur_shutter = motion_blur_shutter

    fps = get_scene_fps(scene)
    print("[setup] shot=%s passes=%s fps=%.3f res=%dx%d out=%s" % (
        shot_name, ",".join(passes), fps,
        scene.render.resolution_x, scene.render.resolution_y, shot_dir))

    return {
        "scene": scene,
        "view_layer": vl,
        "shot_name": shot_name,
        "passes": passes,
        "dirs": dirs,
        "comp": comp_refs,
        "fps": fps,
        "depth_max": depth_max,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def verify_crypto_exr(path, expected_layers):
    """Read back the layer list of a freshly written crypto EXR.

    Uses the OpenEXR python module if this interpreter has it (Blender's
    bundled python usually does not - then the check is skipped with a
    notice, never a false PASS). Reads EVERY part: Blender 5.x writes one
    part per layer and File.channels() alone only shows part 0.

    Returns (ok, found_layers) where ok is None when the check could not
    run.
    """
    try:
        import OpenEXR
    except ImportError:
        return None, []
    found = []
    exr = OpenEXR.File(path, separate_channels=True)
    for part in exr.parts:
        for chan in part.channels.keys():
            layer = chan.rsplit(".", 1)[0]
            if layer not in found:
                found.append(layer)
    missing = [l for l in expected_layers if l not in found]
    return not missing, found


def _render_one(setup, frame_int, subframe, seq_str):
    """Render a single output frame: grey PNG + depth PNG + crypto EXR."""
    scene = setup["scene"]
    dirs = setup["dirs"]
    shot = setup["shot_name"]
    comp = setup["comp"]

    scene.frame_set(frame_int, subframe=subframe)

    write_still = "grey" in setup["passes"]
    if write_still:
        scene.render.filepath = os.path.join(
            dirs["grey"], "%s_grey_%s" % (shot, seq_str))

    # File Output nodes append the SCENE frame number to file_name unless
    # the name ends with a dot: "name_0001" + frame 276 -> "name_00010276".
    # The trailing dot keeps our sequential counter intact.
    crypto_path = None
    if comp["fo_crypto"] is not None:
        comp["fo_crypto"].directory = dirs["crypto"] + os.sep
        comp["fo_crypto"].file_name = "%s_crypto_%s." % (shot, seq_str)
        crypto_path = os.path.join(dirs["crypto"],
                                   "%s_crypto_%s.exr" % (shot, seq_str))
    depth_tmp = depth_final = None
    if comp["fo_depth"] is not None:
        comp["fo_depth"].directory = dirs["depth"] + os.sep
        comp["fo_depth"].file_name = "%s_depth_%s." % (shot, seq_str)
        # IMAGE media type appends the item name: "<name>.Depth.png".
        depth_tmp = os.path.join(dirs["depth"],
                                 "%s_depth_%s.Depth.png" % (shot, seq_str))
        depth_final = os.path.join(dirs["depth"],
                                   "%s_depth_%s.png" % (shot, seq_str))

    bpy.ops.render.render(write_still=write_still)

    if depth_tmp is not None:
        if not os.path.isfile(depth_tmp):
            raise RuntimeError("depth PNG not written: %s" % depth_tmp)
        os.replace(depth_tmp, depth_final)

    if crypto_path is not None:
        if not os.path.isfile(crypto_path):
            raise RuntimeError("crypto EXR not written: %s" % crypto_path)
        # Check PRODUCED CONTENT on the first frame of every run, not just
        # that a file appeared: every File Output item must be a part.
        if seq_str == "0001":
            expected = [it.name for it in comp["fo_crypto"].file_output_items]
            ok, found = verify_crypto_exr(crypto_path, expected)
            if ok is None:
                print("  crypto read-back skipped (no OpenEXR module in "
                      "this python) - check with merge_exr_layers.py "
                      "--inspect")
            elif ok:
                print("  crypto read-back OK: parts=%s" % found)
            else:
                raise RuntimeError("crypto EXR missing layers: expected %s, "
                                   "found %s" % (expected, found))

    # Viewer-based depth extraction (interactive sessions).
    if comp["viewer"] is not None:
        viewer_img = bpy.data.images.get('Viewer Node')
        if viewer_img and viewer_img.size[0] > 0:
            depth_path = os.path.join(
                dirs["depth"], "%s_depth_%s.png" % (shot, seq_str))
            viewer_img.save_render(filepath=depth_path, scene=scene)


def encode_mp4(png_dir, name_prefix, mp4_dir, total_frames, fps):
    """Encode a PNG sequence to MP4 with ffmpeg. Returns path or None."""
    os.makedirs(mp4_dir, exist_ok=True)
    mp4_path = os.path.join(mp4_dir, "%s.mp4" % name_prefix)
    png_pattern = os.path.join(png_dir, "%s_%%04d.png" % name_prefix)
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-start_number", "1",
            "-i", png_pattern,
            "-frames:v", str(total_frames),
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            mp4_path,
        ], check=True, capture_output=True)
        print("  MP4: %s" % mp4_path)
        return mp4_path
    except FileNotFoundError:
        print("  WARNING: ffmpeg not found. PNGs remain at: %s" % png_dir)
        return None
    except subprocess.CalledProcessError as exc:
        err = exc.stderr[:200] if exc.stderr else exc
        print("  WARNING: ffmpeg failed: %s" % err)
        return None


def _outputs_exist(setup, seq_str):
    """True if every enabled pass already has its output file for seq_str."""
    dirs = setup["dirs"]
    shot = setup["shot_name"]
    checks = []
    if "grey" in setup["passes"]:
        checks.append(os.path.join(dirs["grey"], "%s_grey_%s.png" % (shot, seq_str)))
    if "depth" in setup["passes"]:
        checks.append(os.path.join(dirs["depth"], "%s_depth_%s.png" % (shot, seq_str)))
    if "crypto" in setup["passes"]:
        checks.append(os.path.join(dirs["crypto"], "%s_crypto_%s.exr" % (shot, seq_str)))
    return bool(checks) and all(os.path.exists(p) for p in checks)


def render_sequence(setup,
                    frame_start=None,
                    frame_end=None,
                    speed=1.0,
                    min_duration=0.0,
                    test_slice=0,
                    make_mp4=False,
                    restore_override=True,
                    skip_existing=False):
    """Render the sequence using a setup dict from setup_scene().

    frame_start/end  default to the scene frame range
    speed            1.0 = real time; 0.5 = half speed via sub-frame
                     interpolation (doubles the output frame count)
    min_duration     seconds; if the output is shorter, the last frame is
                     repeated (tail-hold) to reach it. 0 disables padding.
                     Useful for video models with a minimum clip length.
    test_slice       if > 0, render only the first N output frames into a
                     separate "<shot>_TEST" folder. ALWAYS run a test slice
                     and inspect it before committing to a full render --
                     a wrong setting on a long sequence wastes hours.
    make_mp4         encode the grey PNGs to MP4 at the SCENE fps
    restore_override the material override is removed after rendering
    skip_existing    skip frames whose output files already exist. CRASH
                     RECOVERY: long python render loops through the MCP have
                     hung Blender with runaway memory (28 GB at frame 116 of
                     118 in production). If that happens, restart Blender,
                     re-run setup_scene, then re-run render_sequence with
                     skip_existing=True -- only missing frames render.
                     Prefer chunked calls (frame_start/frame_end in 20-40
                     frame slices) for long sequences driven via MCP.

    Returns a manifest dict (also written as JSON next to the shot folder).
    """
    scene = setup["scene"]
    fps = setup["fps"]
    shot = setup["shot_name"]
    dirs = dict(setup["dirs"])

    start = frame_start if frame_start is not None else scene.frame_start
    end = frame_end if frame_end is not None else scene.frame_end

    frames = build_frame_list(start, end, speed)

    is_test = test_slice and test_slice > 0
    if is_test:
        frames = frames[:test_slice]
        # Redirect output to a sibling TEST folder so test frames never
        # mix with (or overwrite) a real delivery.
        test_shot_dir = dirs["shot"] + "_TEST"
        run_setup = dict(setup)
        new_dirs = {"shot": test_shot_dir}
        for key in setup["passes"]:
            new_dirs[key] = os.path.join(test_shot_dir, key)
            os.makedirs(new_dirs[key], exist_ok=True)
        if "grey_mp4" in dirs:
            new_dirs["grey_mp4"] = os.path.join(test_shot_dir, "grey_mp4")
        run_setup["dirs"] = new_dirs
        dirs = new_dirs
        setup = run_setup

    rendered = len(frames)
    target_frames = int(round(fps * min_duration)) if min_duration > 0 else 0
    padding = max(0, target_frames - rendered) if not is_test else 0
    total = rendered + padding

    print("\n" + "=" * 60)
    print("ControlNet pass render -- %s%s" % (shot,
                                              " (TEST SLICE)" if is_test else ""))
    print("Frames %d-%d at %sx speed -> %d rendered + %d padded = %d"
          % (start, end, speed, rendered, padding, total))
    print("Duration: %.2fs @ %.3f fps" % (total / fps, fps))
    print("Output: %s" % dirs["shot"])
    print("=" * 60)

    t0 = time.time()
    skipped = 0
    for i, (frame_int, subframe) in enumerate(frames):
        seq_str = "%04d" % (i + 1)
        if skip_existing and _outputs_exist(setup, seq_str):
            skipped += 1
            continue
        _render_one(setup, frame_int, subframe, seq_str)
        if (i + 1) % 10 == 0 or i == 0:
            elapsed = time.time() - t0
            avg = elapsed / (i + 1)
            remaining = avg * (total - i - 1)
            print("[%d/%d] f%d+%.2f -- %.0fs elapsed, ~%.0fs left"
                  % (i + 1, total, frame_int, subframe, elapsed, remaining))

    if padding > 0:
        last_int, last_sub = frames[-1]
        for p in range(padding):
            seq_str = "%04d" % (rendered + p + 1)
            _render_one(setup, last_int, last_sub, seq_str)

    render_time = time.time() - t0
    if skipped:
        print("Skipped %d existing frames (skip_existing)" % skipped)
    print("Rendered %d frames in %.0fs (%.2fs/frame)"
          % (total - skipped, render_time,
             render_time / max(total - skipped, 1)))

    mp4_path = None
    if make_mp4 and "grey" in setup["passes"]:
        mp4_path = encode_mp4(dirs["grey"], "%s_grey" % shot,
                              dirs.get("grey_mp4", dirs["shot"]),
                              total, fps)

    if restore_override:
        setup["view_layer"].material_override = None

    manifest = {
        shot: {
            "test_slice": bool(is_test),
            "frame_start": start,
            "frame_end": end,
            "speed": speed,
            "fps": fps,
            "rendered_frames": rendered,
            "padding_count": padding,
            "total_frames": total,
            "duration_seconds": total / fps,
            "camera": scene.camera.name if scene.camera else None,
            "passes": list(setup["passes"]),
            "dirs": {k: v for k, v in dirs.items()},
            "grey_mp4": mp4_path,
        }
    }
    manifest_path = os.path.join(dirs["shot"], "%s_manifest.json" % shot)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print("Manifest: %s" % manifest_path)
    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="setup_controlnet_passes.py",
        description="Set up and render ControlNet conditioning passes. "
                    "Pass args after '--' on the blender command line.")
    parser.add_argument("--shot", default=DEFAULT_SHOT_NAME,
                        help="shot name / output file prefix")
    parser.add_argument("--output-root", default=None,
                        help="base output dir (default: 'controlnet' folder "
                             "next to the .blend file)")
    parser.add_argument("--passes", default=",".join(DEFAULT_PASSES),
                        help="comma list of passes: grey,depth,crypto")
    parser.add_argument("--frame-start", type=int, default=None,
                        help="default: scene frame_start")
    parser.add_argument("--frame-end", type=int, default=None,
                        help="default: scene frame_end")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="1.0 real time, 0.5 half speed (sub-frame "
                             "interpolation, doubles frame count)")
    parser.add_argument("--min-duration", type=float, default=0.0,
                        help="seconds; tail-hold pad output to at least "
                             "this duration (0 = off)")
    parser.add_argument("--wireframe", action="store_true",
                        help="overlay mesh wireframe on the clay material")
    parser.add_argument("--wire-pixel-size", type=float,
                        default=DEFAULT_WIRE_PIXEL_SIZE)
    parser.add_argument("--grey-value", type=float,
                        default=DEFAULT_GREY_VALUE)
    parser.add_argument("--roughness", type=float, default=DEFAULT_ROUGHNESS)
    parser.add_argument("--depth-max", type=float, default=DEFAULT_DEPTH_MAX,
                        help="distance mapped to black in the depth PNG "
                             "(compositor-side; camera clip is untouched)")
    parser.add_argument("--crypto-depth", type=int,
                        default=DEFAULT_CRYPTO_DEPTH,
                        help="cryptomatte depth (layers = ceil(depth/2))")
    parser.add_argument("--depth-writer", default="auto",
                        choices=["auto", "file_output", "viewer"])
    parser.add_argument("--taa-samples", type=int, default=None,
                        help="override EEVEE TAA render samples (optional)")
    parser.add_argument("--motion-blur", type=float, default=None,
                        metavar="SHUTTER",
                        help="enable motion blur with this shutter value")
    parser.add_argument("--mp4", action="store_true",
                        help="encode grey PNGs to MP4 (needs ffmpeg on PATH)")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--render", action="store_true",
                        help="render the full frame range")
    action.add_argument("--test-slice", nargs="?", type=int,
                        const=DEFAULT_TEST_SLICE, default=None, metavar="N",
                        help="render only the first N frames (default %d) "
                             "into a _TEST folder for verification"
                             % DEFAULT_TEST_SLICE)
    return parser.parse_args(argv)


def main():
    # Blender passes everything after '--' through to the script.
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parse_args(argv)

    setup = setup_scene(
        shot_name=args.shot,
        output_root=args.output_root,
        passes=args.passes.split(","),
        wireframe=args.wireframe,
        wire_pixel_size=args.wire_pixel_size,
        grey_value=args.grey_value,
        roughness=args.roughness,
        depth_max=args.depth_max,
        crypto_depth=args.crypto_depth,
        depth_writer=args.depth_writer,
        taa_samples=args.taa_samples,
        motion_blur_shutter=args.motion_blur,
    )

    if args.test_slice is not None:
        render_sequence(setup,
                        frame_start=args.frame_start,
                        frame_end=args.frame_end,
                        speed=args.speed,
                        min_duration=args.min_duration,
                        test_slice=args.test_slice,
                        make_mp4=args.mp4)
    elif args.render:
        render_sequence(setup,
                        frame_start=args.frame_start,
                        frame_end=args.frame_end,
                        speed=args.speed,
                        min_duration=args.min_duration,
                        make_mp4=args.mp4)
    else:
        print("[setup only] Scene configured -- no frames rendered.")
        print("Re-run with --test-slice to verify, then --render for the "
              "full range.")


if __name__ == "__main__":
    main()
