---
name: blender-physics-simulation
description: Physics simulations including particles, fluids (Mantaflow), rigid/soft body, and cloth in Blender. Use for physics, particles, fluid simulations, or when user mentions "physics," "particle," "fluid," "rigid body," "soft body," "cloth," "fire," "smoke," or "hair."
allowed-tools: Read,Write
---

# Blender Physics Simulation Skill

**Version:** 2.0.0
**Last Updated:** 2026-06-10
**Dependencies:** Blender 5.1+

---

## API Stability (5.1+)

Physics system is stable across 4.x → 5.1. All core APIs work via direct data access:

```python
import bpy

# Particle system — direct API
psys = obj.modifiers.new("ParticleSystem", 'PARTICLE_SYSTEM')
settings = obj.particle_systems[-1].settings

# Rigid body — direct property access
obj.rigid_body.type = 'ACTIVE'
obj.rigid_body.mass = 1.0

# Cloth — direct modifier settings
cloth_mod = obj.modifiers.new("Cloth", 'CLOTH')
cloth_mod.settings.mass = 0.3
```

**Note on fluid baking:** Mantaflow baking cannot be triggered from Python — configure all settings via script, then bake in the Blender UI (Physics Properties > Fluid > Bake All).

---

## QUICK START

### Basic Particle System

```python
import bpy

# Create emitter plane
vertices = [(-1,-1,0), (1,-1,0), (1,1,0), (-1,1,0)]
faces = [[0,1,2,3]]
mesh = bpy.data.meshes.new("Emitter")
mesh.from_pydata(vertices, [], faces)
mesh.update()
emitter = bpy.data.objects.new("ParticleEmitter", mesh)
bpy.context.scene.collection.objects.link(emitter)

# Add particle system
psys_mod = emitter.modifiers.new("ParticleSystem", 'PARTICLE_SYSTEM')
settings = emitter.particle_systems[-1].settings

# Configure
settings.count = 1000
settings.frame_start = 1
settings.frame_end = 250
settings.lifetime = 50
settings.physics_type = 'NEWTON'
settings.normal_factor = 1.0
settings.factor_random = 0.5

print(f"Particle system created: {settings.count} particles")
```

---

## STANDARD WORKFLOWS

### Workflow 1: Rain / Snow Particles

**Use When:** Precipitation effects, environmental particles

```python
import bpy

# Elevated emitter for downward rain
vertices = [(-10,-10,5), (10,-10,5), (10,10,5), (-10,10,5)]
faces = [[0,1,2,3]]
mesh = bpy.data.meshes.new("RainEmitter")
mesh.from_pydata(vertices, [], faces)
mesh.update()
emitter = bpy.data.objects.new("RainEmitter", mesh)
bpy.context.scene.collection.objects.link(emitter)

psys_mod = emitter.modifiers.new("Rain", 'PARTICLE_SYSTEM')
settings = emitter.particle_systems[-1].settings

settings.count = 5000
settings.physics_type = 'NEWTON'
settings.effector_weights.gravity = 1.0
settings.normal_factor = -2.0   # Downward velocity
settings.particle_size = 0.01

# Collision ground
ground_mesh = bpy.data.meshes.new("Ground")
ground_mesh.from_pydata([(-10,-10,0),(10,-10,0),(10,10,0),(-10,10,0)], [], [[0,1,2,3]])
ground_mesh.update()
ground = bpy.data.objects.new("Ground", ground_mesh)
bpy.context.scene.collection.objects.link(ground)
ground.collision.use = True
ground.collision.damping = 0.5

print("Rain system configured")
```

---

### Workflow 2: Rigid Body Stack

**Use When:** Destruction, falling objects, physics animation

```python
import bpy

# Enable rigid body world
scene = bpy.context.scene
if not scene.rigidbody_world:
    bpy.ops.rigidbody.world_add()  # Requires scene context

rb_world = scene.rigidbody_world
rb_world.steps_per_second = 60
rb_world.solver_iterations = 10

# Create stack of cubes (simplified example)
import math
for i in range(5):
    mesh = bpy.data.meshes.new(f"Cube_{i}")
    verts = [(-0.5,-0.5,-0.5),(0.5,-0.5,-0.5),(0.5,0.5,-0.5),(-0.5,0.5,-0.5),
             (-0.5,-0.5,0.5),(0.5,-0.5,0.5),(0.5,0.5,0.5),(-0.5,0.5,0.5)]
    faces = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[0,3,7,4],[1,2,6,5]]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    cube = bpy.data.objects.new(f"Cube_{i}", mesh)
    bpy.context.scene.collection.objects.link(cube)
    cube.location.z = i * 1.1   # Stack them

    bpy.context.view_layer.objects.active = cube
    bpy.ops.rigidbody.object_add()
    cube.rigid_body.type = 'ACTIVE'
    cube.rigid_body.mass = 1.0
    cube.rigid_body.friction = 0.5
    cube.rigid_body.restitution = 0.3

print("Rigid body stack created")
```

---

### Workflow 3: Cloth Draping

**Use When:** Fabric, flags, character clothing

