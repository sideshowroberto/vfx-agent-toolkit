# Installation Guide - Nuke Auto-Tiling Tool

## File Structure

```
.claude/skills/nuke-tiling-tool/
├── scripts/
│   ├── auto_tile_processor.py      # Core implementation
│   ├── auto_tile_processor_1k.py   # 1K tiles (1024x1024)
│   └── auto_tile_processor_2k.py   # 2K tiles (2048x2048)
├── SKILL.md
├── README.md
└── INSTALLATION.md (this file)
```

---

## Option 1: W_hotbox Integration (Recommended)

If you have **w_hotbox** installed, add these buttons:

### Step 1: Open w_hotbox Manager

In Nuke: `Alt+W` or your w_hotbox hotkey

### Step 2: Add Python Buttons

**Button 1: Auto-Tile 2K**
```python
# Button Name: Auto-Tile 2K
# Category: ML Processing
# Icon: (optional) use any icon

import sys
scripts_path = '<workspace>/.claude/skills/nuke-tiling-tool/scripts'
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

execfile(scripts_path + '/auto_tile_processor_2k.py')
```

**Button 2: Auto-Tile 1K**
```python
# Button Name: Auto-Tile 1K
# Category: ML Processing
# Icon: (optional) use any icon

import sys
scripts_path = '<workspace>/.claude/skills/nuke-tiling-tool/scripts'
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

execfile(scripts_path + '/auto_tile_processor_1k.py')
```

### Step 3: Save w_hotbox Configuration

Your w_hotbox should now have two buttons for instant tiling!

---

## Option 2: Nuke Menu Integration (Team-Wide)

For team members without w_hotbox, add to Nuke menu.

### Step 1: Edit menu.py

Location: `~/.nuke/menu.py` (or your studio's shared menu.py)

### Step 2: Add Menu Items

```python
# ============================================================================
# AUTO-TILING FOR ML PROCESSING
# ============================================================================

import nuke
import sys

# Add scripts path
TILING_SCRIPTS_PATH = '<workspace>/.claude/skills/nuke-tiling-tool/scripts'
if TILING_SCRIPTS_PATH not in sys.path:
    sys.path.insert(0, TILING_SCRIPTS_PATH)

# Create custom menu
ml_menu = nuke.menu('Nuke').addMenu('ML Tools')

# Add 2K tiling
def run_auto_tile_2k():
    """Run auto-tiling with 2K tiles"""
    execfile(TILING_SCRIPTS_PATH + '/auto_tile_processor_2k.py')

ml_menu.addCommand('Auto-Tile 2K (2048x2048)', run_auto_tile_2k, 'alt+shift+t')

# Add 1K tiling
def run_auto_tile_1k():
    """Run auto-tiling with 1K tiles"""
    execfile(TILING_SCRIPTS_PATH + '/auto_tile_processor_1k.py')

ml_menu.addCommand('Auto-Tile 1K (1024x1024)', run_auto_tile_1k, 'alt+shift+ctrl+t')
```

### Step 3: Restart Nuke

The menu items will appear under **Nuke > ML Tools**

**Keyboard Shortcuts:**
- `Alt+Shift+T` - Auto-Tile 2K
- `Alt+Shift+Ctrl+T` - Auto-Tile 1K

---

## Option 3: Manual Execution (Script Editor)

For one-off usage or testing:

### For 2K Tiles:

```python
import sys
sys.path.insert(0, '<workspace>/.claude/skills/nuke-tiling-tool/scripts')
execfile('<workspace>/.claude/skills/nuke-tiling-tool/scripts/auto_tile_processor_2k.py')
```

### For 1K Tiles:

```python
import sys
sys.path.insert(0, '<workspace>/.claude/skills/nuke-tiling-tool/scripts')
execfile('<workspace>/.claude/skills/nuke-tiling-tool/scripts/auto_tile_processor_1k.py')
```

---

## Quick Start Workflow

1. **Select** a Read node with your large plate (e.g., 5760x5760)
2. **Run** the tiling script (w_hotbox button, menu, or script editor)
3. **Wait** for the node tree to be created
4. **Replace** the orange NoOp nodes with your ML nodes (ViTMatte, etc.)
5. **Connect** your Viewer to the `Reformat_Final` node
6. **Render** and verify seamless blending

---

## Customization

### Change Overlap Amount

Edit the script files and change:
```python
result = create_tiling_setup(tile_size='2K', overlap=128)
```

To:
```python
result = create_tiling_setup(tile_size='2K', overlap=256)  # Larger overlap
```

### Support for Other Tile Sizes

Edit `auto_tile_processor.py` and add to `TILE_SIZES` dict:
```python
TILE_SIZES = {
    '1K': 1024,
    '2K': 2048,
    '4K': 4096,  # Add custom size
}
```

---

## Troubleshooting

### "No module named 'auto_tile_processor'"

**Fix:** Check the `TILING_SCRIPTS_PATH` points to the correct location.

### "No node selected"

**Fix:** Select a Read node or any image node before running the script.

### "Image too small for tiling"

**Fix:** Your image is smaller than the tile size. Use a smaller tile size or process directly without tiling.

### Visible seams in output

**Fix:**
1. Ensure all ML nodes have identical settings
2. Try increasing overlap to 256px
3. Verify tile mask expressions are correct

---

## Team Deployment

### Shared Studio Setup

1. **Copy scripts to shared network location:**
   ```
   //studio/pipeline/nuke/scripts/auto_tiling/
   ```

2. **Update menu.py paths:**
   ```python
   TILING_SCRIPTS_PATH = '//studio/pipeline/nuke/scripts/auto_tiling'
   ```

3. **Distribute menu.py** to team via studio pipeline

4. **Document** in team wiki/pipeline docs

---

## Version History

- **1.0.0** (2026-01-21)
  - Initial release
  - 1K and 2K tile support
  - Expression-based gradient blending
  - Dynamic layout from input position
  - Automatic grid calculation
  - Support for any aspect ratio

---

## Credits

Created by Claude Code for VFX compositing workflows.
Developed by Rob Williams for a high-resolution commercial plate pipeline.

## Support

For issues or feature requests, contact your pipeline TD or add to team's issue tracker.
