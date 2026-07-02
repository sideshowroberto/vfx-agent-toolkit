---
name: blender-geometry-nodes
description: Procedural modeling using Geometry Nodes in Blender. Use for scattering systems, node trees, parametric design, or when user mentions "procedural," "geometry nodes," "scattering," or "instances."
allowed-tools: Read,Write
---

# Blender Geometry Nodes Skill

**Version:** 2.0.0
**Last Updated:** 2026-06-10
**Dependencies:** Blender 5.1+

---

## API Note (Blender 5.1+)

Use `type='NODES'` (not `type='GEOMETRY_NODES'`, which was removed in 4.5):

```python
import bpy
modifier = obj.modifiers.new("GeometryNodes", type='NODES')
```

`bpy.ops` works normally via the Blender MCP — use direct data API for explicit control, operators when convenient.

---

## QUICK START

### Scattering System

```python
import bpy

# Create base plane
verts = [(-5,-5,0), (5,-5,0), (5,5,0), (-5,5,0)]
faces = [[0,1,2,3]]
mesh = bpy.data.meshes.new("BasePlane")
mesh.from_pydata(verts, [], faces)
mesh.update()

obj = bpy.data.objects.new("ScatterBase", mesh)
bpy.context.collection.objects.link(obj)

# Create NODES modifier
modifier = obj.modifiers.new("Scattering", type='NODES')

# Create node tree
node_tree = bpy.data.node_groups.new("ScatterSystem", type='GeometryNodeTree')
modifier.node_group = node_tree

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

# Build node tree
input_node = nodes.new('NodeGroupInput')
output_node = nodes.new('NodeGroupOutput')
distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
instance = nodes.new('GeometryNodeInstanceOnPoints')
cube = nodes.new('GeometryNodeMeshCube')

# Position nodes
input_node.location = (-400, 0)
distribute.location = (-200, 0)
instance.location = (0, 0)
cube.location = (-200, -200)
output_node.location = (200, 0)

# Connect nodes
links.new(input_node.outputs[0], distribute.inputs[0])
links.new(distribute.outputs[0], instance.inputs[0])
links.new(cube.outputs[0], instance.inputs[2])
links.new(instance.outputs[0], output_node.inputs[0])

print(f"Created: {len(nodes)} nodes, {len(links)} links")
```

---

## STANDARD WORKFLOWS

### Workflow 1: Point Distribution System

**Use When:** Scatter objects across surfaces with density control

```python
import bpy

# Create target surface
mesh = bpy.data.meshes.new("Surface")
verts = [(-10,-10,0), (10,-10,0), (10,10,0), (-10,10,0)]
faces = [[0,1,2,3]]
mesh.from_pydata(verts, [], faces)
mesh.update()

obj = bpy.data.objects.new("Surface", mesh)
bpy.context.collection.objects.link(obj)

# Add geometry nodes
modifier = obj.modifiers.new("Distribution", type='NODES')
node_tree = bpy.data.node_groups.new("PointDistribution", type='GeometryNodeTree')
modifier.node_group = node_tree

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')
group_output = nodes.new('NodeGroupOutput')
distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
instance = nodes.new('GeometryNodeInstanceOnPoints')
sphere = nodes.new('GeometryNodeMeshUVSphere')
random_value = nodes.new('FunctionNodeRandomValue')

distribute.inputs["Density"].default_value = 50.0
sphere.inputs["Radius"].default_value = 0.2
random_value.data_type = 'FLOAT_VECTOR'

group_input.location = (-600, 0)
distribute.location = (-400, 0)
instance.location = (-200, 0)
sphere.location = (-400, -200)
random_value.location = (-400, -400)
group_output.location = (0, 0)

links.new(group_input.outputs[0], distribute.inputs[0])
links.new(distribute.outputs[0], instance.inputs[0])
links.new(sphere.outputs[0], instance.inputs[2])
links.new(random_value.outputs[1], instance.inputs[6])  # Rotation
links.new(instance.outputs[0], group_output.inputs[0])

print(f"Distribution system: {len(nodes)} nodes")
```

---

### Workflow 2: Parametric Array System

**Use When:** Repeating patterns with parameters

