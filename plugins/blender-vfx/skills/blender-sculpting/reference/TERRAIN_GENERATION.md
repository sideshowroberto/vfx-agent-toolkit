# Blender Sculpting - Terrain Generation

**Part of:** blender-sculpting skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

Large-scale terrain creation, heightmap workflows, erosion simulation, and vegetation placement. Use this reference when working on:
- Large terrain systems (>1km^2)
- Heightmap import/export workflows
- Realistic erosion patterns
- Terrain texture blending
- Vegetation scattering on terrain

---

## Large-Scale Terrain Creation

### **Multi-Tile Terrain System**

**Goal:** Create modular terrain tiles that can be assembled into large landscapes

**Step 1: Create Tile Template**
```python
import requests

code = """
import bpy
import numpy as np

def create_terrain_tile(tile_x, tile_y, tile_size=100, subdivisions=100):
    '''Create a single terrain tile at grid position'''
    vertices = []
    faces = []

    # Generate vertex grid
    for y in range(subdivisions + 1):
        for x in range(subdivisions + 1):
            # World position
            world_x = (tile_x * tile_size) + (x / subdivisions) * tile_size
            world_y = (tile_y * tile_size) + (y / subdivisions) * tile_size

            vertices.append((world_x, world_y, 0.0))

    # Generate faces
    for y in range(subdivisions):
        for x in range(subdivisions):
            i = y * (subdivisions + 1) + x
            faces.append([i, i + 1, i + subdivisions + 2, i + subdivisions + 1])

    # Create mesh
    mesh = bpy.data.meshes.new(f'TerrainTile_{tile_x}_{tile_y}')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Create object
    obj = bpy.data.objects.new(f'Terrain_{tile_x}_{tile_y}', mesh)
    bpy.context.collection.objects.link(obj)

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj

# Create 3x3 grid of terrain tiles
tiles = []
for ty in range(-1, 2):
    for tx in range(-1, 2):
        tile = create_terrain_tile(tx, ty)
        tiles.append(tile)

print(f'Created {len(tiles)} terrain tiles (3x3 grid)')
print(f'Total area: 300m x 300m')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
result = response.json()
print(result.get('output'))
```

**Step 2: Apply Continuous Height Function**
```python
code = """
import bpy
import numpy as np

# Define large-scale height function
def terrain_height(x, y):
    '''Calculate height at any world position'''
    height = 0

    # Large mountains
    mountain_x, mountain_y = 50, 50
    dist_mountain = np.sqrt((x - mountain_x)**2 + (y - mountain_y)**2)
    if dist_mountain < 80:
        height += 50 * (1 - dist_mountain / 80) ** 2

    # Rolling hills
    height += 10 * np.sin(x * 0.05) * np.cos(y * 0.05)

    # Fine detail
    height += 2 * np.sin(x * 0.2) * np.sin(y * 0.2)

    return height

# Apply height to all tiles
for obj in [o for o in bpy.data.objects if o.name.startswith('Terrain_')]:
    mesh = obj.data
    for v in mesh.vertices:
        # Get world position
        world_pos = obj.matrix_world @ v.co
        x, y = world_pos.x, world_pos.y

        # Set height
        v.co.z = terrain_height(x, y)

    mesh.update()

print('Continuous height function applied to all tiles')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Heightmap Workflows

### **Import Heightmap from Image**

**Supported Formats:** PNG, EXR, TIFF (16-bit recommended)

**Step 1: Load Heightmap Image**
```python
code = """
import bpy

# Load heightmap image
heightmap_path = r'C:\\Path\\To\\heightmap.png'
heightmap = bpy.data.images.load(heightmap_path)

print(f'Heightmap loaded: {heightmap.size[0]}x{heightmap.size[1]}')
print(f'Channels: {heightmap.channels}')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Step 2: Create Terrain from Heightmap**
```python
code = """
import bpy
import numpy as np

