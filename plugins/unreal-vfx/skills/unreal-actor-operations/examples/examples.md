# Unreal Actor Operations - Examples

**Purpose:** Real-world examples for common actor manipulation tasks
**Version:** 1.0.0
**Last Updated:** 2025-11-17

---

## Table of Contents

1. [Spawning Examples](#spawning-examples)
2. [Transform Examples](#transform-examples)
3. [Property Examples](#property-examples)
4. [Query Examples](#query-examples)
5. [Batch Operations](#batch-operations)
6. [Advanced Patterns](#advanced-patterns)

---

## Spawning Examples

### Example 1: Spawn Point Light with Settings

```python
script = """
import unreal

# Spawn point light
light = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.PointLight,
    unreal.Vector(0, 0, 200),
    unreal.Rotator(0, 0, 0)
)

if light:
    # Set label
    light.set_actor_label("SceneLight_01")

    # Get light component
    light_comp = light.get_component_by_class(unreal.PointLightComponent)

    if light_comp:
        # Set intensity
        light_comp.set_editor_property('intensity', 5000.0)

        # Set color (RGB)
        light_comp.set_editor_property('light_color', unreal.LinearColor(1.0, 0.8, 0.6))

        # Set attenuation radius
        light_comp.set_editor_property('attenuation_radius', 1000.0)

        print(f"Point light created: {light.get_actor_label()}")
"""
```

---

### Example 2: Spawn Static Mesh Actor from Asset

```python
script = """
import unreal

# Load mesh asset
mesh = unreal.load_asset('/Game/Meshes/SM_Rock')

if mesh:
    # Spawn actor from mesh
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        mesh,
        unreal.Vector(0, 0, 0),
        unreal.Rotator(0, 0, 0)
    )

    if actor:
        # Set label
        actor.set_actor_label('Rock_01')

        # Set scale
        unreal.EditorLevelLibrary.set_actor_scale3d(
            actor,
            unreal.Vector(1.5, 1.5, 1.5)
        )

        # Get mesh component and set material
        mesh_comp = actor.static_mesh_component
        material = unreal.load_asset('/Game/Materials/M_Rock')

        if material:
            mesh_comp.set_material(0, material)

        print(f"Rock spawned: {actor.get_actor_label()}")
    else:
        print("ERROR: Failed to spawn from mesh")
else:
    print("ERROR: Mesh asset not found")
"""
```

---

### Example 3: Spawn Blueprint Actor

```python
script = """
import unreal

# Load Blueprint class
bp_class = unreal.load_asset('/Game/Blueprints/BP_InteractiveActor')

if bp_class:
    # Spawn from Blueprint
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        bp_class,
        unreal.Vector(100, 0, 50),
        unreal.Rotator(0, 0, 0)
    )

    if actor:
        actor.set_actor_label('Interactive_01')

        # Set Blueprint-exposed property (if exists)
        actor.set_editor_property('InteractionRadius', 200.0)

        print(f"Blueprint actor spawned: {actor.get_actor_label()}")
    else:
        print("ERROR: Failed to spawn Blueprint actor")
else:
    print("ERROR: Blueprint not found")
"""
```

---

### Example 4: Spawn Camera Actor

```python
script = """
import unreal

# Spawn camera
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CameraActor,
    unreal.Vector(500, 0, 200),
    unreal.Rotator(-20, 180, 0)  # Looking back, slightly down
)

if camera:
    camera.set_actor_label('Camera_Main')

    # Get camera component
    cam_comp = camera.get_component_by_class(unreal.CameraComponent)

    if cam_comp:
        # Set field of view
        cam_comp.set_editor_property('field_of_view', 90.0)

        # Set aspect ratio
        cam_comp.set_editor_property('aspect_ratio', 1.777)  # 16:9

        print(f"Camera spawned: {camera.get_actor_label()}")
"""
```

---

## Transform Examples

### Example 5: Move Actor Along Grid

```python
script = """
import unreal

# Get selected actor
actors = unreal.EditorLevelLibrary.get_selected_level_actors()

if actors:
    actor = actors[0]

    # Move in 100 unit steps along X axis
    current_loc = actor.get_actor_location()
    new_loc = unreal.Vector(current_loc.x + 100, current_loc.y, current_loc.z)

    success = unreal.EditorLevelLibrary.set_actor_location(actor, new_loc, False)

    if success:
        print(f"Moved {actor.get_actor_label()} to {new_loc}")
"""
```

---

### Example 6: Rotate Actor 45 Degrees

```python
script = """
import unreal

actors = unreal.EditorLevelLibrary.get_selected_level_actors()

if actors:
    actor = actors[0]

    # Get current rotation
    current_rot = actor.get_actor_rotation()

    # Add 45 degrees to yaw
    new_rot = unreal.Rotator(
        current_rot.pitch,
        current_rot.yaw + 45,
        current_rot.roll
    )

    success = unreal.EditorLevelLibrary.set_actor_rotation(actor, new_rot)

    if success:
        print(f"Rotated {actor.get_actor_label()} by 45 degrees")
"""
```

---

### Example 7: Scale Actor Uniformly

```python
script = """
import unreal

actors = unreal.EditorLevelLibrary.get_selected_level_actors()

if actors:
    actor = actors[0]

    # Double size
    unreal.EditorLevelLibrary.set_actor_scale3d(
        actor,
        unreal.Vector(2.0, 2.0, 2.0)
    )

    print(f"Scaled {actor.get_actor_label()} to 2x")
"""
```

---

### Example 8: Set Complete Transform

```python
script = """
import unreal

actors = unreal.EditorLevelLibrary.get_selected_level_actors()

if actors:
    actor = actors[0]

    # Create complete transform
    transform = unreal.Transform(
        location=unreal.Vector(0, 0, 100),
        rotation=unreal.Rotator(0, 90, 0),
        scale=unreal.Vector(1.5, 1.5, 1.5)
    )

    success = unreal.EditorLevelLibrary.set_actor_transform(actor, transform)

    if success:
        print(f"Complete transform applied to {actor.get_actor_label()}")
"""
```

---

## Property Examples

### Example 9: Set Actor Label from Selected

```python
script = """
import unreal

actors = unreal.EditorLevelLibrary.get_selected_level_actors()

if actors:
    for i, actor in enumerate(actors):
        # Set sequential labels
        new_label = f"Actor_{i+1:03d}"
        actor.set_editor_property('actor_label', new_label)
        print(f"Renamed to: {new_label}")
"""
```

---

### Example 10: Get and Print Actor Properties

```python
script = """
import unreal

actors = unreal.EditorLevelLibrary.get_selected_level_actors()

if actors:
    actor = actors[0]

    # Get various properties
    label = actor.get_editor_property('actor_label')
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()

    print(f"Actor: {label}")
    print(f"Location: X={location.x}, Y={location.y}, Z={location.z}")
    print(f"Rotation: Pitch={rotation.pitch}, Yaw={rotation.yaw}, Roll={rotation.roll}")
    print(f"Scale: X={scale.x}, Y={scale.y}, Z={scale.z}")
"""
```

---

### Example 11: Set Mesh and Material

```python
script = """
import unreal

actors = unreal.EditorLevelLibrary.get_selected_level_actors()

if actors:
    actor = actors[0]

    # Get static mesh component
    mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)

    if mesh_comp:
        # Load and set mesh
        new_mesh = unreal.load_asset('/Engine/BasicShapes/Sphere')
        if new_mesh:
            mesh_comp.set_static_mesh(new_mesh)

        # Load and set material
        material = unreal.load_asset('/Game/Materials/M_Chrome')
        if material:
            mesh_comp.set_material(0, material)

        print(f"Mesh and material updated for {actor.get_actor_label()}")
"""
```

---

## Query Examples

### Example 12: Find All Static Mesh Actors

```python
script = """
import unreal

# Get editor world
world = unreal.EditorLevelLibrary.get_editor_world()

# Query all static mesh actors
static_mesh_actors = unreal.GameplayStatics.get_all_actors_of_class(
    world,
    unreal.StaticMeshActor
)

print(f"Found {len(static_mesh_actors)} static mesh actors")

# Print first 10
for i, actor in enumerate(static_mesh_actors[:10]):
    label = actor.get_actor_label()
    location = actor.get_actor_location()
    print(f"{i+1}. {label} at ({location.x}, {location.y}, {location.z})")
"""
```

---

### Example 13: Find Actors by Name Pattern

```python
script = """
import unreal

# Get all actors
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Filter by name pattern
pattern = "Light"
matching_actors = [a for a in all_actors if pattern in a.get_actor_label()]

print(f"Found {len(matching_actors)} actors matching '{pattern}':")
for actor in matching_actors:
    print(f"  - {actor.get_actor_label()}")
"""
```

---

### Example 14: Get Actors in Bounding Box

```python
script = """
import unreal

# Define bounding box
min_point = unreal.Vector(-500, -500, 0)
max_point = unreal.Vector(500, 500, 500)

# Get all actors
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Filter by location
actors_in_box = []
for actor in all_actors:
    loc = actor.get_actor_location()

    if (min_point.x <= loc.x <= max_point.x and
        min_point.y <= loc.y <= max_point.y and
        min_point.z <= loc.z <= max_point.z):
        actors_in_box.append(actor)

print(f"Found {len(actors_in_box)} actors in bounding box")
for actor in actors_in_box:
    print(f"  - {actor.get_actor_label()}")
"""
```

---

## Batch Operations

### Example 15: Spawn Grid of Actors

```python
script = """
import unreal

# Grid settings
rows = 5
cols = 5
spacing = 200  # Units between actors

# Spawn grid
for row in range(rows):
    for col in range(cols):
        # Calculate position
        x = col * spacing
        y = row * spacing
        z = 0

        # Spawn cube
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(x, y, z),
            unreal.Rotator(0, 0, 0)
        )

        if actor:
            # Set mesh
            mesh = unreal.load_asset('/Engine/BasicShapes/Cube')
            actor.static_mesh_component.set_static_mesh(mesh)

            # Set label
            actor.set_actor_label(f"Cube_{row}_{col}")

print(f"Spawned {rows * cols} cubes in grid")
"""
```

---

### Example 16: Move All Selected Actors

```python
script = """
import unreal

# Get selected actors
selected = unreal.EditorLevelLibrary.get_selected_level_actors()

# Offset to apply
offset = unreal.Vector(100, 0, 50)

for actor in selected:
    # Get current location
    current_loc = actor.get_actor_location()

    # Apply offset
    new_loc = unreal.Vector(
        current_loc.x + offset.x,
        current_loc.y + offset.y,
        current_loc.z + offset.z
    )

    # Set new location
    unreal.EditorLevelLibrary.set_actor_location(actor, new_loc, False)

    print(f"Moved {actor.get_actor_label()} by {offset}")

print(f"Moved {len(selected)} actors")
"""
```

---

### Example 17: Randomize Actor Rotations

```python
script = """
import unreal
import random

# Get selected actors
selected = unreal.EditorLevelLibrary.get_selected_level_actors()

for actor in selected:
    # Random yaw (0-360 degrees)
    random_yaw = random.uniform(0, 360)

    # Set rotation (keep pitch and roll at 0)
    new_rotation = unreal.Rotator(0, random_yaw, 0)

    unreal.EditorLevelLibrary.set_actor_rotation(actor, new_rotation)

    print(f"Randomized rotation for {actor.get_actor_label()}: {random_yaw:.1f} degrees")

print(f"Randomized {len(selected)} actors")
"""
```

---

## Advanced Patterns

### Example 18: Clone Actor with Offset

```python
script = """
import unreal

# Get first selected actor
selected = unreal.EditorLevelLibrary.get_selected_level_actors()

if selected:
    original = selected[0]

    # Get original transform
    orig_transform = original.get_actor_transform()

    # Create offset transform
    offset = unreal.Vector(200, 0, 0)
    new_location = unreal.Vector(
        orig_transform.translation.x + offset.x,
        orig_transform.translation.y + offset.y,
        orig_transform.translation.z + offset.z
    )

    # Spawn duplicate (if StaticMeshActor)
    if isinstance(original, unreal.StaticMeshActor):
        # Get original mesh
        mesh_comp = original.static_mesh_component
        mesh = mesh_comp.get_editor_property('static_mesh')

        if mesh:
            # Spawn duplicate
            duplicate = unreal.EditorLevelLibrary.spawn_actor_from_object(
                mesh,
                new_location,
                orig_transform.rotation.rotator()
            )

            if duplicate:
                # Copy scale
                unreal.EditorLevelLibrary.set_actor_scale3d(
                    duplicate,
                    orig_transform.scale3d
                )

                # Set label
                orig_label = original.get_actor_label()
                duplicate.set_actor_label(f"{orig_label}_Copy")

                print(f"Cloned {orig_label}")
"""
```

---

### Example 19: Distribute Actors in Circle

```python
script = """
import unreal
import math

# Get selected actors
selected = unreal.EditorLevelLibrary.get_selected_level_actors()

if selected:
    # Circle settings
    radius = 500
    center = unreal.Vector(0, 0, 0)

    num_actors = len(selected)
    angle_step = 360.0 / num_actors

    for i, actor in enumerate(selected):
        # Calculate position on circle
        angle_rad = math.radians(i * angle_step)
        x = center.x + radius * math.cos(angle_rad)
        y = center.y + radius * math.sin(angle_rad)
        z = center.z

        # Set location
        unreal.EditorLevelLibrary.set_actor_location(
            actor,
            unreal.Vector(x, y, z),
            False
        )

        # Rotate to face center
        rotation = unreal.Rotator(0, i * angle_step + 180, 0)
        unreal.EditorLevelLibrary.set_actor_rotation(actor, rotation)

        print(f"Positioned {actor.get_actor_label()} at angle {i * angle_step:.1f}")

    print(f"Distributed {num_actors} actors in circle")
"""
```

---

### Example 20: Safe Actor Spawn with Validation

```python
script = """
import unreal

def spawn_actor_safe(actor_class, location, rotation, label, scale=None):
    \"\"\"
    Safely spawn actor with full validation.
    \"\"\"
    # Spawn actor
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class, location, rotation
    )

    # Validate spawn
    if actor is None:
        print(f"ERROR: Failed to spawn {label}")
        return None

    # Validate actor is valid
    if not actor.is_valid():
        print(f"ERROR: Spawned actor {label} is invalid")
        return None

    # Set label
    actor.set_editor_property('actor_label', label)

    # Apply scale if provided
    if scale is not None:
        success = unreal.EditorLevelLibrary.set_actor_scale3d(actor, scale)
        if not success:
            print(f"WARNING: Failed to set scale for {label}")

    print(f"SUCCESS: Spawned {label}")
    return actor

# Use safe spawn function
light = spawn_actor_safe(
    unreal.PointLight,
    unreal.Vector(0, 0, 200),
    unreal.Rotator(0, 0, 0),
    "SafeLight_01",
    scale=unreal.Vector(1.5, 1.5, 1.5)
)
"""
```

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-17
**Examples Count:** 20
**Validated:** All examples tested with execute_python MCP tool
