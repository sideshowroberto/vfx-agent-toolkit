# Sequencer Automation Examples

**Date:** 2025-11-17
**Source:** Breakthrough session and validation testing

---

## Table of Contents

1. [PCG Animation Example](#pcg-animation-example)
2. [Camera Animation Example](#camera-animation-example)
3. [Transform Animation Example](#transform-animation-example)
4. [Property Animation Examples](#property-animation-examples)

---

## PCG Animation Example

**From:** 2025-11-17 Breakthrough Session
**Use Case:** Animating PCG Box Mask parameters over time

### Scenario

Animate a PCG Box Mask sweeping across a landscape with expanding radius.

### Properties to Animate

- `BoxCenterX` - Sweep from -2000 to 2000
- `BoxCenterY` - Static at 0
- `BoxCenterZ` - Static at 0
- `BoxRadius` - Expand from 500 to 2000

### Complete Script

```python
import unreal

# Create sequence
factory = unreal.LevelSequenceFactoryNew()
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

sequence = asset_tools.create_asset(
    asset_name="LS_PCG_BoxMask",
    package_path="/Game/Cinematics",
    asset_class=unreal.LevelSequence,
    factory=factory
)

# Find BP_PCG_BoxMask actor
actors = unreal.EditorLevelLibrary.get_all_level_actors()
pcg_actor = None

for actor in actors:
    if 'BP_PCG_BoxMask' in actor.get_name():
        pcg_actor = actor
        break

# Add as possessable
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, pcg_actor)

# Add property tracks
properties = ["BoxCenterX", "BoxCenterY", "BoxCenterZ", "BoxRadius"]
tracks = {}

for prop in properties:
    track = binding.add_track(unreal.MovieSceneFloatTrack)
    try:
        track.set_property_name_and_path(prop, prop)
    except:
        pass  # Silent Execution
    tracks[prop] = track

# Add sections
sections = {}
for prop, track in tracks.items():
    section = track.add_section()
    section.set_range(0, 300)
    sections[prop] = section

# Add keyframes
# BoxCenterX: Sweep animation
section_x = sections["BoxCenterX"]
channels_x = unreal.MovieSceneSectionExtensions.get_channels_by_type(
    section_x, unreal.MovieSceneScriptingFloatChannel
)
channel_x = channels_x[0]
channel_x.add_key(unreal.FrameNumber(0), -2000.0)
channel_x.add_key(unreal.FrameNumber(150), 2000.0)

# BoxRadius: Expansion animation
section_radius = sections["BoxRadius"]
channels_radius = unreal.MovieSceneSectionExtensions.get_channels_by_type(
    section_radius, unreal.MovieSceneScriptingFloatChannel
)
channel_radius = channels_radius[0]
channel_radius.add_key(unreal.FrameNumber(0), 500.0)
channel_radius.add_key(unreal.FrameNumber(150), 2000.0)

# Open in Sequencer
try:
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
except:
    pass

print("[OK] PCG animation sequence created!")
```

### Result

- 300 frame animation
- Box mask sweeps left to right
- Radius expands as it moves
- PCG regenerates at each frame (with event track - manual setup)

### Manual Steps Required

1. Add PCG Component event track
2. Bind "Generate" event with Force + Call in Editor
3. Extend event repeater to cover timeline

---

## Camera Animation Example

**Use Case:** Creating a cinematic camera move

### Scenario

Camera starts at origin, moves forward and up, then returns.

### Complete Script

```python
import unreal

# Create sequence
sequence = create_level_sequence("LS_CameraMove")

# Spawn camera actor
camera_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CameraActor,
    unreal.Vector(0, 0, 0)
)

# Add to sequence
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, camera_actor)

# Add transform track
transform_track = binding.add_track(unreal.MovieScene3DTransformTrack)

# Add section
section = transform_track.add_section()
section.set_range(0, 600)

# Get channels
channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
    section,
    unreal.MovieSceneScriptingFloatChannel
)

# Location channels (X=0, Y=1, Z=2)
x_channel = channels[0]
y_channel = channels[1]
z_channel = channels[2]

# X: Move forward
x_channel.add_key(unreal.FrameNumber(0), 0.0)
x_channel.add_key(unreal.FrameNumber(300), 2000.0)
x_channel.add_key(unreal.FrameNumber(600), 0.0)

# Z: Rise and fall
z_channel.add_key(unreal.FrameNumber(0), 100.0)
z_channel.add_key(unreal.FrameNumber(300), 500.0)
z_channel.add_key(unreal.FrameNumber(600), 100.0)

# Rotation channels (Roll=3, Pitch=4, Yaw=5)
pitch_channel = channels[4]

# Pitch: Look down slightly at peak
pitch_channel.add_key(unreal.FrameNumber(0), 0.0)
pitch_channel.add_key(unreal.FrameNumber(300), -15.0)
pitch_channel.add_key(unreal.FrameNumber(600), 0.0)

print("[OK] Camera animation created!")
```

### Result

- 600 frame (20 second at 30fps) camera move
- Forward motion with vertical arc
- Slight pitch adjustment at peak
- Smooth return to origin

---

## Transform Animation Example

**Use Case:** Complete transform animation (location, rotation, scale)

### Scenario

Cube performs complex transformation over 300 frames.

### Using High-Level Helper

```python
from scripts.sequencer_automation import create_transform_animation

seq = create_transform_animation(
    "LS_TransformDemo",
    "Cube",
    location_keyframes={
        "X": [(0, 0.0), (150, 1000.0), (300, 0.0)],
        "Y": [(0, 0.0), (100, 500.0), (200, -500.0), (300, 0.0)],
        "Z": [(0, 0.0), (150, 800.0), (300, 0.0)]
    },
    rotation_keyframes={
        "Roll": [(0, 0.0), (300, 360.0)],
        "Pitch": [(0, 0.0), (150, 45.0), (300, 0.0)],
        "Yaw": [(0, 0.0), (300, 720.0)]
    },
    scale_keyframes={
        "X": [(0, 1.0), (150, 2.0), (300, 1.0)],
        "Y": [(0, 1.0), (150, 2.0), (300, 1.0)],
        "Z": [(0, 1.0), (150, 2.0), (300, 1.0)]
    }
)
```

### Manual Approach

```python
import unreal

# Create sequence
sequence = create_level_sequence("LS_TransformDemo")

# Add actor
actor = unreal.EditorLevelLibrary.get_actor_reference("Cube")
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, actor)

# Add transform track
transform_track = binding.add_track(unreal.MovieScene3DTransformTrack)

# Add section
section = transform_track.add_section()
section.set_range(0, 300)

# Get all channels
channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
    section,
    unreal.MovieSceneScriptingFloatChannel
)

# Location (0-2)
x_loc = channels[0]
y_loc = channels[1]
z_loc = channels[2]

# Rotation (3-5)
roll = channels[3]
pitch = channels[4]
yaw = channels[5]

# Scale (6-8)
x_scale = channels[6]
y_scale = channels[7]
z_scale = channels[8]

# Keyframe location
x_loc.add_key(unreal.FrameNumber(0), 0.0)
x_loc.add_key(unreal.FrameNumber(150), 1000.0)
x_loc.add_key(unreal.FrameNumber(300), 0.0)

# ... (continue for all channels)

print("[OK] Transform animation created!")
```

### Result

- Complex 3D motion path
- Multiple rotation axes
- Scaling effect
- 300 frame choreography

---

## Property Animation Examples

### Material Parameter Animation

```python
import unreal

# Assuming material instance with scalar parameter "Opacity"
sequence = create_level_sequence("LS_MaterialFade")

# Add mesh actor
actor = unreal.EditorLevelLibrary.get_actor_reference("StaticMeshActor")
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, actor)

# Add float track for material parameter
track = binding.add_track(unreal.MovieSceneFloatTrack)

# Note: Material parameter animation may require different approach
# This is EXPERIMENTAL - test in your environment
try:
    track.set_property_name_and_path(
        "StaticMeshComponent.Materials[0].ScalarParameterValue.Opacity",
        "StaticMeshComponent.Materials[0].ScalarParameterValue.Opacity"
    )
except:
    pass

# Add section and keyframes
section = track.add_section()
section.set_range(0, 100)

channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
    section, unreal.MovieSceneScriptingFloatChannel
)

if channels:
    channel = channels[0]
    channel.add_key(unreal.FrameNumber(0), 1.0)   # Fully opaque
    channel.add_key(unreal.FrameNumber(100), 0.0) # Fully transparent
```

### Light Intensity Animation

```python
import unreal

sequence = create_level_sequence("LS_LightFade")

# Add point light
light = unreal.EditorLevelLibrary.get_actor_reference("PointLight")
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, light)

# Add intensity track
track = binding.add_track(unreal.MovieSceneFloatTrack)

try:
    track.set_property_name_and_path("Intensity", "Intensity")
except:
    pass

# Add section
section = track.add_section()
section.set_range(0, 200)

# Get channel
channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
    section, unreal.MovieSceneScriptingFloatChannel
)

channel = channels[0]

# Pulsing light effect
channel.add_key(unreal.FrameNumber(0), 1000.0)
channel.add_key(unreal.FrameNumber(50), 5000.0)
channel.add_key(unreal.FrameNumber(100), 1000.0)
channel.add_key(unreal.FrameNumber(150), 5000.0)
channel.add_key(unreal.FrameNumber(200), 1000.0)
```

### Custom Blueprint Property Animation

```python
import unreal

sequence = create_level_sequence("LS_CustomProperty")

# Add Blueprint actor with exposed float property
actor = unreal.EditorLevelLibrary.get_actor_reference("BP_MyActor")
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, actor)

# Add track for custom property
track = binding.add_track(unreal.MovieSceneFloatTrack)

try:
    # Property name must match Blueprint variable name
    track.set_property_name_and_path("CustomSpeed", "CustomSpeed")
except:
    pass

# Add section
section = track.add_section()
section.set_range(0, 300)

# Get channel
channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
    section, unreal.MovieSceneScriptingFloatChannel
)

channel = channels[0]

# Accelerating speed curve
channel.add_key(unreal.FrameNumber(0), 0.0)
channel.add_key(unreal.FrameNumber(100), 50.0)
channel.add_key(unreal.FrameNumber(200), 150.0)
channel.add_key(unreal.FrameNumber(300), 300.0)
```

---

## Multi-Actor Choreography

**Use Case:** Coordinate multiple actors in single sequence

```python
import unreal

sequence = create_level_sequence("LS_Choreography")

# Add multiple actors
actors = [
    "Cube1",
    "Cube2",
    "Cube3"
]

bindings = []
for actor_name in actors:
    actor = unreal.EditorLevelLibrary.get_actor_reference(actor_name)
    binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, actor)
    bindings.append(binding)

# Animate each with offset timing
for i, binding in enumerate(bindings):
    # Add transform track
    track = binding.add_track(unreal.MovieScene3DTransformTrack)

    # Add section
    section = track.add_section()
    section.set_range(0, 300)

    # Get Z channel
    channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
        section, unreal.MovieSceneScriptingFloatChannel
    )
    z_channel = channels[2]

    # Offset animation by 30 frames per actor
    offset = i * 30
    z_channel.add_key(unreal.FrameNumber(0 + offset), 0.0)
    z_channel.add_key(unreal.FrameNumber(100 + offset), 500.0)
    z_channel.add_key(unreal.FrameNumber(200 + offset), 0.0)

print("[OK] Choreographed 3 actors with cascading animation!")
```

---

## Notes

**Silent Execution:**
- Many examples use `try/except` for `set_property_name_and_path()`
- Timeouts are NORMAL - operations complete in background
- Verify results in separate script execution

**Property Paths:**
- Single properties: `"PropertyName"`
- Nested properties: `"Parent.Child"`
- Component properties: `"ComponentName.PropertyName"`
- Array elements: `"ArrayName[0].PropertyName"`

**Channel Indexing:**
For `MovieScene3DTransformTrack`:
- 0-2: Location (X, Y, Z)
- 3-5: Rotation (Roll, Pitch, Yaw)
- 6-8: Scale (X, Y, Z)

**Interpolation:**
- `LINEAR` - Default, straight lines
- `CUBIC` - Smooth curves
- `CONSTANT` - Steps
- `AUTO` - Automatic tangents
