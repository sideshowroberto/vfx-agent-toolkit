# Blender Rendering - EEVEE_NEXT Complete Guide

**Part of:** blender-rendering skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

Complete reference for EEVEE_NEXT settings, screen space effects, ray tracing configuration, and performance optimization. EEVEE_NEXT is Blender's real-time render engine, designed for fast previews and production rendering.

---

## Complete EEVEE_NEXT Settings Breakdown

### Sampling Configuration

**Temporal Anti-Aliasing (TAA):**

```python
import bpy

def configure_eevee_sampling():
    """Complete EEVEE_NEXT sampling configuration"""
    scene = bpy.context.scene
    eevee = scene.eevee

    # TAA Samples (temporal anti-aliasing)
    eevee.taa_render_samples = 64     # Final render (16-64)
    eevee.taa_samples = 16            # Viewport preview (8-16)

    # Jitter (anti-aliasing quality)
    eevee.use_taa_reprojection = True  # Temporal stability
```

**Sampling Quality Guide:**
| Samples | Quality | Use Case | Render Time |
|---------|---------|----------|-------------|
| 8 | Low | Fast preview | 1x |
| 16 | Medium | Standard preview | 2x |
| 32 | High | Pre-final | 4x |
| 64 | Very High | Final render | 8x |
| 128+ | Maximum | Production finals | 16x+ |

---

### Ambient Occlusion (GTAO)

**Ground Truth Ambient Occlusion settings:**

```python
def configure_gtao():
    """Setup GTAO (ambient occlusion) for EEVEE_NEXT"""
    eevee = bpy.context.scene.eevee

    # Enable GTAO
    eevee.use_gtao = True

    # Distance (how far AO reaches)
    eevee.gtao_distance = 0.2         # Units: Blender units

    # Factor (strength)
    eevee.gtao_factor = 1.0           # 0.0-2.0 range

    # Quality
    eevee.gtao_quality = 0.25         # 0.0-1.0 (lower = faster)
```

**GTAO Best Practices:**
- Distance 0.2: Good for general scenes
- Distance 0.05-0.1: Tight spaces, small details
- Distance 0.5-1.0: Large outdoor scenes
- Factor 1.0: Realistic
- Factor 1.5-2.0: Exaggerated for stylized look

---

### Screen Space Reflections (Replaced by Ray Tracing)

**Old SSR (4.2-4.4):**
```python
# ❌ REMOVED in 4.5.0
# eevee.use_ssr = True
# eevee.ssr_quality = 0.5
```

**New Ray Tracing (4.5.0+):**
```python
def configure_raytracing():
    """Enable ray tracing in EEVEE_NEXT (replaces SSR)"""
    eevee = bpy.context.scene.eevee

    # Enable ray tracing (replaces old SSR)
    eevee.use_raytracing = True

    # Ray tracing quality
    # Note: Individual settings moved to render properties
    # No longer granular SSR controls
```

**Ray Tracing Benefits:**
- Accurate off-screen reflections
- No screen-edge artifacts
- Works with transparent objects
- Better quality than old SSR

---

### Screen Space Global Illumination

**Indirect lighting approximation:**

```python
def configure_ssgi():
    """Screen space global illumination (bounce light)"""
    eevee = bpy.context.scene.eevee

    # Note: SSGI settings may vary by Blender version
    # Check available attributes
    available_gi = [attr for attr in dir(eevee) if 'gi' in attr.lower()]
    print(f"Available GI settings: {available_gi}")
```

**Current Status (4.5.0):**
EEVEE_NEXT's global illumination is primarily handled through:
- Light probes (irradiance volumes)
- Reflection probes
- Indirect lighting approximations

---

## Post-Processing Effects

### Bloom/Glow (Compositor-Based)

**Since bloom was removed from EEVEE settings:**

```python
def add_bloom_effect(threshold=0.8, size=6):
    """Add bloom effect via compositor (replaces old EEVEE bloom)"""
    import bpy

    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    # Render input
    render_layers = tree.nodes.new('CompositorNodeRLayers')
    render_layers.location = (0, 0)

    # Glare node (bloom)
    glare = tree.nodes.new('CompositorNodeGlare')
    glare.location = (300, 0)
    glare.glare_type = 'BLOOM'
    glare.quality = 'HIGH'
    glare.threshold = threshold       # Brightness threshold
    glare.size = size                 # Bloom spread (1-9)
    glare.iterations = 3              # Quality passes

    # Mix original + bloom
    mix = tree.nodes.new('CompositorNodeMixRGB')
    mix.location = (600, 0)
    mix.blend_type = 'ADD'
    mix.inputs['Fac'].default_value = 0.5

    # Output
    composite = tree.nodes.new('CompositorNodeComposite')
    composite.location = (900, 0)

    # Connect
    links = tree.links
    links.new(render_layers.outputs['Image'], glare.inputs['Image'])
    links.new(render_layers.outputs['Image'], mix.inputs[1])
    links.new(glare.outputs['Image'], mix.inputs[2])
    links.new(mix.outputs['Image'], composite.inputs['Image'])
```

