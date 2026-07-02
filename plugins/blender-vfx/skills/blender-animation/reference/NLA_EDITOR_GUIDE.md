# NLA Editor Guide - Non-Linear Animation

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Skill:** blender-animation
**Dependencies:** Blender 4.5.0+, official Blender MCP

---

## 🎯 SCOPE

This reference covers the **Non-Linear Animation (NLA) Editor**, Blender's system for layering, blending, and managing multiple animation actions on a single armature. All APIs are **100% STABLE** across Blender 4.2 → 4.5.0.

**Audience:** Animators familiar with keyframe animation who need to manage complex animation libraries, blend cycles, or create procedural animation systems.

**Topics Covered:**
- NLA track and strip creation
- Action blending and mixing
- Strip timing and scaling
- Animation layering and influence
- Sync points and markers
- Batch animation management
- Game engine animation export

---

## 🚨 CRITICAL: HTTP Bridge Compatibility

**100% STABLE API - NO VERSION CHECKING REQUIRED**

All NLA APIs documented here are validated stable (see `ANIMATION_SYSTEM_VALIDATION_REPORT.md`).

**HTTP Bridge Pattern:**
```python
import requests
# Execute via the Blender MCP tool: execute_blender_code
code = """
import bpy
# NLA code here (direct API only, no bpy.ops.nla operators)
"""
response = requests.post(url, json={"code": code})
```

**Critical Limitation:** NLA operators (`bpy.ops.nla.*`) fail in HTTP Bridge. Use direct API (`obj.animation_data.nla_tracks.new()`) exclusively.

---

## 📚 TABLE OF CONTENTS

