# Procedural Textures Reference

**Skill:** blender-materials-shaders
**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Blender Version:** 4.5.0+
**Requires:** official Blender MCP (blender.org)

---

## Table of Contents

1. [Procedural vs Image Textures](#procedural-vs-image-textures)
2. [Texture Coordinate Systems](#texture-coordinate-systems)
3. [Noise Patterns](#noise-patterns)
4. [Voronoi Patterns](#voronoi-patterns)
5. [Wave and Gradient Patterns](#wave-and-gradient-patterns)
6. [Material Recipes](#material-recipes)
7. [Math Node Techniques](#math-node-techniques)
8. [Color Ramp Mastery](#color-ramp-mastery)
9. [UV-less Workflows](#uv-less-workflows)
10. [Performance Optimization](#performance-optimization)

---

## Procedural vs Image Textures

### When to Use Procedural

**Advantages:**
- **No UV unwrapping required** (use Object/Generated coordinates)
- **Infinite resolution** (no pixelation at any distance)
- **Small file size** (no external textures to manage)
- **Real-time variation** (animate with keyframes)
- **Seamless tiling** (no visible seams)

**Disadvantages:**
- **Performance cost** (calculated per pixel)
- **Less artistic control** (harder to paint specific details)
- **Limited complexity** (hard to create specific logos/text)

**Best Use Cases:**
- Natural materials (wood, stone, clouds)
- Abstract patterns (noise, cells, waves)
- Prototyping (quick material blocking)
- Stylized/non-photorealistic rendering

---

### When to Use Image Textures

**Use image textures when:**
- Photorealistic materials (scanned PBR textures)
- Specific branding (logos, labels, signs)
- Performance-critical (mobile, VR)
- Baked lighting (AO, shadow maps)

**Hybrid Approach (Best of Both):**
```python
code = """
import bpy

mat = bpy.data.materials.new("Hybrid_Material")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

# Base: Image texture (PBR base color)
tex_image = nodes.new('ShaderNodeTexImage')
tex_image.location = (-600, 300)
# tex_image.image = bpy.data.images.load("C:/Textures/base.png")

# Variation: Procedural noise
noise = nodes.new('ShaderNodeTexNoise')
noise.location = (-600, -100)
noise.inputs['Scale'].default_value = 5.0

# Combine
mix = nodes.new('ShaderNodeMix')
mix.data_type = 'RGBA'
mix.blend_type = 'OVERLAY'
mix.location = (-300, 100)
mix.inputs['Factor'].default_value = 0.3

links.new(tex_image.outputs['Color'], mix.inputs['A'])
links.new(noise.outputs['Fac'], mix.inputs['B'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

## Texture Coordinate Systems

### Available Coordinate Types

**Texture Coordinate Node Outputs:**

1. **Generated** - Automatic 0-1 range based on bounding box
2. **Normal** - Object surface normal direction
3. **UV** - UV map coordinates (requires unwrapping)
4. **Object** - Object space coordinates (local to object)
5. **Camera** - Camera view space
6. **Window** - Screen space (viewport projection)
7. **Reflection** - Reflection vector (for environment maps)

```python
code = """
import bpy

mat = bpy.data.materials.new("Coordinate_Demo")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')
texcoord.location = (-800, 0)

# Generated (most common for procedural)
noise = nodes.new('ShaderNodeTexNoise')
noise.location = (-500, 200)
links.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

# Object (world-space aligned)
voronoi = nodes.new('ShaderNodeTexVoronoi')
voronoi.location = (-500, -200)
links.new(texcoord.outputs['Object'], voronoi.inputs['Vector'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Generated vs Object Coordinates

**Generated (0-1 bounding box):**
- Scales with object size
- Different per object instance
- Good for: Unique textures per object

**Object (world space):**
- Same world position = same texture
- All objects share pattern
- Good for: Aligned textures across multiple objects

**Example:**
```python
code = """
import bpy

# Create two cubes
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube1 = bpy.context.active_object

bpy.ops.mesh.primitive_cube_add(location=(3, 0, 0))
cube2 = bpy.context.active_object

# Material with Object coordinates
mat = bpy.data.materials.new("World_Aligned")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.0

# Object coordinates = pattern continues across cubes
links.new(texcoord.outputs['Object'], noise.inputs['Vector'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(noise.outputs['Fac'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

# Assign to both cubes
cube1.data.materials.append(mat)
cube2.data.materials.append(mat)

# Result: Seamless pattern across both cubes
"""
```

---

## Noise Patterns

### Noise Texture Node

**Parameters:**
- **Scale:** Pattern frequency (higher = smaller detail)
- **Detail:** Fractal iterations (0-15, higher = more complexity)
- **Roughness:** Contrast between octaves (0-1)
- **Lacunarity:** Frequency multiplier per octave (default 2.0)
- **Distortion:** Warps pattern (0-10+)

**Outputs:**
- **Fac:** Grayscale noise (0-1)
- **Color:** RGB noise (random per channel)

```python
code = """
import bpy

mat = bpy.data.materials.new("Noise_Variations")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# === SMOOTH NOISE (Perlin) ===
noise_smooth = nodes.new('ShaderNodeTexNoise')
noise_smooth.location = (-600, 400)
noise_smooth.inputs['Scale'].default_value = 3.0
noise_smooth.inputs['Detail'].default_value = 2.0  # Low detail = smooth
noise_smooth.inputs['Roughness'].default_value = 0.5

links.new(texcoord.outputs['Generated'], noise_smooth.inputs['Vector'])

# === DETAILED NOISE (Fractal) ===
noise_detailed = nodes.new('ShaderNodeTexNoise')
noise_detailed.location = (-600, 100)
noise_detailed.inputs['Scale'].default_value = 5.0
noise_detailed.inputs['Detail'].default_value = 10.0  # High detail = fractal
noise_detailed.inputs['Roughness'].default_value = 0.7

links.new(texcoord.outputs['Generated'], noise_detailed.inputs['Vector'])

# === DISTORTED NOISE (Warped) ===
noise_distorted = nodes.new('ShaderNodeTexNoise')
noise_distorted.location = (-600, -200)
noise_distorted.inputs['Scale'].default_value = 4.0
noise_distorted.inputs['Detail'].default_value = 5.0
noise_distorted.inputs['Distortion'].default_value = 5.0  # Warped pattern

links.new(texcoord.outputs['Generated'], noise_distorted.inputs['Vector'])

# Use one (example: smooth)
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(noise_smooth.outputs['Fac'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Noise Applications

**1. Cloud/Smoke:**
```python
code = """
import bpy

mat = bpy.data.materials.new("Clouds")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 2.0
noise.inputs['Detail'].default_value = 8.0
noise.inputs['Roughness'].default_value = 0.6

links.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

# Color ramp for cloud definition
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.4
ramp.color_ramp.elements[1].position = 0.6

links.new(noise.outputs['Fac'], ramp.inputs['Fac'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

**2. Organic Roughness Variation:**
```python
code = """
import bpy

mat = bpy.data.materials.new("Varied_Roughness")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# Fine noise for roughness variation
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 10.0
noise.inputs['Detail'].default_value = 3.0

links.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

# Map to 0.4-0.7 roughness range
map_range = nodes.new('ShaderNodeMapRange')
map_range.inputs['From Min'].default_value = 0.0
map_range.inputs['From Max'].default_value = 1.0
map_range.inputs['To Min'].default_value = 0.4
map_range.inputs['To Max'].default_value = 0.7

links.new(noise.outputs['Fac'], map_range.inputs['Value'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.8, 0.5, 0.3, 1.0)
links.new(map_range.outputs['Result'], bsdf.inputs['Roughness'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

## Voronoi Patterns

### Voronoi Texture Node

**Dimensions:**
- **1D:** Linear cells (stripes)
- **2D:** Flat cells (tiles)
- **3D:** Volume cells (bubbles)
- **4D:** Animated cells (use W input)

**Features:**
- **F1:** Distance to closest cell center
- **F2:** Distance to second-closest cell center
- **SMOOTH_F1:** Smooth falloff
- **DISTANCE_TO_EDGE:** Cell boundaries
- **N_SPHERE_RADIUS:** Cell size

**Outputs:**
- **Distance:** Scalar distance value
- **Color:** Random color per cell
- **Position:** Cell center position

```python
code = """
import bpy

mat = bpy.data.materials.new("Voronoi_Demo")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# === CELL PATTERN (F1) ===
voronoi_cells = nodes.new('ShaderNodeTexVoronoi')
voronoi_cells.location = (-600, 400)
voronoi_cells.voronoi_dimensions = '2D'
voronoi_cells.feature = 'F1'  # Cell centers
voronoi_cells.inputs['Scale'].default_value = 5.0

links.new(texcoord.outputs['Generated'], voronoi_cells.inputs['Vector'])

# === CELL EDGES ===
voronoi_edges = nodes.new('ShaderNodeTexVoronoi')
voronoi_edges.location = (-600, 100)
voronoi_edges.voronoi_dimensions = '2D'
voronoi_edges.feature = 'DISTANCE_TO_EDGE'  # Cell boundaries
voronoi_edges.inputs['Scale'].default_value = 5.0

links.new(texcoord.outputs['Generated'], voronoi_edges.inputs['Vector'])

# === CRACKLE PATTERN (F2-F1) ===
voronoi_f1 = nodes.new('ShaderNodeTexVoronoi')
voronoi_f1.location = (-900, -200)
voronoi_f1.feature = 'F1'
voronoi_f1.inputs['Scale'].default_value = 8.0

voronoi_f2 = nodes.new('ShaderNodeTexVoronoi')
voronoi_f2.location = (-900, -400)
voronoi_f2.feature = 'F2'
voronoi_f2.inputs['Scale'].default_value = 8.0

math_subtract = nodes.new('ShaderNodeMath')
math_subtract.operation = 'SUBTRACT'
math_subtract.location = (-600, -300)

links.new(texcoord.outputs['Generated'], voronoi_f1.inputs['Vector'])
links.new(texcoord.outputs['Generated'], voronoi_f2.inputs['Vector'])
links.new(voronoi_f2.outputs['Distance'], math_subtract.inputs[0])
links.new(voronoi_f1.outputs['Distance'], math_subtract.inputs[1])

# Use one (example: cell edges)
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(voronoi_edges.outputs['Distance'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Voronoi Applications

**1. Honeycomb/Tiles:**
```python
code = """
import bpy

mat = bpy.data.materials.new("Honeycomb")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

voronoi = nodes.new('ShaderNodeTexVoronoi')
voronoi.voronoi_dimensions = '2D'
voronoi.feature = 'DISTANCE_TO_EDGE'
voronoi.inputs['Scale'].default_value = 10.0

links.new(texcoord.outputs['Generated'], voronoi.inputs['Vector'])

# Sharpen edges
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.05
ramp.color_ramp.elements[1].position = 0.1
ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
ramp.color_ramp.elements[1].color = (1, 1, 1, 1)

links.new(voronoi.outputs['Distance'], ramp.inputs['Fac'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

**2. Random Color per Cell:**
```python
code = """
import bpy

mat = bpy.data.materials.new("Random_Cells")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

voronoi = nodes.new('ShaderNodeTexVoronoi')
voronoi.voronoi_dimensions = '2D'
voronoi.feature = 'F1'
voronoi.inputs['Scale'].default_value = 5.0

links.new(texcoord.outputs['Generated'], voronoi.inputs['Vector'])

# Use Color output (random per cell)
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(voronoi.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

**3. Scratches (Linear Voronoi):**
```python
code = """
import bpy

mat = bpy.data.materials.new("Scratches")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# 1D Voronoi for linear pattern
voronoi = nodes.new('ShaderNodeTexVoronoi')
voronoi.voronoi_dimensions = '1D'  # Linear cells
voronoi.feature = 'DISTANCE_TO_EDGE'
voronoi.inputs['Scale'].default_value = 20.0

# Mapping to rotate scratches
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Rotation'].default_value = (0, 0, 0.785)  # 45 deg rotation

links.new(texcoord.outputs['Generated'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], voronoi.inputs['Vector'])

# Sharpen scratches
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.48
ramp.color_ramp.elements[1].position = 0.52

links.new(voronoi.outputs['Distance'], ramp.inputs['Fac'])

# Use as roughness mask
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
bsdf.inputs['Metallic'].default_value = 1.0

# Map to roughness variation
map_range = nodes.new('ShaderNodeMapRange')
map_range.inputs['To Min'].default_value = 0.2
map_range.inputs['To Max'].default_value = 0.6

links.new(ramp.outputs['Color'], map_range.inputs['Value'])
links.new(map_range.outputs['Result'], bsdf.inputs['Roughness'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

## Wave and Gradient Patterns

### Wave Texture Node

**Wave Types:**
- **BANDS:** Straight stripes
- **RINGS:** Concentric circles
- **SIN/SAW/TRI:** Waveform shape

**Parameters:**
- **Scale:** Frequency
- **Distortion:** Warping amount
- **Detail:** Fractal noise addition
- **Detail Scale:** Noise frequency

```python
code = """
import bpy

mat = bpy.data.materials.new("Wave_Patterns")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# === BANDS (Stripes) ===
wave_bands = nodes.new('ShaderNodeTexWave')
wave_bands.location = (-600, 300)
wave_bands.wave_type = 'BANDS'
wave_bands.wave_profile = 'SIN'
wave_bands.inputs['Scale'].default_value = 10.0

links.new(texcoord.outputs['Generated'], wave_bands.inputs['Vector'])

# === RINGS (Concentric) ===
wave_rings = nodes.new('ShaderNodeTexWave')
wave_rings.location = (-600, 0)
wave_rings.wave_type = 'RINGS'
wave_rings.wave_profile = 'SIN'
wave_rings.inputs['Scale'].default_value = 8.0

links.new(texcoord.outputs['Generated'], wave_rings.inputs['Vector'])

# === WOOD RINGS (Distorted) ===
wave_wood = nodes.new('ShaderNodeTexWave')
wave_wood.location = (-600, -300)
wave_wood.wave_type = 'RINGS'
wave_wood.wave_profile = 'SAW'
wave_wood.inputs['Scale'].default_value = 15.0
wave_wood.inputs['Distortion'].default_value = 3.0
wave_wood.inputs['Detail'].default_value = 5.0

links.new(texcoord.outputs['Generated'], wave_wood.inputs['Vector'])

# Use wood pattern
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.3, 0.15, 0.05, 1.0)  # Dark wood
ramp.color_ramp.elements[1].color = (0.6, 0.4, 0.2, 1.0)  # Light wood

links.new(wave_wood.outputs['Fac'], ramp.inputs['Fac'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Gradient Texture Node

**Gradient Types:**
- **LINEAR:** Straight gradient
- **QUADRATIC:** Parabolic falloff
- **EASING:** Smooth S-curve
- **DIAGONAL:** 45 deg gradient
- **SPHERICAL:** Radial from center
- **QUADRATIC_SPHERE:** Soft radial
- **RADIAL:** Circular gradient

```python
code = """
import bpy

mat = bpy.data.materials.new("Gradient_Demo")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# === LINEAR GRADIENT ===
gradient_linear = nodes.new('ShaderNodeTexGradient')
gradient_linear.location = (-600, 300)
gradient_linear.gradient_type = 'LINEAR'

links.new(texcoord.outputs['Generated'], gradient_linear.inputs['Vector'])

# === SPHERICAL GRADIENT (Vignette) ===
gradient_sphere = nodes.new('ShaderNodeTexGradient')
gradient_sphere.location = (-600, 0)
gradient_sphere.gradient_type = 'SPHERICAL'

links.new(texcoord.outputs['Generated'], gradient_sphere.inputs['Vector'])

# Invert for vignette effect
invert = nodes.new('ShaderNodeInvert')
links.new(gradient_sphere.outputs['Fac'], invert.inputs['Color'])

# === RADIAL GRADIENT (Wheel) ===
gradient_radial = nodes.new('ShaderNodeTexGradient')
gradient_radial.location = (-600, -300)
gradient_radial.gradient_type = 'RADIAL'

links.new(texcoord.outputs['Generated'], gradient_radial.inputs['Vector'])

# Use vignette
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(invert.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

## Material Recipes

### Wood Grain

```python
code = """
import bpy

mat = bpy.data.materials.new("Procedural_Wood")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# Mapping for wood direction
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Rotation'].default_value = (1.5708, 0, 0)  # 90 deg X rotation
mapping.inputs['Scale'].default_value = (1, 1, 3)  # Stretch along grain

links.new(texcoord.outputs['Generated'], mapping.inputs['Vector'])

# Wave texture for rings
wave = nodes.new('ShaderNodeTexWave')
wave.wave_type = 'RINGS'
wave.wave_profile = 'SAW'
wave.inputs['Scale'].default_value = 20.0
wave.inputs['Distortion'].default_value = 2.0
wave.inputs['Detail'].default_value = 3.0

links.new(mapping.outputs['Vector'], wave.inputs['Vector'])

# Color ramp for wood colors
ramp = nodes.new('ShaderNodeValToRGB')
# Add third element
ramp.color_ramp.elements.new(0.5)

ramp.color_ramp.elements[0].position = 0.3
ramp.color_ramp.elements[0].color = (0.25, 0.12, 0.05, 1.0)  # Dark

ramp.color_ramp.elements[1].position = 0.5
ramp.color_ramp.elements[1].color = (0.5, 0.3, 0.15, 1.0)  # Medium

ramp.color_ramp.elements[2].position = 0.7
ramp.color_ramp.elements[2].color = (0.6, 0.4, 0.2, 1.0)  # Light

links.new(wave.outputs['Fac'], ramp.inputs['Fac'])

# Add noise for variation
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 50.0
noise.inputs['Detail'].default_value = 5.0

links.new(mapping.outputs['Vector'], noise.inputs['Vector'])

# Mix colors with noise
mix_color = nodes.new('ShaderNodeMix')
mix_color.data_type = 'RGBA'
mix_color.blend_type = 'MULTIPLY'
mix_color.inputs['Factor'].default_value = 0.2

links.new(ramp.outputs['Color'], mix_color.inputs['A'])
links.new(noise.outputs['Fac'], mix_color.inputs['B'])

# Roughness variation
map_roughness = nodes.new('ShaderNodeMapRange')
map_roughness.inputs['To Min'].default_value = 0.5
map_roughness.inputs['To Max'].default_value = 0.7

links.new(noise.outputs['Fac'], map_roughness.inputs['Value'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(mix_color.outputs['Result'], bsdf.inputs['Base Color'])
links.new(map_roughness.outputs['Result'], bsdf.inputs['Roughness'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Marble

```python
code = """
import bpy

mat = bpy.data.materials.new("Procedural_Marble")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# Base noise for veins
noise1 = nodes.new('ShaderNodeTexNoise')
noise1.inputs['Scale'].default_value = 3.0
noise1.inputs['Detail'].default_value = 10.0
noise1.inputs['Distortion'].default_value = 5.0

links.new(texcoord.outputs['Generated'], noise1.inputs['Vector'])

# Second noise layer
noise2 = nodes.new('ShaderNodeTexNoise')
noise2.inputs['Scale'].default_value = 5.0
noise2.inputs['Detail'].default_value = 5.0

links.new(texcoord.outputs['Generated'], noise2.inputs['Vector'])

# Combine noises
math_add = nodes.new('ShaderNodeMath')
math_add.operation = 'ADD'
links.new(noise1.outputs['Fac'], math_add.inputs[0])
links.new(noise2.outputs['Fac'], math_add.inputs[1])

# Color ramp for marble veins
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.4
ramp.color_ramp.elements[0].color = (0.9, 0.9, 0.9, 1.0)  # White base
ramp.color_ramp.elements[1].position = 0.6
ramp.color_ramp.elements[1].color = (0.6, 0.6, 0.6, 1.0)  # Grey veins

links.new(math_add.outputs['Value'], ramp.inputs['Fac'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Roughness'].default_value = 0.3  # Polished
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

# Subsurface scattering for realism
bsdf.inputs['Subsurface Weight'].default_value = 0.05
bsdf.inputs['Subsurface Radius'].default_value = (1.0, 1.0, 1.0)

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Stone/Rock

```python
code = """
import bpy

mat = bpy.data.materials.new("Procedural_Stone")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# Base noise
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 5.0
noise.inputs['Detail'].default_value = 15.0
noise.inputs['Roughness'].default_value = 0.7

links.new(texcoord.outputs['Object'], noise.inputs['Vector'])

# Voronoi for rock chunks
voronoi = nodes.new('ShaderNodeTexVoronoi')
voronoi.voronoi_dimensions = '3D'
voronoi.feature = 'F1'
voronoi.inputs['Scale'].default_value = 3.0

links.new(texcoord.outputs['Object'], voronoi.inputs['Vector'])

# Combine patterns
mix_fac = nodes.new('ShaderNodeMix')
mix_fac.data_type = 'FLOAT'
mix_fac.inputs['Factor'].default_value = 0.5

links.new(noise.outputs['Fac'], mix_fac.inputs['A'])
links.new(voronoi.outputs['Distance'], mix_fac.inputs['B'])

# Color variation
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.3, 0.3, 0.3, 1.0)  # Dark grey
ramp.color_ramp.elements[1].color = (0.6, 0.6, 0.6, 1.0)  # Light grey

links.new(mix_fac.outputs['Result'], ramp.inputs['Fac'])

# Bump for surface detail
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.5
links.new(noise.outputs['Fac'], bump.inputs['Height'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Roughness'].default_value = 0.85
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Metal (Brushed)

```python
code = """
import bpy

mat = bpy.data.materials.new("Procedural_Brushed_Metal")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# Mapping for brush direction
mapping = nodes.new('ShaderNodeMapping')
mapping.inputs['Rotation'].default_value = (0, 0, 0.785)  # 45 deg rotation
mapping.inputs['Scale'].default_value = (50, 1, 1)  # Stretch for brush lines

links.new(texcoord.outputs['Generated'], mapping.inputs['Vector'])

# Noise for brush scratches
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 100.0
noise.inputs['Detail'].default_value = 15.0

links.new(mapping.outputs['Vector'], noise.inputs['Vector'])

# Map to roughness range
map_roughness = nodes.new('ShaderNodeMapRange')
map_roughness.inputs['To Min'].default_value = 0.3
map_roughness.inputs['To Max'].default_value = 0.5

links.new(noise.outputs['Fac'], map_roughness.inputs['Value'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
bsdf.inputs['Metallic'].default_value = 1.0
links.new(map_roughness.outputs['Result'], bsdf.inputs['Roughness'])

# Anisotropic for directional reflection (optional)
# NOTE: Requires Anisotropic BSDF, not Principled
# For Principled, use roughness variation only

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Rust/Corrosion

```python
code = """
import bpy

mat = bpy.data.materials.new("Procedural_Rust")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

# Rust pattern (Voronoi)
voronoi = nodes.new('ShaderNodeTexVoronoi')
voronoi.voronoi_dimensions = '3D'
voronoi.feature = 'F1'
voronoi.inputs['Scale'].default_value = 5.0
voronoi.inputs['Randomness'].default_value = 1.0

links.new(texcoord.outputs['Object'], voronoi.inputs['Vector'])

# Noise for variation
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 10.0
noise.inputs['Detail'].default_value = 8.0

links.new(texcoord.outputs['Object'], noise.inputs['Vector'])

# Combine
mix = nodes.new('ShaderNodeMix')
mix.data_type = 'FLOAT'
mix.inputs['Factor'].default_value = 0.5

links.new(voronoi.outputs['Distance'], mix.inputs['A'])
links.new(noise.outputs['Fac'], mix.inputs['B'])

# Color ramp for rust colors
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements.new(0.5)

ramp.color_ramp.elements[0].position = 0.3
ramp.color_ramp.elements[0].color = (0.6, 0.3, 0.1, 1.0)  # Orange rust

ramp.color_ramp.elements[1].position = 0.6
ramp.color_ramp.elements[1].color = (0.4, 0.2, 0.05, 1.0)  # Brown rust

ramp.color_ramp.elements[2].position = 0.8
ramp.color_ramp.elements[2].color = (0.15, 0.08, 0.03, 1.0)  # Dark rust

links.new(mix.outputs['Result'], ramp.inputs['Fac'])

# Bump for surface roughness
bump = nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.3
links.new(noise.outputs['Fac'], bump.inputs['Height'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Metallic'].default_value = 0.2  # Partially metallic
bsdf.inputs['Roughness'].default_value = 0.9  # Very rough
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

## Math Node Techniques

### Contrast Adjustment

```python
code = """
import bpy

# Increase contrast of noise pattern
mat = bpy.data.materials.new("Contrast_Boost")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 5.0

links.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

# Method 1: Power function (gamma)
math_power = nodes.new('ShaderNodeMath')
math_power.operation = 'POWER'
math_power.inputs[1].default_value = 2.0  # >1 = darken, <1 = brighten

links.new(noise.outputs['Fac'], math_power.inputs[0])

# Method 2: Map Range (precise control)
map_range = nodes.new('ShaderNodeMapRange')
map_range.inputs['From Min'].default_value = 0.3
map_range.inputs['From Max'].default_value = 0.7
map_range.inputs['To Min'].default_value = 0.0
map_range.inputs['To Max'].default_value = 1.0

links.new(noise.outputs['Fac'], map_range.inputs['Value'])

# Use power method
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(math_power.outputs['Value'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Threshold (Binary Mask)

```python
code = """
import bpy

mat = bpy.data.materials.new("Threshold_Mask")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 8.0

links.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

# Threshold at 0.5
math_greater = nodes.new('ShaderNodeMath')
math_greater.operation = 'GREATER_THAN'
math_greater.inputs[1].default_value = 0.5

links.new(noise.outputs['Fac'], math_greater.inputs[0])

# Result: 0 or 1 (binary)
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(math_greater.outputs['Value'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Quantize/Posterize

```python
code = """
import bpy

mat = bpy.data.materials.new("Posterized")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 5.0

links.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

# Quantize to N steps
steps = 5

# Multiply by steps
math_mul = nodes.new('ShaderNodeMath')
math_mul.operation = 'MULTIPLY'
math_mul.inputs[1].default_value = steps

# Floor to integer
math_floor = nodes.new('ShaderNodeMath')
math_floor.operation = 'FLOOR'

# Divide back
math_div = nodes.new('ShaderNodeMath')
math_div.operation = 'DIVIDE'
math_div.inputs[1].default_value = steps

links.new(noise.outputs['Fac'], math_mul.inputs[0])
links.new(math_mul.outputs['Value'], math_floor.inputs[0])
links.new(math_floor.outputs['Value'], math_div.inputs[0])

# Result: Posterized to 5 steps
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(math_div.outputs['Value'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

## Color Ramp Mastery

### Advanced Color Ramp Techniques

**Interpolation Modes:**
- **LINEAR:** Smooth gradient
- **EASE:** S-curve falloff
- **CONSTANT:** Hard steps
- **B_SPLINE:** Very smooth (overshoot)
- **CARDINAL:** Smooth without overshoot

```python
code = """
import bpy

mat = bpy.data.materials.new("ColorRamp_Advanced")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 5.0

links.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

# Complex color ramp
ramp = nodes.new('ShaderNodeValToRGB')

# Add more elements
ramp.color_ramp.elements.new(0.33)
ramp.color_ramp.elements.new(0.66)

# Configure elements
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0.1, 0.0, 0.2, 1.0)  # Dark purple

ramp.color_ramp.elements[1].position = 0.33
ramp.color_ramp.elements[1].color = (0.5, 0.1, 0.3, 1.0)  # Purple

ramp.color_ramp.elements[2].position = 0.66
ramp.color_ramp.elements[2].color = (1.0, 0.5, 0.2, 1.0)  # Orange

ramp.color_ramp.elements[3].position = 1.0
ramp.color_ramp.elements[3].color = (1.0, 1.0, 0.5, 1.0)  # Yellow

# Interpolation
ramp.color_ramp.interpolation = 'LINEAR'  # Change to 'EASE', 'CONSTANT', etc.

links.new(noise.outputs['Fac'], ramp.inputs['Fac'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
"""
```

---

### Color Ramp as Mask

```python
code = """
import bpy

# Use color ramp to create hard mask
mat = bpy.data.materials.new("Ramp_Mask")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')

noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 8.0

links.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

# Sharp cutoff at 0.5
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.49
ramp.color_ramp.elements[0].color = (0, 0, 0, 1)  # Black

ramp.color_ramp.elements[1].position = 0.51
ramp.color_ramp.elements[1].color = (1, 1, 1, 1)  # White

links.new(noise.outputs['Fac'], ramp.inputs['Fac'])

# Use as mix factor
bsdf1 = nodes.new('ShaderNodeBsdfPrincipled')
bsdf1.inputs['Base Color'].default_value = (1, 0, 0, 1)  # Red

bsdf2 = nodes.new('ShaderNodeBsdfPrincipled')
bsdf2.inputs['Base Color'].default_value = (0, 0, 1, 1)  # Blue

mix_shader = nodes.new('ShaderNodeMixShader')
links.new(ramp.outputs['Alpha'], mix_shader.inputs['Fac'])
links.new(bsdf1.outputs['BSDF'], mix_shader.inputs[1])
links.new(bsdf2.outputs['BSDF'], mix_shader.inputs[2])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])
"""
```

---

## UV-less Workflows

### Triplanar Mapping

**Use Case:** Texturing without UV unwrapping (project from 3 axes)

```python
code = """
import bpy

mat = bpy.data.materials.new("Triplanar_Mapping")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')
geometry = nodes.new('ShaderNodeNewGeometry')

# Separate normal to get face orientation
sep_normal = nodes.new('ShaderNodeSeparateXYZ')
links.new(geometry.outputs['Normal'], sep_normal.inputs['Vector'])

# X projection
noise_x = nodes.new('ShaderNodeTexNoise')
noise_x.inputs['Scale'].default_value = 5.0

sep_coord_x = nodes.new('ShaderNodeSeparateXYZ')
links.new(texcoord.outputs['Object'], sep_coord_x.inputs['Vector'])

combine_x = nodes.new('ShaderNodeCombineXYZ')
links.new(sep_coord_x.outputs['Y'], combine_x.inputs['X'])
links.new(sep_coord_x.outputs['Z'], combine_x.inputs['Y'])

links.new(combine_x.outputs['Vector'], noise_x.inputs['Vector'])

# Y projection
noise_y = nodes.new('ShaderNodeTexNoise')
noise_y.inputs['Scale'].default_value = 5.0

combine_y = nodes.new('ShaderNodeCombineXYZ')
links.new(sep_coord_x.outputs['X'], combine_y.inputs['X'])
links.new(sep_coord_x.outputs['Z'], combine_y.inputs['Y'])

links.new(combine_y.outputs['Vector'], noise_y.inputs['Vector'])

# Z projection
noise_z = nodes.new('ShaderNodeTexNoise')
noise_z.inputs['Scale'].default_value = 5.0

combine_z = nodes.new('ShaderNodeCombineXYZ')
links.new(sep_coord_x.outputs['X'], combine_z.inputs['X'])
links.new(sep_coord_x.outputs['Y'], combine_z.inputs['Y'])

links.new(combine_z.outputs['Vector'], noise_z.inputs['Vector'])

# Mix based on normal direction
# X-facing: abs(normal.x)
math_abs_x = nodes.new('ShaderNodeMath')
math_abs_x.operation = 'ABSOLUTE'
links.new(sep_normal.outputs['X'], math_abs_x.inputs[0])

# Y-facing: abs(normal.y)
math_abs_y = nodes.new('ShaderNodeMath')
math_abs_y.operation = 'ABSOLUTE'
links.new(sep_normal.outputs['Y'], math_abs_y.inputs[0])

# Z-facing: abs(normal.z)
math_abs_z = nodes.new('ShaderNodeMath')
math_abs_z.operation = 'ABSOLUTE'
links.new(sep_normal.outputs['Z'], math_abs_z.inputs[0])

# Mix X and Y
mix_xy = nodes.new('ShaderNodeMix')
mix_xy.data_type = 'FLOAT'
links.new(math_abs_y.outputs['Value'], mix_xy.inputs['Factor'])
links.new(noise_x.outputs['Fac'], mix_xy.inputs['A'])
links.new(noise_y.outputs['Fac'], mix_xy.inputs['B'])

# Mix result with Z
mix_final = nodes.new('ShaderNodeMix')
mix_final.data_type = 'FLOAT'
links.new(math_abs_z.outputs['Value'], mix_final.inputs['Factor'])
links.new(mix_xy.outputs['Result'], mix_final.inputs['A'])
links.new(noise_z.outputs['Fac'], mix_final.inputs['B'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
links.new(mix_final.outputs['Result'], bsdf.inputs['Base Color'])

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

print("Triplanar mapping (no UVs required)")
"""
```

**Note:** Triplanar is complex but essential for terrain/large objects without UVs.

---

## Performance Optimization

### Texture Baking (Procedural to Image)

**Convert procedural to image texture for performance:**

```python
code = """
import bpy

# Setup for baking procedural material to image texture
obj = bpy.context.active_object

if obj and obj.type == 'MESH':
    # Get material
    mat = obj.data.materials[0]

    if mat and mat.use_nodes:
        nodes = mat.node_tree.nodes

        # Create bake image
        img = bpy.data.images.new(
            name="Baked_Procedural",
            width=2048,
            height=2048,
            alpha=False
        )

        # Add image texture node for baking
        bake_tex = nodes.new('ShaderNodeTexImage')
        bake_tex.image = img
        nodes.active = bake_tex  # CRITICAL: Active node receives bake

        # Configure bake settings
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = 32
        bpy.context.scene.cycles.bake_type = 'DIFFUSE'
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_pass_color = True

        print("Bake setup complete. Run bpy.ops.object.bake() in interactive Blender")
        print(f"After baking, image will be in {img.name}")
"""
```

---

### Node Complexity Reduction

**Simplify shader for real-time:**

```python
code = """
import bpy

# Analyze and simplify material
mat = bpy.data.materials.get("Complex_Material")

if mat and mat.use_nodes:
    nodes = mat.node_tree.nodes

    # Count expensive nodes
    texture_nodes = [n for n in nodes if 'TEX' in n.type]
    mix_shaders = [n for n in nodes if n.type == 'MIX_SHADER']

    print(f"Texture nodes: {len(texture_nodes)} (medium cost)")
    print(f"Mix shaders: {len(mix_shaders)} (high cost)")

    # Suggestion: Replace multiple textures with single baked texture
    # Suggestion: Replace Mix Shaders with Mix Color before BSDF
    if len(texture_nodes) > 5:
        print("OPTIMIZATION: Consider baking textures to reduce node count")

    if len(mix_shaders) > 2:
        print("OPTIMIZATION: Replace Mix Shaders with color mixing")
"""
```

---

## Cross-References

**Related Skills:**
- `blender-materials-shaders` - Main materials skill (SKILL.md)
- `blender-geometry-nodes` - Procedural modeling (similar node concepts)
- `blender-rendering` - EEVEE_NEXT/Cycles optimization

**ADVANCED_SHADER_NODES.md:**
- Complex node trees (layering, SSS, anisotropy)
- Node groups (reusable procedural patterns)
- EEVEE_NEXT vs Cycles differences

**PBR_WORKFLOWS.md:**
- Texture mapping (UV coordinates)
- Cross-engine export (Unreal, Unity, glTF)
- Material library organization

**blender-ai-compatibility Repository:**
- `api_changes/4.5_lighting_changes.md` - EEVEE_NEXT updates
- `examples/production_workflows/procedural_materials.py` - Complete examples

---

**Last Updated:** 2025-10-25
**Tested With:** Blender 4.5.0 via the official Blender MCP
**Line Count:** ~970 lines
