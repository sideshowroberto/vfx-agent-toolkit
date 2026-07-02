# Blender Compositing - Advanced Techniques

**Part of:** blender-compositing skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers advanced compositing workflows including multi-layer compositing, complex node trees, cryptomatte selection, and professional VFX techniques. These patterns build on the standard workflows in SKILL.md and provide production-ready solutions for complex shots.

---

## Multi-Layer Compositing

### Multi-Pass Layer Combination

**Use Case:** Combining multiple render layers with different objects/settings

**Implementation:**
```python
scene = bpy.context.scene
scene.use_nodes = True
compositor = scene.node_tree
nodes = compositor.nodes
links = compositor.links

# Create multiple render layer nodes
background_layer = nodes.new('CompositorNodeRLayers')
background_layer.location = (0, 200)
background_layer.layer = "Background"  # View layer name

character_layer = nodes.new('CompositorNodeRLayers')
character_layer.location = (0, 0)
character_layer.layer = "Character"

effects_layer = nodes.new('CompositorNodeRLayers')
effects_layer.location = (0, -200)
effects_layer.layer = "Effects"

# Alpha Over nodes for layering
alpha_over_1 = nodes.new('CompositorNodeAlphaOver')
alpha_over_1.location = (400, 100)
alpha_over_1.premul = 1.0  # Premultiplied alpha

alpha_over_2 = nodes.new('CompositorNodeAlphaOver')
alpha_over_2.location = (600, 0)
alpha_over_2.premul = 1.0

# Layer order: Background -> Character -> Effects
links.new(background_layer.outputs['Image'], alpha_over_1.inputs[1])
links.new(character_layer.outputs['Image'], alpha_over_1.inputs[2])
links.new(alpha_over_1.outputs['Image'], alpha_over_2.inputs[1])
links.new(effects_layer.outputs['Image'], alpha_over_2.inputs[2])

# Composite output
composite = nodes.new('CompositorNodeComposite')
composite.location = (800, 0)
links.new(alpha_over_2.outputs['Image'], composite.inputs['Image'])
```

**Advanced Layering:**
- Use Z-Combine for depth-aware compositing
- Add per-layer color correction before combining
- Use Mix nodes with different blend modes per layer

---

## Complex Node Tree Architecture

### Modular Node Groups

**Use Case:** Creating reusable compositor node groups

**Implementation:**
```python
# Create node group
group = bpy.data.node_groups.new('ColorGrade', 'CompositorNodeTree')
group_nodes = group.nodes
group_links = group.links

# Create group inputs/outputs
group_input = group_nodes.new('NodeGroupInput')
group_input.location = (0, 0)
group.inputs.new('NodeSocketColor', 'Image')

group_output = group_nodes.new('NodeGroupOutput')
group_output.location = (800, 0)
group.outputs.new('NodeSocketColor', 'Image')

# Build color grading pipeline inside group
bright_contrast = group_nodes.new('CompositorNodeBrightContrast')
bright_contrast.location = (200, 0)

hue_sat = group_nodes.new('CompositorNodeHueSat')
hue_sat.location = (400, 0)

rgb_curves = group_nodes.new('CompositorNodeCurveRGB')
rgb_curves.location = (600, 0)

# Connect internal nodes
group_links.new(group_input.outputs['Image'], bright_contrast.inputs['Image'])
group_links.new(bright_contrast.outputs['Image'], hue_sat.inputs['Image'])
group_links.new(hue_sat.outputs['Image'], rgb_curves.inputs['Image'])
group_links.new(rgb_curves.outputs['Image'], group_output.inputs['Image'])

# Use group in compositor
group_node = compositor.nodes.new('CompositorNodeGroup')
group_node.node_tree = group
group_node.location = (200, 0)

links.new(render_layers.outputs['Image'], group_node.inputs['Image'])
links.new(group_node.outputs['Image'], composite.inputs['Image'])
```

**Benefits:**
- Reusable across multiple compositor setups
- Clean, organized node trees
- Easy to update all instances
- Shareable between blend files

---

## Cryptomatte Workflows

### Complete Cryptomatte Setup

**Use Case:** Object-based masking for selective color grading or effects

