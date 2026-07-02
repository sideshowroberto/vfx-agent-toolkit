---
name: blender-compositing
description: Compositor nodes, post-processing, and color grading in Blender. Use for compositing workflows, render pass integration, post-processing, color correction, or when user mentions "compositor," "post-process," "color grade," or "render passes."
allowed-tools: Read,Write
---

# Blender Compositing Skill

**Version:** 3.0.0
**Last Updated:** 2026-06-15
**Dependencies:** Blender 5.1+

---

## Breaking Changes (5.1+)

### Compositor Node Tree Access Changed

`scene.node_tree` no longer exists. Use `scene.compositing_node_group` instead. Must create the node group manually if None.

```python
import bpy

scene = bpy.context.scene
scene.use_nodes = True

# ❌ BROKEN in 5.1+
# compositor = scene.node_tree

# ✅ Access or create compositor node group
comp_tree = scene.compositing_node_group
if comp_tree is None:
    comp_tree = bpy.data.node_groups.new(name="Compositor", type='CompositorNodeTree')
    scene.compositing_node_group = comp_tree

scene.render.use_compositing = True
```

### CompositorNodeComposite Removed

There is no Composite output node in 5.1+. The main render output comes directly from the render pipeline (set via `scene.render.filepath` and `scene.render.image_settings`). Use `CompositorNodeViewer` for preview and `CompositorNodeOutputFile` for additional outputs.

```python
import bpy

# ❌ BROKEN in 5.1+ (RuntimeError: Node type undefined)
# composite = nodes.new('CompositorNodeComposite')

# ✅ Main render output is controlled by scene.render settings
scene = bpy.context.scene
scene.render.filepath = "//output/render_"
scene.render.image_settings.file_format = 'PNG'

# ✅ Use Viewer for compositor preview
viewer = comp_tree.nodes.new('CompositorNodeViewer')
```

### CompositorNodeMapRange Removed

No Map Range node in the compositor. Use `ShaderNodeMath` (works in compositor context) to build equivalent logic.

```python
import bpy

# ❌ BROKEN in 5.1+
# map_range = comp_tree.nodes.new('CompositorNodeMapRange')

# ✅ Use Math nodes for range mapping
# Example: clamp depth to max 80m, then normalize
clamp = comp_tree.nodes.new('ShaderNodeMath')
clamp.operation = 'MINIMUM'
clamp.inputs[1].default_value = 80.0

normalize = comp_tree.nodes.new('CompositorNodeNormalize')
comp_tree.links.new(rl.outputs['Depth'], clamp.inputs[0])
comp_tree.links.new(clamp.outputs[0], normalize.inputs[0])
```

### CompositorNodeColorRamp Removed

```python
import bpy

# ❌ BROKEN in 4.5.0+
# color_ramp = nodes.new('CompositorNodeColorRamp')

# ✅ Use ShaderNodeValToRGB (identical API, works in compositor)
color_ramp = comp_tree.nodes.new('ShaderNodeValToRGB')
```

### OPEN_EXR_MULTILAYER Not Available as Main Render Format

Multilayer EXR can only be created via the compositor's File Output node (which defaults to `OPEN_EXR_MULTILAYER`). The main render output supports `OPEN_EXR` (single layer) but not multilayer.

```python
import bpy

# ❌ BROKEN in 5.1+ — not in scene render format enum
# scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'

# ✅ Use File Output compositor node (defaults to OPEN_EXR_MULTILAYER)
fo = comp_tree.nodes.new('CompositorNodeOutputFile')
print(fo.format.file_format)  # 'OPEN_EXR_MULTILAYER'
```

### EEVEE Bloom → Compositor Glare (4.5.3+)

```python
import bpy

# ❌ BROKEN
# scene.eevee.use_bloom = True

# ✅ Use Compositor Glare node
glare = comp_tree.nodes.new('CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'
glare.threshold = 0.8
glare.size = 8
```

---

## QUICK START

### Basic Compositor Setup (5.1+)

```python
import bpy

scene = bpy.context.scene
scene.use_nodes = True

# Create or get compositor node group
comp_tree = scene.compositing_node_group
if comp_tree is None:
    comp_tree = bpy.data.node_groups.new(name="Compositor", type='CompositorNodeTree')
    scene.compositing_node_group = comp_tree

scene.render.use_compositing = True
comp_tree.nodes.clear()

# Core nodes
rl = comp_tree.nodes.new('CompositorNodeRLayers')
rl.location = (0, 0)

viewer = comp_tree.nodes.new('CompositorNodeViewer')
viewer.location = (400, 0)

comp_tree.links.new(rl.outputs['Image'], viewer.inputs['Image'])
```

