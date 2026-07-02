# Component Patterns - Unreal Engine 5.5 Python

**Document Version:** 1.0.0
**Target:** Unreal Engine 5.5+
**Last Updated:** 2025-10-25
**Python Version:** 3.11 (UE built-in)

---

## Overview

### Purpose

Component discovery, property setting, and manipulation patterns for Unreal Engine Python API.

**Key Topics:**
- Finding components (by class, tag, name)
- Setting component properties
- Type coercion (Vector, Rotator, Color)
- Component hierarchy traversal
- Attachment limitations
- Blueprint-based component setup

---

## Finding Components

### Pattern 1: By Class (Most Common)

**Use:** When you know component type

```python
import unreal

actor = unreal.EditorLevelLibrary.get_selected_level_actors()[0]

# Returns LIST (even if only one component)
components = actor.get_components_by_class(unreal.StaticMeshComponent)

if components:
    mesh = components[0]  # Get first component
    mesh.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
```

**Key Points:**
- Always returns **list** (even for single component)
- Empty list if no components found (not None)
- Check `if components:` before accessing

---

### Pattern 2: Single Component

**Use:** When only one component of type expected

```python
# Returns SINGLE component or None (NOT a list)
component = actor.get_component_by_class(unreal.CineCameraComponent)

if component:
    component.set_editor_property('current_focal_length', 35.0)
else:
    print("CineCameraComponent not found")
```

**Difference from Pattern 1:**
- `get_components_by_class()` → List (always)
- `get_component_by_class()` → Single object or None

---

### Pattern 3: All Components

**Use:** Get all components regardless of type

```python
# Get ALL components (all types)
all_comps = actor.get_components_by_class(unreal.ActorComponent)

for comp in all_comps:
    print(f"Component: {comp.get_name()}")
    print(f"  Type: {type(comp).__name__}")
    print(f"  Class: {comp.get_class().get_name()}")
```

**Use Case:** Debugging, component discovery, validation

---

### Pattern 4: By Tag

**Use:** Components tagged in Blueprint/editor

**Blueprint Setup:**
1. Select component in Blueprint
2. Tags section → Add tag (e.g., "MainCamera")

**Python:**
```python
# Get all components
all_comps = actor.get_components_by_class(unreal.ActorComponent)

# Filter by tag
for comp in all_comps:
    if comp.component_has_tag("MainCamera"):
        print(f"Found tagged component: {comp.get_name()}")
        # Configure component
```

**Useful For:** Identifying specific components in complex hierarchies

---

### Pattern 5: By Name

**Use:** Component has specific name

```python
# Get all components
all_comps = actor.get_components_by_class(unreal.SceneComponent)

# Find by name
for comp in all_comps:
    if comp.get_name() == "CameraComponent1":
        # Configure component
        pass
```

**Warning:** Component names auto-generated, may change

---

## Setting Component Properties

### Exposed Properties (via set_editor_property)

**Pattern:**
```python
component.set_editor_property('property_name', value)
```

**Example:**
```python
camera = actor.get_component_by_class(unreal.CineCameraComponent)

# Simple scalar
camera.set_editor_property('current_focal_length', 35.0)

# Enum
camera.set_editor_property('projection_mode',
    unreal.CameraProjectionMode.PERSPECTIVE
)

# Boolean
camera.set_editor_property('constrain_aspect_ratio', True)
```

---

### Property Name Discovery

**Method 1: dir() Listing**
```python
camera = actor.get_component_by_class(unreal.CineCameraComponent)

# List all attributes
properties = dir(camera)

# Filter for likely properties (no underscores)
public_props = [p for p in properties if not p.startswith('_')]

for prop in public_props:
    print(prop)
```

**Method 2: Official Documentation**
- Unreal Engine Python API Reference
- Search for component class (e.g., "CineCameraComponent Python")

**Method 3: Trial-and-Error**
```python
try:
    camera.set_editor_property('current_focal_length', 50.0)
    print("Property set successfully")
except AttributeError as e:
    print(f"Property not found: {e}")
```

---

### Common Component Properties

**CineCameraComponent:**
```python
camera.set_editor_property('current_focal_length', 35.0)  # mm
camera.set_editor_property('current_aperture', 2.8)       # f-stop
camera.set_editor_property('focus_settings.manual_focus_distance', 100.0)  # cm
camera.set_editor_property('filmback',
    unreal.CameraFilmbackSettings(
        sensor_width=36.0,   # mm
        sensor_height=24.0   # mm
    )
)
```