```python
import bpy
import math

# Create subdivided plane (20x20 grid)
subdivisions = 20
verts = []
faces = []
for y in range(subdivisions + 1):
    for x in range(subdivisions + 1):
        verts.append((x / subdivisions - 0.5, y / subdivisions - 0.5, 0))

for y in range(subdivisions):
    for x in range(subdivisions):
        i = y * (subdivisions + 1) + x
        faces.append([i, i+1, i+subdivisions+2, i+subdivisions+1])

mesh = bpy.data.meshes.new("Cloth")
mesh.from_pydata(verts, [], faces)
mesh.update()
cloth_obj = bpy.data.objects.new("Cloth", mesh)
bpy.context.scene.collection.objects.link(cloth_obj)
cloth_obj.location.z = 2.0   # Start above ground

# Add cloth modifier
cloth_mod = cloth_obj.modifiers.new("Cloth", 'CLOTH')
cloth_mod.settings.quality = 5
cloth_mod.settings.mass = 0.3
cloth_mod.settings.tension_stiffness = 15
cloth_mod.settings.bending_stiffness = 0.5
cloth_mod.collision_settings.collision_quality = 5
cloth_mod.collision_settings.distance_min = 0.015

# Pin top edge
vgroup = cloth_obj.vertex_groups.new(name="Pin")
top_verts = [i for i in range(subdivisions + 1)]  # top row
vgroup.add(top_verts, 1.0, 'ADD')
cloth_mod.settings.vertex_group_mass = "Pin"

print(f"Cloth created: {len(verts)} vertices, pinned {len(top_verts)} top verts")
```

---

### Workflow 4: Fluid / Smoke (Mantaflow)

**Use When:** Liquid, smoke, fire effects

```python
import bpy

# Create domain container
domain_verts = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
domain_mesh = bpy.data.meshes.new("FluidDomain")
domain_mesh.from_pydata(domain_verts, [], [[0,1,2,3],[4,5,6,7]])
domain_mesh.update()
domain_obj = bpy.data.objects.new("FluidDomain", domain_mesh)
bpy.context.scene.collection.objects.link(domain_obj)

# Configure domain
fluid_domain = domain_obj.modifiers.new("Fluid", 'FLUID')
fluid_domain.fluid_type = 'DOMAIN'
fluid_domain.domain_settings.domain_type = 'GAS'   # or 'LIQUID'
fluid_domain.domain_settings.resolution_max = 64
fluid_domain.domain_settings.time_scale = 1.0

# Create emitter/flow object
emitter_mesh = bpy.data.meshes.new("Emitter")
emitter_mesh.from_pydata([(0,0,0)], [], [])
emitter_mesh.update()
emitter_obj = bpy.data.objects.new("SmokeEmitter", emitter_mesh)
bpy.context.scene.collection.objects.link(emitter_obj)

fluid_flow = emitter_obj.modifiers.new("FluidFlow", 'FLUID')
fluid_flow.fluid_type = 'FLOW'
fluid_flow.flow_settings.flow_type = 'SMOKE'   # or 'LIQUID', 'FIRE'
fluid_flow.flow_settings.smoke_color = (0.5, 0.5, 0.5)

print("Fluid domain and emitter configured.")
print("To bake: select domain > Physics Properties > Fluid > Bake All")
```

---

## ADVANCED TECHNIQUES

### Particle Instancing (Mesh on Particles)

```python
import bpy

# After setting up particle system:
settings = obj.particle_systems[-1].settings
settings.render_type = 'OBJECT'
settings.instance_object = instance_obj   # Your mesh object
settings.use_rotation_instance = True
settings.use_scale_instance = True
settings.particle_size = 0.1
settings.size_random = 0.5
```

### Force Fields

```python
import bpy

empty_mesh = bpy.data.meshes.new("ForceField")
force_obj = bpy.data.objects.new("Wind", empty_mesh)
bpy.context.scene.collection.objects.link(force_obj)

force_obj.field.type = 'WIND'       # or 'TURBULENCE', 'VORTEX'
force_obj.field.strength = 5.0
force_obj.field.flow = 1.0
force_obj.field.noise = 2.0
```

---

## TROUBLESHOOTING

### Particles Not Appearing

```python
import bpy

settings = obj.particle_systems[-1].settings
print(f"Count: {settings.count}, Start frame: {settings.frame_start}")

# Advance timeline to see particles
bpy.context.scene.frame_set(settings.frame_start + 10)
print(f"Active particles: {len(obj.particle_systems[-1].particles)}")
```

### Rigid Body Not Moving

```python
import bpy

# Check world is enabled
if bpy.context.scene.rigidbody_world:
    print(f"RB world enabled: {bpy.context.scene.rigidbody_world.enabled}")

# Check object types
for o in bpy.data.objects:
    if o.rigid_body:
        print(f"{o.name}: type={o.rigid_body.type}")
```

### Cloth Explodes

```python
import bpy

# Lower stiffness and increase collision quality
cloth_mod.settings.tension_stiffness = 10     # Reduce if exploding
cloth_mod.collision_settings.collision_quality = 8
cloth_mod.collision_settings.distance_min = 0.02

# Move cloth away from collision objects
cloth_obj.location.z += 0.5
```

---

## VALIDATION CHECKLIST

- [ ] Particle/physics settings configured
- [ ] Collision objects enabled (if needed)
- [ ] Timeline range covers simulation
- [ ] Rigid body world enabled for rigid/soft body sims
- [ ] For fluid/smoke: configure settings via script, bake in Blender UI

---

## VERSION HISTORY

**v2.0.0** (2026-06-10) - MCP migration
- Removed HTTP Bridge section and curl health-check
- Removed `import requests` / `requests.post()` wrappers
- Added `import bpy` to all code blocks
- Updated target: Blender 5.1+
- Removed absolute paths to blender-ai-compatibility
- Added rigid body world setup with bpy.ops (now valid with MCP context)

**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+