---

## STANDARD WORKFLOWS

### Workflow 1: File Output Node (Multilayer EXR)

The File Output node in 5.1+ uses `directory` and `file_name` (not `base_path`/`file_slots`). Add pass inputs via `file_output_items.new()`.

**CRITICAL: Trailing dot in `file_name`** — the File Output node appends the scene frame number to `file_name`. Without a trailing `.`, sequential numbering like `0001` gets the scene frame appended (e.g., `00010276`). Add `.` to terminate: `"output_0001."` → `output_0001.exr`.

```python
import bpy

comp_tree = bpy.context.scene.compositing_node_group
rl = comp_tree.nodes.get('Render Layers')

fo = comp_tree.nodes.new('CompositorNodeOutputFile')
fo.location = (600, -300)

# Set output directory and base filename
fo.directory = "D:\\output\\exr\\"
fo.file_name = "shot_0001."  # Trailing dot prevents frame number append

# Add pass inputs (the node starts with 1 default input + 0 file_output_items)
# Must add items for the node to actually write output
combined = fo.file_output_items.new(socket_type='RGBA', name='Combined')
depth = fo.file_output_items.new(socket_type='FLOAT', name='Depth')
crypto0 = fo.file_output_items.new(socket_type='RGBA', name='CryptoObject00')

# Connect render layer outputs to file output inputs
comp_tree.links.new(rl.outputs['Image'], fo.inputs['Combined'])
comp_tree.links.new(rl.outputs['Depth'], fo.inputs['Depth'])
comp_tree.links.new(rl.outputs['CryptoObject00'], fo.inputs['CryptoObject00'])
```

**File Output API Reference (5.1+):**

| Old API (pre-5.1) | New API (5.1+) |
|---|---|
| `fo.base_path` | `fo.directory` |
| `fo.file_slots[0].path` | `fo.file_name` |
| `fo.file_slots.new("name")` | `fo.file_output_items.new(socket_type='RGBA', name='name')` |
| Format changeable per-node | Format locked to `OPEN_EXR_MULTILAYER` |

**Socket types for `file_output_items.new()`:** `'FLOAT'`, `'RGBA'`, `'VECTOR'`, `'INT'`, `'BOOLEAN'`

---

### Workflow 2: Depth Pass Normalization

**IMPORTANT: Never change camera `clip_end` to control depth range.** Reducing `clip_end` clips geometry from the render entirely — far objects disappear. Instead, clamp depth values in the compositor.

```python
import bpy

comp_tree = bpy.context.scene.compositing_node_group
rl = comp_tree.nodes.get('Render Layers')

# Clamp depth at desired max distance (e.g., 80m)
# Objects beyond this distance map to black, but still RENDER
clamp = comp_tree.nodes.new('ShaderNodeMath')
clamp.operation = 'MINIMUM'
clamp.inputs[1].default_value = 80.0  # max depth in meters
clamp.location = (200, -200)

# Normalize to 0-1 range
normalize = comp_tree.nodes.new('CompositorNodeNormalize')
normalize.location = (400, -200)

# Invert so near=white, far=black (ControlNet convention)
invert = comp_tree.nodes.new('CompositorNodeInvert')
invert.location = (600, -200)

# Chain: Depth → Clamp → Normalize → Invert → Viewer
comp_tree.links.new(rl.outputs['Depth'], clamp.inputs[0])
comp_tree.links.new(clamp.outputs[0], normalize.inputs[0])
comp_tree.links.new(normalize.outputs[0], invert.inputs['Color'])

# View in Viewer, save via viewer_img.save_render()
viewer = comp_tree.nodes.new('CompositorNodeViewer')
viewer.location = (800, -200)
comp_tree.links.new(invert.outputs['Color'], viewer.inputs['Image'])
```

**Saving Viewer output as PNG:**
```python
import bpy

viewer_img = bpy.data.images.get('Viewer Node')
if viewer_img and viewer_img.size[0] > 0:
    viewer_img.save_render(filepath="//depth_0001.png", scene=bpy.context.scene)
```

---

### Workflow 3: Color Correction Pipeline