**StaticMeshComponent:**
```python
mesh = actor.get_component_by_class(unreal.StaticMeshComponent)

mesh.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
mesh.set_editor_property('cast_shadow', True)
mesh.set_static_mesh(unreal.load_asset("/Game/Meshes/SM_Cube"))
mesh.set_material(0, unreal.load_asset("/Game/Materials/M_Material"))
```

**PointLightComponent:**
```python
light = actor.get_component_by_class(unreal.PointLightComponent)

light.set_editor_property('intensity', 5000.0)  # lumens
light.set_editor_property('light_color',
    unreal.LinearColor(1.0, 0.8, 0.6, 1.0)  # warm white
)
light.set_editor_property('attenuation_radius', 1000.0)  # cm
light.set_editor_property('source_radius', 10.0)  # cm (soft shadows)
```

---

## Type Coercion

### Vector

**Definition:** 3D position (X, Y, Z in centimeters)

```python
import unreal

# Create Vector
location = unreal.Vector(100.0, 200.0, 300.0)  # X, Y, Z

# Set actor location
actor.set_actor_location(location)

# Component location (relative to parent)
component.set_relative_location(unreal.Vector(0, 0, 100))
```

**Common Mistakes:**
```python
# ❌ WRONG: Tuple won't work
actor.set_actor_location((0, 0, 100))

# ✅ CORRECT: Must use unreal.Vector
actor.set_actor_location(unreal.Vector(0, 0, 100))
```

---

### Rotator

**Definition:** 3D rotation (Pitch, Yaw, Roll in degrees)

```python
import unreal

# Create Rotator
rotation = unreal.Rotator(
    pitch=0.0,   # Up/down tilt
    yaw=90.0,    # Left/right rotation
    roll=0.0     # Bank/lean
)

# Set actor rotation
actor.set_actor_rotation(rotation)

# Component rotation (relative to parent)
component.set_relative_rotation(unreal.Rotator(0, 45, 0))
```

**Axis Convention:**
- **Pitch:** X-axis rotation (up/down)
- **Yaw:** Z-axis rotation (left/right)
- **Roll:** Y-axis rotation (bank)

**Common Values:**
```python
# Look forward (default)
unreal.Rotator(0, 0, 0)

# Look right (90 degrees)
unreal.Rotator(0, 90, 0)

# Look up (45 degrees)
unreal.Rotator(45, 0, 0)
```

---

### LinearColor

**Definition:** RGBA color (0.0 to 1.0 range)

```python
import unreal

# Create LinearColor
color = unreal.LinearColor(
    r=1.0,  # Red
    g=0.0,  # Green
    b=0.0,  # Blue
    a=1.0   # Alpha (usually 1.0 for opaque)
)

# Set light color
light.set_editor_property('light_color', color)
```

**Common Colors:**
```python
# Red
unreal.LinearColor(1.0, 0.0, 0.0, 1.0)

# Green
unreal.LinearColor(0.0, 1.0, 0.0, 1.0)

# Blue
unreal.LinearColor(0.0, 0.0, 1.0, 1.0)

# White
unreal.LinearColor(1.0, 1.0, 1.0, 1.0)

# Warm white (lighting)
unreal.LinearColor(1.0, 0.9, 0.8, 1.0)

# Cool white (lighting)
unreal.LinearColor(0.8, 0.9, 1.0, 1.0)

# Gray (50%)
unreal.LinearColor(0.5, 0.5, 0.5, 1.0)
```

**Range:** 0.0 to 1.0 (NOT 0-255 like sRGB)

**Conversion from sRGB:**
```python
# sRGB: RGB(255, 128, 64)
# LinearColor: divide by 255
color = unreal.LinearColor(255/255, 128/255, 64/255, 1.0)
# Result: LinearColor(1.0, 0.502, 0.251, 1.0)
```

---

### Transform

**Definition:** Combined location, rotation, and scale

```python
import unreal

# Create Transform
transform = unreal.Transform(
    location=unreal.Vector(0, 0, 100),
    rotation=unreal.Rotator(0, 90, 0),
    scale=unreal.Vector(1, 1, 1)
)

# Set actor transform
actor.set_actor_transform(transform)

# Component transform (relative to parent)
component.set_relative_transform(transform)
```

