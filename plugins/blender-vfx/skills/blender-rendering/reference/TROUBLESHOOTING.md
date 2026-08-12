# Blender Rendering - Troubleshooting Guide

**Part of:** blender-rendering skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

Comprehensive troubleshooting guide for common rendering errors, performance issues, material problems, and render pass debugging. Use this when encountering errors not covered in the main SKILL.md.

---

## Common Rendering Errors

### Error 1: "BLENDER_EEVEE not found"

**Full Error Message:**
```
ValueError: bpy_struct: item.attr = val: enum "BLENDER_EEVEE" not found in ('BLENDER_EEVEE_NEXT', 'CYCLES', 'BLENDER_WORKBENCH')
```

**Cause:**
EEVEE (legacy) was completely removed in Blender 4.5.0. Only EEVEE_NEXT remains.

**Solution:**
```python
# [FAIL] OLD - Will fail in 4.5.0+
scene.render.engine = 'BLENDER_EEVEE'

# [OK] NEW - Works in 4.5.0+
scene.render.engine = 'BLENDER_EEVEE_NEXT'
```

**Version Detection Code:**
```python
import bpy

def get_available_engines():
    """List all available render engines"""
    # Get engine enum
    engine_items = bpy.types.Scene.bl_rna.properties['render'].keywords['type'].bl_rna.properties['engine'].enum_items

    available = [item.identifier for item in engine_items]
    print(f"Available engines: {available}")
    return available

# Check if EEVEE_NEXT is available
engines = get_available_engines()
if 'BLENDER_EEVEE_NEXT' in engines:
    print("[OK] EEVEE_NEXT available")
else:
    print("[FAIL] EEVEE_NEXT not found (update Blender)")
```

---

### Error 2: Material Input KeyError

**Full Error Message:**
```
KeyError: 'bpy_prop_collection[key]: key "Transmission" not found'
KeyError: 'bpy_prop_collection[key]: key "Subsurface" not found'
```

**Cause:**
Principled BSDF input names changed in Blender 4.5.0.

**Old vs New Names:**
| Old Name (4.2-4.4) | New Name (4.5.0+) | Type |
|-------------------|-------------------|------|
| Transmission | Transmission Weight | Float |
| Subsurface | Subsurface Weight | Float |
| Emission | Emission Color | Color |

**Solution - Version-Safe Code:**
```python
import bpy

def set_bsdf_input_safe(bsdf, input_name, value):
    """Set BSDF input with fallback for version compatibility"""

    # Mapping of new to old names
    name_map = {
        'Transmission Weight': 'Transmission',
        'Subsurface Weight': 'Subsurface',
        'Emission Color': 'Emission'
    }

    # Try new name first
    if input_name in bsdf.inputs:
        bsdf.inputs[input_name].default_value = value
        return True

    # Try old name (fallback)
    old_name = name_map.get(input_name)
    if old_name and old_name in bsdf.inputs:
        bsdf.inputs[old_name].default_value = value
        return True

    print(f"Warning: Input '{input_name}' not found in Principled BSDF")
    return False

# Usage
mat = bpy.data.materials.get("MyMaterial")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
set_bsdf_input_safe(bsdf, 'Transmission Weight', 1.0)
set_bsdf_input_safe(bsdf, 'Emission Color', (1,1,1,1))
```

---

### Error 3: AttributeError - Bloom/SSR Settings

**Full Error Message:**
```
AttributeError: 'SceneEEVEE' object has no attribute 'use_bloom'
AttributeError: 'SceneEEVEE' object has no attribute 'use_ssr'
AttributeError: 'SceneEEVEE' object has no attribute 'bloom_threshold'
```

**Cause:**
Bloom and Screen Space Reflections (SSR) were moved/removed in Blender 4.5.0:
- Bloom -> Compositor (Glare node)
- SSR -> Ray Tracing (use_raytracing)