1. [NLA Fundamentals](#nla-fundamentals)
2. [Creating NLA Tracks and Strips](#creating-nla-tracks-and-strips)
3. [Action Blending](#action-blending)
4. [Strip Timing and Scaling](#strip-timing-and-scaling)
5. [Animation Layering](#animation-layering)
6. [Sync Points and Markers](#sync-points-and-markers)
7. [Batch Animation Management](#batch-animation-management)
8. [Game Engine Export](#game-engine-export)
9. [Troubleshooting](#troubleshooting)

---

## NLA FUNDAMENTALS

### What is the NLA Editor?

**Concept:** The NLA (Non-Linear Animation) Editor treats animation actions as reusable clips that can be:
- Played in any order (non-linear)
- Blended together (multiple actions on same object)
- Repeated and scaled (cycles, slow-motion)
- Layered with different influences (additive animation)

**Hierarchy:**
```
Object (e.g., Armature)
└── animation_data
    ├── action (current/active action being edited)
    └── nla_tracks (list of NLA tracks)
        ├── Track 0 (e.g., "Locomotion")
        │   ├── Strip 0 (e.g., "Walk Cycle", frames 1-50)
        │   └── Strip 1 (e.g., "Run Cycle", frames 51-100)
        └── Track 1 (e.g., "Upper Body")
            └── Strip 0 (e.g., "Wave", frames 10-30)
```

**Key Difference from Dopesheet:**
- **Dopesheet/Action Editor:** Edit individual keyframes in one action
- **NLA Editor:** Arrange multiple actions in time, blend them, repeat them

---

### NLA Workflow Visualization

**ASCII Timeline:**
```
Frame:     1   10   20   30   40   50   60   70   80   90  100
           |----|----|----|----|----|----|----|----|----|----|
Track 0:   [====Walk====]    [===Run===]         [==Idle==]
Track 1:        [Wave]             [Punch]
Track 2:   [=============Breathing (influence 0.3)==========]

Legend:
[===]  = NLA Strip (action playback)
Track 0 = Base locomotion (influence 1.0, Replace mode)
Track 1 = Upper body actions (influence 1.0, Combine mode)
Track 2 = Subtle overlay (influence 0.3, Combine mode)
```

**Result:** Character walks (frames 1-20), waves while walking (frames 10-20), runs (frames 30-50), punches while running (frames 40-50), idles (frames 70-90). Breathing overlay affects entire timeline at 30% strength.

---

## CREATING NLA TRACKS AND STRIPS

### Creating First NLA Track

**Goal:** Convert action editor action into NLA strip

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# Ensure animation data exists
if not armature_obj.animation_data:
    armature_obj.animation_data_create()

# Create action (if not exists)
action = bpy.data.actions.get("WalkCycle")
if not action:
    action = bpy.data.actions.new("WalkCycle")
    armature_obj.animation_data.action = action

    # Add some keyframes (example)
    scene = bpy.context.scene
    root_bone = armature_obj.pose.bones["Root"]
    scene.frame_set(1)
    root_bone.location.y = 0
    root_bone.keyframe_insert(data_path="location", frame=1)
    scene.frame_set(24)
    root_bone.location.y = 2
    root_bone.keyframe_insert(data_path="location", frame=24)

# "Push down" action to NLA (STABLE API)
nla_track = armature_obj.animation_data.nla_tracks.new()
nla_track.name = "Locomotion"

# Create strip from action
strip = nla_track.strips.new(
    name="Walk",
    start=1,       # Start frame in timeline
    action=action  # Action to use
)

# Clear active action (now controlled by NLA)
armature_obj.animation_data.action = None

print(f"NLA track '{nla_track.name}' created with strip '{strip.name}'")
print(f"  Strip frames: {strip.frame_start} - {strip.frame_end}")
```

**Result:** Action "WalkCycle" now plays as NLA strip from frame 1-24.

---

### Adding Multiple Strips to Track

**Goal:** Sequence multiple actions on one track (e.g., walk → run → idle)

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
nla_track = armature_obj.animation_data.nla_tracks["Locomotion"]

# Create actions (or get existing)
actions = {
    "Walk": bpy.data.actions.get("WalkCycle"),
    "Run": bpy.data.actions.get("RunCycle"),
    "Idle": bpy.data.actions.get("IdleCycle")
}

# Add strips sequentially
frame_cursor = 1

for name, action in actions.items():
    if not action:
        print(f"Warning: Action '{name}' not found, skipping")
        continue

    strip = nla_track.strips.new(
        name=name,
        start=frame_cursor,
        action=action
    )

    print(f"Strip '{strip.name}': frames {strip.frame_start} - {strip.frame_end}")

    # Move cursor to end of this strip (+1 frame gap)
    frame_cursor = strip.frame_end + 1

print(f"Track '{nla_track.name}' has {len(nla_track.strips)} strips")
```

**Timeline Result:**
```
Frame:   1        24  25       48  49       72
         |---------|---|---------|---|---------|
Track:   [==Walk==]   [===Run===]   [==Idle==]
```

---

### Creating Layered Tracks

**Goal:** Add second track for upper-body actions that play simultaneously with locomotion

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# Create second track
upper_track = armature_obj.animation_data.nla_tracks.new()
upper_track.name = "UpperBody"

# Get action
wave_action = bpy.data.actions.get("Wave")
if wave_action:
    wave_strip = upper_track.strips.new(
        name="Wave",
        start=10,  # Starts while walking (frame 10)
        action=wave_action
    )

    # Set blend mode to Combine (adds to base animation)
    wave_strip.blend_type = 'COMBINE'
    wave_strip.influence = 1.0

    print(f"Upper body strip added: '{wave_strip.name}' (frames {wave_strip.frame_start}-{wave_strip.frame_end})")

# Track order matters: bottom tracks evaluated first
# To reorder: move tracks in list (see Troubleshooting section)
```

**Timeline Result:**
```
Frame:      1        10   20   24
            |---------|----|----|
Locomotion: [=====Walk=====]
UpperBody:           [Wave]

Result: Frames 10-20 = Walk + Wave blended
```

---

## ACTION BLENDING

### Blend Modes Overview

**Blend Types:**
```python
'REPLACE'  # Strip replaces base animation (default)
'COMBINE'  # Strip adds to base animation (additive)
'ADD'      # Deprecated alias for COMBINE (use COMBINE)
'MULTIPLY' # Strip multiplies base animation (scaling effect)
```

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["UpperBody"].strips["Wave"]

# Set blend mode
strip.blend_type = 'COMBINE'  # Additive blending
strip.influence = 0.5  # 50% strength

print(f"Strip '{strip.name}': blend={strip.blend_type}, influence={strip.influence}")
```

**Visual Comparison:**
```
Base Animation: Root bone Y location = 2.0 (from walk)
Overlay Animation: Root bone Y location = 1.0 (from wave)

REPLACE (influence 1.0):
  Result = 1.0 (overlay replaces base)

COMBINE (influence 1.0):
  Result = 2.0 + 1.0 = 3.0 (overlay adds to base)

COMBINE (influence 0.5):
  Result = 2.0 + (1.0 * 0.5) = 2.5 (50% of overlay added)
```

---

### Influence Curves

**Goal:** Fade strip in/out over time using F-curves

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["UpperBody"].strips["Wave"]

# Enable influence animation
strip.use_animated_influence = True

# Create F-curve for influence
# Access via strip's NLA strip FCurves (special location)
# NOTE: This requires NLA strip to be selected (operator-dependent)
# Workaround: Manually create keyframes on influence property

# Add keyframes to influence (requires direct access to NLA strip data)
# This is complex in HTTP Bridge - use Blender UI or set constant influence

# Set influence curve points (conceptual - requires UI access)
# Frame 1: influence = 0.0 (invisible)
# Frame 10: influence = 1.0 (full strength)
# Frame 20: influence = 1.0 (hold)
# Frame 25: influence = 0.0 (fade out)

print(f"Strip influence animation enabled: {strip.use_animated_influence}")
```

**Timeline Visualization:**
```
Frame:     1    5    10   15   20   25
           |----|----|----|----|----|
Influence: 0.0  0.5  1.0  1.0  1.0  0.0
Strip:          [===Wave===]
Effect:    (fade in)(full)(fade out)
```

**Workaround (HTTP Bridge):**
```python
# Set linear ramp via strip properties (no F-curve needed)
strip.use_auto_blend = True  # Auto fade-in/out
strip.blend_in = 5   # 5 frames fade-in
strip.blend_out = 5  # 5 frames fade-out

print(f"Auto blend: in={strip.blend_in}, out={strip.blend_out}")
```

---

### Extrapolation Modes

**Goal:** Define strip behavior outside its frame range

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# Extrapolation options
strip.extrapolation = 'HOLD'  # Default options below

print(f"Strip extrapolation: {strip.extrapolation}")
```

**Extrapolation Types:**
```
'NOTHING'       # No effect outside strip range
'HOLD'          # Hold first/last frame values
'HOLD_FORWARD'  # Hold last frame forward in time only
```

**Timeline Example:**
```
Action frames: 1-24 (walk cycle)
Strip range: Frames 1-50

Extrapolation = 'HOLD':
  Frames 1-24: Play walk cycle
  Frames 25-50: Hold frame 24 pose (frozen)

Extrapolation = 'NOTHING':
  Frames 1-24: Play walk cycle
  Frames 25-50: No animation (default pose)
```

---

## STRIP TIMING AND SCALING

### Time Scaling (Slow Motion / Speed Up)

**Goal:** Play action faster or slower without re-timing keyframes

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# Original: Action is 24 frames, plays over 24 timeline frames (1:1)
print(f"Original: frame_start={strip.frame_start}, frame_end={strip.frame_end}")
print(f"  Action length: {strip.action.frame_range[1] - strip.action.frame_range[0]} frames")

# Speed up 2x: Play 24-frame action in 12 timeline frames
strip.scale = 2.0  # 2x speed
strip.frame_end = strip.frame_start + (strip.action.frame_range[1] - strip.action.frame_range[0]) / strip.scale

print(f"2x speed: frame_start={strip.frame_start}, frame_end={strip.frame_end}, scale={strip.scale}")

# Slow motion 0.5x: Play 24-frame action in 48 timeline frames
strip.scale = 0.5  # 0.5x speed (half speed)
strip.frame_end = strip.frame_start + (strip.action.frame_range[1] - strip.action.frame_range[0]) / strip.scale

print(f"0.5x speed: frame_start={strip.frame_start}, frame_end={strip.frame_end}, scale={strip.scale}")
```

**Scale Calculation:**
```
Timeline frames = Action frames / Scale

Example:
  Action = 24 frames
  Scale = 2.0 → Timeline = 24 / 2.0 = 12 frames (2x faster)
  Scale = 0.5 → Timeline = 24 / 0.5 = 48 frames (2x slower)
  Scale = 1.0 → Timeline = 24 / 1.0 = 24 frames (normal)
```

---

### Repeating Strips (Cycles)

**Goal:** Loop action multiple times without duplicating strips

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# Enable repeat
strip.use_animated_time_cyclic = False  # Simple repeat (not time-remapped)
strip.repeat = 3.5  # Play action 3.5 times

# Calculate new strip end
action_length = strip.action.frame_range[1] - strip.action.frame_range[0]
strip.frame_end = strip.frame_start + (action_length * strip.repeat)

print(f"Strip repeats {strip.repeat} times: frames {strip.frame_start}-{strip.frame_end}")
```

**Timeline Example:**
```
Action: 24 frames
Repeat: 3.5

Frame:   1        24  25       48  49       72  73       84
         |---------|---|---------|---|---------|---|------|
Strip:   [==Cycle==][==Cycle==][==Cycle==][=Half=]

Result: 3 full cycles + 12 frames (half of 24)
```

---

### Action Time Remapping

**Goal:** Play different parts of action at different speeds (e.g., speed up middle, slow end)

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# Enable animated time (allows F-curve control)
strip.use_animated_time = True

# Access strip's time F-curve (complex - requires NLA UI access)
# Workaround: Use strip scale for uniform time changes (see above)

# Manual time curve setup (conceptual):
# Frame 1 (timeline) → Frame 1 (action) - normal speed
# Frame 12 (timeline) → Frame 18 (action) - 1.5x speed (6 frames skipped)
# Frame 24 (timeline) → Frame 24 (action) - 0.5x speed (slow ending)

print(f"Animated time enabled: {strip.use_animated_time}")
```

**Note:** Action time remapping via F-curves is difficult in HTTP Bridge. Use `strip.scale` for uniform timing, or edit in Blender UI.

---

### Strip Reversal

**Goal:** Play action backwards

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# Reverse playback
strip.use_reverse = True

print(f"Strip '{strip.name}' reversed: {strip.use_reverse}")
```

**Timeline Result:**
```
Forward (use_reverse=False):
  Frame 1 → Action frame 1
  Frame 12 → Action frame 12
  Frame 24 → Action frame 24

Reverse (use_reverse=True):
  Frame 1 → Action frame 24
  Frame 12 → Action frame 12
  Frame 24 → Action frame 1
```

---

## ANIMATION LAYERING

### Additive Upper Body Animation

**Goal:** Add arm wave on top of full-body walk without affecting legs

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# Base layer: Full-body walk
base_track = armature_obj.animation_data.nla_tracks["Locomotion"]
walk_strip = base_track.strips["Walk"]
walk_strip.blend_type = 'REPLACE'  # Base animation

# Additive layer: Upper body wave
upper_track = armature_obj.animation_data.nla_tracks.new()
upper_track.name = "Additive_Upper"

wave_action = bpy.data.actions.get("Wave")
wave_strip = upper_track.strips.new(name="Wave", start=10, action=wave_action)
wave_strip.blend_type = 'COMBINE'  # Adds to base
wave_strip.influence = 1.0

# Key: Wave action should only animate upper body bones
# (arm, shoulder), leaving leg keyframes absent

print("Additive layering configured:")
print(f"  Base: {walk_strip.name} (REPLACE)")
print(f"  Overlay: {wave_strip.name} (COMBINE, influence={wave_strip.influence})")
```

**Best Practice:** Additive actions should only keyframe bones they affect. If wave action has leg keyframes, they'll add to base walk (causing double movement).

---

### Track Muting and Soloing

**Goal:** Temporarily disable tracks for testing or performance

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# Mute track (disable all strips)
upper_track = armature_obj.animation_data.nla_tracks["Additive_Upper"]
upper_track.mute = True
print(f"Track '{upper_track.name}' muted: {upper_track.mute}")

# Solo track (mute all others)
base_track = armature_obj.animation_data.nla_tracks["Locomotion"]
base_track.is_solo = True  # Only this track plays
print(f"Track '{base_track.name}' solo: {base_track.is_solo}")

# Unmute all
for track in armature_obj.animation_data.nla_tracks:
    track.mute = False
    track.is_solo = False
```

---

### Influence Blending Between Tracks

**Goal:** Blend track 1 into track 2 over time (e.g., transition walk to run)

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# Track 0: Walk (full influence frames 1-30, fade out 30-40)
walk_track = armature_obj.animation_data.nla_tracks["Locomotion"]
walk_strip = walk_track.strips["Walk"]
walk_strip.use_auto_blend = True
walk_strip.blend_in = 0
walk_strip.blend_out = 10  # Fade out over 10 frames

# Track 1: Run (fade in frames 30-40, full influence 40+)
run_track = armature_obj.animation_data.nla_tracks.new()
run_track.name = "Run"
run_action = bpy.data.actions.get("RunCycle")
run_strip = run_track.strips.new(name="Run", start=30, action=run_action)
run_strip.use_auto_blend = True
run_strip.blend_in = 10  # Fade in over 10 frames
run_strip.blend_out = 0

print("Cross-fade configured:")
print(f"  Walk: fade out at frame {walk_strip.frame_end - walk_strip.blend_out}")
print(f"  Run: fade in at frame {run_strip.frame_start}")
```

**Timeline Visualization:**
```
Frame:   1        20   30        40   50
         |---------|----|---------|----|
Walk:    [=======100%======][Fade]
Run:                    [Fade][==100%==]

Frames 30-40: Walk influence 100%→0%, Run influence 0%→100%
Result: Smooth transition from walk to run
```

---

## SYNC POINTS AND MARKERS

### Timeline Markers for NLA Events

**Goal:** Mark important animation events (e.g., footsteps, impacts) for syncing strips

**Implementation:**
```python
import bpy

scene = bpy.context.scene

# Add timeline markers
marker1 = scene.timeline_markers.new(name="LeftFoot_Contact", frame=6)
marker2 = scene.timeline_markers.new(name="RightFoot_Contact", frame=18)

print(f"Created markers:")
print(f"  {marker1.name} at frame {marker1.frame}")
print(f"  {marker2.name} at frame {marker2.frame}")

# Use markers to align strips
armature_obj = bpy.data.objects["Armature"]
walk_strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# Offset strip to align action frame 6 (foot contact) with timeline frame 10
action_contact_frame = 6
timeline_target_frame = 10
walk_strip.frame_start = timeline_target_frame - action_contact_frame

print(f"Strip aligned: action frame {action_contact_frame} → timeline frame {timeline_target_frame}")
```

---

### Action Pose Markers (Sync Points)

**Goal:** Define sync points within action (e.g., "Contact", "Passing", "Up") for precise alignment

**Implementation:**
```python
import bpy

action = bpy.data.actions["WalkCycle"]

# Add pose markers to action
marker1 = action.pose_markers.new(name="Contact_L")
marker1.frame = 1

marker2 = action.pose_markers.new(name="Down_L")
marker2.frame = 6

marker3 = action.pose_markers.new(name="Passing")
marker3.frame = 12

marker4 = action.pose_markers.new(name="Contact_R")
marker4.frame = 18

marker5 = action.pose_markers.new(name="Down_R")
marker5.frame = 24

print(f"Action '{action.name}' has {len(action.pose_markers)} pose markers:")
for marker in action.pose_markers:
    print(f"  {marker.name} at frame {marker.frame}")
```

**Usage:** When aligning strips, pose markers help identify equivalent frames across different actions (e.g., align "Contact_L" of walk with "Contact_L" of run).

---

### Strip Sync Length

**Goal:** Automatically adjust strip length to match timeline duration (not action duration)

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# Sync strip to specific timeline length
desired_timeline_length = 50  # frames

# Calculate required scale
action_length = strip.action.frame_range[1] - strip.action.frame_range[0]
strip.scale = action_length / desired_timeline_length

strip.frame_end = strip.frame_start + desired_timeline_length

print(f"Strip synced to {desired_timeline_length} frames (scale={strip.scale:.2f})")
```

---

## BATCH ANIMATION MANAGEMENT

### Listing All Actions

**Goal:** Inventory all actions in .blend file for NLA organization

**Implementation:**
```python
import bpy

print("All actions in file:")
for action in bpy.data.actions:
    frame_range = action.frame_range
    fcurve_count = len(action.fcurves)

    print(f"  {action.name}:")
    print(f"    Frames: {frame_range[0]:.0f} - {frame_range[1]:.0f} ({frame_range[1]-frame_range[0]:.0f} frames)")
    print(f"    F-curves: {fcurve_count}")

    # Check if used in NLA
    used_in_nla = False
    for obj in bpy.data.objects:
        if obj.animation_data:
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.action == action:
                        used_in_nla = True
                        break

    print(f"    In NLA: {'Yes' if used_in_nla else 'No'}")
```

---

### Creating NLA Library from Action List

**Goal:** Batch convert all actions to NLA strips on separate tracks

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# Ensure animation data
if not armature_obj.animation_data:
    armature_obj.animation_data_create()

# Get all actions
actions = [action for action in bpy.data.actions if action.name.startswith("Character_")]

frame_cursor = 1

for action in actions:
    # Create track for each action
    track = armature_obj.animation_data.nla_tracks.new()
    track.name = action.name

    # Add strip
    strip = track.strips.new(name=action.name, start=frame_cursor, action=action)

    print(f"Track '{track.name}': strip at frames {strip.frame_start}-{strip.frame_end}")

    # Offset next action by 10 frames
    frame_cursor = strip.frame_end + 10

print(f"Created {len(armature_obj.animation_data.nla_tracks)} NLA tracks")
```

---

### Baking NLA to Single Action

**Goal:** Flatten all NLA tracks into one action (for export to game engines)

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# NOTE: Baking requires operator - not available in HTTP Bridge
# Use Blender UI: Select armature → Animation menu → Bake Action
# Settings: Visual Keying (enabled), Clear Constraints (disabled), Bake Data (Pose)

# Workaround (conceptual): Sample each frame and insert keyframes
def manual_bake_nla(obj, start_frame, end_frame):
    """Sample NLA output and create keyframed action (slow)"""

    # Create new action for bake
    bake_action = bpy.data.actions.new(f"{obj.name}_Bake")
    obj.animation_data.action = bake_action

    scene = bpy.context.scene

    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)

        # Insert keyframe for all pose bones
        for pose_bone in obj.pose.bones:
            pose_bone.keyframe_insert(data_path="location", frame=frame)
            pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)
            pose_bone.keyframe_insert(data_path="scale", frame=frame)

    print(f"Baked {end_frame - start_frame + 1} frames to action '{bake_action.name}'")
    return bake_action

# Example (WARNING: Very slow for long frame ranges)
# baked = manual_bake_nla(armature_obj, 1, 100)
```

**Note:** Use Blender UI bake operator for production. Manual baking is educational only.

---

## GAME ENGINE EXPORT

### Creating Action Library for Unreal

**Goal:** Organize NLA strips for Unreal Engine animation asset import

**Unreal Requirements:**
1. One FBX per character rig (skeleton)
2. Multiple actions embedded in FBX
3. Each action must be separate (not NLA-baked)

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# Create actions for each animation state
animation_states = {
    "Idle": (1, 60),      # Frame range for idle cycle
    "Walk": (61, 120),
    "Run": (121, 180),
    "Jump": (181, 220)
}

for state_name, (start, end) in animation_states.items():
    # Create action
    action = bpy.data.actions.new(f"Character_{state_name}")

    # Set as active action
    armature_obj.animation_data.action = action

    # Copy keyframes from NLA track (if exists)
    # OR animate manually using keyframe_insert

    print(f"Action created: {action.name} ({start}-{end})")

# FBX export (requires operator - use Blender UI)
# File → Export → FBX
# Settings:
#   - Bake Animation: Enabled
#   - NLA Strips: Enabled (exports each action as separate animation)
#   - All Actions: Enabled
```

**Unreal Import:**
```
1. Import FBX to Unreal
2. Animation: Import dialog shows list of actions
3. Each action becomes separate Animation Sequence asset
4. Link to Animation Blueprint state machine
```

---

### Single-Strip Export (One Animation per FBX)

**Goal:** Export individual NLA strip as standalone FBX animation

**Implementation:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

def export_strip_to_fbx(obj, track_name, strip_name, filepath):
    """Export single NLA strip as FBX animation"""

    # Find strip
    track = obj.animation_data.nla_tracks.get(track_name)
    if not track:
        print(f"Error: Track '{track_name}' not found")
        return

    strip = track.strips.get(strip_name)
    if not strip:
        print(f"Error: Strip '{strip_name}' not found in track '{track_name}'")
        return

    # Set active action to strip's action
    obj.animation_data.action = strip.action

    # Set timeline range to strip range
    scene = bpy.context.scene
    scene.frame_start = int(strip.frame_start)
    scene.frame_end = int(strip.frame_end)

    # Export FBX (requires operator - use Blender UI)
    # bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True, bake_anim=True)

    print(f"Configured export for '{strip_name}' ({strip.frame_start}-{strip.frame_end}) → {filepath}")

# Example
export_strip_to_fbx(
    armature_obj,
    track_name="Locomotion",
    strip_name="Walk",
    filepath="C:/Export/Character_Walk.fbx"
)
```

---

## TROUBLESHOOTING

### Issue: NLA Strip Has No Effect

**Symptoms:** Strip added to track but object doesn't animate

**Causes:**
1. Active action overriding NLA
2. Track muted or strip influence = 0
3. Strip outside timeline playback range

**Solutions:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# Check 1: Clear active action (NLA takes priority when action is None)
if armature_obj.animation_data.action:
    print(f"Active action: {armature_obj.animation_data.action.name}")
    print("Clearing active action to enable NLA")
    armature_obj.animation_data.action = None

# Check 2: Verify track not muted
for track in armature_obj.animation_data.nla_tracks:
    if track.mute:
        print(f"Track '{track.name}' is MUTED")
        track.mute = False

# Check 3: Verify strip influence
for track in armature_obj.animation_data.nla_tracks:
    for strip in track.strips:
        if strip.influence == 0:
            print(f"Strip '{strip.name}' has ZERO influence")
            strip.influence = 1.0

# Check 4: Verify timeline range includes strip
scene = bpy.context.scene
for track in armature_obj.animation_data.nla_tracks:
    for strip in track.strips:
        if strip.frame_end < scene.frame_start or strip.frame_start > scene.frame_end:
            print(f"Strip '{strip.name}' OUTSIDE timeline range ({scene.frame_start}-{scene.frame_end})")
```

---

### Issue: Strips Not Blending Correctly

**Symptoms:** Additive strip replaces base animation instead of adding to it

**Cause:** Strip blend_type set to 'REPLACE' instead of 'COMBINE'

**Solution:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
overlay_strip = armature_obj.animation_data.nla_tracks["UpperBody"].strips["Wave"]

# Check blend type
print(f"Current blend type: {overlay_strip.blend_type}")

# Set to additive
overlay_strip.blend_type = 'COMBINE'
print(f"Changed to: {overlay_strip.blend_type}")

# Verify influence
overlay_strip.influence = 1.0
```

---

### Issue: Strip Timing Incorrect After Scale

**Symptoms:** Strip plays at wrong speed or ends at unexpected frame

**Cause:** `frame_end` not updated after changing `scale`

**Solution:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# Get action length
action_length = strip.action.frame_range[1] - strip.action.frame_range[0]

# Set scale
strip.scale = 2.0  # 2x speed

# Recalculate frame_end
strip.frame_end = strip.frame_start + (action_length / strip.scale)

print(f"Strip timing corrected:")
print(f"  Start: {strip.frame_start}")
print(f"  End: {strip.frame_end}")
print(f"  Duration: {strip.frame_end - strip.frame_start} frames")
print(f"  Scale: {strip.scale}")
```

---

### Issue: Track Order Wrong (Bottom Track Overrides Top)

**Symptoms:** Upper track should override lower track, but doesn't

**Cause:** NLA evaluates tracks bottom-to-top. Top track in UI = last evaluated = highest priority (for REPLACE mode).

**Solution:**
```python
import bpy

armature_obj = bpy.data.objects["Armature"]

# List current track order (index 0 = bottom, higher = top)
print("Current track order (bottom to top):")
for i, track in enumerate(armature_obj.animation_data.nla_tracks):
    print(f"  {i}: {track.name}")

# Move track to different position (requires manual reordering)
# Workaround: Remove and re-add tracks in desired order

# Example: Move "UpperBody" track to top
tracks_data = []
for track in armature_obj.animation_data.nla_tracks:
    strips_data = [(s.name, s.action, s.frame_start, s.blend_type, s.influence) for s in track.strips]
    tracks_data.append((track.name, track.mute, strips_data))

# Clear all tracks
armature_obj.animation_data.nla_tracks.clear()

# Re-add in desired order (UpperBody last = top priority)
for track_name, mute, strips_data in sorted(tracks_data, key=lambda x: 0 if x[0] == "UpperBody" else 1):
    track = armature_obj.animation_data.nla_tracks.new()
    track.name = track_name
    track.mute = mute

    for strip_name, action, start, blend, influence in strips_data:
        strip = track.strips.new(name=strip_name, start=start, action=action)
        strip.blend_type = blend
        strip.influence = influence

print("Tracks reordered")
```

---

### Issue: Can't Edit Strip Properties in HTTP Bridge

**Symptoms:** Need to adjust strip timing/influence but UI access required

**Solution:** All strip properties are accessible via Python API (no operators needed):

```python
import bpy

armature_obj = bpy.data.objects["Armature"]
strip = armature_obj.animation_data.nla_tracks["Locomotion"].strips["Walk"]

# All these are direct property access (HTTP Bridge safe)
strip.frame_start = 10
strip.frame_end = 50
strip.scale = 1.5
strip.repeat = 2.0
strip.influence = 0.8
strip.blend_type = 'COMBINE'
strip.use_reverse = False
strip.use_auto_blend = True
strip.blend_in = 5
strip.blend_out = 5
strip.extrapolation = 'HOLD'
strip.mute = False

print("Strip properties updated (all HTTP Bridge safe)")
```

---

## REFERENCE MATERIALS

**Animation System Validation Report:**
`<workspace>\Blender\blender-ai-compatibility\ANIMATION_SYSTEM_VALIDATION_REPORT.md`

**HTTP Bridge Documentation:**
`<workspace>\Blender\blender-ai-compatibility\CLAUDE.md`

**Blender NLA API Reference (Official):**
https://docs.blender.org/api/current/bpy.types.NlaTrack.html
https://docs.blender.org/api/current/bpy.types.NlaStrip.html

---

## VERSION HISTORY

**v1.0.0** (2025-10-25) - Initial release
- NLA track and strip creation
- Action blending (REPLACE, COMBINE modes)
- Strip timing, scaling, and repeats
- Animation layering techniques
- Timeline markers and pose markers
- Batch animation management
- Game engine export workflows
- Comprehensive troubleshooting

---

**Document Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Last Updated:** 2025-10-25
**Lines:** ~850
**API Stability:** 100% STABLE (Blender 4.2 → 4.5.0)