**Glare Types:**
- **BLOOM:** Soft glow (most common)
- **FOG_GLOW:** Bloom-like fog
- **STREAKS:** Star-shaped highlights
- **SIMPLE_STAR:** 4-point star

---

### Depth of Field

**Camera-based DOF in EEVEE_NEXT:**

```python
def configure_depth_of_field(camera, focus_distance=5.0, fstop=2.8):
    """Setup depth of field for EEVEE_NEXT"""
    import bpy

    # Camera DOF settings
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = focus_distance
    camera.data.dof.aperture_fstop = fstop
    camera.data.dof.aperture_blades = 5  # Bokeh shape
    camera.data.dof.aperture_rotation = 0.0
    camera.data.dof.aperture_ratio = 1.0

    # EEVEE-specific quality
    eevee = bpy.context.scene.eevee
    # DOF is automatic in EEVEE_NEXT, no separate enable
```

**F-Stop Guide:**
| F-Stop | DOF | Use Case |
|--------|-----|----------|
| f/1.4 | Very shallow | Portrait, macro |
| f/2.8 | Shallow | Cinematic, bokeh |
| f/5.6 | Medium | Standard shots |
| f/11 | Deep | Landscapes |
| f/22 | Very deep | Architecture |

---

### Motion Blur

**Shutter-based motion blur:**

```python
def configure_motion_blur():
    """Setup motion blur for EEVEE_NEXT"""
    render = bpy.context.scene.render

    # Enable motion blur
    render.use_motion_blur = True

    # Shutter settings
    render.motion_blur_shutter = 0.5      # 180° shutter (cinematic)
    render.motion_blur_position = 'CENTER'  # or 'START', 'END'

    # EEVEE-specific
    eevee = bpy.context.scene.eevee
    eevee.motion_blur_steps = 8           # Quality (8-32)
```

**Shutter Angle Guide:**
- 0.5 = 180° (standard cinematic)
- 1.0 = 360° (full rotation blur)
- 0.25 = 90° (less blur, "Saving Private Ryan" look)

---

## Viewport vs Final Render

### Viewport Settings

**Optimized viewport for real-time editing:**

```python
def configure_viewport_display():
    """Setup viewport for interactive editing"""
    import bpy

    # Find 3D viewport
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Shading settings
                    shading = space.shading
                    shading.type = 'MATERIAL'  # Material preview mode
                    shading.use_scene_lights = True
                    shading.use_scene_world = True

                    # Performance
                    space.overlay.show_overlays = True
                    space.overlay.show_floor = True
                    space.overlay.show_axis_x = True
                    space.overlay.show_axis_y = True
```

**Viewport Shading Modes:**
- **SOLID:** Fast, no materials
- **MATERIAL:** Preview with EEVEE_NEXT
- **RENDERED:** Full EEVEE_NEXT/Cycles preview

---

### Render Settings Differences

**What changes between viewport and final render:**

```python
def print_viewport_vs_render_differences():
    """Show differences between viewport and final render"""
    eevee = bpy.context.scene.eevee

    differences = {
        "Samples": {
            "Viewport": eevee.taa_samples,
            "Render": eevee.taa_render_samples
        },
        "Resolution": {
            "Viewport": "Automatic (window size)",
            "Render": f"{bpy.context.scene.render.resolution_x}x{bpy.context.scene.render.resolution_y}"
        },
        "Effects": {
            "Viewport": "Simplified for performance",
            "Render": "Full quality post-processing"
        }
    }

    for setting, values in differences.items():
        print(f"{setting}: {values}")
```

---

## Performance Optimization

### Render Speed Optimization

**Settings for faster EEVEE_NEXT renders:**

```python
def optimize_for_speed():
    """Configure EEVEE_NEXT for maximum speed"""
    scene = bpy.context.scene
    eevee = scene.eevee
    render = scene.render

    # Lower samples (faster)
    eevee.taa_render_samples = 16     # Minimum acceptable

    # Disable expensive effects
    eevee.use_gtao = False            # Disable AO
    eevee.use_raytracing = False      # Disable ray tracing

    # Simplify scene
    render.use_simplify = True
    render.simplify_subdivision = 0   # Disable subdivision

    # Resolution percentage (render at lower res)
    render.resolution_percentage = 50  # 50% resolution = 4x faster

    # Disable motion blur
    render.use_motion_blur = False
```

