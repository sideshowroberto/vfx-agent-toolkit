# Blender Geometry Nodes - Procedural Modeling

**Part of:** blender-geometry-nodes skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers procedural modeling workflows for architecture, terrain generation, vegetation systems, and parametric design patterns using Geometry Nodes.

---

## Procedural Architecture

### Building Generator

Create parametric building systems with controllable dimensions.

```python
import requests
import json
# Execute via the Blender MCP tool: execute_blender_code
code = """
import bpy

# Create building generator
mesh = bpy.data.meshes.new("BuildingBase")
obj = bpy.data.objects.new("Building", mesh)
bpy.context.collection.objects.link(obj)

modifier = obj.modifiers.new("BuildingGen", type='NODES')
node_tree = bpy.data.node_groups.new("BuildingGenerator", type='GeometryNodeTree')
modifier.node_group = node_tree

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Building parameters
group_input = nodes.new('NodeGroupInput')
node_tree.interface.new_socket("Width", in_out='INPUT', socket_type='NodeSocketFloat')
node_tree.interface.new_socket("Length", in_out='INPUT', socket_type='NodeSocketFloat')
node_tree.interface.new_socket("Height", in_out='INPUT', socket_type='NodeSocketFloat')
node_tree.interface.new_socket("Floors", in_out='INPUT', socket_type='NodeSocketInt')

# Floor generation
cube = nodes.new('GeometryNodeMeshCube')
duplicate = nodes.new('GeometryNodeDuplicateElements')
transform_floors = nodes.new('GeometryNodeTransform')

# Window array
window_cube = nodes.new('GeometryNodeMeshCube')
array_x = nodes.new('GeometryNodeDuplicateElements')
array_z = nodes.new('GeometryNodeDuplicateElements')
transform_windows = nodes.new('GeometryNodeTransform')

# Boolean subtract windows
boolean = nodes.new('GeometryNodeMeshBoolean')
boolean.operation = 'DIFFERENCE'

# Layout
group_input.location = (-800, 0)
cube.location = (-600, 0)
duplicate.location = (-400, 0)
transform_floors.location = (-200, 0)
window_cube.location = (-600, -300)
array_x.location = (-400, -300)
array_z.location = (-200, -300)
boolean.location = (0, 0)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (200, 0)

# Connect building structure
links.new(group_input.outputs["Width"], cube.inputs["Size X"])
links.new(group_input.outputs["Length"], cube.inputs["Size Y"])
links.new(cube.outputs[0], duplicate.inputs[0])
links.new(group_input.outputs["Floors"], duplicate.inputs["Amount"])
links.new(duplicate.outputs[0], transform_floors.inputs[0])

# Window pattern
window_cube.inputs["Size"].default_value = (0.8, 0.1, 1.5)
array_x.inputs["Amount"].default_value = 5
array_z.inputs["Amount"].default_value = 10

links.new(window_cube.outputs[0], array_x.inputs[0])
links.new(array_x.outputs[0], array_z.inputs[0])
links.new(array_z.outputs[0], transform_windows.inputs[0])

# Subtract windows from building
links.new(transform_floors.outputs[0], boolean.inputs[0])
links.new(transform_windows.outputs[0], boolean.inputs[1])
links.new(boolean.outputs[0], group_output.inputs[0])

print("Procedural building generator created")
"""

response = requests.post(url, json={"code": code})
print(response.json()["output"])
```

### Parametric Facade

Create parametric building facades with modular panels.

```python
code = """
import bpy

# Facade panel system
node_tree = bpy.data.node_groups.new("FacadeSystem", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Input parameters
group_input = nodes.new('NodeGroupInput')
node_tree.interface.new_socket("Panel Width", in_out='INPUT', socket_type='NodeSocketFloat')
node_tree.interface.new_socket("Panel Height", in_out='INPUT', socket_type='NodeSocketFloat')
node_tree.interface.new_socket("Columns", in_out='INPUT', socket_type='NodeSocketInt')
node_tree.interface.new_socket("Rows", in_out='INPUT', socket_type='NodeSocketInt')

# Create base panel
panel = nodes.new('GeometryNodeMeshCube')
inset_faces = nodes.new('GeometryNodeExtrudeMesh')
scale_elements = nodes.new('GeometryNodeScaleElements')

# Array panels
grid = nodes.new('GeometryNodeMeshGrid')
instance_on_points = nodes.new('GeometryNodeInstanceOnPoints')

# Panel detail
inset_faces.inputs["Offset"].default_value = -0.05
scale_elements.inputs["Scale"].default_value = 0.9

# Connect panel creation
links.new(group_input.outputs["Panel Width"], panel.inputs["Size X"])
links.new(group_input.outputs["Panel Height"], panel.inputs["Size Y"])
links.new(panel.outputs[0], inset_faces.inputs[0])
links.new(inset_faces.outputs[0], scale_elements.inputs[0])

# Grid distribution
links.new(group_input.outputs["Columns"], grid.inputs["Vertices X"])
links.new(group_input.outputs["Rows"], grid.inputs["Vertices Y"])
links.new(grid.outputs[0], instance_on_points.inputs[0])
links.new(scale_elements.outputs[0], instance_on_points.inputs[2])

group_output = nodes.new('NodeGroupOutput')
links.new(instance_on_points.outputs[0], group_output.inputs[0])

print("Parametric facade system created")
"""

response = requests.post(url, json={"code": code})
```

