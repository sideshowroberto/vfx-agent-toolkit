# Common Blueprint Automation Workflows

**Version:** 2.0.0
**Created:** 2025-10-26
**Last Updated:** 2026-07-06 (UE 5.8 native MCP migration)

Copy-paste ready templates for common Blueprint automation tasks.

**Calling convention:** Every Python block below runs inside the Unreal Editor via `mcp__ue58-mcp__execute_python_code(code=...)`. Each phase is a **separate** `execute_python_code` call so async validation can complete between phases (see `silent_execution_blueprints.md`).

## Template 1: Simple Actor with Static Mesh

**Use Case:** Basic prop, placeholder, static object

**Complete Workflow:**

```python
# Phase 1: Create Blueprint
import unreal
bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="BP_SimpleProp",
    package_path="/Game/Blueprints",
    asset_class=unreal.Blueprint,
    factory=unreal.BlueprintFactory()
)

# Phase 2: Add Component + Set Mesh (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_SimpleProp')
scs = bp.simple_construction_script
mesh_node = scs.create_node(unreal.StaticMeshComponent)
scs.add_node(mesh_node)
mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")  # Change to your mesh
mesh_node.component_template.set_static_mesh(mesh)
print("Mesh component added and configured")

# Phase 3: Compile (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_SimpleProp')
unreal.KismetSystemLibrary.compile_blueprint(bp)
# Silent Execution
```

**Time:** <1 second
**Result:** Blueprint with assigned mesh, ready to place in level

## Template 2: Lit Prop (Mesh + Light)

**Use Case:** Self-illuminated prop, lamp, glowing object

```python
# Phase 1: Create
import unreal
bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="BP_LitProp",
    package_path="/Game/Blueprints",
    asset_class=unreal.Blueprint,
    factory=unreal.BlueprintFactory()
)

# Phase 2: Add + Configure Components (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_LitProp')
scs = bp.simple_construction_script

# Add mesh
mesh_node = scs.create_node(unreal.StaticMeshComponent)
scs.add_node(mesh_node)
mesh = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
mesh_node.component_template.set_static_mesh(mesh)

# Add light
light_node = scs.create_node(unreal.PointLightComponent)
scs.add_node(light_node)
light = light_node.component_template

# Set light intensity
light.set_editor_property('intensity', 5000.0)

# Set light color (orange glow)
light.set_editor_property('light_color', unreal.Color(255, 128, 0, 255))  # R, G, B, A

# Position light above mesh
light.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 150.0))

print("Components added and configured")

# Phase 3: Compile (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_LitProp')
unreal.KismetSystemLibrary.compile_blueprint(bp)
# Silent Execution
```

## Template 3: VFX Prop (Mesh + Particle System)

**Use Case:** Torch, fire, smoke emitter, magic effect

```python
# Phase 1: Create
import unreal
bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="BP_VFXProp",
    package_path="/Game/Blueprints",
    asset_class=unreal.Blueprint,
    factory=unreal.BlueprintFactory()
)

# Phase 2: Add + Configure Components (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_VFXProp')
scs = bp.simple_construction_script

# Mesh base
mesh_node = scs.create_node(unreal.StaticMeshComponent)
scs.add_node(mesh_node)
mesh = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
mesh_node.component_template.set_static_mesh(mesh)

# Particle system
vfx_node = scs.create_node(unreal.ParticleSystemComponent)
scs.add_node(vfx_node)
vfx = vfx_node.component_template

# Position VFX above mesh
vfx.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 200.0))

# Set particle template (change to your particle system)
particle_asset = unreal.load_asset(
    "/Engine/Tutorial/SubEditors/TutorialAssets/TutorialParticleSystem.TutorialParticleSystem")
vfx.set_editor_property('template', particle_asset)

print("Components added and configured")

# Phase 3: Compile (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_VFXProp')
unreal.KismetSystemLibrary.compile_blueprint(bp)
# Silent Execution
```

## Template 4: Collision Trigger Volume

**Use Case:** Trigger zone, interaction area, proximity detector

