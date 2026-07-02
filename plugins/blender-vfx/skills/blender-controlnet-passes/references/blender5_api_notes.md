# Blender 5.x API Notes for Pass Rendering

Verified on Blender 5.1.2. Companion to `Blender/scripts/setup_controlnet_passes.py`.

## Compositor node tree

- `scene.node_tree` no longer exists. The compositor lives in
  `scene.compositing_node_group`.
- It is None until you assign one:

```python
comp = scene.compositing_node_group
if comp is None:
    comp = bpy.data.node_groups.new("Compositor", type='CompositorNodeTree')
    scene.compositing_node_group = comp
```

- There is no `CompositorNodeComposite` node. The main render output is
  written from `scene.render.filepath` directly; the compositor is only
  needed for extra outputs (File Output nodes, Viewer).
- `CompositorNodeMapRange` was removed. `ShaderNodeMath` is a shared node
  type and works inside compositor trees -- use MINIMUM + DIVIDE for fixed
  depth normalization.
- Setting `scene.render.use_compositing = True` is still required for the
  tree to execute during renders.

## File Output node (CompositorNodeOutputFile)

- Path API is `directory` + `file_name` (not `base_path` + slot paths).
  End `directory` with a path separator.
- **Trailing dot:** the node appends the scene frame number to `file_name`.
  `shot_crypto_0001` rendered at scene frame 276 writes
  `shot_crypto_00010276.exr`. `shot_crypto_0001.` writes
  `shot_crypto_0001.exr`. Always end custom-numbered names with `.`.
- **file_output_items:** the node is created with ZERO items and produces
  no files until items exist:

```python
for item in list(fo.file_output_items):
    fo.file_output_items.remove(item)
fo.file_output_items.new(socket_type='RGBA', name='Combined')   # FLOAT / RGBA / VECTOR
```

- Connect inputs by index (`fo.inputs[0]`, `fo.inputs[1]`, ...) in item
  creation order. Name-based lookup on this node is unreliable in 5.1.x.
- Format is per node via `fo.format` (`file_format`, `color_depth`,
  `color_mode`, `exr_codec`). `OPEN_EXR_MULTILAYER` is valid here and on
  `scene.render.image_settings`.
- Adding items crashed one interactive session historically; add them one
  at a time and save the file before large compositor edits.

## Depth extraction

Two working patterns:

1. **File Output PNG node** (background-safe): route the normalized depth
   into a second File Output node with PNG/16-bit/BW format and one FLOAT
   item. Works under `blender -b`.
2. **Viewer node + save_render** (interactive, battle-tested):

```python
viewer_img = bpy.data.images.get('Viewer Node')
if viewer_img and viewer_img.size[0] > 0:
    viewer_img.save_render(filepath=path, scene=scene)
```

   Viewer images may not update in background mode; prefer pattern 1 for CLI.

Never shape the depth range with `camera.data.clip_end` -- clipping applies
to the whole render, so geometry beyond clip_end disappears from the grey
and crypto passes too.

## Cryptomatte

```python
vl.use_pass_cryptomatte_object = True
vl.pass_cryptomatte_depth = 6            # layers written = ceil(depth / 2)
```

Render Layers then exposes `CryptoObject00`, `CryptoObject01`, ... Route each
into an OPEN_EXR_MULTILAYER File Output as RGBA items.

## Layered Actions (keyframe queries)

Blender 5.x actions are layered; `action.fcurves` is not the primary path.
To read fcurves from a baked action:

```python
action = obj.animation_data.action
strip = action.layers[0].strips[0]
channelbag = strip.channelbags[0]        # or strip.channelbag(slot)
for fc in channelbag.fcurves:
    ...  # fc.data_path, fc.keyframe_points
```

## Sub-frame rendering

`scene.frame_set(frame_int, subframe=0.5)` evaluates animation at
fractional frame positions -- real interpolated in-betweens, not duplicated
frames. Used for half-speed output when a video model has a minimum clip
duration.

## Material override

`view_layer.material_override = mat` replaces object materials only. The
world shader (sky/HDRI/atmosphere lighting) renders normally, so clay
renders keep scene lighting. Set it back to None after rendering.

## EEVEE temporal stability (context, not defaults)

- TAA uses a different sub-pixel jitter sequence per frame; on slow camera
  moves this reads as noise in tracking curves. `taa_render_samples = 1`
  eliminates jitter but is aliased -- production judged it worse and
  reverted to default sampling. Treat as a per-shot experiment only.
- Motion blur (`shutter 0.5`) was also tested for sub-pixel judder with
  mixed results. The script leaves both settings untouched unless
  `--taa-samples` / `--motion-blur` are passed explicitly.