**Implementation:**
```python
# Enable cryptomatte passes
view_layer = bpy.context.view_layer
view_layer.use_pass_cryptomatte_object = True
view_layer.use_pass_cryptomatte_material = True
view_layer.use_pass_cryptomatte_asset = True

# Configure cryptomatte accuracy
view_layer.pass_cryptomatte_depth = 6  # Higher = more accurate

# Create cryptomatte node
cryptomatte = nodes.new('CompositorNodeCryptomatte')
cryptomatte.location = (200, 0)

# Connect cryptomatte inputs (automatic from render layers)
links.new(render_layers.outputs['Image'], cryptomatte.inputs['Image'])

# Add object to selection (via matte ID)
# Note: Object selection typically done via UI picker
# Manual approach requires matte ID hash lookup

# Use matte for selective effects
color_correction = nodes.new('CompositorNodeHueSat')
color_correction.location = (400, 100)
color_correction.inputs['Saturation'].default_value = 1.5

# Mix original with corrected using cryptomatte matte
mix = nodes.new('CompositorNodeMixRGB')
mix.location = (600, 0)
mix.blend_type = 'MIX'

links.new(render_layers.outputs['Image'], mix.inputs[1])  # Original
links.new(render_layers.outputs['Image'], color_correction.inputs['Image'])
links.new(color_correction.outputs['Image'], mix.inputs[2])  # Corrected
links.new(cryptomatte.outputs['Matte'], mix.inputs['Fac'])  # Mask
```

**Advanced Cryptomatte Techniques:**
- **Multiple Objects**: Add multiple cryptomatte nodes for different selections
- **Material-Based**: Use cryptomatte_material for material-specific effects
- **Invert Selection**: Use Invert node on matte for "everything except" selection
- **Feather Edges**: Use Dilate/Erode nodes on matte for soft edges

---

## Alpha Compositing Techniques

### Advanced Alpha Blending

**Use Case:** Foreground/background compositing with edge refinement

**Implementation:**
```python
# Load foreground and background
foreground = nodes.new('CompositorNodeImage')
foreground.location = (0, 100)
foreground.image = bpy.data.images.load('/path/to/foreground.png')

background = nodes.new('CompositorNodeImage')
background.location = (0, -100)
background.image = bpy.data.images.load('/path/to/background.png')

# Edge refinement
dilate = nodes.new('CompositorNodeDilateErode')
dilate.location = (200, 100)
dilate.distance = 2  # Expand alpha slightly

blur = nodes.new('CompositorNodeBlur')
blur.location = (400, 100)
blur.size_x = 3
blur.size_y = 3
blur.filter_type = 'GAUSS'

# Premultiply alpha
premul = nodes.new('CompositorNodePremulKey')
premul.location = (600, 100)
premul.mapping = 'PREMUL'

# Alpha over composite
alpha_over = nodes.new('CompositorNodeAlphaOver')
alpha_over.location = (800, 0)

links.new(foreground.outputs['Image'], dilate.inputs['Mask'])
links.new(dilate.outputs['Mask'], blur.inputs['Image'])
links.new(blur.outputs['Image'], premul.inputs['Image'])
links.new(background.outputs['Image'], alpha_over.inputs[1])
links.new(premul.outputs['Image'], alpha_over.inputs[2])
```

**Edge Refinement Strategies:**
- **Choke/Spread**: Use Dilate/Erode to adjust matte size
- **Edge Blur**: Gaussian blur on alpha for soft composites
- **Spill Suppression**: Color correction on edges to remove green screen spill
- **Light Wrap**: Add edge glow from background onto foreground

---

## Performance Optimization

### Render Region Optimization

**Use Case:** Faster iteration when working on specific areas

**Implementation:**
```python
# Enable render region
scene.render.use_border = True
scene.render.border_min_x = 0.25
scene.render.border_min_y = 0.25
scene.render.border_max_x = 0.75
scene.render.border_max_y = 0.75

# Crop compositor to render region
scene.render.use_crop_to_border = True
```

### Node Optimization

**Best Practices:**
```python
# Use Mute to disable expensive nodes during iteration
expensive_node.mute = True

# Use Viewer nodes for intermediate checks
viewer = nodes.new('CompositorNodeViewer')
viewer.location = (400, -200)
links.new(intermediate_output, viewer.inputs['Image'])

# Use File Output for render passes you want to save
file_output = nodes.new('CompositorNodeOutputFile')
file_output.location = (800, -200)
file_output.base_path = 'C:\\renders\\passes\\'
file_output.file_slots.clear()
file_output.file_slots.new('beauty')
file_output.file_slots.new('depth')
links.new(render_layers.outputs['Image'], file_output.inputs['beauty'])
links.new(render_layers.outputs['Depth'], file_output.inputs['depth'])
```

---

## Cross-Application Workflows

### Exporting for Nuke

**Use Case:** Export multi-channel EXR for Nuke compositing

