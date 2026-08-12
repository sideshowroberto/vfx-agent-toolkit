# Blueprint Patterns - Unreal Engine 5.5 Python

**Document Version:** 1.0.0
**Target:** Unreal Engine 5.5+
**Last Updated:** 2025-10-25
**Python Version:** 3.11 (UE built-in)

---

## Overview

### Purpose

Deep dive into Blueprint class loading, spawning, and component access patterns in Unreal Engine Python API.

**Key Topics:**
- `_C` suffix explained
- Blueprint path resolution
- Blueprint vs plain actor trade-offs
- Component access patterns
- Common Blueprint types

---

## The `_C` Suffix Explained

### What is `_C`?

**Definition:** `_C` suffix indicates the **compiled Blueprint class** (C++ generated class)

**Unreal's Blueprint Naming:**
- **Blueprint Asset:** `BP_Actor` (the .uasset file)
- **Generated C++ Class:** `BP_Actor_C` (runtime class)

**Why Required:**
- `load_class()` needs the **compiled class**, not the asset
- Blueprint asset is editor-only
- `_C` class is what gets instantiated at runtime

---

### Visual Explanation

**Content Browser:**
```
/Game/Blueprints/
  +-- BP_Actor  (Blueprint asset - editor-only)
```

**Runtime:**
```cpp
// Generated C++ class (what Python sees)
class BP_Actor_C : public AActor {
    // Blueprint logic compiled to C++
};
```

**Python:**
```python
# [FAIL] WRONG: Asset path
bp = unreal.load_class(None, "/Game/Blueprints/BP_Actor")  # None returned

# [OK] CORRECT: Compiled class path
bp = unreal.load_class(None, "/Game/Blueprints/BP_Actor.BP_Actor_C")
```

---

### Common Mistakes

**Mistake 1: Forgetting `_C` Suffix**
```python
# [FAIL] Returns None
bp = unreal.load_class(None, "/Game/BP_Actor")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
# TypeError: 'NoneType' object is not callable
```

**Mistake 2: Wrong Case**
```python
# [FAIL] Case-sensitive
bp = unreal.load_class(None, "/Game/BP_Actor.bp_actor_c")  # None
```

**Mistake 3: Not Repeating Name**
```python
# [FAIL] Must repeat Blueprint name
bp = unreal.load_class(None, "/Game/BP_Actor.BP_Actor_C")  # [OK] Correct
bp = unreal.load_class(None, "/Game/BP_Actor_C")           # [FAIL] Wrong
```

---

## Blueprint Path Resolution

### Getting the Correct Path

**Method 1: Copy Reference (Recommended)**

1. Right-click Blueprint in Content Browser
2. Select **Copy Reference**
3. Paste result: `/Script/Engine.Blueprint'/Game/Path/BP_Name.BP_Name'`
4. Extract: `/Game/Path/BP_Name.BP_Name_C` (add `_C`)

**Example:**
```
Copied: /Script/Engine.Blueprint'/Game/Blueprints/Cameras/BP_Camera.BP_Camera'
Extract: /Game/Blueprints/Cameras/BP_Camera.BP_Camera_C
```

---

**Method 2: Manual Construction**

**Pattern:**
```
/Game/<folder>/<subfolder>/<BlueprintName>.<BlueprintName>_C
       ^ Path to folder    ^ Repeat name with _C
```

**Examples:**
```python
# Root of /Game
"/Game/BP_Actor.BP_Actor_C"

# In subfolder
"/Game/Blueprints/BP_Camera.BP_Camera_C"

# Deep nesting
"/Game/VFX/Cameras/CineCameras/BP_CineCamera.BP_CineCamera_C"
```

---

**Method 3: Load Asset First (Slower)**
```python
# Load Blueprint asset
bp_asset = unreal.load_asset("/Game/BP_Actor")

# Get generated class
bp_class = bp_asset.generated_class()

# Use class
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp_class, ...)
```

**When to Use:** Dynamic Blueprint loading (path unknown at code-time)

---

### Path Format Rules

**[OK] Correct:**
- Forward slashes: `/Game/BP_Actor.BP_Actor_C`
- Repeat name: `/Game/BP_Name.BP_Name_C`
- Case-sensitive: Match exact Blueprint name

**[FAIL] Wrong:**
- Backslashes: `\Game\BP_Actor.BP_Actor_C`
- No repeat: `/Game/BP_Actor_C`
- Wrong case: `/Game/bp_actor.bp_actor_c`
- No `_C`: `/Game/BP_Actor.BP_Actor`

---

## Blueprint vs Plain Actor

### Decision Matrix

