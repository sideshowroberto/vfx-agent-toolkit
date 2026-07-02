# Multi-Shot Production - Production Patterns and Scaling

**Purpose:** Production-validated patterns for setting up 5-50+ foreground plates with consistent materials, efficient workflow, and shot isolation.

---

## Overview

**The Challenge:**
- VFX sequences typically have 10-50+ shots
- Each shot needs: MediaSource, MediaPlayer, MediaTexture, Material, Camera
- Setup must be fast, consistent, and maintainable
- Material changes should propagate, but texture changes must be isolated

**The Solution:**
Master Material + Material Instances pattern
- ONE master material with shared logic
- ONE material instance PER SHOT with unique texture
- Update master → All shots update
- Update instance texture → Only that shot changes

---

## Production Patterns

### Pattern 1: Master Material + Instances (Recommended)

**Use When:**
- 5+ shots in sequence
- Want consistent look across shots
- Need ability to update all shots at once
- Want shot isolation (texture changes don't affect other shots)

**Architecture:**
```
M_ForegroundPlate_Master (Master Material)
├── Texture Parameter: PlateTexture (default: None)
├── Scalar Parameter: OpacityMultiplier (default: 1.0)
├── Scalar Parameter: EmissiveMultiplier (default: 1.0)
└── Material Graph (shared logic)

MI_Shot001_FG (Material Instance)
├── Parent: M_ForegroundPlate_Master
└── PlateTexture = MT_Shot001_FG (OVERRIDDEN)

MI_Shot002_FG (Material Instance)
├── Parent: M_ForegroundPlate_Master
└── PlateTexture = MT_Shot002_FG (OVERRIDDEN)

... (50+ instances)
```

**Setup Workflow:**

**Step 1: Create Master Material (One Time)**
```python
# First shot creates master material
result = mcp__unreal-mcp__create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    master_material_path="/Game/Materials/M_ForegroundPlate_Master"
)
# Creates master material + instance for Shot001
```

**Step 2: Create Additional Shots (Reuse Master)**
```python
# Subsequent shots create instances only
for shot_num in range(2, 51):  # Shots 2-50
    result = mcp__unreal-mcp__create_foreground_plate(
        sequence_path=f"D:/Plates/Shot{shot_num:03d}/Shot{shot_num:03d}_0001.exr",
        plate_name=f"Shot{shot_num:03d}_FG",
        master_material_path="/Game/Materials/M_ForegroundPlate_Master"
    )
    # Creates instance referencing master
```

**Benefits:**
- ✅ Material logic shared (one update propagates to all)
- ✅ Texture changes isolated (Shot002 doesn't affect Shot003)
- ✅ Scalable to 100+ shots (instances are lightweight)
- ✅ Consistent look enforced
- ✅ Easy to adjust all shots (change master parameters)

**Example Scenario:**
```
VFX Supervisor: "All plates need to be 20% brighter"

WITHOUT master material:
- Open M_Shot001_FG → Change EmissiveMultiplier → Save
- Open M_Shot002_FG → Change EmissiveMultiplier → Save
- ... (repeat 50 times) ❌

WITH master material:
- Open M_ForegroundPlate_Master → Change EmissiveMultiplier → Save
- All 50 instances update automatically ✅
```

---

### Pattern 2: Unique Materials Per Shot

**Use When:**
- 1-4 shots only (small sequence)
- Each shot needs drastically different material logic
- No need for consistency across shots

**Architecture:**
```
M_Shot001_FG (Unique Material)
M_Shot002_FG (Unique Material)
M_Shot003_FG (Unique Material)
```

**Setup Workflow:**
```python
# Each shot creates unique material
for shot_num in range(1, 5):
    result = mcp__unreal-mcp__create_foreground_plate(
        sequence_path=f"D:/Plates/Shot{shot_num:03d}/Shot{shot_num:03d}_0001.exr",
        plate_name=f"Shot{shot_num:03d}_FG"
        # No master_material_path = unique material
    )
```

**Benefits:**
- ✅ Maximum flexibility per shot
- ✅ No dependencies between shots

**Drawbacks:**
- ❌ Updates must be applied to each shot individually
- ❌ Inconsistency risk (easy to forget to update all shots)
- ❌ Not scalable beyond ~5 shots

---

## Batch Processing Workflows

### Workflow 1: Folder-Based Batch Processing

**Directory Structure:**
```
D:/VFX/Plates/
├── Shot001/
│   └── Shot001_0001.exr, Shot001_0002.exr, ...
├── Shot002/
│   └── Shot002_0001.exr, Shot002_0002.exr, ...
├── Shot003/
│   └── Shot003_0001.exr, Shot003_0002.exr, ...
└── ... (50+ shot folders)
```

**Python Batch Script:**
```python
import os

# Configuration
plates_root = "D:/VFX/Plates"
master_material = "/Game/Materials/M_ForegroundPlate_Master"

# Discover all shot folders
shot_folders = [f for f in os.listdir(plates_root)
                if os.path.isdir(os.path.join(plates_root, f))]

# Process each shot
for shot_folder in sorted(shot_folders):
    shot_path = os.path.join(plates_root, shot_folder)

    # Find first frame (assumes naming: ShotName_0001.exr)
    files = os.listdir(shot_path)
    first_frame = next((f for f in files if f.endswith("_0001.exr")), None)

    if not first_frame:
        print(f"⚠️  Skipping {shot_folder}: No _0001.exr found")
        continue

    sequence_path = os.path.join(shot_path, first_frame)
    plate_name = f"{shot_folder}_FG"

    # Create foreground plate
    print(f"📦 Processing {shot_folder}...")
    result = mcp__unreal-mcp__create_foreground_plate(
        sequence_path=sequence_path,
        plate_name=plate_name,
        master_material_path=master_material
    )

    if result["success"]:
        print(f"   ✅ {shot_folder} complete")
    else:
        print(f"   ❌ {shot_folder} failed: {result['errors']}")

print("\n🎬 Batch processing complete!")
```

**Expected Output:**
```
📦 Processing Shot001...
   ✅ Shot001 complete
📦 Processing Shot002...
   ✅ Shot002 complete
📦 Processing Shot003...
   ✅ Shot003 complete
...
🎬 Batch processing complete!
```

---

### Workflow 2: CSV-Driven Batch Processing

**Use When:** Shot metadata varies (frame ranges, opacity, etc.)

**CSV File (shots.csv):**
```csv
shot_name,sequence_path,opacity,emissive,proxy
Shot001_FG,D:/Plates/Shot001/Shot001_0001.exr,1.0,1.0,lowres
Shot002_FG,D:/Plates/Shot002/Shot002_0001.exr,0.5,2.0,
Shot003_FG,D:/Plates/Shot003/Shot003_0001.exr,1.0,1.0,lowres
```

**Python Batch Script:**
```python
import csv

# Read CSV
with open("D:/VFX/shots.csv", "r") as f:
    reader = csv.DictReader(f)
    shots = list(reader)

# Process each shot
for shot in shots:
    print(f"📦 Processing {shot['shot_name']}...")

    result = mcp__unreal-mcp__create_foreground_plate(
        sequence_path=shot['sequence_path'],
        plate_name=shot['shot_name'],
        opacity_multiplier=float(shot['opacity']),
        emissive_multiplier=float(shot['emissive']),
        proxy_path=shot['proxy'] if shot['proxy'] else None,
        master_material_path="/Game/Materials/M_ForegroundPlate_Master"
    )

    if result["success"]:
        print(f"   ✅ {shot['shot_name']} complete")
    else:
        print(f"   ❌ {shot['shot_name']} failed: {result['errors']}")
```

**Benefits:**
- ✅ Per-shot configuration (opacity, emissive, proxy)
- ✅ Easy to review/edit (spreadsheet-friendly)
- ✅ Version control friendly (text-based)
- ✅ Can be generated by pipeline tools

---

## Naming Conventions

### Standard VFX Naming

**Shot Naming:**
```
Format: [Sequence][Shot][Element]_[Descriptor]
Examples:
- Shot001_FG (foreground plate)
- Shot002_BG (background plate)
- Shot003A_FG (shot variant A)
- Shot010_FG_Ghost (ghosted version)
```

**Asset Naming (Auto-Generated):**
```
MediaSource:  MS_Shot001_FG
MediaPlayer:  MP_Shot001_FG
MediaTexture: MT_Shot001_FG
Material:     M_ForegroundPlate_Master (master)
Material:     MI_Shot001_FG (instance)
Camera:       Cam_Shot001_FG
```

**File System Naming:**
```
Shot001_0001.exr, Shot001_0002.exr, ...
Shot002_0001.exr, Shot002_0002.exr, ...
```

### Variant Naming

**Multiple Plates Per Shot:**
```python
# Foreground plate
mcp__unreal-mcp__create_foreground_plate(
    sequence_path="D:/Plates/Shot001/FG/Shot001_FG_0001.exr",
    plate_name="Shot001_FG"
)

# Background plate
mcp__unreal-mcp__create_foreground_plate(
    sequence_path="D:/Plates/Shot001/BG/Shot001_BG_0001.exr",
    plate_name="Shot001_BG"
)
```

**Shot Variants:**
```python
# Version A
mcp__unreal-mcp__create_foreground_plate(
    sequence_path="D:/Plates/Shot003/v001/Shot003A_0001.exr",
    plate_name="Shot003A_FG"
)

# Version B
mcp__unreal-mcp__create_foreground_plate(
    sequence_path="D:/Plates/Shot003/v002/Shot003B_0001.exr",
    plate_name="Shot003B_FG"
)
```

---

## Material Management

### Updating Master Material

**Scenario:** Need to change blend mode from Masked to Translucent for all shots

**Process:**
1. Content Browser → Find M_ForegroundPlate_Master
2. Double-click → Material Editor
3. Details Panel → Blend Mode → Change to Translucent
4. Save and compile
5. **Result:** All 50 material instances update automatically ✅

**What Updates Automatically:**
- Shading model (Unlit, Lit, etc.)
- Blend mode (Masked, Translucent, Opaque)
- Two-Sided setting
- Material graph logic
- Parameter defaults

**What Does NOT Update:**
- Instance-specific parameter overrides (PlateTexture, OpacityMultiplier, etc.)
- Per-shot texture assignments

---

### Per-Shot Material Adjustments

**Scenario:** Shot025 needs different opacity (0.5 instead of 1.0)

**Process:**
```python
# Option 1: Adjust instance parameters via Python
import unreal

# Load material instance
mi = unreal.load_asset("/Game/Materials/Instances/MI_Shot025_FG")

# Override opacity parameter
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    mi, "OpacityMultiplier", 0.5
)

# Option 2: Manual adjustment
# 1. Content Browser → Find MI_Shot025_FG
# 2. Double-click → Material Instance Editor
# 3. Check "Override" next to OpacityMultiplier
# 4. Set value to 0.5
# 5. Save
```

**Best Practice:**
- Use instances for per-shot adjustments
- Keep master clean (default values)
- Document overrides in shot notes

---

## Proxy to Full-Res Workflow

### Development Phase (Proxy)

**Directory Structure:**
```
D:/Plates/Shot001/
├── Shot001_0001.exr (4K full-res)
├── Shot001_0002.exr
├── ...
└── lowres/
    ├── Shot001_0001.exr (1080p proxy)
    ├── Shot001_0002.exr
    └── ...
```

**Setup (All Shots with Proxy):**
```python
# Batch setup with proxy
for shot_num in range(1, 51):
    mcp__unreal-mcp__create_foreground_plate(
        sequence_path=f"D:/Plates/Shot{shot_num:03d}/Shot{shot_num:03d}_0001.exr",
        plate_name=f"Shot{shot_num:03d}_FG",
        proxy_path="lowres",  # Use lowres subfolder
        master_material_path="/Game/Materials/M_ForegroundPlate_Master"
    )
```

**Result:**
- All MediaSources point to `D:/Plates/ShotXXX/lowres/` folders
- Fast playback during development
- Full frame rate on mid-range workstations

---

### Switching to Full-Res

**Option 1: Manual Switch (Per Shot)**
```
1. Content Browser → Find MS_Shot001_FG
2. Double-click → ImgMediaSource Editor
3. Sequence Path:
   - FROM: D:/Plates/Shot001/lowres
   - TO: D:/Plates/Shot001
4. Save
5. MediaPlayer automatically updates
```

**Option 2: Batch Switch (All Shots)**
```python
# Python script to switch all shots to full-res
import unreal

# Find all ImgMediaSources
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
media_sources = asset_registry.get_assets_by_class("ImgMediaSource")

for asset_data in media_sources:
    # Load asset
    media_source = asset_data.get_asset()

    # Get current path
    current_path = media_source.get_editor_property('sequence_path').path

    # Check if proxy
    if "lowres" in current_path:
        # Remove /lowres from path
        new_path = current_path.replace("/lowres", "")

        print(f"📦 Switching {asset_data.asset_name}")
        print(f"   FROM: {current_path}")
        print(f"   TO: {new_path}")

        # Update path
        media_source.set_editor_property('sequence_path',
            unreal.DirectoryPath(new_path))

        # Save asset
        unreal.EditorAssetLibrary.save_asset(asset_data.package_name)

print("\n✅ All shots switched to full-res")
```

**Expected Output:**
```
📦 Switching MS_Shot001_FG
   FROM: D:/Plates/Shot001/lowres
   TO: D:/Plates/Shot001
📦 Switching MS_Shot002_FG
   FROM: D:/Plates/Shot002/lowres
   TO: D:/Plates/Shot002
...
✅ All shots switched to full-res
```

---

## Shot Management

### Organizing Assets

**Content Browser Structure:**
```
/Game/
├── Media/
│   ├── Sources/
│   │   ├── MS_Shot001_FG
│   │   ├── MS_Shot002_FG
│   │   └── ... (50+ sources)
│   ├── Players/
│   │   ├── MP_Shot001_FG
│   │   ├── MP_Shot002_FG
│   │   └── ... (50+ players)
│   └── Textures/
│       ├── MT_Shot001_FG
│       ├── MT_Shot002_FG
│       └── ... (50+ textures)
├── Materials/
│   ├── M_ForegroundPlate_Master (ONE master)
│   └── Instances/
│       ├── MI_Shot001_FG
│       ├── MI_Shot002_FG
│       └── ... (50+ instances)
└── Cameras/
    ├── Cam_Shot001_FG
    ├── Cam_Shot002_FG
    └── ... (50+ cameras)
```

**Folder Benefits:**
- Quick filtering (Sources vs Players vs Textures)
- Easy to find related assets
- Scalable to 100+ shots

---

### Disabling/Enabling Shots

**Scenario:** Shot015 is on hold, need to hide camera

**Process:**
```python
# Option 1: Hide actor in outliner
import unreal

camera = unreal.EditorLevelLibrary.get_actor_reference("Cam_Shot015_FG")
camera.set_is_temporarily_hidden_in_editor(True)

# Option 2: Move to "Disabled" folder in outliner
# Drag Cam_Shot015_FG to /Disabled folder in World Outliner

# Option 3: Pause MediaPlayer
media_player = unreal.load_asset("/Game/Media/Players/MP_Shot015_FG")
media_player.pause()
```

---

### Deleting Shots

**Scenario:** Shot020 cut from sequence, need to clean up

**Manual Process:**
```
1. Delete camera:
   - World Outliner → Right-click Cam_Shot020_FG → Delete

2. Delete assets:
   - Content Browser → Select all Shot020 assets:
     - MS_Shot020_FG
     - MP_Shot020_FG
     - MT_Shot020_FG
     - MI_Shot020_FG (keep master!)
   - Right-click → Delete
   - Fix Up Redirectors (important!)
```

**Python Cleanup Script:**
```python
import unreal

def delete_shot(shot_name):
    """Delete all assets for a shot"""

    # Asset paths to delete
    assets_to_delete = [
        f"/Game/Media/Sources/MS_{shot_name}",
        f"/Game/Media/Players/MP_{shot_name}",
        f"/Game/Media/Textures/MT_{shot_name}",
        f"/Game/Materials/Instances/MI_{shot_name}"
    ]

    # Delete each asset
    for asset_path in assets_to_delete:
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            print(f"🗑️  Deleting {asset_path}")
            unreal.EditorAssetLibrary.delete_asset(asset_path)

    # Delete camera actor
    camera_name = f"Cam_{shot_name}"
    camera = unreal.EditorLevelLibrary.get_actor_reference(camera_name)
    if camera:
        print(f"🗑️  Deleting {camera_name}")
        unreal.EditorLevelLibrary.destroy_actor(camera)

    print(f"✅ {shot_name} deleted")

# Usage
delete_shot("Shot020_FG")
```

---

## Performance Optimization

### Memory Management

**Challenge:** 50 shots × 500MB each = 25GB memory usage

**Solution 1: Level Streaming**
```
Create level per shot group:
- Level_Shots001-010 (10 cameras)
- Level_Shots011-020 (10 cameras)
- Level_Shots021-030 (10 cameras)

Only load active level → 5GB memory instead of 25GB
```

**Solution 2: MediaPlayer Pooling**
```python
# Don't auto-play all MediaPlayers
# Play only when shot is active in Sequencer

# In Sequencer:
# - Add Media Track
# - Add Shot001 clip → Plays MP_Shot001_FG
# - Add Shot002 clip → Plays MP_Shot002_FG
# Only one player active at a time
```

**Solution 3: Proxy Workflow**
```
1080p proxy: ~100MB per shot × 50 = 5GB ✅
4K full-res: ~500MB per shot × 50 = 25GB ❌

Use proxy during development, full-res only for final render
```

---

### Playback Optimization

**Issue:** 4K EXR sequences drop frames (12fps instead of 24fps)

**Solutions:**

**1. Proxy Workflow:**
```python
# Use 1080p proxy during preview
mcp__unreal-mcp__create_foreground_plate(
    ...,
    proxy_path="lowres"
)
```

**2. ImgMedia Cache Settings:**
```
Edit → Project Settings → Plugins → ImgMedia
- Cache Size: 2GB (increase from default 1GB)
- Cache Mode: Behind + Ahead
- Max Cache Size: 4GB
```

**3. SSD Storage:**
```
Move image sequences to SSD (not HDD)
- HDD: ~100MB/s → 4K EXR = 12fps max
- SSD: ~500MB/s → 4K EXR = 24fps+ ✅
```

---

## Production Checklist

### Pre-Production Setup

- [ ] Create master material (M_ForegroundPlate_Master)
- [ ] Verify Blueprint camera template exists (cam_example_Blueprint)
- [ ] Verify ImagePlate plugin enabled
- [ ] Set up directory structure (D:/Plates/ShotXXX/)
- [ ] Generate proxy sequences if needed (lowres subfolder)
- [ ] Create shot list (CSV or spreadsheet)

### Per-Shot Setup

- [ ] Run create_foreground_plate() with master_material_path
- [ ] Verify camera created (World Outliner)
- [ ] Verify MediaPlayer playing (Content Browser)
- [ ] Pilot camera to check ImagePlate visible
- [ ] Adjust material instance if needed (opacity/emissive)

### Post-Production

- [ ] Switch proxy to full-res (if applicable)
- [ ] Update master material for final look
- [ ] Verify all shots update correctly
- [ ] Delete unused shots (clean up assets)
- [ ] Archive project (include master material)

---

## Case Study: 50-Shot Sequence

**Project:** VFX set extension for 50-shot sequence

**Setup:**
```
Sequence: D:/Plates/Shot001/ through D:/Plates/Shot050/
Format: 4K EXR with alpha channel
Duration: 120 frames per shot (5 seconds @ 24fps)
Total: 6,000 frames, ~240GB
```

**Workflow:**

**Day 1: Initial Setup (Proxy)**
```python
# Create master material with Shot001
mcp__unreal-mcp__create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG",
    proxy_path="lowres",
    master_material_path="/Game/Materials/M_ForegroundPlate_Master"
)

# Batch remaining 49 shots (proxy)
for shot_num in range(2, 51):
    mcp__unreal-mcp__create_foreground_plate(
        sequence_path=f"D:/Plates/Shot{shot_num:03d}/Shot{shot_num:03d}_0001.exr",
        plate_name=f"Shot{shot_num:03d}_FG",
        proxy_path="lowres",
        master_material_path="/Game/Materials/M_ForegroundPlate_Master"
    )

# Time: ~30 seconds for 50 shots ✅
```

**Week 1-2: Development (Proxy)**
- Align CG elements to plates
- Adjust lighting to match
- Preview in Sequencer at full 24fps
- Memory usage: ~5GB (proxy)

**Week 3: Final Render (Full-Res)**
```python
# Switch all shots to full-res
[Run batch switch script from above]

# Final render settings:
# - MovieRenderQueue
# - 4K output
# - Match plate frame range (120 frames per shot)
```

**Results:**
- ✅ 50 shots set up in <1 minute (vs 8+ hours manual)
- ✅ Consistent look across all shots (master material)
- ✅ Per-shot adjustments where needed (material instances)
- ✅ Smooth development workflow (proxy)
- ✅ High-quality final renders (full-res)

---

## Troubleshooting Multi-Shot Issues

### Issue 1: Texture Change Affects All Shots

**Symptom:**
```
Changed Shot002 texture → Shot003 also changed ❌
```

**Diagnosis:**
```python
# Check if using material instances
mi = unreal.load_asset("/Game/Materials/Instances/MI_Shot002_FG")
parent = mi.get_editor_property('parent')

if parent.get_name() != "M_ForegroundPlate_Master":
    print("❌ ERROR: Not using master material pattern")
```

**Fix:**
```python
# Re-create with master_material_path parameter
mcp__unreal-mcp__create_foreground_plate(
    ...,
    master_material_path="/Game/Materials/M_ForegroundPlate_Master"
)
```

---

### Issue 2: Master Material Change Doesn't Propagate

**Symptom:**
```
Changed M_ForegroundPlate_Master → Instances didn't update ❌
```

**Diagnosis:**
```
Instance has parameter override → Override takes precedence
```

**Fix:**
```
1. Open material instance (MI_Shot025_FG)
2. Find overridden parameter (checkbox checked)
3. Un-check override to inherit from master
4. Save
```

---

### Issue 3: Batch Processing Fails Mid-Way

**Symptom:**
```
Shots 1-15 created ✅
Shot 16 failed ❌
Shots 17-50 not created ❌
```

**Diagnosis:**
```python
# Check error in result
result = mcp__unreal-mcp__create_foreground_plate(...)
if not result["success"]:
    print(f"Error: {result['errors']}")
    # Common: "First frame not found"
```

**Fix:**
```python
# Add error handling to batch script
for shot_num in range(1, 51):
    try:
        result = mcp__unreal-mcp__create_foreground_plate(...)
        if result["success"]:
            print(f"✅ Shot{shot_num:03d}")
        else:
            print(f"❌ Shot{shot_num:03d}: {result['errors']}")
    except Exception as e:
        print(f"❌ Shot{shot_num:03d}: {str(e)}")
        continue  # Continue with next shot
```

---

## Reference

**Related Documentation:**
- Core workflow: foreground_plate_workflow.md
- Troubleshooting: troubleshooting.md
- Main skill: unreal-vfx-automation/SKILL.md

**Session Logs:**
- Session_2025-10-25_ImagePlate.md (ImagePlate discovery)

**Scripts:**
- ForegroundPlateSetup.py (core automation)
- Batch processing examples (this document)

**Version:** 1.0.0
**Last Updated:** 2025-10-25