```python
# Phase 1: Create
import unreal
bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="BP_TriggerVolume",
    package_path="/Game/Blueprints",
    asset_class=unreal.Blueprint,
    factory=unreal.BlueprintFactory()
)

# Phase 2: Add + Configure Component (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_TriggerVolume')
scs = bp.simple_construction_script

# Box collision
box_node = scs.create_node(unreal.BoxComponent)
scs.add_node(box_node)
box = box_node.component_template

# Set box size (X, Y, Z half-extents)
box.set_editor_property('box_extent', unreal.Vector(200.0, 200.0, 100.0))

# Enable overlap events
box.set_editor_property('generate_overlap_events', True)

print("Trigger box configured")

# Phase 3: Compile (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_TriggerVolume')
unreal.KismetSystemLibrary.compile_blueprint(bp)
# Silent Execution
```

## Template 5: Complex Multi-Component Actor

**Use Case:** Complete game object with mesh, light, VFX, and collision

```python
# Phase 1: Create
import unreal
bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="BP_ComplexActor",
    package_path="/Game/Blueprints",
    asset_class=unreal.Blueprint,
    factory=unreal.BlueprintFactory()
)

# Phase 2: Add All Components (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_ComplexActor')
scs = bp.simple_construction_script

# Root mesh
mesh_node = scs.create_node(unreal.StaticMeshComponent)
scs.add_node(mesh_node)

# Collision
sphere_node = scs.create_node(unreal.SphereComponent)
scs.add_node(sphere_node)

# Light
light_node = scs.create_node(unreal.PointLightComponent)
scs.add_node(light_node)

# VFX
vfx_node = scs.create_node(unreal.ParticleSystemComponent)
scs.add_node(vfx_node)

# Audio
audio_node = scs.create_node(unreal.AudioComponent)
scs.add_node(audio_node)

print("All components added")

# Phase 3: Configure Properties (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_ComplexActor')
scs = bp.simple_construction_script

for node in scs.get_all_nodes():
    comp = node.component_template
    if isinstance(comp, unreal.StaticMeshComponent):
        mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
        comp.set_static_mesh(mesh)
    elif isinstance(comp, unreal.SphereComponent):
        comp.set_editor_property('sphere_radius', 300.0)
    elif isinstance(comp, unreal.PointLightComponent):
        comp.set_editor_property('intensity', 3000.0)
        comp.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 200.0))
    elif isinstance(comp, unreal.ParticleSystemComponent):
        comp.set_editor_property('relative_location', unreal.Vector(0.0, 0.0, 150.0))

print("Properties configured")

# Phase 4: Compile (separate call)
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_ComplexActor')
unreal.KismetSystemLibrary.compile_blueprint(bp)
# Silent Execution
```

## Template 6: Blueprint Spawning Pattern

**Use Case:** Spawn Blueprint instance in level after creation

```python
# After Blueprint is compiled... (via execute_python_code)
import unreal

bp_class = unreal.load_class(None, "/Game/Blueprints/BP_SimpleProp.BP_SimpleProp_C")

# Spawn single instance
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    bp_class,
    unreal.Vector(0, 0, 0),
    unreal.Rotator(0, 0, 0)
)
actor.set_actor_label("Prop_001")

# Spawn multiple instances (single script is fine - spawning does not compile)
positions = [
    unreal.Vector(0, 0, 0),
    unreal.Vector(500, 0, 0),
    unreal.Vector(1000, 0, 0)
]

for i, pos in enumerate(positions):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        bp_class, pos, unreal.Rotator(0, 0, 0)
    )
    actor.set_actor_label(f"Prop_{i:03d}")
```

## VibeUE Toolset Alternative

When the VibeUE plugin is installed, component operations are also available as toolset services (no Python required):

```python
mcp__ue58-mcp__call_tool(
    toolset_name="VibeUE.BlueprintService",
    tool_name="add_component_to_blueprint",
    arguments={
        "blueprint_name": "BP_SimpleProp",
        "component_type": "StaticMeshComponent",
        "component_name": "Mesh"
    }
)
```

Discover available tools with `mcp__ue58-mcp__describe_toolset(toolset_name="VibeUE.BlueprintService")`.

## Common Property Values

Set properties on `node.component_template` via `set_editor_property()`. Property names are snake_case; values are native `unreal` types.

