# Blender Geometry Nodes - Node Tree Optimization

**Part of:** blender-geometry-nodes skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers performance optimization techniques, node tree organization patterns, debugging strategies, and common reusable node tree patterns for Geometry Nodes.

---

## Performance Optimization

### Geometry Complexity Management

**Rule of Thumb:** Keep viewport geometry under 1M vertices for interactive performance.

```python
import requests
import json
# Execute via the Blender MCP tool: execute_blender_code
# Check geometry complexity
code = """
import bpy

obj = bpy.data.objects.get("ProceduralObject")
if obj and obj.type == 'MESH':
    # Get evaluated geometry (after modifiers)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.data

    vert_count = len(mesh_eval.vertices)
    poly_count = len(mesh_eval.polygons)

    print(f"Vertices: {vert_count:,}")
    print(f"Polygons: {poly_count:,}")

    if vert_count > 1_000_000:
        print("[WARN] WARNING: High vertex count may impact performance")
    elif vert_count > 5_000_000:
        print("[FAIL] CRITICAL: Reduce geometry complexity")
"""

response = requests.post(url, json={"code": code})
print(response.json()["output"])
```

### Viewport vs Render Detail

Use different detail levels for viewport and final render.

```python
code = """
import bpy

# Create LOD system
node_tree = bpy.data.node_groups.new("LODSystem", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')

# Detect render context
is_viewport = nodes.new('GeometryNodeIsViewport')

# Low detail (viewport)
low_detail_grid = nodes.new('GeometryNodeMeshGrid')
low_detail_grid.inputs["Vertices X"].default_value = 50
low_detail_grid.inputs["Vertices Y"].default_value = 50

# High detail (render)
high_detail_grid = nodes.new('GeometryNodeMeshGrid')
high_detail_grid.inputs["Vertices X"].default_value = 500
high_detail_grid.inputs["Vertices Y"].default_value = 500

# Switch based on context
switch = nodes.new('GeometryNodeSwitch')
switch.input_type = 'GEOMETRY'

# Layout
group_input.location = (-600, 0)
is_viewport.location = (-400, -200)
low_detail_grid.location = (-200, 100)
high_detail_grid.location = (-200, -100)
switch.location = (0, 0)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (200, 0)

# Connect LOD logic
links.new(is_viewport.outputs[0], switch.inputs[0])
links.new(low_detail_grid.outputs[0], switch.inputs[1])  # False = viewport
links.new(high_detail_grid.outputs[0], switch.inputs[2])  # True = render
links.new(switch.outputs[0], group_output.inputs[0])

print("LOD system created (50x50 viewport, 500x500 render)")
"""

response = requests.post(url, json={"code": code})
```

### Instancing vs Real Geometry

**Performance Impact:** Instances are 10-100x faster than real geometry.

```python
code = """
import bpy

# Compare: Real geometry vs instances
node_tree = bpy.data.node_groups.new("InstanceComparison", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# [FAIL] SLOW: Joining real geometry (100 cubes = 800 verts each = 80k verts)
cube_slow = nodes.new('GeometryNodeMeshCube')
duplicate_slow = nodes.new('GeometryNodeDuplicateElements')
duplicate_slow.inputs["Amount"].default_value = 100
realize_slow = nodes.new('GeometryNodeRealizeInstances')  # Makes real geometry

# [OK] FAST: Using instances (100 cubes = 800 verts TOTAL)
cube_fast = nodes.new('GeometryNodeMeshCube')
points = nodes.new('GeometryNodePoints')
points.inputs["Count"].default_value = 100
instance_fast = nodes.new('GeometryNodeInstanceOnPoints')

# Slow path
links.new(cube_slow.outputs[0], duplicate_slow.inputs[0])
links.new(duplicate_slow.outputs[0], realize_slow.inputs[0])

# Fast path
links.new(points.outputs[0], instance_fast.inputs[0])
links.new(cube_fast.outputs[0], instance_fast.inputs[2])

print("Slow path: 80,000 vertices")
print("Fast path: 800 vertices (100x improvement)")
"""

response = requests.post(url, json={"code": code})
```

### Caching Expensive Operations

Use "Capture Attribute" to cache expensive calculations.