heightmap = bpy.data.images.get('heightmap.png')
if heightmap:
    width, height = heightmap.size
    pixels = np.array(heightmap.pixels[:]).reshape((height, width, heightmap.channels))

    # Create terrain mesh matching heightmap resolution
    vertices = []
    faces = []

    terrain_size = 1000  # meters
    max_height = 100     # meters

    # Generate vertices from heightmap
    for y in range(height):
        for x in range(width):
            # World position
            world_x = (x / width - 0.5) * terrain_size
            world_y = (y / height - 0.5) * terrain_size

            # Height from image (use red channel or average)
            if heightmap.channels >= 3:
                height_value = (pixels[y, x, 0] + pixels[y, x, 1] + pixels[y, x, 2]) / 3
            else:
                height_value = pixels[y, x, 0]

            world_z = height_value * max_height

            vertices.append((world_x, world_y, world_z))

    # Generate faces
    for y in range(height - 1):
        for x in range(width - 1):
            i = y * width + x
            faces.append([i, i + 1, i + width + 1, i + width])

    # Create mesh
    mesh = bpy.data.meshes.new('HeightmapTerrain')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new('HeightmapTerrain', mesh)
    bpy.context.collection.objects.link(obj)

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    print(f'Terrain created from heightmap: {len(vertices)} vertices')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Step 3: Export Terrain as Heightmap**
```python
code = """
import bpy
import numpy as np

terrain = bpy.data.objects.get('Terrain')
mesh = terrain.data

# Determine heightmap resolution
resolution = 1024  # Output image size

# Calculate bounds
vertices = [terrain.matrix_world @ v.co for v in mesh.vertices]
min_x = min(v.x for v in vertices)
max_x = max(v.x for v in vertices)
min_y = min(v.y for v in vertices)
max_y = max(v.y for v in vertices)
min_z = min(v.z for v in vertices)
max_z = max(v.z for v in vertices)

# Create image
image = bpy.data.images.new('TerrainHeightmap', resolution, resolution, float_buffer=True)
pixels = [0.0] * (resolution * resolution * 4)

# Sample terrain height at each pixel
for py in range(resolution):
    for px in range(resolution):
        # World position
        world_x = min_x + (px / resolution) * (max_x - min_x)
        world_y = min_y + (py / resolution) * (max_y - min_y)

        # Find closest vertex (simple approach - could use interpolation)
        closest_z = 0
        min_dist = float('inf')
        for v in vertices:
            dist = (v.x - world_x)**2 + (v.y - world_y)**2
            if dist < min_dist:
                min_dist = dist
                closest_z = v.z

        # Normalize height to 0-1 range
        normalized_height = (closest_z - min_z) / (max_z - min_z) if max_z > min_z else 0

        # Set pixel
        idx = (py * resolution + px) * 4
        pixels[idx] = normalized_height      # R
        pixels[idx + 1] = normalized_height  # G
        pixels[idx + 2] = normalized_height  # B
        pixels[idx + 3] = 1.0                # A

image.pixels = pixels

# Save to file
output_path = r'C:\\Output\\terrain_heightmap.exr'
image.filepath_raw = output_path
image.file_format = 'OPEN_EXR'
image.save()

print(f'Heightmap exported: {resolution}x{resolution}')
print(f'Height range: {min_z:.2f} to {max_z:.2f}')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Erosion Simulation

### **Hydraulic Erosion (Simplified)**

**Concept:** Simulate water flow to create realistic erosion patterns

```python
code = """
import bpy
import numpy as np

terrain = bpy.data.objects.get('Terrain')
mesh = terrain.data

# Erosion parameters
iterations = 10
erosion_strength = 0.5
deposition_strength = 0.3

for iteration in range(iterations):
    # For each vertex, simulate water flow
    for v in mesh.vertices:
        # Find lowest neighbor (water flows downhill)
        lowest_neighbor = None
        lowest_height = v.co.z

        for edge in mesh.edges:
            if v.index in edge.vertices:
                other_idx = edge.vertices[0] if edge.vertices[1] == v.index else edge.vertices[1]
                other_v = mesh.vertices[other_idx]

                if other_v.co.z < lowest_height:
                    lowest_height = other_v.co.z
                    lowest_neighbor = other_v

        if lowest_neighbor:
            # Calculate height difference
            height_diff = v.co.z - lowest_neighbor.co.z

            # Erode current vertex
            erosion = min(height_diff * erosion_strength, height_diff * 0.5)
            v.co.z -= erosion

            # Deposit on lower vertex
            lowest_neighbor.co.z += erosion * deposition_strength

    mesh.update()
    print(f'Erosion iteration {iteration + 1}/{iterations} complete')

print('Hydraulic erosion simulation complete')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **Thermal Erosion (Slope-Based)**

**Concept:** Erode steep slopes to create realistic talus and scree

```python
code = """
import bpy
import numpy as np

terrain = bpy.data.objects.get('Terrain')
mesh = terrain.data

# Thermal erosion parameters
max_slope_angle = 45  # degrees
talus_angle = np.radians(max_slope_angle)
iterations = 5

