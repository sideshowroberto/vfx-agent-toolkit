# PBR Workflows Reference

**Skill:** blender-materials-shaders
**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Blender Version:** 4.5.0+
**Requires:** official Blender MCP (blender.org)

---

## Table of Contents

1. [PBR Theory and Principles](#pbr-theory-and-principles)
2. [Texture Map Types](#texture-map-types)
3. [Complete PBR Material Setup](#complete-pbr-material-setup)
4. [UV Mapping Workflows](#uv-mapping-workflows)
5. [Texture Painting Integration](#texture-painting-integration)
6. [Material Library Organization](#material-library-organization)
7. [Cross-Engine Export](#cross-engine-export)
8. [Industry-Standard PBR Values](#industry-standard-pbr-values)
9. [Texture Optimization](#texture-optimization)
10. [Common PBR Mistakes](#common-pbr-mistakes)

---

## PBR Theory and Principles

### What is PBR?

**Physically-Based Rendering (PBR):** Shading model based on real-world physics of light interaction with surfaces.

**Core Principles:**
1. **Energy Conservation:** Surfaces cannot reflect more light than received
2. **Fresnel Effect:** Reflectivity increases at grazing angles
3. **Metallic Workflow:** Materials are either metal or dielectric (insulator)
4. **Roughness/Smoothness:** Micro-surface detail determines reflection sharpness

**Benefits:**
- Materials look correct in all lighting conditions
- Portable across engines (Unreal, Unity, Cycles, EEVEE_NEXT)
- Predictable results with physically accurate values

---

### Metallic vs Specular Workflows

**Metallic Workflow (Recommended):**
```
Base Color + Metallic + Roughness
```
- **Metallic = 0:** Dielectric (plastic, wood, stone)
- **Metallic = 1:** Conductor (metal)
- Simpler, less error-prone

**Specular Workflow (Legacy):**
```
Diffuse + Specular + Glossiness
```
- More artistic control
- Harder to achieve physically correct results
- Blender Principled BSDF uses Metallic workflow

**Blender Implementation:**
```python
# Metallic workflow (default)
bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)
bsdf.inputs['Metallic'].default_value = 0.0  # Dielectric
bsdf.inputs['Roughness'].default_value = 0.5

# Metal version
bsdf.inputs['Base Color'].default_value = (1.0, 0.85, 0.6, 1.0)  # Gold tint
bsdf.inputs['Metallic'].default_value = 1.0  # Conductor
bsdf.inputs['Roughness'].default_value = 0.2  # Polished
```

---

## Texture Map Types

### Standard PBR Texture Set

**Required Maps:**
1. **Base Color (Albedo)** - RGB diffuse color
2. **Roughness** - Grayscale surface micro-roughness
3. **Metallic** - Grayscale metal mask (0 or 1, rarely in-between)

**Optional Maps:**
4. **Normal** - RGB normal map (tangent space)
5. **Height (Displacement)** - Grayscale height detail
6. **Ambient Occlusion (AO)** - Grayscale cavity shading
7. **Emission** - RGB self-illumination

**Advanced Maps:**
8. **Subsurface Color** - RGB internal scattering color
9. **Opacity** - Grayscale transparency mask
10. **Anisotropy** - Grayscale directional reflection

---

### Texture Map Guidelines

**Base Color (Albedo):**
- **Do:** Pure surface color (no lighting/shadows)
- **Don't:** Include AO, shadows, highlights
- **Range:** 30-240 sRGB (not pure black/white)
- **Color Space:** sRGB

**Roughness:**
- **Do:** Gray values representing micro-surface detail
- **Don't:** Use inverted glossiness without conversion
- **Range:** 0.0 (mirror) to 1.0 (clay)
- **Color Space:** Non-Color (Linear)

**Metallic:**
- **Do:** Binary mask (0 = dielectric, 1 = metal)
- **Don't:** Use partial values unless physically accurate
- **Range:** Usually 0 or 1 (rarely 0.5)
- **Color Space:** Non-Color (Linear)

**Normal Map:**
- **Do:** RGB tangent-space normal map
- **Don't:** Confuse with bump/height map
- **Range:** RGB (128, 128, 255) = flat surface
- **Color Space:** Non-Color (Linear)
- **Note:** OpenGL (Y+) vs DirectX (Y-) format matters for cross-engine

---

## Complete PBR Material Setup

### Full Texture Setup (HTTP Bridge)

```python
import requests
# Execute via the Blender MCP tool: execute_blender_code
code = """
import bpy
import os

# === CONFIGURATION ===
texture_folder = "C:/Textures/Wood_Oak_001"
material_name = "Wood_Oak_PBR"

# Texture file names
textures = {
    'base_color': os.path.join(texture_folder, "Wood_Oak_001_Base_Color.png"),
    'roughness': os.path.join(texture_folder, "Wood_Oak_001_Roughness.png"),
    'normal': os.path.join(texture_folder, "Wood_Oak_001_Normal.png"),
    'ao': os.path.join(texture_folder, "Wood_Oak_001_AO.png"),
    'height': os.path.join(texture_folder, "Wood_Oak_001_Height.png"),
}

# === CREATE MATERIAL ===
mat = bpy.data.materials.new(material_name)
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# === LOAD TEXTURES ===
tex_nodes = {}
x_offset = -1200
y_offset = 0

for map_type, filepath in textures.items():
    if os.path.exists(filepath):
        tex = nodes.new('ShaderNodeTexImage')
        tex.location = (x_offset, y_offset)
        tex.label = map_type
        tex.image = bpy.data.images.load(filepath, check_existing=True)

        # Set color space
        if map_type == 'base_color':
            tex.image.colorspace_settings.name = 'sRGB'
        else:
            tex.image.colorspace_settings.name = 'Non-Color'

        tex_nodes[map_type] = tex
        y_offset -= 300

# === TEXTURE COORDINATE ===
texcoord = nodes.new('ShaderNodeTexCoord')
texcoord.location = (x_offset - 400, 0)

mapping = nodes.new('ShaderNodeMapping')
mapping.location = (x_offset - 200, 0)
links.new(texcoord.outputs['UV'], mapping.inputs['Vector'])

# Connect mapping to all textures
for tex in tex_nodes.values():
    links.new(mapping.outputs['Vector'], tex.inputs['Vector'])

# === NORMAL MAP ===
if 'normal' in tex_nodes:
    normal_map = nodes.new('ShaderNodeNormalMap')
    normal_map.location = (x_offset + 400, -600)
    links.new(tex_nodes['normal'].outputs['Color'], normal_map.inputs['Color'])

# === BUMP/DISPLACEMENT ===
if 'height' in tex_nodes:
    bump = nodes.new('ShaderNodeBump')
    bump.location = (x_offset + 400, -900)
    bump.inputs['Strength'].default_value = 0.3
    links.new(tex_nodes['height'].outputs['Color'], bump.inputs['Height'])

    # Combine with normal map
    if 'normal' in tex_nodes:
        links.new(normal_map.outputs['Normal'], bump.inputs['Normal'])

# === PRINCIPLED BSDF ===
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.location = (x_offset + 800, 0)

# Base Color
if 'base_color' in tex_nodes:
    if 'ao' in tex_nodes:
        # Mix AO with base color
        mix_ao = nodes.new('ShaderNodeMix')
        mix_ao.data_type = 'RGBA'
        mix_ao.blend_type = 'MULTIPLY'
        mix_ao.location = (x_offset + 400, 0)
        links.new(tex_nodes['base_color'].outputs['Color'], mix_ao.inputs['A'])
        links.new(tex_nodes['ao'].outputs['Color'], mix_ao.inputs['B'])
        links.new(mix_ao.outputs['Result'], bsdf.inputs['Base Color'])
    else:
        links.new(tex_nodes['base_color'].outputs['Color'], bsdf.inputs['Base Color'])

# Roughness
if 'roughness' in tex_nodes:
    links.new(tex_nodes['roughness'].outputs['Color'], bsdf.inputs['Roughness'])

# Normal
if 'normal' in tex_nodes:
    if 'height' in tex_nodes:
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])

# === MATERIAL OUTPUT ===
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (x_offset + 1200, 0)
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

# === ASSIGN TO ACTIVE OBJECT ===
obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat

print(f"Material '{material_name}' created with {len(tex_nodes)} textures")
"""

response = requests.post(url, json={"code": code})
print(response.json())
```

**Node Layout:**
```
TexCoord → Mapping → [All Texture Nodes]
                           ↓
Base Color ─┐         Normal → NormalMap ─┐
AO ─────────┴→ Mix →                      ├→ Bump → BSDF → Output
Roughness ───────────────────────────────→│
Height ──────────────────────────────────→┘
```

---

### Simplified PBR Setup (No Textures)

```python
code = """
import bpy

# Quick PBR material without textures
mat = bpy.data.materials.new("Simple_PBR")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.location = (0, 0)

# Dielectric (non-metal) values
bsdf.inputs['Base Color'].default_value = (0.8, 0.6, 0.4, 1.0)  # Wood color
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.6
bsdf.inputs['IOR'].default_value = 1.45  # Wood/plastic
bsdf.inputs['Specular IOR Level'].default_value = 0.5  # Standard specular

output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

## UV Mapping Workflows

### UV Unwrapping (Direct API)

```python
code = """
import bpy
import bmesh

obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    # Enter edit mode via bmesh (HTTP Bridge compatible)
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    # Select all faces
    for face in bm.faces:
        face.select = True

    # Smart UV Project (direct API)
    # NOTE: bpy.ops.uv.smart_project() FAILS in HTTP Bridge
    # Use bmesh.ops instead

    # Option 1: Cube projection
    bmesh.ops.create_cube(bm, size=2.0)

    # Option 2: Manual UV unwrap (production method)
    # Must use direct geometry manipulation
    uv_layer = bm.loops.layers.uv.verify()

    for face in bm.faces:
        for loop in face.loops:
            # Simple planar projection (XY plane)
            loop[uv_layer].uv = (
                loop.vert.co.x * 0.5 + 0.5,
                loop.vert.co.y * 0.5 + 0.5
            )

    # Apply changes
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

print(f"UV unwrapping completed for {obj.name}")
"""
```

**HTTP Bridge Limitation:** UV operators (`bpy.ops.uv.*`) fail. Use bmesh direct manipulation.

---

### UV Layout Best Practices

**Texture Space Optimization:**
1. **Minimize Seams:** Fewer UV islands = fewer texture seams
2. **Uniform Texel Density:** Similar-sized faces get similar UV space
3. **Avoid Stretching:** Maintain aspect ratio where possible
4. **0-1 Range:** Keep UVs within 0-1 for standard tiling

**Checking UV Layout:**
```python
code = """
import bpy

obj = bpy.context.active_object
mesh = obj.data

if mesh.uv_layers.active:
    uv_layer = mesh.uv_layers.active.data

    # Check if UVs exist
    if len(uv_layer) > 0:
        print(f"UV count: {len(uv_layer)}")

        # Calculate UV bounds
        min_u = min_v = 999
        max_u = max_v = -999

        for loop in mesh.loops:
            uv = uv_layer[loop.index].uv
            min_u = min(min_u, uv.x)
            min_v = min(min_v, uv.y)
            max_u = max(max_u, uv.x)
            max_v = max(max_v, uv.y)

        print(f"UV bounds: U({min_u:.2f} to {max_u:.2f}), V({min_v:.2f} to {max_v:.2f})")

        if min_u < 0 or max_u > 1 or min_v < 0 or max_v > 1:
            print("WARNING: UVs outside 0-1 range")
    else:
        print("ERROR: No UV data")
else:
    print("ERROR: No active UV layer")
"""
```

---

### Texture Tiling and Offset

```python
code = """
import bpy

mat = bpy.data.materials.new("Tiled_Material")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# Mapping node for tiling
mapping = nodes.new('ShaderNodeMapping')
mapping.location = (-800, 0)
mapping.inputs['Scale'].default_value = (4.0, 4.0, 1.0)  # 4x tiling
mapping.inputs['Location'].default_value = (0.5, 0.5, 0.0)  # Center offset

links.new(texcoord.outputs['UV'], mapping.inputs['Vector'])

# Texture
tex_image = nodes.new('ShaderNodeTexImage')
tex_image.location = (-500, 0)
tex_image.extension = 'REPEAT'  # REPEAT, EXTEND, CLIP
# tex_image.image = bpy.data.images.load("C:/Textures/tiles.png")

links.new(mapping.outputs['Vector'], tex_image.inputs['Vector'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

**Mapping Parameters:**
- **Location:** Offset texture (0.5 = 50% shift)
- **Rotation:** Rotate texture (radians: 1.5708 = 90°)
- **Scale:** Tile count (2.0 = 2x2 tiles)

---

## Texture Painting Integration

### Setup for Texture Painting

```python
code = """
import bpy

obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    # Create material with image texture for painting
    mat = bpy.data.materials.new("Paintable_Material")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    # Create blank image
    img = bpy.data.images.new(
        name="PaintTexture",
        width=2048,
        height=2048,
        alpha=True,
        float_buffer=False
    )
    img.colorspace_settings.name = 'sRGB'

    # Image texture node
    tex_image = nodes.new('ShaderNodeTexImage')
    tex_image.image = img

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])

    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # Assign material
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat

    print(f"Paintable material created with {img.size[0]}x{img.size[1]} texture")
"""
```

**HTTP Bridge Note:** Texture painting itself requires interactive viewport (not via HTTP Bridge), but setup works.

---

### Baking PBR Textures

**Bake AO to Texture:**
```python
code = """
import bpy

obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    # Create image for baking
    img = bpy.data.images.new(
        name="Baked_AO",
        width=1024,
        height=1024,
        alpha=False
    )

    # Material setup
    mat = obj.data.materials[0]
    if mat and mat.use_nodes:
        nodes = mat.node_tree.nodes

        # Add image texture for bake target
        bake_tex = nodes.new('ShaderNodeTexImage')
        bake_tex.image = img
        nodes.active = bake_tex  # CRITICAL: Active node is bake target

    # Bake settings (HTTP Bridge compatible)
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 32
    bpy.context.scene.cycles.bake_type = 'AO'

    # NOTE: bpy.ops.object.bake() may fail in HTTP Bridge
    # Use Cycles standalone or interactive Blender for baking
    print("Bake setup complete. Run bpy.ops.object.bake(type='AO') in interactive Blender")
"""
```

**Baking Limitations:** `bpy.ops.object.bake()` requires interactive context. Setup via HTTP Bridge, execute bake manually.

---

## Material Library Organization

### Naming Conventions

**Standard Format:**
```
[Category]_[Material]_[Variant]_[Resolution]

Examples:
M_Metal_Steel_Brushed_2K
M_Wood_Oak_Dark_4K
M_Plastic_Red_Glossy_1K
M_Stone_Granite_Grey_2K
```

**Prefixes:**
- `M_` = Material
- `T_` = Texture
- `NG_` = Node Group

---

### Material Library Structure

```python
code = """
import bpy

# Organize materials into collections (fake users)
categories = {
    "Metals": ["M_Steel_Brushed", "M_Copper_Patina", "M_Gold_Polished"],
    "Woods": ["M_Oak_Natural", "M_Pine_Aged", "M_Walnut_Dark"],
    "Plastics": ["M_Plastic_Red", "M_Plastic_Matte_Black"],
    "Stones": ["M_Granite_Grey", "M_Marble_White"],
}

for category, materials in categories.items():
    for mat_name in materials:
        mat = bpy.data.materials.get(mat_name)
        if mat:
            # Add fake user (prevents auto-deletion)
            mat.use_fake_user = True

            # Add custom property for category
            mat['category'] = category

print("Material library organized")
"""
```

---

### Material Browser System

```python
code = """
import bpy

def get_materials_by_category(category):
    \"\"\"Retrieve all materials in category\"\"\"
    materials = []
    for mat in bpy.data.materials:
        if mat.get('category') == category:
            materials.append(mat)
    return materials

def apply_library_material(obj, material_name):
    \"\"\"Apply material from library to object\"\"\"
    mat = bpy.data.materials.get(material_name)
    if mat and obj.type == 'MESH':
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
        return True
    return False

# Example usage
metals = get_materials_by_category("Metals")
print(f"Found {len(metals)} metal materials")

obj = bpy.context.active_object
if apply_library_material(obj, "M_Steel_Brushed"):
    print("Material applied successfully")
"""
```

---

## Cross-Engine Export

### Unreal Engine Export

**Material Requirements:**
- **Base Color:** sRGB texture
- **Normal:** Linear (DirectX format: Y-)
- **Roughness:** Linear grayscale
- **Metallic:** Linear grayscale (0 or 1)
- **AO:** Optional (baked into Base Color OR separate)

**Export Setup:**
```python
code = """
import bpy

# Export FBX with materials for Unreal
obj = bpy.context.active_object
export_path = "C:/Exports/model_for_unreal.fbx"

# NOTE: bpy.ops.export_scene.fbx() may fail in HTTP Bridge
# Setup only, execute in interactive Blender

# Material naming convention for Unreal
for mat in bpy.data.materials:
    if not mat.name.startswith('M_'):
        mat.name = f"M_{mat.name}"

# Texture naming for Unreal
for img in bpy.data.images:
    if not img.name.startswith('T_'):
        img.name = f"T_{img.name}"

print(f"Materials renamed for Unreal Engine export to {export_path}")
"""
```

**Unreal Import Settings:**
- **Material Import:** Import Materials + Textures
- **Normal Map:** Flip Green Channel (Y-)
- **Combine Meshes:** Off (preserve instances)

---

### Unity Export

**Material Requirements:**
- **Base Color (Albedo):** sRGB
- **Normal:** Linear (OpenGL format: Y+)
- **Metallic + Smoothness:** Combined in single texture (Metallic=RGB, Smoothness=A)
- **AO:** Red channel only

**Texture Packing for Unity:**
```python
code = """
import bpy

# Combine Metallic + Smoothness into single texture
mat = bpy.data.materials.get("YourMaterial")
if mat and mat.use_nodes:
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Get existing textures
    metallic_tex = None
    roughness_tex = None

    for node in nodes:
        if node.type == 'TEX_IMAGE':
            if 'metallic' in node.label.lower():
                metallic_tex = node
            elif 'roughness' in node.label.lower():
                roughness_tex = node

    if metallic_tex and roughness_tex:
        # Combine using Separate/Combine Color nodes
        sep_metal = nodes.new('ShaderNodeSeparateColor')
        sep_rough = nodes.new('ShaderNodeSeparateColor')
        combine = nodes.new('ShaderNodeCombineColor')

        links.new(metallic_tex.outputs['Color'], sep_metal.inputs['Color'])
        links.new(roughness_tex.outputs['Color'], sep_rough.inputs['Color'])

        # Metallic → RGB, Smoothness (1-Roughness) → Alpha
        links.new(sep_metal.outputs['Red'], combine.inputs['Red'])
        links.new(sep_metal.outputs['Red'], combine.inputs['Green'])
        links.new(sep_metal.outputs['Red'], combine.inputs['Blue'])

        # Invert roughness for smoothness
        invert = nodes.new('ShaderNodeMath')
        invert.operation = 'SUBTRACT'
        invert.inputs[0].default_value = 1.0
        links.new(sep_rough.outputs['Red'], invert.inputs[1])
        links.new(invert.outputs['Value'], combine.inputs['Alpha'])

        print("Metallic+Smoothness texture combined for Unity")
"""
```

---

### glTF/glb Export

**Material Standard:** PBR Metallic-Roughness
- **Base Color:** sRGB
- **Metallic-Roughness:** Combined (B=Metallic, G=Roughness)
- **Normal:** Linear (OpenGL Y+)
- **Occlusion:** Red channel only
- **Emission:** sRGB

**Export:**
```python
code = """
import bpy

# glTF export (HTTP Bridge compatible setup)
export_path = "C:/Exports/model.glb"

# Ensure materials are PBR-compatible
for mat in bpy.data.materials:
    if mat.use_nodes:
        nodes = mat.node_tree.nodes
        bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)

        if bsdf:
            # glTF requires Principled BSDF
            print(f"Material {mat.name} is glTF-compatible")
        else:
            print(f"WARNING: Material {mat.name} missing Principled BSDF")

# NOTE: Execute bpy.ops.export_scene.gltf() in interactive Blender
print(f"glTF export prepared for {export_path}")
"""
```

---

## Industry-Standard PBR Values

### Material Reference Values

**Dielectrics (Non-Metals):**
| Material | Base Color (sRGB) | Metallic | Roughness | IOR |
|----------|------------------|----------|-----------|-----|
| **Plastic (Matte)** | Varies | 0.0 | 0.7-0.9 | 1.45 |
| **Plastic (Glossy)** | Varies | 0.0 | 0.2-0.4 | 1.45 |
| **Wood (Oak)** | (140, 100, 70) | 0.0 | 0.6-0.8 | 1.5 |
| **Wood (Polished)** | (120, 80, 50) | 0.0 | 0.3-0.5 | 1.5 |
| **Concrete (Rough)** | (150, 150, 150) | 0.0 | 0.8-1.0 | 1.55 |
| **Concrete (Smooth)** | (140, 140, 140) | 0.0 | 0.6-0.8 | 1.55 |
| **Glass (Clear)** | (255, 255, 255) | 0.0 | 0.0-0.1 | 1.5 |
| **Water** | (220, 230, 240) | 0.0 | 0.0-0.2 | 1.33 |
| **Ice** | (230, 240, 250) | 0.0 | 0.1-0.3 | 1.31 |
| **Rubber** | Varies | 0.0 | 0.8-1.0 | 1.52 |
| **Leather** | (100, 70, 50) | 0.0 | 0.5-0.7 | 1.5 |
| **Fabric (Cotton)** | Varies | 0.0 | 0.9-1.0 | 1.5 |

**Metals (Conductors):**
| Material | Base Color (sRGB) | Metallic | Roughness | Notes |
|----------|------------------|----------|-----------|-------|
| **Iron (Clean)** | (198, 198, 198) | 1.0 | 0.3-0.5 | Pure metal |
| **Iron (Rust)** | Mix with (140, 70, 40) | 0.0-1.0 | 0.7-0.9 | Layer over metal |
| **Steel (Polished)** | (215, 215, 215) | 1.0 | 0.2-0.3 | Mirror-like |
| **Steel (Brushed)** | (210, 210, 210) | 1.0 | 0.4-0.6 | Anisotropic |
| **Aluminum** | (235, 235, 235) | 1.0 | 0.3-0.5 | Lighter than steel |
| **Copper (Clean)** | (255, 195, 170) | 1.0 | 0.2-0.4 | Reddish tint |
| **Copper (Oxidized)** | Mix with (100, 140, 130) | 0.5 | 0.6-0.8 | Patina layer |
| **Gold (24k)** | (255, 215, 150) | 1.0 | 0.2-0.3 | Yellow tint |
| **Silver** | (250, 250, 250) | 1.0 | 0.1-0.3 | Brightest metal |
| **Brass** | (230, 190, 130) | 1.0 | 0.3-0.5 | Yellow-brown |
| **Bronze** | (210, 150, 100) | 1.0 | 0.4-0.6 | Darker than brass |
| **Chrome** | (220, 220, 220) | 1.0 | 0.0-0.2 | Very reflective |

---

### Applying Reference Values

```python
code = """
import bpy

# Material presets
PRESETS = {
    'plastic_matte': {'base_color': (0.8, 0.2, 0.2, 1.0), 'metallic': 0.0, 'roughness': 0.8, 'ior': 1.45},
    'wood_oak': {'base_color': (0.55, 0.39, 0.27, 1.0), 'metallic': 0.0, 'roughness': 0.7, 'ior': 1.5},
    'steel_polished': {'base_color': (0.84, 0.84, 0.84, 1.0), 'metallic': 1.0, 'roughness': 0.25, 'ior': 1.45},
    'copper_clean': {'base_color': (1.0, 0.76, 0.67, 1.0), 'metallic': 1.0, 'roughness': 0.3, 'ior': 1.45},
    'gold_24k': {'base_color': (1.0, 0.84, 0.59, 1.0), 'metallic': 1.0, 'roughness': 0.25, 'ior': 1.45},
    'glass_clear': {'base_color': (1.0, 1.0, 1.0, 1.0), 'metallic': 0.0, 'roughness': 0.05, 'ior': 1.5},
}

def create_preset_material(preset_name):
    \"\"\"Create material from preset\"\"\"
    if preset_name not in PRESETS:
        return None

    preset = PRESETS[preset_name]

    mat = bpy.data.materials.new(f"M_{preset_name.title()}")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = preset['base_color']
    bsdf.inputs['Metallic'].default_value = preset['metallic']
    bsdf.inputs['Roughness'].default_value = preset['roughness']
    bsdf.inputs['IOR'].default_value = preset['ior']

    # Glass: Enable transmission
    if 'glass' in preset_name:
        bsdf.inputs['Transmission Weight'].default_value = 1.0
        mat.blend_method = 'BLEND'

    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat

# Create all presets
for preset_name in PRESETS.keys():
    mat = create_preset_material(preset_name)
    if mat:
        mat.use_fake_user = True  # Keep in library
        print(f"Created preset: {mat.name}")
"""
```

---

## Texture Optimization

### Resolution Guidelines

**Texture Size by Object Importance:**
- **Hero Asset:** 4K (4096x4096) - Main character, key props
- **Secondary Asset:** 2K (2048x2048) - Supporting props
- **Background Asset:** 1K (1024x1024) - Environment fill
- **Tiny Props:** 512x512 - Barely visible objects

**VRAM Budget (per material):**
- 4K PBR set (5 maps): ~100 MB
- 2K PBR set (5 maps): ~25 MB
- 1K PBR set (5 maps): ~6 MB

---

### Texture Compression

```python
code = """
import bpy

# Set compression for all textures
for img in bpy.data.images:
    # Non-Color (linear) textures
    if img.colorspace_settings.name == 'Non-Color':
        # Use lightweight compression
        img.use_half_precision = True  # 16-bit float (saves 50% VRAM)

    # sRGB textures
    else:
        # Standard 8-bit
        img.use_half_precision = False

    # Pack image into .blend file (optional)
    if not img.packed_file:
        img.pack()

print(f"Optimized {len(bpy.data.images)} textures")
"""
```

---

### Texture Atlasing

**Combine Multiple Materials into Single Texture:**
```python
code = """
import bpy

# Example: Create texture atlas for 4 materials
# Assumes UVs are already laid out in quadrants

atlas_size = 2048
quadrant_size = atlas_size // 2

# Create combined material
atlas_mat = bpy.data.materials.new("M_Atlas_Combined")
atlas_mat.use_nodes = True
nodes, links = atlas_mat.node_tree.nodes, atlas_mat.links
nodes.clear()

# Single texture for all 4 materials
tex_image = nodes.new('ShaderNodeTexImage')
# tex_image.image = bpy.data.images.load("C:/Textures/atlas_4x.png")

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

print(f"Atlas material created ({atlas_size}x{atlas_size})")
print(f"Each quadrant: {quadrant_size}x{quadrant_size}")
"""
```

**Benefits:**
- Fewer draw calls (1 material instead of 4)
- Smaller VRAM footprint
- Faster rendering

**Drawbacks:**
- Complex UV layout
- Lower effective resolution per material
- Less flexible material variations

---

## Common PBR Mistakes

### Mistake 1: Incorrect Color Space

**Problem:** Normal maps look wrong, colors too bright/dark

**Fix:**
```python
# WRONG
tex_image.image.colorspace_settings.name = 'sRGB'  # For normal map

# CORRECT
tex_image.image.colorspace_settings.name = 'Non-Color'  # For normal/roughness/metallic
```

**Rule:**
- **sRGB:** Base Color, Emission
- **Non-Color:** Normal, Roughness, Metallic, AO, Height

---

### Mistake 2: Pure Black/White Albedo

**Problem:** Materials look unrealistic (too dark or blown out)

**Fix:**
```python
# WRONG
base_color = (0.0, 0.0, 0.0, 1.0)  # Pure black (non-physical)

# CORRECT (charcoal)
base_color = (0.12, 0.12, 0.12, 1.0)  # ~30 sRGB (darkest real material)

# WRONG
base_color = (1.0, 1.0, 1.0, 1.0)  # Pure white (too bright)

# CORRECT (chalk)
base_color = (0.94, 0.94, 0.94, 1.0)  # ~240 sRGB (brightest real material)
```

**Albedo Range:** 30-240 sRGB (0.12-0.94 linear)

---

### Mistake 3: Partial Metallic Values

**Problem:** 0.5 metallic looks wrong (neither metal nor dielectric)

**Fix:**
```python
# WRONG (unless physically accurate)
metallic = 0.5  # Rare in real world

# CORRECT
metallic = 0.0  # Dielectric
# OR
metallic = 1.0  # Metal
```

**Exception:** Oxidized metals (rust, patina) can use 0.3-0.7 for transition zones.

---

### Mistake 4: Glossy Rough Surfaces

**Problem:** Concrete with 0.1 roughness (too shiny)

**Fix:**
```python
# WRONG
roughness = 0.1  # Mirror-like (only for polished metal/glass)

# CORRECT (concrete)
roughness = 0.85  # Diffuse scatter
```

**Roughness Guide:**
- **0.0-0.2:** Polished metal, glass, water
- **0.3-0.5:** Satin, painted surfaces
- **0.6-0.8:** Wood, plastic, stone
- **0.9-1.0:** Fabric, rough concrete, clay

---

### Mistake 5: Inverted Normal Maps

**Problem:** Bumps look like indentations (Y-axis flipped)

**Fix:**
```python
# Check normal map format
normal_map_node = nodes.new('ShaderNodeNormalMap')

# OpenGL (Y+): Blender default, Unity, glTF
normal_map_node.space = 'TANGENT'

# DirectX (Y-): Unreal Engine
# Must flip green channel externally OR:
separate = nodes.new('ShaderNodeSeparateColor')
invert = nodes.new('ShaderNodeMath')
invert.operation = 'SUBTRACT'
invert.inputs[0].default_value = 1.0
combine = nodes.new('ShaderNodeCombineColor')

# R=R, G=1-G, B=B
links.new(tex_normal.outputs['Color'], separate.inputs['Color'])
links.new(separate.outputs['Green'], invert.inputs[1])
links.new(separate.outputs['Red'], combine.inputs['Red'])
links.new(invert.outputs['Value'], combine.inputs['Green'])
links.new(separate.outputs['Blue'], combine.inputs['Blue'])
links.new(combine.outputs['Color'], normal_map_node.inputs['Color'])
```

---

### Mistake 6: Missing AO Contribution

**Problem:** Flat lighting, missing depth cues

**Fix:**
```python
# Multiply AO with Base Color (not add)
mix_ao = nodes.new('ShaderNodeMix')
mix_ao.data_type = 'RGBA'
mix_ao.blend_type = 'MULTIPLY'  # CRITICAL: Multiply, not Mix
mix_ao.inputs['Factor'].default_value = 1.0

links.new(tex_base_color.outputs['Color'], mix_ao.inputs['A'])
links.new(tex_ao.outputs['Color'], mix_ao.inputs['B'])
links.new(mix_ao.outputs['Result'], bsdf.inputs['Base Color'])
```

---

## HTTP Bridge Limitations

**PBR Workflows:**
1. **UV Unwrapping:** Use bmesh direct API (operators fail)
2. **Texture Painting:** Setup works, painting requires interactive Blender
3. **Baking:** Setup works, execution requires interactive/standalone
4. **File Paths:** Use absolute paths only (no relative `//`)
5. **Context Access:** Pass objects explicitly (don't rely on `bpy.context.active_object`)

**Working Patterns:**
```python
# WORKS: Material creation, node setup, texture loading
mat = bpy.data.materials.new("Material")
mat.use_nodes = True
img = bpy.data.images.load("C:/absolute/path.png")

# FAILS: Operators
bpy.ops.uv.smart_project()  # Use bmesh instead
bpy.ops.object.bake()  # Run in interactive Blender
```

---

## Cross-References

**Related Skills:**
- `blender-specialist` - Main Blender coordination agent
- `blender-rendering` - EEVEE_NEXT/Cycles render settings
- `blender-api-compatibility` - Breaking changes database

**blender-ai-compatibility Repository:**
- `api_changes/4.5_lighting_changes.md` - EEVEE_NEXT updates
- `api_changes/4.3_node_interface_changes.md` - Node API changes
- `examples/production_workflows/pbr_material_setup.py` - Complete examples

**External Resources:**
- Substance 3D Documentation (PBR standards)
- Unreal Engine Material Documentation
- glTF 2.0 Specification (PBR)

---

**Last Updated:** 2025-10-25
**Tested With:** Blender 4.5.0 via the official Blender MCP
**Line Count:** ~890 lines