```python
code = """
import bpy

# Cache expensive noise calculation
node_tree = bpy.data.node_groups.new("CachedNoise", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')
grid = nodes.new('GeometryNodeMeshGrid')

# Expensive operation (calculated once)
position = nodes.new('GeometryNodeInputPosition')
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs["Scale"].default_value = 5.0
noise.inputs["Detail"].default_value = 15.0  # Expensive

# Cache result
capture = nodes.new('GeometryNodeCaptureAttribute')
capture.data_type = 'FLOAT'

# Use cached value multiple times
color_ramp_1 = nodes.new('ShaderNodeValToRGB')
color_ramp_2 = nodes.new('ShaderNodeValToRGB')
color_ramp_3 = nodes.new('ShaderNodeValToRGB')

# Layout
group_input.location = (-800, 0)
grid.location = (-600, 0)
position.location = (-600, -200)
noise.location = (-400, -200)
capture.location = (-200, 0)
color_ramp_1.location = (0, 100)
color_ramp_2.location = (0, 0)
color_ramp_3.location = (0, -100)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (200, 0)

# Cache noise output
links.new(grid.outputs[0], capture.inputs[0])
links.new(position.outputs[0], noise.inputs[0])
links.new(noise.outputs[0], capture.inputs[1])

# Reuse cached value (noise calculated only once)
links.new(capture.outputs[1], color_ramp_1.inputs[0])
links.new(capture.outputs[1], color_ramp_2.inputs[0])
links.new(capture.outputs[1], color_ramp_3.inputs[0])

links.new(capture.outputs[0], group_output.inputs[0])

print("Expensive noise cached and reused 3 times")
"""

response = requests.post(url, json={"code": code})
```

---

## Node Tree Organization

### Naming Conventions

**Standard Naming Pattern:**
- **Node Trees:** `[Purpose]_[Type]` (e.g., "Terrain_Generator", "Tree_Scattering")
- **Nodes:** `[Function]_[Index]` (e.g., "Noise_01", "Instance_Main")
- **Attributes:** `[domain]_[name]` (e.g., "point_color", "face_index")

```python
code = """
import bpy

# Apply naming convention
node_tree = bpy.data.node_groups.new("Forest_Scattering_System", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Named nodes for clarity
group_input = nodes.new('NodeGroupInput')
group_input.name = "Input_Parameters"

distribute_main = nodes.new('GeometryNodeDistributePointsOnFaces')
distribute_main.name = "Distribute_Main_Trees"
distribute_main.label = "Main Distribution"

distribute_undergrowth = nodes.new('GeometryNodeDistributePointsOnFaces')
distribute_undergrowth.name = "Distribute_Undergrowth"
distribute_undergrowth.label = "Undergrowth Layer"

instance_trees = nodes.new('GeometryNodeInstanceOnPoints')
instance_trees.name = "Instance_Trees_Collection"
instance_trees.label = "Tree Instances"

group_output = nodes.new('NodeGroupOutput')
group_output.name = "Output_Geometry"

print("Node tree organized with clear naming")
for node in nodes:
    print(f"  - {node.name}: {node.type}")
"""

response = requests.post(url, json={"code": code})
```

### Frame Organization

Group related nodes in frames for visual clarity.

```python
code = """
import bpy

node_tree = bpy.data.node_groups.get("Forest_Scattering_System")
if node_tree:
    nodes = node_tree.nodes

    # Create frame for distribution logic
    frame_distribution = nodes.new('NodeFrame')
    frame_distribution.name = "FRAME_Distribution"
    frame_distribution.label = "Point Distribution System"
    frame_distribution.use_custom_color = True
    frame_distribution.color = (0.3, 0.5, 0.3)  # Green

    # Create frame for instancing
    frame_instances = nodes.new('NodeFrame')
    frame_instances.name = "FRAME_Instances"
    frame_instances.label = "Instance Generation"
    frame_instances.use_custom_color = True
    frame_instances.color = (0.3, 0.3, 0.5)  # Blue

    # Assign nodes to frames
    distribute_main = nodes.get("Distribute_Main_Trees")
    if distribute_main:
        distribute_main.parent = frame_distribution

    instance_trees = nodes.get("Instance_Trees_Collection")
    if instance_trees:
        instance_trees.parent = frame_instances

    print("Node tree organized with color-coded frames")
"""

response = requests.post(url, json={"code": code})
```

### Reroute Nodes for Clean Connections

Use reroute nodes to avoid crossing connections.

```python
code = """
import bpy

node_tree = bpy.data.node_groups.get("Forest_Scattering_System")
if node_tree:
    nodes = node_tree.nodes
    links = node_tree.links

    # Create reroute for commonly used data
    reroute_geometry = nodes.new('NodeReroute')
    reroute_geometry.name = "REROUTE_Base_Geometry"
    reroute_geometry.location = (-400, 200)

    reroute_random = nodes.new('NodeReroute')
    reroute_random.name = "REROUTE_Random_Seed"
    reroute_random.location = (-400, -200)

    print("Reroute nodes created for clean connections")
"""

response = requests.post(url, json={"code": code})
```

---

## Debugging Strategies

### Geometry Viewers

Use "Viewer" node to inspect intermediate geometry.

