---
name: blender-animation
description: Keyframe animation, rigging, constraints, and armatures in Blender. Use for animation, rigging, camera movement, or when user mentions "animate," "keyframe," "rig," or "armature."
allowed-tools: Read,Write
---

# Blender Animation Skill

**Version:** 2.0.0
**Last Updated:** 2026-06-10
**Dependencies:** Blender 5.1+

---

## Animation System Status (5.1+)

**All core animation APIs are stable — no breaking changes from 4.x to 5.1.**

Validated: `obj.keyframe_insert()`, F-curve access, armature creation, constraints, shape keys, drivers, NLA system.

---

## QUICK START

### Basic Object Animation

```python
import bpy

# Create cube via direct API
mesh = bpy.data.meshes.new("AnimatedMesh")
vertices = [
    (-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),
    (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1)
]
faces = [
    [0,1,2,3], [4,5,6,7], [0,1,5,4],
    [2,3,7,6], [0,3,7,4], [1,2,6,5]
]
mesh.from_pydata(vertices, [], faces)
obj = bpy.data.objects.new("AnimatedCube", mesh)
bpy.context.collection.objects.link(obj)

# Animate location
scene = bpy.context.scene

scene.frame_set(1)
obj.location = (0, 0, 0)
obj.keyframe_insert(data_path="location", frame=1)

scene.frame_set(50)
obj.location = (5, 0, 0)
obj.keyframe_insert(data_path="location", frame=50)

scene.frame_set(100)
obj.location = (5, 5, 0)
obj.keyframe_insert(data_path="location", frame=100)

print(f"Created animation with {len(obj.animation_data.action.fcurves)} F-curves")
```

---

## STANDARD WORKFLOWS

### Workflow 1: Camera Animation with Constraints

**Use When:** Creating animated camera for cinematics or previews

```python
import bpy

camera_data = bpy.data.cameras.new("AnimatedCamera")
camera_obj = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera_obj)

# Create target object
target_obj = bpy.data.objects.get("TargetObject")  # Must exist

# Add Track-To constraint
track_constraint = camera_obj.constraints.new(type='TRACK_TO')
track_constraint.target = target_obj
track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
track_constraint.up_axis = 'UP_Y'

# Animate camera position
scene = bpy.context.scene

scene.frame_set(1)
camera_obj.location = (10, -10, 5)
camera_obj.keyframe_insert(data_path="location", frame=1)

scene.frame_set(50)
camera_obj.location = (0, -15, 8)
camera_obj.keyframe_insert(data_path="location", frame=50)

scene.frame_set(100)
camera_obj.location = (-10, -10, 5)
camera_obj.keyframe_insert(data_path="location", frame=100)
```

---

### Workflow 2: Character Armature Rigging

**Use When:** Setting up character animation with IK/FK controls

```python
import bpy

armature_data = bpy.data.armatures.new("CharacterRig")
armature_obj = bpy.data.objects.new("Armature", armature_data)
bpy.context.collection.objects.link(armature_obj)

# NOTE: Bone creation in edit mode is easiest in Blender UI.
# For scripted bone creation, set active + switch mode:
bpy.context.view_layer.objects.active = armature_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = armature_data.edit_bones
hip = edit_bones.new("Hip")
hip.head = (0, 0, 0)
hip.tail = (0, 0, 1)

spine = edit_bones.new("Spine")
spine.head = (0, 0, 1)
spine.tail = (0, 0, 2)
spine.parent = hip

bpy.ops.object.mode_set(mode='OBJECT')

# Add IK constraint in pose mode
bpy.ops.object.mode_set(mode='POSE')
pose_bone = armature_obj.pose.bones.get("Spine")
if pose_bone:
    ik = pose_bone.constraints.new(type='IK')
    ik.chain_count = 2

bpy.ops.object.mode_set(mode='OBJECT')
```

---

### Workflow 3: Shape Key Animation (Facial Expressions)

