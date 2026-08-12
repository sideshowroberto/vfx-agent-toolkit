# Blender Compositing - Color Grading Guide

**Part of:** blender-compositing skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers advanced color correction techniques, LUT workflows, color space management, and professional color grading patterns. These techniques transform raw renders into cinematic, polished final images.

---

## Professional Color Grading Pipeline

### Complete Grading Node Setup

**Full Color Correction Stack:**
```python
def create_grading_pipeline(compositor):
    """
    Professional color grading setup with:
    - Exposure correction
    - Contrast adjustment
    - Color balance (shadows/midtones/highlights)
    - Saturation control
    - RGB curves for fine-tuning
    """
    nodes = compositor.nodes
    links = compositor.links

    render_layers = nodes.new('CompositorNodeRLayers')
    render_layers.location = (0, 0)

    # Stage 1: Exposure
    exposure = nodes.new('CompositorNodeExposure')
    exposure.location = (250, 0)
    exposure.inputs['Exposure'].default_value = 0.0

    # Stage 2: Brightness/Contrast
    bright_contrast = nodes.new('CompositorNodeBrightContrast')
    bright_contrast.location = (500, 0)
    bright_contrast.inputs['Bright'].default_value = 0.0
    bright_contrast.inputs['Contrast'].default_value = 0.0

    # Stage 3: Color Balance
    color_balance = nodes.new('CompositorNodeColorBalance')
    color_balance.location = (750, 0)
    color_balance.correction_method = 'LIFT_GAMMA_GAIN'

    # Lift (shadows): (1.0, 1.0, 1.0) = neutral
    color_balance.lift = (1.0, 1.0, 1.0)
    # Gamma (midtones): (1.0, 1.0, 1.0) = neutral
    color_balance.gamma = (1.0, 1.0, 1.0)
    # Gain (highlights): (1.0, 1.0, 1.0) = neutral
    color_balance.gain = (1.0, 1.0, 1.0)

    # Stage 4: Hue/Saturation
    hue_sat = nodes.new('CompositorNodeHueSat')
    hue_sat.location = (1000, 0)
    hue_sat.inputs['Hue'].default_value = 0.5  # 0.5 = no shift
    hue_sat.inputs['Saturation'].default_value = 1.0  # 1.0 = original
    hue_sat.inputs['Value'].default_value = 1.0

    # Stage 5: RGB Curves (final refinement)
    rgb_curves = nodes.new('CompositorNodeCurveRGB')
    rgb_curves.location = (1250, 0)

    # Connect pipeline
    links.new(render_layers.outputs['Image'], exposure.inputs['Image'])
    links.new(exposure.outputs['Image'], bright_contrast.inputs['Image'])
    links.new(bright_contrast.outputs['Image'], color_balance.inputs['Image'])
    links.new(color_balance.outputs['Image'], hue_sat.inputs['Image'])
    links.new(hue_sat.outputs['Image'], rgb_curves.inputs['Image'])

    # Output
    composite = nodes.new('CompositorNodeComposite')
    composite.location = (1500, 0)
    links.new(rgb_curves.outputs['Image'], composite.inputs['Image'])

    return {
        'exposure': exposure,
        'bright_contrast': bright_contrast,
        'color_balance': color_balance,
        'hue_sat': hue_sat,
        'rgb_curves': rgb_curves
    }
```

---

## Cinematic Color Grading Presets

### Orange and Teal Look

**Classic Blockbuster Color Grade:**
```python
def apply_orange_teal_grade(color_balance, hue_sat):
    """
    Cinematic orange/teal color grade.
    Warm skin tones, cool shadows/backgrounds.
    """
    # Lift (shadows): Cool blue-teal
    color_balance.lift = (0.85, 0.95, 1.05)

    # Gamma (midtones): Slight warm
    color_balance.gamma = (1.05, 1.0, 0.95)

    # Gain (highlights): Warm orange
    color_balance.gain = (1.15, 1.05, 0.90)

    # Boost saturation for stronger effect
    hue_sat.inputs['Saturation'].default_value = 1.2
```

