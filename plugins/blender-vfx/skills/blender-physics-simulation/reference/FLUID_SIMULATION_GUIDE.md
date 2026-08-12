# Fluid Simulation Guide (Mantaflow)

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Skill:** blender-physics-simulation
**Prerequisites:** Blender 4.5.0+, official Blender MCP

---

## Table of Contents

1. [Overview](#overview)
2. [Baking Limitations](#baking-limitations)
3. [Mantaflow Architecture](#mantaflow-architecture)
4. [Domain Setup](#domain-setup)
5. [Liquid Simulations](#liquid-simulations)
6. [Smoke Simulations](#smoke-simulations)
7. [Fire Simulations](#fire-simulations)
8. [Effector Objects](#effector-objects)
9. [Adaptive Domains](#adaptive-domains)
10. [Baking Workflows](#baking-workflows)
11. [Cache Management](#cache-management)
12. [Render Optimization](#render-optimization)
13. [Troubleshooting](#troubleshooting)
14. [Production Examples](#production-examples)

---

## Overview

Blender's Mantaflow system (introduced in 2.82) provides unified fluid simulation for:
- **Liquid:** Water, oil, lava
- **Gas:** Smoke, steam, fog
- **Fire:** Flames, explosions

**Key Components:**
- **Domain:** Container that defines simulation volume
- **Flow Objects:** Emit or absorb fluid/smoke
- **Effector Objects:** Obstacles, collision objects, guides

**Critical Difference from Legacy:**
- Mantaflow replaces old "Smoke" and "Fluid" systems
- Unified modifier type: `FLUID`
- Requires baking before playback/render

---

## Baking Limitations

### CRITICAL: Baking Restriction

**Cannot bake via a scripted call - these are long-running, blocking operators:**
```python
# ❌ ALL require interactive Blender (blocking, frame-stepped simulation)
bpy.ops.fluid.bake_all()
bpy.ops.fluid.free_all()
bpy.ops.fluid.bake_data()
bpy.ops.fluid.bake_mesh()
```

**The official Blender MCP can:**
- Create domain and flow objects
- Configure all fluid settings
- Set resolution, viscosity, diffusion
- Configure cache paths
- Verify bake status

**The official Blender MCP cannot (practically):**
- Trigger a full bake and wait for it to finish within a single tool call
- Free baked cache mid-bake
- Pause/resume baking

### Recommended Workflow

**Step 1: Configure via the official Blender MCP**
```python
code = """
import bpy

# Setup domain, flows, effectors
# Configure all settings
# Set cache path
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Step 2: Bake in Blender UI**
1. Open Blender
2. Select domain object
3. Physics Properties > Fluid > Bake
4. Click "Bake All" or specific data types
5. Wait for completion

**Step 3: Verify via the official Blender MCP**
```python
code = """
import bpy
domain = bpy.data.objects['Domain']
settings = domain.modifiers['Fluid'].domain_settings
print(f"Baked: {settings.cache_data_format}")
print(f"Frames: {settings.cache_frame_start} - {settings.cache_frame_end}")
"""
```

---

## Mantaflow Architecture

### Data Flow

```
Flow Object (Emitter)
        ↓
    Domain (Simulation Container)
        ↓
    Cache Files (Baked Data)
        ↓
    Render (Volume/Mesh)
```

### Fluid Types

**GAS (Smoke/Fire):**
- Buoyant, rises with temperature
- Dissipates over time
- Volumetric rendering

**LIQUID:**
- Falls with gravity
- Preserves volume
- Mesh rendering (optional particle system)

### Simulation Steps

1. **Emit:** Flow objects add fluid/smoke to domain
2. **Advect:** Move fluid based on velocity
3. **Forces:** Apply gravity, buoyancy, wind
4. **Viscosity:** Resistance to flow (liquid only)
5. **Diffusion:** Spread density/temperature (gas only)
6. **Mesh:** Generate surface mesh (liquid only)
7. **Cache:** Write data to disk

---

## Domain Setup

### Creating Domain

```python
import bpy

# Create cube for domain
bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 2))
domain_obj = bpy.context.active_object
domain_obj.name = "Domain"

# Add fluid modifier
fluid_mod = domain_obj.modifiers.new("Fluid", 'FLUID')
fluid_mod.fluid_type = 'DOMAIN'

# Access domain settings
domain_settings = fluid_mod.domain_settings
```

### Domain Type: GAS (Smoke/Fire)

```python
# Configure for smoke/fire
domain_settings.domain_type = 'GAS'

# Resolution (quality)
domain_settings.resolution_max = 128  # 32-512 typical range
domain_settings.use_noise = False     # High-res noise (slower)
domain_settings.noise_scale = 2       # If use_noise=True

# Time scale
domain_settings.time_scale = 1.0      # 1.0 = realtime, 0.5 = slow-mo

# Gravity
domain_settings.gravity = (0, 0, -9.81)

# Viscosity (resistance)
domain_settings.viscosity_base = 1e-6  # Very low for smoke
```

**Resolution Guidelines:**
- **Preview:** 32-64 (fast, low quality)
- **Production:** 128-256 (balanced)
- **Hero Shot:** 384-512 (slow, high quality)

### Domain Type: LIQUID

```python
# Configure for liquid
domain_settings.domain_type = 'LIQUID'

# Resolution
domain_settings.resolution_max = 100
domain_settings.use_mesh = True      # Generate surface mesh
domain_settings.mesh_scale = 2       # Mesh detail

# Viscosity (water = 1e-6, honey = 1e-2)
domain_settings.viscosity_base = 1e-6
domain_settings.viscosity_exponent = 6

# Diffusion
domain_settings.use_diffusion = True
domain_settings.diffusion_base = 1e-6

# Gravity
domain_settings.gravity = (0, 0, -9.81)

# Particles (splash, foam, bubbles)
domain_settings.use_spray_particles = True
domain_settings.use_foam_particles = True
domain_settings.use_bubble_particles = True
```

### Border Collisions

```python
# Domain boundaries
domain_settings.use_collision_border_front = True
domain_settings.use_collision_border_back = True
domain_settings.use_collision_border_right = True
domain_settings.use_collision_border_left = True
domain_settings.use_collision_border_top = False    # Open top for smoke
domain_settings.use_collision_border_bottom = True
```

---

## Liquid Simulations

### Basic Water Pour

```python
import bpy

# Domain (large container)
bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 2))
domain = bpy.context.active_object
domain.name = "WaterDomain"

fluid_mod = domain.modifiers.new("Fluid", 'FLUID')
fluid_mod.fluid_type = 'DOMAIN'
settings = fluid_mod.domain_settings

settings.domain_type = 'LIQUID'
settings.resolution_max = 100
settings.use_mesh = True
settings.mesh_scale = 2

# Flow object (water source)
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 4))
inflow = bpy.context.active_object
inflow.name = "WaterInflow"

inflow_mod = inflow.modifiers.new("FluidFlow", 'FLUID')
inflow_mod.fluid_type = 'FLOW'
flow_settings = inflow_mod.flow_settings

flow_settings.flow_type = 'LIQUID'
flow_settings.flow_behavior = 'INFLOW'  # Continuous emission
flow_settings.use_inflow = True
flow_settings.velocity_normal = 0.5  # Downward velocity
flow_settings.velocity_coord = (0, 0, -1)  # Direction

# Collision floor
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"

floor_mod = floor.modifiers.new("FluidEffector", 'FLUID')
floor_mod.fluid_type = 'EFFECTOR'
effector_settings = floor_mod.effector_settings
effector_settings.effector_type = 'COLLISION'
effector_settings.use_plane_init = True

# Cache configuration
settings.cache_frame_start = 1
settings.cache_frame_end = 250
settings.cache_directory = "//cache/liquid/"
```

**Next Step:** Bake in Blender UI (Physics > Fluid > Bake All)

### Viscosity Examples

**Water:**
```python
domain_settings.viscosity_base = 1.0
domain_settings.viscosity_exponent = -6  # 1e-6
```

**Oil:**
```python
domain_settings.viscosity_base = 5.0
domain_settings.viscosity_exponent = -5  # 5e-5
```

**Honey:**
```python
domain_settings.viscosity_base = 2.0
domain_settings.viscosity_exponent = -2  # 2e-2
```

**Lava:**
```python
domain_settings.viscosity_base = 1.0
domain_settings.viscosity_exponent = -1  # 0.1
```

### Liquid Particles

```python
# Enable particles (splash, foam, bubbles)
domain_settings.use_spray_particles = True
domain_settings.spray_potential_min = 1.0
domain_settings.spray_potential_max = 5.0

domain_settings.use_foam_particles = True
domain_settings.foam_potential_min = 1.0
domain_settings.foam_potential_max = 3.0

domain_settings.use_bubble_particles = True
domain_settings.bubble_buoyancy = 1.0
domain_settings.bubble_drag = 0.5

# Particle sampling
domain_settings.particle_radius = 1.0
domain_settings.particle_number = 2  # Particles per cell
domain_settings.particle_max = 0  # 0 = unlimited
```

### Mesh Generation

```python
# Surface mesh quality
domain_settings.use_mesh = True
domain_settings.mesh_scale = 2  # Higher = more detail (slower)

# Smoothing
domain_settings.mesh_smoothness_pos = 1  # Positive curvature
domain_settings.mesh_smoothness_neg = 1  # Negative curvature

# Concavity (detail in recesses)
domain_settings.mesh_concave_upper = 3.5
domain_settings.mesh_concave_lower = 0.4
```

---

## Smoke Simulations

### Basic Smoke Column

```python
import bpy

# Domain
bpy.ops.mesh.primitive_cube_add(size=6, location=(0, 0, 3))
domain = bpy.context.active_object
domain.name = "SmokeDomain"

fluid_mod = domain.modifiers.new("Fluid", 'FLUID')
fluid_mod.fluid_type = 'DOMAIN'
settings = fluid_mod.domain_settings

settings.domain_type = 'GAS'
settings.resolution_max = 128

# Smoke behavior
settings.alpha = 1.0  # Buoyancy (how much smoke rises)
settings.beta = 0.0   # Temperature difference (heat rise)
settings.vorticity = 0.1  # Turbulence

# Dissolve
settings.use_dissolve_smoke = True
settings.dissolve_speed = 5  # Frames to dissolve

# Flow object (smoke emitter)
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.5, location=(0, 0, 0.5))
emitter = bpy.context.active_object
emitter.name = "SmokeEmitter"

emitter_mod = emitter.modifiers.new("FluidFlow", 'FLUID')
emitter_mod.fluid_type = 'FLOW'
flow_settings = emitter_mod.flow_settings

flow_settings.flow_type = 'SMOKE'
flow_settings.flow_behavior = 'INFLOW'
flow_settings.smoke_color = (0.7, 0.7, 0.7)  # Gray smoke
flow_settings.volume_density = 1.0
flow_settings.velocity_normal = 1.0  # Upward velocity

# Cache
settings.cache_directory = "//cache/smoke/"
settings.cache_frame_start = 1
settings.cache_frame_end = 250
```

### Smoke Color and Density

```python
# Colored smoke (fire source)
flow_settings.smoke_color = (0.05, 0.05, 0.05)  # Dark smoke
flow_settings.volume_density = 2.0  # Thick smoke

# Light smoke (steam)
flow_settings.smoke_color = (0.9, 0.9, 0.9)  # Light gray
flow_settings.volume_density = 0.3  # Thin smoke
```

### Temperature and Buoyancy

```python
# Hot rising smoke
flow_settings.temperature = 2.0  # Heat value
domain_settings.alpha = 1.0  # Density buoyancy
domain_settings.beta = 1.0   # Temperature buoyancy

# Cold falling smoke (dry ice effect)
flow_settings.temperature = -2.0
domain_settings.alpha = -1.0
domain_settings.beta = 0.0
```

### Turbulence (Noise)

```python
# High-res noise for detail
domain_settings.use_noise = True
domain_settings.noise_scale = 2  # Noise resolution multiplier
domain_settings.noise_strength = 1.0
domain_settings.noise_pos_scale = 2.0  # Spatial scale
domain_settings.noise_time_anim = 0.1  # Temporal variation
```

---

## Fire Simulations

### Basic Fire

```python
import bpy

# Domain (same as smoke)
bpy.ops.mesh.primitive_cube_add(size=6, location=(0, 0, 3))
domain = bpy.context.active_object
domain.name = "FireDomain"

fluid_mod = domain.modifiers.new("Fluid", 'FLUID')
fluid_mod.fluid_type = 'DOMAIN'
settings = fluid_mod.domain_settings

settings.domain_type = 'GAS'
settings.resolution_max = 128

# Fire-specific settings
settings.use_dissolve_smoke = True
settings.dissolve_speed = 10
settings.vorticity = 0.2
settings.alpha = 1.0
settings.beta = 2.0  # Temperature buoyancy

# Emitter
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.2, location=(0, 0, 0.5))
emitter = bpy.context.active_object
emitter.name = "FireEmitter"

emitter_mod = emitter.modifiers.new("FluidFlow", 'FLUID')
emitter_mod.fluid_type = 'FLOW'
flow_settings = emitter_mod.flow_settings

# Fire flow type
flow_settings.flow_type = 'FIRE'
flow_settings.flow_behavior = 'INFLOW'
flow_settings.fuel_amount = 1.0  # Fuel for combustion
flow_settings.smoke_color = (0.1, 0.1, 0.1)  # Smoke from fire
flow_settings.volume_density = 0.0  # No initial smoke
flow_settings.temperature = 3.0  # Heat

# Cache
settings.cache_directory = "//cache/fire/"
```

### Fire and Smoke

Fire automatically generates smoke as it burns:

```python
# Control smoke generation from fire
domain_settings.burning_rate = 0.75  # How fast fuel burns
domain_settings.flame_smoke = 1.0    # Smoke amount from flame
domain_settings.flame_vorticity = 0.5  # Flame turbulence
domain_settings.flame_max_temp = 3.0   # Maximum temperature
domain_settings.flame_ignition = 1.25  # Ignition temperature
```

### Explosion Effect

```python
# Large burst of fire
flow_settings.flow_type = 'FIRE'
flow_settings.flow_behavior = 'GEOMETRY'  # Emit from volume, then stop
flow_settings.fuel_amount = 5.0  # High fuel
flow_settings.temperature = 10.0  # Extreme heat

# Domain settings for explosion
domain_settings.vorticity = 0.5  # High turbulence
domain_settings.beta = 3.0  # Strong temperature rise
domain_settings.burning_rate = 1.5  # Fast burn

# Animate emitter (grow then shrink)
emitter.scale = (0.1, 0.1, 0.1)
emitter.keyframe_insert(data_path="scale", frame=1)
emitter.scale = (2.0, 2.0, 2.0)
emitter.keyframe_insert(data_path="scale", frame=5)
emitter.scale = (0.1, 0.1, 0.1)
emitter.keyframe_insert(data_path="scale", frame=10)
```

---

## Effector Objects

### Collision Objects

```python
# Static obstacle (sphere in smoke path)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 2))
obstacle = bpy.context.active_object
obstacle.name = "Obstacle"

effector_mod = obstacle.modifiers.new("FluidEffector", 'FLUID')
effector_mod.fluid_type = 'EFFECTOR'
effector_settings = effector_mod.effector_settings

effector_settings.effector_type = 'COLLISION'
effector_settings.surface_distance = 0.5  # Collision margin
effector_settings.velocity_factor = 1.0   # Velocity influence
```

### Animated Obstacles

```python
# Moving obstacle (stirs smoke)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2, 0, 2))
moving_obstacle = bpy.context.active_object
moving_obstacle.name = "MovingObstacle"

# Animate position
moving_obstacle.location = (-2, 0, 2)
moving_obstacle.keyframe_insert(data_path="location", frame=1)
moving_obstacle.location = (2, 0, 2)
moving_obstacle.keyframe_insert(data_path="location", frame=100)

# Effector
effector_mod = moving_obstacle.modifiers.new("FluidEffector", 'FLUID')
effector_mod.fluid_type = 'EFFECTOR'
effector_settings = effector_mod.effector_settings

effector_settings.effector_type = 'COLLISION'
effector_settings.is_planar = False
effector_settings.use_plane_init = False

# Velocity influence (stirring)
effector_settings.velocity_factor = 2.0  # Strong influence
```

### Guide Objects

```python
# Force field to guide smoke
bpy.ops.mesh.primitive_curve.add(location=(0, 0, 0))
guide = bpy.context.active_object
guide.name = "SmokeGuide"

guide_mod = guide.modifiers.new("FluidEffector", 'FLUID')
guide_mod.fluid_type = 'EFFECTOR'
guide_settings = guide_mod.effector_settings

guide_settings.effector_type = 'GUIDE'
guide_settings.velocity_factor = 5.0  # Guide strength
guide_settings.guide_mode = 'OVERRIDE'  # or 'ADDITIVE'
```

---

## Adaptive Domains

Adaptive domains automatically resize to contain active fluid, improving performance.

### Enable Adaptive Domain

```python
# Gas domain (smoke/fire)
domain_settings.use_adaptive_domain = True
domain_settings.additional_res = 3  # Extra cells around fluid
domain_settings.adapt_margin = 4    # Margin in cells
domain_settings.adapt_threshold = 0.02  # Density threshold for resize
```

**Benefits:**
- Smaller effective resolution (faster)
- Auto-focuses detail on active areas
- Reduces memory usage

**Limitations:**
- Gas only (not liquid)
- Domain mesh animates (consider for rendering)

---

## Baking Workflows

### Cache Types

Blender fluid simulations have multiple cache types:

1. **Data:** Core simulation (density, velocity, temperature)
2. **Mesh:** Liquid surface mesh
3. **Particles:** Spray, foam, bubbles
4. **Noise:** High-res detail (gas only)
5. **Guide:** Velocity guide cache

### Cache Settings (official Blender MCP)

```python
# Configure before manual bake
domain_settings.cache_frame_start = 1
domain_settings.cache_frame_end = 250
domain_settings.cache_frame_offset = 0

# Cache directory
domain_settings.cache_directory = "//cache/fluid/"
domain_settings.cache_type = 'MODULAR'  # Separate files per frame

# Export format
domain_settings.cache_data_format = 'OPENVDB'  # or 'UNI' (legacy)

# Resumable baking
domain_settings.cache_resumable = True
```

### Baking in Blender UI

**Manual Bake Steps:**

1. **Configure via the official Blender MCP:**
   ```python
   # Set all domain/flow/effector settings
   # Configure cache path
   # Set frame range
   ```

2. **Open Blender UI**

3. **Select Domain Object**

4. **Physics Properties > Fluid**

5. **Bake Section:**
   - **Bake All:** Bakes all enabled cache types
   - **Bake Data:** Core simulation only
   - **Bake Mesh:** Liquid mesh only
   - **Bake Particles:** Spray/foam/bubbles only
   - **Bake Noise:** High-res detail only

6. **Click "Bake All"**
   - Progress bar shows completion
   - Can be paused/resumed if cache_resumable=True
   - Cache files written to cache_directory

7. **Verify:**
   - Timeline scrubs smoothly
   - Cache info shows frames cached
   - Viewport displays fluid correctly

### Verify Bake Status (official Blender MCP)

```python
code = """
import bpy

domain = bpy.data.objects['Domain']
settings = domain.modifiers['Fluid'].domain_settings

print(f"Cache directory: {settings.cache_directory}")
print(f"Frame range: {settings.cache_frame_start} - {settings.cache_frame_end}")
print(f"Data format: {settings.cache_data_format}")

# Check if baked
print(f"Has cache: {settings.has_cache_baked_data}")

# Cache file info
import os
cache_path = bpy.path.abspath(settings.cache_directory)
if os.path.exists(cache_path):
    files = os.listdir(cache_path)
    print(f"Cache files: {len(files)}")
else:
    print("Cache directory does not exist")
"""
```

---

## Cache Management

### Cache File Structure

```
//cache/fluid/
├── config/
│   └── config_0001.uni
├── data/
│   ├── fluid_data_0001.vdb
│   ├── fluid_data_0002.vdb
│   └── ...
├── mesh/
│   ├── mesh_0001.vdb
│   └── ...
└── particles/
    ├── particles_0001.uni
    └── ...
```

### Free Cache (Manual)

`bpy.ops.fluid.free_all()` is a blocking operator - run it in interactive Blender rather than scripting it:

```python
# Run interactively, not via a scripted call
bpy.ops.fluid.free_all()
```

**Workaround - Delete Files:**
```python
import os
import shutil

cache_path = bpy.path.abspath(domain_settings.cache_directory)
if os.path.exists(cache_path):
    shutil.rmtree(cache_path)
    os.makedirs(cache_path)
    print(f"Cache cleared: {cache_path}")
```

### Cache Size Optimization

```python
# Reduce resolution
domain_settings.resolution_max = 64  # Lower = smaller cache

# Reduce frame range
domain_settings.cache_frame_start = 50  # Don't cache early frames
domain_settings.cache_frame_end = 100

# Disable unnecessary features
domain_settings.use_mesh = False  # If only need particles
domain_settings.use_spray_particles = False
domain_settings.use_noise = False
```

---

## Render Optimization

### Volume Rendering (Smoke/Fire)

```python
# Create material for domain
mat = bpy.data.materials.new("SmokeMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes.clear()

# Volume output
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (400, 0)

# Principled Volume shader
principled_vol = nodes.new('ShaderNodeVolumePrincipled')
principled_vol.location = (0, 0)

# Connect
mat.node_tree.links.new(principled_vol.outputs['Volume'], output.inputs['Volume'])

# Assign to domain
if domain.data.materials:
    domain.data.materials[0] = mat
else:
    domain.data.materials.append(mat)

# Configure volume properties
principled_vol.inputs['Density'].default_value = 1.0
principled_vol.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1.0)

# Fire properties
principled_vol.inputs['Blackbody Intensity'].default_value = 1.0
principled_vol.inputs['Temperature'].default_value = 1000.0  # Kelvin
```

### Mesh Rendering (Liquid)

```python
# Domain generates mesh automatically if use_mesh=True
# Render mesh like normal object

# Create material
mat = bpy.data.materials.new("WaterMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = nodes.get('Principled BSDF')

# Glass-like water
bsdf.inputs['Base Color'].default_value = (0.1, 0.3, 0.5, 1.0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.05
bsdf.inputs['Transmission'].default_value = 0.95
bsdf.inputs['IOR'].default_value = 1.33  # Water IOR

# Assign
domain.data.materials.append(mat)
```

### Render Settings

```python
# Cycles render engine (required for volumes)
bpy.context.scene.render.engine = 'CYCLES'

# Volume sampling
bpy.context.scene.cycles.volume_step_rate = 1.0  # Lower = faster, less accurate
bpy.context.scene.cycles.volume_max_steps = 1024  # Max steps through volume

# Render resolution
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.resolution_percentage = 100

# Samples (denoising recommended)
bpy.context.scene.cycles.samples = 128
bpy.context.scene.cycles.use_denoising = True
```

---

## Troubleshooting

### Issue: Bake Button Grayed Out

**Cause:** Cache directory invalid or domain not selected

**Solutions:**
```python
# Verify domain type
print(f"Fluid type: {fluid_mod.fluid_type}")  # Should be 'DOMAIN'

# Set cache directory
domain_settings.cache_directory = "//cache/fluid/"

# Verify frame range
domain_settings.cache_frame_start = 1
domain_settings.cache_frame_end = 250

# Ensure timeline matches
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 250
```

### Issue: Smoke Not Visible in Viewport

**Cause:** Volume display disabled or density too low

**Solutions:**
```python
# Enable volume display
bpy.context.space_data.shading.type = 'SOLID'
bpy.context.space_data.shading.show_xray = False

# Increase density
flow_settings.volume_density = 2.0

# Verify emission
flow_settings.flow_behavior = 'INFLOW'
flow_settings.use_inflow = True

# Check timeline
bpy.context.scene.frame_set(10)  # Advance timeline
```

### Issue: Liquid Not Generating Mesh

**Cause:** Mesh generation disabled or resolution too low

**Solutions:**
```python
# Enable mesh
domain_settings.use_mesh = True

# Increase resolution
domain_settings.resolution_max = 100  # Minimum for visible mesh

# Mesh scale
domain_settings.mesh_scale = 2  # Higher = more detail

# Verify liquid in domain
flow_settings.flow_type = 'LIQUID'
flow_settings.flow_behavior = 'INFLOW'
```

### Issue: Fire Not Burning

**Cause:** Fuel amount too low or temperature insufficient

**Solutions:**
```python
# Increase fuel
flow_settings.fuel_amount = 2.0

# Increase temperature
flow_settings.temperature = 3.0

# Domain burning rate
domain_settings.burning_rate = 1.0
domain_settings.flame_ignition = 1.25

# Verify fire type
flow_settings.flow_type = 'FIRE'  # Not 'SMOKE'
```

### Issue: Simulation Explodes/Artifacts

**Cause:** Resolution too low, timestep too large, or velocity too high

**Solutions:**
```python
# Increase resolution
domain_settings.resolution_max = 128  # Higher = more stable

# Reduce timestep
domain_settings.cfl_condition = 2.0  # Lower = more steps (slower, stable)

# Reduce velocity
flow_settings.velocity_normal = 0.5  # Lower emission velocity

# Border collisions
domain_settings.use_collision_border_front = True
domain_settings.use_collision_border_back = True
# etc.
```

### Issue: Slow Bake Performance

**Cause:** High resolution, noise enabled, or complex mesh

**Solutions:**
```python
# Reduce resolution
domain_settings.resolution_max = 64  # Faster bake

# Disable noise
domain_settings.use_noise = False

# Disable mesh (liquid)
domain_settings.use_mesh = False  # Use particles only

# Disable particles
domain_settings.use_spray_particles = False
domain_settings.use_foam_particles = False

# Adaptive domain (gas only)
domain_settings.use_adaptive_domain = True
```

---

## Production Examples

### Example 1: Steam from Coffee Cup

```python
import bpy

# Domain (small, above cup)
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 1.5))
domain = bpy.context.active_object
domain.name = "SteamDomain"

fluid_mod = domain.modifiers.new("Fluid", 'FLUID')
fluid_mod.fluid_type = 'DOMAIN'
settings = fluid_mod.domain_settings

settings.domain_type = 'GAS'
settings.resolution_max = 64  # Low res for steam
settings.alpha = 0.5  # Light buoyancy
settings.beta = 0.5   # Temperature rise
settings.use_dissolve_smoke = True
settings.dissolve_speed = 20  # Quick dissolve

# Borders - open top
settings.use_collision_border_top = False
settings.use_collision_border_bottom = True

# Emitter (small circle at cup surface)
bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.05, location=(0, 0, 0.5))
emitter = bpy.context.active_object
emitter.name = "SteamEmitter"

emitter_mod = emitter.modifiers.new("FluidFlow", 'FLUID')
emitter_mod.fluid_type = 'FLOW'
flow_settings = emitter_mod.flow_settings

flow_settings.flow_type = 'SMOKE'
flow_settings.flow_behavior = 'INFLOW'
flow_settings.smoke_color = (0.95, 0.95, 0.95)  # Light gray
flow_settings.volume_density = 0.2  # Thin steam
flow_settings.temperature = 1.0  # Warm
flow_settings.velocity_normal = 0.5  # Gentle rise

# Cache
settings.cache_directory = "//cache/steam/"
settings.cache_frame_start = 1
settings.cache_frame_end = 120

print("Steam configured - bake in Blender UI")
```

### Example 2: Waterfall

```python
import bpy

# Domain (tall, narrow)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 3))
domain = bpy.context.active_object
domain.name = "WaterfallDomain"
domain.scale = (2, 2, 6)  # Tall domain

fluid_mod = domain.modifiers.new("Fluid", 'FLUID')
fluid_mod.fluid_type = 'DOMAIN'
settings = fluid_mod.domain_settings

settings.domain_type = 'LIQUID'
settings.resolution_max = 150
settings.use_mesh = True
settings.mesh_scale = 3  # Detailed mesh

# Viscosity (water)
settings.viscosity_base = 1.0
settings.viscosity_exponent = -6

# Particles
settings.use_spray_particles = True
settings.use_foam_particles = True

# Flow object (narrow at top)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 5.5))
inflow = bpy.context.active_object
inflow.name = "WaterfallSource"
inflow.scale = (0.5, 0.5, 0.2)

inflow_mod = inflow.modifiers.new("FluidFlow", 'FLUID')
inflow_mod.fluid_type = 'FLOW'
flow_settings = inflow_mod.flow_settings

flow_settings.flow_type = 'LIQUID'
flow_settings.flow_behavior = 'INFLOW'
flow_settings.use_inflow = True
flow_settings.velocity_normal = 5.0  # Strong downward flow
flow_settings.velocity_coord = (0, 0, -1)

# Collision rocks
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(0, 0, 2))
rock1 = bpy.context.active_object
rock1.name = "Rock1"

rock1_mod = rock1.modifiers.new("FluidEffector", 'FLUID')
rock1_mod.fluid_type = 'EFFECTOR'
rock1_mod.effector_settings.effector_type = 'COLLISION'

# Pool at bottom
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.2))
pool = bpy.context.active_object
pool.name = "Pool"
pool.scale = (3, 3, 0.2)

pool_mod = pool.modifiers.new("FluidEffector", 'FLUID')
pool_mod.fluid_type = 'EFFECTOR'
pool_mod.effector_settings.effector_type = 'COLLISION'

# Cache
settings.cache_directory = "//cache/waterfall/"
settings.cache_frame_start = 1
settings.cache_frame_end = 250

print("Waterfall configured - bake in Blender UI")
```

### Example 3: Candle Flame

```python
import bpy

# Domain (small, above candle)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1))
domain = bpy.context.active_object
domain.name = "FlameDomain"
domain.scale = (0.5, 0.5, 1.5)

fluid_mod = domain.modifiers.new("Fluid", 'FLUID')
fluid_mod.fluid_type = 'DOMAIN'
settings = fluid_mod.domain_settings

settings.domain_type = 'GAS'
settings.resolution_max = 96
settings.alpha = 1.0
settings.beta = 2.0
settings.vorticity = 0.1
settings.use_dissolve_smoke = True
settings.dissolve_speed = 5

# Fire settings
settings.burning_rate = 1.0
settings.flame_smoke = 0.5  # Moderate smoke from flame

# Emitter (small sphere at wick)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0, 0, 0.3))
emitter = bpy.context.active_object
emitter.name = "Wick"

emitter_mod = emitter.modifiers.new("FluidFlow", 'FLUID')
emitter_mod.fluid_type = 'FLOW'
flow_settings = emitter_mod.flow_settings

flow_settings.flow_type = 'FIRE'
flow_settings.flow_behavior = 'INFLOW'
flow_settings.fuel_amount = 0.5  # Gentle flame
flow_settings.smoke_color = (0.05, 0.05, 0.05)  # Dark smoke
flow_settings.temperature = 2.0

# Cache
settings.cache_directory = "//cache/candle/"
settings.cache_frame_start = 1
settings.cache_frame_end = 240

print("Candle flame configured - bake in Blender UI")
```

---

**End of Fluid Simulation Guide**

For particle systems, see: ADVANCED_PARTICLE_SYSTEMS.md
For rigid/soft body, see: RIGID_SOFT_BODY.md
For skill overview, see: ../SKILL.md