---

### Struct Types

**CameraFilmbackSettings:**
```python
filmback = unreal.CameraFilmbackSettings(
    sensor_width=36.0,   # mm (full-frame)
    sensor_height=24.0   # mm (full-frame)
)
camera.set_editor_property('filmback', filmback)
```

**CameraLensSettings:**
```python
lens = unreal.CameraLensSettings(
    min_focal_length=18.0,  # mm
    max_focal_length=200.0, # mm
    min_f_stop=1.8,
    max_f_stop=22.0
)
camera.set_editor_property('lens_settings', lens)
```

---

## Component Hierarchy Traversal

### Get Parent Component

```python
# Get component's parent
parent = component.get_attach_parent()

if parent:
    print(f"Parent: {parent.get_name()}")
else:
    print("No parent (root component)")
```

---

### Get Children Components

```python
# Get all children of component
children = component.get_attach_children()

for child in children:
    print(f"Child: {child.get_name()}")
```

---

### Get Root Component

```python
# Get actor's root component
root = actor.get_editor_property('root_component')

print(f"Root component: {root.get_name()}")
```

---

### Traverse Entire Hierarchy

```python
def print_component_hierarchy(component, indent=0):
    """Recursively print component hierarchy."""
    print("  " * indent + f"- {component.get_name()} ({type(component).__name__})")

    # Recurse into children
    children = component.get_attach_children()
    for child in children:
        print_component_hierarchy(child, indent + 1)

# Usage
root = actor.get_editor_property('root_component')
print_component_hierarchy(root)
```

**Example Output:**
```
- DefaultSceneRoot (SceneComponent)
  - CineCameraComponent (CineCameraComponent)
    - ImagePlateComponent (ImagePlateComponent)
      - ImagePlateFrustumComponent (ImagePlateFrustumComponent)
  - PointLightComponent (PointLightComponent)
```

---

## Attachment Limitations

### What Works

**Finding Existing Attachments:**
```python
# ✅ Get parent
parent = component.get_attach_parent()

# ✅ Get children
children = component.get_attach_children()

# ✅ Traverse hierarchy
root = actor.get_editor_property('root_component')
```

**Setting Properties on Attached Components:**
```python
# ✅ Configure attached components
component = actor.get_component_by_class(unreal.ImagePlateComponent)
component.set_editor_property('plate', material)
```

---

### What DOESN'T Work

**Runtime Component Attachment:**
```python
# ❌ setup_attachment() not available
component.setup_attachment(parent)  # AttributeError

# ❌ attach_to_component() not available
component.attach_to_component(parent, ...)  # AttributeError

# ❌ Component registration not available
component.register_component()  # AttributeError
```

**Why?** These methods C++ only, not exposed to Python (see api_limitations_ue55.md)

---

### Workaround: Blueprint-Based Component Setup

**Pattern:**
1. Create Blueprint in editor
2. Define component hierarchy in Blueprint
3. Spawn Blueprint instance in Python
4. Components already attached correctly

**Blueprint Setup (Editor):**
1. Create Blueprint (based on Actor or CineCameraActor)
2. Add components in Blueprint editor
3. Arrange hierarchy (drag-and-drop to attach)
4. Save Blueprint

**Python Usage:**
```python
# Spawn Blueprint
bp = unreal.load_class(None, "/Game/BP_Actor.BP_Actor_C")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)

# Components already attached (defined in Blueprint)
component = actor.get_component_by_class(unreal.ImagePlateComponent)
# Component attached to parent, ready to configure
```

**Result:** Component hierarchy pre-defined, no attachment code needed

---

## Blueprint-Based Component Setup

### Example: Camera with ImagePlate

**Blueprint Setup (Editor):**

**Step 1:** Create Blueprint
- File → New C++ Class → CineCameraActor (or Blueprint Class)
- Name: `BP_CameraWithPlate`
- Save to: `/Game/`

**Step 2:** Add Components
1. Open Blueprint editor
2. Components panel → Add Component → ImagePlate Component
3. ImagePlateComponent auto-creates ImagePlateFrustumComponent

**Step 3:** Configure Hierarchy
1. Drag ImagePlateComponent onto CineCameraComponent (attaches)
2. Set ImagePlateComponent properties (optional default material)

