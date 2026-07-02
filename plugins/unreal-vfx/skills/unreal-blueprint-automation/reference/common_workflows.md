# Common Blueprint Automation Workflows

**Version:** 1.0.0
**Created:** 2025-10-26

Copy-paste ready templates for common Blueprint automation tasks.

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

# Phase 2: Add Component
from unreal_mcp_server import get_unreal_connection
unreal_conn = get_unreal_connection()
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_SimpleProp",
    "component_type": "StaticMeshComponent",
    "component_name": "Mesh"
})

# Phase 3: Set Mesh
unreal_conn.send_command("set_static_mesh_properties", {
    "blueprint_name": "BP_SimpleProp",
    "component_name": "Mesh",
    "static_mesh": "/Engine/BasicShapes/Cube.Cube"  # Change to your mesh
})

# Phase 4: Compile
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

# Phase 2: Add Components
from unreal_mcp_server import get_unreal_connection
unreal_conn = get_unreal_connection()

# Add mesh
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_LitProp",
    "component_type": "StaticMeshComponent",
    "component_name": "BaseMesh"
})

# Add light
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_LitProp",
    "component_type": "PointLightComponent",
    "component_name": "Light"
})

# Phase 3: Configure
# Set mesh
unreal_conn.send_command("set_static_mesh_properties", {
    "blueprint_name": "BP_LitProp",
    "component_name": "BaseMesh",
    "static_mesh": "/Engine/BasicShapes/Sphere.Sphere"
})

# Set light intensity
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_LitProp",
    "component_name": "Light",
    "property_name": "Intensity",
    "property_value": "5000.0"
})

# Set light color (orange glow)
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_LitProp",
    "component_name": "Light",
    "property_name": "LightColor",
    "property_value": "[255, 128, 0, 255]"  # R, G, B, A
})

# Position light above mesh
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_LitProp",
    "component_name": "Light",
    "property_name": "RelativeLocation",
    "property_value": "[0.0, 0.0, 150.0]"
})

# Phase 4: Compile
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_LitProp')
unreal.KismetSystemLibrary.compile_blueprint(bp)
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

# Phase 2: Add Components
from unreal_mcp_server import get_unreal_connection
unreal_conn = get_unreal_connection()

# Mesh base
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_VFXProp",
    "component_type": "StaticMeshComponent",
    "component_name": "Base"
})

# Particle system
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_VFXProp",
    "component_type": "ParticleSystemComponent",
    "component_name": "VFX"
})

# Phase 3: Configure
# Set mesh
unreal_conn.send_command("set_static_mesh_properties", {
    "blueprint_name": "BP_VFXProp",
    "component_name": "Base",
    "static_mesh": "/Engine/BasicShapes/Cylinder.Cylinder"
})

# Position VFX above mesh
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_VFXProp",
    "component_name": "VFX",
    "property_name": "RelativeLocation",
    "property_value": "[0.0, 0.0, 200.0]"
})

# Set particle template (change to your particle system)
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_VFXProp",
    "component_name": "VFX",
    "property_name": "Template",
    "property_value": "/Engine/Tutorial/SubEditors/TutorialAssets/TutorialParticleSystem.TutorialParticleSystem"
})

# Phase 4: Compile
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_VFXProp')
unreal.KismetSystemLibrary.compile_blueprint(bp)
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

# Phase 2: Add Components
from unreal_mcp_server import get_unreal_connection
unreal_conn = get_unreal_connection()

# Box collision
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_TriggerVolume",
    "component_type": "BoxComponent",
    "component_name": "TriggerBox"
})

# Phase 3: Configure
# Set box size
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_TriggerVolume",
    "component_name": "TriggerBox",
    "property_name": "BoxExtent",
    "property_value": "[200.0, 200.0, 100.0]"  # X, Y, Z half-extents
})

# Enable overlap events
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_TriggerVolume",
    "component_name": "TriggerBox",
    "property_name": "bGenerateOverlapEvents",
    "property_value": "true"
})

# Phase 4: Compile
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_TriggerVolume')
unreal.KismetSystemLibrary.compile_blueprint(bp)
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

# Phase 2: Add All Components
from unreal_mcp_server import get_unreal_connection
unreal_conn = get_unreal_connection()

# Root mesh
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_ComplexActor",
    "component_type": "StaticMeshComponent",
    "component_name": "MainMesh"
})

# Collision
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_ComplexActor",
    "component_type": "SphereComponent",
    "component_name": "InteractionZone"
})

# Light
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_ComplexActor",
    "component_type": "PointLightComponent",
    "component_name": "MainLight"
})

# VFX
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_ComplexActor",
    "component_type": "ParticleSystemComponent",
    "component_name": "AmbientVFX"
})

