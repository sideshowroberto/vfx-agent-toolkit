---
name: blender-rendering
description: EEVEE_NEXT and Cycles rendering, lighting, and render optimization in Blender. Use for rendering setup, lighting, render settings, or when user mentions "render," "lighting," "EEVEE," "Cycles," or "materials."
allowed-tools: Read,Write
---

# Blender Rendering Skill

**Version:** 2.0.0
**Last Updated:** 2026-06-10
**Dependencies:** Blender 5.1+

---

## Breaking Changes (4.5+ / 5.1+)

```python
import bpy

# 1. EEVEE engine renamed (complete removal)
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Not 'BLENDER_EEVEE'

# 2. Bloom removed from EEVEE - use Compositor Glare node
# scene.eevee.use_bloom = True  <- AttributeError in 4.5.3+

# 3. SSR removed - use ray tracing
# scene.eevee.use_ssr = True  <- AttributeError
scene.eevee.use_raytracing = True  # replacement

# 4. Principled BSDF input names changed
bsdf.inputs["Transmission Weight"].default_value = 1.0   # was "Transmission"
bsdf.inputs["Subsurface Weight"].default_value = 0.2     # was "Subsurface"
bsdf.inputs["Emission Color"].default_value = (1,1,1,1)  # was "Emission"

# 5. Cycles settings
cycles = bpy.context.scene.cycles    # Direct access - no import needed
cycles.samples = 128
```

---

## QUICK START

### Setup EEVEE_NEXT Rendering

```python
import bpy

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'

# Quality settings
eevee = scene.eevee
eevee.taa_render_samples = 64     # Render quality
eevee.taa_samples = 16            # Viewport preview quality
eevee.use_gtao = True             # Ambient occlusion
eevee.use_raytracing = True       # Ray-traced reflections (replaces SSR)

# Output settings
render = scene.render
render.resolution_x = 1920
render.resolution_y = 1080
render.resolution_percentage = 100
render.filepath = "//renders/output_"
render.image_settings.file_format = 'PNG'

print(f"Engine: {scene.render.engine}")
print(f"Resolution: {render.resolution_x}x{render.resolution_y}")
```

---

## STANDARD WORKFLOWS

### Workflow 1: Production Cycles Setup

```python
import bpy

scene = bpy.context.scene
scene.render.engine = 'CYCLES'

# Cycles settings via scene.cycles
cycles = scene.cycles
cycles.samples = 256
cycles.use_denoising = True
cycles.denoiser = 'OPENIMAGEDENOISE'

# Adaptive sampling
cycles.use_adaptive_sampling = True
cycles.adaptive_threshold = 0.01

# Light paths
cycles.max_bounces = 8
cycles.diffuse_bounces = 4
cycles.glossy_bounces = 4
cycles.transmission_bounces = 12

# GPU rendering
preferences = bpy.context.preferences
cycles_prefs = preferences.addons['cycles'].preferences
cycles_prefs.compute_device_type = 'CUDA'  # or 'OPTIX', 'HIP', 'METAL'
scene.cycles.device = 'GPU'

print(f"Cycles configured: {cycles.samples} samples, GPU={scene.cycles.device}")
```

---

### Workflow 2: Three-Point Lighting Setup

```python
import bpy

# Key light - main directional
key_data = bpy.data.lights.new("KeyLight", 'AREA')
key_data.energy = 1000
key_data.size = 2.0
key_obj = bpy.data.objects.new("KeyLight", key_data)
bpy.context.scene.collection.objects.link(key_obj)
key_obj.location = (3, -5, 5)
key_obj.rotation_euler = (0.8, 0, 0.6)

# Fill light - softer, opposite side
fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 400
fill_data.size = 4.0
fill_obj = bpy.data.objects.new("FillLight", fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (-4, -3, 3)
fill_obj.rotation_euler = (0.6, 0, -0.8)

# Rim light - behind subject
rim_data = bpy.data.lights.new("RimLight", 'SPOT')
rim_data.energy = 600
rim_data.spot_size = 0.5
rim_obj = bpy.data.objects.new("RimLight", rim_data)
bpy.context.scene.collection.objects.link(rim_obj)
rim_obj.location = (0, 5, 4)
rim_obj.rotation_euler = (2.4, 0, 3.14)

print("Three-point lighting configured")
```