**Step 4:** Save Blueprint

---

**Python Usage:**
```python
import unreal

# Load Blueprint class
bp = unreal.load_class(None, "/Game/BP_CameraWithPlate.BP_CameraWithPlate_C")

# Spawn instance
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    bp,
    location=unreal.Vector(0, 0, 100)
)

# Access components (already attached)
image_plates = camera.get_components_by_class(unreal.ImagePlateComponent)
if image_plates:
    image_plate = image_plates[0]

    # Configure material
    material = unreal.load_asset("/Game/Materials/M_Plate")
    image_plate.set_editor_property('plate', material)
```

**Advantages:**
- Component attachment handled by Blueprint
- No component registration needed
- Reusable across shots
- Artists can modify Blueprint without code changes

---

## Common Component Types

### SceneComponent (Base)

**All visual components inherit from SceneComponent**

**Common Properties:**
```python
scene_comp = actor.get_component_by_class(unreal.SceneComponent)

# Transform
scene_comp.set_relative_location(unreal.Vector(0, 0, 100))
scene_comp.set_relative_rotation(unreal.Rotator(0, 90, 0))
scene_comp.set_relative_scale3d(unreal.Vector(1, 1, 1))

# Visibility
scene_comp.set_visibility(True)
scene_comp.set_hidden_in_game(False)

# Mobility
scene_comp.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
```

---

### CineCameraComponent

**Film-quality camera**

```python
camera = actor.get_component_by_class(unreal.CineCameraComponent)

# Lens settings
camera.set_editor_property('current_focal_length', 35.0)  # mm
camera.set_editor_property('current_aperture', 2.8)       # f-stop

# Filmback (sensor size)
camera.set_editor_property('filmback',
    unreal.CameraFilmbackSettings(
        sensor_width=36.0,   # mm (full-frame)
        sensor_height=24.0   # mm
    )
)

# Focus
camera.set_editor_property('focus_settings.manual_focus_distance', 100.0)  # cm
camera.set_editor_property('focus_settings.focus_method',
    unreal.CameraFocusMethod.MANUAL
)
```

---

### StaticMeshComponent

**Static mesh rendering**

```python
mesh = actor.get_component_by_class(unreal.StaticMeshComponent)

# Set mesh
mesh.set_static_mesh(unreal.load_asset("/Game/Meshes/SM_Cube"))

# Set material
mesh.set_material(0, unreal.load_asset("/Game/Materials/M_Material"))

# Mobility
mesh.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)

# Shadows
mesh.set_editor_property('cast_shadow', True)

# Collision
mesh.set_editor_property('collision_enabled',
    unreal.CollisionEnabled.QUERY_AND_PHYSICS
)
```

---

### PointLightComponent

**Point light source**

```python
light = actor.get_component_by_class(unreal.PointLightComponent)

# Intensity
light.set_editor_property('intensity', 5000.0)  # lumens

# Color
light.set_editor_property('light_color',
    unreal.LinearColor(1.0, 0.9, 0.8, 1.0)  # warm white
)

# Attenuation (range)
light.set_editor_property('attenuation_radius', 1000.0)  # cm

# Source radius (soft shadows)
light.set_editor_property('source_radius', 10.0)  # cm

# Shadows
light.set_editor_property('cast_shadows', True)
```

---

### DirectionalLightComponent

**Directional light (sun)**

```python
sun = actor.get_component_by_class(unreal.DirectionalLightComponent)

# Intensity
sun.set_editor_property('intensity', 10.0)  # lux

# Color
sun.set_editor_property('light_color',
    unreal.LinearColor(1.0, 0.95, 0.9, 1.0)  # sunlight
)

# Shadows
sun.set_editor_property('cast_shadows', True)
sun.set_editor_property('cast_dynamic_shadows', True)
```

---

### ImagePlateComponent

**VFX foreground/background plate**

```python
image_plate = actor.get_component_by_class(unreal.ImagePlateComponent)

# Assign material
material = unreal.load_asset("/Game/Materials/M_Plate")
image_plate.set_editor_property('plate', material)

# Render mode
image_plate.set_editor_property('render_target_mode',
    unreal.ImagePlateMode.FIT_TO_FRUSTUM
)
```

**Note:** Must be attached to CineCameraActor (Blueprint setup required)