```python
import bpy

scene = bpy.context.scene
scene.use_nodes = True

comp_tree = scene.compositing_node_group
if comp_tree is None:
    comp_tree = bpy.data.node_groups.new(name="Compositor", type='CompositorNodeTree')
    scene.compositing_node_group = comp_tree
scene.render.use_compositing = True

comp_tree.nodes.clear()

rl = comp_tree.nodes.new('CompositorNodeRLayers')
rl.location = (0, 0)

bright_contrast = comp_tree.nodes.new('CompositorNodeBrightContrast')
bright_contrast.location = (250, 0)
bright_contrast.inputs['Bright'].default_value = 0.1
bright_contrast.inputs['Contrast'].default_value = 0.2

rgb_curves = comp_tree.nodes.new('CompositorNodeCurveRGB')
rgb_curves.location = (500, 0)

hue_sat = comp_tree.nodes.new('CompositorNodeHueSat')
hue_sat.location = (750, 0)
hue_sat.inputs['Saturation'].default_value = 1.2

viewer = comp_tree.nodes.new('CompositorNodeViewer')
viewer.location = (1000, 0)

comp_tree.links.new(rl.outputs['Image'], bright_contrast.inputs['Image'])
comp_tree.links.new(bright_contrast.outputs['Image'], rgb_curves.inputs['Image'])
comp_tree.links.new(rgb_curves.outputs['Image'], hue_sat.inputs['Image'])
comp_tree.links.new(hue_sat.outputs['Image'], viewer.inputs['Image'])
```

---

### Workflow 4: Cryptomatte + Render Passes

```python
import bpy

scene = bpy.context.scene
vl = scene.view_layers["ViewLayer"]

# Enable passes
vl.use_pass_combined = True
vl.use_pass_z = True
vl.use_pass_cryptomatte_object = True
vl.use_pass_cryptomatte_accurate = True

# Cryptomatte outputs appear as CryptoObject00, CryptoObject01, CryptoObject02
# on the Render Layers node. Must be saved in multilayer EXR to be useful
# (use File Output node — see Workflow 1)
```

---

## TROUBLESHOOTING

### "Scene object has no attribute node_tree"

**Cause:** Blender 5.1+ removed `scene.node_tree`
**Fix:** Use `scene.compositing_node_group` (see Breaking Changes above)

### "Node type CompositorNodeComposite undefined"

**Cause:** Composite node removed in 5.1+
**Fix:** Main output uses `scene.render.filepath`. Use Viewer for preview.

### File Output Node Produces No Files

**Cause:** `file_output_items` is empty (0 items). The default input exists but without items defined, nothing is written.
**Fix:** Add at least one item via `fo.file_output_items.new(socket_type='RGBA', name='Combined')`

### File Output Frame Numbers Wrong (e.g., 00010276)

**Cause:** File Output appends the scene frame number to `file_name`
**Fix:** Add trailing `.` to `file_name`: `fo.file_name = "output_0001."`

### Far Objects Missing from Render

**Cause:** Camera `clip_end` was reduced for depth normalization
**Fix:** Never change `clip_end`. Use compositor Math(MINIMUM) node to clamp depth values instead.

### Render Passes Not Showing in Render Layers Node

```python
import bpy
view_layer = bpy.context.scene.view_layers[0]
view_layer.use_pass_z = True
view_layer.use_pass_normal = True
```

---

## VALIDATION CHECKLIST

- [ ] Compositor accessed via `scene.compositing_node_group` (not `scene.node_tree`)
- [ ] No `CompositorNodeComposite` nodes (removed in 5.1)
- [ ] No `CompositorNodeMapRange` nodes (removed — use ShaderNodeMath)
- [ ] ColorRamp nodes use `ShaderNodeValToRGB`
- [ ] File Output uses `directory`/`file_name` (not `base_path`/`file_slots`)
- [ ] File Output `file_name` ends with `.` when using custom frame numbering
- [ ] File Output has `file_output_items` defined (otherwise produces no output)
- [ ] Depth normalization uses compositor clamp, NOT camera `clip_end`
- [ ] Render passes enabled in view layer before use
- [ ] `scene.render.use_compositing = True` set

---

## VERSION HISTORY

**v3.0.0** (2026-06-15) - Blender 5.1.2 compositor overhaul
- `scene.node_tree` → `scene.compositing_node_group` (CompositorNodeTree)
- `CompositorNodeComposite` removed — documented replacement pattern
- `CompositorNodeMapRange` removed — Math node workaround
- File Output node: `base_path`→`directory`, `file_slots`→`file_output_items`
- File Output trailing dot naming fix
- OPEN_EXR_MULTILAYER only via File Output node
- Depth normalization: never change clip_end, use compositor clamp
- Added Cryptomatte + render pass workflow

**v2.0.0** (2026-06-10) - MCP migration
**v1.1.0** (2025-10-24) - Progressive disclosure update
**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+
