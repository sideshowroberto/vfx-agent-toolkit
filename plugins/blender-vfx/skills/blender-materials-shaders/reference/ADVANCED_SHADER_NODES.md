# Advanced Shader Nodes Reference

**Skill:** blender-materials-shaders
**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Blender Version:** 4.5.0+
**Requires:** official Blender MCP (blender.org)

---

## Table of Contents

1. [Complex Node Trees](#complex-node-trees)
2. [Shader Mixing Strategies](#shader-mixing-strategies)
3. [Custom Shader Networks](#custom-shader-networks)
4. [Node Group Creation](#node-group-creation)
5. [Performance Optimization](#performance-optimization)
6. [EEVEE_NEXT vs Cycles Differences](#eevee_next-vs-cycles-differences)
7. [Advanced Node Techniques](#advanced-node-techniques)
8. [Material Utilities](#material-utilities)

---

## Complex Node Trees

### Multi-Layer Material System

**Use Case:** Realistic surfaces with multiple material layers (base metal, scratches, dirt, rust)

```python
import requests
# Execute via the Blender MCP tool: execute_blender_code
code = """
import bpy

# Create complex layered metal material
mat = bpy.data.materials.new("Complex_Metal")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Positioning helper (for viewport organization)
x_offset = 0

# === LAYER 1: Base Metal ===
metal_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
metal_bsdf.location = (x_offset, 300)
metal_bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
metal_bsdf.inputs['Metallic'].default_value = 1.0
metal_bsdf.inputs['Roughness'].default_value = 0.2

# === LAYER 2: Scratches ===
scratch_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
scratch_bsdf.location = (x_offset, 100)
scratch_bsdf.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1.0)
scratch_bsdf.inputs['Metallic'].default_value = 0.8
scratch_bsdf.inputs['Roughness'].default_value = 0.6

# Scratch pattern (Voronoi for linear scratches)
scratch_voronoi = nodes.new('ShaderNodeTexVoronoi')
scratch_voronoi.location = (x_offset - 600, 100)
scratch_voronoi.voronoi_dimensions = '2D'
scratch_voronoi.feature = 'DISTANCE_TO_EDGE'
scratch_voronoi.inputs['Scale'].default_value = 20.0

scratch_ramp = nodes.new('ShaderNodeValToRGB')
scratch_ramp.location = (x_offset - 300, 100)
scratch_ramp.color_ramp.elements[0].position = 0.4
scratch_ramp.color_ramp.elements[1].position = 0.5

links.new(scratch_voronoi.outputs['Distance'], scratch_ramp.inputs['Fac'])

# Mix scratches with base metal
mix_scratch = nodes.new('ShaderNodeMixShader')
mix_scratch.location = (x_offset + 300, 200)
links.new(scratch_ramp.outputs['Color'], mix_scratch.inputs['Fac'])
links.new(metal_bsdf.outputs['BSDF'], mix_scratch.inputs[1])
links.new(scratch_bsdf.outputs['BSDF'], mix_scratch.inputs[2])

# === LAYER 3: Rust/Dirt ===
rust_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
rust_bsdf.location = (x_offset, -100)
rust_bsdf.inputs['Base Color'].default_value = (0.5, 0.25, 0.1, 1.0)
rust_bsdf.inputs['Metallic'].default_value = 0.0
rust_bsdf.inputs['Roughness'].default_value = 0.9

# Rust pattern (Noise for organic growth)
rust_noise = nodes.new('ShaderNodeTexNoise')
rust_noise.location = (x_offset - 600, -100)
rust_noise.inputs['Scale'].default_value = 5.0
rust_noise.inputs['Detail'].default_value = 10.0

rust_ramp = nodes.new('ShaderNodeValToRGB')
rust_ramp.location = (x_offset - 300, -100)
rust_ramp.color_ramp.elements[0].position = 0.3
rust_ramp.color_ramp.elements[1].position = 0.7

links.new(rust_noise.outputs['Fac'], rust_ramp.inputs['Fac'])

# Mix rust with previous layers
mix_rust = nodes.new('ShaderNodeMixShader')
mix_rust.location = (x_offset + 600, 0)
links.new(rust_ramp.outputs['Color'], mix_rust.inputs['Fac'])
links.new(mix_scratch.outputs['Shader'], mix_rust.inputs[1])
links.new(rust_bsdf.outputs['BSDF'], mix_rust.inputs[2])

# === OUTPUT ===
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (x_offset + 900, 0)
links.new(mix_rust.outputs['Shader'], output.inputs['Surface'])

# Assign to active object
obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat
"""

response = requests.post(url, json={"code": code})
print(response.json())
```

**Node Tree Diagram:**
```
Voronoi(Scratches) → ColorRamp → MixShader1[Fac]
Metal_BSDF ────────────────────→ MixShader1[1]
Scratch_BSDF ──────────────────→ MixShader1[2]
                                      ↓
Noise(Rust) → ColorRamp → MixShader2[Fac]
MixShader1[Output] ───────────→ MixShader2[1]
Rust_BSDF ────────────────────→ MixShader2[2]
                                      ↓
                                Material Output
```

---

### Subsurface Scattering (SSS) Setup

**Use Case:** Organic materials (skin, wax, marble, jade)

```python
# Via HTTP Bridge
code = """
import bpy

mat = bpy.data.materials.new("SSS_Skin")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Principled BSDF with SSS
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.location = (0, 0)

# Subsurface parameters (skin values)
bsdf.inputs['Base Color'].default_value = (0.8, 0.6, 0.5, 1.0)
bsdf.inputs['Subsurface Weight'].default_value = 0.15  # 15% SSS
bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.5, 0.25)  # RGB scattering
bsdf.inputs['Subsurface Scale'].default_value = 0.05  # Scale factor
bsdf.inputs['Subsurface IOR'].default_value = 1.4  # Skin IOR
bsdf.inputs['Roughness'].default_value = 0.4

# Add texture variation (optional)
texcoord = nodes.new('ShaderNodeTexCoord')
texcoord.location = (-800, 0)

noise = nodes.new('ShaderNodeTexNoise')
noise.location = (-600, 0)
noise.inputs['Scale'].default_value = 3.0
noise.inputs['Detail'].default_value = 5.0

# Color variation
color_mix = nodes.new('ShaderNodeMix')
color_mix.data_type = 'RGBA'
color_mix.location = (-300, 100)
color_mix.inputs['A'].default_value = (0.8, 0.6, 0.5, 1.0)  # Base
color_mix.inputs['B'].default_value = (0.6, 0.4, 0.3, 1.0)  # Variation

links.new(texcoord.outputs['Object'], noise.inputs['Vector'])
links.new(noise.outputs['Fac'], color_mix.inputs['Factor'])
links.new(color_mix.outputs['Result'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""

response = requests.post(url, json={"code": code})
```

**SSS Parameters Guide:**
- **Weight:** 0.0-0.3 (0 = no SSS, 0.3 = wax)
- **Radius:** RGB channels for different penetration depths
  - Red: Deep scattering (blood)
  - Green: Medium scattering
  - Blue: Shallow scattering (surface detail)
- **Scale:** Overall scattering distance (0.01-1.0)
- **IOR:** 1.3-1.5 for organic materials

**EEVEE_NEXT vs Cycles:**
- **EEVEE_NEXT:** Uses screen-space approximation (fast, limited accuracy)
- **Cycles:** Ray-traced SSS (accurate but slower)

---

## Shader Mixing Strategies

### Mix Shader vs Mix RGB

**Critical Difference:**
- **Mix Shader:** Mixes two BSDF shaders (physically correct)
- **Mix RGB:** Mixes colors/values (mathematical operation)

```python
# CORRECT: Mix Shader for combining materials
code = """
import bpy

mat = bpy.data.materials.new("Mixed_Shaders")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Two different materials
diffuse = nodes.new('ShaderNodeBsdfPrincipled')
diffuse.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)

glossy = nodes.new('ShaderNodeBsdfPrincipled')
glossy.inputs['Base Color'].default_value = (0.2, 0.2, 0.8, 1.0)
glossy.inputs['Metallic'].default_value = 1.0

# Mix Shader (not Mix RGB!)
mix = nodes.new('ShaderNodeMixShader')
mix.inputs['Fac'].default_value = 0.5

links.new(diffuse.outputs['BSDF'], mix.inputs[1])
links.new(glossy.outputs['BSDF'], mix.inputs[2])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(mix.outputs['Shader'], output.inputs['Surface'])
"""
```

**When to Use Each:**
- **Mix Shader:** Combining materials (metal+plastic, clean+dirty)
- **Mix (Color):** Blending textures/colors before BSDF
- **Mix (Float):** Blending scalar values (roughness, metallic)

---

### Layer Weight for Realistic Mixing

**Use Case:** Physically-based mixing using viewing angle (Fresnel)

```python
code = """
import bpy

mat = bpy.data.materials.new("Fresnel_Mix")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Layer Weight (provides Fresnel/Facing)
layer_weight = nodes.new('ShaderNodeLayerWeight')
layer_weight.location = (-600, 0)
layer_weight.inputs['Blend'].default_value = 0.5  # 0 = sharp, 1 = soft

# Base material (viewed straight on)
base_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
base_bsdf.location = (-300, 200)
base_bsdf.inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)

# Edge material (viewed at grazing angles)
edge_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
edge_bsdf.location = (-300, -200)
edge_bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)

# Mix based on viewing angle
mix = nodes.new('ShaderNodeMixShader')
mix.location = (0, 0)
links.new(layer_weight.outputs['Facing'], mix.inputs['Fac'])
links.new(base_bsdf.outputs['BSDF'], mix.inputs[1])
links.new(edge_bsdf.outputs['BSDF'], mix.inputs[2])

output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)
links.new(mix.outputs['Shader'], output.inputs['Surface'])
"""
```

**Layer Weight Outputs:**
- **Facing:** 0 = perpendicular, 1 = grazing angles (Fresnel)
- **Fresnel:** More accurate IOR-based falloff (same as Facing with IOR=1.45)

---

## Custom Shader Networks

### Anisotropic Metal (Brushed Metal)

```python
code = """
import bpy

mat = bpy.data.materials.new("Brushed_Metal")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Anisotropic BSDF (not Principled)
anisotropic = nodes.new('ShaderNodeBsdfAnisotropic')
anisotropic.location = (0, 0)
anisotropic.distribution = 'GGX'
anisotropic.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1.0)
anisotropic.inputs['Roughness'].default_value = 0.3
anisotropic.inputs['Anisotropy'].default_value = 0.8  # 0 = isotropic, 1 = max anisotropy

# Tangent direction (defines brush direction)
tangent = nodes.new('ShaderNodeTangent')
tangent.location = (-300, -100)
tangent.direction_type = 'UV_MAP'

links.new(tangent.outputs['Tangent'], anisotropic.inputs['Tangent'])

output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)
links.new(anisotropic.outputs['BSDF'], output.inputs['Surface'])
"""
```

**Anisotropic Parameters:**
- **Anisotropy:** 0.0-1.0 (0 = round highlights, 1 = streaked highlights)
- **Rotation:** 0.0-1.0 (rotates highlight direction)
- **Tangent:** UV-based or radial direction

**Common Uses:**
- Brushed aluminum
- CD/DVD surfaces
- Hair/fur
- Satin fabric

---

### Emission with HDR Control

```python
code = """
import bpy

mat = bpy.data.materials.new("HDR_Emission")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Emission shader
emission = nodes.new('ShaderNodeEmission')
emission.location = (0, 0)
emission.inputs['Color'].default_value = (1.0, 0.5, 0.2, 1.0)  # Orange glow
emission.inputs['Strength'].default_value = 10.0  # HDR value (>1.0 for bloom)

# Optional: Texture for emission pattern
texcoord = nodes.new('ShaderNodeTexCoord')
texcoord.location = (-600, 0)

voronoi = nodes.new('ShaderNodeTexVoronoi')
voronoi.location = (-400, 0)
voronoi.voronoi_dimensions = '3D'
voronoi.inputs['Scale'].default_value = 5.0

# Use Voronoi as emission mask
color_mix = nodes.new('ShaderNodeMix')
color_mix.data_type = 'RGBA'
color_mix.location = (-200, 100)
color_mix.inputs['A'].default_value = (0.0, 0.0, 0.0, 1.0)  # Off
color_mix.inputs['B'].default_value = (1.0, 0.5, 0.2, 1.0)  # On

links.new(texcoord.outputs['Object'], voronoi.inputs['Vector'])
links.new(voronoi.outputs['Distance'], color_mix.inputs['Factor'])
links.new(color_mix.outputs['Result'], emission.inputs['Color'])

output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)
links.new(emission.outputs['Emission'], output.inputs['Surface'])
"""
```

**Emission Strength Guide:**
- **0.0-1.0:** Standard range (no bloom in EEVEE_NEXT)
- **>1.0:** HDR emission (creates bloom if enabled)
- **10-100:** Strong light sources (neon, fire)
- **1000+:** Sun-like intensity

**EEVEE_NEXT Bloom Setup:**
```python
# Enable bloom in scene settings
bpy.context.scene.eevee.use_bloom = True
bpy.context.scene.eevee.bloom_threshold = 1.0
bpy.context.scene.eevee.bloom_intensity = 0.5
```

---

## Node Group Creation

### Creating Reusable Node Groups

**Use Case:** Weathering, damage, or any repeatable shader pattern

```python
code = """
import bpy

# Create node group
group = bpy.data.node_groups.new("Weathering_Mask", 'ShaderNodeTree')
group_nodes = group.nodes
group_links = group.links

# Create input/output nodes
group_in = group_nodes.new('NodeGroupInput')
group_in.location = (-600, 0)

group_out = group_nodes.new('NodeGroupOutput')
group_out.location = (600, 0)

# Define interface (inputs/outputs)
# NOTE: Blender 4.5 uses group.interface.new_socket()
group.interface.new_socket("Scale", in_out='INPUT', socket_type='NodeSocketFloat')
group.interface.new_socket("Detail", in_out='INPUT', socket_type='NodeSocketFloat')
group.interface.new_socket("Roughness", in_out='INPUT', socket_type='NodeSocketFloat')
group.interface.new_socket("Mask", in_out='OUTPUT', socket_type='NodeSocketFloat')

# Set default values
group.interface.items_tree['Scale'].default_value = 5.0
group.interface.items_tree['Detail'].default_value = 2.0
group.interface.items_tree['Roughness'].default_value = 0.5

# Internal nodes
noise1 = group_nodes.new('ShaderNodeTexNoise')
noise1.location = (-400, 100)

noise2 = group_nodes.new('ShaderNodeTexNoise')
noise2.location = (-400, -100)

mix = group_nodes.new('ShaderNodeMix')
mix.data_type = 'FLOAT'
mix.location = (-200, 0)

ramp = group_nodes.new('ShaderNodeValToRGB')
ramp.location = (0, 0)
ramp.color_ramp.elements[0].position = 0.3
ramp.color_ramp.elements[1].position = 0.7

# Connect internal nodes
group_links.new(group_in.outputs['Scale'], noise1.inputs['Scale'])
group_links.new(group_in.outputs['Detail'], noise1.inputs['Detail'])
group_links.new(group_in.outputs['Scale'], noise2.inputs['Scale'])

group_links.new(noise1.outputs['Fac'], mix.inputs['A'])
group_links.new(noise2.outputs['Fac'], mix.inputs['B'])
group_links.new(group_in.outputs['Roughness'], mix.inputs['Factor'])

group_links.new(mix.outputs['Result'], ramp.inputs['Fac'])
group_links.new(ramp.outputs['Color'], group_out.inputs['Mask'])

# === USE THE GROUP ===
mat = bpy.data.materials.new("Material_With_Group")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Instance the node group
group_node = nodes.new('ShaderNodeGroup')
group_node.node_tree = group
group_node.location = (-300, 0)
group_node.inputs['Scale'].default_value = 8.0

# Use output
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.location = (0, 0)

links.new(group_node.outputs['Mask'], bsdf.inputs['Roughness'])

output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

**Node Group Best Practices:**
- Keep inputs/outputs to 3-5 sockets (usability)
- Name sockets clearly ("Scale" not "Input_1")
- Set sensible default values
- Document purpose in group name
- Version complex groups (Weathering_v1, Weathering_v2)

---

### Appending Node Groups from Libraries

```python
# Load node group from external .blend file
code = """
import bpy

library_path = "C:/Materials/material_library.blend"
node_group_name = "Weathering_Mask"

# Append node group
with bpy.data.libraries.load(library_path, link=False) as (data_from, data_to):
    if node_group_name in data_from.node_groups:
        data_to.node_groups = [node_group_name]

# Use in material
mat = bpy.data.materials.new("Appended_Material")
mat.use_nodes = True
nodes = mat.node_tree.nodes

group_node = nodes.new('ShaderNodeGroup')
group_node.node_tree = bpy.data.node_groups[node_group_name]
"""
```

**HTTP Bridge Limitation:** File I/O works, but use absolute paths (no relative paths in HTTP context).

---

## Performance Optimization

### Shader Complexity Analysis

**Node Count Guidelines:**
- **EEVEE_NEXT (Real-time):** <10 nodes for 60fps, <20 for 30fps
- **Cycles (Offline):** <50 nodes recommended (diminishing returns beyond this)

**Performance Costs (Relative):**
- **Cheap:** ColorRamp, Mix, Math nodes
- **Medium:** Texture nodes (Noise, Voronoi, Musgrave)
- **Expensive:** Multiple Mix Shaders, displacement
- **Very Expensive:** Volumetrics, SSS with high scatter distance

```python
# Measure shader complexity
code = """
import bpy

mat = bpy.data.materials['YourMaterial']
if mat.use_nodes:
    node_count = len(mat.node_tree.nodes)
    link_count = len(mat.node_tree.links)

    mix_shaders = [n for n in mat.node_tree.nodes if n.type == 'MIX_SHADER']
    texture_nodes = [n for n in mat.node_tree.nodes if 'TEX' in n.type]

    print(f"Total Nodes: {node_count}")
    print(f"Mix Shaders: {len(mix_shaders)} (expensive)")
    print(f"Texture Nodes: {len(texture_nodes)} (medium)")
    print(f"Complexity: {'High' if node_count > 20 else 'Medium' if node_count > 10 else 'Low'}")
"""
```

---

### Shader Simplification Techniques

**1. Combine Texture Nodes**
```python
# SLOW: Multiple noise textures
noise1 = nodes.new('ShaderNodeTexNoise')
noise2 = nodes.new('ShaderNodeTexNoise')
mix = nodes.new('ShaderNodeMix')

# FAST: Single texture with ColorRamp
noise = nodes.new('ShaderNodeTexNoise')
ramp = nodes.new('ShaderNodeValToRGB')
# Adjust ramp elements for variation
```

**2. Use Mix Node Instead of Mix Shader**
```python
# SLOW: Mix two complete BSDFs
bsdf1 = nodes.new('ShaderNodeBsdfPrincipled')
bsdf2 = nodes.new('ShaderNodeBsdfPrincipled')
mix_shader = nodes.new('ShaderNodeMixShader')

# FAST: Mix input values into one BSDF
color_mix = nodes.new('ShaderNodeMix')
color_mix.data_type = 'RGBA'
# Mix colors before BSDF, use single Principled
```

**3. Texture Resolution Control**
```python
# Use ColorRamp to reduce texture detail
noise = nodes.new('ShaderNodeTexNoise')
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'CONSTANT'  # Posterize effect = fewer samples
```

---

### Material Instancing

**Use Case:** Thousands of objects with slight material variations

```python
code = """
import bpy

# Base material
base_mat = bpy.data.materials.new("Base_Material")
base_mat.use_nodes = True
nodes = base_mat.node_tree.nodes
links = base_mat.node_tree.links
nodes.clear()

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

# Create instances with variations
import random

for i in range(100):
    obj = bpy.data.objects.get(f"Object_{i}")
    if obj:
        # Share material (instances)
        if len(obj.data.materials) == 0:
            obj.data.materials.append(base_mat)

        # Override color per object (using Object Info node in material)
        # OR create material copy with variation:
        mat_instance = base_mat.copy()
        mat_instance.name = f"Material_{i}"

        # Vary color
        bsdf = mat_instance.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (
            random.uniform(0.5, 1.0),
            random.uniform(0.2, 0.5),
            random.uniform(0.1, 0.3),
            1.0
        )

        obj.data.materials[0] = mat_instance
"""
```

**Instancing vs Copying:**
- **Same Material:** 1000 objects = 1 shader compiled (fast)
- **1000 Copies:** 1000 shaders compiled (slow startup, same runtime)

---

## EEVEE_NEXT vs Cycles Differences

### Render Engine Detection

```python
code = """
import bpy

engine = bpy.context.scene.render.engine

if engine == 'BLENDER_EEVEE_NEXT':
    print("EEVEE_NEXT: Real-time, screen-space effects")
elif engine == 'CYCLES':
    print("Cycles: Ray-traced, physically accurate")
else:
    print(f"Unknown engine: {engine}")
"""
```

---

### Feature Comparison Table

| Feature | EEVEE_NEXT | Cycles | Notes |
|---------|-----------|--------|-------|
| **Subsurface Scattering** | Screen-space approx | Ray-traced | Cycles more accurate |
| **Caustics** | No | Yes | Use Cycles for glass focus |
| **Volumetrics** | Limited | Full ray-marching | Cycles for fog/smoke |
| **Displacement** | Bump only | True displacement | Cycles can deform geometry |
| **Transparent Shadows** | Limited | Full | Cycles for colored glass shadows |
| **Refraction** | Screen-space | Ray-traced | Enable SSR in EEVEE_NEXT |
| **Ambient Occlusion** | Screen-space | Ray-traced | Both supported |
| **Speed** | Real-time (60fps+) | Offline (minutes) | EEVEE for preview |

---

### Engine-Specific Material Setup

**EEVEE_NEXT Optimizations:**
```python
code = """
import bpy

mat = bpy.data.materials.new("EEVEE_Optimized")
mat.use_nodes = True

# EEVEE_NEXT settings
mat.use_backface_culling = True  # Skip backfaces (2x faster)
mat.blend_method = 'OPAQUE'  # Avoid alpha sorting overhead
mat.shadow_method = 'OPAQUE'  # Faster shadow rendering

# Scene settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.use_ssr = True  # Screen-space reflections
scene.eevee.use_ssr_refraction = True  # Screen-space refraction
scene.eevee.use_gtao = True  # Ground-truth AO (better quality)
"""
```

**Cycles Optimizations:**
```python
code = """
import bpy

scene = bpy.context.scene
scene.render.engine = 'CYCLES'

# Device settings
scene.cycles.device = 'GPU'  # Use GPU if available

# Sample settings
scene.cycles.samples = 128  # Preview: 32-128, Final: 512-4096
scene.cycles.use_adaptive_sampling = True  # Stop early if converged
scene.cycles.adaptive_threshold = 0.01  # Lower = more accurate

# Denoising (AI-powered noise reduction)
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'  # Best quality
"""
```

---

### Material Fallback Pattern

**Use Case:** Create material that works in both engines

```python
code = """
import bpy

mat = bpy.data.materials.new("Universal_Material")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Detect engine at render time (not edit time)
# Use shader that works in both

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.location = (0, 0)

# Settings that work in both
bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)
bsdf.inputs['Metallic'].default_value = 0.5
bsdf.inputs['Roughness'].default_value = 0.4

# Conditional SSS (works better in Cycles, but acceptable in EEVEE_NEXT)
bsdf.inputs['Subsurface Weight'].default_value = 0.1

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

# Engine-specific scene setup (run separately)
engine = bpy.context.scene.render.engine
if engine == 'BLENDER_EEVEE_NEXT':
    # Enable SSR for reflections
    bpy.context.scene.eevee.use_ssr = True
elif engine == 'CYCLES':
    # Increase samples for quality
    bpy.context.scene.cycles.samples = 256
"""
```

---

## Advanced Node Techniques

### Math Node Tricks

**1. Gradient Mapping (Altitude-based Coloring)**
```python
code = """
import bpy

mat = bpy.data.materials.new("Altitude_Gradient")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Get Z-coordinate of object
texcoord = nodes.new('ShaderNodeTexCoord')
separate_xyz = nodes.new('ShaderNodeSeparateXYZ')
links.new(texcoord.outputs['Object'], separate_xyz.inputs['Vector'])

# Normalize Z (0-1 range)
math_normalize = nodes.new('ShaderNodeMath')
math_normalize.operation = 'MULTIPLY'
math_normalize.inputs[1].default_value = 0.1  # Adjust for scale

# Color ramp for gradient
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0.1, 0.3, 0.1, 1.0)  # Low = green
ramp.color_ramp.elements[1].position = 1.0
ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)  # High = white

links.new(separate_xyz.outputs['Z'], math_normalize.inputs[0])
links.new(math_normalize.outputs['Value'], ramp.inputs['Fac'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

**2. Mask Generation (Isolate Top Faces)**
```python
code = """
import bpy

mat = bpy.data.materials.new("Top_Face_Mask")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Geometry node (provides normal vector)
geometry = nodes.new('ShaderNodeNewGeometry')

# Separate normal components
separate_xyz = nodes.new('ShaderNodeSeparateXYZ')
links.new(geometry.outputs['Normal'], separate_xyz.inputs['Vector'])

# Z-normal > 0.9 = top faces
math_greater = nodes.new('ShaderNodeMath')
math_greater.operation = 'GREATER_THAN'
math_greater.inputs[1].default_value = 0.9  # Threshold

links.new(separate_xyz.outputs['Z'], math_greater.inputs[0])

# Use mask
ramp = nodes.new('ShaderNodeValToRGB')
links.new(math_greater.outputs['Value'], ramp.inputs['Fac'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

**Math Node Operations:**
- **GREATER_THAN:** Threshold masking
- **MULTIPLY/DIVIDE:** Scaling values
- **POWER:** Contrast adjustment
- **MODULO:** Tiling/repeating patterns
- **SNAP:** Posterization/quantization

---

### Mapping Node (Texture Transformations)

```python
code = """
import bpy

mat = bpy.data.materials.new("Transformed_Texture")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# Mapping node (translate, rotate, scale)
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Location'].default_value = (0.5, 0.5, 0.0)  # Offset
mapping.inputs['Rotation'].default_value = (0.0, 0.0, 0.785)  # 45° rotation (radians)
mapping.inputs['Scale'].default_value = (2.0, 2.0, 1.0)  # 2x tiling

noise = nodes.new('ShaderNodeTexNoise')
links.new(texcoord.outputs['Generated'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], noise.inputs['Vector'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(noise.outputs['Fac'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

**Common Use Cases:**
- **Location:** Center texture on object
- **Rotation:** Align wood grain, directional scratches
- **Scale:** Control tiling density

---

### Bump and Normal Mapping

**Bump Mapping (Height-based):**
```python
code = """
import bpy

mat = bpy.data.materials.new("Bump_Mapped")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Texture for bump
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 10.0

# Bump node
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.5  # 0-1 (subtle to extreme)
bump.inputs['Distance'].default_value = 0.1  # Ray offset distance

links.new(noise.outputs['Fac'], bump.inputs['Height'])

# Connect to BSDF normal
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

**Normal Mapping (RGB Texture):**
```python
code = """
import bpy

mat = bpy.data.materials.new("Normal_Mapped")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Image texture (normal map)
tex_image = nodes.new('ShaderNodeTexImage')
# tex_image.image = bpy.data.images.load("C:/Textures/normal_map.png")

# Normal Map node
normal_map = nodes.new('ShaderNodeNormalMap')
normal_map.inputs['Strength'].default_value = 1.0

links.new(tex_image.outputs['Color'], normal_map.inputs['Color'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

**Bump vs Normal Map:**
- **Bump:** Procedural, generated from grayscale height
- **Normal Map:** Baked RGB texture (higher quality, pre-computed)

---

## Material Utilities

### Batch Material Assignment

```python
code = """
import bpy

# Assign material to all selected objects
mat = bpy.data.materials.get("YourMaterial")
if not mat:
    mat = bpy.data.materials.new("YourMaterial")
    mat.use_nodes = True

for obj in bpy.context.selected_objects:
    if obj.type == 'MESH':
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
"""
```

---

### Material Slot Management

```python
code = """
import bpy

obj = bpy.context.active_object

# Add material slot
obj.data.materials.append(None)  # Empty slot

# Assign material to slot
mat = bpy.data.materials.get("Material1")
obj.data.materials[0] = mat

# Remove unused slots
for i in range(len(obj.data.materials) - 1, -1, -1):
    if obj.data.materials[i] is None:
        obj.data.materials.pop(index=i)
"""
```

---

### Material Cleanup

```python
code = """
import bpy

# Remove unused materials
for mat in bpy.data.materials:
    if not mat.users:
        bpy.data.materials.remove(mat)

# Remove duplicate materials (Material.001, Material.002)
import re
for mat in bpy.data.materials:
    match = re.match(r'(.+)\\.\\d{3}$', mat.name)
    if match:
        base_name = match.group(1)
        base_mat = bpy.data.materials.get(base_name)
        if base_mat:
            # Remap users to base material
            mat.user_remap(base_mat)
            bpy.data.materials.remove(mat)
"""
```

---

### Material Library Export

```python
code = """
import bpy

# Save selected materials to library file
library_path = "C:/Materials/my_materials.blend"

# Select materials to export
materials_to_export = ["Metal_Brushed", "Glass_Clear", "Plastic_Red"]

# Save blend file with only these materials
bpy.data.libraries.write(
    library_path,
    {mat for mat in bpy.data.materials if mat.name in materials_to_export},
    compress=True
)
"""
```

**HTTP Bridge Note:** File I/O works via HTTP Bridge, but paths must be absolute.

---

## Troubleshooting

### Shader Not Updating in Viewport

**Cause:** Viewport shading not set correctly
**Fix:**
```python
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'
                space.shading.use_scene_lights = True
                space.shading.use_scene_world = True
```

---

### Node Links Not Creating

**Error:** `TypeError: link() argument must be bpy.types.NodeSocket`
**Cause:** Attempting to link incompatible socket types
**Fix:**
```python
# Check socket types
print(f"Output type: {node1.outputs['BSDF'].type}")  # 'SHADER'
print(f"Input type: {node2.inputs['Surface'].type}")  # 'SHADER'

# Only link matching types:
# SHADER → SHADER
# RGBA → RGBA
# VALUE → VALUE
```

---

### Material Renders Black in Cycles

**Causes:**
1. No light sources in scene
2. Material Output not connected
3. BSDF emission = 0 with no external light
4. Transparent material with no background

**Fix:**
```python
# Add sun light
light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_data.energy = 1.0
light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (5, 5, 10)

# Verify material connection
mat = bpy.data.materials['YourMaterial']
nodes = mat.node_tree.nodes
output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
if output and not output.inputs['Surface'].is_linked:
    print("ERROR: Material Output not connected!")
```

---

## HTTP Bridge Limitations

**Known Issues:**
1. **Operators Fail:** `bpy.ops.material.*` doesn't work → Use `bpy.data.materials.new()`
2. **File Paths:** Must be absolute (no `//` relative paths)
3. **Context:** No `bpy.context.active_object` in some cases → Pass object explicitly
4. **UI Updates:** Viewport doesn't auto-refresh → Force redraw via `bpy.ops.wm.redraw_timer()`

**Workarounds:**
```python
# WRONG (operator)
bpy.ops.material.new()

# CORRECT (direct API)
mat = bpy.data.materials.new("Material")
mat.use_nodes = True

# WRONG (relative path)
bpy.data.images.load("//textures/image.png")

# CORRECT (absolute path)
bpy.data.images.load("C:/Project/textures/image.png")
```

---

## Cross-References

**Related Skills:**
- `blender-geometry-nodes` - Procedural modeling, node-based workflows
- `blender-rendering` - EEVEE_NEXT/Cycles settings, lighting
- `blender-api-compatibility` - Breaking changes database

**blender-ai-compatibility Repository:**
- `api_changes/4.5_lighting_changes.md` - EEVEE → EEVEE_NEXT
- `api_changes/4.3_node_interface_changes.md` - Node group interface API
- `examples/production_workflows/pbr_material_setup.py` - Complete PBR examples

---

**Last Updated:** 2025-10-25
**Tested With:** Blender 4.5.0 via the official Blender MCP
**Line Count:** ~950 lines