| Feature | Blueprint Actor | Plain Actor |
|---------|----------------|-------------|
| **Component Setup** | Pre-configured [OK] | Limited (no `register_component`) [FAIL] |
| **Flexibility** | Fixed in Blueprint | Fully code-driven |
| **Setup Time** | Fast (spawn + access) | Slow (manual config) |
| **Requires Asset** | Yes (Blueprint file) | No (code-only) |
| **Team Sharing** | Easy (check in Blueprint) | Harder (Python script) |
| **Version Control** | Blueprint .uasset | Python .py |
| **Editor Visibility** | Visible in Content Browser | Not visible (code-only) |
| **Recommended For** | Component hierarchies | Simple actors |

---

### When to Use Blueprint Actor

**Use Cases:**
- Need complex component hierarchy (camera + ImagePlate + lights)
- Components must be attached (no `setup_attachment` in Python)
- Artists need to modify actor in editor
- Reusable asset across shots/levels
- Team collaboration (Blueprint easier to understand)

**Example:**
```python
# Spawn Blueprint with pre-configured components
bp = unreal.load_class(None, "/Game/BP_CameraRig.BP_CameraRig_C")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    bp, location=unreal.Vector(0, 0, 100)
)

# Components already attached and configured
camera = actor.get_components_by_class(unreal.CineCameraComponent)[0]
lights = actor.get_components_by_class(unreal.PointLightComponent)
# Ready to use, no additional setup
```

---

### When to Use Plain Actor

**Use Cases:**
- Simple actor with no components
- Properties set via code
- No component hierarchy needed
- Temporary/test actors

**Example:**
```python
# Spawn plain actor
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.Actor, location=unreal.Vector(0, 0, 0)
)

# Set properties
actor.set_actor_label("Test_Actor_001")
actor.set_actor_scale3d(unreal.Vector(2, 2, 2))
```

**Limitation:** Cannot add components effectively (no `register_component`)

---

## Component Access on Blueprint Actors

### Pattern 1: Single Component

**Use:** When Blueprint has one of a component type

```python
# Returns list (even if only one component!)
components = actor.get_components_by_class(unreal.CineCameraComponent)

if components:
    camera = components[0]  # Get first (and only) component
    camera.set_editor_property('current_focal_length', 35.0)
```

**Key Point:** Always returns **list**, even for single component

---

### Pattern 2: Multiple Components

**Use:** When Blueprint has multiple of same type (e.g., multiple lights)

```python
# Get all PointLightComponents
lights = actor.get_components_by_class(unreal.PointLightComponent)

for i, light in enumerate(lights):
    light.set_editor_property('intensity', 5000.0 * (i + 1))
    light.set_editor_property('light_color',
        unreal.LinearColor(1.0, 0.8, 0.6, 1.0)
    )
```

**Key Point:** Iterate over list, configure each independently

---

### Pattern 3: Single Component (Alternative)

**Use:** When only one component expected (cleaner code)

```python
# Returns single component or None (NOT a list)
camera = actor.get_component_by_class(unreal.CineCameraComponent)

if camera:
    camera.set_editor_property('current_focal_length', 50.0)
else:
    print("Camera component not found")
```

**Difference:**
- `get_components_by_class()` -> List (always)
- `get_component_by_class()` -> Single object or None

---

### Pattern 4: All Components

**Use:** When need to inspect all components (debugging)

```python
# Get ALL components of all types
all_comps = actor.get_components_by_class(unreal.ActorComponent)

for comp in all_comps:
    print(f"Component: {comp.get_name()}")
    print(f"  Type: {type(comp).__name__}")
    print(f"  Class: {comp.get_class().get_name()}")
```

**Use Case:** Debugging, discovery, validation

---

### Component Access Error Handling

**Pattern:**
```python
# Safe component access
def get_camera_component(actor):
    """Get CineCameraComponent from actor, return None if not found."""
    components = actor.get_components_by_class(unreal.CineCameraComponent)
    return components[0] if components else None

# Usage
camera = get_camera_component(actor)
if camera:
    # Configure camera
    pass
else:
    unreal.log_error(f"Actor {actor.get_name()} has no CineCameraComponent")
```

---

## Common Blueprint Types

### Actor (Base Class)

**Use:** Generic actor with custom logic

**Python:**
```python
bp = unreal.load_class(None, "/Game/BP_CustomActor.BP_CustomActor_C")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
```

**When to Use:** Custom game logic, VFX tools, level automation

---

### Pawn

**Use:** Controllable actor (player, AI)

**Python:**
```python
bp = unreal.load_class(None, "/Game/BP_PlayerPawn.BP_PlayerPawn_C")
pawn = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
```

**When to Use:** Player characters, AI agents, vehicles

---

### Character

**Use:** Pawn with movement component and animation

