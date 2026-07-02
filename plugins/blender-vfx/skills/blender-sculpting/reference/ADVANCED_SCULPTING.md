# Blender Sculpting - Advanced Sculpting Techniques

**Part of:** blender-sculpting skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

Advanced sculpting techniques for character work, organic modeling, and ZBrush-style workflows. Use this reference when working on:
- Character sculpting (heads, bodies, creatures)
- Detailed organic forms
- High-resolution detail work
- Symmetry and mirroring setups
- Custom brush creation and configuration

---

## Character Sculpting Workflow

### **Head Sculpting from Base Mesh**

**Goal:** Create detailed character head using Blender's sculpting tools

**Step 1: Create Base Head Mesh**
```python
import requests
import json

code = """
import bpy
import math

# Clear existing head models
for obj in [o for o in bpy.data.objects if o.name.startswith('Head')]:
    bpy.data.objects.remove(obj, do_unlink=True)

# Create UV sphere base (better resolution for sculpting)
vertices = []
faces = []

segments = 16  # Longitudinal segments
rings = 16     # Latitudinal rings

# Generate vertices
for ring in range(rings + 1):
    theta = math.pi * ring / rings
    for seg in range(segments):
        phi = 2 * math.pi * seg / segments
        x = math.sin(theta) * math.cos(phi)
        y = math.sin(theta) * math.sin(phi)
        z = math.cos(theta)
        vertices.append((x, y, z))

# Generate quad faces
for ring in range(rings):
    for seg in range(segments):
        i = ring * segments + seg
        j = i + segments
        next_seg = (seg + 1) % segments
        i_next = ring * segments + next_seg
        j_next = i_next + segments

        if ring < rings:
            faces.append([i, i_next, j_next, j])

# Create mesh
mesh = bpy.data.meshes.new('HeadBaseMesh')
mesh.from_pydata(vertices, [], faces)
mesh.update()

# Create object
obj = bpy.data.objects.new('HeadBase', mesh)
bpy.context.collection.objects.link(obj)

# Enable smooth shading
for poly in mesh.polygons:
    poly.use_smooth = True

print(f'Head base created: {len(vertices)} vertices, {len(faces)} faces')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
result = response.json()
print(result.get('output'))
```

**Step 2: Set Up Symmetry Mirror**
```python
code = """
import bpy

head = bpy.data.objects.get('HeadBase')
if head:
    # Add mirror modifier for symmetrical sculpting
    mirror = head.modifiers.new('Mirror', 'MIRROR')
    mirror.use_axis[0] = True   # X-axis symmetry
    mirror.use_axis[1] = False
    mirror.use_axis[2] = False
    mirror.use_clip = True      # Prevent vertices from crossing mirror plane
    mirror.merge_threshold = 0.001

    print(f'Mirror modifier added to {head.name}')
    print(f'Symmetry axis: X')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Step 3: Add Multires for Detail Levels**
```python
code = """
import bpy

head = bpy.data.objects.get('HeadBase')
if head:
    # Add multires modifier
    multires = head.modifiers.new('Multires', 'MULTIRES')

    # NOTE: Subdivision must be done in Blender UI due to HTTP bridge limitations
    # bpy.ops.object.multires_subdivide() will fail

    print(f'Multires modifier added - subdivide in Blender UI')
    print(f'Recommended: 4-5 subdivision levels for character work')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Step 4: Create Reference Image Planes**
```python
code = """
import bpy

# Add reference image planes for character proportions
# Front view reference
front_plane_data = bpy.data.meshes.new('FrontRefMesh')
front_plane_data.from_pydata(
    [(-2, -5, -2), (-2, -5, 2), (-2, -5, -2), (-2, -5, 2)],
    [],
    [[0, 1, 3, 2]]
)
front_plane = bpy.data.objects.new('FrontReference', front_plane_data)
bpy.context.collection.objects.link(front_plane)

# Side view reference
side_plane_data = bpy.data.meshes.new('SideRefMesh')
side_plane_data.from_pydata(
    [(0, -5, -2), (0, -5, 2), (0, 5, 2), (0, 5, -2)],
    [],
    [[0, 1, 2, 3]]
)
side_plane = bpy.data.objects.new('SideReference', side_plane_data)
bpy.context.collection.objects.link(side_plane)

print('Reference planes created (assign image textures in Blender UI)')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## ZBrush-Style Workflows

### **DynaMesh Alternative (Remeshing)**

ZBrush users are familiar with DynaMesh for dynamic topology. Blender's equivalent is remeshing.

**Voxel Remesher (Similar to DynaMesh):**
```python
code = """
import bpy

obj = bpy.data.objects.get('Sculpture')
if obj:
    # Add remesh modifier (voxel mode like DynaMesh)
    remesh = obj.modifiers.new('Remesh', 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 0.05  # Smaller = higher resolution
    remesh.adaptivity = 0.0   # 0 = uniform, 1 = adaptive

    # Apply remesh
    bpy.context.view_layer.objects.active = obj
    # NOTE: Apply modifier via UI or manual mesh data copy

    print(f'Voxel remesh added - voxel size: {remesh.voxel_size}')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Adaptive Subdivision (for Detail Areas):**
```python
code = """
import bpy

obj = bpy.data.objects.get('Sculpture')
mesh = obj.data

# Manually subdivide high-curvature areas
# Identify vertices with high curvature
import numpy as np

curvature_threshold = 0.5
vertices_to_subdivide = []

for v in mesh.vertices:
    # Calculate approximate curvature from normal differences
    connected_normals = [v.normal]
    for edge in mesh.edges:
        if v.index in edge.vertices:
            other_idx = edge.vertices[0] if edge.vertices[1] == v.index else edge.vertices[1]
            connected_normals.append(mesh.vertices[other_idx].normal)

    # Calculate normal variation
    avg_normal = np.mean([n[:] for n in connected_normals], axis=0)
    variation = np.linalg.norm(np.array(v.normal[:]) - avg_normal)

    if variation > curvature_threshold:
        vertices_to_subdivide.append(v.index)

print(f'High curvature vertices identified: {len(vertices_to_subdivide)}')
print('Subdivide these areas manually in Blender for detail')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Advanced Brush Customization

### **Custom Brush Creation**

**Create Height Stamp Brush:**
```python
code = """
import bpy

