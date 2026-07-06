---
name: unreal-sequencer-automation
description: Automate Level Sequence creation, camera cuts, transform animation, and VFX plate workflows via Python. Use when creating sequences, adding tracks, setting keyframes, camera cuts, ImagePlate, or when user mentions "sequencer", "level sequence", "animation", "keyframe", "cinematic", "camera cut", "foreground plate".
allowed-tools: mcp__ue58-mcp__execute_python_code,mcp__ue58-mcp__call_tool
---

# Unreal Sequencer Automation

**Version:** 3.0.0
**Last Updated:** 2026-07-06
**Dependencies:** Unreal Engine 5.8+, UE 5.8 native MCP (HTTP, port 8000)
**Major Updates:** UE 5.8 migration, camera cuts, channel initialization, ImagePlate 100%

---

## CRITICAL DISCOVERIES

### 1. Camera Cut Tracks - SOLVED
**The API that doesn't exist:** `add_camera_cut_track()` - Use generic `add_track()` instead!

### 2. Transform Channels - SOLVED
**Empty channels are NORMAL!** Channels don't exist until you add the first keyframe.

### 3. ImagePlate Python API - DISCOVERED
**BREAKING:** ImagePlate DOES have Python API (`get_plate()`, `set_image_plate()`)

---

## QUICK START: Complete Animated Sequence

```python
# Via mcp__ue58-mcp__execute_python_code
import unreal

# 1. Create Level Sequence
factory = unreal.LevelSequenceFactoryNew()
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

sequence = asset_tools.create_asset(
    asset_name="LS_MyAnimation",
    package_path="/Game/Cinematics",
    asset_class=unreal.LevelSequence,
    factory=factory
)

# 2. Get actor using modern API (not deprecated EditorLevelLibrary)
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
actor = actors[0]

# 3. Add actor as possessable
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, actor)

# 4. Add transform track
track = binding.add_track(unreal.MovieScene3DTransformTrack)

# 5. Add section
section = track.add_section()
section.set_range(0, 300)

# 6. CRITICAL: Initialize channels by adding first key!
# Channels don't exist until you do this
location_z_channel = unreal.MovieSceneSectionExtensions.get_channel_by_name(
    section,
    "Location.Z"
)
location_z_channel.add_key(unreal.FrameNumber(0), 0.0)

# 7. Add remaining keyframes
location_z_channel.add_key(unreal.FrameNumber(150), 500.0)
location_z_channel.add_key(unreal.FrameNumber(300), 0.0)

print(f"Created sequence with {location_z_channel.get_num_keys()} keyframes!")
```

---

## CAMERA CUT TRACKS

### The Correct API Pattern

```python
import unreal

def create_camera_cut(sequence, camera_binding, start_frame, end_frame):
    """
    Creates camera cut track and section.
    IMPORTANT: Use generic add_track(), NOT add_camera_cut_track() (doesn't exist!)
    """
    # Add camera cut track using GENERIC add_track method
    camera_cut_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneCameraCutTrack
    )

    # Add section to track
    section = unreal.MovieSceneTrackExtensions.add_section(camera_cut_track)

    # Cast to correct section type
    camera_cut_section = section.cast(unreal.MovieSceneCameraCutSection)

    # Get camera binding ID
    camera_binding_id = unreal.MovieSceneSequenceExtensions.get_binding_id(
        sequence,
        camera_binding
    )

    # Configure the cut
    camera_cut_section.set_camera_binding_id(camera_binding_id)
    camera_cut_section.set_range(start_frame, end_frame)

    return camera_cut_section
```

### Multi-Camera Cuts Example

```python
def setup_multi_camera_sequence(sequence, cameras_with_ranges):
    """
    Creates camera cuts for multiple cameras.
    cameras_with_ranges: List of (camera_binding, start, end) tuples
    """
    camera_cut_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneCameraCutTrack
    )

    for camera_binding, start, end in cameras_with_ranges:
        section = unreal.MovieSceneTrackExtensions.add_section(camera_cut_track)
        camera_cut_section = section.cast(unreal.MovieSceneCameraCutSection)

        camera_id = unreal.MovieSceneSequenceExtensions.get_binding_id(
            sequence, camera_binding
        )

        camera_cut_section.set_camera_binding_id(camera_id)
        camera_cut_section.set_range(start, end)

    return camera_cut_track
```

---

## TRANSFORM CHANNEL INITIALIZATION

### The Problem: Empty Channels

```python
section = track.add_section()
channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
    section,
    unreal.MovieSceneScriptingFloatChannel
)
print(len(channels))  # Prints: 0 - channels don't exist yet!
```

### The Solution: Lazy Initialization

**Channels don't exist until you add the first keyframe!**