**Python:**
```python
bp = unreal.load_class(None, "/Game/BP_Character.BP_Character_C")
character = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)

# Access movement component
movement = character.get_component_by_class(unreal.CharacterMovementComponent)
movement.set_editor_property('max_walk_speed', 600.0)
```

**When to Use:** Third-person characters, NPCs with animation

---

### CineCameraActor

**Use:** Film-quality camera with filmback, lens settings

**Python:**
```python
bp = unreal.load_class(None, "/Game/BP_CineCamera.BP_CineCamera_C")
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)

# Access CineCameraComponent
cine_cam = camera.get_component_by_class(unreal.CineCameraComponent)
cine_cam.set_editor_property('current_focal_length', 35.0)
cine_cam.set_editor_property('current_aperture', 2.8)
cine_cam.set_editor_property('filmback',
    unreal.CameraFilmbackSettings(
        sensor_width=36.0,
        sensor_height=24.0
    )
)
```

**When to Use:** Cinematics, VFX shots, film-accurate camera

---

### StaticMeshActor

**Use:** Actor with static mesh component

**Python:**
```python
bp = unreal.load_class(None, "/Game/BP_Prop.BP_Prop_C")
mesh_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)

# Access mesh component
mesh = mesh_actor.get_component_by_class(unreal.StaticMeshComponent)
mesh.set_static_mesh(unreal.load_asset("/Game/Meshes/SM_Cube"))
mesh.set_material(0, unreal.load_asset("/Game/Materials/M_Material"))
```

**When to Use:** Props, environment assets, mesh instances

---

## Blueprint Spawning Patterns

### Basic Spawn

```python
import unreal

# Load Blueprint class
bp = unreal.load_class(None, "/Game/BP_Actor.BP_Actor_C")

# Spawn at location
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    actor_class=bp,
    location=unreal.Vector(0, 0, 100),
    rotation=unreal.Rotator(0, 0, 0)
)
```

---

### Spawn with Name

```python
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    actor_class=bp,
    location=unreal.Vector(0, 0, 100)
)

# Set label (editor display name)
actor.set_actor_label("CustomName_001")
```

---

### Batch Spawn

```python
bp = unreal.load_class(None, "/Game/BP_Actor.BP_Actor_C")

actors = []
for i in range(10):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        bp,
        location=unreal.Vector(i * 100, 0, 0)
    )
    actor.set_actor_label(f"Actor_{i:03d}")
    actors.append(actor)

print(f"Spawned {len(actors)} actors")
```

---

### Spawn with Component Configuration

```python
bp = unreal.load_class(None, "/Game/BP_Camera.BP_Camera_C")

camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    bp, location=unreal.Vector(0, 0, 100)
)

# Access component
cine_cam = camera.get_component_by_class(unreal.CineCameraComponent)

# Configure
cine_cam.set_editor_property('current_focal_length', 50.0)
cine_cam.set_editor_property('current_aperture', 2.8)
```

---

## Advanced Patterns

### Dynamic Blueprint Loading

**Use Case:** Blueprint path not known until runtime

```python
def spawn_blueprint_by_name(blueprint_name, location):
    """Spawn Blueprint by name (searches /Game/)."""

    # Construct path
    bp_path = f"/Game/{blueprint_name}.{blueprint_name}_C"

    # Load class
    bp = unreal.load_class(None, bp_path)

    if bp is None:
        unreal.log_error(f"Blueprint not found: {bp_path}")
        return None

    # Spawn
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        bp, location=location
    )

    return actor

# Usage
actor = spawn_blueprint_by_name("BP_Camera", unreal.Vector(0, 0, 100))
```

---

### Blueprint Validation

**Check if Blueprint exists before spawning:**

```python
def blueprint_exists(blueprint_path):
    """Check if Blueprint class can be loaded."""
    bp = unreal.load_class(None, blueprint_path)
    return bp is not None

# Usage
bp_path = "/Game/BP_Actor.BP_Actor_C"
if blueprint_exists(bp_path):
    bp = unreal.load_class(None, bp_path)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
else:
    print(f"Blueprint not found: {bp_path}")
```

---

### Get Blueprint from Spawned Actor

**Reverse lookup: Get Blueprint class from actor instance:**

```python
actor = unreal.EditorLevelLibrary.get_selected_level_actors()[0]

# Get class
actor_class = actor.get_class()

# Get class path
class_path = actor_class.get_path_name()
print(f"Actor class: {class_path}")

# Example output: /Game/BP_Actor.BP_Actor_C
```

---

### Find All Actors of Blueprint Type

```python
def find_actors_of_blueprint(blueprint_path):
    """Find all actors in level of specific Blueprint type."""

    # Load Blueprint class
    bp = unreal.load_class(None, blueprint_path)
    if bp is None:
        return []

    # Get all actors in level
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

    # Filter by class
    matching = [actor for actor in all_actors if actor.get_class() == bp]

    return matching

# Usage
cameras = find_actors_of_blueprint("/Game/BP_Camera.BP_Camera_C")
print(f"Found {len(cameras)} camera actors")
```

