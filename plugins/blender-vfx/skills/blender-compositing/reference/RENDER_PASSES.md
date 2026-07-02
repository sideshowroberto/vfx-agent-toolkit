# Blender Compositing - Render Passes Guide

**Part of:** blender-compositing skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers complete render pass setup, AOV (Arbitrary Output Variable) configuration, denoising workflows, and multi-pass rendering strategies. Understanding render passes is essential for professional compositing control.

---

## Essential Render Passes

### Enabling Core Passes

**Complete Pass Setup:**
```python
view_layer = bpy.context.view_layer

# Core image passes
view_layer.use_pass_combined = True      # Beauty pass (default)
view_layer.use_pass_z = True             # Depth
view_layer.use_pass_normal = True        # World-space normals
view_layer.use_pass_vector = True        # Motion vectors

# Lighting passes
view_layer.use_pass_diffuse_direct = True    # Direct diffuse
view_layer.use_pass_diffuse_indirect = True  # Indirect diffuse (GI)
view_layer.use_pass_glossy_direct = True     # Direct specular
view_layer.use_pass_glossy_indirect = True   # Indirect specular (reflections)
view_layer.use_pass_emit = True              # Emission
view_layer.use_pass_environment = True       # Environment/HDRI

# Material passes
view_layer.use_pass_diffuse_color = True     # Diffuse albedo
view_layer.use_pass_glossy_color = True      # Specular/reflection color

# Utility passes
view_layer.use_pass_ambient_occlusion = True  # Ambient occlusion
view_layer.use_pass_shadow = True             # Shadow pass
view_layer.use_pass_mist = True               # Distance mist
```

### Accessing Passes in Compositor

**Render Layer Output Names:**
```python
render_layers = compositor.nodes.new('CompositorNodeRLayers')

# Available outputs (when enabled):
outputs = {
    'Image': 'Combined beauty pass',
    'Depth': 'Z-depth',
    'Normal': 'World normals',
    'Vector': 'Motion vectors',
    'DiffDir': 'Diffuse Direct',
    'DiffInd': 'Diffuse Indirect',
    'DiffCol': 'Diffuse Color',
    'GlossDir': 'Glossy Direct',
    'GlossInd': 'Glossy Indirect',
    'GlossCol': 'Glossy Color',
    'Emit': 'Emission',
    'Env': 'Environment',
    'AO': 'Ambient Occlusion',
    'Shadow': 'Shadow',
    'Mist': 'Mist'
}

# Example: Connect depth pass
defocus = compositor.nodes.new('CompositorNodeDefocus')
links.new(render_layers.outputs['Depth'], defocus.inputs['Z'])
```

---

## AOV (Arbitrary Output Variables)

### Custom AOV Setup (EEVEE_NEXT / Cycles)

**Creating Custom AOVs:**
```python
# Add AOV to view layer
view_layer = bpy.context.view_layer
aov = view_layer.aovs.add()
aov.name = "CustomMask"
aov.type = 'VALUE'  # Options: VALUE, COLOR

# Use AOV in shader (Shader Editor)
# Add AOV Output node in material shader
# This would typically be done via UI or shader scripting
```

**Accessing Custom AOVs:**
```python
# Custom AOVs appear as outputs on Render Layers node
custom_aov_output = render_layers.outputs['CustomMask']

# Use in compositor
links.new(custom_aov_output, some_node.inputs['Fac'])
```

**Common AOV Use Cases:**
- **ID Masks**: Object/material identification
- **Control Maps**: Drive compositor effects by shader values
- **UV Passes**: For texture reprojection
- **Custom Lighting**: Specific light group contributions

---

## Denoising Workflows

### Native Blender Denoising

**Setup Denoising Passes:**
```python
# Enable denoising data in view layer
view_layer.use_pass_denoising_data = True  # Enables Denoising Normal + Albedo

# Configure render settings
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'  # Options: OPENIMAGEDENOISE, OPTIX

# For compositing control, disable automatic denoising
scene.cycles.use_denoising = False  # Denoise in compositor instead
```

