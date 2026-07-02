# Advanced Particle Systems Reference

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Skill:** blender-physics-simulation
**Prerequisites:** Blender 4.5.0+, official Blender MCP

---

## Table of Contents

1. [Overview](#overview)
2. [HTTP Bridge Compatibility](#http-bridge-compatibility)
3. [Particle System Architecture](#particle-system-architecture)
4. [Emission Methods](#emission-methods)
5. [Physics Types](#physics-types)
6. [Particle Instancing](#particle-instancing)
7. [Force Fields](#force-fields)
8. [Collision Detection](#collision-detection)
9. [Caching and Baking](#caching-and-baking)
10. [Performance Optimization](#performance-optimization)
11. [Render Settings](#render-settings)
12. [Advanced Techniques](#advanced-techniques)
13. [Troubleshooting](#troubleshooting)

---

## Overview

Blender's particle system is a complex framework for creating dynamic effects ranging from rain and snow to debris, sparks, smoke trails, and instanced geometry forests. This reference covers advanced particle workflows optimized for HTTP Bridge automation.

**Key Capabilities:**
- Emitter-based particle generation
- Newton/Keyed/Boids physics simulation
- Particle instancing (render objects on particles)
- Force field interactions
- Collision detection and response
- Hair and fluid particle systems
- Caching for performance and repeatability

**Critical Limitation:** 80% of `bpy.ops` operators fail in HTTP Bridge context. Use direct API patterns documented below.

---

## HTTP Bridge Compatibility

### Critical Patterns

**ALWAYS USE Direct API:**
```python
import requests

code = """
import bpy

# ✅ CORRECT: Direct modifier creation
obj = bpy.data.objects['Emitter']
psys_mod = obj.modifiers.new("ParticleSystem", 'PARTICLE_SYSTEM')
settings = obj.particle_systems[-1].settings
settings.count = 1000
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**NEVER USE Operators:**
```python
# ❌ WRONG: Context failure
bpy.ops.object.particle_system_add()  # Fails in HTTP Bridge
bpy.ops.particle.new()                # Fails in HTTP Bridge
bpy.ops.ptcache.bake_all()           # Fails in HTTP Bridge
```

### Verification Pattern

```python
# Always verify HTTP Bridge before execution
import requests

try:
    health = requests.get("http://the Blender MCP/health", timeout=2)
    if health.status_code != 200:
        raise ConnectionError("HTTP Bridge unhealthy")
except Exception as e:
    print(f"ERROR: HTTP Bridge not available - {e}")
    exit(1)
```

---

## Particle System Architecture

### Data Structure

```
Object (Emitter)
└── Modifiers
    └── ParticleSystem Modifier
        └── Particle System
            ├── Settings (ParticleSettings)
            │   ├── Emission properties
            │   ├── Physics properties
            │   ├── Render properties
            │   ├── Field weights
            │   └── Vertex groups
            └── Particles (runtime data)
                ├── Location
                ├── Velocity
                ├── Rotation
                └── Lifetime
```

### Creating Particle System (Direct API)

```python
import bpy

# Get or create emitter object
emitter = bpy.data.objects.get("Emitter")
if not emitter:
    mesh = bpy.data.meshes.new("EmitterMesh")
    emitter = bpy.data.objects.new("Emitter", mesh)
    bpy.context.scene.collection.objects.link(emitter)

# Add particle system modifier
psys_mod = emitter.modifiers.new("ParticleSystem", 'PARTICLE_SYSTEM')

# Access settings (created automatically)
psys = emitter.particle_systems[-1]
settings = psys.settings
settings.name = "MyParticles"

# Configure basic properties
settings.count = 1000
settings.frame_start = 1
settings.frame_end = 250
settings.lifetime = 50
settings.lifetime_random = 0.2
```

### Multiple Particle Systems

```python
# Add second particle system to same object
psys_mod2 = emitter.modifiers.new("ParticleSystem2", 'PARTICLE_SYSTEM')
settings2 = emitter.particle_systems[-1].settings
settings2.count = 500
settings2.particle_size = 0.05

# Access specific particle system
psys_by_name = emitter.particle_systems.get("MyParticles")
psys_by_index = emitter.particle_systems[0]
```

---

## Emission Methods

### Volume Emission

Emit from object volume (default for meshes):

```python
settings.emit_from = 'VOLUME'
settings.count = 5000
settings.normal_factor = 0.0  # No surface normal influence
settings.factor_random = 1.0  # Random direction
settings.use_emit_random = True
settings.use_even_distribution = False  # Random positions
```

**Use Case:** Explosions, dust clouds, magic effects

### Face Emission

Emit from mesh faces:

```python
settings.emit_from = 'FACE'
settings.use_emit_random = True
settings.normal_factor = 1.0  # Emit along face normals
settings.tangent_factor = 0.0
settings.tangent_phase = 0.0
```

**Use Case:** Smoke from surface, sparks from metal, rain from cloud

### Vertex Emission

Emit from vertices (precise control):

```python
settings.emit_from = 'VERT'
settings.use_emit_random = False
settings.invert_vertex_group_density = False

# Use vertex group for density control
vgroup = emitter.vertex_groups.new(name="EmissionDensity")
for i, vert in enumerate(emitter.data.vertices):
    weight = 1.0 if i % 2 == 0 else 0.0
    vgroup.add([i], weight, 'ADD')

settings.vertex_group_density = "EmissionDensity"
```

**Use Case:** Grass/hair placement, precise effect triggering

### Emission Distribution

```python
# Even distribution (grid-like)
settings.use_even_distribution = True
settings.jitter_factor = 0.0  # No randomness

# Random distribution
settings.use_even_distribution = False
settings.use_emit_random = True
settings.random_factor = 1.0

# Grid distribution (volume only)
settings.distribution = 'GRID'
settings.grid_resolution = 10
settings.grid_random = 0.2
```

---

## Physics Types

### Newton Physics

Realistic physics with gravity and forces:

```python
settings.physics_type = 'NEWTON'

# Initial velocity
settings.normal_factor = 1.0      # Velocity along emission normal
settings.tangent_factor = 0.0     # Tangent velocity
settings.factor_random = 0.5      # Randomness (0-1)
settings.object_align_factor = (0, 0, 1)  # Global direction

# Physics properties
settings.mass = 1.0
settings.use_multiply_size_mass = True  # Mass = size * mass
settings.brownian_factor = 0.1     # Random motion
settings.drag_factor = 0.05        # Air resistance
settings.damping = 0.1             # Velocity damping

# Gravity/forces
settings.effector_weights.gravity = 1.0
settings.effector_weights.all = 1.0
```

**Complete Example - Fountain:**
```python
import bpy

# Create emitter (small sphere at base)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 0))
emitter = bpy.context.active_object
emitter.name = "Fountain"

# Particle system
psys_mod = emitter.modifiers.new("Particles", 'PARTICLE_SYSTEM')
settings = emitter.particle_systems[-1].settings

# Emission
settings.count = 2000
settings.frame_start = 1
settings.frame_end = 250
settings.lifetime = 100
settings.emit_from = 'VOLUME'

# Physics - upward spray
settings.physics_type = 'NEWTON'
settings.normal_factor = 5.0      # Strong upward velocity
settings.factor_random = 0.3
settings.mass = 0.1
settings.use_multiply_size_mass = False
settings.drag_factor = 0.1

# Gravity
settings.effector_weights.gravity = 1.0

# Render
settings.particle_size = 0.02
settings.size_random = 0.5
```

### Keyed Physics

Animated paths between keyframes:

```python
settings.physics_type = 'KEYED'

# Add key targets
key1 = settings.keys.new()
key1.object = target_obj1
key1.system = 0  # Particle system index on target
key1.time = 0.0

key2 = settings.keys.new()
key2.object = target_obj2
key2.system = 0
key2.time = 50.0

# Timing
settings.keyed_timing = 1.0  # 100% of lifetime between keys
```

**Use Case:** Magic trails, controlled swarms, animated effects

### Boids Physics

Flocking behavior (birds, fish, insects):

```python
settings.physics_type = 'BOIDS'

# Boid settings
boids = settings.boids

# Brain rules
boids.states[0].rule_fuzzy = 0.5

# Separate rule (avoid crowding)
sep_rule = boids.states[0].rules.new(type='SEPARATE')
sep_rule.distance = 1.0

# Flock rule (stay together)
flock_rule = boids.states[0].rules.new(type='FLOCK')
flock_rule.distance = 5.0

# Avoid rule (obstacle avoidance)
avoid_rule = boids.states[0].rules.new(type='AVOID')
avoid_rule.fear_factor = 2.0

# Movement
boids.air_speed_max = 5.0
boids.air_speed_min = 1.0
boids.air_acc_max = 2.0
```

**Use Case:** Birds, fish schools, insect swarms

### Fluid Physics

Particles behave as liquid (deprecated - use Mantaflow):

```python
settings.physics_type = 'FLUID'

# Fluid properties
fluid = settings.fluid
fluid.spring_force = 0.0
fluid.stiffness_viscosity = 1.0
fluid.buoyancy = 0.0
fluid.fluid_radius = 1.0
```

**Note:** Deprecated in Blender 2.82+. Use Mantaflow fluid system instead (see FLUID_SIMULATION_GUIDE.md).

---

## Particle Instancing

Render objects on particles for complex effects with minimal memory.

### Object Instancing

```python
# Create instance object (shared by all particles)
bpy.ops.mesh.primitive_cube_add(size=0.1)
instance_obj = bpy.context.active_object
instance_obj.name = "Instance"

# Configure particle rendering
settings.render_type = 'OBJECT'
settings.instance_object = instance_obj

# Size/rotation
settings.particle_size = 0.1
settings.size_random = 0.5
settings.use_rotation_instance = True
settings.use_scale_instance = True

# Rotation settings
settings.angular_velocity_mode = 'VELOCITY'
settings.angular_velocity_factor = 0.1
settings.use_dynamic_rotation = True
```

**Complete Example - Falling Leaves:**
```python
import bpy

# Create leaf instance (flattened cube)
bpy.ops.mesh.primitive_cube_add(size=1.0)
leaf = bpy.context.active_object
leaf.name = "Leaf"
leaf.scale = (0.05, 0.1, 0.001)  # Flat leaf shape

# Create emitter (elevated plane)
vertices = [(-5,-5,5), (5,-5,5), (5,5,5), (-5,5,5)]
faces = [[0,1,2,3]]
mesh = bpy.data.meshes.new("Emitter")
mesh.from_pydata(vertices, [], faces)
mesh.update()
emitter = bpy.data.objects.new("LeafEmitter", mesh)
bpy.context.scene.collection.objects.link(emitter)

# Particle system
psys_mod = emitter.modifiers.new("Particles", 'PARTICLE_SYSTEM')
settings = emitter.particle_systems[-1].settings

# Emission
settings.count = 500
settings.frame_start = 1
settings.frame_end = 250
settings.lifetime = 200
settings.emit_from = 'FACE'

# Physics - slow falling with turbulence
settings.physics_type = 'NEWTON'
settings.normal_factor = -0.5  # Slight downward start
settings.factor_random = 0.2
settings.mass = 0.01
settings.drag_factor = 0.5  # High drag for slow fall
settings.brownian_factor = 2.0  # Tumbling motion

# Gravity
settings.effector_weights.gravity = 0.3  # Reduced gravity

# Instancing
settings.render_type = 'OBJECT'
settings.instance_object = leaf
settings.particle_size = 1.0
settings.size_random = 0.3
settings.use_rotation_instance = True
settings.use_scale_instance = True
settings.angular_velocity_mode = 'VELOCITY'
settings.angular_velocity_factor = 0.5
```

### Collection Instancing

Instance random objects from collection:

```python
# Create collection with multiple objects
collection = bpy.data.collections.new("Instances")
bpy.context.scene.collection.children.link(collection)

# Add objects to collection
for i in range(5):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1)
    obj = bpy.context.active_object
    obj.name = f"Instance_{i}"
    collection.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)

# Configure particle rendering
settings.render_type = 'COLLECTION'
settings.instance_collection = collection
settings.use_collection_pick_random = True
settings.use_whole_collection = True
settings.use_collection_count = False
```

**Use Case:** Debris (different shapes), forest (tree variety), asteroids

### Geometry Nodes Integration

Modern approach - use Geometry Nodes instead of particle instancing:

```python
# Create geometry nodes modifier
gn_mod = emitter.modifiers.new("GeometryNodes", 'NODES')

# Create node tree
node_tree = bpy.data.node_groups.new("ParticleInstancing", 'GeometryNodeTree')
gn_mod.node_group = node_tree

# Add nodes (Distribute Points on Faces + Instance on Points)
input_node = node_tree.nodes.new('NodeGroupInput')
output_node = node_tree.nodes.new('NodeGroupOutput')
distribute = node_tree.nodes.new('GeometryNodeDistributePointsOnFaces')
instance = node_tree.nodes.new('GeometryNodeInstanceOnPoints')

# Link nodes
node_tree.links.new(input_node.outputs[0], distribute.inputs[0])
node_tree.links.new(distribute.outputs[0], instance.inputs[0])
node_tree.links.new(instance.outputs[0], output_node.inputs[0])

# Configure
distribute.inputs['Density'].default_value = 100.0
instance.inputs['Instance'].default_value = instance_obj
```

**Advantages:**
- Real-time viewport updates
- More control (scale, rotation, selection)
- Better performance
- Non-destructive workflow

---

## Force Fields

### Wind Force

```python
# Create empty for force field
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, -5, 0))
wind = bpy.context.active_object
wind.name = "Wind"

# Configure wind
wind.field.type = 'WIND'
wind.field.strength = 5.0
wind.field.flow = 1.0        # Laminar flow
wind.field.noise = 0.5       # Turbulence
wind.field.seed = 42

# Falloff
wind.field.use_max_distance = True
wind.field.distance_max = 10.0
wind.field.falloff_type = 'SPHERE'
wind.field.falloff_power = 2.0

# Particle system must be affected
settings.effector_weights.wind = 1.0
```

### Turbulence Force

```python
# Create turbulence
bpy.ops.object.empty_add(type='PLAIN_AXES')
turbulence = bpy.context.active_object
turbulence.name = "Turbulence"

turbulence.field.type = 'TURBULENCE'
turbulence.field.strength = 3.0
turbulence.field.size = 2.0  # Noise scale
turbulence.field.flow = 0.5
turbulence.field.seed = 123

# Particle response
settings.effector_weights.turbulence = 1.0
```

### Vortex Force

```python
# Create vortex (spiral motion)
bpy.ops.object.empty_add(type='SINGLE_ARROW', location=(0, 0, 2))
vortex = bpy.context.active_object
vortex.name = "Vortex"

vortex.field.type = 'VORTEX'
vortex.field.strength = 10.0
vortex.field.flow = 1.0
vortex.field.inflow = 0.5  # Inward pull

settings.effector_weights.vortex = 1.0
```

### Force Field Combination

```python
# Multiple forces for complex behavior
winds = []
for i in range(3):
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    wind = bpy.context.active_object
    wind.name = f"Wind_{i}"
    wind.location = (i*5 - 5, 0, 0)
    wind.field.type = 'WIND'
    wind.field.strength = 5.0 + i
    wind.field.noise = 0.5
    winds.append(wind)

# Global weights (affects all forces)
settings.effector_weights.gravity = 0.5
settings.effector_weights.all = 1.0
settings.effector_weights.wind = 0.8
settings.effector_weights.turbulence = 1.2
```

---

## Collision Detection

### Object Collision

```python
# Create collision object
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -1))
ground = bpy.context.active_object
ground.name = "Ground"

# Enable collision
ground.collision.use = True
ground.collision.damping = 0.5       # Energy loss (0-1)
ground.collision.friction = 0.5      # Surface friction
ground.collision.permeability = 0.0  # 0=solid, 1=ghost
ground.collision.stickiness = 0.0    # Particle sticking
ground.collision.use_particle_kill = False  # Kill on collision

# Particle system collision response
settings.collision_collection = None  # Use all collision objects
```

### Collision Groups

```python
# Create collision group
coll_group = bpy.data.collections.new("Colliders")
bpy.context.scene.collection.children.link(coll_group)

# Add collision objects
for obj in collision_objects:
    obj.collision.use = True
    coll_group.objects.link(obj)

# Limit particle system to this group
settings.collision_collection = coll_group
```

### Particle Death on Collision

```python
# Kill particles on impact
ground.collision.use_particle_kill = True

# Alternative: Trigger event on collision
# (Requires Python script in particle system)
```

### Collision Performance

```python
# Optimize collision detection
ground.collision.damping_factor = 0.1  # Lower = more bouncy
ground.collision.random_damping = 0.0  # Consistent bounces
ground.collision.friction_factor = 0.5
ground.collision.random_friction = 0.0

# Reduce collision quality if needed
settings.collision_collection = small_collection  # Fewer objects
```

---

## Caching and Baking

### Understanding Particle Cache

Blender stores particle simulation results in cache for playback performance. Cache can be:
- **Memory Cache:** Stored in RAM (fast, lost on close)
- **Disk Cache:** Stored as files (persistent, slower)

### HTTP Bridge Limitation

**CRITICAL:** Baking cannot be triggered via HTTP Bridge. Operators fail.

```python
# ❌ FAILS in HTTP Bridge
bpy.ops.ptcache.bake_all()
bpy.ops.ptcache.free_bake_all()
```

**Workaround:** Configure via HTTP Bridge, bake manually in UI.

### Cache Configuration

```python
# Access point cache
pcache = emitter.particle_systems[-1].point_cache

# Cache settings
pcache.frame_start = 1
pcache.frame_end = 250
pcache.frame_step = 1  # Cache every N frames

# Disk cache location
pcache.use_disk_cache = True
pcache.use_library_path = False
pcache.filepath = "//cache/particles/"  # Relative to .blend file

# Cache name
pcache.name = "ParticleCache_001"
```

### Manual Baking Workflow

**Step 1: Configure via HTTP Bridge**
```python
import requests

code = """
import bpy

# Setup particle system
emitter = bpy.data.objects['Emitter']
settings = emitter.particle_systems[-1].settings
settings.count = 10000
settings.frame_start = 1
settings.frame_end = 250

# Configure cache
pcache = emitter.particle_systems[-1].point_cache
pcache.frame_start = 1
pcache.frame_end = 250
pcache.use_disk_cache = True
pcache.filepath = "//cache/particles/"
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Step 2: Bake in Blender UI**
1. Open Blender
2. Select emitter object
3. Physics Properties > Particle System > Cache
4. Click "Bake All Dynamics"
5. Wait for bake completion

**Step 3: Verify via HTTP Bridge**
```python
code = """
import bpy
pcache = bpy.data.objects['Emitter'].particle_systems[-1].point_cache
print(f"Baked: {pcache.is_baked}")
print(f"Frames: {pcache.info}")
"""
```

### Cache Management

```python
# Check cache status
pcache = emitter.particle_systems[-1].point_cache
is_baked = pcache.is_baked
is_outdated = pcache.is_outdated
frame_range = (pcache.frame_start, pcache.frame_end)

# Free cache (via UI only)
# bpy.ops.ptcache.free_bake_all()  # Operator - fails in HTTP Bridge

# Delete cache files manually
import os
cache_dir = bpy.path.abspath(pcache.filepath)
if os.path.exists(cache_dir):
    for file in os.listdir(cache_dir):
        os.remove(os.path.join(cache_dir, file))
```

---

## Performance Optimization

### Emission Optimization

```python
# Reduce particle count
settings.count = 1000  # Start low, increase if needed

# Limit emission timeframe
settings.frame_start = 1
settings.frame_end = 50  # Short emission burst vs continuous

# Use distribution efficiently
settings.use_even_distribution = True  # Faster than random
settings.emit_from = 'FACE'  # Faster than VOLUME for meshes
```

### Physics Optimization

```python
# Simplify physics
settings.physics_type = 'NEWTON'  # Simpler than BOIDS
settings.integrator = 'MIDPOINT'  # Faster than 'VERLET'
settings.timestep = 0.04  # Larger timestep = faster (less accurate)

# Reduce forces
settings.effector_weights.gravity = 1.0
settings.effector_weights.all = 0.5  # Reduce all other forces by 50%

# Disable unnecessary features
settings.use_rotations = False  # If rotation not visible
settings.use_dynamic_rotation = False
```

### Collision Optimization

```python
# Limit collision objects
collision_group = bpy.data.collections.new("MinimalColliders")
settings.collision_collection = collision_group

# Simplify collision geometry
# Use proxy objects (low-poly) for collision
for obj in collision_objects:
    obj.collision.use = True
    obj.display_type = 'WIRE'  # Hide visual complexity
```

### Viewport Display

```python
# Reduce viewport particles
settings.display_percentage = 50  # Show 50% in viewport
settings.display_method = 'DOT'  # Fastest display

# Child particles (render-time only)
settings.child_type = 'SIMPLE'
settings.rendered_child_count = 100
settings.child_nbr = 10  # Viewport children
```

### Render Optimization

```python
# Particle size
settings.particle_size = 0.01  # Smaller = fewer pixels

# Instancing vs paths
settings.render_type = 'OBJECT'  # Instancing faster than HALO

# Limit render children
settings.rendered_child_count = 100  # vs viewport child_nbr

# Motion blur
settings.use_motion_blur = False  # If not needed
```

---

## Render Settings

### Render Types

**HALO (Billboard):**
```python
settings.render_type = 'HALO'
settings.particle_size = 0.05
settings.halo.size = 0.05
settings.halo.hardness = 50
settings.halo.add = 0.1  # Additive blending
```

**PATH (Trails):**
```python
settings.render_type = 'PATH'
settings.path_start = 0.0  # Trail start (0=birth, 1=death)
settings.path_end = 1.0
settings.trail_count = 10  # Number of trail segments

# Material for path
path_material = bpy.data.materials.new("TrailMat")
path_material.use_nodes = True
settings.material_slot = path_material.name
```

**OBJECT (Instancing):**
```python
settings.render_type = 'OBJECT'
settings.instance_object = instance_obj
settings.particle_size = 0.1
settings.use_rotation_instance = True
settings.use_scale_instance = True
```

**COLLECTION:**
```python
settings.render_type = 'COLLECTION'
settings.instance_collection = collection
settings.use_collection_pick_random = True
```

### Material Assignment

```python
# Create material
mat = bpy.data.materials.new("ParticleMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes.get("Principled BSDF")
bsdf.inputs['Base Color'].default_value = (1, 0.5, 0, 1)
bsdf.inputs['Emission'].default_value = (1, 0.8, 0, 1)
bsdf.inputs['Emission Strength'].default_value = 2.0

# Assign to emitter (particles inherit)
if emitter.data.materials:
    emitter.data.materials[0] = mat
else:
    emitter.data.materials.append(mat)
```

### Particle Color

```python
# Use vertex colors for particle color
vcol_layer = emitter.data.vertex_colors.new(name="ParticleColor")
for i, data in enumerate(vcol_layer.data):
    # Set color per vertex/face
    data.color = (1.0, 0.5, 0.0, 1.0)  # RGBA

# Material setup (Attribute node)
nodes = mat.node_tree.nodes
attr_node = nodes.new('ShaderNodeAttribute')
attr_node.attribute_name = "ParticleColor"
mat.node_tree.links.new(attr_node.outputs['Color'], bsdf.inputs['Base Color'])
```

---

## Advanced Techniques

### Hair Particle System

```python
# Hair particles (grass, fur)
settings.type = 'HAIR'
settings.count = 10000
settings.hair_length = 0.5
settings.use_advanced_hair = True

# Hair dynamics (requires baking)
settings.use_hair_dynamics = True
settings.hair_dynamics.vertex_group_mass = "Mass"

# Render
settings.render_type = 'PATH'
settings.child_type = 'INTERPOLATED'
settings.child_nbr = 10
settings.rendered_child_count = 100
```

### Dynamic Paint Integration

```python
# Use particle system as dynamic paint brush
# Create canvas object
bpy.ops.mesh.primitive_plane_add(size=10)
canvas = bpy.context.active_object

# Add dynamic paint modifier
dp_mod = canvas.modifiers.new("DynamicPaint", 'DYNAMIC_PAINT')
dp_mod.ui_type = 'CANVAS'
canvas_settings = dp_mod.canvas_settings

# Create surface
surface = canvas_settings.canvas_surfaces.active

# Configure emitter as brush
emitter_dp = emitter.modifiers.new("DynamicPaintBrush", 'DYNAMIC_PAINT')
emitter_dp.ui_type = 'BRUSH'
brush_settings = emitter_dp.brush_settings
brush_settings.particle_system = emitter.particle_systems[-1]
```

### Texture Influence

```python
# Use texture to control emission density
tex = bpy.data.textures.new("EmissionTex", 'IMAGE')
tex.image = bpy.data.images.load("/path/to/texture.png")

# Add texture slot (legacy system)
tex_slot = settings.texture_slots.add()
tex_slot.texture = tex
tex_slot.texture_coords = 'UV'
tex_slot.use_map_density = True
tex_slot.density_factor = 1.0
```

### Particle Info Node (Shader)

```python
# Access particle data in shader
mat = bpy.data.materials.new("ParticleInfoMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes

# Particle Info node
pinfo = nodes.new('ShaderNodeParticleInfo')

# Use particle age for color gradient
colorramp = nodes.new('ShaderNodeValToRGB')
mat.node_tree.links.new(pinfo.outputs['Age'], colorramp.inputs['Fac'])
mat.node_tree.links.new(colorramp.outputs['Color'], nodes['Principled BSDF'].inputs['Base Color'])

# Color ramp (young particles = white, old = black)
colorramp.color_ramp.elements[0].color = (1, 1, 1, 1)
colorramp.color_ramp.elements[1].color = (0, 0, 0, 1)
```

---

## Troubleshooting

### Issue: Particles Not Appearing

**Symptoms:**
- Viewport shows emitter but no particles
- Render is empty

**Diagnosis:**
```python
code = """
import bpy
emitter = bpy.data.objects['Emitter']
psys = emitter.particle_systems[-1]
settings = psys.settings

print(f"Count: {settings.count}")
print(f"Start: {settings.frame_start}, End: {settings.frame_end}")
print(f"Lifetime: {settings.lifetime}")
print(f"Current frame: {bpy.context.scene.frame_current}")
print(f"Active particles: {len([p for p in psys.particles if p.alive_state == 'ALIVE'])}")
"""
```

**Solutions:**
1. **Timeline not advanced:**
   ```python
   bpy.context.scene.frame_set(settings.frame_start + 10)
   ```

2. **Emission frame range wrong:**
   ```python
   settings.frame_start = 1
   settings.frame_end = 250
   ```

3. **Lifetime too short:**
   ```python
   settings.lifetime = 100  # Increase
   ```

4. **Display percentage low:**
   ```python
   settings.display_percentage = 100
   ```

### Issue: Particles Falling Through Floor

**Symptoms:**
- Particles pass through collision objects
- No collision response

**Solutions:**
```python
# Enable collision on floor
floor.collision.use = True
floor.collision.damping = 0.5

# Verify particle system collision enabled
settings.collision_collection = None  # Use all collision objects

# Check collision group
if settings.collision_collection:
    print(f"Collision group: {settings.collision_collection.name}")
    print(f"Objects: {[o.name for o in settings.collision_collection.objects]}")

# Increase timestep quality
settings.timestep = 0.02  # Smaller = more accurate
```

### Issue: Slow Viewport Performance

**Symptoms:**
- Lag when scrubbing timeline
- Viewport FPS drops

**Solutions:**
```python
# Reduce viewport display
settings.display_percentage = 25  # Show 25% of particles
settings.display_method = 'DOT'  # Simplest display

# Limit viewport children
settings.child_nbr = 5  # Reduce from default 10

# Simplify physics
settings.timestep = 0.04  # Larger timestep
settings.integrator = 'MIDPOINT'  # Faster

# Bake simulation
# (Must be done in UI - see Caching section)
```

### Issue: Instancing Not Working

**Symptoms:**
- OBJECT render type shows no objects
- Only points visible

**Solutions:**
```python
# Verify instance object exists
if settings.instance_object:
    print(f"Instance: {settings.instance_object.name}")
else:
    print("ERROR: No instance object set")
    settings.instance_object = bpy.data.objects['InstanceObj']

# Check render type
settings.render_type = 'OBJECT'

# Verify particle size
settings.particle_size = 0.1  # Must be > 0

# Enable scale/rotation
settings.use_scale_instance = True
settings.use_rotation_instance = True
```

### Issue: Force Fields Not Affecting Particles

**Symptoms:**
- Wind/turbulence has no effect
- Particles ignore forces

**Solutions:**
```python
# Enable effector weights
settings.effector_weights.all = 1.0
settings.effector_weights.gravity = 1.0
settings.effector_weights.wind = 1.0
settings.effector_weights.turbulence = 1.0

# Check force field setup
for obj in bpy.data.objects:
    if obj.field:
        print(f"{obj.name}: {obj.field.type}, strength={obj.field.strength}")

# Verify force field in range
wind_obj.field.use_max_distance = True
wind_obj.field.distance_max = 20.0  # Increase range

# Check physics type
settings.physics_type = 'NEWTON'  # Must be physics-enabled type
```

### Issue: Baking Fails

**Symptoms:**
- Cache shows as unbaked
- Bake operation completes but no cache files

**Solutions:**
1. **HTTP Bridge Limitation:**
   - Cannot bake via HTTP Bridge
   - Must use Blender UI (see Caching section)

2. **Cache path invalid:**
   ```python
   pcache = emitter.particle_systems[-1].point_cache
   pcache.use_disk_cache = True
   pcache.filepath = "//cache/"  # Must be relative or absolute valid path

   # Verify path
   import os
   abs_path = bpy.path.abspath(pcache.filepath)
   print(f"Cache path: {abs_path}")
   os.makedirs(abs_path, exist_ok=True)
   ```

3. **Frame range mismatch:**
   ```python
   pcache.frame_start = 1
   pcache.frame_end = 250
   # Must match scene timeline
   bpy.context.scene.frame_start = 1
   bpy.context.scene.frame_end = 250
   ```

---

## Complete Production Example

**Sparks from Welding:**

```python
import requests

code = """
import bpy

# Create weld point (small sphere)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0, 0, 1))
weld_point = bpy.context.active_object
weld_point.name = "WeldPoint"

# Particle system - sparks
psys_mod = weld_point.modifiers.new("Sparks", 'PARTICLE_SYSTEM')
settings = weld_point.particle_systems[-1].settings

# Emission - burst
settings.count = 500
settings.frame_start = 10
settings.frame_end = 11  # Single frame burst
settings.lifetime = 30
settings.lifetime_random = 0.5
settings.emit_from = 'VOLUME'

# Physics - explosive outward
settings.physics_type = 'NEWTON'
settings.normal_factor = 0.0
settings.factor_random = 5.0  # Random directions
settings.mass = 0.001
settings.drag_factor = 0.3  # Air resistance
settings.damping = 0.1

# Gravity
settings.effector_weights.gravity = 2.0  # Strong gravity

# Render - glowing trails
settings.render_type = 'PATH'
settings.path_start = 0.0
settings.path_end = 1.0
settings.trail_count = 5
settings.particle_size = 0.005

# Material - emission
mat = bpy.data.materials.new("SparkMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes['Principled BSDF']
bsdf.inputs['Emission'].default_value = (1.0, 0.6, 0.2, 1.0)  # Orange
bsdf.inputs['Emission Strength'].default_value = 10.0

weld_point.data.materials.append(mat)

# Ground collision
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.collision.use = True
ground.collision.damping = 0.8  # Sparks lose energy on bounce
ground.collision.friction = 0.5

print("Sparks created - advance timeline to frame 10+")
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
print(response.json())
```

**Expected Result:**
- Frame 10: Burst of 500 sparks from weld point
- Sparks fly outward in random directions
- Gravity pulls sparks down
- Sparks bounce off ground with energy loss
- Orange glowing trails visible in render
- Duration: ~30 frames before all sparks die

---

**End of Advanced Particle Systems Reference**

For fluid simulation, see: FLUID_SIMULATION_GUIDE.md
For rigid/soft body, see: RIGID_SOFT_BODY.md
For skill overview, see: ../SKILL.md