---

## Multi-Instance Independence

### Blueprint Instances are Independent

**Key Concept:** Each Blueprint instance has its own component instances

```python
bp = unreal.load_class(None, "/Game/BP_Camera.BP_Camera_C")

# Spawn two instances
cam1 = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
cam2 = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)

# Get components (different instances!)
comp1 = cam1.get_component_by_class(unreal.CineCameraComponent)
comp2 = cam2.get_component_by_class(unreal.CineCameraComponent)

# Configure independently
comp1.set_editor_property('current_focal_length', 35.0)
comp2.set_editor_property('current_focal_length', 50.0)

# comp1 and comp2 are DIFFERENT objects
assert comp1 != comp2  # True
```

---

### Material Instance Per Actor

**Pattern:** Each Blueprint instance can have different material instances

```python
bp = unreal.load_class(None, "/Game/BP_Prop.BP_Prop_C")
master_mat = unreal.load_asset("/Game/Materials/M_Master")
tools = unreal.AssetToolsHelpers.get_asset_tools()

for i in range(10):
    # Spawn actor
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)

    # Create material instance
    mat_instance = tools.create_asset(
        f"MI_Prop_{i:03d}", "/Game/Materials/Instances",
        unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew()
    )
    mat_instance.set_editor_property('parent', master_mat)

    # Assign to actor
    mesh = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh.set_material(0, mat_instance)
```

**Result:** Each actor has unique material instance (independent color/properties)

---

## Troubleshooting

### Blueprint Not Loading (Returns None)

**Symptom:**
```python
bp = unreal.load_class(None, "/Game/BP_Actor.BP_Actor")  # None
```

**Fixes:**
1. Add `_C` suffix: `/Game/BP_Actor.BP_Actor_C`
2. Check path (case-sensitive)
3. Verify Blueprint exists in Content Browser
4. Use Copy Reference to get exact path

---

### Spawned Actor Has No Components

**Symptom:**
```python
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
comps = actor.get_components_by_class(unreal.CameraComponent)
# comps is empty list
```

**Fixes:**
1. Check Blueprint actually has component
2. Verify component type (CameraComponent vs CineCameraComponent)
3. Check if component enabled in Blueprint

---

### Component Properties Not Settable

**Symptom:**
```python
component.set_editor_property('property_name', value)
# AttributeError: property not found
```

**Fixes:**
1. Check property name (case-sensitive)
2. Use `dir(component)` to list properties
3. Some properties C++ only (see api_limitations_ue55.md)

---

## Best Practices

### 1. Always Check Blueprint Loaded

```python
bp = unreal.load_class(None, bp_path)
if bp is None:
    unreal.log_error(f"Blueprint not found: {bp_path}")
    return
# Use bp safely
```

---

### 2. Cache Blueprint Class

**Don't:**
```python
# Load Blueprint 100 times (slow)
for i in range(100):
    bp = unreal.load_class(None, "/Game/BP_Actor.BP_Actor_C")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
```

**Do:**
```python
# Load once, reuse (fast)
bp = unreal.load_class(None, "/Game/BP_Actor.BP_Actor_C")
for i in range(100):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
```

---

### 3. Use Type Hints

```python
import unreal
from typing import Optional

def get_camera_component(actor: unreal.Actor) -> Optional[unreal.CineCameraComponent]:
    """Get CineCameraComponent from actor."""
    components = actor.get_components_by_class(unreal.CineCameraComponent)
    return components[0] if components else None
```

---

### 4. Validate Components After Spawn

```python
def spawn_and_validate(bp_path, location):
    """Spawn Blueprint and validate required components."""
    bp = unreal.load_class(None, bp_path)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, location=location)

    # Validate camera component exists
    camera = actor.get_component_by_class(unreal.CineCameraComponent)
    if camera is None:
        unreal.log_error(f"Actor missing CineCameraComponent")
        unreal.EditorLevelLibrary.destroy_actor(actor)
        return None

    return actor
```

---

## References

### Related Documentation
- **api_limitations_ue55.md** - Why Blueprint workarounds needed
- **component_patterns.md** - Component access patterns
- **SKILL.md** - Quick start patterns

### Official Documentation
- Unreal Engine Python API - Blueprint class loading
- Epic Games - Blueprint naming conventions

---

**Document Status:** Production-ready
**Tested:** UE 5.5.0, Windows 11, 2025-10-25
**Coverage:** Blueprint loading, spawning, component access

---

*Blueprint Patterns - Unreal Engine 5.5 Python*
*Last Updated: 2025-10-25*