**Compositor Denoising:**
```python
# Create denoise node
denoise = compositor.nodes.new('CompositorNodeDenoise')
denoise.location = (200, 0)
denoise.prefilter = 'ACCURATE'  # Options: NONE, FAST, ACCURATE

# Connect required passes
links.new(render_layers.outputs['Noisy Image'], denoise.inputs['Image'])
links.new(render_layers.outputs['Denoising Normal'], denoise.inputs['Normal'])
links.new(render_layers.outputs['Denoising Albedo'], denoise.inputs['Albedo'])

# Output denoised image
links.new(denoise.outputs['Image'], composite.inputs['Image'])
```

**Advanced Denoising Strategies:**
```python
# Denoise only specific passes (e.g., indirect lighting)
denoise_indirect = compositor.nodes.new('CompositorNodeDenoise')

# Denoise indirect diffuse/glossy separately
links.new(render_layers.outputs['DiffInd'], denoise_indirect.inputs['Image'])

# Combine denoised indirect with clean direct lighting
add = compositor.nodes.new('CompositorNodeMixRGB')
add.blend_type = 'ADD'
links.new(render_layers.outputs['DiffDir'], add.inputs[1])
links.new(denoise_indirect.outputs['Image'], add.inputs[2])
```

---

## Multi-Pass Reconstruction

### Reconstructing Beauty Pass

**Complete Light Path Reconstruction:**
```python
def reconstruct_beauty_pass(compositor):
    """
    Manually reconstruct beauty pass from individual light paths.
    Useful for adjusting individual lighting components.
    """
    nodes = compositor.nodes
    links = compositor.links

    render_layers = nodes.new('CompositorNodeRLayers')
    render_layers.location = (0, 0)

    # Combine diffuse (direct + indirect)
    add_diffuse = nodes.new('CompositorNodeMixRGB')
    add_diffuse.blend_type = 'ADD'
    add_diffuse.location = (300, 200)
    links.new(render_layers.outputs['DiffDir'], add_diffuse.inputs[1])
    links.new(render_layers.outputs['DiffInd'], add_diffuse.inputs[2])

    # Combine glossy (direct + indirect)
    add_glossy = nodes.new('CompositorNodeMixRGB')
    add_glossy.blend_type = 'ADD'
    add_glossy.location = (300, 0)
    links.new(render_layers.outputs['GlossDir'], add_glossy.inputs[1])
    links.new(render_layers.outputs['GlossInd'], add_glossy.inputs[2])

    # Combine transmission (if enabled)
    # add_transmission = nodes.new('CompositorNodeMixRGB')
    # add_transmission.blend_type = 'ADD'
    # links.new(render_layers.outputs['TransDir'], add_transmission.inputs[1])
    # links.new(render_layers.outputs['TransInd'], add_transmission.inputs[2])

    # Add all lighting components
    add_diffuse_glossy = nodes.new('CompositorNodeMixRGB')
    add_diffuse_glossy.blend_type = 'ADD'
    add_diffuse_glossy.location = (600, 100)
    links.new(add_diffuse.outputs['Image'], add_diffuse_glossy.inputs[1])
    links.new(add_glossy.outputs['Image'], add_diffuse_glossy.inputs[2])

    # Add emission
    add_emission = nodes.new('CompositorNodeMixRGB')
    add_emission.blend_type = 'ADD'
    add_emission.location = (900, 0)
    links.new(add_diffuse_glossy.outputs['Image'], add_emission.inputs[1])
    links.new(render_layers.outputs['Emit'], add_emission.inputs[2])

    # Add environment
    add_environment = nodes.new('CompositorNodeMixRGB')
    add_environment.blend_type = 'ADD'
    add_environment.location = (1200, 0)
    links.new(add_emission.outputs['Image'], add_environment.inputs[1])
    links.new(render_layers.outputs['Env'], add_environment.inputs[2])

    # Final composite
    composite = nodes.new('CompositorNodeComposite')
    composite.location = (1500, 0)
    links.new(add_environment.outputs['Image'], composite.inputs['Image'])

    return compositor
```

**Benefits of Manual Reconstruction:**
- Adjust diffuse/specular balance independently
- Color-grade specific light paths
- Add effects to specific components (e.g., glare on specular only)
- Debug render issues by isolating components

---

## Advanced Pass Workflows

### Shadow Control