**Solution - Bloom via Compositor:**
```python
import bpy

def add_bloom_compositor():
    """Recreate bloom effect using compositor"""
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    # Render layers
    rl = tree.nodes.new('CompositorNodeRLayers')
    rl.location = (0, 0)

    # Glare (bloom)
    glare = tree.nodes.new('CompositorNodeGlare')
    glare.location = (300, 0)
    glare.glare_type = 'BLOOM'      # Bloom effect
    glare.quality = 'HIGH'
    glare.threshold = 0.8           # Old: eevee.bloom_threshold
    glare.size = 6                  # Old: eevee.bloom_intensity (scaled)
    glare.iterations = 3

    # Composite
    comp = tree.nodes.new('CompositorNodeComposite')
    comp.location = (600, 0)

    # Connect
    tree.links.new(rl.outputs['Image'], glare.inputs['Image'])
    tree.links.new(glare.outputs['Image'], comp.inputs['Image'])
```

**Solution - Reflections via Ray Tracing:**
```python
# [FAIL] OLD (removed)
# scene.eevee.use_ssr = True
# scene.eevee.ssr_quality = 0.5

# [OK] NEW - Enable ray tracing
scene.eevee.use_raytracing = True
# Ray tracing provides better quality than old SSR
```

---

## Performance Issues

### Issue 1: Slow Render Times (Cycles)

**Symptoms:**
- Renders take hours for single frame
- High sample count (512+)
- Complex scenes with many lights

**Diagnosis:**
```python
import bpy

def diagnose_slow_render():
    """Identify render performance bottlenecks"""
    scene = bpy.context.scene
    cycles = scene.cycles

    issues = []

    # Check samples
    if cycles.samples > 512:
        issues.append(f"Very high samples: {cycles.samples} (consider 128-256)")

    # Check light bounces
    if cycles.max_bounces > 12:
        issues.append(f"High light bounces: {cycles.max_bounces}")

    # Check device
    if cycles.device == 'CPU':
        issues.append("Using CPU (GPU is 5-10x faster)")

    # Check denoising
    if not cycles.use_denoising:
        issues.append("Denoising disabled (can use lower samples with denoising)")

    # Check scene complexity
    poly_count = sum(len(obj.data.polygons) for obj in bpy.data.objects if obj.type == 'MESH')
    if poly_count > 1000000:
        issues.append(f"High poly count: {poly_count:,} (consider simplify)")

    return issues
```

**Solutions:**
```python
def optimize_cycles_performance():
    """Apply performance optimizations"""
    scene = bpy.context.scene
    cycles = scene.cycles
    render = scene.render

    # 1. Lower samples, enable denoising
    cycles.samples = 128              # Down from 512+
    cycles.use_denoising = True
    cycles.denoiser = 'OPENIMAGEDENOISE'

    # 2. Reduce light bounces
    cycles.max_bounces = 8            # Down from 12+
    cycles.diffuse_bounces = 3
    cycles.glossy_bounces = 3
    cycles.transmission_bounces = 8

    # 3. Enable GPU
    cycles.device = 'GPU'

    # 4. Enable adaptive sampling
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.01

    # 5. Simplify scene
    render.use_simplify = True
    render.simplify_subdivision = 2   # Max subdiv levels

    # 6. Clamp fireflies
    cycles.sample_clamp_indirect = 3.0
```

---

### Issue 2: Slow Viewport (EEVEE_NEXT)

**Symptoms:**
- Laggy viewport navigation
- Low FPS in material preview mode
- Viewport freezes

**Diagnosis:**
```python
def diagnose_viewport_performance():
    """Check viewport performance settings"""
    eevee = bpy.context.scene.eevee

    issues = []

    # Check viewport samples
    if eevee.taa_samples > 32:
        issues.append(f"High viewport samples: {eevee.taa_samples}")

    # Check GTAO
    if eevee.use_gtao and eevee.gtao_quality > 0.5:
        issues.append(f"High GTAO quality: {eevee.gtao_quality}")

    # Check ray tracing
    if eevee.use_raytracing:
        issues.append("Ray tracing enabled (expensive for viewport)")

    return issues
```