---

## Terrain Generation

### Heightmap-Based Terrain

Create terrain from noise-based heightmaps.

```python
code = """
import bpy

# Create terrain system
mesh = bpy.data.meshes.new("TerrainMesh")
obj = bpy.data.objects.new("Terrain", mesh)
bpy.context.collection.objects.link(obj)

modifier = obj.modifiers.new("TerrainGen", type='NODES')
node_tree = bpy.data.node_groups.new("TerrainGenerator", type='GeometryNodeTree')
modifier.node_group = node_tree

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Terrain parameters
group_input = nodes.new('NodeGroupInput')
node_tree.interface.new_socket("Size", in_out='INPUT', socket_type='NodeSocketFloat')
node_tree.interface.new_socket("Resolution", in_out='INPUT', socket_type='NodeSocketInt')
node_tree.interface.new_socket("Height Scale", in_out='INPUT', socket_type='NodeSocketFloat')
node_tree.interface.new_socket("Noise Scale", in_out='INPUT', socket_type='NodeSocketFloat')

# Create base grid
grid = nodes.new('GeometryNodeMeshGrid')

# Heightmap generation
position = nodes.new('GeometryNodeInputPosition')
noise_texture = nodes.new('ShaderNodeTexNoise')
voronoi_texture = nodes.new('ShaderNodeTexVoronoi')
mix_rgb = nodes.new('ShaderNodeMix')
mix_rgb.data_type = 'FLOAT'

# Set position based on noise
set_position = nodes.new('GeometryNodeSetPosition')
vector_math = nodes.new('ShaderNodeVectorMath')
vector_math.operation = 'MULTIPLY'

# Configure noise layers
noise_texture.inputs["Scale"].default_value = 2.0
noise_texture.inputs["Detail"].default_value = 8.0
noise_texture.inputs["Roughness"].default_value = 0.6

voronoi_texture.inputs["Scale"].default_value = 1.0
voronoi_texture.voronoi_dimensions = '3D'

# Mix noise types
mix_rgb.inputs["Factor"].default_value = 0.5

# Layout
group_input.location = (-1000, 0)
grid.location = (-800, 0)
position.location = (-800, -200)
noise_texture.location = (-600, -300)
voronoi_texture.location = (-600, -500)
mix_rgb.location = (-400, -400)
vector_math.location = (-200, -200)
set_position.location = (0, 0)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (200, 0)

# Connect terrain generation
links.new(group_input.outputs["Size"], grid.inputs["Size X"])
links.new(group_input.outputs["Size"], grid.inputs["Size Y"])
links.new(group_input.outputs["Resolution"], grid.inputs["Vertices X"])
links.new(group_input.outputs["Resolution"], grid.inputs["Vertices Y"])

links.new(grid.outputs[0], set_position.inputs[0])
links.new(position.outputs[0], noise_texture.inputs[0])
links.new(position.outputs[0], voronoi_texture.inputs[0])

links.new(noise_texture.outputs["Fac"], mix_rgb.inputs[6])
links.new(voronoi_texture.outputs["Distance"], mix_rgb.inputs[7])

# Apply height
vector_math.inputs[1].default_value = (0.0, 0.0, 5.0)  # Z-only displacement
links.new(mix_rgb.outputs[2], vector_math.inputs[0])
links.new(vector_math.outputs[0], set_position.inputs[3])

links.new(set_position.outputs[0], group_output.inputs[0])

print("Terrain generator created with multi-layer noise")
"""

response = requests.post(url, json={"code": code})
```

### Terrain Erosion Simulation

Add erosion effects to terrain using geometry nodes.

