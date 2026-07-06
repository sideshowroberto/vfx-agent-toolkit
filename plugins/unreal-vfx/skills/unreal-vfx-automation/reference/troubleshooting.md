# Unreal VFX Automation - Troubleshooting Guide

**Version:** 2.0.0
**Last Updated:** 2026-07-06
**Skill:** unreal-vfx-automation
**Purpose:** Complete diagnostic guide for resolving foreground plate and image sequence issues

---

## Overview

This guide provides detailed troubleshooting for the most common issues encountered when using the unreal-vfx-automation skill. Each issue includes symptoms, diagnosis steps, solutions, and validation procedures.

**Calling convention (UE 5.8 native MCP):** All Python in this document runs inside the Unreal Editor via `mcp__ue58-mcp__execute_python_code(code=...)`. The `create_foreground_plate()` helper comes from `ForegroundPlateSetup.py` - copy it (and `InspectCameraComponents.py`) into your UE project's `Content/Python/` folder, then import directly:

```python
from ForegroundPlateSetup import create_foreground_plate
```

**Quick Navigation:**
- [Issue 1: ImagePlate Not Visible](#issue-1-imageplate-not-visible)
- [Issue 2: Alpha Channel Not Working](#issue-2-alpha-channel-not-working)
- [Issue 3: Texture Changes Affect Other Shots](#issue-3-texture-changes-affect-other-shots)
- [Issue 4: MediaPlayer Not Auto-Playing](#issue-4-mediaplayer-not-auto-playing)
- [Issue 5: Performance Problems](#issue-5-performance-problems-frame-drops-slow-loading)
- [Issue 6: Blueprint Template Missing](#issue-6-blueprint-template-missing-or-misconfigured)
- [Issue 7: ImagePlate Plugin Not Enabled](#issue-7-imageplate-plugin-not-enabled)
- [Issue 8: Memory Issues with Large Sequences](#issue-8-memory-issues-with-large-sequences)

---

## Issue 1: ImagePlate Not Visible

### Symptoms
- Camera spawned successfully in Outliner
- ImagePlate component appears in Details panel
- But image sequence NOT visible in viewport
- Viewport shows empty scene or just CG elements

### Diagnosis

**Step 1: Verify MediaPlayer State**

```python
# Method A: Check MediaPlayer via Content Browser
# 1. Content Browser → Search for MP_{plate_name}
# 2. Double-click to open MediaPlayer editor
# 3. Check playback status (should show "Playing")
# 4. Verify first frame appears in preview

# Method B: Check via Python
import unreal

# Find MediaPlayer asset
media_player_path = "/Game/Media/MP_Shot001_FG"
media_player = unreal.load_asset(media_player_path)

# Check if playing
is_playing = media_player.is_playing()
print(f"MediaPlayer Playing: {is_playing}")

# Check duration
duration = media_player.get_duration()
print(f"Duration: {duration}")

# If duration is 0.0, media source not loaded
```

**Expected:**
- `is_playing()` returns `True`
- `get_duration()` returns positive value (e.g., 5.0 seconds for 120-frame sequence at 24fps)

**Step 2: Validate ImagePlate Component Hierarchy**

```python
# Run diagnostic script
# InspectCameraComponents.py lives in your UE project's Content/Python/ folder
# (auto-added to sys.path by the editor)
from InspectCameraComponents import inspect_camera_components

# Inspect all cameras
inspect_camera_components()

# Expected output:
# Camera: Cam_Shot001_FG
#   - CineCameraComponent
#   - ImagePlateComponent (✓)
#   - ImagePlateFrustumComponent (✓)
```

**Expected:**
- ImagePlateComponent exists
- ImagePlateFrustumComponent exists (auto-created by ImagePlate)
- Both components attached to camera

**Step 3: Verify Camera Viewport View**

```
Manual Check:
1. Outliner → Select Cam_{plate_name}
2. Right-click → "Pilot Camera Actor"
3. Viewport → Should show camera's view
4. Verify you're looking THROUGH the camera, not AT it
```

**Step 4: Check ImagePlate Material Assignment**

```python
# Get camera from level
camera = unreal.EditorLevelLibrary.get_selected_level_actors()[0]

# Get ImagePlate component
image_plate = camera.get_component_by_class(unreal.ImagePlateComponent)

# Check material
material_interface = image_plate.get_editor_property("material")
print(f"Material: {material_interface.get_name()}")

# Check texture parameter
texture = image_plate.get_editor_property("image_plate_source")
print(f"Texture: {texture}")
```

**Expected:**
- Material should be `M_{plate_name}` or `MI_{plate_name}`
- Texture should reference MediaTexture asset

### Solutions

**Solution 1: MediaPlayer Not Playing**

```python
# Force MediaPlayer to play
media_player = unreal.load_asset("/Game/Media/MP_Shot001_FG")
media_player.play()

# Or re-create with auto_play_media=True
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    auto_play_media=True  # Ensure this is True
)
```

**Solution 2: ImagePlateFrustumComponent Missing**

**Cause:** Camera created without Blueprint template

**Fix:**
```python
# 1. Delete broken camera
unreal.EditorLevelLibrary.destroy_actor(camera)

# 2. Verify Blueprint template exists
blueprint_path = "/Game/cam_example_Blueprint"
blueprint = unreal.load_asset(blueprint_path)

if blueprint is None:
    print("ERROR: Blueprint template not found!")
    print("Create Blueprint camera with ImagePlate component first")
    # See Issue 6 for Blueprint creation guide

# 3. Re-run foreground plate creation (uses Blueprint)
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG"
)
```

**Solution 3: Camera Not Piloted**

**Fix:**
```
1. Outliner → Select Cam_{plate_name}
2. Right-click → "Pilot Camera Actor"
3. Viewport updates to camera view
4. ImagePlate should now be visible
```

**Solution 4: Material Not Assigned to ImagePlate**

```python
# Get camera and component
camera = unreal.EditorLevelLibrary.get_actor_reference("Cam_Shot001_FG")
image_plate = camera.get_component_by_class(unreal.ImagePlateComponent)

# Load material
material = unreal.load_asset("/Game/Materials/M_Shot001_FG")

# Assign to ImagePlate
image_plate.set_editor_property("material", material)
```

### Validation

**Checklist:**
- [ ] MediaPlayer shows "Playing" status
- [ ] MediaPlayer duration > 0.0 seconds
- [ ] ImagePlateFrustumComponent exists in component hierarchy
- [ ] Camera is piloted in viewport
- [ ] Material assigned to ImagePlate component
- [ ] Image sequence visible in viewport when looking through camera

**Successful Result:**
- Image sequence plays in viewport
- First frame appears immediately
- Playback smooth (no stuttering)

---

## Issue 2: Alpha Channel Not Working

### Symptoms
- Image sequence visible but alpha transparency NOT working
- Black areas instead of transparent regions
- Hard edges around cutout areas
- Background CG elements not visible through transparent areas

### Diagnosis

**Step 1: Check Material Blend Mode**

```python
# Load material
material_path = "/Game/Materials/M_Shot001_FG"
material = unreal.load_asset(material_path)

# For regular materials (not instances)
if isinstance(material, unreal.Material):
    blend_mode = material.get_editor_property("blend_mode")
    print(f"Blend Mode: {blend_mode}")
    # Expected: BLEND_Masked or BLEND_Translucent

# For material instances
if isinstance(material, unreal.MaterialInstanceConstant):
    parent = material.get_editor_property("parent")
    print(f"Parent Material: {parent.get_name()}")
    # Check parent material's blend mode
```

**Expected Blend Modes:**
- **BLEND_Masked** - Hard alpha cutout (0 or 1, no gradients)
- **BLEND_Translucent** - Soft alpha blend (0.0-1.0 gradients)

**NOT Supported:**
- **BLEND_Opaque** - No alpha support (solid material)

**Step 2: Validate Texture Format**

```python
# Check MediaTexture settings
media_texture_path = "/Game/Media/MT_Shot001_FG"
media_texture = unreal.load_asset(media_texture_path)

# MediaTexture doesn't expose compression settings directly
# Check source image format instead
```

**Manual Check:**
```
1. Content Browser → MS_{plate_name} (ImgMediaSource)
2. Double-click to open
3. Check "Sequence Path" points to correct format
4. Supported formats:
   - EXR with alpha channel (recommended)
   - PNG with alpha channel
   - TGA with alpha channel
5. NOT supported:
   - JPG (no alpha channel)
   - BMP (no alpha channel)
```

**Step 3: Verify Opacity Mask Connection**

```
Manual Check (Material Editor):
1. Content Browser → M_{plate_name} or M_ForegroundPlate_Master
2. Double-click to open Material Editor
3. Verify material graph:
   - PlateTexture → Texture Sample node
   - Alpha output (pin 4) → Opacity Mask input
   - Should see connection line from Alpha pin to Opacity Mask
```

**Expected Material Graph:**
```
[Texture Sample: PlateTexture]
├── RGB (pin 1-3) → EmissiveColor
└── Alpha (pin 4) → OpacityMask (× OpacityMultiplier)
```

**Step 4: Check Opacity Multiplier Parameter**

```python
# For material instances
material_instance = unreal.load_asset("/Game/Materials/MI_Shot001_FG")

# Get scalar parameter value
opacity = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
    material_instance,
    "OpacityMultiplier"
)
print(f"OpacityMultiplier: {opacity}")

# Expected: 1.0 (full opacity where alpha exists)
# If 0.0: Completely transparent (invisible)
```

### Solutions

**Solution 1: Fix Blend Mode**

```python
# For regular materials
material = unreal.load_asset("/Game/Materials/M_Shot001_FG")

# Set blend mode to Masked
material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)

# Alternative: Translucent for soft edges
# material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)

# Mark dirty and save
unreal.EditorAssetLibrary.save_loaded_asset(material)
```

**Solution 2: Re-Export Sequence with Alpha**

**Nuke Export Example:**
```
Write Node Settings:
- File Type: exr
- Channels: rgba (MUST include alpha)
- Compression: ZIP (recommended)
- Bit Depth: 16-bit half (recommended)

Checklist:
- [ ] Alpha channel included in render
- [ ] Alpha premultiplication correct
- [ ] Test single frame in Photoshop (alpha visible)
```

**Solution 3: Recreate Material with Correct Settings**

```python
# Delete broken material
unreal.EditorAssetLibrary.delete_asset("/Game/Materials/M_Shot001_FG")

# Re-create with correct blend mode
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    auto_play_media=True
)

# Verify blend mode after creation
material = unreal.load_asset("/Game/Materials/M_Shot001_FG")
blend_mode = material.get_editor_property("blend_mode")
assert blend_mode == unreal.BlendMode.BLEND_MASKED
```

**Solution 4: Fix Opacity Multiplier**

```python
# For material instances
material_instance = unreal.load_asset("/Game/Materials/MI_Shot001_FG")

# Set OpacityMultiplier to 1.0
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    material_instance,
    "OpacityMultiplier",
    1.0  # Full opacity
)

# Save
unreal.EditorAssetLibrary.save_loaded_asset(material_instance)
```

### Validation

**Checklist:**
- [ ] Material blend mode is Masked or Translucent
- [ ] Image sequence includes alpha channel
- [ ] Opacity Mask connected in material graph
- [ ] OpacityMultiplier = 1.0 in material instance
- [ ] Transparent areas show CG background
- [ ] No black fringing around edges

**Test Procedure:**
```
1. Place colored cube behind ImagePlate
2. Transparent areas of plate should reveal cube
3. If cube not visible → alpha still broken
4. If black fringing → check premultiplication
```

---

## Issue 3: Texture Changes Affect Other Shots

### Symptoms
- Modified Shot002 MediaTexture to new sequence
- Shot003 also changed to same sequence
- Multiple shots showing wrong image sequence
- Expected isolation NOT working

### Diagnosis

**Step 1: Verify Material vs Material Instance**

```python
# Check asset type
shot002_material = unreal.load_asset("/Game/Materials/MI_Shot002_FG")
shot003_material = unreal.load_asset("/Game/Materials/MI_Shot003_FG")

# Determine type
print(f"Shot002: {type(shot002_material).__name__}")
print(f"Shot003: {type(shot003_material).__name__}")

# Expected: MaterialInstanceConstant
# Problem: Material (both shots share same material)
```

**Step 2: Inspect Material Hierarchy**

```python
# For material instances
if isinstance(shot002_material, unreal.MaterialInstanceConstant):
    parent = shot002_material.get_editor_property("parent")
    print(f"Shot002 Parent: {parent.get_path_name()}")

if isinstance(shot003_material, unreal.MaterialInstanceConstant):
    parent = shot003_material.get_editor_property("parent")
    print(f"Shot003 Parent: {parent.get_path_name()}")

# Expected: Different instances, same parent
# Shot002 Parent: /Game/Materials/M_ForegroundPlate_Master
# Shot003 Parent: /Game/Materials/M_ForegroundPlate_Master

# Problem: Both reference same parent AND same texture parameter
```

**Step 3: Check Texture Parameter Overrides**

```python
# Get texture parameter for each instance
shot002_texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
    shot002_material,
    "PlateTexture"
)
shot003_texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
    shot003_material,
    "PlateTexture"
)

print(f"Shot002 Texture: {shot002_texture.get_name()}")
print(f"Shot003 Texture: {shot003_texture.get_name()}")

# Expected: Different textures
# Shot002 Texture: MT_Shot002_FG
# Shot003 Texture: MT_Shot003_FG

# Problem: Same texture reference
```

**Step 4: Validate MediaTexture Assets**

```python
# Check if separate MediaTexture assets exist
mt_shot002 = unreal.load_asset("/Game/Media/MT_Shot002_FG")
mt_shot003 = unreal.load_asset("/Game/Media/MT_Shot003_FG")

print(f"MT_Shot002 exists: {mt_shot002 is not None}")
print(f"MT_Shot003 exists: {mt_shot003 is not None}")

# Expected: Both exist
# Problem: Only one exists (shared MediaTexture)
```

### Solutions

**Solution 1: Recreate with Master Material Pattern**

```python
# DELETE broken shots first
unreal.EditorAssetLibrary.delete_directory("/Game/Materials/Shot002")
unreal.EditorAssetLibrary.delete_directory("/Game/Materials/Shot003")

# Recreate Shot 1 (creates master)
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    master_material_path="/Game/Materials/M_ForegroundPlate_Master"
)

# Recreate Shot 2 (creates instance)
create_foreground_plate(
    sequence_path="D:/Plates/Shot002/Shot002_0001.exr",
    plate_name="Shot002_FG",
    master_material_path="/Game/Materials/M_ForegroundPlate_Master"
)

# Recreate Shot 3 (creates instance)
create_foreground_plate(
    sequence_path="D:/Plates/Shot003/Shot003_0001.exr",
    plate_name="Shot003_FG",
    master_material_path="/Game/Materials/M_ForegroundPlate_Master"
)
```

**Solution 2: Manually Create Material Instances**

```python
import unreal

# Load master material
master_material = unreal.load_asset("/Game/Materials/M_ForegroundPlate_Master")

# Create material instance for Shot002
mi_shot002 = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="MI_Shot002_FG",
    package_path="/Game/Materials",
    asset_class=unreal.MaterialInstanceConstant,
    factory=unreal.MaterialInstanceConstantFactoryNew()
)
mi_shot002.set_editor_property("parent", master_material)

# Set texture parameter
mt_shot002 = unreal.load_asset("/Game/Media/MT_Shot002_FG")
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    mi_shot002,
    "PlateTexture",
    mt_shot002
)

# Save
unreal.EditorAssetLibrary.save_loaded_asset(mi_shot002)

# Repeat for Shot003...
```

**Solution 3: Verify Master Material Exists**

```python
# Check if master material exists
master_material_path = "/Game/Materials/M_ForegroundPlate_Master"
master_material = unreal.load_asset(master_material_path)

if master_material is None:
    print("ERROR: Master material not found!")
    print("Create master material first:")
    # Create first shot with master_material_path parameter
    create_foreground_plate(
        sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
        plate_name="Shot001_FG",
        master_material_path=master_material_path  # Creates master
    )
```

### Validation

**Checklist:**
- [ ] Each shot has separate material instance (MI_Shot001_FG, MI_Shot002_FG, etc.)
- [ ] All instances reference same master material
- [ ] Each instance has unique PlateTexture parameter
- [ ] Each shot has separate MediaTexture (MT_Shot001_FG, MT_Shot002_FG, etc.)
- [ ] Changing Shot002 texture does NOT affect Shot003

**Test Procedure:**
```
1. Load Shot002 material instance
2. Change PlateTexture parameter to different MediaTexture
3. Verify Shot003 still shows original texture
4. If Shot003 changed → material instances not set up correctly
```

**Expected Hierarchy:**
```
M_ForegroundPlate_Master (master material)
├── MI_Shot001_FG (PlateTexture = MT_Shot001_FG)
├── MI_Shot002_FG (PlateTexture = MT_Shot002_FG)
└── MI_Shot003_FG (PlateTexture = MT_Shot003_FG)
```

---

## Issue 4: MediaPlayer Not Auto-Playing

### Symptoms
- Foreground plate creation completes successfully
- MediaPlayer asset created
- But MediaPlayer shows black frame (not playing)
- No errors in output log

### Diagnosis

**Step 1: Check Auto-Play Parameter**

```python
# Verify auto_play_media was set to True
# Review command used:
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    auto_play_media=True  # Should be True
)

# If auto_play_media was False or omitted:
# → MediaPlayer won't auto-play
```

**Step 2: Validate ImgMediaSource Path**

```python
# Load ImgMediaSource
img_media_source = unreal.load_asset("/Game/Media/MS_Shot001_FG")

# Get sequence path
sequence_path = img_media_source.get_editor_property("sequence_path")
print(f"Sequence Path: {sequence_path}")

# Expected format:
# D:/Plates/Shot001/Shot001_*.exr (with wildcard *)
# NOT: D:/Plates/Shot001/Shot001_0001.exr (single file)
```

**Path Format Requirements:**
- Must use forward slashes: `D:/Plates/` NOT `D:\Plates\`
- Must include wildcard: `Shot001_*.exr` NOT `Shot001_0001.exr`
- Must point to first frame's directory
- Frame number format: `_0001`, `_0002`, etc. (4 digits with underscore)

**Step 3: Check MediaPlayer OpenSource Call**

```python
# Get MediaPlayer
media_player = unreal.load_asset("/Game/Media/MP_Shot001_FG")

# Check if media source is opened
media_source = media_player.get_editor_property("media_source")
print(f"Media Source: {media_source}")

# If None → MediaPlayer not connected to ImgMediaSource

# Attempt to open source manually
img_media_source = unreal.load_asset("/Game/Media/MS_Shot001_FG")
success = media_player.open_source(img_media_source)
print(f"OpenSource Success: {success}")

# If False → path or format issue
```

**Step 4: Verify File System Access**

```python
import os

# Check if sequence path exists
sequence_dir = "D:/Plates/Shot001"
first_frame = "D:/Plates/Shot001/Shot001_0001.exr"

print(f"Directory exists: {os.path.exists(sequence_dir)}")
print(f"First frame exists: {os.path.exists(first_frame)}")

# List files in directory
if os.path.exists(sequence_dir):
    files = [f for f in os.listdir(sequence_dir) if f.endswith(".exr")]
    print(f"EXR files found: {len(files)}")
    print(f"First 3 files: {files[:3]}")

# Expected: Multiple files with sequential naming
```

### Solutions

**Solution 1: Re-Create with Auto-Play Enabled**

```python
# Re-run with auto_play_media=True
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    auto_play_media=True  # Explicitly set to True
)
```

**Solution 2: Manually Start MediaPlayer**

```python
# Load MediaPlayer
media_player = unreal.load_asset("/Game/Media/MP_Shot001_FG")

# Play
media_player.play()

# Verify playing
is_playing = media_player.is_playing()
print(f"Now Playing: {is_playing}")
```

**Solution 3: Fix ImgMediaSource Path**

```python
# Load ImgMediaSource
img_media_source = unreal.load_asset("/Game/Media/MS_Shot001_FG")

# Set correct path (with wildcard)
correct_path = unreal.DirectoryPath("D:/Plates/Shot001")
img_media_source.set_editor_property("sequence_path", correct_path)

# Save
unreal.EditorAssetLibrary.save_loaded_asset(img_media_source)

# Reopen MediaPlayer
media_player = unreal.load_asset("/Game/Media/MP_Shot001_FG")
media_player.open_source(img_media_source)
media_player.play()
```

**Solution 4: Verify Frame Naming Convention**

**Expected Naming:**
```
Shot001_0001.exr
Shot001_0002.exr
Shot001_0003.exr
...
Shot001_0120.exr
```

**NOT Supported:**
```
Shot001.0001.exr (dot separator - not supported)
Shot001_1.exr (variable digits - not supported)
Shot001_001.exr (3 digits - may work but 4 recommended)
```

**Fix Naming:**
```bash
# PowerShell script to rename files
$files = Get-ChildItem "D:\Plates\Shot001\*.exr"
$counter = 1
foreach ($file in $files) {
    $newName = "Shot001_{0:D4}.exr" -f $counter
    Rename-Item $file.FullName -NewName $newName
    $counter++
}
```

### Validation

**Checklist:**
- [ ] auto_play_media=True in create command
- [ ] ImgMediaSource path includes wildcard (*)
- [ ] First frame file exists at specified path
- [ ] Frame naming follows convention (name_####.ext)
- [ ] MediaPlayer shows "Playing" status
- [ ] First frame visible in MediaPlayer preview

**Test Procedure:**
```
1. Content Browser → MP_{plate_name}
2. Double-click to open MediaPlayer editor
3. Verify:
   - Source shows MS_{plate_name}
   - Duration > 0.0 seconds
   - Timeline scrubber moveable
   - First frame visible in preview
4. Click Play button if not auto-playing
5. Verify playback starts
```

---

## Issue 5: Performance Problems (Frame Drops, Slow Loading)

### Symptoms
- Image sequence loads but playback stutters
- Frame rate drops when ImagePlate visible
- Long load times (10+ seconds) for first frame
- Editor becomes unresponsive during playback
- High memory usage in Task Manager

### Diagnosis

**Step 1: Check Image Sequence Size**

```python
import os

# Check file sizes
sequence_dir = "D:/Plates/Shot001"
first_frame = os.path.join(sequence_dir, "Shot001_0001.exr")

if os.path.exists(first_frame):
    file_size_mb = os.path.getsize(first_frame) / (1024 * 1024)
    print(f"Frame Size: {file_size_mb:.2f} MB")

    # Count total frames
    files = [f for f in os.listdir(sequence_dir) if f.endswith(".exr")]
    total_size_mb = sum(os.path.getsize(os.path.join(sequence_dir, f)) for f in files) / (1024 * 1024)
    print(f"Total Sequence Size: {total_size_mb:.2f} MB")
    print(f"Frame Count: {len(files)}")

# Performance thresholds:
# <5MB per frame → Good performance
# 5-20MB per frame → Moderate (proxy recommended)
# >20MB per frame → Poor (proxy required)
```

**Step 2: Check Image Resolution**

```python
# Check MediaTexture resolution
media_texture = unreal.load_asset("/Game/Media/MT_Shot001_FG")

# MediaTexture doesn't expose resolution directly
# Check in Content Browser Details panel instead
```

**Manual Check:**
```
1. Content Browser → MT_{plate_name}
2. Right-click → Asset Actions → Show in Explorer
3. Check source image resolution
   - 1920x1080 (HD) → Good performance
   - 3840x2160 (4K) → Moderate performance
   - 7680x4320 (8K) → Poor performance (proxy required)
```

**Step 3: Monitor Memory Usage**

```
Task Manager → Performance Tab → Memory
- Before loading ImagePlate: Note usage
- After loading ImagePlate: Note usage
- Difference = memory used by sequence

Warning Signs:
- >4GB memory used by sequence → Too large
- Memory usage climbing during playback → Memory leak
- Available memory <2GB → System under pressure
```

**Step 4: Check Disk Speed**

```python
import time
import os

# Test read speed
sequence_dir = "D:/Plates/Shot001"
first_frame = os.path.join(sequence_dir, "Shot001_0001.exr")

start = time.time()
with open(first_frame, 'rb') as f:
    data = f.read()
elapsed = time.time() - start

file_size_mb = len(data) / (1024 * 1024)
speed_mbps = file_size_mb / elapsed

print(f"File Size: {file_size_mb:.2f} MB")
print(f"Read Time: {elapsed:.2f} seconds")
print(f"Read Speed: {speed_mbps:.2f} MB/s")

# Performance targets:
# >100 MB/s → SSD (good)
# 50-100 MB/s → SATA SSD (acceptable)
# <50 MB/s → HDD (slow, proxy recommended)
```

### Solutions

**Solution 1: Use Proxy Workflow**

```python
# Create lowres proxy sequence (via Nuke, FFmpeg, etc.)
# Example structure:
# D:/Plates/Shot001/
# ├── Shot001_0001.exr (4K - 20MB per frame)
# └── lowres/
#     └── Shot001_0001.exr (1080p - 2MB per frame)

# Set up with proxy
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    proxy_path="lowres"  # Uses lowres subfolder
)

# Development: Fast playback with lowres
# Final render: Switch to full-res
```

**Creating Proxy Sequence (Nuke):**
```
# Nuke script for proxy generation
Read {
    file D:/Plates/Shot001/Shot001_####.exr
}
Reformat {
    type "to box"
    box_width 1920
    box_height 1080
    resize fit
    filter Lanczos6
}
Write {
    file D:/Plates/Shot001/lowres/Shot001_####.exr
    compression "ZIP (1 scanline)"
    datatype "16 bit half"
}
```

**Solution 2: Optimize EXR Compression**

**Recommended Settings:**
```
Compression: ZIP (1 scanline) or DWAA
Bit Depth: 16-bit half (not 32-bit float)
Channels: RGBA only (remove extra AOVs)
```

**Re-Export Example (Nuke):**
```
Read {
    file D:/Plates/Shot001/Shot001_####.exr
}
Write {
    file D:/Plates/Shot001_optimized/Shot001_####.exr
    compression "ZIP (1 scanline)"
    datatype "16 bit half"
    channels rgba  # Only export necessary channels
}
```

**Solution 3: Reduce Sequence Frame Range**

```python
# Load only necessary frames (not entire sequence)
# Trim sequence to shot length + handles

# Example: Shot is frames 1001-1120
# Export frames 995-1126 (6-frame handles)
# NOT frames 1-2000 (full timeline)

# Benefits:
# - Fewer files to load
# - Less memory usage
# - Faster seek times
```

**Solution 4: Enable MediaPlayer Caching**

```python
# Load MediaPlayer
media_player = unreal.load_asset("/Game/Media/MP_Shot001_FG")

# Enable caching (if supported)
media_player.set_editor_property("cache_settings", {
    "cache_ahead": 10,  # Cache 10 frames ahead
    "cache_behind": 5   # Cache 5 frames behind
})

# Note: Caching settings may vary by UE version
```

**Solution 5: Move Sequence to Faster Drive**

```
Current: D:\ (HDD - 80 MB/s)
Target: C:\ (SSD - 500 MB/s)

Steps:
1. Copy sequence to SSD
2. Update ImgMediaSource path
3. Re-test performance
```

### Validation

**Checklist:**
- [ ] Frame size <10MB (or using proxy)
- [ ] Resolution appropriate for hardware (1080p for mid-range)
- [ ] Memory usage <4GB for sequence
- [ ] Disk read speed >100 MB/s
- [ ] Playback smooth (no stuttering)
- [ ] Load time <2 seconds for first frame

**Performance Test:**
```
1. Load foreground plate
2. Pilot camera to see ImagePlate
3. Press Play in MediaPlayer
4. Verify:
   - No frame drops during playback
   - Scrubbing timeline responsive
   - No editor freezing
   - Memory usage stable
```

**Proxy Validation:**
```
1. Set up with proxy_path="lowres"
2. Verify lowres sequence loads
3. Test playback (should be smooth)
4. Switch to full-res for final render:
   - Content Browser → MS_{plate_name}
   - Change Sequence Path to parent directory
   - Verify full-res loads
```

---

## Issue 6: Blueprint Template Missing or Misconfigured

### Symptoms
- create_foreground_plate() fails with "Blueprint not found" error
- Camera spawns without ImagePlate component
- Error: "cam_example_Blueprint does not exist"
- ImagePlateFrustumComponent missing from hierarchy

### Diagnosis

**Step 1: Verify Blueprint Exists**

```python
# Check if Blueprint exists
blueprint_path = "/Game/cam_example_Blueprint"
blueprint = unreal.load_asset(blueprint_path)

if blueprint is None:
    print("ERROR: Blueprint template not found!")
    print("Blueprint must be created manually first")
else:
    print(f"Blueprint found: {blueprint.get_name()}")
```

**Step 2: Validate Blueprint Structure**

```python
# Load Blueprint
blueprint_path = "/Game/cam_example_Blueprint"
blueprint = unreal.load_asset(blueprint_path)

if blueprint:
    # Get Blueprint generated class
    blueprint_class = unreal.load_class(None, blueprint_path + "_C")

    # Spawn test instance
    test_camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        blueprint_class,
        [0, 0, 0]
    )

    # Check for ImagePlate component
    image_plate = test_camera.get_component_by_class(unreal.ImagePlateComponent)

    if image_plate:
        print("✓ ImagePlate component found")
    else:
        print("✗ ImagePlate component MISSING")
        print("Blueprint needs ImagePlate component added")

    # Cleanup
    unreal.EditorLevelLibrary.destroy_actor(test_camera)
```

### Solutions

**Solution 1: Create Blueprint Template**

**Manual Creation (Unreal Editor):**
```
1. Content Browser → Right-click → Blueprint Class
2. Pick Parent Class: CineCameraActor
3. Name: cam_example_Blueprint
4. Location: /Game/ (root content folder)
5. Open Blueprint Editor (double-click)
6. Components Panel → Add Component → ImagePlate
7. Attach ImagePlate to CineCameraComponent
8. Compile and Save
```

**Python Creation (Advanced):**
```python
import unreal

# Create Blueprint asset
factory = unreal.BlueprintFactory()
factory.set_editor_property("parent_class", unreal.CineCameraActor)

blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="cam_example_Blueprint",
    package_path="/Game",
    asset_class=unreal.Blueprint,
    factory=factory
)

# Save
unreal.EditorAssetLibrary.save_loaded_asset(blueprint)

print("Blueprint created: /Game/cam_example_Blueprint")
print("IMPORTANT: Manually add ImagePlate component in Blueprint Editor")
```

**Note:** Python API cannot add components to Blueprints at design time. ImagePlate component must be added manually in Blueprint Editor.

**Solution 2: Fix Blueprint Path**

```python
# If Blueprint exists but at different path
# Update ForegroundPlateSetup.py to use correct path

# Example: Blueprint at /Game/Blueprints/cam_example_Blueprint
# Update script:
BLUEPRINT_PATH = "/Game/Blueprints/cam_example_Blueprint"

# Or specify in create_foreground_plate call (if supported)
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    camera_blueprint_path="/Game/Blueprints/cam_example_Blueprint"
)
```

**Solution 3: Verify Blueprint Class Path**

```python
# Blueprint class path requires "_C" suffix
blueprint_path = "/Game/cam_example_Blueprint"
blueprint_class_path = blueprint_path + "_C"

# Load class
blueprint_class = unreal.load_class(None, blueprint_class_path)

if blueprint_class is None:
    print("ERROR: Blueprint class not found!")
    print(f"Tried: {blueprint_class_path}")
    print("Verify Blueprint compiled successfully")
else:
    print(f"Blueprint class loaded: {blueprint_class.get_name()}")
```

**Solution 4: Recompile Blueprint**

```
If Blueprint exists but class won't load:

1. Content Browser → cam_example_Blueprint
2. Double-click to open Blueprint Editor
3. Toolbar → Compile button
4. Verify "Compile Successful" message
5. Save and close
6. Retry create_foreground_plate()
```

### Validation

**Checklist:**
- [ ] Blueprint exists at /Game/cam_example_Blueprint
- [ ] Blueprint based on CineCameraActor parent class
- [ ] ImagePlate component added to Blueprint
- [ ] ImagePlate attached to CineCameraComponent
- [ ] Blueprint compiles without errors
- [ ] Blueprint class loads with "_C" suffix

**Test Procedure:**
```python
# Full validation script
import unreal

# 1. Load Blueprint
blueprint_path = "/Game/cam_example_Blueprint"
blueprint = unreal.load_asset(blueprint_path)
assert blueprint is not None, "Blueprint not found"

# 2. Load Blueprint class
blueprint_class = unreal.load_class(None, blueprint_path + "_C")
assert blueprint_class is not None, "Blueprint class not found"

# 3. Spawn test instance
test_camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    blueprint_class,
    [0, 0, 0]
)
assert test_camera is not None, "Failed to spawn Blueprint"

# 4. Check ImagePlate component
image_plate = test_camera.get_component_by_class(unreal.ImagePlateComponent)
assert image_plate is not None, "ImagePlate component missing"

# 5. Cleanup
unreal.EditorLevelLibrary.destroy_actor(test_camera)

print("✓ Blueprint validation PASSED")
```

---

## Issue 7: ImagePlate Plugin Not Enabled

### Symptoms
- Error: "Module 'ImagePlate' not found"
- ImagePlate component not available in component list
- Blueprint cannot add ImagePlate component
- Python error: "unreal.ImagePlateComponent does not exist"

### Diagnosis

**Step 1: Check Plugin Status**

```
Manual Check:
1. Edit → Plugins
2. Search: "ImagePlate"
3. Check status:
   - Enabled (✓) → Plugin active
   - Disabled → Plugin inactive
```

**Python Check:**
```python
# Attempt to access ImagePlate class
try:
    image_plate_class = unreal.ImagePlateComponent
    print("✓ ImagePlate plugin is enabled")
except AttributeError:
    print("✗ ImagePlate plugin is NOT enabled")
    print("Enable plugin: Edit → Plugins → ImagePlate")
```

**Step 2: Verify Plugin Installation**

```
Plugin Location:
C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\ImagePlate\

Check:
- [ ] Directory exists
- [ ] ImagePlate.uplugin file exists
- [ ] Binaries folder exists
```

### Solutions

**Solution 1: Enable Plugin**

```
1. Unreal Editor → Edit → Plugins
2. Search: "ImagePlate"
3. Check "Enabled" checkbox
4. Click "Restart Now" button
5. Wait for editor to restart
6. Verify plugin loaded (no errors in Output Log)
```

**Solution 2: Enable Plugin via .uproject File**

```json
// Edit Project.uproject file
{
    "FileVersion": 3,
    "EngineAssociation": "5.8",
    "Plugins": [
        {
            "Name": "ImagePlate",
            "Enabled": true
        }
    ]
}
```

**After editing:**
```
1. Save .uproject file
2. Right-click .uproject → Generate Visual Studio project files
3. Launch Unreal Editor
4. Verify plugin enabled
```

**Solution 3: Verify Plugin Binaries**

```
If plugin enabled but still not working:

1. Close Unreal Editor
2. Navigate to:
   C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\ImagePlate\Binaries\Win64\
3. Check for:
   - UnrealEditor-ImagePlate.dll
   - UnrealEditor-ImagePlate.pdb
4. If missing:
   - Reinstall Unreal Engine
   - Or rebuild plugin from source
```

### Validation

**Checklist:**
- [ ] Plugin appears in Plugins list
- [ ] Plugin enabled checkbox checked
- [ ] Editor restarted after enabling
- [ ] No errors in Output Log
- [ ] ImagePlateComponent available in Python
- [ ] ImagePlate component available in Blueprint editor

**Test Procedure:**
```python
# Full validation script
import unreal

# 1. Check class exists
try:
    image_plate_class = unreal.ImagePlateComponent
    print("✓ ImagePlateComponent class available")
except AttributeError:
    print("✗ ImagePlateComponent class NOT available")
    print("Enable ImagePlate plugin: Edit → Plugins")
    exit()

# 2. Test component creation
try:
    test_component = unreal.new_object(unreal.ImagePlateComponent)
    print("✓ ImagePlateComponent can be instantiated")
except Exception as e:
    print(f"✗ Failed to create ImagePlateComponent: {e}")
    exit()

print("✓ ImagePlate plugin validation PASSED")
```

---

## Issue 8: Memory Issues with Large Sequences

### Symptoms
- Unreal Editor crashes when loading large sequences
- "Out of memory" errors in Output Log
- Editor becomes extremely slow after loading ImagePlate
- Windows shows "Low memory" warnings
- Task Manager shows Unreal using >90% RAM

### Diagnosis

**Step 1: Calculate Sequence Memory Usage**

```python
import os

# Estimate memory usage for sequence
sequence_dir = "D:/Plates/Shot001"
files = [f for f in os.listdir(sequence_dir) if f.endswith(".exr")]

if files:
    # Check first frame size
    first_frame_path = os.path.join(sequence_dir, files[0])
    frame_size_bytes = os.path.getsize(first_frame_path)
    frame_size_mb = frame_size_bytes / (1024 * 1024)

    # Calculate total
    total_frames = len(files)
    total_size_mb = frame_size_mb * total_frames
    total_size_gb = total_size_mb / 1024

    print(f"Frame Size: {frame_size_mb:.2f} MB")
    print(f"Frame Count: {total_frames}")
    print(f"Total Size: {total_size_gb:.2f} GB")

    # Estimate loaded memory (uncompressed in RAM)
    # EXR 16-bit RGBA = width × height × 8 bytes
    # Assume 4K (3840×2160)
    uncompressed_mb = (3840 * 2160 * 8) / (1024 * 1024)
    total_uncompressed_gb = (uncompressed_mb * total_frames) / 1024

    print(f"Estimated RAM Usage: {total_uncompressed_gb:.2f} GB")

    # Warning thresholds
    if total_uncompressed_gb > 16:
        print("WARNING: Sequence may exceed available RAM")
        print("Recommendation: Use proxy workflow")
```

**Step 2: Check System Memory**

```python
import psutil

# Get system memory info
mem = psutil.virtual_memory()
total_gb = mem.total / (1024**3)
available_gb = mem.available / (1024**3)
percent_used = mem.percent

print(f"Total RAM: {total_gb:.2f} GB")
print(f"Available RAM: {available_gb:.2f} GB")
print(f"Used: {percent_used:.1f}%")

# Warnings
if available_gb < 4:
    print("WARNING: Low available memory (<4GB)")
    print("Close other applications before loading large sequences")

if percent_used > 80:
    print("WARNING: System memory usage high (>80%)")
    print("Consider restarting system or using proxy workflow")
```

**Step 3: Monitor Unreal Memory Usage**

```
Task Manager → Details Tab → UnrealEditor.exe
Right-click columns → Select columns:
- Memory (Private Working Set)
- Commit Size

Before loading ImagePlate: Note values
After loading ImagePlate: Note values
Difference = memory used by sequence

Red Flags:
- >16GB memory used → Too large for 32GB system
- Memory climbing during playback → Memory leak
- Commit Size >> Physical RAM → Heavy paging (slow)
```

### Solutions

**Solution 1: Use Proxy Workflow (Recommended)**

```python
# Create lowres proxy (1/4 resolution)
# Original: 4K (3840×2160) = 8.3 megapixels
# Proxy: 1080p (1920×1080) = 2.1 megapixels
# Memory reduction: 75%

# Set up with proxy
create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    proxy_path="lowres",  # Uses lowres subfolder
    auto_play_media=True
)

# Benefits:
# - 75% memory reduction
# - 4x faster loading
# - Smooth playback even on 16GB RAM systems
```

**Proxy Creation Script (Python + OpenImageIO):**
```python
# Generate lowres proxy sequence
import OpenImageIO as oiio

input_dir = "D:/Plates/Shot001"
output_dir = "D:/Plates/Shot001/lowres"
os.makedirs(output_dir, exist_ok=True)

for frame_num in range(1, 121):  # 120 frames
    input_path = f"{input_dir}/Shot001_{frame_num:04d}.exr"
    output_path = f"{output_dir}/Shot001_{frame_num:04d}.exr"

    # Read full-res
    input_img = oiio.ImageBuf(input_path)

    # Resize to 1920x1080
    output_spec = oiio.ImageSpec(1920, 1080, 4, oiio.HALF)
    output_img = oiio.ImageBuf(output_spec)
    oiio.ImageBufAlgo.resize(output_img, input_img)

    # Write with compression
    output_img.write(output_path, oiio.HALF, {"compression": "zip"})

    print(f"Processed frame {frame_num}/120")
```

**Solution 2: Reduce Sequence Length**

```python
# Load only shot frames + handles (not entire timeline)

# Example: Shot is 5 seconds (120 frames at 24fps)
# Timeline: 0-2000 frames (exported full timeline by mistake)
# Solution: Export only 114-126 frames (120 frames + 6-frame handles)

# Benefits:
# - 90%+ memory reduction
# - Faster loading
# - Easier to manage
```

**Solution 3: Optimize EXR Settings**

**Re-Export with Lower Bit Depth:**
```
Original: 32-bit float RGBA = 16 bytes per pixel
Optimized: 16-bit half RGBA = 8 bytes per pixel
Memory reduction: 50%

Nuke Write Node:
- Data Type: 16 bit half (NOT 32 bit float)
- Compression: DWAA or ZIP
- Channels: rgba only (remove AOVs)
```

**Solution 4: Increase System Virtual Memory**

```
Windows Settings:
1. System → About → Advanced system settings
2. Advanced tab → Performance → Settings
3. Advanced tab → Virtual memory → Change
4. Uncheck "Automatically manage paging file"
5. Set custom size:
   - Initial: 16384 MB (16GB)
   - Maximum: 32768 MB (32GB)
6. Restart system

Warning: This is a workaround, not a solution
Better solution: Use proxy workflow or add more RAM
```

**Solution 5: Split Sequence into Chunks**

```python
# For very long sequences (500+ frames)
# Split into multiple shots

# Original: Shot001 (500 frames) = 10GB RAM
# Split:
#   Shot001A (150 frames) = 3GB RAM
#   Shot001B (150 frames) = 3GB RAM
#   Shot001C (200 frames) = 4GB RAM

# Each shot loaded independently
# Memory usage reduced per shot
```

### Validation

**Checklist:**
- [ ] Sequence memory usage <50% available RAM
- [ ] Unreal memory usage stable during playback
- [ ] No "Out of memory" errors in log
- [ ] Editor responsive (not freezing)
- [ ] Windows not showing low memory warnings
- [ ] Proxy workflow in place for large sequences

**Memory Test Procedure:**
```
1. Close all other applications
2. Restart Unreal Editor (fresh memory state)
3. Note memory usage before loading:
   - Task Manager → UnrealEditor.exe → Memory
4. Load foreground plate
5. Note memory usage after loading
6. Play sequence for 30 seconds
7. Verify:
   - Memory usage stable (not climbing)
   - No crashes
   - Playback smooth
   - Memory increase <4GB
```

**Proxy Workflow Validation:**
```
1. Create proxy sequence (1/4 resolution)
2. Set up ImagePlate with proxy_path="lowres"
3. Verify lowres loads and plays smoothly
4. Note memory usage (should be ~25% of full-res)
5. For final render:
   - Content Browser → MS_{plate_name}
   - Change Sequence Path to full-res
   - Verify full-res loads (memory usage increases)
```

---

## Advanced Diagnostics

### Python Diagnostic Script

**Complete validation script for all common issues:**

```python
import unreal
import os
import sys

def diagnose_foreground_plate(plate_name):
    """
    Complete diagnostic for foreground plate setup
    Returns dict with results and recommendations
    """
    results = {
        "errors": [],
        "warnings": [],
        "info": [],
        "status": "PASS"
    }

    # 1. Check ImagePlate plugin
    try:
        image_plate_class = unreal.ImagePlateComponent
        results["info"].append("✓ ImagePlate plugin enabled")
    except AttributeError:
        results["errors"].append("✗ ImagePlate plugin NOT enabled")
        results["status"] = "FAIL"
        return results

    # 2. Check Blueprint template
    blueprint_path = "/Game/cam_example_Blueprint"
    blueprint = unreal.load_asset(blueprint_path)
    if blueprint is None:
        results["errors"].append(f"✗ Blueprint not found: {blueprint_path}")
        results["status"] = "FAIL"
        return results
    else:
        results["info"].append(f"✓ Blueprint found: {blueprint_path}")

    # 3. Check camera exists
    camera_name = f"Cam_{plate_name}"
    camera = unreal.EditorLevelLibrary.get_actor_reference(camera_name)
    if camera is None:
        results["errors"].append(f"✗ Camera not found: {camera_name}")
        results["status"] = "FAIL"
        return results
    else:
        results["info"].append(f"✓ Camera found: {camera_name}")

    # 4. Check ImagePlate component
    image_plate = camera.get_component_by_class(unreal.ImagePlateComponent)
    if image_plate is None:
        results["errors"].append("✗ ImagePlate component missing")
        results["status"] = "FAIL"
        return results
    else:
        results["info"].append("✓ ImagePlate component found")

    # 5. Check MediaPlayer
    media_player_path = f"/Game/Media/MP_{plate_name}"
    media_player = unreal.load_asset(media_player_path)
    if media_player is None:
        results["errors"].append(f"✗ MediaPlayer not found: {media_player_path}")
        results["status"] = "FAIL"
    else:
        results["info"].append(f"✓ MediaPlayer found: {media_player_path}")

        # Check playing status
        is_playing = media_player.is_playing()
        if is_playing:
            results["info"].append("✓ MediaPlayer is playing")
        else:
            results["warnings"].append("⚠ MediaPlayer is NOT playing")
            results["warnings"].append("  Fix: media_player.play()")

        # Check duration
        duration = media_player.get_duration()
        if duration > 0:
            results["info"].append(f"✓ Duration: {duration:.2f} seconds")
        else:
            results["errors"].append("✗ Duration is 0 (media not loaded)")
            results["status"] = "FAIL"

    # 6. Check ImgMediaSource
    img_media_source_path = f"/Game/Media/MS_{plate_name}"
    img_media_source = unreal.load_asset(img_media_source_path)
    if img_media_source is None:
        results["errors"].append(f"✗ ImgMediaSource not found: {img_media_source_path}")
        results["status"] = "FAIL"
    else:
        results["info"].append(f"✓ ImgMediaSource found: {img_media_source_path}")

        # Check sequence path
        sequence_path = img_media_source.get_editor_property("sequence_path")
        results["info"].append(f"  Sequence Path: {sequence_path}")

        # Verify path exists (basic check)
        # Note: sequence_path is DirectoryPath object, not string
        # Cannot validate easily in Python

    # 7. Check material
    material_path = f"/Game/Materials/M_{plate_name}"
    material = unreal.load_asset(material_path)
    if material is None:
        # Try material instance
        material_path = f"/Game/Materials/MI_{plate_name}"
        material = unreal.load_asset(material_path)

    if material is None:
        results["errors"].append(f"✗ Material not found: M_{plate_name} or MI_{plate_name}")
        results["status"] = "FAIL"
    else:
        results["info"].append(f"✓ Material found: {material.get_name()}")

        # Check blend mode (if regular material)
        if isinstance(material, unreal.Material):
            blend_mode = material.get_editor_property("blend_mode")
            if blend_mode in [unreal.BlendMode.BLEND_MASKED, unreal.BlendMode.BLEND_TRANSLUCENT]:
                results["info"].append(f"✓ Blend Mode: {blend_mode}")
            else:
                results["warnings"].append(f"⚠ Blend Mode: {blend_mode} (should be Masked or Translucent)")

    # Summary
    if len(results["errors"]) == 0 and len(results["warnings"]) == 0:
        results["status"] = "PASS"
    elif len(results["errors"]) == 0:
        results["status"] = "WARNINGS"

    return results


# Usage
plate_name = "Shot001_FG"
results = diagnose_foreground_plate(plate_name)

print("=" * 60)
print(f"DIAGNOSTIC REPORT: {plate_name}")
print("=" * 60)

if results["info"]:
    print("\nINFO:")
    for msg in results["info"]:
        print(f"  {msg}")

if results["warnings"]:
    print("\nWARNINGS:")
    for msg in results["warnings"]:
        print(f"  {msg}")

if results["errors"]:
    print("\nERRORS:")
    for msg in results["errors"]:
        print(f"  {msg}")

print(f"\nSTATUS: {results['status']}")
print("=" * 60)
```

---

## Getting Help

If issues persist after following this guide:

1. **Check Session Documentation:**
   - `UnrealEngine/unreal-mcp-main/development/Session_2025-10-25_ImagePlate.md`
   - Contains complete architectural details and edge cases

2. **Review Reference Documentation:**
   - `foreground_plate_workflow.md` - Step-by-step process
   - `multi_shot_production.md` - Production patterns

3. **Enable Debug Logging:**
   ```python
   unreal.log("Debug message")
   unreal.log_warning("Warning message")
   unreal.log_error("Error message")
   ```

4. **Check Unreal Output Log:**
   - Window → Developer Tools → Output Log
   - Filter: "ImagePlate" or "MediaPlayer"
   - Look for errors or warnings

5. **Validate with Diagnostic Script:**
   - Run `diagnose_foreground_plate()` script above
   - Follow recommendations in output

---

**Document Version:** 2.0.0
**Last Updated:** 2026-07-06 (UE 5.8 native MCP migration)
**Skill Version:** 2.0.0
**Status:** Production-ready