```python
def initialize_transform_channels(transform_section):
    location_x = unreal.MovieSceneSectionExtensions.get_channel_by_name(
        transform_section, "Location.X"
    )
    # Add first key - THIS CREATES ALL 9 CHANNELS!
    location_x.add_key(unreal.FrameNumber(0), 0.0)

    all_channels = unreal.MovieSceneSectionExtensions.get_all_channels(
        transform_section
    )
    print(len(all_channels))  # Prints: 9
    return transform_section
```

### Channel Naming Convention

Transform sections have 9 float channels:

**Location:** `Location.X`, `Location.Y`, `Location.Z`
**Rotation:** `Rotation.X`, `Rotation.Y`, `Rotation.Z`
**Scale:** `Scale.X`, `Scale.Y`, `Scale.Z`

### Complete Transform Animation

```python
def animate_transform(section, component, axis, keyframes):
    channel_name = f"{component}.{axis}"
    channel = unreal.MovieSceneSectionExtensions.get_channel_by_name(
        section, channel_name
    )

    for frame, value in keyframes:
        channel.add_key(
            time=unreal.FrameNumber(frame),
            new_value=value,
            interpolation=unreal.MovieSceneKeyInterpolation.AUTO
        )

    return channel.get_num_keys()

# Example: Bouncing animation
keyframes = [
    (0, 0.0), (75, 500.0), (150, 0.0), (225, 300.0), (300, 0.0)
]
animate_transform(section, "Location", "Z", keyframes)
```

---

## IMAGEPLATE AUTOMATION (VFX WORKFLOWS)

**For complete foreground plate setup, use `unreal-vfx-automation` skill.**

### Integrated Workflow

**Step 1: Create Assets (VFX Automation Skill)**
```python
# Via mcp__ue58-mcp__execute_python_code - run ForegroundPlateSetup script
# See unreal-vfx-automation skill for full details
```

**Step 2: Add to Sequence (This Skill)**
```python
import unreal

sequence = unreal.load_asset('/Game/Sequences/Shot001_Sequence')

# Get camera actor created by VFX automation
world = unreal.EditorLevelLibrary.get_editor_world()
cameras = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CineCameraActor)
camera = [c for c in cameras if "Shot001" in c.get_actor_label()][0]

# Add to sequence
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, camera)

# Add transform track for animation
track = binding.add_track(unreal.MovieScene3DTransformTrack)
section = track.add_section()
section.set_range(0, 300)

animate_transform(section, "Location", "Z", [(0, 0.0), (150, 500.0), (300, 0.0)])
```

---

## MEDIA TRACKS

### Pattern: Generic add_track() + Property Access

```python
import unreal

def add_media_to_sequence(sequence, media_source_path, start_frame=0, end_frame=240):
    media_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneMediaTrack
    )

    section = unreal.MovieSceneTrackExtensions.add_section(media_track)
    media_section = section.cast(unreal.MovieSceneMediaSection)

    media_section.media_source = unreal.load_asset(media_source_path)
    media_section.start_frame_offset = unreal.FrameNumber(0)
    media_section.set_range(
        unreal.FrameNumber(start_frame),
        unreal.FrameNumber(end_frame)
    )

    return media_section
```

**Complete API:** See `reference/media_track_api.md`

---

## TROUBLESHOOTING

**Empty Channels:** Add first key to any channel (lazy initialization)
**Camera Cut Track:** Use add_track(sequence, MovieSceneCameraCutTrack)
**Deprecated API:** Use GameplayStatics.get_all_actors_of_class

---

## VALIDATION CHECKLIST

**After creating sequence:** Check sequence exists, bindings added, tracks/sections created, first keyframe added (initializes channels), camera cuts/ImagePlate configured (if needed), playback works

---

## Reference Documentation

- Complete API: `reference/`
- Media Tracks: `reference/media_track_api.md`
- Code Examples: `examples/examples.md`

---

## Constitutional Compliance

**Article I:** General-purpose scripts (no hardcoded paths)
**Article III:** SKILL.md under 500 lines
**Article IV:** Independent testing (verify_sequence.py)
**Article VI:** Progressive disclosure (3 reference files)

---

## VERSION HISTORY

**v3.0.0** (2026-07-06) - UE 5.8 Migration
- Migrated from community MCP to UE 5.8 native MCP (HTTP, port 8000)
- Updated allowed-tools to mcp__ue58-mcp__execute_python_code + call_tool
- Removed all references to old unreal-mcp server
- Updated VFX workflow to use direct Python via execute_python_code

**v2.2.0** (2025-11-20) - ImagePlate Integration & 100% Coverage
**v2.1.0** (2025-11-20) - Media Track API Added
**v2.0.0** (2025-11-20) - Major API Corrections (camera cuts, channel init)
**v1.0.0** (2025-11-17) - Initial Discovery