```python
code = """
import bpy

# Erosion effect using slope-based displacement
erosion_modifier = obj.modifiers.new("Erosion", type='NODES')
erosion_tree = bpy.data.node_groups.new("ErosionEffect", type='GeometryNodeTree')
erosion_modifier.node_group = erosion_tree

nodes = erosion_tree.nodes
links = erosion_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')

# Calculate slope
normal = nodes.new('GeometryNodeInputNormal')
separate_xyz = nodes.new('ShaderNodeSeparateXYZ')
math_abs = nodes.new('ShaderNodeMath')
math_abs.operation = 'ABSOLUTE'

# Erode steep slopes
compare = nodes.new('FunctionNodeCompare')
compare.operation = 'GREATER_THAN'
compare.inputs[1].default_value = 0.5  # Slope threshold

# Displace based on slope
set_position = nodes.new('GeometryNodeSetPosition')
vector_math = nodes.new('ShaderNodeVectorMath')
vector_math.operation = 'SCALE'

# Layout
group_input.location = (-600, 0)
normal.location = (-400, -200)
separate_xyz.location = (-200, -200)
compare.location = (0, -200)
set_position.location = (200, 0)
vector_math.location = (0, -400)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (400, 0)

# Connect erosion logic
links.new(group_input.outputs[0], set_position.inputs[0])
links.new(normal.outputs[0], separate_xyz.inputs[0])
links.new(separate_xyz.outputs[2], compare.inputs[0])  # Z component
links.new(compare.outputs[0], vector_math.inputs[1])
links.new(normal.outputs[0], vector_math.inputs[0])
links.new(vector_math.outputs[0], set_position.inputs[3])
links.new(set_position.outputs[0], group_output.inputs[0])

print("Erosion simulation created")
"""

response = requests.post(url, json={"code": code})
```

---

## Vegetation Systems

### Biome-Based Distribution

Create vegetation that responds to terrain slope and height.

```python
code = """
import bpy

# Create biome-aware vegetation system
vegetation_tree = bpy.data.node_groups.new("BiomeVegetation", type='GeometryNodeTree')
nodes = vegetation_tree.nodes
links = vegetation_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')

# Sample terrain attributes
position = nodes.new('GeometryNodeInputPosition')
separate_xyz = nodes.new('ShaderNodeSeparateXYZ')
normal = nodes.new('GeometryNodeInputNormal')

# Height-based biome zones
color_ramp_height = nodes.new('ShaderNodeValToRGB')
color_ramp_height.color_ramp.elements[0].position = 0.0  # Low = grass
color_ramp_height.color_ramp.elements[1].position = 0.7  # High = trees

# Slope-based filtering
color_ramp_slope = nodes.new('ShaderNodeValToRGB')
color_ramp_slope.color_ramp.elements[0].position = 0.3  # Flat areas only

# Distribution
distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
distribute.distribute_method = 'POISSON'

# Vegetation instances
instance_grass = nodes.new('GeometryNodeInstanceOnPoints')
instance_trees = nodes.new('GeometryNodeInstanceOnPoints')

# Vegetation geometry
grass_collection = nodes.new('GeometryNodeCollectionInfo')
tree_collection = nodes.new('GeometryNodeCollectionInfo')

# Switch based on biome
switch_biome = nodes.new('GeometryNodeSwitch')
switch_biome.input_type = 'GEOMETRY'

# Layout
group_input.location = (-1000, 0)
position.location = (-800, -200)
normal.location = (-800, -400)
separate_xyz.location = (-600, -200)
color_ramp_height.location = (-400, -200)
color_ramp_slope.location = (-400, -400)
distribute.location = (-200, 0)
switch_biome.location = (200, 0)
instance_grass.location = (0, 100)
instance_trees.location = (0, -100)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (400, 0)

# Connect biome logic
links.new(group_input.outputs[0], distribute.inputs[0])
links.new(position.outputs[0], separate_xyz.inputs[0])
links.new(separate_xyz.outputs[2], color_ramp_height.inputs[0])  # Height

# Filter by slope
links.new(normal.outputs[0], color_ramp_slope.inputs[0])
links.new(color_ramp_slope.outputs[0], distribute.inputs["Density"])

# Distribute vegetation
links.new(distribute.outputs[0], instance_grass.inputs[0])
links.new(distribute.outputs[0], instance_trees.inputs[0])

# Biome selection
links.new(color_ramp_height.outputs[0], switch_biome.inputs[0])
links.new(instance_grass.outputs[0], switch_biome.inputs[1])
links.new(instance_trees.outputs[0], switch_biome.inputs[2])

links.new(switch_biome.outputs[0], group_output.inputs[0])

print("Biome-based vegetation system created")
"""

response = requests.post(url, json={"code": code})
```

### Forest Scattering

Create realistic forest distribution with clearings.