**Extracting and Manipulating Shadows:**
```python
# Enable shadow pass
view_layer.use_pass_shadow = True

# Create shadow manipulation setup
render_layers = nodes.new('CompositorNodeRLayers')
shadow_pass = render_layers.outputs['Shadow']

# Intensify or lighten shadows
shadow_multiply = nodes.new('CompositorNodeMath')
shadow_multiply.operation = 'MULTIPLY'
shadow_multiply.location = (300, 0)
shadow_multiply.inputs[1].default_value = 1.5  # Darken shadows

links.new(shadow_pass, shadow_multiply.inputs[0])

# Color shadows (warm or cool)
shadow_color = nodes.new('CompositorNodeMixRGB')
shadow_color.blend_type = 'MULTIPLY'
shadow_color.location = (500, 0)
shadow_color.inputs[2].default_value = (0.7, 0.75, 1.0, 1.0)  # Cool blue tint

links.new(shadow_multiply.outputs['Value'], shadow_color.inputs['Fac'])
```

### Ambient Occlusion Enhancement

**Setup AO Pass:**
```python
# Enable AO pass
view_layer.use_pass_ambient_occlusion = True

# Configure AO in world settings
world = bpy.data.worlds['World']
world.light_settings.use_ambient_occlusion = True
world.light_settings.ao_factor = 1.0
world.light_settings.distance = 10.0

# Compositor AO enhancement
ao_pass = render_layers.outputs['AO']

# Multiply AO with beauty pass for extra depth
ao_multiply = nodes.new('CompositorNodeMixRGB')
ao_multiply.blend_type = 'MULTIPLY'
ao_multiply.location = (400, 0)
ao_multiply.inputs['Fac'].default_value = 0.5  # Subtle

links.new(render_layers.outputs['Image'], ao_multiply.inputs[1])
links.new(ao_pass, ao_multiply.inputs[2])
links.new(ao_multiply.outputs['Image'], composite.inputs['Image'])
```

### Motion Vector Usage

**Motion Blur in Compositor:**
```python
# Enable vector pass
view_layer.use_pass_vector = True

# Create vector blur node
vector_blur = nodes.new('CompositorNodeVecBlur')
vector_blur.location = (200, 0)
vector_blur.factor = 1.0  # Blur strength
vector_blur.samples = 32  # Quality

# Connect
links.new(render_layers.outputs['Image'], vector_blur.inputs['Image'])
links.new(render_layers.outputs['Vector'], vector_blur.inputs['Speed'])
links.new(vector_blur.outputs['Image'], composite.inputs['Image'])
```

---

## Render Layer Organization

### Multiple View Layers

**Creating View Layer Structure:**
```python
scene = bpy.context.scene

# Create view layers for different object groups
background_layer = scene.view_layers.new("Background")
character_layer = scene.view_layers.new("Character")
effects_layer = scene.view_layers.new("Effects")

# Configure layer visibility
# Example: Background layer only renders background collection
background_layer.layer_collection.children['Background'].exclude = False
background_layer.layer_collection.children['Character'].exclude = True
background_layer.layer_collection.children['Effects'].exclude = True

# Compositor setup for multiple layers (see ADVANCED_COMPOSITING.md)
```

**View Layer Pass Optimization:**
```python
# Disable unnecessary passes per layer
background_layer.use_pass_glossy_direct = False  # Background doesn't need specular
background_layer.use_pass_glossy_indirect = False

effects_layer.use_pass_z = False  # Effects layer doesn't need depth
```

---

## File Output Strategies

### Multi-Pass EXR Export

**Complete Multi-Layer EXR Setup:**
```python
# Configure scene for EXR output
scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
scene.render.image_settings.color_depth = '32'
scene.render.image_settings.exr_codec = 'DWAA'  # Lossy compression

# File output node for specific passes
file_output = nodes.new('CompositorNodeOutputFile')
file_output.location = (1000, -400)
file_output.base_path = 'C:\\renders\\passes\\'
file_output.format.file_format = 'OPEN_EXR_MULTILAYER'
file_output.format.color_depth = '32'

# Clear default slots
file_output.layer_slots.clear()

# Add passes to export
passes_to_export = [
    ('beauty', 'Image'),
    ('diffuse_dir', 'DiffDir'),
    ('diffuse_ind', 'DiffInd'),
    ('glossy_dir', 'GlossDir'),
    ('glossy_ind', 'GlossInd'),
    ('emit', 'Emit'),
    ('env', 'Env'),
    ('depth', 'Depth'),
    ('normal', 'Normal'),
    ('vector', 'Vector'),
]

for slot_name, pass_name in passes_to_export:
    file_output.layer_slots.new(slot_name)
    links.new(render_layers.outputs[pass_name], file_output.inputs[slot_name])
```

