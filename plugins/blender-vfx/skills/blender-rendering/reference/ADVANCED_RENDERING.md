# Blender Rendering - Advanced Rendering

**Part of:** blender-rendering skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference contains advanced rendering techniques, Cycles optimization, complex lighting setups, and render layer management. Use this when the basic workflows in SKILL.md don't provide enough detail for your production needs.

---

## Advanced Cycles Configuration

### Sampling Strategy

**Understanding Samples:**
- **Render Samples:** Final output quality (128-1024)
- **Preview Samples:** Viewport quality (16-64)
- **Adaptive Sampling:** Reduces samples in uniform areas

```python
import bpy

def configure_advanced_cycles():
    """Advanced Cycles sampling configuration"""
    scene = bpy.context.scene
    cycles = scene.cycles

    # Base sampling
    cycles.samples = 256              # Final render quality
    cycles.preview_samples = 32       # Viewport preview

    # Adaptive sampling (smart quality)
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.01   # Lower = higher quality
    cycles.adaptive_min_samples = 16   # Minimum samples per pixel

    # Denoising (AI-based cleanup)
    cycles.use_denoising = True
    cycles.denoiser = 'OPENIMAGEDENOISE'
    cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'

    return "Advanced Cycles configured"
```

**Performance Trade-offs:**
- 128 samples: Fast previews, some noise
- 256 samples: Good quality, balanced time
- 512 samples: High quality, 2x longer
- 1024+ samples: Maximum quality, production finals

---

### Light Path Settings

**Complete Light Bounce Configuration:**

```python
def configure_light_paths():
    """Advanced light path settings for different scenarios"""
    cycles = bpy.context.scene.cycles

    # Maximum quality (slow)
    cycles.max_bounces = 12           # Total light bounces
    cycles.diffuse_bounces = 4        # Non-reflective surfaces
    cycles.glossy_bounces = 4         # Reflective surfaces
    cycles.transmission_bounces = 12  # Glass/transparent
    cycles.volume_bounces = 2         # Fog/smoke
    cycles.transparent_max_bounces = 8

    # Caustics (light through glass)
    cycles.caustics_reflective = True
    cycles.caustics_refractive = True

    # Clamping (reduces fireflies)
    cycles.sample_clamp_indirect = 10.0
    cycles.sample_clamp_direct = 0.0

    # Performance optimization
    cycles.use_light_tree = True      # Smart light sampling (4.5.0+)
```

**Light Bounce Guidelines:**
| Scene Type | Diffuse | Glossy | Transmission | Volume |
|-----------|---------|--------|--------------|--------|
| Exterior | 2 | 2 | 4 | 0 |
| Interior | 4 | 4 | 8 | 2 |
| Glass/Jewelry | 3 | 6 | 12 | 0 |
| Fog/Smoke | 2 | 2 | 4 | 4 |

---

### GPU Acceleration

**Multi-GPU and OptiX Configuration:**

```python
def configure_gpu_rendering():
    """Setup GPU rendering with OptiX (NVIDIA) or HIP (AMD)"""
    import bpy

    prefs = bpy.context.preferences
    cycles_prefs = prefs.addons['cycles'].preferences

    # Enable GPU compute
    cycles_prefs.compute_device_type = 'CUDA'  # or 'OPTIX', 'HIP', 'METAL'

    # Enable all available GPUs
    for device in cycles_prefs.devices:
        device.use = True
        print(f"Enabled: {device.name}")

    # Scene settings
    scene = bpy.context.scene
    scene.cycles.device = 'GPU'

    # OptiX-specific settings (NVIDIA RTX cards)
    if cycles_prefs.compute_device_type == 'OPTIX':
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPTIX'  # Hardware accelerated
```

**Device Selection:**
- **CUDA:** NVIDIA GPUs (all generations)
- **OptiX:** NVIDIA RTX cards (faster, hardware RT cores)
- **HIP:** AMD GPUs
- **Metal:** Apple Silicon

---

## Advanced Lighting Techniques

### HDRI Environment Setup

**Complete HDRI workflow:**

```python
def setup_hdri_environment(hdri_path, rotation=0, strength=1.0):
    """Setup HDRI with rotation and strength control"""
    import bpy

    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create node tree
    tex_coord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    env_tex = nodes.new('ShaderNodeTexEnvironment')
    background = nodes.new('ShaderNodeBackground')
    output = nodes.new('ShaderNodeWorldOutput')

    # Load HDRI
    env_tex.image = bpy.data.images.load(hdri_path)

    # Configure mapping (rotation)
    mapping.inputs['Rotation'].default_value[2] = rotation

    # Set strength
    background.inputs['Strength'].default_value = strength

    # Connect nodes
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
    links.new(env_tex.outputs['Color'], background.inputs['Color'])
    links.new(background.outputs['Background'], output.inputs['Surface'])

    return "HDRI environment configured"
```