**Solutions:**
```python
def optimize_viewport():
    """Optimize EEVEE_NEXT for smooth viewport"""
    eevee = bpy.context.scene.eevee

    # Lower viewport samples
    eevee.taa_samples = 8             # Down from 16+

    # Reduce GTAO quality
    if eevee.use_gtao:
        eevee.gtao_quality = 0.1      # Low quality for viewport

    # Disable ray tracing in viewport
    eevee.use_raytracing = False

    # Simplify
    render = bpy.context.scene.render
    render.use_simplify = True
    render.simplify_subdivision = 0
```

---

### Issue 3: Out of Memory (GPU)

**Symptoms:**
```
CUDA error: Out of memory
OptiX error: Out of memory
```

**Cause:**
Scene exceeds GPU VRAM (textures, geometry, samples).

**Solutions:**
```python
def reduce_memory_usage():
    """Reduce GPU memory usage"""
    cycles = bpy.context.scene.cycles

    # 1. Reduce tile size (if using tiles)
    # Note: Tile rendering deprecated in newer Blender

    # 2. Reduce texture resolution
    for image in bpy.data.images:
        if image.size[0] > 2048:
            print(f"Large texture: {image.name} ({image.size[0]}x{image.size[1]})")

    # 3. Use CPU for geometry, GPU for rendering
    cycles.device = 'GPU'

    # 4. Reduce samples
    cycles.samples = 64

    # 5. Enable adaptive sampling
    cycles.use_adaptive_sampling = True
    cycles.adaptive_min_samples = 16
```

---

## Material Problems

### Issue 1: Black Materials in Render

**Symptoms:**
- Materials appear black in final render
- Viewport preview looks correct
- No errors reported

**Causes & Solutions:**

**Cause 1: Missing Light**
```python
# EEVEE_NEXT requires explicit lights (unlike Cycles)
def add_default_light():
    light_data = bpy.data.lights.new(name="DefaultLight", type='SUN')
    light_data.energy = 1.0
    light_obj = bpy.data.objects.new("DefaultLight", light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = (0, 0, 10)
```

**Cause 2: Incorrect Material Output**
```python
# Check material has proper output connection
mat = bpy.data.materials.get("MyMaterial")
output = mat.node_tree.nodes.get("Material Output")
if not output.inputs['Surface'].is_linked:
    print("[FAIL] Surface not connected to Material Output")
```

**Cause 3: Zero Emission/Reflectivity**
```python
# Check if material is completely non-reflective
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    base_color = bsdf.inputs['Base Color'].default_value
    if sum(base_color[:3]) < 0.01:
        print("[WARN] Base color too dark (nearly black)")
```

---

### Issue 2: Materials Look Different in EEVEE vs Cycles

**Expected Differences:**

| Feature | Cycles | EEVEE_NEXT | Why Different |
|---------|--------|------------|---------------|
| Caustics | Accurate | Approximated | EEVEE is rasterized |
| Volumetrics | Path traced | Screen-space | Different algorithms |
| Reflections | Recursive | Single bounce | Performance trade-off |
| SSS | Full scatter | Approximation | Speed optimization |

**Minimize Differences:**
```python
def create_compatible_material(name):
    """Material that looks similar in both engines"""
    import bpy

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # Principled BSDF (universal)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')

    # Avoid features that differ:
    # - Keep roughness > 0.1 (mirrors differ)
    # - Avoid high transmission (glass differs)
    # - Avoid volumetrics (very different)
    bsdf.inputs['Roughness'].default_value = 0.3

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat
```

---

## Render Pass Issues

### Issue 1: Missing Render Passes

**Symptoms:**
- Expected pass not available in compositor
- "Pass not found" errors

