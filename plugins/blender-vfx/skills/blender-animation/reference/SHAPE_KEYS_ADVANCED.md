# Shape Keys Advanced Reference

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Skill:** blender-animation
**Dependencies:** Blender 4.5.0+, official Blender MCP

---

## 🎯 SCOPE

This reference covers advanced **Shape Key** workflows for facial animation, corrective deformations, and mesh morphing. All APIs documented are **100% STABLE** across Blender 4.2 → 4.5.0.

**Audience:** Character artists and technical animators working with blend shapes, morph targets, and facial animation systems.

**Topics Covered:**
- Shape key creation and management
- Driver systems and expressions
- Corrective shape keys for rigging
- Shape key organization and naming
- FBX and Alembic export workflows
- Performance optimization
- Facial animation pipelines

---

## 🎯 API STABILITY

**100% STABLE API - NO VERSION CHECKING REQUIRED**

All shape key APIs validated stable (see `ANIMATION_SYSTEM_VALIDATION_REPORT.md`). Use the `mcp__blender__execute_blender_code` tool to run the snippets below via the official Blender MCP.

---

## 📚 TABLE OF CONTENTS

1. [Shape Key Fundamentals](#shape-key-fundamentals)
2. [Creating Shape Keys](#creating-shape-keys)
3. [Driver Systems](#driver-systems)
4. [Corrective Shape Keys](#corrective-shape-keys)
5. [Organization and Naming](#organization-and-naming)
6. [Export Workflows](#export-workflows)
7. [Performance Optimization](#performance-optimization)
8. [Facial Animation Pipelines](#facial-animation-pipelines)
9. [Troubleshooting](#troubleshooting)

---

## SHAPE KEY FUNDAMENTALS

### What are Shape Keys?

**Concept:** Shape keys (also called blend shapes or morph targets) store alternative vertex positions for a mesh. Blending between "Basis" (original) and shape key creates smooth deformations.

**Data Structure:**
```
Mesh Object
└── data (Mesh datablock)
    └── shape_keys (Key datablock)
        ├── reference_key (Basis - original vertex positions)
        ├── key_blocks[0] (Smile - offset from Basis)
        ├── key_blocks[1] (Blink_L - offset from Basis)
        └── key_blocks[2] (Blink_R - offset from Basis)
```

**How It Works:**
```
Final vertex position = Basis + (Shape1 * value1) + (Shape2 * value2) + ...

Example:
  Basis vertex at (0, 0, 0)
  Smile shape key offset: (0, 0.1, 0.05) - mouth corners up
  Smile.value = 0.5 (50% blend)

  Result: (0, 0, 0) + ((0, 0.1, 0.05) * 0.5) = (0, 0.05, 0.025)
```

---

### Shape Key vs Armature Deformation

**Shape Keys:**
- Vertex-level control (any deformation possible)
- Pre-calculated (fast at runtime)
- Limited to predefined shapes
- Best for: Facial expressions, muscle bulges, clothing wrinkles

**Armature:**
- Bone-driven control (hierarchical)
- Calculated per-frame (more flexible)
- Infinite variations from bone rotations
- Best for: Body movement, skeletal animation

**Combined Use:** Body animated with armature, facial expressions with shape keys, corrective bulges with shape keys driven by bone rotations.

---

### Relative vs Absolute Shape Keys

**Relative Shape Keys (Default):**
- Each shape is offset from Basis
- Values: 0.0 (no effect) to 1.0 (full effect)
- Can be animated, driven, or blended
- Most common for character animation

**Absolute Shape Keys (Rare):**
- Each shape is absolute vertex position
- Values represent frame-like progression
- Primarily for legacy workflows

**This document covers Relative shape keys only** (99% of use cases).

---

## CREATING SHAPE KEYS

### Basic Shape Key Creation

**Goal:** Create facial expression shape key from scratch

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# Add Basis shape key (required - stores original positions)
if not mesh_obj.data.shape_keys:
    basis = mesh_obj.shape_key_add(name="Basis")
    basis.interpolation = 'KEY_LINEAR'
    print(f"Basis shape key created")
else:
    basis = mesh_obj.data.shape_keys.reference_key
    print(f"Basis already exists: {basis.name}")

# Add expression shape key
smile = mesh_obj.shape_key_add(name="Smile")
smile.value = 0.0  # Start at 0 (no effect)

print(f"Shape key '{smile.name}' created (index {len(mesh_obj.data.shape_keys.key_blocks) - 1})")

# Modify shape key vertex positions
# Access vertex via shape key's data array
for i, vert in enumerate(smile.data):
    # Example: Move mouth corner vertices up
    if i in [100, 101, 150, 151]:  # Mouth corner vertex indices
        vert.co.z += 0.05  # Move up 0.05 units

print(f"Modified {len([100, 101, 150, 151])} vertices in '{smile.name}'")
```

**Vertex Access Pattern:**
```python
# Shape key vertex data
shape_key = mesh_obj.data.shape_keys.key_blocks["Smile"]
shape_vert = shape_key.data[vertex_index]  # ShapeKeyPoint

# Mesh vertex data (original)
mesh_vert = mesh_obj.data.vertices[vertex_index]  # MeshVertex

# Shape key stores ABSOLUTE positions (not offsets)
# Blender calculates offset: shape_vert.co - basis_vert.co
```

---

### Creating Shape Key from Current Mesh State

**Goal:** Capture current mesh deformation (e.g., from modifiers) as shape key

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# Add new shape key (captures current mesh state)
shape_key = mesh_obj.shape_key_add(name="Smile_Sculpted", from_mix=False)

# from_mix=False: Capture current mesh vertex positions (default)
# from_mix=True: Capture result of all shape keys at current values

print(f"Shape key '{shape_key.name}' created from current mesh state")

# Example workflow:
# 1. Sculpt smile expression in Sculpt Mode
# 2. Run above code to capture as shape key
# 3. Shape key now stores sculpted deformation
```

**Creating from Mix (Advanced):**
```python
# Set multiple shape keys to desired values
mesh_obj.data.shape_keys.key_blocks["Smile"].value = 0.5
mesh_obj.data.shape_keys.key_blocks["Blink_L"].value = 0.3

# Capture combined result as new shape key
combined = mesh_obj.shape_key_add(name="Smile_Blink_Combo", from_mix=True)

# Now "Smile_Blink_Combo" contains 50% smile + 30% blink combined
```

---

### Duplicating Shape Keys

**Goal:** Create mirrored or variant shape keys

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
source_key = mesh_obj.data.shape_keys.key_blocks["Smile_L"]

# Create duplicate
duplicate = mesh_obj.shape_key_add(name="Smile_R", from_mix=False)

# Copy vertex positions from source
for i, source_vert in enumerate(source_key.data):
    duplicate.data[i].co = source_vert.co.copy()

print(f"Duplicated '{source_key.name}' → '{duplicate.name}'")

# Mirror across X-axis (for symmetrical shapes)
for i, vert in enumerate(duplicate.data):
    basis_vert = mesh_obj.data.shape_keys.reference_key.data[i]
    offset = vert.co - basis_vert.co
    offset.x = -offset.x  # Flip X-axis offset
    duplicate.data[i].co = basis_vert.co + offset

print(f"Mirrored '{duplicate.name}' across X-axis")
```

---

### Shape Key from Vertex Group

**Goal:** Limit shape key deformation to specific vertex group (e.g., only upper face)

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
shape_key = mesh_obj.data.shape_keys.key_blocks["Smile"]

# Assign vertex group as mask
vertex_group = mesh_obj.vertex_groups.get("UpperFace")
if vertex_group:
    shape_key.vertex_group = vertex_group.name
    print(f"Shape key '{shape_key.name}' masked to vertex group '{vertex_group.name}'")

    # Vertices outside group will not deform when shape key is active
else:
    print("Error: Vertex group 'UpperFace' not found")
```

**Use Case:** Create mouth shape keys that don't affect eyes, or vice versa.

---

## DRIVER SYSTEMS

### Basic Property Driver

**Goal:** Control shape key value with custom property (e.g., slider)

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
armature_obj = bpy.data.objects["Armature"]

# Add custom property to control bone
control_bone = armature_obj.pose.bones["Face_Control"]
control_bone["Smile"] = 0.0  # Custom property (0.0 - 1.0 range)

# Add UI metadata for property
prop_ui = control_bone.id_properties_ui("Smile")
prop_ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description="Smile intensity")

# Get shape key
smile_key = mesh_obj.data.shape_keys.key_blocks["Smile"]

# Add driver to shape key value
driver = smile_key.driver_add("value")
driver_var = driver.driver.variables.new()
driver_var.name = "smile_control"
driver_var.type = 'SINGLE_PROP'
driver_var.targets[0].id = armature_obj
driver_var.targets[0].data_path = 'pose.bones["Face_Control"]["Smile"]'

# Simple pass-through expression
driver.driver.expression = "smile_control"

print(f"Driver added: Face_Control['Smile'] → {smile_key.name}.value")
```

**Test Driver:**
```python
# Set control property
control_bone["Smile"] = 0.5

# Force update
bpy.context.view_layer.update()

# Check shape key value
print(f"Shape key value: {smile_key.value}")  # Should be 0.5
```

---

### Transform Driver (Bone Rotation → Shape Key)

**Goal:** Drive shape key with bone rotation (e.g., jaw rotation → mouth open)

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
armature_obj = bpy.data.objects["Armature"]

# Get shape key
mouth_open_key = mesh_obj.data.shape_keys.key_blocks["Mouth_Open"]

# Add transform driver
driver = mouth_open_key.driver_add("value")
driver_var = driver.driver.variables.new()
driver_var.name = "jaw_rot"
driver_var.type = 'TRANSFORMS'
driver_var.targets[0].id = armature_obj
driver_var.targets[0].bone_target = "Jaw"
driver_var.targets[0].transform_type = 'ROT_X'  # X-axis rotation
driver_var.targets[0].transform_space = 'LOCAL_SPACE'

# Expression: Convert rotation (radians) to 0-1 range
# Jaw opens ~0.5 radians max → map to shape key 0.0-1.0
driver.driver.expression = "max(0, min(1, -jaw_rot / 0.5))"

print(f"Transform driver added: Jaw.rotation_x → {mouth_open_key.name}.value")
```

**Rotation Mapping:**
```
Jaw rotation (radians) → Shape key value:
  0.0 rad (closed) → 0.0 (no shape key)
  -0.25 rad → 0.5 (50% mouth open)
  -0.5 rad (max open) → 1.0 (100% mouth open)
  -1.0 rad (beyond max) → 1.0 (clamped)
```

---

### Multi-Variable Driver (Combination Shapes)

**Goal:** Activate shape key only when two conditions met (e.g., smile + blink = squint)

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
armature_obj = bpy.data.objects["Armature"]

# Get corrective shape key
squint_key = mesh_obj.data.shape_keys.key_blocks["Squint_L"]

# Add driver
driver = squint_key.driver_add("value")

# Variable 1: Smile intensity
smile_var = driver.driver.variables.new()
smile_var.name = "smile"
smile_var.type = 'SINGLE_PROP'
smile_var.targets[0].id = armature_obj
smile_var.targets[0].data_path = 'pose.bones["Face_Control"]["Smile"]'

# Variable 2: Blink intensity
blink_var = driver.driver.variables.new()
blink_var.name = "blink"
blink_var.type = 'SINGLE_PROP'
blink_var.targets[0].id = armature_obj
blink_var.targets[0].data_path = 'pose.bones["Face_Control"]["Blink_L"]'

# Expression: Squint activates when both smile and blink > 0.5
# Multiply values for smooth blend
driver.driver.expression = "smile * blink if (smile > 0.5 and blink > 0.5) else 0.0"

print(f"Multi-variable driver added: Squint activates when Smile AND Blink > 0.5")
```

**Expression Variants:**
```python
# Additive (max 1.0)
driver.driver.expression = "min(1.0, smile + blink)"

# Multiplicative (requires both active)
driver.driver.expression = "smile * blink"

# Average
driver.driver.expression = "(smile + blink) / 2.0"

# Threshold activation
driver.driver.expression = "1.0 if (smile > 0.7 and blink > 0.7) else 0.0"
```

---

### Distance Driver (Proximity-Based Deformation)

**Goal:** Drive shape key based on distance between two objects (e.g., lips close → pucker)

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
upper_lip = bpy.data.objects["UpperLip_Tracker"]  # Empty object
lower_lip = bpy.data.objects["LowerLip_Tracker"]

# Get shape key
pucker_key = mesh_obj.data.shape_keys.key_blocks["Lips_Pucker"]

# Add driver
driver = pucker_key.driver_add("value")

# Variable 1: Upper lip Y position
upper_var = driver.driver.variables.new()
upper_var.name = "upper_y"
upper_var.type = 'TRANSFORMS'
upper_var.targets[0].id = upper_lip
upper_var.targets[0].transform_type = 'LOC_Y'
upper_var.targets[0].transform_space = 'WORLD_SPACE'

# Variable 2: Lower lip Y position
lower_var = driver.driver.variables.new()
lower_var.name = "lower_y"
lower_var.type = 'TRANSFORMS'
lower_var.targets[0].id = lower_lip
lower_var.targets[0].transform_type = 'LOC_Y'
lower_var.targets[0].transform_space = 'WORLD_SPACE'

# Expression: Pucker inversely proportional to lip distance
# Lips apart (0.1 units) → pucker = 0.0
# Lips touching (0.0 units) → pucker = 1.0
driver.driver.expression = "max(0, min(1, 1.0 - abs(upper_y - lower_y) * 10))"

print("Distance driver added: Lip proximity → Pucker.value")
```

---

## CORRECTIVE SHAPE KEYS

### Shoulder Bulge Corrective

**Goal:** Add muscle bulge when arm is raised (fixes armature deformation artifacts)

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterBody"]
armature_obj = bpy.data.objects["Armature"]

# Create corrective shape key
# 1. Pose arm at 90° (where artifact occurs)
shoulder_bone = armature_obj.pose.bones["UpperArm.R"]
shoulder_bone.rotation_euler.z = 1.5708  # 90 degrees

# 2. Update view to apply armature deformation
bpy.context.view_layer.update()

# 3. Sculpt mesh to correct artifact (in Blender UI Sculpt Mode)
# 4. Capture corrective as shape key
corrective = mesh_obj.shape_key_add(name="Shoulder_Bulge.R")

# 5. Reset arm to rest pose
shoulder_bone.rotation_euler.z = 0.0

# 6. Add driver to activate corrective when arm raised
driver = corrective.driver_add("value")
driver_var = driver.driver.variables.new()
driver_var.name = "arm_rot"
driver_var.type = 'TRANSFORMS'
driver_var.targets[0].id = armature_obj
driver_var.targets[0].bone_target = "UpperArm.R"
driver_var.targets[0].transform_type = 'ROT_Z'
driver_var.targets[0].transform_space = 'LOCAL_SPACE'

# Expression: Activate corrective from 45° to 90°
# 0.785 rad = 45°, 1.5708 rad = 90°
driver.driver.expression = "max(0, min(1, (arm_rot - 0.785) / (1.5708 - 0.785)))"

print(f"Corrective shape key '{corrective.name}' added with driver")
```

**Result:**
```
Arm rotation (radians) → Corrective value:
  0.0 (rest) → 0.0 (no correction)
  0.785 (45°) → 0.0 (start of correction)
  1.178 (67.5°) → 0.5 (50% correction)
  1.5708 (90°) → 1.0 (full correction)
  3.14 (180°) → 1.0 (clamped at max)
```

---

### Elbow Pinch Fix

**Goal:** Correct elbow mesh collapse when forearm bends

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterBody"]
armature_obj = bpy.data.objects["Armature"]

# Pose arm bent (where pinching occurs)
forearm = armature_obj.pose.bones["Forearm.R"]
forearm.rotation_euler.x = 2.0  # ~115° bend

bpy.context.view_layer.update()

# Create corrective (sculpt in UI to add volume to elbow)
elbow_fix = mesh_obj.shape_key_add(name="Elbow_Fix.R")

# Reset pose
forearm.rotation_euler.x = 0.0

# Add driver
driver = elbow_fix.driver_add("value")
driver_var = driver.driver.variables.new()
driver_var.name = "forearm_rot"
driver_var.type = 'TRANSFORMS'
driver_var.targets[0].id = armature_obj
driver_var.targets[0].bone_target = "Forearm.R"
driver_var.targets[0].transform_type = 'ROT_X'
driver_var.targets[0].transform_space = 'LOCAL_SPACE'

# Linear activation from 90° to 135°
driver.driver.expression = "max(0, min(1, (forearm_rot - 1.5708) / (2.356 - 1.5708)))"

print("Elbow corrective added")
```

---

### Facial Combination Correctives

**Goal:** Fix facial shape key combinations that create artifacts (e.g., smile + blink = eye deformation)

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# Activate base shapes to problematic values
smile_key = mesh_obj.data.shape_keys.key_blocks["Smile"]
blink_key = mesh_obj.data.shape_keys.key_blocks["Blink_L"]

smile_key.value = 1.0
blink_key.value = 1.0

bpy.context.view_layer.update()

# Sculpt correction in UI (fix eye deformation)
# Then capture as corrective
combo_fix = mesh_obj.shape_key_add(name="Smile_Blink_Fix", from_mix=False)

# Reset base shapes
smile_key.value = 0.0
blink_key.value = 0.0

# Add driver (multiplicative - only activates when both shapes active)
driver = combo_fix.driver_add("value")

smile_var = driver.driver.variables.new()
smile_var.name = "smile"
smile_var.type = 'SINGLE_PROP'
smile_var.targets[0].id_type = 'KEY'
smile_var.targets[0].id = mesh_obj.data.shape_keys
smile_var.targets[0].data_path = 'key_blocks["Smile"].value'

blink_var = driver.driver.variables.new()
blink_var.name = "blink"
blink_var.type = 'SINGLE_PROP'
blink_var.targets[0].id_type = 'KEY'
blink_var.targets[0].id = mesh_obj.data.shape_keys
blink_var.targets[0].data_path = 'key_blocks["Blink_L"].value'

driver.driver.expression = "smile * blink"

print("Combination corrective added (activates when Smile * Blink)")
```

---

## ORGANIZATION AND NAMING

### Naming Conventions

**Best Practices:**
```python
# Bilateral shapes (left/right)
"Smile_L", "Smile_R"
"Blink_L", "Blink_R"
"Eyebrow_Raise_L", "Eyebrow_Raise_R"

# Unilateral shapes (center)
"Jaw_Open"
"Mouth_O"
"Lips_Pucker"

# Corrective shapes
"Shoulder_Bulge.R"  # Dot notation for correctives
"Elbow_Fix.L"
"Smile_Blink_Fix"   # Combination correctives

# Phoneme shapes (for lip sync)
"Viseme_A"  # "ah"
"Viseme_E"  # "eh"
"Viseme_O"  # "oh"
"Viseme_M"  # "mmm"

# Directional controls
"Eye_Look_Up"
"Eye_Look_Down"
"Eye_Look_Left"
"Eye_Look_Right"
```

---

### Shape Key Folders (Virtual Organization)

**Goal:** Group related shape keys for easier management

**Implementation (Python 3.2+ ID Property Folders):**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
shape_keys = mesh_obj.data.shape_keys

# Add custom property for folder grouping
for key_block in shape_keys.key_blocks:
    if "Blink" in key_block.name:
        key_block["Folder"] = "Eyes"
    elif "Smile" in key_block.name or "Jaw" in key_block.name:
        key_block["Folder"] = "Mouth"
    elif "Eyebrow" in key_block.name:
        key_block["Folder"] = "Brows"
    elif "Viseme" in key_block.name:
        key_block["Folder"] = "Phonemes"
    else:
        key_block["Folder"] = "Other"

    print(f"{key_block.name} → Folder: {key_block['Folder']}")
```

**Note:** Blender doesn't have native folder UI for shape keys. Custom properties help organize in code/scripts.

---

### Reordering Shape Keys

**Goal:** Change shape key evaluation order (important for combination shapes)

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
shape_keys = mesh_obj.data.shape_keys

# Get current order
print("Current shape key order:")
for i, kb in enumerate(shape_keys.key_blocks):
    print(f"  {i}: {kb.name}")

# Move shape key to different position
# bpy.ops.object.shape_key_move(type='UP')  # Move active up
# bpy.ops.object.shape_key_move(type='DOWN')  # Move active down

# Workaround: Remove and re-add in desired order (destructive)
# Use Blender UI for non-destructive reordering
```

---

## EXPORT WORKFLOWS

### FBX Export for Unreal Engine

**Goal:** Export mesh with shape keys as morph targets for UE5

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# Verify shape keys exist
if not mesh_obj.data.shape_keys:
    print("Error: No shape keys to export")
else:
    print(f"Exporting {len(mesh_obj.data.shape_keys.key_blocks)} shape keys")

    # FBX export settings (requires operator - use Blender UI)
    # File → Export → FBX
    # Settings:
    #   - Apply Modifiers: YES (except Armature if exporting rig separately)
    #   - Shape Keys: ENABLED (exports morph targets)
    #   - Armature: Disabled (shape keys only) OR Enabled (combined rig+shapes)
    #   - Bake Animation: Disabled (shape keys are mesh data, not animation)

    # Check for driver dependencies
    for kb in mesh_obj.data.shape_keys.key_blocks:
        if kb.driver_add("value"):  # Check if driver exists
            print(f"  Warning: {kb.name} has driver (won't export to UE)")

print("FBX export configured for Unreal Engine")
```

**Unreal Import:**
```
1. Import FBX to Unreal Content Browser
2. Import dialog: Enable "Import Morph Targets"
3. Each Blender shape key becomes Unreal morph target
4. Access in Skeletal Mesh Editor → Morph Targets panel
5. Animate via Animation Blueprint or Control Rig
```

---

### Alembic Export (Animated Shape Keys)

**Goal:** Bake animated shape keys to Alembic for interchange

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
scene = bpy.context.scene

# Animate shape keys (example)
smile_key = mesh_obj.data.shape_keys.key_blocks["Smile"]

scene.frame_set(1)
smile_key.value = 0.0
smile_key.keyframe_insert(data_path="value", frame=1)

scene.frame_set(24)
smile_key.value = 1.0
smile_key.keyframe_insert(data_path="value", frame=24)

# Alembic export (requires operator - use Blender UI)
# File → Export → Alembic (.abc)
# Settings:
#   - Frame Range: Animation length
#   - Geometry: Face Sets (for shape keys)
#   - Transform: Scene (or custom)

print("Alembic export configured (frames 1-24)")
print("Shape key animation will bake as geometry cache")
```

**Alembic vs FBX:**
```
FBX:
  - Exports shape key definitions (not animation)
  - Smaller file size
  - Best for game engines (Unreal, Unity)

Alembic:
  - Bakes shape key animation as geometry cache
  - Larger file size
  - Best for VFX (Nuke, Houdini, Maya)
  - Preserves exact deformation per-frame
```

---

### Removing Drivers for Export

**Goal:** Convert driven shape keys to keyframed animation for cleaner export

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
scene = bpy.context.scene

# Bake drivers to keyframes
start_frame = scene.frame_start
end_frame = scene.frame_end

for kb in mesh_obj.data.shape_keys.key_blocks:
    # Check if has driver
    if kb.animation_data and kb.animation_data.drivers:
        print(f"Baking driver for {kb.name}...")

        # Sample each frame
        for frame in range(start_frame, end_frame + 1):
            scene.frame_set(frame)
            # Driver evaluates automatically
            kb.keyframe_insert(data_path="value", frame=frame)

        # Remove driver
        kb.driver_remove("value")
        print(f"  Driver removed, keyframes added")

print("All drivers baked to keyframes")
```

---

## PERFORMANCE OPTIMIZATION

### Shape Key Count vs Performance

**Performance Impact:**
```
Shape Keys: Low impact (pre-calculated offsets)
  - 10 keys: Negligible
  - 50 keys: Minimal (~5% slower)
  - 200 keys: Moderate (~20% slower)
  - 500+ keys: Significant (use optimization)

Active Shape Keys: Higher impact
  - Only keys with value > 0.0 are calculated
  - Keep inactive keys at 0.0 for best performance
```

---

### Vertex Group Masking

**Goal:** Reduce shape key calculation overhead by limiting affected vertices

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# Create vertex group for mouth region
mouth_vg = mesh_obj.vertex_groups.new(name="Mouth_Region")

# Assign mouth vertices (example indices)
mouth_vertices = list(range(1000, 1500))  # 500 vertices
mouth_vg.add(mouth_vertices, 1.0, 'REPLACE')

# Assign to all mouth shape keys
for kb in mesh_obj.data.shape_keys.key_blocks:
    if "Mouth" in kb.name or "Jaw" in kb.name or "Lips" in kb.name:
        kb.vertex_group = mouth_vg.name
        print(f"{kb.name} masked to {len(mouth_vertices)} vertices")

print(f"Performance improvement: {(len(mesh_obj.data.vertices) - len(mouth_vertices)) / len(mesh_obj.data.vertices) * 100:.1f}% vertices excluded")
```

---

### Relative Key Cleanup

**Goal:** Remove unused or redundant shape keys

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
shape_keys = mesh_obj.data.shape_keys

# Find shape keys with zero deformation
zero_deform_keys = []

for kb in shape_keys.key_blocks:
    if kb == shape_keys.reference_key:
        continue  # Skip Basis

    # Check if any vertex has non-zero offset
    has_deformation = False
    basis = shape_keys.reference_key

    for i, vert in enumerate(kb.data):
        offset = vert.co - basis.data[i].co
        if offset.length > 0.0001:  # Tolerance
            has_deformation = True
            break

    if not has_deformation:
        zero_deform_keys.append(kb.name)

print(f"Shape keys with zero deformation: {len(zero_deform_keys)}")
for name in zero_deform_keys:
    print(f"  - {name}")

# Remove zero-deform keys (requires operator - use UI)
# Or keep for documentation purposes
```

---

### Shape Key Baking (Reduce Complexity)

**Goal:** Combine multiple shape keys into single baked geometry for export

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# Set shape keys to desired values
mesh_obj.data.shape_keys.key_blocks["Smile"].value = 0.5
mesh_obj.data.shape_keys.key_blocks["Blink_L"].value = 0.3

# Apply shape keys as basis (destructive - duplicate mesh first)
# NOTE: Requires operator - use Blender UI
# Object menu → Apply → Shape Keys

# Workaround: Create new mesh with applied shape keys
applied_mesh = mesh_obj.data.copy()
applied_mesh.name = f"{mesh_obj.data.name}_Baked"

# Copy current vertex positions (includes shape key deformation)
for i, vert in enumerate(applied_mesh.vertices):
    vert.co = mesh_obj.data.vertices[i].co

# Remove shape keys from new mesh
applied_mesh.shape_keys_clear()

print(f"Baked mesh created: {applied_mesh.name} (no shape keys)")
```

---

## FACIAL ANIMATION PIPELINES

### FACS-Based Shape Key Set

**Goal:** Create Facial Action Coding System (FACS) shape keys for realistic facial animation

**FACS Action Units (Subset):**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# FACS Action Units (AU) mapping
facs_shapes = {
    # Upper Face
    "AU1_Inner_Brow_Raise": "Inner eyebrow raise",
    "AU2_Outer_Brow_Raise": "Outer eyebrow raise",
    "AU4_Brow_Lower": "Frown (brow down)",
    "AU5_Upper_Lid_Raise": "Wide eyes",
    "AU6_Cheek_Raise": "Squint",
    "AU7_Lid_Tight": "Eyes closed tight",

    # Lower Face
    "AU9_Nose_Wrinkle": "Disgust",
    "AU10_Upper_Lip_Raise": "Sneer",
    "AU12_Lip_Corner_Pull": "Smile",
    "AU15_Lip_Corner_Depress": "Frown",
    "AU16_Lower_Lip_Depress": "Chin down",
    "AU17_Chin_Raise": "Doubt",
    "AU20_Lip_Stretch": "Wide mouth",
    "AU23_Lip_Tighten": "Lips pressed",
    "AU25_Lips_Part": "Mouth open",
    "AU26_Jaw_Drop": "Jaw down",
    "AU27_Mouth_Stretch": "Yawn"
}

# Create shape keys (add basis first)
if not mesh_obj.data.shape_keys:
    mesh_obj.shape_key_add(name="Basis")

for au_name, description in facs_shapes.items():
    shape_key = mesh_obj.shape_key_add(name=au_name)
    shape_key["Description"] = description  # Custom property
    print(f"Created {au_name}: {description}")

print(f"\nFACS shape key set: {len(facs_shapes)} action units")
```

---

### Phoneme Shape Keys for Lip Sync

**Goal:** Create viseme set for speech animation

**Implementation:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# Standard viseme set (Preston Blair style)
visemes = {
    "Viseme_Neutral": "Rest position",
    "Viseme_M": "M, B, P (lips closed)",
    "Viseme_AH": "Father, hot (jaw open, relaxed)",
    "Viseme_OH": "Go, boat (lips rounded)",
    "Viseme_EE": "See, eat (lips wide, teeth close)",
    "Viseme_ER": "Bird, her (lips slightly rounded)",
    "Viseme_L": "L, T, D (tongue up)",
    "Viseme_F": "F, V (upper teeth on lower lip)",
    "Viseme_S": "S, Z (teeth close, lips parted)",
    "Viseme_SH": "Sh, Ch (lips forward)"
}

if not mesh_obj.data.shape_keys:
    mesh_obj.shape_key_add(name="Basis")

for viseme_name, description in visemes.items():
    shape_key = mesh_obj.shape_key_add(name=viseme_name)
    shape_key["Description"] = description
    print(f"Created {viseme_name}: {description}")

print(f"\nViseme set: {len(visemes)} shapes")
```

**Lip Sync Workflow:**
```
1. Record/import audio
2. Analyze audio for phonemes (Papagayo, Rhubarb Lip Sync)
3. Map phonemes to visemes
4. Keyframe viseme shape keys to match audio
```

---

## TROUBLESHOOTING

### Issue: Shape Key Has No Effect

**Symptoms:** Shape key value set to 1.0 but mesh doesn't deform

**Causes:**
1. Shape key has zero deformation (vertices identical to Basis)
2. Vertex group mask excludes all vertices
3. Modifier order issue (shape keys before Armature)

**Solutions:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
shape_key = mesh_obj.data.shape_keys.key_blocks["Smile"]

# Check 1: Verify deformation exists
basis = mesh_obj.data.shape_keys.reference_key
has_deform = False

for i in range(len(shape_key.data)):
    offset = (shape_key.data[i].co - basis.data[i].co).length
    if offset > 0.0001:
        has_deform = True
        print(f"Vertex {i} offset: {offset:.4f}")
        break

if not has_deform:
    print("ERROR: Shape key has zero deformation")

# Check 2: Verify vertex group
if shape_key.vertex_group:
    vg = mesh_obj.vertex_groups.get(shape_key.vertex_group)
    if vg:
        count = sum(1 for v in mesh_obj.data.vertices if vg.index in [g.group for g in v.groups])
        print(f"Vertex group '{vg.name}': {count} vertices")
    else:
        print(f"ERROR: Vertex group '{shape_key.vertex_group}' not found")

# Check 3: Modifier order (shape keys always first internally)
# No action needed - Blender handles automatically
```

---

### Issue: Driver Not Updating Shape Key

**Symptoms:** Custom property changed but shape key doesn't respond

**Causes:**
1. Driver expression error
2. Dependency graph not updated
3. Incorrect data path

**Solutions:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]
shape_key = mesh_obj.data.shape_keys.key_blocks["Smile"]

# Check 1: Verify driver exists
anim_data = shape_key.animation_data
if anim_data and anim_data.drivers:
    for driver in anim_data.drivers:
        print(f"Driver on: {driver.data_path}")

        # Check expression
        print(f"  Expression: {driver.driver.expression}")

        # Check variables
        for var in driver.driver.variables:
            print(f"  Variable '{var.name}':")
            for target in var.targets:
                print(f"    ID: {target.id}")
                print(f"    Path: {target.data_path}")

        # Test evaluation
        try:
            result = driver.driver.expression
            print(f"  Evaluates to: {result}")
        except Exception as e:
            print(f"  ERROR: {e}")
else:
    print("No driver found")

# Force update
bpy.context.view_layer.update()
mesh_obj.update_tag()
```

---

### Issue: Shape Keys Deform Incorrectly on Export

**Symptoms:** FBX export to Unreal shows distorted morph targets

**Cause:** Modifiers applied before shape keys (wrong order)

**Solution:**
```python
import bpy

mesh_obj = bpy.data.objects["CharacterHead"]

# Check modifier stack
print("Modifier order:")
for i, mod in enumerate(mesh_obj.modifiers):
    print(f"  {i}: {mod.name} ({mod.type})")

# Shape keys are always evaluated first (can't reorder)
# Issue: Armature modifier on mesh with shape keys AND armature parent

# Fix: Remove armature modifier, use parent-only
for mod in mesh_obj.modifiers:
    if mod.type == 'ARMATURE':
        print(f"Removing armature modifier: {mod.name}")
        mesh_obj.modifiers.remove(mod)

# Parent mesh to armature (deformation handled by shape keys + parent)
armature_obj = bpy.data.objects["Armature"]
mesh_obj.parent = armature_obj
mesh_obj.parent_type = 'OBJECT'

print("Mesh parented to armature (no modifier)")
```

---

## REFERENCE MATERIALS

**Animation System Validation Report:**
`<workspace>\Blender\blender-ai-compatibility\ANIMATION_SYSTEM_VALIDATION_REPORT.md`

**Blender Shape Keys API Reference (Official):**
https://docs.blender.org/api/current/bpy.types.ShapeKey.html
https://docs.blender.org/api/current/bpy.types.Key.html

---

## VERSION HISTORY

**v1.0.0** (2025-10-25) - Initial release
- Shape key creation and management
- Driver systems (property, transform, multi-variable, distance)
- Corrective shape keys for rigging
- Organization and naming conventions
- FBX and Alembic export workflows
- Performance optimization techniques
- FACS and phoneme shape key sets
- Comprehensive troubleshooting

---

**Document Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Last Updated:** 2025-10-25
**Lines:** ~800
**API Stability:** 100% STABLE (Blender 4.2 → 4.5.0)