---

### Quality Optimization

**Settings for maximum quality (slower):**

```python
def optimize_for_quality():
    """Configure EEVEE_NEXT for maximum quality"""
    eevee = bpy.context.scene.eevee
    render = bpy.context.scene.render

    # Maximum samples
    eevee.taa_render_samples = 128

    # Enable all effects
    eevee.use_gtao = True
    eevee.gtao_quality = 1.0          # Maximum quality
    eevee.use_raytracing = True

    # Full resolution
    render.resolution_percentage = 100

    # Enable effects
    render.use_motion_blur = True
    render.motion_blur_steps = 32     # Maximum quality
```

---

## Light Probes

### Irradiance Volume

**Baked global illumination:**

```python
def create_irradiance_volume(location=(0,0,0), size=(10,10,3)):
    """Create light probe for GI (global illumination)"""
    import bpy

    # Create irradiance volume
    bpy.ops.object.lightprobe_add(type='VOLUME', location=location)
    probe = bpy.context.active_object

    # Configure
    probe.data.influence_distance = max(size)
    probe.data.falloff = 0.5
    probe.data.intensity = 1.0

    # Grid resolution
    probe.data.grid_resolution_x = 4
    probe.data.grid_resolution_y = 4
    probe.data.grid_resolution_z = 4

    # Scale to scene
    probe.scale = size

    return probe
```

**Baking Light Probes:**
```python
# Note: Baking requires operator context and is a blocking call
# Use viewport preview instead, or bake in Blender UI
```

---

### Reflection Probe

**Localized reflections:**

```python
def create_reflection_probe(location=(0,0,0), size=5.0):
    """Create reflection probe for accurate reflections"""
    import bpy

    # Create reflection probe (sphere)
    bpy.ops.object.lightprobe_add(type='SPHERE', location=location)
    probe = bpy.context.active_object

    # Configure
    probe.data.influence_distance = size
    probe.data.falloff = 0.2
    probe.data.intensity = 1.0
    probe.data.clip_start = 0.1
    probe.data.clip_end = size * 2

    return probe
```

---

## Material-Specific Settings

### Material Blend Modes

**How materials render in EEVEE_NEXT:**

```python
def configure_material_blend_mode(material, mode='OPAQUE'):
    """Set material blend mode for EEVEE_NEXT"""

    # Blend modes
    material.blend_method = mode
    # Options: 'OPAQUE', 'CLIP', 'HASHED', 'BLEND'

    # Shadow modes
    material.shadow_method = 'OPAQUE'
    # Options: 'OPAQUE', 'CLIP', 'HASHED', 'NONE'

    # Alpha threshold (for CLIP/HASHED)
    material.alpha_threshold = 0.5

    # Backface culling (performance)
    material.use_backface_culling = False  # True for closed objects

    # Show backface
    material.show_transparent_back = True
```

**Blend Mode Guide:**
| Mode | Use Case | Transparency | Performance |
|------|----------|--------------|-------------|
| OPAQUE | Solid objects | No | Fastest |
| CLIP | Foliage, cutouts | Binary | Fast |
| HASHED | Dithered alpha | Dithered | Medium |
| BLEND | Glass, smoke | Smooth | Slow |

---

### Shader to RGB Node

**EEVEE-specific shader effects:**

```python
def create_toon_shader():
    """Create toon/cel shader for EEVEE_NEXT"""
    import bpy

    mat = bpy.data.materials.new(name="ToonShader")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Shader to RGB (EEVEE-specific)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    shader_to_rgb = nodes.new('ShaderNodeShaderToRGB')
    color_ramp = nodes.new('ShaderNodeValToRGB')
    emission = nodes.new('ShaderNodeEmission')
    output = nodes.new('ShaderNodeOutputMaterial')

    # Configure color ramp for toon look
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[1].position = 0.6

    # Connect
    links.new(bsdf.outputs['BSDF'], shader_to_rgb.inputs['Shader'])
    links.new(shader_to_rgb.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])

    return mat
```

---

## Troubleshooting EEVEE_NEXT

### Common Issues

**Black renders:**
- Missing lights (EEVEE requires explicit lights)
- Camera clipping (check clip_start/clip_end)
- Incorrect material blend mode

**Noisy renders:**
- Increase taa_render_samples (64-128)
- Enable denoising in compositor
- Check light intensity

**Slow viewport:**
- Lower taa_samples (8-16)
- Disable GTAO in viewport
- Reduce scene complexity

**Missing reflections:**
- Enable use_raytracing
- Add reflection probes
- Check material roughness (too rough = no reflections)

---

**Return to:** `.claude/skills/blender-rendering/SKILL.md`