```python
code = """
import bpy

node_tree = bpy.data.node_groups.get("Your_Node_Tree")
if node_tree:
    nodes = node_tree.nodes
    links = node_tree.links

    # Add viewer to inspect geometry
    viewer = nodes.new('GeometryNodeViewer')
    viewer.name = "DEBUG_Viewer"
    viewer.location = (0, -300)

    # Connect to geometry you want to inspect
    distribute_node = nodes.get("Distribute_Main_Trees")
    if distribute_node:
        links.new(distribute_node.outputs[0], viewer.inputs[0])

    print("Viewer node added - check 'Viewer' object in outliner")
"""

response = requests.post(url, json={"code": code})
```

### Attribute Inspection

Check attribute values during debugging.

```python
code = """
import bpy

# Inspect attributes on evaluated geometry
obj = bpy.data.objects.get("ProceduralObject")
if obj and obj.type == 'MESH':
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.data

    # List all attributes
    print("Attributes on geometry:")
    for attr in mesh.attributes:
        print(f"  - {attr.name}: {attr.data_type} ({attr.domain})")

        # Sample first few values
        if attr.domain == 'POINT' and len(attr.data) > 0:
            if attr.data_type == 'FLOAT':
                print(f"    Sample values: {[attr.data[i].value for i in range(min(3, len(attr.data)))]}")
            elif attr.data_type == 'FLOAT_VECTOR':
                print(f"    Sample values: {[attr.data[i].vector[:] for i in range(min(3, len(attr.data)))]}")
"""

response = requests.post(url, json={"code": code})
```

### Node Socket Value Inspection

Check intermediate node values.

```python
code = """
import bpy

# Inspect node socket default values
node_tree = bpy.data.node_groups.get("Your_Node_Tree")
if node_tree:
    print("Node socket values:")
    for node in node_tree.nodes:
        print(f"\\n{node.name} ({node.type}):")
        for input in node.inputs:
            if hasattr(input, 'default_value'):
                print(f"  Input: {input.name} = {input.default_value}")
        for output in node.outputs:
            if hasattr(output, 'default_value'):
                print(f"  Output: {output.name} = {output.default_value}")
"""

response = requests.post(url, json={"code": code})
```

### Performance Profiling

Identify slow nodes using viewport statistics.

```python
code = """
import bpy
import time

# Time modifier evaluation
obj = bpy.data.objects.get("ProceduralObject")
if obj:
    start_time = time.time()

    # Force evaluation
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    _ = obj_eval.data  # Access mesh to force full evaluation

    elapsed = time.time() - start_time
    print(f"Modifier evaluation time: {elapsed:.3f} seconds")

    if elapsed > 1.0:
        print("[WARN] Slow evaluation - consider optimization")
    elif elapsed > 5.0:
        print("[FAIL] Very slow - reduce complexity or cache results")
"""

response = requests.post(url, json={"code": code})
```

---

## Common Node Tree Patterns

### Pattern: Scatter with Exclusion Zones

Create scattering that avoids specific areas.

```python
code = """
import bpy

# Scattering with exclusion zones
node_tree = bpy.data.node_groups.new("Scatter_With_Exclusion", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')
node_tree.interface.new_socket("Surface", in_out='INPUT', socket_type='NodeSocketGeometry')
node_tree.interface.new_socket("Exclusion Zone", in_out='INPUT', socket_type='NodeSocketGeometry')

# Check distance to exclusion zone
geometry_proximity = nodes.new('GeometryNodeProximity')
geometry_proximity.target_element = 'FACES'

# Filter points outside exclusion radius
compare = nodes.new('FunctionNodeCompare')
compare.operation = 'GREATER_THAN'
compare.inputs[1].default_value = 2.0  # Exclusion radius

# Distribution
distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
distribute.inputs["Density"].default_value = 100.0

# Delete points in exclusion zone
delete_geometry = nodes.new('GeometryNodeDeleteGeometry')

# Layout
group_input.location = (-600, 0)
distribute.location = (-400, 0)
geometry_proximity.location = (-400, -200)
compare.location = (-200, -200)
delete_geometry.location = (0, 0)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (200, 0)

# Connect exclusion logic
links.new(group_input.outputs["Surface"], distribute.inputs[0])
links.new(distribute.outputs[0], delete_geometry.inputs[0])
links.new(group_input.outputs["Exclusion Zone"], geometry_proximity.inputs[0])
links.new(geometry_proximity.outputs[1], compare.inputs[0])  # Distance
links.new(compare.outputs[0], delete_geometry.inputs[1])  # Selection
links.new(delete_geometry.outputs[0], group_output.inputs[0])

print("Scatter with exclusion zones pattern created")
"""

response = requests.post(url, json={"code": code})
```

### Pattern: Attribute-Driven Variation

Use attributes to control per-instance properties.