for iteration in range(iterations):
    for v in mesh.vertices:
        # Check slope to neighbors
        for edge in mesh.edges:
            if v.index in edge.vertices:
                other_idx = edge.vertices[0] if edge.vertices[1] == v.index else edge.vertices[1]
                other_v = mesh.vertices[other_idx]

                # Calculate slope
                height_diff = v.co.z - other_v.co.z
                horizontal_dist = np.sqrt(
                    (v.co.x - other_v.co.x)**2 +
                    (v.co.y - other_v.co.y)**2
                )

                if horizontal_dist > 0:
                    slope = np.arctan(height_diff / horizontal_dist)

                    # If slope exceeds threshold, move material
                    if abs(slope) > talus_angle:
                        # Transfer height
                        transfer = height_diff * 0.5
                        v.co.z -= transfer
                        other_v.co.z += transfer

    mesh.update()
    print(f'Thermal erosion iteration {iteration + 1}/{iterations} complete')

print('Thermal erosion complete')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Vegetation Placement

### **Slope-Based Vegetation Zones**

**Create vertex groups for vegetation scattering:**

```python
code = """
import bpy
import numpy as np

terrain = bpy.data.objects.get('Terrain')
mesh = terrain.data

# Create vegetation zone vertex groups
vg_trees = terrain.vertex_groups.new(name='Trees')
vg_grass = terrain.vertex_groups.new(name='Grass')
vg_rocks = terrain.vertex_groups.new(name='Rocks')

# Classify vertices by slope and height
for v in mesh.vertices:
    # Calculate slope (using vertex normal)
    slope = np.arccos(v.normal.z)  # Angle from vertical
    height = v.co.z

    # Trees: gentle slopes, mid height
    if slope < np.radians(25) and 10 < height < 40:
        vg_trees.add([v.index], 1.0, 'ADD')

    # Grass: gentle to moderate slopes, lower height
    if slope < np.radians(35) and height < 30:
        vg_grass.add([v.index], 1.0 - (slope / np.radians(35)), 'ADD')

    # Rocks: steep slopes, high areas
    if slope > np.radians(30) or height > 35:
        vg_rocks.add([v.index], slope / np.radians(90), 'ADD')

print('Vegetation zones created:')
for vg in terrain.vertex_groups:
    count = sum(1 for v in mesh.vertices if vg.index in [g.group for g in v.groups])
    print(f'  {vg.name}: {count} vertices')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **Export Vertex Groups for Scattering**

Use geometry nodes or external tools to scatter vegetation based on these groups.

---

## Terrain Texture Blending

### **Height-Based Material Zones**

```python
code = """
import bpy

terrain = bpy.data.objects.get('Terrain')

# Create material with multiple texture zones
mat = bpy.data.materials.new('TerrainMaterial')
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear default nodes
nodes.clear()

# Create nodes
output = nodes.new('ShaderNodeOutputMaterial')
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
coord = nodes.new('ShaderNodeTexCoord')
separate = nodes.new('ShaderNodeSeparateXYZ')
colorramp = nodes.new('ShaderNodeValToRGB')

# Setup color ramp for height-based blending
colorramp.color_ramp.elements[0].color = (0.2, 0.15, 0.1, 1)  # Low (dark soil)
colorramp.color_ramp.elements[1].color = (0.6, 0.6, 0.5, 1)  # High (rock)

# Add middle stops
colorramp.color_ramp.elements.new(0.3)
colorramp.color_ramp.elements[1].color = (0.3, 0.5, 0.2, 1)  # Grass

# Link nodes
links.new(coord.outputs['Object'], separate.inputs['Vector'])
links.new(separate.outputs['Z'], colorramp.inputs['Fac'])
links.new(colorramp.outputs['Color'], bsdf.inputs['Base Color'])
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

# Assign material
if terrain.data.materials:
    terrain.data.materials[0] = mat
else:
    terrain.data.materials.append(mat)

print('Height-based terrain material created')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Performance Optimization

### **Level of Detail (LOD) System**

Create multiple resolution versions of terrain for distant viewing:

```python
code = """
import bpy

def create_lod_terrain(source_obj, lod_level, decimation_ratio):
    '''Create LOD version of terrain'''
    # Duplicate terrain
    lod_mesh = source_obj.data.copy()
    lod_obj = source_obj.copy()
    lod_obj.data = lod_mesh
    lod_obj.name = f'{source_obj.name}_LOD{lod_level}'

    bpy.context.collection.objects.link(lod_obj)

    # Add decimate modifier
    decimate = lod_obj.modifiers.new('Decimate', 'DECIMATE')
    decimate.ratio = decimation_ratio

    return lod_obj

# Create LOD versions
terrain = bpy.data.objects.get('Terrain')
lod1 = create_lod_terrain(terrain, 1, 0.5)   # 50% vertices
lod2 = create_lod_terrain(terrain, 2, 0.25)  # 25% vertices
lod3 = create_lod_terrain(terrain, 3, 0.1)   # 10% vertices

print('LOD terrain versions created')
print('Use distance-based switching in game engine')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

**Return to:** `.claude/skills/blender-sculpting/SKILL.md`
