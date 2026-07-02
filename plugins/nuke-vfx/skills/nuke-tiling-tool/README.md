# Nuke Auto-Tiling Tool for ML Processing

Automated image tiling for ML nodes (ViTMatte, etc.) that work best with smaller image sizes.

## Quick Start

### 1. Recommended: Use Separate Scripts for 1K/2K

**For 2K tiles (2048x2048) - Most common:**
```python
import sys
sys.path.insert(0, '<workspace>/.claude/skills/nuke-tiling-tool/scripts')
execfile('<workspace>/.claude/skills/nuke-tiling-tool/scripts/auto_tile_processor_2k.py')
```

**For 1K tiles (1024x1024) - Memory-constrained GPUs:**
```python
import sys
sys.path.insert(0, '<workspace>/.claude/skills/nuke-tiling-tool/scripts')
execfile('<workspace>/.claude/skills/nuke-tiling-tool/scripts/auto_tile_processor_1k.py')
```

### 2. Replace Orange NoOp Placeholders

After running the script, you'll see **orange NoOp nodes** named `MLNode_Tile_X_Y`.

**Replace each NoOp with your ML node:**
1. Delete the NoOp placeholder
2. Insert your ML node (e.g., ViTMatte)
3. It will auto-connect to Reformat above and Expression below

**Tip:** Configure your ML node settings on the first tile, then copy-paste to all other tiles.

### 3. Connect Viewer

Connect your existing Viewer to the **`Reformat_Final`** node to see the final merged result.

## What It Creates

```
Input Image (5760x5760)
    ↓
Horizontal Dot distribution
    ↓     ↓     ↓
    │     │     └─ Tile (2,2): Transform
    │     │                    → Reformat (to 2K)
    │     │                    → NoOp (orange - swap for ML node)
    │     │                    → Expression (mask gradient)
    │     │                    → Premult (apply mask.a)
    │     │                    → InverseTransform
    │     │                    ↓
    │     └─ Tile (1,1): [same vertical stack]
    │                    ↓
    └─ Tile (0,0): [same vertical stack]
                   ↓
    ┌──────────────┴──────────────┐
    Merge2 (plus, rgba) → Merge2 → Merge2 ...
                                   ↓
                          Reformat_Final (back to 5760x5760)
                                   ↓
                          [Connect your Viewer here]
```

## Examples

### Example 1: ViTMatte on 5760x5760 Plate

```python
# 1. Load your plate
read = nuke.createNode('Read')
read['file'].setValue('/path/to/plates/plate.####.exr')

# 2. Create tiling setup
import sys
sys.path.append('<workspace>/.claude/skills/nuke-tiling-tool/scripts')
from auto_tile_processor import create_tiling_setup

result = create_tiling_setup(input_node=read, tile_size='2K')

# Output:
# Creating tiling setup:
#   Input: Read1 (5760x5760)
#   Tile size: 2K (2048x2048)
#   Overlap: 128px
#   Grid: 3x3 (9 tiles)
#   Created 9 tile branches
#   Created merge tree

# 3. Replace Group nodes with ViTMatte
# Find nodes: MLNode_Tile_0_0, MLNode_Tile_0_1, ..., MLNode_Tile_2_2
# Replace each with ViTMatte gizmo

# 4. Render
# Check TiledOutput_Viewer for final result
```

### Example 2: 8K Image with 1K Tiles

```python
# Smaller tiles for memory-constrained GPUs
result = create_tiling_setup(tile_size='1K', overlap=128)

# For 8192x8192 image:
# Grid: 9x9 (81 tiles)
# More tiles = more processing, but less memory per tile
```

### Example 3: Non-Square Image

```python
# Works with any aspect ratio
# Example: 7680x4320 (8K cinema)
result = create_tiling_setup(tile_size='2K')

# Grid: 4x3 (12 tiles)
# Automatically calculates grid_x ≠ grid_y
```

## Parameters Reference

### `create_tiling_setup(input_node, tile_size, overlap)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_node` | `nuke.Node` | Selected node | Input image node to tile |
| `tile_size` | `str` | `'2K'` | Tile size: `'1K'` (1024x1024) or `'2K'` (2048x2048) |
| `overlap` | `int` | `128` | Overlap between tiles in pixels |