---

### Workflow 3: HDRI Environment Lighting

```python
import bpy

scene = bpy.context.scene
world = scene.world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

# Background node
background = nodes.new('ShaderNodeBackground')
background.inputs['Strength'].default_value = 1.5

# Environment texture
env_texture = nodes.new('ShaderNodeTexEnvironment')
# Load HDRI - replace path with actual file
import bpy
hdri_path = "//textures/studio_hdri.hdr"   # path relative to .blend
try:
    env_texture.image = bpy.data.images.load(hdri_path)
    print(f"HDRI loaded: {hdri_path}")
except Exception:
    print(f"Could not load HDRI from {hdri_path} - set manually in Shader Editor")

# Texture Coordinate -> Mapping -> Environment Texture
tex_coord = nodes.new('ShaderNodeTexCoord')
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Rotation'].default_value = (0, 0, 0)   # Rotate HDRI

world_output = nodes.new('ShaderNodeOutputWorld')

links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], env_texture.inputs['Vector'])
links.new(env_texture.outputs['Color'], background.inputs['Color'])
links.new(background.outputs['Background'], world_output.inputs['Surface'])

print("HDRI world lighting configured")
```

---

### Workflow 4: Bloom via Compositor (4.5.3+ Pattern)

```python
import bpy

scene = bpy.context.scene
scene.use_nodes = True
nodes = scene.node_tree.nodes
links = scene.node_tree.links
nodes.clear()

render_layers = nodes.new('CompositorNodeRLayers')
render_layers.location = (0, 0)

# Glare node replaces old EEVEE bloom
glare = nodes.new('CompositorNodeGlare')
glare.location = (300, 0)
glare.glare_type = 'FOG_GLOW'   # soft bloom
glare.threshold = 0.8
glare.size = 8

composite = nodes.new('CompositorNodeComposite')
composite.location = (600, 0)

links.new(render_layers.outputs['Image'], glare.inputs['Image'])
links.new(glare.outputs['Image'], composite.inputs['Image'])

print("Bloom via Compositor Glare configured")
```

---

## TROUBLESHOOTING

### "BLENDER_EEVEE" ValueError

```python
import bpy
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'   # Fixed
```

### KeyError on Principled BSDF Inputs

```python
import bpy
# Use 4.5+ names
bsdf.inputs["Transmission Weight"].default_value = 1.0
bsdf.inputs["Subsurface Weight"].default_value = 0.2
```

### Black Renders

```python
import bpy

scene = bpy.context.scene

# Check engine
print(f"Engine: {scene.render.engine}")

# Check camera is assigned
if not scene.camera:
    print("No camera assigned to scene")

# Check there are lights (or HDRI)
lights = [o for o in bpy.data.objects if o.type == 'LIGHT']
print(f"Lights in scene: {len(lights)}")

# Check output path is valid
print(f"Output path: {scene.render.filepath}")
```

---

## VALIDATION CHECKLIST

- [ ] Correct engine set (`BLENDER_EEVEE_NEXT` or `CYCLES`)
- [ ] No legacy `BLENDER_EEVEE` or `use_bloom`/`use_ssr` references
- [ ] Principled BSDF inputs use 4.5+ naming
- [ ] Output path configured
- [ ] Camera assigned to scene
- [ ] Lighting set up (area lights or HDRI)
- [ ] Compositor configured for post-processing (bloom, etc.)

---

## VERSION HISTORY

**v2.0.0** (2026-06-10) - MCP migration
- Removed HTTP Bridge requirements and curl health-check
- Removed `import requests` / `requests.post()` wrappers
- Added `import bpy` to all code blocks
- Updated target: Blender 5.1+
- Removed absolute paths to blender-ai-compatibility
- Added HDRI and Bloom/Compositor workflows

**v1.1.0** (2025-10-24) - Progressive disclosure
**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+