```python
import bpy

mesh = bpy.data.meshes.new("ArrayBase")
obj = bpy.data.objects.new("ParametricArray", mesh)
bpy.context.collection.objects.link(obj)

modifier = obj.modifiers.new("Array", type='NODES')
node_tree = bpy.data.node_groups.new("ParametricSystem", type='GeometryNodeTree')
modifier.node_group = node_tree

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')
group_output = nodes.new('NodeGroupOutput')
cube_node = nodes.new('GeometryNodeMeshCube')
duplicate = nodes.new('GeometryNodeDuplicateElements')
transform = nodes.new('GeometryNodeTransform')

cube_node.inputs["Size"].default_value = (1.0, 1.0, 1.0)
duplicate.inputs["Amount"].default_value = 10
transform.inputs["Translation"].default_value = (2.0, 0.0, 0.0)

group_input.location = (-600, 0)
cube_node.location = (-400, 0)
duplicate.location = (-200, 0)
transform.location = (0, 0)
group_output.location = (200, 0)

links.new(cube_node.outputs[0], duplicate.inputs[0])
links.new(duplicate.outputs[0], transform.inputs[0])
links.new(transform.outputs[0], group_output.inputs[0])

print(f"Array created: {duplicate.inputs['Amount'].default_value} instances")
```

---

### Workflow 3: Curve-to-Mesh Procedural

**Use When:** Convert curves to geometry procedurally

```python
import bpy

curve_data = bpy.data.curves.new("PathCurve", type='CURVE')
curve_data.dimensions = '3D'
spline = curve_data.splines.new('BEZIER')
spline.bezier_points.add(3)

points = [(-5, 0, 0), (-2, 3, 0), (2, 3, 0), (5, 0, 0)]
for i, point in enumerate(points):
    spline.bezier_points[i].co = point
    spline.bezier_points[i].handle_left_type = 'AUTO'
    spline.bezier_points[i].handle_right_type = 'AUTO'

curve_obj = bpy.data.objects.new("Path", curve_data)
bpy.context.collection.objects.link(curve_obj)

modifier = curve_obj.modifiers.new("CurveToMesh", type='NODES')
node_tree = bpy.data.node_groups.new("CurveConversion", type='GeometryNodeTree')
modifier.node_group = node_tree

nodes = node_tree.nodes
links = node_tree.links
nodes.clear()

group_input = nodes.new('NodeGroupInput')
group_output = nodes.new('NodeGroupOutput')
curve_to_mesh = nodes.new('GeometryNodeCurveToMesh')
curve_circle = nodes.new('GeometryNodeCurvePrimitiveCircle')

curve_circle.inputs["Radius"].default_value = 0.1
curve_circle.inputs["Resolution"].default_value = 8

group_input.location = (-400, 0)
curve_circle.location = (-200, -200)
curve_to_mesh.location = (0, 0)
group_output.location = (200, 0)

links.new(group_input.outputs[0], curve_to_mesh.inputs[0])
links.new(curve_circle.outputs[0], curve_to_mesh.inputs[1])
links.new(curve_to_mesh.outputs[0], group_output.inputs[0])

print("Curve-to-mesh created")
```

---

### Workflow 4: Multi-Lane Scatter System

**Use When:** Production ground cover — pebbles, gravel, debris with realistic density falloff across size ranges

**Pattern:** Three lanes (large/medium/small) each with an independent mask input. Medium and small use a two-stage density multiply for non-linear falloff. All lanes share a single Factor input. Output joins all instance geo plus the pass-through ground.

**Scale ranges:** Large 0.25–0.60 | Medium 0.25–0.45 | Small 0.10–0.35

