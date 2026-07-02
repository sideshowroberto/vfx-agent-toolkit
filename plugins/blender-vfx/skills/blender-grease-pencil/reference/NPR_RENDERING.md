# Blender Grease Pencil - NPR Rendering

**Part of:** blender-grease-pencil skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers Non-Photorealistic Rendering (NPR) techniques for Grease Pencil, including stylized rendering, toon shading, line art workflows, and advanced 2D/3D integration.

**When to Use This Reference:**
- Creating stylized/cel-shaded visuals
- Integrating 2D animation with 3D environments
- Achieving specific art styles (anime, comic book, etc.)
- Professional NPR production workflows

---

## Advanced Mixed Media Workflows

### Camera Setup for 2D/3D Integration

```python
import bpy
from mathutils import Vector

def setup_mixed_media_camera(target_2d=None, target_3d=None):
    """
    Configure camera for optimal 2D/3D composition

    Args:
        target_2d: Grease Pencil object to frame
        target_3d: 3D object to frame
    """
    camera = bpy.data.objects.get('Camera')
    if not camera:
        # Create camera
        cam_data = bpy.data.cameras.new("MixedMediaCam")
        camera = bpy.data.objects.new("Camera", cam_data)
        bpy.context.scene.collection.objects.link(camera)
        bpy.context.scene.camera = camera

    # Camera settings for stylized rendering
    camera.data.lens = 35  # Wide lens for dynamic composition
    camera.data.dof.use_dof = True
    camera.data.dof.aperture_fstop = 2.8  # Shallow depth of field

    # Position camera to frame both 2D and 3D elements
    camera.location = (-8, -8, 5)
    camera.rotation_euler = (1.1, 0, -0.785)

    # Set focal point
    if target_2d:
        camera.data.dof.focus_object = target_2d

    print("Mixed media camera configured")
    return camera

# Example usage
gp_character = bpy.data.objects['Character_2D']
camera = setup_mixed_media_camera(target_2d=gp_character)
```

---

### Lighting for NPR

```python
import bpy

def setup_npr_lighting(style='anime'):
    """
    Configure lighting for specific NPR styles

    Styles:
    - anime: High contrast, rimlight emphasis
    - comic: Strong shadows, dramatic
    - pastel: Soft, diffused lighting
    """
    # Remove default lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    if style == 'anime':
        # Key light (strong, side)
        key = bpy.data.lights.new("KeyLight", type='SUN')
        key_obj = bpy.data.objects.new("KeyLight", key)
        bpy.context.scene.collection.objects.link(key_obj)
        key_obj.location = (5, -5, 8)
        key_obj.rotation_euler = (0.8, 0, 0.785)
        key.energy = 3.0

        # Rim light (strong backlight)
        rim = bpy.data.lights.new("RimLight", type='SUN')
        rim_obj = bpy.data.objects.new("RimLight", rim)
        bpy.context.scene.collection.objects.link(rim_obj)
        rim_obj.location = (-5, 5, 8)
        rim_obj.rotation_euler = (0.8, 0, -2.356)
        rim.energy = 2.0
        rim.color = (0.8, 0.9, 1.0)  # Cool rim

        # Fill (subtle)
        fill = bpy.data.lights.new("FillLight", type='AREA')
        fill_obj = bpy.data.objects.new("FillLight", fill)
        bpy.context.scene.collection.objects.link(fill_obj)
        fill_obj.location = (-3, -3, 3)
        fill.energy = 100
        fill.size = 5

    elif style == 'comic':
        # Single dramatic light
        key = bpy.data.lights.new("DramaticKey", type='SPOT')
        key_obj = bpy.data.objects.new("DramaticKey", key)
        bpy.context.scene.collection.objects.link(key_obj)
        key_obj.location = (3, -3, 6)
        key_obj.rotation_euler = (1.2, 0, 0.785)
        key.energy = 5000
        key.spot_size = 1.2
        key.spot_blend = 0.3

    elif style == 'pastel':
        # Soft HDRI-based lighting
        world = bpy.context.scene.world
        world.use_nodes = True
        nodes = world.node_tree.nodes
        nodes.clear()

        # Add Environment Texture
        env_node = nodes.new(type='ShaderNodeTexEnvironment')
        bg_node = nodes.new(type='ShaderNodeBackground')
        output_node = nodes.new(type='ShaderNodeOutputWorld')

        # Link nodes
        world.node_tree.links.new(env_node.outputs['Color'], bg_node.inputs['Color'])
        world.node_tree.links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])

        bg_node.inputs['Strength'].default_value = 0.8  # Soft intensity

    print(f"NPR lighting setup: {style}")

# Example: Anime-style lighting
setup_npr_lighting(style='anime')
```