# Create custom brush texture via image
width, height = 256, 256
pixels = [0.0] * (width * height * 4)  # RGBA

# Create radial gradient for brush falloff
import math
for y in range(height):
    for x in range(width):
        # Distance from center
        dx = (x - width/2) / (width/2)
        dy = (y - height/2) / (height/2)
        dist = math.sqrt(dx*dx + dy*dy)

        # Radial falloff
        value = max(0, 1.0 - dist)

        idx = (y * width + x) * 4
        pixels[idx] = value      # R
        pixels[idx+1] = value    # G
        pixels[idx+2] = value    # B
        pixels[idx+3] = 1.0      # A

# Create image
image = bpy.data.images.new('BrushTexture', width, height)
image.pixels = pixels

# Create texture from image
tex = bpy.data.textures.new('CustomBrush', 'IMAGE')
tex.image = image

print(f'Custom brush texture created: {width}x{height}')
print('Assign to sculpting brush in Blender UI')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Noise-Based Detail Brush:**
```python
code = """
import bpy
import random

# Create noise texture for detail work
width, height = 512, 512
pixels = [0.0] * (width * height * 4)

# Perlin-style noise generation (simplified)
for y in range(height):
    for x in range(width):
        # Multi-octave noise
        noise = 0
        amplitude = 1.0
        frequency = 1.0

        for octave in range(4):
            sample_x = x * frequency / width
            sample_y = y * frequency / height

            # Simple hash-based noise
            noise_val = random.Random(int(sample_x * 1000 + sample_y)).random()
            noise += noise_val * amplitude

            amplitude *= 0.5
            frequency *= 2.0

        noise = noise / 2.0  # Normalize

        idx = (y * width + x) * 4
        pixels[idx] = noise
        pixels[idx+1] = noise
        pixels[idx+2] = noise
        pixels[idx+3] = 1.0

image = bpy.data.images.new('NoiseBrushTexture', width, height)
image.pixels = pixels

tex = bpy.data.textures.new('NoiseDetailBrush', 'IMAGE')
tex.image = image

print('Noise detail brush texture created')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Symmetry and Mirroring Techniques

### **Multi-Axis Symmetry**

**Radial Symmetry (for Creatures, Flowers):**
```python
code = """
import bpy

obj = bpy.data.objects.get('Creature')
if obj:
    # Use array modifier for radial symmetry
    array = obj.modifiers.new('RadialArray', 'ARRAY')
    array.count = 6  # 6-way symmetry
    array.use_relative_offset = False
    array.use_object_offset = True

    # Create empty for rotation center
    empty = bpy.data.objects.new('RadialCenter', None)
    bpy.context.collection.objects.link(empty)
    empty.location = obj.location
    empty.rotation_euler[2] = 3.14159 * 2 / 6  # 60 degrees

    array.offset_object = empty

    print(f'Radial symmetry setup: {array.count} instances')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Bi-Lateral + Vertical Symmetry:**
```python
code = """
import bpy

obj = bpy.data.objects.get('Sculpture')
if obj:
    # X-axis mirror (left/right)
    mirror_x = obj.modifiers.new('MirrorX', 'MIRROR')
    mirror_x.use_axis = [True, False, False]
    mirror_x.use_clip = True

    # Z-axis mirror (top/bottom)
    mirror_z = obj.modifiers.new('MirrorZ', 'MIRROR')
    mirror_z.use_axis = [False, False, True]
    mirror_z.use_clip = True

    print('Bi-lateral symmetry setup (X + Z axes)')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Detailed Organic Forms

### **Skin/Pore Detail Technique**

**Procedural Pore Generation:**
```python
code = """
import bpy
import random

obj = bpy.data.objects.get('Skin')
mesh = obj.data

# Add subtle displacement for pore detail
for v in mesh.vertices:
    # Random pore displacement
    if random.random() > 0.95:  # 5% of vertices
        # Inset slightly for pore
        v.co += v.normal * -0.002

    # Add overall skin texture noise
    noise = random.gauss(0, 0.0005)
    v.co += v.normal * noise

mesh.update()
print('Skin pore detail applied')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Workflow Tips

### **Layer-Based Sculpting**

1. **Base Form Layer** - Primary shapes, proportions
2. **Secondary Forms Layer** - Muscles, major features
3. **Tertiary Details Layer** - Wrinkles, pores, fine detail

**Implementation:**
```python
# Use shape keys to store sculpting layers
code = """
import bpy

obj = bpy.data.objects.get('Character')
if obj:
    # Create shape key layers
    basis = obj.shape_key_add(name='Basis')
    layer1 = obj.shape_key_add(name='BaseForm')
    layer2 = obj.shape_key_add(name='SecondaryForms')
    layer3 = obj.shape_key_add(name='Details')

    # All layers at full strength
    layer1.value = 1.0
    layer2.value = 1.0
    layer3.value = 1.0

    print('Sculpting layers created (use shape keys to isolate)')
"""
```

---

**Return to:** `.claude/skills/blender-sculpting/SKILL.md`