**Solution - Enable All Passes:**
```python
def enable_all_passes():
    """Enable all available render passes"""
    scene = bpy.context.scene
    view_layer = scene.view_layers["ViewLayer"]

    # Standard passes
    view_layer.use_pass_combined = True
    view_layer.use_pass_z = True
    view_layer.use_pass_mist = True
    view_layer.use_pass_normal = True
    view_layer.use_pass_vector = True
    view_layer.use_pass_uv = True
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
```

---

### Issue 2: Cryptomatte Not Working

**Symptoms:**
- Cryptomatte passes are black/empty
- Cannot select objects in compositor

**Solutions:**
```python
def verify_cryptomatte():
    """Check cryptomatte is properly configured"""
    scene = bpy.context.scene

    # 1. Must be using Cycles
    if scene.render.engine != 'CYCLES':
        print("[FAIL] Cryptomatte only works with Cycles")
        return

    # 2. Enable cryptomatte passes
    view_layer = scene.view_layers["ViewLayer"]
    cycles_passes = view_layer.cycles
    cycles_passes.use_pass_crypto_object = True
    cycles_passes.use_pass_crypto_material = True
    cycles_passes.use_pass_crypto_asset = True

    # 3. Set cryptomatte accuracy
    cycles_passes.pass_crypto_depth = 6  # Number of layers (default 6)

    print("[OK] Cryptomatte configured")
```

---

## Color Management Issues

### Issue 1: Washed Out Colors

**Cause:**
Incorrect color space or view transform.

**Solution:**
```python
def configure_color_management():
    """Set standard color management"""
    scene = bpy.context.scene

    # View settings
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'None'  # or 'Medium High Contrast', 'High Contrast'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    # Display device
    scene.display_settings.display_device = 'sRGB'

    # Sequencer color space
    scene.sequencer_colorspace_settings.name = 'sRGB'
```

---

### Issue 2: Incorrect Texture Colors

**Cause:**
Wrong texture color space (sRGB vs Linear).

**Solution:**
```python
def fix_texture_color_spaces():
    """Set correct color space for all textures"""
    import bpy

    for image in bpy.data.images:
        # Color/albedo textures: sRGB
        if any(x in image.name.lower() for x in ['color', 'diffuse', 'albedo']):
            image.colorspace_settings.name = 'sRGB'

        # Data textures: Linear/Non-Color
        elif any(x in image.name.lower() for x in ['normal', 'roughness', 'metallic', 'bump', 'displacement']):
            image.colorspace_settings.name = 'Non-Color'

        print(f"{image.name}: {image.colorspace_settings.name}")
```

---

## Advanced Debugging

### Enable Blender Debug Output

```python
import bpy

# Enable console output for errors
bpy.app.debug = True
bpy.app.debug_value = 1  # 0-255, higher = more verbose
```

### Render Statistics

```python
def print_render_stats():
    """Print detailed render statistics"""
    scene = bpy.context.scene

    stats = {
        "Engine": scene.render.engine,
        "Resolution": f"{scene.render.resolution_x}x{scene.render.resolution_y}",
        "Samples": None,
        "Objects": len([obj for obj in bpy.data.objects if obj.type == 'MESH']),
        "Polygons": sum(len(obj.data.polygons) for obj in bpy.data.objects if obj.type == 'MESH'),
        "Materials": len(bpy.data.materials),
        "Lights": len([obj for obj in bpy.data.objects if obj.type == 'LIGHT'])
    }

    # Engine-specific
    if scene.render.engine == 'CYCLES':
        stats["Samples"] = scene.cycles.samples
        stats["Device"] = scene.cycles.device
    elif scene.render.engine == 'BLENDER_EEVEE_NEXT':
        stats["Samples"] = scene.eevee.taa_render_samples

    for key, value in stats.items():
        print(f"{key}: {value}")
```

---

**Return to:** `.claude/skills/blender-rendering/SKILL.md`