### Bleach Bypass

**High-Contrast Desaturated Look:**
```python
def apply_bleach_bypass(compositor):
    """
    Bleach bypass effect: desaturated, high contrast.
    Popular in war/action films.
    """
    nodes = compositor.nodes
    links = compositor.links

    # Desaturate
    hue_sat = nodes.new('CompositorNodeHueSat')
    hue_sat.inputs['Saturation'].default_value = 0.4  # 60% desaturation

    # High contrast
    bright_contrast = nodes.new('CompositorNodeBrightContrast')
    bright_contrast.inputs['Contrast'].default_value = 20.0

    # Sharp luminance curve
    rgb_curves = nodes.new('CompositorNodeCurveRGB')
    curve = rgb_curves.mapping.curves[3]  # C channel (combined)

    # S-curve for contrast
    # Note: Direct curve point manipulation requires UI or complex API
    # Simpler approach: Use Color Correction node instead

    return hue_sat, bright_contrast
```

### Vintage Film Look

**Warm, Nostalgic Color Grade:**
```python
def apply_vintage_film_look(color_balance, hue_sat):
    """
    Vintage film aesthetic: warm tones, lifted blacks, soft highlights.
    """
    # Lift blacks (faded look)
    color_balance.lift = (1.15, 1.12, 1.05)  # Warm, lifted shadows

    # Warm midtones
    color_balance.gamma = (1.08, 1.05, 0.95)

    # Soft highlights
    color_balance.gain = (1.05, 1.02, 0.92)

    # Slight desaturation
    hue_sat.inputs['Saturation'].default_value = 0.85
```

### Cool Sci-Fi Look

**Modern Sci-Fi Aesthetic:**
```python
def apply_scifi_grade(color_balance, hue_sat):
    """
    Cool, high-tech sci-fi color grade.
    Blue/cyan tones, high contrast.
    """
    # Cool shadows
    color_balance.lift = (0.90, 0.95, 1.15)

    # Neutral-cool midtones
    color_balance.gamma = (0.98, 1.0, 1.08)

    # Slightly cool highlights
    color_balance.gain = (0.95, 1.0, 1.10)

    # Reduce saturation for clinical look
    hue_sat.inputs['Saturation'].default_value = 0.75
```

---

## RGB Curves Mastery

### Understanding RGB Curves

**Curve Manipulation Concepts:**
```python
rgb_curves = nodes.new('CompositorNodeCurveRGB')

# Access curves:
# rgb_curves.mapping.curves[0] = Red channel
# rgb_curves.mapping.curves[1] = Green channel
# rgb_curves.mapping.curves[2] = Blue channel
# rgb_curves.mapping.curves[3] = Combined (C) channel

# Note: Direct curve point manipulation complex via API
# Typically done through UI or using predefined curve types
```

**Common Curve Patterns:**

1. **S-Curve (Contrast)**: Darkens shadows, brightens highlights
2. **Inverse S-Curve**: Lifts shadows, compresses highlights (faded look)
3. **Crushed Blacks**: Steep curve at bottom (pure black shadows)
4. **Lifted Blacks**: Curve starts above 0 (no pure black)

**Practical Implementation:**
```python
# Use Color Correction node for more control
color_correct = nodes.new('CompositorNodeColorCorrection')
color_correct.location = (400, 0)

# Master controls
color_correct.master_saturation = 1.0
color_correct.master_contrast = 1.0
color_correct.master_gamma = 1.0
color_correct.master_gain = 1.0
color_correct.master_lift = 0.0

# Per-channel controls (Red, Green, Blue)
color_correct.red_saturation = 1.0
color_correct.green_saturation = 1.0
color_correct.blue_saturation = 1.0
```

---

## LUT Workflows

### Using LUTs in Blender

**LUT (Look-Up Table) Application:**
```python
# Blender doesn't have native LUT node in compositor
# Use Color Management settings instead

scene = bpy.context.scene

# Apply LUT via View Transform
scene.view_settings.view_transform = 'Filmic'  # Default
scene.view_settings.look = 'Medium High Contrast'  # Built-in looks

# Custom LUT application (requires addon or manual implementation)
# Alternative: Use external compositor (Nuke, Resolve) for complex LUT workflows
```