```python
code = """
import bpy

# Attribute-driven instance variation
node_tree = bpy.data.node_groups.new("Attribute_Variation", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')

# Create points with custom attribute
distribute = nodes.new('GeometryNodeDistributePointsOnFaces')

# Generate variation attribute (0.0 to 1.0)
random_value = nodes.new('FunctionNodeRandomValue')
random_value.data_type = 'FLOAT'

# Store as named attribute
store_attr = nodes.new('GeometryNodeStoreNamedAttribute')
store_attr.data_type = 'FLOAT'
store_attr.inputs["Name"].default_value = "variation"

# Use attribute to control scale
map_range = nodes.new('ShaderNodeMapRange')
map_range.inputs["From Min"].default_value = 0.0
map_range.inputs["From Max"].default_value = 1.0
map_range.inputs["To Min"].default_value = 0.5
map_range.inputs["To Max"].default_value = 2.0

combine_xyz = nodes.new('ShaderNodeCombineXYZ')

# Instance with scale from attribute
instance = nodes.new('GeometryNodeInstanceOnPoints')
cube = nodes.new('GeometryNodeMeshCube')

# Layout
group_input.location = (-800, 0)
distribute.location = (-600, 0)
random_value.location = (-600, -200)
store_attr.location = (-400, 0)
map_range.location = (-200, -200)
combine_xyz.location = (0, -200)
instance.location = (200, 0)
cube.location = (0, -400)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (400, 0)

# Connect attribute variation
links.new(group_input.outputs[0], distribute.inputs[0])
links.new(distribute.outputs[0], store_attr.inputs[0])
links.new(random_value.outputs[1], store_attr.inputs[3])
links.new(store_attr.outputs[0], instance.inputs[0])
links.new(random_value.outputs[1], map_range.inputs[0])
links.new(map_range.outputs[0], combine_xyz.inputs[0])
links.new(map_range.outputs[0], combine_xyz.inputs[1])
links.new(map_range.outputs[0], combine_xyz.inputs[2])
links.new(combine_xyz.outputs[0], instance.inputs[6])  # Scale
links.new(cube.outputs[0], instance.inputs[2])
links.new(instance.outputs[0], group_output.inputs[0])

print("Attribute-driven variation pattern created")
"""

response = requests.post(url, json={"code": code})
```

### Pattern: Procedural Masking

Create complex distribution masks using multiple noise layers.

```python
code = """
import bpy

# Multi-layer procedural mask
node_tree = bpy.data.node_groups.new("Procedural_Mask", type='GeometryNodeTree')
nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')
position = nodes.new('GeometryNodeInputPosition')

# Layer 1: Large features
noise_large = nodes.new('ShaderNodeTexNoise')
noise_large.inputs["Scale"].default_value = 1.0
noise_large.inputs["Detail"].default_value = 2.0

# Layer 2: Medium detail
noise_medium = nodes.new('ShaderNodeTexNoise')
noise_medium.inputs["Scale"].default_value = 5.0
noise_medium.inputs["Detail"].default_value = 5.0

# Layer 3: Fine detail
noise_fine = nodes.new('ShaderNodeTexNoise')
noise_fine.inputs["Scale"].default_value = 20.0
noise_fine.inputs["Detail"].default_value = 8.0

# Combine layers
mix_1 = nodes.new('ShaderNodeMix')
mix_1.data_type = 'FLOAT'
mix_1.inputs[0].default_value = 0.5

mix_2 = nodes.new('ShaderNodeMix')
mix_2.data_type = 'FLOAT'
mix_2.inputs[0].default_value = 0.3

# Final threshold
color_ramp = nodes.new('ShaderNodeValToRGB')
color_ramp.color_ramp.elements[0].position = 0.4
color_ramp.color_ramp.elements[1].position = 0.6

# Layout
group_input.location = (-800, 0)
position.location = (-600, -200)
noise_large.location = (-400, 0)
noise_medium.location = (-400, -200)
noise_fine.location = (-400, -400)
mix_1.location = (-200, -100)
mix_2.location = (0, -200)
color_ramp.location = (200, -200)
group_output = nodes.new('NodeGroupOutput')
group_output.location = (400, 0)

# Connect mask layers
links.new(position.outputs[0], noise_large.inputs[0])
links.new(position.outputs[0], noise_medium.inputs[0])
links.new(position.outputs[0], noise_fine.inputs[0])
links.new(noise_large.outputs[0], mix_1.inputs[6])
links.new(noise_medium.outputs[0], mix_1.inputs[7])
links.new(mix_1.outputs[2], mix_2.inputs[6])
links.new(noise_fine.outputs[0], mix_2.inputs[7])
links.new(mix_2.outputs[2], color_ramp.inputs[0])
links.new(color_ramp.outputs[0], group_output.inputs[0])

print("Multi-layer procedural mask created")
"""

response = requests.post(url, json={"code": code})
```

---

## Return to Main Skill

**Back to:** `<workspace>\.claude\skills\blender-geometry-nodes\SKILL.md`
