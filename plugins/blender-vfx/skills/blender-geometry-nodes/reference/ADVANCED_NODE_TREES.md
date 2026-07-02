# Blender Geometry Nodes - Advanced Node Trees

**Part of:** blender-geometry-nodes skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers advanced geometry node tree techniques including complex procedural systems, multi-level instancing, field-based operations, and advanced attribute manipulation.

---

## Field-Based Animation

### Overview

Field nodes allow procedural animation by driving geometry parameters with mathematical fields.

### Implementation Pattern

```python
import requests
import json
# Execute via the Blender MCP tool: execute_blender_code
code = """
import bpy

# Create animated system
obj = bpy.data.objects.get("AnimatedGeometry")
if not obj:
    mesh = bpy.data.meshes.new("AnimatedMesh")
    obj = bpy.data.objects.new("AnimatedGeometry", mesh)
    bpy.context.collection.objects.link(obj)

modifier = obj.modifiers.new("Animation", type='NODES')
node_tree = bpy.data.node_groups.new("FieldAnimation", type='GeometryNodeTree')
modifier.node_group = node_tree

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Build field-based system
group_input = nodes.new('NodeGroupInput')
group_output = nodes.new('NodeGroupOutput')
grid = nodes.new('GeometryNodeMeshGrid')
set_position = nodes.new('GeometryNodeSetPosition')
position = nodes.new('GeometryNodeInputPosition')
noise = nodes.new('ShaderNodeTexNoise')
vector_math = nodes.new('ShaderNodeVectorMath')

# Parameters
grid.inputs["Size X"].default_value = 10.0
grid.inputs["Size Y"].default_value = 10.0
grid.inputs["Vertices X"].default_value = 20
grid.inputs["Vertices Y"].default_value = 20
noise.inputs["Scale"].default_value = 2.0
vector_math.operation = 'MULTIPLY'

# Layout
group_input.location = (-800, 0)
grid.location = (-600, 0)
set_position.location = (0, 0)
position.location = (-400, -200)
noise.location = (-400, -400)
vector_math.location = (-200, -300)
group_output.location = (200, 0)

# Connect field system
links.new(grid.outputs[0], set_position.inputs[0])
links.new(position.outputs[0], noise.inputs[0])
links.new(noise.outputs[1], vector_math.inputs[0])
links.new(vector_math.outputs[0], set_position.inputs[2])
links.new(set_position.outputs[0], group_output.inputs[0])

print("Field-based animation system created")
"""

response = requests.post(url, json={"code": code})
print(response.json()["output"])
```

### Key Parameters

- `noise.inputs["Scale"]`: Controls wave frequency (higher = more detail)
- `vector_math multiplier`: Animation amplitude (displacement strength)
- `grid resolution`: Detail level (vertices X/Y)

### Animation Techniques

**Time-Based Animation:**
```python
# Add scene time input
scene_time = nodes.new('GeometryNodeInputSceneTime')
math_add = nodes.new('ShaderNodeMath')
math_add.operation = 'ADD'

# Connect time to noise offset
links.new(scene_time.outputs[0], math_add.inputs[0])
links.new(position.outputs[0], math_add.inputs[1])
links.new(math_add.outputs[0], noise.inputs[0])
```

**Directional Wave:**
```python
# Add vector multiply for direction
vector_multiply = nodes.new('ShaderNodeVectorMath')
vector_multiply.operation = 'MULTIPLY'
vector_multiply.inputs[1].default_value = (1.0, 0.0, 0.0)  # X-axis wave

links.new(noise.outputs[1], vector_multiply.inputs[0])
links.new(vector_multiply.outputs[0], set_position.inputs[2])
```

---

## Multi-Level Instancing

### Overview

Create complex procedural systems by nesting instance operations for performance.

### Pattern: Instanced Vegetation System