**Returns:** Dict with:
- `status`: `'success'` or `'error'`
- `message`: Status message
- `grid`: `(grid_x, grid_y)` tuple
- `tile_count`: Total number of tiles
- `placeholders`: List of NoOp nodes to replace
- `output`: Final Reformat node (connect viewer here)
- `final_reformat`: Same as output

## How Blending Works

### Expression-Based Gradient Masks

Instead of blurring the alpha (which destroys detail), we create **gradient masks** that control how much each tile contributes in overlap zones.

**Visual Example:**

```
Tile Overlap Zone (128px):
┌──────────────────┬──────────────────┐
│  Tile A          │  Overlap         │  Tile B
│  Mask = 1.0      │  Zone            │  Mask = 1.0
│  (full strength) │  Tile A: 1.0→0.0 │  (full strength)
│                  │  Tile B: 0.0→1.0 │
└──────────────────┴──────────────────┘
                   ↑
            128px gradient falloff
```

**Expression Node Logic:**

**CRITICAL:** Frame edges stay SHARP, interior tile boundaries BLEND.

```python
# X direction (horizontal):
if tile_x == 0:                    # Leftmost column
    smoothstep(0, 128, x)          # Only fade IN from left
elif tile_x == grid_x - 1:         # Rightmost column
    smoothstep(2048, 1920, x)      # Only fade OUT to right
else:                              # Middle columns
    smoothstep(0, 128, x) * smoothstep(2048, 1920, x)  # Both edges

# Y direction (vertical): same pattern
```

**Examples for 3x3 grid:**
- **Tile (0,0) top-left**: `smoothstep(0, 128, x) * smoothstep(0, 128, y)` - only interior edges
- **Tile (1,1) center**: All 4 edges fade (both directions)
- **Tile (2,2) bottom-right**: `smoothstep(2048, 1920, x) * smoothstep(2048, 1920, y)` - only interior edges

**Result:**
- Frame boundaries: Sharp (no fade at image edges) ✓
- Interior tile boundaries: Smooth gradient blend ✓
- Output to **mask** channel, applied via Premult node ✓

**Why This Works:**
- Preserves ML node output quality (no blur)
- Smooth, seamless blending (no visible seams)
- Efficient (single Expression node per tile)

## Troubleshooting

### Q: "No node selected" error

**A:** Select an input image node (Read, etc.) before running the script:

```python
# Select node in GUI first, OR
input_node = nuke.toNode('Read1')
result = create_tiling_setup(input_node=input_node)
```

### Q: Visible seams in output

**Possible causes:**

1. **ML node settings differ between tiles**
   - Solution: Copy first ML node settings to all tiles
   - Ensure all ViTMatte nodes have identical parameters

2. **Overlap too small**
   - Solution: Increase overlap
   ```python
   result = create_tiling_setup(overlap=256)  # Double the overlap
   ```

3. **ML node produces inconsistent results**
   - Some ML models have randomness/non-determinism
   - Solution: Check if ML node has "seed" or "deterministic" setting

### Q: "Image too small for tiling" error

**A:** Your image is smaller than the tile size. No tiling needed - process directly:

```python
# For 1920x1080 image, don't tile:
vitmatte = nuke.createNode('ViTMatte')
# Process entire image at once
```

### Q: Script runs slowly / Nuke freezes

**A:** Creating many tiles can take time. For very large grids:

```python
# 8192x8192 with 1K tiles = 81 tiles
# This is expected to take 10-20 seconds to create all nodes

# Recommendation: Use 2K tiles instead
result = create_tiling_setup(tile_size='2K')  # Only 25 tiles
```

### Q: How do I know if blending is working?

**A:** Check the Expression mask nodes:

1. Find `TileMask_X_Y` nodes
2. View the alpha channel (should show gradient falloff at edges)
3. Center tiles should have gradients on all 4 edges
4. Corner tiles should only have gradients on 2 edges

### Q: Can I adjust the blend falloff curve?

**A:** Yes, modify the Expression nodes:

```python
# Find TileMask nodes, edit expr3
# Current: smoothstep (smooth S-curve)
# Options:
# - Linear: x / 128 (less smooth)
# - Custom: smoothstep(0, 128, x) * smoothstep(0, 128, x)  (sharper falloff)
```

## Advanced Usage

### Custom Overlap Per Edge

If you want different overlap amounts:

```python
# Edit the script constants
DEFAULT_OVERLAP = 256  # Increase from 128
```

### Batch Processing Multiple Shots

```python
import os

shots = ['shot001', 'shot002', 'shot003']
plate_dir = '/path/to/plates/'
output_dir = '/path/to/output/'

for shot in shots:
    nuke.scriptClear()

    # Load plate
    read = nuke.createNode('Read')
    read['file'].setValue(f'{plate_dir}{shot}.####.exr')

    # Create tiling
    result = create_tiling_setup(input_node=read)

    if result['status'] == 'success':
        # TODO: Insert ML nodes into result['placeholders']
        # TODO: Render output

        # Save script
        nuke.scriptSaveAs(f'{output_dir}{shot}_tiled.nk')
```

### Save as Reusable Template

Once you've configured your ML nodes:

```python
# 1. Create tiling setup
result = create_tiling_setup()

# 2. Configure first ML node
ml_node = result['placeholders'][0]
# Set all parameters on ml_node

# 3. Copy to all other placeholders
for placeholder in result['placeholders'][1:]:
    # Copy ml_node settings to placeholder
    pass

# 4. Save as template
nuke.nodeCopy('path/to/template.nk')
```

## Performance Tips

### Tile Size Selection

| Tile Size | Memory Usage | Processing Time | Use Case |
|-----------|-------------|-----------------|----------|
| 1K | Lowest | Slower (more tiles) | Memory-constrained GPUs |
| 2K | Medium | Faster (fewer tiles) | **Recommended for most cases** |

**Example:**
- 5760x5760 with 1K tiles = 6x6 = 36 tiles
- 5760x5760 with 2K tiles = 3x3 = 9 tiles
- **4x fewer tiles with 2K = faster processing**

### Grid Size Impact

| Input Size | Tile Size | Grid | Tiles | Relative Processing Time |
|------------|-----------|------|-------|--------------------------|
| 5760x5760 | 2K | 3x3 | 9 | 1x |
| 5760x5760 | 1K | 6x6 | 36 | ~4x |
| 8192x8192 | 2K | 5x5 | 25 | ~2.7x |

**Recommendation:** Use 2K tiles unless GPU memory requires 1K.

### Render Optimization

When rendering, process tiles in parallel if possible:

```python
# Nuke can render Write nodes in parallel
# Set Write nodes for each tile's output
# Use nuke.execute() with multiple threads
```

## Integration with Nuke MCP

### Via Claude Code

```
User: "Create tiling setup for this 5760x5760 plate using 2K tiles"

Claude will:
1. Detect "tiling setup" trigger
2. Invoke nuke-tiling-tool skill
3. Run create_tiling_setup_with_logger() via MCP
4. Return structured results with NukeMCPLogger format
```

### MCP Python Pattern

```python
# In Nuke MCP bridge
import sys
sys.path.append('<workspace>/.claude/skills/nuke-tiling-tool/scripts')
from auto_tile_processor import create_tiling_setup_with_logger

# This version uses NukeMCPLogger for proper MCP integration
result = create_tiling_setup_with_logger(
    input_node=selected_node,
    tile_size='2K',
    overlap=128
)

# Returns NukeMCPLogger formatted dict:
# {
#   'status': 'success',
#   'session': 'AutoTileProcessor',
#   'logs': [...],
#   'stats': {'grid_size': '3x3', 'tile_count': 9},
#   'grid': (3, 3),
#   'tile_count': 9,
#   'placeholders': [<node>, <node>, ...],
#   'output': <viewer_node>
# }
```

## File Structure

```
.claude/skills/nuke-tiling-tool/
├── SKILL.md                          # Skill manifest (triggers, usage)
├── README.md                          # This file
└── scripts/
    └── auto_tile_processor.py        # Main implementation (600 lines)
```

## Version History

- **1.0.0** (2026-01-21)
  - Initial release
  - Auto grid calculation
  - Expression-based gradient masks
  - 1K and 2K tile support
  - NukeMCPLogger integration
  - Edge/corner tile handling

## Credits

Created by Claude Code for VFX compositing workflows.

Inspired by manual tiling workflows for ViTMatte alpha generation on large plates.

## License

Part of the VFX Agent Skills system. See ClaudeCode/development/VFX_SKILL_CONSTITUTION.md for principles.