---

## Stylized Rendering with EEVEE_NEXT

### Complete EEVEE_NEXT NPR Configuration

```python
import bpy

def configure_eevee_npr(use_bloom=True, use_cel_shading=True, use_outlines=True):
    """
    Configure EEVEE_NEXT for stylized NPR rendering
    """
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    eevee = scene.eevee

    # Screen space effects
    eevee.use_gtao = True
    eevee.gtao_distance = 1.0
    eevee.gtao_factor = 0.5

    if use_bloom:
        eevee.use_bloom = True
        eevee.bloom_threshold = 0.8
        eevee.bloom_knee = 0.5
        eevee.bloom_radius = 6.5
        eevee.bloom_intensity = 0.05  # Subtle for NPR

    # Shadows for cel-shading
    eevee.use_shadows = True
    eevee.shadow_cube_size = '2048'
    eevee.shadow_cascade_size = '2048'
    eevee.use_soft_shadows = False  # Hard shadows for cel-look

    # Color management for stylized look
    scene.view_settings.view_transform = 'Standard'  # Not Filmic
    scene.view_settings.look = 'None'

    # Sampling (higher for final render)
    eevee.taa_render_samples = 64
    eevee.taa_samples = 16  # Viewport

    print("EEVEE_NEXT configured for NPR rendering")

# Example usage
configure_eevee_npr(use_bloom=True, use_cel_shading=True)
```

---

### Cycles NPR Rendering

```python
import bpy

def configure_cycles_npr():
    """
    Configure Cycles for stylized NPR (more control than EEVEE)
    """
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    cycles = scene.cycles

    # Lower samples for stylized (not photoreal)
    cycles.samples = 256

    # Disable caustics for cleaner look
    cycles.caustics_reflective = False
    cycles.caustics_refractive = False

    # Max bounces (stylized needs fewer)
    cycles.max_bounces = 4
    cycles.diffuse_bounces = 2
    cycles.glossy_bounces = 2
    cycles.transmission_bounces = 2

    # Denoising
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'

    # Color management
    scene.view_settings.view_transform = 'Standard'
    scene.sequencer_colorspace_settings.name = 'sRGB'

    print("Cycles configured for NPR rendering")

# Example usage
configure_cycles_npr()
```

---

## Custom Brush Styles and Material Libraries

### Cel-Shaded Material for 3D Objects

```python
import bpy

def create_cel_shader_material(name="CelShader", base_color=(1,0,0,1), levels=3):
    """
    Create toon shader material for 3D objects to match 2D style

    Args:
        name: Material name
        base_color: Base color (RGBA)
        levels: Number of discrete shading levels (3 = shadow, mid, light)
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Input nodes
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfDiffuse')
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    shader_to_rgb = nodes.new(type='ShaderNodeShaderToRGB')

    # Configure color ramp for cel-shading
    color_ramp.color_ramp.interpolation = 'CONSTANT'  # No gradient
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[1].position = 0.7

    # Add third level if needed
    if levels > 2:
        color_ramp.color_ramp.elements.new(0.55)

    # Set colors
    shader.inputs['Color'].default_value = base_color

    # Link nodes
    links.new(shader.outputs['BSDF'], shader_to_rgb.inputs['Shader'])
    links.new(shader_to_rgb.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], output.inputs['Surface'])

    print(f"Cel shader material created: {name}")
    return mat

# Example: Apply to 3D building
building = bpy.data.objects['Building_3D']
cel_mat = create_cel_shader_material("Building_CelShader", base_color=(0.7,0.7,0.8,1))
building.data.materials.append(cel_mat)
```

---

### Grease Pencil Material Library

```python
import bpy

def create_gp_material_library():
    """
    Create standard material library for production consistency
    """
    materials = {}

    # Line material (black outline)
    line_mat = bpy.data.materials.new("GP_Line_Black")
    line_mat.grease_pencil.color = (0.0, 0.0, 0.0, 1.0)
    line_mat.grease_pencil.mode = 'LINE'
    line_mat.grease_pencil.alignment_mode = 'PATH'
    materials['line_black'] = line_mat

    # Fill material (skin tone example)
    fill_mat = bpy.data.materials.new("GP_Fill_Skin")
    fill_mat.grease_pencil.color = (1.0, 0.8, 0.7, 1.0)
    fill_mat.grease_pencil.mode = 'FILL'
    fill_mat.grease_pencil.fill_color = (1.0, 0.8, 0.7, 1.0)
    materials['fill_skin'] = fill_mat

    # Highlight material (specular)
    highlight_mat = bpy.data.materials.new("GP_Highlight")
    highlight_mat.grease_pencil.color = (1.0, 1.0, 1.0, 0.6)
    highlight_mat.grease_pencil.mode = 'LINE'
    materials['highlight'] = highlight_mat

    # Shadow material
    shadow_mat = bpy.data.materials.new("GP_Shadow")
    shadow_mat.grease_pencil.color = (0.3, 0.3, 0.4, 0.5)
    shadow_mat.grease_pencil.mode = 'FILL'
    materials['shadow'] = shadow_mat

    print(f"Material library created: {len(materials)} materials")
    return materials

# Example: Apply to character
materials = create_gp_material_library()
character = bpy.data.objects['Character_GP']
character.data.materials.append(materials['line_black'])
character.data.materials.append(materials['fill_skin'])
character.data.materials.append(materials['highlight'])
character.data.materials.append(materials['shadow'])
```