**HDRI Best Practices:**
- Use 32-bit .exr files (high dynamic range)
- Rotate environment to position sun/key light
- Typical strength: 0.8-1.5 for outdoor, 0.3-0.8 for indoor
- Combine with area lights for fill

---

### Advanced Light Types

**Area Light with Portals:**

```python
def create_area_light_with_portal(location, rotation, size=2.0, energy=500):
    """Create area light optimized for window lighting"""
    import bpy

    # Create area light
    light_data = bpy.data.lights.new(name="AreaLight", type='AREA')
    light_data.energy = energy
    light_data.size = size
    light_data.shape = 'RECTANGLE'  # or 'SQUARE', 'DISK', 'ELLIPSE'

    # Cycles-specific settings
    light_data.cycles.is_portal = True  # Portal light (for windows)
    light_data.cycles.use_multiple_importance_sampling = True

    # Create object
    light_obj = bpy.data.objects.new("AreaLight", light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = location
    light_obj.rotation_euler = rotation

    return light_obj
```

**Light Type Selection:**
| Type | Use Case | Soft Shadows | Performance |
|------|----------|--------------|-------------|
| Point | Omnidirectional | Hard | Fast |
| Sun | Distant/outdoor | Hard | Medium |
| Spot | Focused beam | Adjustable | Medium |
| Area | Soft lighting | Very soft | Slow |

---

### Volumetric Lighting

**Fog and god rays:**

```python
def setup_volumetric_fog(density=0.01, scatter_color=(1,1,1)):
    """Create volumetric fog effect"""
    import bpy

    world = bpy.context.scene.world

    # Enable volume rendering
    cycles = bpy.context.scene.cycles
    cycles.volume_bounces = 2
    cycles.volume_step_rate = 1.0  # Lower = higher quality
    cycles.volume_max_steps = 1024

    # Setup world volume shader
    world.use_nodes = True
    nodes = world.node_tree.nodes

    # Add volume scatter
    volume_scatter = nodes.new('ShaderNodeVolumeScatter')
    volume_scatter.inputs['Density'].default_value = density
    volume_scatter.inputs['Color'].default_value = (*scatter_color, 1.0)

    # Connect to world output
    output = nodes.get('World Output')
    world.node_tree.links.new(
        volume_scatter.outputs['Volume'],
        output.inputs['Volume']
    )
```

---

## Render Optimization

### Render Layers and AOVs

**Advanced render pass setup:**

```python
def setup_production_render_layers():
    """Configure all render passes for compositing"""
    import bpy

    scene = bpy.context.scene
    view_layer = scene.view_layers["ViewLayer"]

    # Standard passes
    view_layer.use_pass_combined = True
    view_layer.use_pass_z = True
    view_layer.use_pass_normal = True
    view_layer.use_pass_vector = True  # Motion vectors
    view_layer.use_pass_object_index = True
    view_layer.use_pass_material_index = True

    # Light passes
    view_layer.use_pass_diffuse_direct = True
    view_layer.use_pass_diffuse_indirect = True
    view_layer.use_pass_diffuse_color = True
    view_layer.use_pass_glossy_direct = True
    view_layer.use_pass_glossy_indirect = True
    view_layer.use_pass_glossy_color = True
    view_layer.use_pass_transmission_direct = True
    view_layer.use_pass_transmission_indirect = True
    view_layer.use_pass_transmission_color = True
    view_layer.use_pass_emit = True
    view_layer.use_pass_environment = True

    # Cycles-specific
    if scene.render.engine == 'CYCLES':
        cycles_passes = view_layer.cycles
        cycles_passes.use_pass_crypto_object = True
        cycles_passes.use_pass_crypto_material = True
        cycles_passes.use_pass_crypto_asset = True
        cycles_passes.denoising_store_passes = True

    return "Production render layers configured"
```

**Pass Usage Guide:**
- **Diffuse/Glossy/Transmission:** Color grading per material type
- **Crypto:** Object/material ID for masking
- **Z-Depth:** Depth of field in comp
- **Normal:** Relighting in comp
- **Vector:** Motion blur in comp