---

## Batch Component Operations

### Batch Property Setting

**Pattern:**
```python
# Get selected actors
actors = unreal.EditorLevelLibrary.get_selected_level_actors()

for actor in actors:
    # Find components
    lights = actor.get_components_by_class(unreal.PointLightComponent)

    # Configure each component
    for light in lights:
        light.set_editor_property('intensity', 5000.0)
        light.set_editor_property('light_color',
            unreal.LinearColor(1.0, 0.8, 0.6, 1.0)
        )

print(f"Configured lights in {len(actors)} actors")
```

---

### Conditional Component Configuration

**Pattern:**
```python
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for actor in actors:
    cameras = actor.get_components_by_class(unreal.CineCameraComponent)

    for camera in cameras:
        # Only update if focal length < 50mm
        current_focal = camera.get_editor_property('current_focal_length')
        if current_focal < 50.0:
            camera.set_editor_property('current_focal_length', 50.0)
            print(f"Updated camera in {actor.get_name()}")
```

---

## Error Handling

### Safe Component Access

```python
def get_component_safe(actor, component_class):
    """Get component with error handling."""
    try:
        components = actor.get_components_by_class(component_class)
        return components[0] if components else None
    except Exception as e:
        unreal.log_error(f"Error getting component: {e}")
        return None

# Usage
camera = get_component_safe(actor, unreal.CineCameraComponent)
if camera:
    # Configure camera
    pass
```

---

### Safe Property Setting

```python
def set_property_safe(component, property_name, value):
    """Set property with error handling."""
    try:
        component.set_editor_property(property_name, value)
        return True
    except AttributeError:
        unreal.log_warning(f"Property '{property_name}' not found")
        return False
    except Exception as e:
        unreal.log_error(f"Error setting property: {e}")
        return False

# Usage
if set_property_safe(camera, 'current_focal_length', 35.0):
    print("Property set successfully")
```

---

## Troubleshooting

### Component Not Found

**Symptom:**
```python
components = actor.get_components_by_class(unreal.CameraComponent)
# Empty list
```

**Fixes:**
1. Check component type (CameraComponent vs CineCameraComponent)
2. Verify component exists in Blueprint
3. Check if component enabled in Blueprint

---

### Property Not Settable

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

### Type Mismatch

**Symptom:**
```python
actor.set_actor_location((0, 0, 100))
# TypeError: expected Vector, got tuple
```

**Fix:**
```python
# Use unreal.Vector
actor.set_actor_location(unreal.Vector(0, 0, 100))
```

---

## Best Practices

### 1. Cache Component References

**Don't:**
```python
# Find component 100 times (slow)
for i in range(100):
    camera = actor.get_component_by_class(unreal.CineCameraComponent)
    camera.set_editor_property('current_focal_length', 35.0 + i)
```

**Do:**
```python
# Find once, reuse (fast)
camera = actor.get_component_by_class(unreal.CineCameraComponent)
for i in range(100):
    camera.set_editor_property('current_focal_length', 35.0 + i)
```

---

### 2. Check Component Exists

```python
# Always check before using
component = actor.get_component_by_class(ComponentClass)
if component:
    # Use component safely
    pass
else:
    unreal.log_error("Component not found")
```

---

### 3. Use Type Hints

```python
import unreal
from typing import Optional

def get_camera(actor: unreal.Actor) -> Optional[unreal.CineCameraComponent]:
    """Get CineCameraComponent from actor."""
    return actor.get_component_by_class(unreal.CineCameraComponent)
```

---

### 4. Validate Property Names

```python
# Check if property exists before setting
if hasattr(component, 'current_focal_length'):
    component.set_editor_property('current_focal_length', 50.0)
else:
    print("Property not available")
```

---

## References

### Related Documentation
- **api_limitations_ue55.md** - Component attachment limitations
- **blueprint_patterns.md** - Blueprint-based component setup
- **SKILL.md** - Quick start patterns

### Official Documentation
- Unreal Engine Python API - Component classes
- Epic Games - Component best practices

---

**Document Status:** Production-ready
**Tested:** UE 5.5.0, Windows 11, 2025-10-25
**Coverage:** Component discovery, property setting, hierarchy traversal

---

*Component Patterns - Unreal Engine 5.5 Python*
*Last Updated: 2025-10-25*