**Simulating LUT with Color Ramp:**
```python
# Basic color grading with color ramp (ShaderNodeValToRGB)
def create_lut_simulation(compositor):
    """
    Simulate simple LUT using color ramp.
    Limited compared to real 3D LUTs but useful for stylization.
    """
    nodes = compositor.nodes
    links = compositor.links

    # Convert to B&W for ramp input
    rgb_to_bw = nodes.new('CompositorNodeRGBToBW')
    rgb_to_bw.location = (200, 0)

    # Color ramp (gradient map)
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (400, 0)

    cr = color_ramp.color_ramp

    # Example: Warm gradient
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.1, 0.05, 0.2, 1.0)  # Dark purple shadows

    mid = cr.elements.new(0.5)
    mid.color = (0.8, 0.6, 0.4, 1.0)  # Warm midtones

    cr.elements[-1].position = 1.0
    cr.elements[-1].color = (1.0, 0.95, 0.8, 1.0)  # Bright warm highlights

    # Mix with original for subtlety
    mix = nodes.new('CompositorNodeMixRGB')
    mix.location = (600, 0)
    mix.blend_type = 'MIX'
    mix.inputs['Fac'].default_value = 0.5  # 50% effect

    return color_ramp
```

---

## Selective Color Grading

### Masking Specific Areas

**Luminance-Based Masking:**
```python
def create_luminance_mask(compositor):
    """
    Create mask based on image brightness.
    Useful for grading highlights/shadows separately.
    """
    nodes = compositor.nodes
    links = compositor.links

    render_layers = nodes.new('CompositorNodeRLayers')

    # Convert to B&W (luminance)
    rgb_to_bw = nodes.new('CompositorNodeRGBToBW')
    rgb_to_bw.location = (200, 0)
    links.new(render_layers.outputs['Image'], rgb_to_bw.inputs['Image'])

    # Color ramp to isolate highlights
    highlights_mask = nodes.new('ShaderNodeValToRGB')
    highlights_mask.location = (400, 100)

    cr = highlights_mask.color_ramp
    cr.elements[0].position = 0.7  # Only values above 0.7
    cr.elements[0].color = (0, 0, 0, 1)  # Black (no mask)
    cr.elements[-1].position = 1.0
    cr.elements[-1].color = (1, 1, 1, 1)  # White (full mask)

    links.new(rgb_to_bw.outputs['Val'], highlights_mask.inputs['Fac'])

    # Use mask to grade highlights only
    highlight_grade = nodes.new('CompositorNodeHueSat')
    highlight_grade.location = (600, 100)
    highlight_grade.inputs['Saturation'].default_value = 1.3  # Boost highlight saturation

    mix = nodes.new('CompositorNodeMixRGB')
    mix.location = (800, 0)
    mix.blend_type = 'MIX'

    links.new(render_layers.outputs['Image'], mix.inputs[1])  # Original
    links.new(highlight_grade.outputs['Image'], mix.inputs[2])  # Graded
    links.new(highlights_mask.outputs['Color'], mix.inputs['Fac'])  # Mask

    return mix
```

### Object-Based Grading (Cryptomatte)

**Grade Specific Objects:**
```python
def grade_object_selective(compositor, object_name):
    """
    Apply color grading to specific object using cryptomatte.
    """
    nodes = compositor.nodes
    links = compositor.links

    # Cryptomatte for object selection
    cryptomatte = nodes.new('CompositorNodeCryptomatte')
    cryptomatte.location = (200, 0)
    # Note: Object selection typically done via UI

    # Color correction for selected object
    object_grade = nodes.new('CompositorNodeHueSat')
    object_grade.location = (400, 100)
    object_grade.inputs['Hue'].default_value = 0.6  # Shift hue
    object_grade.inputs['Saturation'].default_value = 1.5  # Boost saturation

    # Apply grade to original using cryptomatte mask
    render_layers = nodes.new('CompositorNodeRLayers')

    object_graded = nodes.new('CompositorNodeMixRGB')
    links.new(render_layers.outputs['Image'], object_grade.inputs['Image'])

    mix = nodes.new('CompositorNodeMixRGB')
    mix.location = (600, 0)
    links.new(render_layers.outputs['Image'], mix.inputs[1])  # Original
    links.new(object_grade.outputs['Image'], mix.inputs[2])  # Graded object
    links.new(cryptomatte.outputs['Matte'], mix.inputs['Fac'])  # Object mask

    return mix
```