**Implementation:**
```python
# Enable required passes
view_layer = bpy.context.view_layer
view_layer.use_pass_diffuse_direct = True
view_layer.use_pass_glossy_direct = True
view_layer.use_pass_z = True
view_layer.use_pass_normal = True
view_layer.use_pass_emit = True

# Configure EXR output
scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '32'  # Float32
scene.render.image_settings.exr_codec = 'DWAA'  # Compression

# Use File Output node for specific passes
file_output = nodes.new('CompositorNodeOutputFile')
file_output.format.file_format = 'OPEN_EXR_MULTILAYER'
file_output.base_path = 'C:\\renders\\nuke_export\\'

# Add passes as separate layers
file_output.layer_slots.clear()
file_output.layer_slots.new('beauty')
file_output.layer_slots.new('diffuse')
file_output.layer_slots.new('glossy')
file_output.layer_slots.new('depth')

links.new(render_layers.outputs['Image'], file_output.inputs['beauty'])
links.new(render_layers.outputs['DiffDir'], file_output.inputs['diffuse'])
links.new(render_layers.outputs['GlossDir'], file_output.inputs['glossy'])
links.new(render_layers.outputs['Depth'], file_output.inputs['depth'])
```

**Nuke-Ready Channel Naming:**
- Use standard AOV names: beauty, diffuse, specular, reflect, refract
- Export depth as Z channel (Nuke expects this)
- Use DWAA compression for smaller file sizes

---

## Production Patterns

### Scene-Wide Compositor Template

**Use Case:** Consistent compositor setup across multiple shots

**Implementation:**
```python
def create_production_compositor_template():
    """
    Production-ready compositor template with:
    - Render layers input
    - Lens distortion correction
    - Exposure/color correction
    - Vignette
    - Film grain
    - Output composite
    """
    scene = bpy.context.scene
    scene.use_nodes = True
    compositor = scene.node_tree
    compositor.nodes.clear()

    nodes = compositor.nodes
    links = compositor.links

    # Input
    render_layers = nodes.new('CompositorNodeRLayers')
    render_layers.location = (0, 0)

    # Lens distortion
    distortion = nodes.new('CompositorNodeLensdist')
    distortion.location = (200, 0)
    distortion.inputs['Distort'].default_value = -0.02  # Slight correction

    # Exposure
    exposure = nodes.new('CompositorNodeExposure')
    exposure.location = (400, 0)
    exposure.inputs['Exposure'].default_value = 0.0

    # Color correction
    color_correct = nodes.new('CompositorNodeColorCorrection')
    color_correct.location = (600, 0)

    # Vignette (subtle)
    ellipse_mask = nodes.new('CompositorNodeEllipseMask')
    ellipse_mask.location = (600, -200)
    ellipse_mask.x = 0.5
    ellipse_mask.y = 0.5
    ellipse_mask.width = 1.0
    ellipse_mask.height = 1.0

    blur_mask = nodes.new('CompositorNodeBlur')
    blur_mask.location = (800, -200)
    blur_mask.size_x = 100
    blur_mask.size_y = 100

    mix_vignette = nodes.new('CompositorNodeMixRGB')
    mix_vignette.location = (1000, 0)
    mix_vignette.blend_type = 'MULTIPLY'
    mix_vignette.inputs[2].default_value = (0.3, 0.3, 0.3, 1.0)  # Dark edges

    # Film grain
    # Note: Would need custom implementation or texture-based grain

    # Output
    composite = nodes.new('CompositorNodeComposite')
    composite.location = (1200, 0)

    # Connect pipeline
    links.new(render_layers.outputs['Image'], distortion.inputs['Image'])
    links.new(distortion.outputs['Image'], exposure.inputs['Image'])
    links.new(exposure.outputs['Image'], color_correct.inputs['Image'])
    links.new(color_correct.outputs['Image'], mix_vignette.inputs[1])
    links.new(ellipse_mask.outputs['Mask'], blur_mask.inputs['Image'])
    links.new(blur_mask.outputs['Image'], mix_vignette.inputs['Fac'])
    links.new(mix_vignette.outputs['Image'], composite.inputs['Image'])

    return compositor
```

---

## Troubleshooting Advanced Issues

### Issue: Cryptomatte Not Working

**Symptoms:**
- Cryptomatte node shows no matte output
- Object selection doesn't create mask

**Solutions:**
```python
# Verify cryptomatte is enabled
print(view_layer.use_pass_cryptomatte_object)  # Should be True

# Check cryptomatte depth
view_layer.pass_cryptomatte_depth = 6  # Increase if needed

# Verify objects have correct naming
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"Object: {obj.name}, ID: {obj.pass_index}")
```

### Issue: Multi-Layer Alpha Not Compositing

**Symptoms:**
- Layers overlap incorrectly
- Alpha channels not working

**Solutions:**
```python
# Ensure render layers have transparent background
scene.render.film_transparent = True

# Check alpha mode on Alpha Over nodes
alpha_over.use_premultiply = True  # Most common
alpha_over.premul = 1.0  # Fully premultiplied

# Verify layer order (bottom to top in node tree)
```

---

**Return to:** `.claude/skills/blender-compositing/SKILL.md`