```python
import bpy
import math

# Assumes you have objects named "Pebble_Large", "Pebble_Medium", "Pebble_Small"
# and a ground plane object named "Ground" already in the scene.
# Adjust object names to match your scene.

ground = bpy.data.objects.get("Ground")
if not ground:
    print("ERROR: 'Ground' object not found")
    raise SystemExit

modifier = ground.modifiers.new("MultiLaneScatter", type='NODES')
nt = bpy.data.node_groups.new("MultiLaneScatter", type='GeometryNodeTree')
modifier.node_group = nt

nodes = nt.nodes
links = nt.links
nodes.clear()

# --- Group I/O ---
gi = nodes.new('NodeGroupInput')
go = nodes.new('NodeGroupOutput')
gi.location = (-1200, 0)
go.location = (800, 0)

# Expose inputs: Factor (float), Seed (int), MaskLarge/MaskMedium/MaskSmall (float)
iface = nt.interface
iface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
iface.new_socket("Factor", in_out='INPUT', socket_type='NodeSocketFloat')
iface.new_socket("Seed", in_out='INPUT', socket_type='NodeSocketInt')
iface.new_socket("Mask Large", in_out='INPUT', socket_type='NodeSocketFloat')
iface.new_socket("Mask Medium", in_out='INPUT', socket_type='NodeSocketFloat')
iface.new_socket("Mask Small", in_out='INPUT', socket_type='NodeSocketFloat')
iface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

# --- LARGE LANE (single-stage: Density Factor + Density Max) ---
dist_large = nodes.new('GeometryNodeDistributePointsOnFaces')
dist_large.distribute_method = 'RANDOM'
dist_large.inputs["Density"].default_value = 2.0   # Density Factor
dist_large.inputs["Distance Min"].default_value = 0.25
dist_large.location = (-800, 300)

inst_large = nodes.new('GeometryNodeInstanceOnPoints')
inst_large.location = (-400, 300)

scale_large = nodes.new('FunctionNodeRandomValue')
scale_large.data_type = 'FLOAT'
scale_large.inputs[2].default_value = 0.25   # min
scale_large.inputs[3].default_value = 0.60   # max
scale_large.location = (-600, 150)

rot_large = nodes.new('FunctionNodeRandomValue')
rot_large.data_type = 'FLOAT_VECTOR'
rot_large.inputs[4].default_value = (-math.pi, -math.pi, -math.pi)
rot_large.inputs[5].default_value = (math.pi, math.pi, math.pi)
rot_large.location = (-600, 50)

obj_info_large = nodes.new('GeometryNodeObjectInfo')
obj_large = bpy.data.objects.get("Pebble_Large")
if obj_large:
    obj_info_large.inputs[0].default_value = obj_large
obj_info_large.location = (-600, 400)

links.new(gi.outputs["Geometry"], dist_large.inputs["Mesh"])
links.new(gi.outputs["Mask Large"], dist_large.inputs["Selection"])
links.new(gi.outputs["Factor"], dist_large.inputs["Density"])
links.new(dist_large.outputs["Points"], inst_large.inputs["Points"])
links.new(obj_info_large.outputs["Geometry"], inst_large.inputs["Instance"])
links.new(rot_large.outputs[0], inst_large.inputs["Rotation"])
links.new(scale_large.outputs[1], inst_large.inputs["Scale"])

# --- MEDIUM LANE (two-stage density multiply for non-linear falloff) ---
dist_medium = nodes.new('GeometryNodeDistributePointsOnFaces')
dist_medium.distribute_method = 'RANDOM'
dist_medium.inputs["Density"].default_value = 8.0
dist_medium.location = (-800, 0)

mul_medium = nodes.new('ShaderNodeMath')
mul_medium.operation = 'MULTIPLY'
mul_medium.inputs[1].default_value = 0.5   # density multiplier stage 2
mul_medium.location = (-1000, -100)

inst_medium = nodes.new('GeometryNodeInstanceOnPoints')
inst_medium.location = (-400, 0)

scale_medium = nodes.new('FunctionNodeRandomValue')
scale_medium.data_type = 'FLOAT'
scale_medium.inputs[2].default_value = 0.25
scale_medium.inputs[3].default_value = 0.45
scale_medium.location = (-600, -100)

rot_medium = nodes.new('FunctionNodeRandomValue')
rot_medium.data_type = 'FLOAT_VECTOR'
rot_medium.inputs[4].default_value = (-math.pi, -math.pi, -math.pi)
rot_medium.inputs[5].default_value = (math.pi, math.pi, math.pi)
rot_medium.location = (-600, -200)

obj_info_medium = nodes.new('GeometryNodeObjectInfo')
obj_medium = bpy.data.objects.get("Pebble_Medium")
if obj_medium:
    obj_info_medium.inputs[0].default_value = obj_medium
obj_info_medium.location = (-600, 100)

links.new(gi.outputs["Factor"], mul_medium.inputs[0])
links.new(gi.outputs["Mask Medium"], mul_medium.inputs[1])
links.new(gi.outputs["Geometry"], dist_medium.inputs["Mesh"])
links.new(gi.outputs["Mask Medium"], dist_medium.inputs["Selection"])
links.new(mul_medium.outputs[0], dist_medium.inputs["Density"])
links.new(dist_medium.outputs["Points"], inst_medium.inputs["Points"])
links.new(obj_info_medium.outputs["Geometry"], inst_medium.inputs["Instance"])
links.new(rot_medium.outputs[0], inst_medium.inputs["Rotation"])
links.new(scale_medium.outputs[1], inst_medium.inputs["Scale"])

# --- SMALL LANE (two-stage density multiply, denser) ---
dist_small = nodes.new('GeometryNodeDistributePointsOnFaces')
dist_small.distribute_method = 'RANDOM'
dist_small.inputs["Density"].default_value = 20.0
dist_small.location = (-800, -300)

mul_small = nodes.new('ShaderNodeMath')
mul_small.operation = 'MULTIPLY'
mul_small.inputs[1].default_value = 0.7
mul_small.location = (-1000, -400)

inst_small = nodes.new('GeometryNodeInstanceOnPoints')
inst_small.location = (-400, -300)

scale_small = nodes.new('FunctionNodeRandomValue')
scale_small.data_type = 'FLOAT'
scale_small.inputs[2].default_value = 0.10
scale_small.inputs[3].default_value = 0.35
scale_small.location = (-600, -350)

rot_small = nodes.new('FunctionNodeRandomValue')
rot_small.data_type = 'FLOAT_VECTOR'
rot_small.inputs[4].default_value = (-math.pi, -math.pi, -math.pi)
rot_small.inputs[5].default_value = (math.pi, math.pi, math.pi)
rot_small.location = (-600, -450)

obj_info_small = nodes.new('GeometryNodeObjectInfo')
obj_small = bpy.data.objects.get("Pebble_Small")
if obj_small:
    obj_info_small.inputs[0].default_value = obj_small
obj_info_small.location = (-600, -200)

links.new(gi.outputs["Factor"], mul_small.inputs[0])
links.new(gi.outputs["Mask Small"], mul_small.inputs[1])
links.new(gi.outputs["Geometry"], dist_small.inputs["Mesh"])
links.new(gi.outputs["Mask Small"], dist_small.inputs["Selection"])
links.new(mul_small.outputs[0], dist_small.inputs["Density"])
links.new(dist_small.outputs["Points"], inst_small.inputs["Points"])
links.new(obj_info_small.outputs["Geometry"], inst_small.inputs["Instance"])
links.new(rot_small.outputs[0], inst_small.inputs["Rotation"])
links.new(scale_small.outputs[1], inst_small.inputs["Scale"])

# --- JOIN all instance geo + pass-through ground ---
join = nodes.new('GeometryNodeJoinGeometry')
join.location = (400, 0)

links.new(gi.outputs["Geometry"], join.inputs["Geometry"])   # ground pass-through
links.new(inst_large.outputs["Instances"], join.inputs["Geometry"])
links.new(inst_medium.outputs["Instances"], join.inputs["Geometry"])
links.new(inst_small.outputs["Instances"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], go.inputs["Geometry"])

print("Multi-lane scatter system created: 3 lanes (large/medium/small)")
print("Notes: expose Seed input per-lane if needed; merge three Factor sockets into one shared driver")
```