```python
code = """
import bpy

# Create vegetation distribution system
mesh = bpy.data.meshes.new("TerrainBase")
obj = bpy.data.objects.new("Terrain", mesh)
bpy.context.collection.objects.link(obj)

modifier = obj.modifiers.new("Vegetation", type='NODES')
node_tree = bpy.data.node_groups.new("VegetationSystem", type='GeometryNodeTree')
modifier.node_group = node_tree

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Layer 1: Terrain distribution
group_input = nodes.new('NodeGroupInput')
distribute_main = nodes.new('GeometryNodeDistributePointsOnFaces')
instance_main = nodes.new('GeometryNodeInstanceOnPoints')

# Layer 2: Grass clump (nested instances)
distribute_grass = nodes.new('GeometryNodeDistributePointsInVolume')
instance_grass = nodes.new('GeometryNodeInstanceOnPoints')
grass_blade = nodes.new('GeometryNodeMeshCone')

# Layer 3: Random variation
random_scale = nodes.new('FunctionNodeRandomValue')
random_rotation = nodes.new('FunctionNodeRandomValue')

# Configure grass blade
grass_blade.inputs["Radius Top"].default_value = 0.0
grass_blade.inputs["Radius Bottom"].default_value = 0.02
grass_blade.inputs["Depth"].default_value = 0.3

# Configure distributions
distribute_main.inputs["Density"].default_value = 10.0  # Clumps per m²
distribute_grass.inputs["Density"].default_value = 100.0  # Blades per clump

# Configure randomization
random_scale.data_type = 'FLOAT_VECTOR'
random_scale.inputs[2].default_value = (0.5, 0.5, 0.5)  # Min
random_scale.inputs[3].default_value = (1.5, 1.5, 1.5)  # Max
random_rotation.data_type = 'FLOAT_VECTOR'

# Layout
group_input.location = (-1000, 0)
distribute_main.location = (-800, 0)
distribute_grass.location = (-600, -300)
instance_grass.location = (-400, -300)
grass_blade.location = (-600, -500)
instance_main.location = (-200, 0)
random_scale.location = (-400, -100)
random_rotation.location = (-400, -200)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (0, 0)

# Connect nested system
links.new(group_input.outputs[0], distribute_main.inputs[0])
links.new(distribute_main.outputs[0], instance_main.inputs[0])

# Grass clump creation
links.new(grass_blade.outputs[0], instance_grass.inputs[2])
links.new(distribute_grass.outputs[0], instance_grass.inputs[0])

# Connect to main instances
links.new(instance_grass.outputs[0], instance_main.inputs[2])

# Randomization
links.new(random_scale.outputs[1], instance_grass.inputs[6])
links.new(random_rotation.outputs[1], instance_grass.inputs[7])

links.new(instance_main.outputs[0], group_output.inputs[0])

print("Multi-level vegetation system created")
"""

response = requests.post(url, json={"code": code})
```

### Performance Optimization

**Instance Collections:**
```python
# Use collection instances for complex geometry
collection = bpy.data.collections.new("TreeVariations")
bpy.context.scene.collection.children.link(collection)

# Add multiple tree models to collection
# ...then instance entire collection
collection_info = nodes.new('GeometryNodeCollectionInfo')
collection_info.inputs["Collection"].default_value = collection
links.new(collection_info.outputs[0], instance_main.inputs[2])
```

**Level-of-Detail:**
```python
# Distance-based LOD switching
proximity = nodes.new('GeometryNodeProximity')
compare = nodes.new('FunctionNodeCompare')
switch = nodes.new('GeometryNodeSwitch')

# Switch between high/low detail based on distance
compare.operation = 'LESS_THAN'
compare.inputs[1].default_value = 10.0  # Switch distance

links.new(proximity.outputs[1], compare.inputs[0])
links.new(compare.outputs[0], switch.inputs[0])
links.new(high_detail_geo.outputs[0], switch.inputs[1])
links.new(low_detail_geo.outputs[0], switch.inputs[2])
```

---

## Advanced Attribute Manipulation

### Named Attributes

Create and manipulate custom attributes for procedural control.

```python
code = """
import bpy

node_tree = bpy.data.node_groups.get("AttributeSystem")
if not node_tree:
    node_tree = bpy.data.node_groups.new("AttributeSystem", type='GeometryNodeTree')

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Create geometry with custom attributes
group_input = nodes.new('NodeGroupInput')
grid = nodes.new('GeometryNodeMeshGrid')

# Store custom attribute
store_attr = nodes.new('GeometryNodeStoreNamedAttribute')
store_attr.data_type = 'FLOAT_VECTOR'
store_attr.inputs["Name"].default_value = "custom_color"

# Generate attribute data with noise
position = nodes.new('GeometryNodeInputPosition')
noise = nodes.new('ShaderNodeTexNoise')
color_ramp = nodes.new('ShaderNodeValToRGB')

# Connect attribute generation
links.new(grid.outputs[0], store_attr.inputs[0])
links.new(position.outputs[0], noise.inputs[0])
links.new(noise.outputs[1], color_ramp.inputs[0])
links.new(color_ramp.outputs[0], store_attr.inputs[3])

# Use attribute later in tree
capture_attr = nodes.new('GeometryNodeCaptureAttribute')
capture_attr.data_type = 'FLOAT_VECTOR'

group_output = nodes.new('NodeGroupOutput')
links.new(store_attr.outputs[0], group_output.inputs[0])

print("Named attribute system created")
"""

response = requests.post(url, json={"code": code})
```

### Attribute Transfer

Transfer attributes between geometries:

```python
# Transfer attributes from source to target
sample_nearest = nodes.new('GeometryNodeSampleNearest')
sample_index = nodes.new('GeometryNodeSampleIndex')

# Sample from source geometry
links.new(source_geo.outputs[0], sample_nearest.inputs[0])
links.new(target_position.outputs[0], sample_nearest.inputs[1])
links.new(sample_nearest.outputs[0], sample_index.inputs[1])

# Read and store attribute
links.new(source_geo.outputs[0], sample_index.inputs[0])
links.new(sample_index.outputs[2], store_attr.inputs[3])  # Vector output
```

---

## Geometry Math Operations

### Boolean Operations (Procedural)

```python
code = """
import bpy

# Create boolean system
node_tree = bpy.data.node_groups.new("BooleanSystem", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')
mesh_boolean = nodes.new('GeometryNodeMeshBoolean')

# Create objects to boolean
cube = nodes.new('GeometryNodeMeshCube')
sphere = nodes.new('GeometryNodeMeshUVSphere')

# Position sphere inside cube
transform = nodes.new('GeometryNodeTransform')
transform.inputs["Translation"].default_value = (0.5, 0.5, 0.5)

# Setup boolean
mesh_boolean.operation = 'DIFFERENCE'  # Subtract sphere from cube

# Layout
cube.location = (-400, 0)
sphere.location = (-400, -200)
transform.location = (-200, -200)
mesh_boolean.location = (0, 0)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (200, 0)

# Connect
links.new(cube.outputs[0], mesh_boolean.inputs[0])
links.new(sphere.outputs[0], transform.inputs[0])
links.new(transform.outputs[0], mesh_boolean.inputs[1])
links.new(mesh_boolean.outputs[0], group_output.inputs[0])

print("Procedural boolean system created")
"""

response = requests.post(url, json={"code": code})
```

### Convex Hull

```python
# Create convex hull from points
convex_hull = nodes.new('GeometryNodeConvexHull')
points = nodes.new('GeometryNodePoints')

# Generate random points
random_pos = nodes.new('FunctionNodeRandomValue')
random_pos.data_type = 'FLOAT_VECTOR'
random_pos.inputs[2].default_value = (-5, -5, -5)  # Min
random_pos.inputs[3].default_value = (5, 5, 5)    # Max

points.inputs["Count"].default_value = 50

links.new(points.outputs[0], convex_hull.inputs[0])
links.new(random_pos.outputs[1], points.inputs[0])
```

### Merge by Distance

```python
# Clean up overlapping vertices
merge = nodes.new('GeometryNodeMergeByDistance')
merge.inputs["Distance"].default_value = 0.001  # Threshold

links.new(source_geo.outputs[0], merge.inputs[0])
links.new(merge.outputs[0], output_node.inputs[0])
```

---

## Simulation Nodes

### Overview

Geometry nodes simulation allows frame-by-frame state storage.

### Basic Simulation Pattern

```python
code = """
import bpy

# Create simulation node tree
node_tree = bpy.data.node_groups.new("SimulationSystem", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Simulation zone
sim_input = nodes.new('GeometryNodeSimulationInput')
sim_output = nodes.new('GeometryNodeSimulationOutput')

# Physics simulation (gravity example)
points = nodes.new('GeometryNodePoints')
set_position = nodes.new('GeometryNodeSetPosition')
position = nodes.new('GeometryNodeInputPosition')
vector_math = nodes.new('ShaderNodeVectorMath')

# Add gravity vector
vector_math.operation = 'ADD'
vector_math.inputs[1].default_value = (0.0, 0.0, -0.1)  # Gravity

# Initial state
points.inputs["Count"].default_value = 100
points.location = (-600, 0)

# Simulation loop
sim_input.location = (-400, 0)
set_position.location = (-200, 0)
position.location = (-400, -200)
vector_math.location = (-200, -200)
sim_output.location = (0, 0)

# Connect simulation
links.new(points.outputs[0], sim_input.inputs[0])
links.new(sim_input.outputs[0], set_position.inputs[0])
links.new(position.outputs[0], vector_math.inputs[0])
links.new(vector_math.outputs[0], set_position.inputs[2])
links.new(set_position.outputs[0], sim_output.inputs[0])

group_output = nodes.new('NodeGroupOutput')
group_output.location = (200, 0)
links.new(sim_output.outputs[0], group_output.inputs[0])

print("Simulation system created")
"""

response = requests.post(url, json={"code": code})
```

### State Storage

Simulations can store multiple attributes:

```python
# Store velocity attribute in simulation
store_velocity = nodes.new('GeometryNodeStoreNamedAttribute')
store_velocity.data_type = 'FLOAT_VECTOR'
store_velocity.inputs["Name"].default_value = "velocity"

# Update velocity each frame
links.new(velocity_calc.outputs[0], store_velocity.inputs[3])
links.new(store_velocity.outputs[0], sim_output.inputs[0])
```

---

## Return to Main Skill

**Back to:** `<workspace>\.claude\skills\blender-geometry-nodes\SKILL.md`