**Use When:** Animating mesh morphs for facial expressions or deformations

```python
import bpy

mesh_obj = bpy.data.objects.get("CharacterHead")  # Must exist

# Add basis shape key
basis = mesh_obj.shape_key_add(name="Basis")

# Add expression shape keys
smile = mesh_obj.shape_key_add(name="Smile")
blink = mesh_obj.shape_key_add(name="Blink")

# Animate shape key values
scene = bpy.context.scene

scene.frame_set(1)
smile.value = 0.0
smile.keyframe_insert(data_path="value", frame=1)

scene.frame_set(12)
smile.value = 1.0
smile.keyframe_insert(data_path="value", frame=12)

scene.frame_set(24)
smile.value = 0.0
smile.keyframe_insert(data_path="value", frame=24)
```

---

## API REFERENCE

### Keyframe Operations

```python
import bpy

# Insert keyframe
obj.keyframe_insert(data_path="location", frame=10, index=-1)
# data_path: "location", "rotation_euler", "scale", etc.
# index: -1 for all axes, 0/1/2 for X/Y/Z

# Delete keyframe
obj.keyframe_delete(data_path="location", frame=10, index=-1)

# Create animation data manually
anim_data = obj.animation_data_create()
```

### F-Curve Access

```python
import bpy

# Safe access pattern
if obj.animation_data and obj.animation_data.action:
    fcurves = obj.animation_data.action.fcurves
    for fc in fcurves:
        print(f"{fc.data_path}[{fc.array_index}]: {len(fc.keyframe_points)} keyframes")

# Insert keyframe point directly
fcurve = obj.animation_data.action.fcurves[0]
point = fcurve.keyframe_points.insert(frame=25, value=2.5)
point.interpolation = 'BEZIER'  # or 'LINEAR', 'CONSTANT'
```

### Constraints

```python
import bpy

# IK constraint
pose_bone = armature_obj.pose.bones["BoneName"]
ik = pose_bone.constraints.new(type='IK')
ik.target = target_obj
ik.subtarget = "TargetBone"
ik.chain_count = 2

# Copy Location
copy_loc = pose_bone.constraints.new(type='COPY_LOCATION')
copy_loc.target = target_obj
```

---

## TROUBLESHOOTING

### Keyframe Not Inserted

```python
import bpy

# Verify property path exists
if hasattr(obj, "location"):
    result = obj.keyframe_insert(data_path="location", frame=1)
    print(f"Keyframe inserted: {result}")

# Check animation data was created
if obj.animation_data and obj.animation_data.action:
    print(f"F-curves: {len(obj.animation_data.action.fcurves)}")
else:
    print("No animation data — keyframe_insert may have failed")
```

### Constraint Not Working

```python
import bpy

# Verify target exists
target_obj = bpy.data.objects.get("TargetObject")
if not target_obj:
    print("Error: Target object not found")
else:
    constraint = pose_bone.constraints.new(type='IK')
    constraint.target = target_obj
    # Verify subtarget bone
    if "TargetBone" in target_obj.pose.bones:
        constraint.subtarget = "TargetBone"

# Check constraints are active
for c in pose_bone.constraints:
    print(f"{c.name}: muted={c.mute}")
```

---

## VALIDATION CHECKLIST

- [ ] Animation data exists (`obj.animation_data is not None`)
- [ ] F-curves created (`len(action.fcurves) > 0`)
- [ ] Frame range set (`scene.frame_start`, `frame_end`)
- [ ] Keyframes at expected frames
- [ ] Constraints have valid targets
- [ ] Timeline playback works

---

## VERSION HISTORY

**v2.0.0** (2026-06-10) - MCP migration
- Removed HTTP Bridge connection steps and curl health-check
- Removed `import requests` / `requests.post()` wrappers
- Added `import bpy` to all code blocks
- Updated target: Blender 5.1+
- Workflow 2 now shows full operator-based bone creation (valid with MCP context)

**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+