# Audio
unreal_conn.send_command("add_component_to_blueprint", {
    "blueprint_name": "BP_ComplexActor",
    "component_type": "AudioComponent",
    "component_name": "AmbientSound"
})

# Phase 3: Configure Properties
# Mesh
unreal_conn.send_command("set_static_mesh_properties", {
    "blueprint_name": "BP_ComplexActor",
    "component_name": "MainMesh",
    "static_mesh": "/Engine/BasicShapes/Cube.Cube"
})

# Collision sphere
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_ComplexActor",
    "component_name": "InteractionZone",
    "property_name": "SphereRadius",
    "property_value": "300.0"
})

# Light
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_ComplexActor",
    "component_name": "MainLight",
    "property_name": "Intensity",
    "property_value": "3000.0"
})

unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_ComplexActor",
    "component_name": "MainLight",
    "property_name": "RelativeLocation",
    "property_value": "[0.0, 0.0, 200.0]"
})

# VFX
unreal_conn.send_command("set_component_property", {
    "blueprint_name": "BP_ComplexActor",
    "component_name": "AmbientVFX",
    "property_name": "RelativeLocation",
    "property_value": "[0.0, 0.0, 150.0]"
})

# Phase 4: Compile
import unreal
bp = unreal.load_asset('/Game/Blueprints/BP_ComplexActor')
unreal.KismetSystemLibrary.compile_blueprint(bp)
```

## Template 6: Blueprint Spawning Pattern

**Use Case:** Spawn Blueprint instance in level after creation

```python
# After Blueprint is compiled...

from unreal_mcp_server import get_unreal_connection
unreal_conn = get_unreal_connection()

# Spawn single instance
result = unreal_conn.send_command("spawn_blueprint_actor", {
    "blueprint_name": "BP_SimpleProp",
    "actor_name": "Prop_001",
    "location": [0, 0, 0],
    "rotation": [0, 0, 0]
})

# Spawn multiple instances (loop in Python, separate MCP calls)
positions = [
    [0, 0, 0],
    [500, 0, 0],
    [1000, 0, 0]
]

for i, pos in enumerate(positions):
    unreal_conn.send_command("spawn_blueprint_actor", {
        "blueprint_name": "BP_SimpleProp",
        "actor_name": f"Prop_{i:03d}",
        "location": pos,
        "rotation": [0, 0, 0]
    })
```

## Common Property Values

### Transform Properties

```python
# Location (Vector)
"property_name": "RelativeLocation"
"property_value": "[100.0, 200.0, 50.0]"  # X, Y, Z

# Rotation (Rotator - Pitch, Yaw, Roll in degrees)
"property_name": "RelativeRotation"
"property_value": "[0.0, 45.0, 0.0]"  # Pitch, Yaw, Roll

# Scale (Vector)
"property_name": "RelativeScale3D"
"property_value": "[2.0, 2.0, 2.0]"  # Uniform 2x scale
```

### Light Properties

```python
# Intensity
"property_name": "Intensity"
"property_value": "5000.0"  # Candelas

# Color (LinearColor - R, G, B, A in 0-255 range)
"property_name": "LightColor"
"property_value": "[255, 128, 64, 255]"  # Orange

# Attenuation Radius
"property_name": "AttenuationRadius"
"property_value": "1000.0"  # Unreal units

# Cast Shadows
"property_name": "CastShadows"
"property_value": "true"
```

### Collision Properties

```python
# Box Extent (half-size)
"property_name": "BoxExtent"
"property_value": "[100.0, 100.0, 50.0]"

# Sphere Radius
"property_name": "SphereRadius"
"property_value": "200.0"

# Capsule Radius/Height
"property_name": "CapsuleRadius"
"property_value": "50.0"

"property_name": "CapsuleHalfHeight"
"property_value": "100.0"

# Generate Overlap Events
"property_name": "bGenerateOverlapEvents"
"property_value": "true"
```

### Mesh Properties

```python
# Cast Shadow
"property_name": "CastShadow"
"property_value": "true"

# Receive Decals
"property_name": "bReceivesDecals"
"property_value": "true"

# Collision Preset
"property_name": "CollisionPreset"
"property_value": "BlockAll"  # Options: NoCollision, OverlapAll, BlockAll, etc.
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

Build up from simple → complex:
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

To find available properties for a component:

```python
import unreal

# Get component class
comp_class = unreal.PointLightComponent

# Get all properties
for prop in comp_class.get_editor_property_list():
    print(prop)
```

Check Blueprint API docs for detailed property info:
`<workspace>\UnrealEngine\guides\blueprints`

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