---

## Color Space Management

### Understanding Color Spaces

**Blender Color Management:**
```python
scene = bpy.context.scene

# View settings (how colors are displayed)
scene.view_settings.view_transform = 'Standard'  # Options: Standard, Filmic, etc.
scene.view_settings.look = 'None'  # Built-in color grades
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0

# Sequencer settings
scene.sequencer_colorspace_settings.name = 'sRGB'  # Default color space

# Display device
scene.display_settings.display_device = 'sRGB'  # Options: sRGB, XYZ, None
```

**ACES Workflow:**
```python
# Set up ACES color management
scene.view_settings.view_transform = 'ACES'
scene.display_settings.display_device = 'sRGB'

# For VFX work, use ACES:
# - Wider color gamut
# - Consistent across applications
# - Standard in film industry
```

**Color Space Best Practices:**
1. **Render in linear color space** (scene_linear)
2. **Apply color grading in linear** (before view transform)
3. **Output in appropriate color space** (sRGB for web, ACES for film)
4. **Match color spaces across pipeline** (Blender -> Nuke -> final output)

---

## Advanced Grading Techniques

### Film Emulation

**Emulating Film Stock Characteristics:**
```python
def emulate_film_stock(compositor, film_type='kodak_5219'):
    """
    Emulate film stock characteristics.
    """
    nodes = compositor.nodes
    links = compositor.links

    render_layers = nodes.new('CompositorNodeRLayers')

    if film_type == 'kodak_5219':  # Kodak Vision3 500T
        # Warm color bias
        color_balance = nodes.new('CompositorNodeColorBalance')
        color_balance.lift = (1.0, 1.0, 1.05)  # Slight blue in shadows
        color_balance.gamma = (1.05, 1.02, 0.98)  # Warm midtones
        color_balance.gain = (1.08, 1.0, 0.95)  # Warmer highlights

        # Soft rolloff in highlights
        bright_contrast = nodes.new('CompositorNodeBrightContrast')
        bright_contrast.inputs['Contrast'].default_value = -5.0  # Softer

        # Grain (would need custom implementation or texture)
        # See grain section below

    elif film_type == 'fuji_eterna':  # Fujifilm Eterna
        color_balance = nodes.new('CompositorNodeColorBalance')
        color_balance.lift = (0.95, 1.0, 1.05)  # Cool shadows
        color_balance.gamma = (1.0, 1.0, 1.0)  # Neutral mids
        color_balance.gain = (1.0, 0.98, 0.95)  # Warm highlights

        # Low saturation
        hue_sat = nodes.new('CompositorNodeHueSat')
        hue_sat.inputs['Saturation'].default_value = 0.8

    return color_balance
```

### Adding Film Grain

**Procedural Film Grain:**
```python
def add_film_grain(compositor, grain_strength=0.05):
    """
    Add film grain texture to image.
    Requires external grain texture or procedural generation.
    """
    nodes = compositor.nodes
    links = compositor.links

    # Load grain texture (or generate procedurally)
    grain_texture = nodes.new('CompositorNodeImage')
    grain_texture.location = (0, -300)
    # grain_texture.image = bpy.data.images.load('C:\\textures\\grain.png')

    # Scale grain to match render resolution
    scale = nodes.new('CompositorNodeScale')
    scale.location = (200, -300)
    scale.space = 'RENDER_SIZE'

    # Mix grain with image
    mix = nodes.new('CompositorNodeMixRGB')
    mix.location = (600, 0)
    mix.blend_type = 'OVERLAY'  # Or 'ADD' for subtle
    mix.inputs['Fac'].default_value = grain_strength

    render_layers = nodes.new('CompositorNodeRLayers')
    links.new(render_layers.outputs['Image'], mix.inputs[1])
    links.new(scale.outputs['Image'], mix.inputs[2])

    return mix
```

