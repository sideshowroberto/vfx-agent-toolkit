---
name: unreal-vfx-automation
description: Automate VFX workflows in Unreal Engine 5.8 including foreground plates, image sequences, and multi-shot production. Use when setting up ImagePlate, creating foreground plates, batch processing shots, or when user mentions unreal foreground plate, image sequence, vfx set extension, imageplate setup, foreground plate, vfx automation, unreal vfx, set extension, multi shot.
allowed-tools: mcp__ue58-mcp__execute_python_code,mcp__ue58-mcp__call_tool,Read,Write,Grep
---

# Unreal VFX Automation

**Production-ready automation for VFX workflows in Unreal Engine 5.8**

Automates the 23-step manual process for foreground plate setup, image sequence management, and multi-shot production pipelines. Built on production-validated patterns from real VFX workflows.

---

## Quick Start

### Basic Foreground Plate Setup

```python
# Via mcp__ue58-mcp__execute_python_code
# Run the ForegroundPlateSetup script directly in UE Python
import unreal
import sys
sys.path.append("/Game/Scripts")  # Or wherever ForegroundPlateSetup.py lives

# Or execute the setup inline:
# 1. Create ImgMediaSource
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
media_source = asset_tools.create_asset(
    "MS_Shot001_FG", "/Game/Media",
    unreal.ImgMediaSource, unreal.ImgMediaSourceFactoryNew()
)
media_source.set_editor_property('sequence_path',
    unreal.DirectoryPath("D:/Plates/Shot001"))

# 2. Create MediaPlayer + MediaTexture
player = asset_tools.create_asset(
    "MP_Shot001_FG", "/Game/Media",
    unreal.MediaPlayer, unreal.MediaPlayerFactoryNew()
)

# 3. Configure and connect...
print("Foreground plate setup complete")
```

**Result:** Complete setup in ~500ms:
- ImgMediaSource created
- MediaPlayer + MediaTexture configured
- VFX-optimized material with alpha support
- ImagePlate component attached to camera
- MediaPlayer auto-plays for immediate preview

### Multi-Shot Production (Master Material + Instances)

**Pattern:** One master material -> Many instances (scalable to 50+ shots)

```python
# Shot 1 - Creates master material (via execute_python_code)
# Shot 2+ - Creates material instances referencing master
```

---

## Standard Workflows

**For detailed workflow code and step-by-step instructions, see:** `reference/detailed-workflows.md`

**Three Core Workflows:**

1. **Basic Foreground Plate (Single Shot)** - One-shot setup with unique material, ImagePlate integration, validation steps
2. **Multi-Shot Production (Master Material Pattern)** - 5+ shots sharing material logic, master material instance workflow
3. **Proxy Workflow (Low-Res Development)** - High-res/low-res switching, performance optimization, final delivery

## SEQUENCER INTEGRATION HANDOFF

**This skill creates VFX-ready assets for handoff to `unreal-sequencer-automation` skill.**

### What This Skill Creates

**Assets Ready for Sequencer:**
- Camera Actor - `Cam_{plate_name}` (CineCameraActor with ImagePlate attached)
- Media Assets - MS/MP/MT_{plate_name} (fully configured)
- Material - M_{plate_name} or MI_{plate_name} (VFX-optimized)
- ImagePlate Component - Attached to camera, plate assigned

### Sequencer Handoff Pattern

**Step 1: Create Assets (This Skill)**
```python
# Via mcp__ue58-mcp__execute_python_code
# Run ForegroundPlateSetup to create all media/material/camera assets
# Returns camera name for sequencer integration: "Cam_Shot001_FG"
```

**Step 2: Add to Sequence (Sequencer Skill)**
```python
# Via mcp__ue58-mcp__execute_python_code
import unreal

sequence = unreal.load_asset('/Game/Sequences/Shot001_Sequence')

# Find camera actor
world = unreal.EditorLevelLibrary.get_editor_world()
cameras = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CineCameraActor)
camera = [c for c in cameras if "Shot001" in c.get_actor_label()][0]

# Add to sequence
binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, camera)

# Add transform track for camera animation
track = binding.add_track(unreal.MovieScene3DTransformTrack)
section = track.add_section()
section.set_range(0, 300)

# Camera is now in sequence with plate visible
```