---

## Line Art Integration

### Automatic Line Art from 3D

```python
import bpy

def create_line_art_from_3d(source_3d_obj, collection_name="3D_Scene"):
    """
    Generate Grease Pencil line art from 3D scene
    """
    # Create line art object
    gpencil = bpy.data.grease_pencils.new("LineArt_GP")
    line_obj = bpy.data.objects.new("LineArt_Object", gpencil)
    bpy.context.scene.collection.objects.link(line_obj)

    # Add Line Art modifier
    lineart_mod = line_obj.grease_pencil_modifiers.new("LineArt", type='GP_LINEART')

    # Configure line art settings
    lineart_mod.use_crease = True  # Include creases
    lineart_mod.crease_threshold = 2.0  # 140 degrees
    lineart_mod.use_intersection = True
    lineart_mod.use_material = True

    # Source collection (all 3D objects to trace)
    if collection_name:
        lineart_mod.source_collection = bpy.data.collections.get(collection_name)

    # Target layer
    layer = gpencil.layers.new("LineArt_Layer")
    lineart_mod.target_layer = "LineArt_Layer"

    # Bake line art to grease pencil
    # (Use UI: "Bake Line Art" button in modifier panel)

    print("Line art modifier created (use 'Bake Line Art' to finalize)")
    return line_obj

# Example usage
building = bpy.data.objects['Building_3D']
line_art = create_line_art_from_3d(building, collection_name="Scene")
```

---

## Production Workflow: 2D Animation Over 3D Background

### Complete Pipeline Setup

```python
import bpy

def setup_mixed_production_scene():
    """
    Setup complete mixed media production scene

    Workflow:
    1. Create/import 3D environment
    2. Apply cel-shader materials
    3. Generate line art
    4. Create 2D character animation
    5. Configure NPR rendering
    """

    # 1. 3D Environment (placeholder cube)
    bpy.ops.mesh.primitive_cube_add(location=(0, 5, 0), scale=(3, 3, 3))
    building = bpy.context.active_object
    building.name = "Background_3D"

    # Apply cel shader
    cel_mat = create_cel_shader_material("Building_Cel", base_color=(0.6, 0.6, 0.7, 1))
    building.data.materials.append(cel_mat)

    # 2. Line art from 3D
    line_art = create_line_art_from_3d(building)
    line_art.location.z = 0.01  # Slightly in front

    # 3. 2D Character
    gpencil = bpy.data.grease_pencils.new("Character_2D")
    char_obj = bpy.data.objects.new("Character_2D", gpencil)
    bpy.context.scene.collection.objects.link(char_obj)
    char_obj.location = (0, 0, 1)

    # Apply material library
    materials = create_gp_material_library()
    for mat in materials.values():
        char_obj.data.materials.append(mat)

    # 4. Camera and lighting
    camera = setup_mixed_media_camera(target_2d=char_obj)
    setup_npr_lighting(style='anime')

    # 5. Render settings
    configure_eevee_npr(use_bloom=True, use_cel_shading=True)

    print("Mixed media production scene setup complete")

# Run complete setup
setup_mixed_production_scene()
```

---

## Render Output Settings

```python
import bpy

def configure_npr_output(output_path="/tmp/render", format='PNG'):
    """
    Configure render output for NPR production
    """
    scene = bpy.context.scene

    # Resolution
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100

    # Output format
    scene.render.image_settings.file_format = format
    if format == 'PNG':
        scene.render.image_settings.color_mode = 'RGBA'
        scene.render.image_settings.compression = 15

    # Output path
    scene.render.filepath = output_path

    # Frame rate
    scene.render.fps = 24

    print(f"Render output configured: {output_path}")

# Example usage
configure_npr_output(output_path="C:/Projects/Renders/scene_")
```

---

**Return to:** `.claude/skills/blender-grease-pencil/SKILL.md`