**Design notes:**
- Large lane uses single-stage density (direct Factor × Density Factor) for natural sparse distribution
- Medium/small use two-stage multiply (Factor × Mask) for non-linear density falloff in masked areas
- Expose `Seed` as a group input so iterations can be varied non-destructively
- Merging all three per-lane Factor sockets to a single shared Factor makes the system easier to art-direct

---

## TROUBLESHOOTING

### Issue 1: "GEOMETRY_NODES" Type Error

**Symptoms:** `enum "GEOMETRY_NODES" not found`

**Solution:**
```python
import bpy
modifier = obj.modifiers.new("Name", type='NODES')  # Not 'GEOMETRY_NODES'
```

---

### Issue 2: Socket Type Mismatch

**Symptoms:** Nodes won't connect, grey connections, "Incompatible socket types"

```python
import bpy

node_tree = bpy.data.node_groups.get("YourTree")
if node_tree:
    node_a = node_tree.nodes.get("NodeA")
    node_b = node_tree.nodes.get("NodeB")

    output_type = node_a.outputs[0].type
    input_type = node_b.inputs[0].type
    print(f"Output: {output_type}, Input: {input_type}")

    if output_type == input_type:
        node_tree.links.new(node_a.outputs[0], node_b.inputs[0])
    else:
        if output_type == 'VALUE' and input_type == 'VECTOR':
            combine = node_tree.nodes.new('ShaderNodeCombineXYZ')
            node_tree.links.new(node_a.outputs[0], combine.inputs[0])
            node_tree.links.new(combine.outputs[0], node_b.inputs[0])
```

---

## VALIDATION CHECKLIST

- [ ] Using `type='NODES'` not `type='GEOMETRY_NODES'`
- [ ] Node tree created and assigned to modifier
- [ ] Node connections valid (matching socket types)
- [ ] Parameters exposed for user control
- [ ] Visual result visible in viewport
- [ ] No console errors

---

## VERSION HISTORY

**v2.0.0** (2026-06-10) - MCP migration
- Removed legacy HTTP bridge patterns (migrated to Blender MCP)
- Removed `import requests` wrappers
- Added `import bpy` to all code blocks
- Added Workflow 4: Multi-Lane Scatter System (pebble/gravel production pattern)
- Updated target: Blender 5.1+
- Removed absolute paths to blender-ai-compatibility

**v1.1.0** (2025-10-24) - Article III compliance
**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+