### Transform Properties

```python
# Location (Vector)
comp.set_editor_property('relative_location', unreal.Vector(100.0, 200.0, 50.0))  # X, Y, Z

# Rotation (Rotator - Pitch, Yaw, Roll in degrees)
comp.set_editor_property('relative_rotation', unreal.Rotator(0.0, 45.0, 0.0))

# Scale (Vector)
comp.set_editor_property('relative_scale3d', unreal.Vector(2.0, 2.0, 2.0))  # Uniform 2x scale
```

### Light Properties

```python
# Intensity (candelas)
comp.set_editor_property('intensity', 5000.0)

# Color (R, G, B, A in 0-255 range)
comp.set_editor_property('light_color', unreal.Color(255, 128, 64, 255))  # Orange

# Attenuation Radius (Unreal units)
comp.set_editor_property('attenuation_radius', 1000.0)

# Cast Shadows
comp.set_editor_property('cast_shadows', True)
```

### Collision Properties

```python
# Box Extent (half-size)
comp.set_editor_property('box_extent', unreal.Vector(100.0, 100.0, 50.0))

# Sphere Radius
comp.set_editor_property('sphere_radius', 200.0)

# Capsule Radius/Height
comp.set_editor_property('capsule_radius', 50.0)
comp.set_editor_property('capsule_half_height', 100.0)

# Generate Overlap Events
comp.set_editor_property('generate_overlap_events', True)
```

### Mesh Properties

```python
# Cast Shadow
comp.set_editor_property('cast_shadow', True)

# Receive Decals
comp.set_editor_property('receives_decals', True)

# Collision Preset (via collision profile name)
comp.set_collision_profile_name("BlockAll")  # Options: NoCollision, OverlapAll, BlockAll, etc.
```

## Workflow Tips

### 1. Test with Basic Shapes First

Always prototype with Engine basic shapes:
- `/Engine/BasicShapes/Cube.Cube`
- `/Engine/BasicShapes/Sphere.Sphere`
- `/Engine/BasicShapes/Cylinder.Cylinder`
- `/Engine/BasicShapes/Cone.Cone`

Replace with project assets after validation.

### 2. Incremental Complexity

Build up from simple to complex:
1. Single mesh only
2. Add one light
3. Add VFX/audio
4. Add collision
5. Add logic (later)

### 3. Component Naming Conventions

**Good:**
- `BaseMesh`, `MainMesh` (descriptive)
- `InteractionZone`, `DamageArea` (purpose-clear)
- `AmbientLight`, `FillLight` (role-specific)

**Avoid:**
- `Mesh1`, `Mesh2` (non-descriptive)
- `Component`, `Thing` (vague)

### 4. Property Discovery

To find available properties for a component, use the native MCP discovery tool:

```python
mcp__ue58-mcp__discover_python_class(class_name="PointLightComponent")
```

Or inside editor Python:

```python
import unreal

# List editor properties on an instance
comp = light_node.component_template
print(comp.get_editor_property('intensity'))  # Probe a known property
help(unreal.PointLightComponent)  # Full class reference
```

## Validation Checklist

After running workflow:

- [ ] Blueprint appears in Content Browser at expected path
- [ ] All components visible in Components panel (left side)
- [ ] Component hierarchy correct (parents/children)
- [ ] Properties set correctly in Details panel
- [ ] Blueprint compiles (green checkmark, no errors)
- [ ] Can place Blueprint in level
- [ ] Components visible in viewport
- [ ] Collision working (if applicable)

## Performance Notes

**Single Blueprint Creation:**
- Total time: <1 second
- Phases execute sequentially
- No user wait time between phases

**Batch Creation (10 Blueprints):**
- Estimate: ~10 seconds total
- Run phases in loops
- Consider parallel execution for large batches (advanced)

## Related Templates

**PCG Workflows:**
- `.claude/skills/unreal-pcg-automation/reference/complete_graph_template.md`

**Skill Documentation:**
- `.claude/skills/unreal-blueprint-automation/SKILL.md`

**Silent Execution Pattern:**
- `.claude/skills/unreal-blueprint-automation/reference/silent_execution_blueprints.md`