```python
code = """
import bpy

# Forest with natural clearings
forest_tree = bpy.data.node_groups.new("ForestScatter", type='GeometryNodeTree')
nodes = forest_tree.nodes
links = forest_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')

# Create clearing pattern with Voronoi
position = nodes.new('GeometryNodeInputPosition')
voronoi = nodes.new('ShaderNodeTexVoronoi')
voronoi.voronoi_dimensions = '2D'
voronoi.inputs["Scale"].default_value = 0.5  # Large cells = large clearings

# Use distance from voronoi for density
color_ramp = nodes.new('ShaderNodeValToRGB')
color_ramp.color_ramp.elements[0].position = 0.3  # Dense forest
color_ramp.color_ramp.elements[1].position = 0.6  # Sparse edges

# Distribution with density mask
distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
math_multiply = nodes.new('ShaderNodeMath')
math_multiply.operation = 'MULTIPLY'
math_multiply.inputs[1].default_value = 100.0  # Base density

# Tree instances
instance_trees = nodes.new('GeometryNodeInstanceOnPoints')
collection_info = nodes.new('GeometryNodeCollectionInfo')

# Random rotation and scale
random_rotation = nodes.new('FunctionNodeRandomValue')
random_rotation.data_type = 'FLOAT_VECTOR'
random_scale = nodes.new('FunctionNodeRandomValue')
random_scale.data_type = 'FLOAT_VECTOR'
random_scale.inputs[2].default_value = (0.8, 0.8, 0.8)
random_scale.inputs[3].default_value = (1.5, 1.5, 1.5)

# Layout
group_input.location = (-1000, 0)
position.location = (-800, -200)
voronoi.location = (-600, -200)
color_ramp.location = (-400, -200)
math_multiply.location = (-200, -200)
distribute.location = (-200, 0)
instance_trees.location = (200, 0)
collection_info.location = (0, -200)
random_rotation.location = (0, -400)
random_scale.location = (0, -500)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (400, 0)

# Connect forest logic
links.new(group_input.outputs[0], distribute.inputs[0])
links.new(position.outputs[0], voronoi.inputs[0])
links.new(voronoi.outputs["Distance"], color_ramp.inputs[0])
links.new(color_ramp.outputs[0], math_multiply.inputs[0])
links.new(math_multiply.outputs[0], distribute.inputs["Density"])

# Instance trees
links.new(distribute.outputs[0], instance_trees.inputs[0])
links.new(collection_info.outputs[0], instance_trees.inputs[2])
links.new(random_rotation.outputs[1], instance_trees.inputs[5])
links.new(random_scale.outputs[1], instance_trees.inputs[6])

links.new(instance_trees.outputs[0], group_output.inputs[0])

print("Forest scattering system with natural clearings created")
"""

response = requests.post(url, json={"code": code})
```

---

## Parametric Design Patterns

### Modular Asset System

Create reusable parametric modules.

```python
code = """
import bpy

# Create parametric module (reusable node group)
module = bpy.data.node_groups.new("ParametricModule", type='GeometryNodeTree')
nodes = module.nodes
links = module.links
nodes.clear()

# Define module inputs
module.interface.new_socket("Base Size", in_out='INPUT', socket_type='NodeSocketFloat')
module.interface.new_socket("Detail Level", in_out='INPUT', socket_type='NodeSocketInt')
module.interface.new_socket("Variation Seed", in_out='INPUT', socket_type='NodeSocketInt')

# Module inputs/outputs
group_input = nodes.new('NodeGroupInput')
group_output = nodes.new('NodeGroupOutput')

# Module geometry
cube = nodes.new('GeometryNodeMeshCube')
subdivide = nodes.new('GeometryNodeSubdivisionSurface')
displace = nodes.new('GeometryNodeSetPosition')
noise = nodes.new('ShaderNodeTexNoise')

# Connect module
links.new(group_input.outputs["Base Size"], cube.inputs["Size"])
links.new(cube.outputs[0], subdivide.inputs[0])
links.new(group_input.outputs["Detail Level"], subdivide.inputs["Level"])
links.new(subdivide.outputs[0], displace.inputs[0])
links.new(group_input.outputs["Variation Seed"], noise.inputs["Seed"])
links.new(noise.outputs[0], displace.inputs[3])
links.new(displace.outputs[0], group_output.inputs[0])

print("Parametric module created and ready for reuse")
"""

# Use module in main tree
code2 = """
import bpy

# Reference module in main system
main_tree = bpy.data.node_groups.new("MainSystem", type='GeometryNodeTree')
nodes = main_tree.nodes
links = main_tree.links
nodes.clear()

# Instance the module
module_node = nodes.new('GeometryNodeGroup')
module_node.node_tree = bpy.data.node_groups.get("ParametricModule")

# Set module parameters
module_node.inputs["Base Size"].default_value = 2.0
module_node.inputs["Detail Level"].default_value = 3
module_node.inputs["Variation Seed"].default_value = 42

group_output = nodes.new('NodeGroupOutput')
links.new(module_node.outputs[0], group_output.inputs[0])

print("Module instance created in main tree")
"""

response = requests.post(url, json={"code": code})
response2 = requests.post(url, json={"code": code2})
```

---

## Return to Main Skill

**Back to:** `<workspace>\.claude\skills\blender-geometry-nodes\SKILL.md`