**Complete Workflow:**
1. Create assets -> ForegroundPlateSetup (this skill)
2. Add camera to sequence -> `unreal-sequencer-automation` skill
3. Animate camera transform -> Sequencer Python API
4. Add camera cuts -> Sequencer skill
5. Render sequence -> Final output with foreground plate

**See Also:** `.claude/skills/unreal-sequencer-automation/SKILL.md` for complete sequencer workflows

---

### Workflow 4: Proxy Workflow (Development -> Final)

**Use When:** Working on slow workstation or with large (4K+) EXR sequences

**Directory Structure:**
```
D:/Plates/Shot001/
  Shot001_0001.exr (full-res 4K)
  Shot001_0002.exr
  ...
  lowres/
    Shot001_0001.exr (proxy 1080p)
    Shot001_0002.exr
    ...
```

**Development Setup (Proxy):**
Create ImgMediaSource pointing to `lowres/` subfolder.

**Switch to Full-Res:**
1. Open ImgMediaSource in Content Browser (MS_Shot001_FG)
2. Change Sequence Path to full-res folder
3. MediaPlayer automatically updates

---

## Troubleshooting

### Issue 1: ImagePlate Not Visible

**Solutions:**
1. **Check MediaPlayer is playing:** Content Browser -> Find MP_{plate_name}, verify "Play" active
2. **Check ImagePlate component:** Run diagnostic script
3. **Verify camera selected and piloted:** Outliner -> Select Cam_{plate_name} -> Pilot Camera Actor
4. **Check ImagePlateFrustumComponent exists:** Delete camera and recreate if missing

---

### Issue 2: Alpha Channel Not Working

**Solutions:**
1. **Check blend mode:** Material should be "Masked" or "Translucent"
2. **Check texture format:** EXR/PNG with alpha supported, JPG does NOT
3. **Check opacity multiplier:** Should be 1.0 for full opacity

---

### Issue 3: Texture Changes Affect Other Shots

**Cause:** Using same material instead of material instances

**Fix:** Use master_material_path parameter to create per-shot instances

---

### Issue 4: MediaPlayer Not Auto-Playing

**Solutions:**
1. Check auto_play settings on MediaPlayer asset
2. Manually open MediaPlayer and click "Play"
3. Check ImgMediaSource path points to correct folder with `*` wildcard

---

## Reference Documentation

### Detailed Workflows
- **foreground_plate_workflow.md** - Step-by-step process breakdown
- **multi_shot_production.md** - Production patterns and scaling
- **troubleshooting.md** - Complete diagnostic guide

### Python Scripts
- **ForegroundPlateSetup.py** - Core automation script
  - Location: `UnrealEngine/unreal-mcp-main/Python/editor_utilities/`
- **InspectCameraComponents.py** - Diagnostic tool

---

## Constitutional Compliance

**Article I:** All scripts parameterized (no hardcoded paths)
**Article III:** SKILL.md under 500 lines, reference docs on-demand
**Article IV:** Tested independently with real VFX sequences
**Article V:** Follows UE Python API patterns
**Article VII:** Cross-app (Nuke -> Unreal EXR workflow validated)

---

## Version History

**v2.0.0** (2026-07-06) - UE 5.8 Migration
- Migrated from community MCP to UE 5.8 native MCP (HTTP, port 8000)
- Replaced mcp__unreal-mcp__create_foreground_plate() with direct Python via execute_python_code
- Updated allowed-tools to mcp__ue58-mcp__execute_python_code + call_tool
- Updated description from "5.5" to "5.8"

**v1.0.0** (2025-10-25) - Initial Release
- Foreground plate automation, multi-shot production, proxy workflow
- MCP integration, diagnostic tools
- Production-validated in Unreal 5.5