**Compression Options:**
- **ZIP**: Lossless, good compression for most passes
- **DWAA**: Lossy, excellent compression for beauty/color passes
- **NONE**: No compression, largest files, fastest write
- **PIZ**: Lossless, best for noisy/grainy images

---

## Troubleshooting Pass Issues

### Issue: Render Pass Not Showing

**Symptoms:**
- Pass enabled but output not available on Render Layers node

**Solutions:**
```python
# Verify pass is enabled
print(view_layer.use_pass_z)  # Should be True

# Re-create render layers node (refresh outputs)
old_render_layers = nodes.get('Render Layers')
if old_render_layers:
    location = old_render_layers.location
    nodes.remove(old_render_layers)
    new_render_layers = nodes.new('CompositorNodeRLayers')
    new_render_layers.location = location

# Check if pass is supported by render engine
if scene.render.engine == 'BLENDER_EEVEE_NEXT':
    # EEVEE_NEXT doesn't support all Cycles passes
    print("Note: Some Cycles passes unavailable in EEVEE")
```

### Issue: Denoising Artifacts

**Symptoms:**
- Denoise node creates blotchy or overly smooth results

**Solutions:**
```python
# Lower denoise strength (blend with original)
mix_denoise = nodes.new('CompositorNodeMixRGB')
mix_denoise.blend_type = 'MIX'
mix_denoise.inputs['Fac'].default_value = 0.7  # 70% denoised, 30% original

links.new(render_layers.outputs['Image'], mix_denoise.inputs[1])  # Original
links.new(denoise.outputs['Image'], mix_denoise.inputs[2])  # Denoised

# Use FAST prefilter for less aggressive denoising
denoise.prefilter = 'FAST'

# Denoise individual passes instead of beauty
# (see "Advanced Denoising Strategies" above)
```

### Issue: Multi-Pass Doesn't Match Beauty

**Symptoms:**
- Manually reconstructed beauty doesn't match combined pass

**Solutions:**
```python
# Verify all passes are enabled
required_passes = [
    'use_pass_diffuse_direct',
    'use_pass_diffuse_indirect',
    'use_pass_glossy_direct',
    'use_pass_glossy_indirect',
    'use_pass_emit',
    'use_pass_environment',
]

for pass_name in required_passes:
    if not getattr(view_layer, pass_name):
        print(f"Missing pass: {pass_name}")

# Check for transmission/volume passes if present
# view_layer.use_pass_transmission_direct
# view_layer.use_pass_transmission_indirect

# Verify color management is identical
scene.view_settings.view_transform  # Should be same for all passes
```

---

## Production Best Practices

### Standard Pass Setup

**Recommended Pass Configuration:**
```python
def setup_production_passes(view_layer):
    """
    Standard pass setup for production rendering.
    Balances control with render time.
    """
    # Core passes (always enable)
    view_layer.use_pass_combined = True
    view_layer.use_pass_z = True

    # Lighting passes (essential for compositing)
    view_layer.use_pass_diffuse_direct = True
    view_layer.use_pass_diffuse_indirect = True
    view_layer.use_pass_glossy_direct = True
    view_layer.use_pass_glossy_indirect = True
    view_layer.use_pass_emit = True

    # Utility passes (enable as needed)
    view_layer.use_pass_normal = True  # For re-lighting
    view_layer.use_pass_denoising_data = True  # For denoise control

    # Optional passes (enable for specific needs)
    # view_layer.use_pass_ambient_occlusion = True
    # view_layer.use_pass_shadow = True
    # view_layer.use_pass_vector = True

    return view_layer
```

---

**Return to:** `.claude/skills/blender-compositing/SKILL.md`
