# Rigid Body and Soft Body Physics

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Skill:** blender-physics-simulation
**Prerequisites:** Blender 4.5.0+, official Blender MCP

---

## Table of Contents

1. [Overview](#overview)
2. [Rigid Body System](#rigid-body-system)
3. [Rigid Body World](#rigid-body-world)
4. [Active vs Passive Objects](#active-vs-passive-objects)
5. [Collision Shapes](#collision-shapes)
6. [Constraints](#constraints)
7. [Soft Body Physics](#soft-body-physics)
8. [Cloth Simulation](#cloth-simulation)
9. [Performance Optimization](#performance-optimization)
10. [Baking and Cache](#baking-and-cache)
11. [Export Workflows](#export-workflows)
12. [Troubleshooting](#troubleshooting)
13. [Production Examples](#production-examples)

---

## Overview

Blender's physics system provides realistic motion for:
- **Rigid Body:** Hard objects (cubes, spheres, complex meshes)
- **Soft Body:** Deformable objects (rubber, jello, cushions)
- **Cloth:** Fabric simulation (flags, clothing, curtains)

**Key Capabilities:**
- Real-time viewport preview
- Accurate collision detection
- Constraint systems (hinges, motors, springs)
- Integration with particle systems
- Export to game engines (FBX, Alembic)

---

## Rigid Body System

### Architecture

```
Scene
+-- Rigid Body World
    +-- Simulation settings (gravity, steps, solver)
    +-- Objects
        +-- Active objects (dynamic)
        +-- Passive objects (static collision)
```

### Rigid Body World

The world contains global simulation settings:

```python
import bpy

# Access or create world
rb_world = bpy.context.scene.rigidbody_world
if not rb_world:
    # Create world (manual workaround - requires UI)
    print("ERROR: Rigid body world not initialized")
    print("Solution: Create in Blender UI first")
else:
    # Configure world
    rb_world.enabled = True
    rb_world.time_scale = 1.0  # 1.0 = realtime

    # Simulation quality
    rb_world.steps_per_second = 60  # Physics steps
    rb_world.solver_iterations = 10  # Constraint solver

    # Gravity
    rb_world.effector_weights.gravity = 1.0  # 0-1 multiplier
    # Note: Actual gravity vector from scene.gravity
    bpy.context.scene.gravity = (0, 0, -9.81)

    # Collision margins
    rb_world.use_split_impulse = True
```

**Performance vs Quality:**
- **Fast:** steps_per_second=30, solver_iterations=5
- **Balanced:** steps_per_second=60, solver_iterations=10
- **Accurate:** steps_per_second=120, solver_iterations=20

---

## Active vs Passive Objects

### Active Objects (Dynamic)

Move and react to forces:

```python
obj = bpy.data.objects['Cube']

# Set as active
obj.rigid_body.type = 'ACTIVE'

# Mass properties
obj.rigid_body.mass = 1.0
obj.rigid_body.use_margin = True
obj.rigid_body.collision_margin = 0.04

# Surface properties
obj.rigid_body.friction = 0.5      # 0=ice, 1=rubber
obj.rigid_body.restitution = 0.3   # 0=no bounce, 1=perfect bounce

# Damping (energy loss)
obj.rigid_body.linear_damping = 0.04   # Velocity damping
obj.rigid_body.angular_damping = 0.1   # Rotation damping
```

### Passive Objects (Static)

Stationary collision objects:

```python
ground = bpy.data.objects['Ground']

# Set as passive
ground.rigid_body.type = 'PASSIVE'

# Surface properties (still affect collisions)
ground.rigid_body.friction = 0.8
ground.rigid_body.restitution = 0.0

# Collision shape (important for complex geometry)
ground.rigid_body.collision_shape = 'MESH'  # See Collision Shapes section
```

### Animated Passive Objects

Passive objects can be animated (active objects collide with them):

```python
# Animate passive object location
moving_platform = bpy.data.objects['Platform']
moving_platform.rigid_body.type = 'PASSIVE'
moving_platform.rigid_body.kinematic = True  # Driven by animation, not physics

# Animate
moving_platform.location = (0, 0, 0)
moving_platform.keyframe_insert(data_path="location", frame=1)
moving_platform.location = (5, 0, 0)
moving_platform.keyframe_insert(data_path="location", frame=100)

# Active objects on platform will move with it
```

---

## Collision Shapes

### Shape Types

**BOX (Fastest):**
```python
obj.rigid_body.collision_shape = 'BOX'
# Uses object bounding box
# Best for: Cubes, rectangular objects
```

**SPHERE:**
```python
obj.rigid_body.collision_shape = 'SPHERE'
# Uses bounding sphere
# Best for: Balls, round objects
```

**CAPSULE:**
```python
obj.rigid_body.collision_shape = 'CAPSULE'
# Cylinder with hemispherical ends
# Best for: Characters, pills
```

**CYLINDER:**
```python
obj.rigid_body.collision_shape = 'CYLINDER'
# Flat-ended cylinder
# Best for: Cans, barrels
```

**CONE:**
```python
obj.rigid_body.collision_shape = 'CONE'
# Best for: Cone-shaped objects
```

**CONVEX_HULL:**
```python
obj.rigid_body.collision_shape = 'CONVEX_HULL'
# Wraps mesh in convex shape
# Best for: Simple complex shapes (rocks, props)
# More accurate than primitives, faster than MESH
```

**MESH (Slowest, Most Accurate):**
```python
obj.rigid_body.collision_shape = 'MESH'
# Uses actual mesh geometry
# Best for: Terrain, complex static objects
# WARNING: Only use for PASSIVE objects (active objects may be unstable)
```

### Shape Selection Guidelines

```python
# Simple objects -> Primitives
cube.rigid_body.collision_shape = 'BOX'
sphere.rigid_body.collision_shape = 'SPHERE'

# Complex active objects -> Convex Hull
rock.rigid_body.collision_shape = 'CONVEX_HULL'

# Complex passive objects -> Mesh
terrain.rigid_body.type = 'PASSIVE'
terrain.rigid_body.collision_shape = 'MESH'

# Moving objects -> Avoid MESH
moving_obstacle.rigid_body.type = 'ACTIVE'
moving_obstacle.rigid_body.collision_shape = 'CONVEX_HULL'  # Not MESH
```

---

## Constraints

Constraints connect rigid bodies (hinges, motors, springs).

### Constraint Types

**FIXED (Glue):**
```python
# Create empty at connection point
bpy.ops.object.empty_add(location=(0, 0, 1))
constraint_obj = bpy.context.active_object
constraint_obj.name = "FixedConstraint"

# Add constraint
constraint = constraint_obj.rigid_body_constraint
constraint.type = 'FIXED'
constraint.object1 = obj1
constraint.object2 = obj2

# Strength
constraint.use_breaking = True
constraint.breaking_threshold = 10.0  # Break at force > 10
```

**HINGE (Door):**
```python
constraint_obj.rigid_body_constraint.type = 'HINGE'
constraint.object1 = door
constraint.object2 = frame

# Hinge axis (Z-axis rotation)
constraint.use_limit_ang_z = True
constraint.limit_ang_z_lower = 0.0     # Fully closed
constraint.limit_ang_z_upper = 1.57    # 90 degrees open

# Motor (powered hinge)
constraint.use_motor_ang = True
constraint.motor_ang_target_velocity = 1.0  # Rotation speed
constraint.motor_ang_max_impulse = 1.0      # Motor strength
```

**SLIDER (Piston):**
```python
constraint_obj.rigid_body_constraint.type = 'SLIDER'
constraint.object1 = piston
constraint.object2 = cylinder

# Linear limits (Z-axis movement)
constraint.use_limit_lin_z = True
constraint.limit_lin_z_lower = 0.0
constraint.limit_lin_z_upper = 2.0  # 2 units of travel

# Spring
constraint.use_spring_z = True
constraint.spring_stiffness_z = 10.0
constraint.spring_damping_z = 0.5
```

**SPRING:**
```python
constraint_obj.rigid_body_constraint.type = 'SPRING'
constraint.object1 = weight
constraint.object2 = anchor

# Spring on all axes
constraint.use_spring_x = True
constraint.use_spring_y = True
constraint.use_spring_z = True

constraint.spring_stiffness_x = 10.0
constraint.spring_damping_x = 0.5
# etc. for Y, Z
```

**MOTOR:**
```python
constraint_obj.rigid_body_constraint.type = 'MOTOR'
constraint.object1 = wheel
constraint.object2 = axle

# Motor on Z-axis
constraint.use_motor_ang = True
constraint.motor_ang_target_velocity = 5.0  # Radians/sec
constraint.motor_ang_max_impulse = 10.0

# Linear motor (conveyor belt)
constraint.use_motor_lin = True
constraint.motor_lin_target_velocity = 2.0
constraint.motor_lin_max_impulse = 5.0
```

### Complete Constraint Example

**Swinging Pendulum:**
```python
import bpy

# Anchor (passive sphere at top)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 3))
anchor = bpy.context.active_object
anchor.name = "Anchor"
anchor.rigid_body.type = 'PASSIVE'

# Weight (active sphere below)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 1))
weight = bpy.context.active_object
weight.name = "Weight"
weight.rigid_body.type = 'ACTIVE'
weight.rigid_body.mass = 2.0

# Constraint (point between anchor and weight)
bpy.ops.object.empty_add(location=(0, 0, 2))
constraint_obj = bpy.context.active_object
constraint_obj.name = "PendulumHinge"

constraint = constraint_obj.rigid_body_constraint
constraint.type = 'HINGE'
constraint.object1 = anchor
constraint.object2 = weight

# Allow full rotation
constraint.use_limit_ang_z = False

# Disable breaking (rigid connection)
constraint.use_breaking = False

# Give initial push (animate weight at frame 1)
weight.location.x = 1.0  # Offset to side
```

---

## Soft Body Physics

Soft body simulates deformable objects.

### Basic Setup

```python
obj = bpy.data.objects['Cube']

# Add soft body modifier
sb_mod = obj.modifiers.new("Softbody", 'SOFT_BODY')
sb_settings = obj.soft_body

# Simulation settings
sb_settings.use_goal = True  # Pin vertices
sb_settings.use_edges = True  # Edge springs
sb_settings.use_self_collision = False  # Self-intersection

# Mass and friction
sb_settings.mass = 1.0
sb_settings.friction = 0.5

# Goal (vertex pinning)
sb_settings.goal_default = 0.0  # 0=free, 1=pinned
sb_settings.goal_min = 0.0
sb_settings.goal_max = 1.0
sb_settings.goal_spring = 0.5  # Pin strength
sb_settings.goal_friction = 0.0
```

### Stiffness Settings

```python
# Edge springs (structural integrity)
sb_settings.pull = 0.9   # Tension resistance (0-1)
sb_settings.push = 0.9   # Compression resistance (0-1)
sb_settings.damping = 0.5  # Oscillation damping
sb_settings.plastic = 0.0   # Permanent deformation
sb_settings.bend = 0.5      # Bending resistance

# Shear (lateral resistance)
sb_settings.shear = 0.5
```

### Collision Settings

```python
# Self collision
sb_settings.use_self_collision = True
sb_settings.self_collision_friction = 0.5

# Object collision
sb_settings.collision_type = 'MANUAL'
sb_settings.ball_size = 0.49  # Collision radius (< 0.5)
sb_settings.ball_damp = 0.5
```

### Vertex Group Pinning

```python
# Create vertex group for pinned vertices
vgroup = obj.vertex_groups.new(name="Pin")

# Pin top row of vertices (example for subdivided plane)
mesh = obj.data
for i, vert in enumerate(mesh.vertices):
    if vert.co.z > 0.9:  # Top vertices
        vgroup.add([i], 1.0, 'ADD')

# Assign to soft body
sb_settings.vertex_group_goal = "Pin"
```

### Complete Soft Body Example

**Bouncing Jello:**
```python
import bpy

# Create cube (subdivided for deformation)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2))
jello = bpy.context.active_object
jello.name = "Jello"

# Subdivide for smooth deformation
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=5)
bpy.ops.object.mode_set(mode='OBJECT')

# Soft body
sb_mod = jello.modifiers.new("Softbody", 'SOFT_BODY')
sb_settings = jello.soft_body

# Jello-like properties (soft, bouncy)
sb_settings.mass = 1.0
sb_settings.pull = 0.5   # Low tension (wobbly)
sb_settings.push = 0.5
sb_settings.damping = 0.05  # Low damping (oscillates)
sb_settings.friction = 0.2

# No pinning
sb_settings.use_goal = False

# Self collision
sb_settings.use_self_collision = True

# Ground (passive rigid body)
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.rigid_body.type = 'PASSIVE'
ground.rigid_body.friction = 0.5

print("Jello will fall and bounce - advance timeline")
```

---

## Cloth Simulation

Cloth is specialized soft body for fabric.

### Basic Cloth Setup

```python
obj = bpy.data.objects['Plane']

# Add cloth modifier
cloth_mod = obj.modifiers.new("Cloth", 'CLOTH')
cloth_settings = cloth_mod.settings

# Quality (simulation steps)
cloth_settings.quality = 5  # 1=fast, 10=accurate

# Physical properties
cloth_settings.mass = 0.3  # kg/m^2 (cotton ~ 0.3)
cloth_settings.air_damping = 1.0  # Air resistance

# Stiffness
cloth_settings.tension_stiffness = 15  # Stretch resistance
cloth_settings.compression_stiffness = 15
cloth_settings.shear_stiffness = 5     # Lateral resistance
cloth_settings.bending_stiffness = 0.5  # Fold resistance
```

### Material Presets

**Cotton:**
```python
cloth_settings.mass = 0.3
cloth_settings.tension_stiffness = 15
cloth_settings.bending_stiffness = 0.5
```

**Silk:**
```python
cloth_settings.mass = 0.15
cloth_settings.tension_stiffness = 5
cloth_settings.bending_stiffness = 0.05
```

**Leather:**
```python
cloth_settings.mass = 0.4
cloth_settings.tension_stiffness = 80
cloth_settings.bending_stiffness = 10
```

**Rubber:**
```python
cloth_settings.mass = 0.15
cloth_settings.tension_stiffness = 10
cloth_settings.bending_stiffness = 25
```

### Collision Settings

```python
# Cloth collision quality
collision = cloth_mod.collision_settings
collision.collision_quality = 5  # 1=fast, 5=accurate
collision.distance_min = 0.015   # Collision margin
collision.self_distance_min = 0.015  # Self-collision margin

# Friction
collision.friction = 5.0  # Cloth-object friction

# Self collision
cloth_settings.use_self_collision = True
collision.self_friction = 5.0
```

### Pinning Vertices

```python
# Create vertex group for pinned areas
vgroup = obj.vertex_groups.new(name="Pin")

# Pin top edge (example: subdivided plane)
mesh = obj.data
for i, vert in enumerate(mesh.vertices):
    if vert.co.z > 0.95:  # Top vertices
        vgroup.add([i], 1.0, 'ADD')

# Assign to cloth
cloth_settings.vertex_group_mass = "Pin"

# Pin stiffness
cloth_settings.pin_stiffness = 1.0  # 1.0 = fully pinned
```

### Wind and Forces

```python
# Wind force field
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, -5, 2))
wind = bpy.context.active_object
wind.name = "Wind"
wind.field.type = 'WIND'
wind.field.strength = 5.0
wind.field.noise = 1.0

# Cloth responds to force fields by default
# Adjust influence:
cloth_settings.effector_weights.gravity = 1.0
cloth_settings.effector_weights.wind = 1.0
```

### Complete Cloth Example

**Flag Waving in Wind:**
```python
import bpy

# Create plane (flag)
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 2))
flag = bpy.context.active_object
flag.name = "Flag"

# Subdivide for smooth draping
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=20)
bpy.ops.object.mode_set(mode='OBJECT')

# Rotate to vertical
flag.rotation_euler = (0, 1.5708, 0)  # 90 degrees Y-axis

# Cloth modifier
cloth_mod = flag.modifiers.new("Cloth", 'CLOTH')
cloth_settings = cloth_mod.settings

# Cotton-like properties
cloth_settings.quality = 5
cloth_settings.mass = 0.3
cloth_settings.tension_stiffness = 15
cloth_settings.bending_stiffness = 0.5
cloth_settings.air_damping = 1.0

# Collision settings
collision = cloth_mod.collision_settings
collision.collision_quality = 5
collision.distance_min = 0.015

# Pin left edge (flagpole side)
vgroup = flag.vertex_groups.new(name="Pin")
mesh = flag.data
for i, vert in enumerate(mesh.vertices):
    if vert.co.x < -0.95:  # Left edge
        vgroup.add([i], 1.0, 'ADD')

cloth_settings.vertex_group_mass = "Pin"

# Wind force
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(5, 0, 2))
wind = bpy.context.active_object
wind.name = "Wind"
wind.field.type = 'WIND'
wind.field.strength = 8.0
wind.field.noise = 2.0
wind.field.flow = 1.0

print("Flag configured - advance timeline to see waving")
```

---

## Performance Optimization

### Rigid Body Optimization

```python
# Use simple collision shapes
obj.rigid_body.collision_shape = 'BOX'  # Faster than MESH

# Reduce substeps for fast-moving objects
rb_world.steps_per_second = 60  # Lower = faster
rb_world.solver_iterations = 10  # Lower = faster, less stable

# Deactivation (sleep inactive objects)
obj.rigid_body.use_deactivation = True
obj.rigid_body.start_deactivated = False

# Margin optimization
obj.rigid_body.collision_margin = 0.04  # Larger = faster, less accurate
```

### Cloth Optimization

```python
# Reduce quality for preview
cloth_settings.quality = 2  # Increase to 5 for final

# Simplify mesh
# Use low-poly proxy for simulation, high-poly for render

# Collision quality
collision.collision_quality = 2  # Lower = faster

# Disable self-collision if not needed
cloth_settings.use_self_collision = False
```

### Soft Body Optimization

```python
# Reduce substeps
sb_settings.step_min = 10  # Default 10
sb_settings.step_max = 100  # Default 100

# Disable self-collision
sb_settings.use_self_collision = False

# Use goal pinning strategically
# Only pin necessary vertices
```

---

## Baking and Cache

### Baking Limitation

**Don't script the bake - it's a blocking, frame-stepped operation:**
```python
# Run interactively in Blender, not via a scripted call
bpy.ops.ptcache.bake_all()
bpy.ops.ptcache.free_bake_all()
```

**Workaround:** Configure via the official Blender MCP, bake in UI.

### Cache Configuration

**Rigid Body:**
```python
# Access point cache
rb_cache = bpy.context.scene.rigidbody_world.point_cache

rb_cache.frame_start = 1
rb_cache.frame_end = 250

# Cache to disk
rb_cache.use_disk_cache = True
rb_cache.use_library_path = False
rb_cache.filepath = "//cache/rigidbody/"
```

**Cloth:**
```python
cloth_cache = cloth_mod.point_cache

cloth_cache.frame_start = 1
cloth_cache.frame_end = 250
cloth_cache.use_disk_cache = True
cloth_cache.filepath = "//cache/cloth/"
```

**Soft Body:**
```python
sb_cache = obj.soft_body.point_cache

sb_cache.frame_start = 1
sb_cache.frame_end = 250
sb_cache.use_disk_cache = True
sb_cache.filepath = "//cache/softbody/"
```

### Manual Baking Workflow

1. **Configure via the official Blender MCP**
2. **Open Blender UI**
3. **Select object**
4. **Physics Properties > Cache**
5. **Click "Bake All Dynamics"**
6. **Verify cache files created**

### Verify Cache Status

```python
code = """
import bpy

# Rigid body
rb_cache = bpy.context.scene.rigidbody_world.point_cache
print(f"RB Baked: {rb_cache.is_baked}")

# Cloth
cloth_obj = bpy.data.objects['Flag']
cloth_cache = cloth_obj.modifiers['Cloth'].point_cache
print(f"Cloth Baked: {cloth_cache.is_baked}")

# Check cache files
import os
cache_path = bpy.path.abspath(cloth_cache.filepath)
if os.path.exists(cache_path):
    files = os.listdir(cache_path)
    print(f"Cache files: {len(files)}")
"""
```

---

## Export Workflows

### Export to Unreal Engine

**Rigid Body Animation:**
```python
# Bake rigid body simulation
# (Manual in UI - see above)

# Export as FBX
bpy.ops.export_scene.fbx(
    filepath="//export/rigid_body_sim.fbx",
    use_selection=False,
    bake_anim=True,
    bake_anim_use_all_bones=False,
    bake_anim_use_nla_strips=False,
    bake_anim_step=1.0,
    bake_anim_simplify_factor=0.0,
    add_leaf_bones=False
)
```

**Cloth/Soft Body Animation:**
```python
# Apply modifier (converts to keyframed mesh)
# WARNING: Irreversible - duplicate object first
obj_copy = obj.copy()
obj_copy.data = obj.data.copy()
bpy.context.scene.collection.objects.link(obj_copy)

# Apply cloth modifier (baked cache required)
bpy.context.view_layer.objects.active = obj_copy
bpy.ops.object.modifier_apply(modifier="Cloth")

# Export applied mesh
bpy.ops.export_scene.fbx(
    filepath="//export/cloth_baked.fbx",
    use_selection=True,
    bake_anim=True
)
```

### Export as Alembic

```python
# Alembic preserves deformation (better for cloth/soft body)
bpy.ops.wm.alembic_export(
    filepath="//export/cloth_sim.abc",
    selected=True,
    start=1,
    end=250,
    sh_open=0.0,
    sh_close=1.0,
    export_hair=False,
    export_particles=False,
    as_background_job=False
)
```

---

## Troubleshooting

### Issue: Rigid Body Not Moving

**Symptoms:**
- Object stays frozen
- Timeline advances but no motion

**Solutions:**
```python
# Check rigid body type
obj.rigid_body.type = 'ACTIVE'  # Not 'PASSIVE'

# Verify world enabled
if not bpy.context.scene.rigidbody_world:
    print("ERROR: Rigid body world not initialized")
    # Initialize in Blender UI first

rb_world = bpy.context.scene.rigidbody_world
rb_world.enabled = True

# Check mass (must be > 0)
obj.rigid_body.mass = 1.0

# Verify timeline advancing
bpy.context.scene.frame_set(10)
```

### Issue: Objects Falling Through Floor

**Symptoms:**
- Active objects pass through passive collision objects

**Solutions:**
```python
# Verify floor is passive
floor.rigid_body.type = 'PASSIVE'

# Check collision shape
floor.rigid_body.collision_shape = 'MESH'  # For complex geometry

# Increase collision margin
obj.rigid_body.collision_margin = 0.04
floor.rigid_body.collision_margin = 0.04

# Increase simulation quality
rb_world.steps_per_second = 120  # More steps = more accurate
rb_world.solver_iterations = 20
```

### Issue: Cloth Explodes

**Symptoms:**
- Cloth violently expands or tears
- Vertices shoot off

**Solutions:**
```python
# Reduce stiffness
cloth_settings.tension_stiffness = 5  # Lower = softer
cloth_settings.bending_stiffness = 0.1

# Increase quality
cloth_settings.quality = 10  # Max quality

# Increase collision distance
collision.distance_min = 0.05  # Larger margin

# Check for intersecting geometry
# Move cloth away from collision objects at frame 1
cloth_obj.location.z += 0.1

# Reduce time scale (slow motion debug)
rb_world.time_scale = 0.5  # Slower = more stable
```

### Issue: Soft Body Jittering

**Symptoms:**
- Constant vibration
- Unstable oscillation

**Solutions:**
```python
# Increase damping
sb_settings.damping = 0.9  # Higher = less oscillation

# Reduce stiffness
sb_settings.pull = 0.5
sb_settings.push = 0.5

# Increase simulation steps
sb_settings.step_min = 5
sb_settings.step_max = 50

# Enable goal (pin some vertices)
sb_settings.use_goal = True
sb_settings.goal_default = 0.5  # Partial pinning
```

### Issue: Constraints Breaking Too Easily

**Symptoms:**
- Hinges, sliders disconnect unexpectedly

**Solutions:**
```python
# Increase breaking threshold
constraint.use_breaking = True
constraint.breaking_threshold = 100.0  # Higher = stronger

# Or disable breaking
constraint.use_breaking = False

# Increase solver iterations
rb_world.solver_iterations = 20  # More accurate constraints

# Reduce object mass (less force on constraint)
obj.rigid_body.mass = 0.5
```

---

## Production Examples

### Example 1: Domino Chain

```python
import bpy

# Rigid body world
rb_world = bpy.context.scene.rigidbody_world
rb_world.steps_per_second = 60
rb_world.solver_iterations = 10

# Create domino template
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
domino_template = bpy.context.active_object
domino_template.name = "DominoTemplate"
domino_template.scale = (0.1, 0.5, 1.0)

# Rigid body
domino_template.rigid_body.type = 'ACTIVE'
domino_template.rigid_body.mass = 0.5
domino_template.rigid_body.friction = 0.5
domino_template.rigid_body.restitution = 0.1  # Low bounce

# Create chain
for i in range(10):
    domino = domino_template.copy()
    domino.data = domino_template.data.copy()
    domino.name = f"Domino_{i}"
    domino.location = (i * 0.6, 0, 0.5)  # Spaced 0.6 units apart
    bpy.context.scene.collection.objects.link(domino)

    # Rigid body instance
    domino.rigid_body.type = 'ACTIVE'

# Delete template
bpy.data.objects.remove(domino_template)

# Ground
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
ground = bpy.context.active_object
ground.rigid_body.type = 'PASSIVE'
ground.rigid_body.friction = 0.8

# Push first domino (keyframe rotation)
first_domino = bpy.data.objects['Domino_0']
first_domino.rotation_euler.y = 0.0
first_domino.keyframe_insert(data_path="rotation_euler", frame=1)
first_domino.rotation_euler.y = 0.3
first_domino.keyframe_insert(data_path="rotation_euler", frame=20)

print("Domino chain ready - advance timeline")
```

### Example 2: Wrecking Ball

```python
import bpy

# Anchor point (passive)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 5))
anchor = bpy.context.active_object
anchor.name = "Anchor"
anchor.rigid_body.type = 'PASSIVE'

# Wrecking ball (active, heavy)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 3, 2))
ball = bpy.context.active_object
ball.name = "WreckingBall"
ball.rigid_body.type = 'ACTIVE'
ball.rigid_body.mass = 100.0  # Heavy
ball.rigid_body.collision_shape = 'SPHERE'

# Constraint (cable)
bpy.ops.object.empty_add(location=(0, 0, 3.5))
constraint_obj = bpy.context.active_object
constraint_obj.name = "Cable"

constraint = constraint_obj.rigid_body_constraint
constraint.type = 'POINT'  # Ball joint
constraint.object1 = anchor
constraint.object2 = ball
constraint.use_breaking = False

# Wall to destroy (stack of cubes)
for i in range(3):
    for j in range(5):
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, -1, 0.25 + i*0.5))
        cube = bpy.context.active_object
        cube.name = f"Brick_{i}_{j}"
        cube.location.y = -1.0 - j * 0.5
        cube.rigid_body.type = 'ACTIVE'
        cube.rigid_body.mass = 1.0

# Ground
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
ground = bpy.context.active_object
ground.rigid_body.type = 'PASSIVE'

print("Wrecking ball ready - timeline plays destruction")
```

### Example 3: Tablecloth Pull

```python
import bpy

# Table (passive)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
table = bpy.context.active_object
table.name = "Table"
table.scale = (2, 1, 0.1)
table.rigid_body.type = 'PASSIVE'

# Tablecloth (cloth)
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, 1.1))
cloth = bpy.context.active_object
cloth.name = "Tablecloth"

# Subdivide
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=30)
bpy.ops.object.mode_set(mode='OBJECT')

# Cloth modifier
cloth_mod = cloth.modifiers.new("Cloth", 'CLOTH')
cloth_settings = cloth_mod.settings

cloth_settings.quality = 5
cloth_settings.mass = 0.3
cloth_settings.tension_stiffness = 10
cloth_settings.bending_stiffness = 1.0

# Collision
collision = cloth_mod.collision_settings
collision.collision_quality = 5
collision.distance_min = 0.02

# Tableware (rigid bodies on cloth)
for i in range(3):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.2, location=(i*0.5 - 0.5, 0, 1.2))
    cup = bpy.context.active_object
    cup.name = f"Cup_{i}"
    cup.rigid_body.type = 'ACTIVE'
    cup.rigid_body.mass = 0.2
    cup.rigid_body.collision_shape = 'CYLINDER'

# Animate cloth pull (move one edge)
vgroup = cloth.vertex_groups.new(name="Pull")
mesh = cloth.data
for i, vert in enumerate(mesh.vertices):
    if vert.co.x < -1.4:  # One edge
        vgroup.add([i], 1.0, 'ADD')

# Animate vertex group (requires shape keys - complex)
# Simpler: Animate wind force
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-5, 0, 1))
wind = bpy.context.active_object
wind.name = "Pull"
wind.field.type = 'WIND'
wind.field.strength = 0.0
wind.keyframe_insert(data_path="field.strength", frame=1)
wind.field.strength = 50.0
wind.keyframe_insert(data_path="field.strength", frame=20)
wind.field.strength = 0.0
wind.keyframe_insert(data_path="field.strength", frame=40)

print("Tablecloth pull ready - cups will tumble")
```

---

**End of Rigid Body and Soft Body Physics Reference**

For particle systems, see: ADVANCED_PARTICLE_SYSTEMS.md
For fluid simulation, see: FLUID_SIMULATION_GUIDE.md
For skill overview, see: ../SKILL.md