---

### Render Output Configuration

**Multi-format output setup:**

```python
def configure_output_formats():
    """Setup render output with multiple formats"""
    import bpy

    scene = bpy.context.scene
    render = scene.render

    # Main output (EXR for compositing)
    render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
    render.image_settings.color_mode = 'RGBA'
    render.image_settings.color_depth = '32'  # 32-bit float
    render.image_settings.exr_codec = 'DWAA'  # Lossy compression

    # Color management
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    # Setup compositor for PNG preview
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    # Render layers
    rl = tree.nodes.new('CompositorNodeRLayers')

    # EXR output (all passes)
    exr_output = tree.nodes.new('CompositorNodeOutputFile')
    exr_output.base_path = "//renders/exr/"
    exr_output.format.file_format = 'OPEN_EXR_MULTILAYER'

    # PNG output (preview)
    png_output = tree.nodes.new('CompositorNodeOutputFile')
    png_output.base_path = "//renders/png/"
    png_output.format.file_format = 'PNG'
    png_output.format.color_mode = 'RGBA'
    png_output.format.color_depth = '8'

    # Connect
    tree.links.new(rl.outputs['Image'], exr_output.inputs['Image'])
    tree.links.new(rl.outputs['Image'], png_output.inputs['Image'])
```

---

## Engine Comparison Workflows

### Quality vs Speed Analysis

**Rendering the same scene with both engines:**

```python
def benchmark_engines(scene_name, samples_cycles=128, samples_eevee=64):
    """Compare Cycles and EEVEE_NEXT render times and quality"""
    import bpy
    import time

    scene = bpy.context.scene
    results = {}

    # Test Cycles
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples_cycles
    scene.cycles.use_denoising = True
    results['cycles_samples'] = samples_cycles

    # Test EEVEE_NEXT
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples = samples_eevee
    results['eevee_samples'] = samples_eevee

    return results
```

**Typical Performance Comparison:**
| Feature | Cycles | EEVEE_NEXT | Winner |
|---------|--------|------------|--------|
| Render Speed | 1x | 10-50x | EEVEE |
| Caustics | Accurate | Approximation | Cycles |
| Volumetrics | Accurate | Good | Cycles |
| Reflections | Perfect | Screen-space | Cycles |
| Preview | Slow | Real-time | EEVEE |
| Production | Best quality | Best speed | Depends |

---

## Material System Optimization

### Shader Complexity Management

**Optimize complex shader trees:**

```python
def optimize_material_for_rendering(material):
    """Optimize material node tree for faster rendering"""
    import bpy

    if not material.use_nodes:
        return

    nodes = material.node_tree.nodes

    # Find high-cost nodes
    expensive_nodes = []
    for node in nodes:
        # Noise/Voronoi textures are expensive
        if node.type in ['TEX_NOISE', 'TEX_VORONOI', 'TEX_MUSGRAVE']:
            expensive_nodes.append(node)

    # Optimization: Bake procedural textures
    print(f"Found {len(expensive_nodes)} expensive nodes")
    print("Consider baking procedural textures to image textures")

    # Simplification: Use simpler BSDF for distant objects
    # This would require duplicate material creation
```

**Material Optimization Tips:**
- Bake procedural textures to images for final renders
- Use lower resolution textures for distant objects
- Disable unused material outputs
- Use single BSDF when possible (avoid mixing)

---

## Cross-Engine Material Compatibility

### Creating Universal Materials

**Materials that work well in both engines:**

```python
def create_universal_material(name, base_color, metallic=0, roughness=0.5):
    """Create material optimized for both Cycles and EEVEE_NEXT"""
    import bpy

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # Principled BSDF (universal)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness

    # Material output
    output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # EEVEE_NEXT specific settings
    mat.blend_method = 'OPAQUE'  # or 'BLEND', 'CLIP', 'HASHED'
    mat.shadow_method = 'OPAQUE'

    # Backface culling (performance)
    mat.use_backface_culling = False  # True for closed meshes

    return mat
```

**Feature Compatibility:**
| Feature | Cycles | EEVEE_NEXT | Notes |
|---------|--------|------------|-------|
| Principled BSDF | Full | Full | Universal |
| Displacement | True | Adaptive | Use modifier |
| SSS | Accurate | Approximation | Works both |
| Emission | Correct | Correct | No difference |
| Volume | Accurate | Good | Lower quality EEVEE |

---

**Return to:** `.claude/skills/blender-rendering/SKILL.md`