---

## Professional Workflow Tips

### Non-Destructive Grading

**Layer Multiple Corrections:**
```python
def create_layered_grade(compositor):
    """
    Non-destructive grading with multiple adjustment layers.
    Each can be toggled on/off for testing.
    """
    nodes = compositor.nodes
    links = compositor.links

    render_layers = nodes.new('CompositorNodeRLayers')
    current_output = render_layers.outputs['Image']

    # Layer 1: Exposure correction
    exposure = nodes.new('CompositorNodeExposure')
    exposure.label = "Grade Layer 1: Exposure"
    exposure.mute = False  # Toggle on/off
    links.new(current_output, exposure.inputs['Image'])
    current_output = exposure.outputs['Image']

    # Layer 2: Color balance
    color_balance = nodes.new('CompositorNodeColorBalance')
    color_balance.label = "Grade Layer 2: Color Balance"
    color_balance.mute = False
    links.new(current_output, color_balance.inputs['Image'])
    current_output = color_balance.outputs['Image']

    # Layer 3: Saturation
    hue_sat = nodes.new('CompositorNodeHueSat')
    hue_sat.label = "Grade Layer 3: Saturation"
    hue_sat.mute = False
    links.new(current_output, hue_sat.inputs['Image'])
    current_output = hue_sat.outputs['Image']

    # Layer 4: Final curves
    rgb_curves = nodes.new('CompositorNodeCurveRGB')
    rgb_curves.label = "Grade Layer 4: Curves"
    rgb_curves.mute = False
    links.new(current_output, rgb_curves.inputs['Image'])
    current_output = rgb_curves.outputs['Image']

    return current_output
```

### Before/After Comparison

**A/B Comparison Setup:**
```python
def create_comparison_setup(compositor):
    """
    Create side-by-side or split comparison of graded vs original.
    """
    nodes = compositor.nodes
    links = compositor.links

    render_layers = nodes.new('CompositorNodeRLayers')

    # Graded version (your color grading pipeline)
    # ... grading nodes ...

    # Split screen using Transform nodes
    transform_left = nodes.new('CompositorNodeTransform')
    transform_left.location = (800, 100)
    transform_left.filter_type = 'BILINEAR'
    # Position original on left half

    transform_right = nodes.new('CompositorNodeTransform')
    transform_right.location = (800, -100)
    # Position graded on right half

    # Alpha over to combine
    alpha_over = nodes.new('CompositorNodeAlphaOver')
    alpha_over.location = (1000, 0)

    return alpha_over
```

---

## Troubleshooting Color Issues

### Issue: Colors Look Washed Out

**Cause:** Incorrect color management or excessive exposure

**Solutions:**
```python
# Check view transform
scene.view_settings.view_transform = 'Filmic'  # Not 'Standard'

# Reduce exposure
exposure_node.inputs['Exposure'].default_value = -0.5

# Boost contrast
bright_contrast.inputs['Contrast'].default_value = 10.0

# Increase saturation
hue_sat.inputs['Saturation'].default_value = 1.2
```

### Issue: Banding in Gradients

**Cause:** 8-bit color depth or aggressive grading

**Solutions:**
```python
# Render in higher bit depth
scene.render.image_settings.color_depth = '16'  # Or '32' for EXR

# Add subtle noise/grain to mask banding
# (see film grain section)

# Use gentler grading adjustments
```

### Issue: Colors Not Matching Reference

**Cause:** Different color spaces or viewing conditions

**Solutions:**
```python
# Match color space to reference
scene.view_settings.view_transform = 'Standard'  # Or ACES, Filmic

# Check display calibration
# Ensure monitor is calibrated

# Use Color Checker chart for accurate matching
# Create reference render with known color values
```

---

**Return to:** `.claude/skills/blender-compositing/SKILL.md`
