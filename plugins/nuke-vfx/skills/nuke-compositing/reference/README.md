# Nuke 15.0 Reference Database

Organized node reference extracted from the official **Nuke 15.0v4 Reference Guide** (1371 pages). Structured for progressive disclosure following VFX Skill Constitution Article III.

## File Structure

| File | Topics | Use When |
|------|--------|----------|
| **01-essential-nodes.md** | Read, Write, Viewer, Merge basics | Starting any comp |
| **02-color-nodes.md** | Grade, ColorCorrect, Exposure, OCIO | Color grading, color space |
| **03-keyer-nodes.md** | Primatte, Keylight, Ultimatte, Cryptomatte | Keying green/blue screen |
| **04-transform-nodes.md** | Transform, Crop, Reformat, CornerPin | Moving, scaling, warping |
| **05-filter-nodes.md** | Blur, Defocus, Sharpen, Denoise, Glow | Blurs, sharpening, cleanup |
| **06-draw-paint-nodes.md** | Roto, RotoPaint, Text, Grain, Noise | Rotoscoping, painting, textures |
| **07-merge-composite-nodes.md** | Merge operations, blend modes, Keymix | Layering, compositing |
| **08-time-nodes.md** | Retime, OFlow, Kronos, TimeWarp | Retiming, optical flow |
| **09-channel-nodes.md** | Shuffle, Copy, Remove, ChannelMerge | Channel manipulation |
| **10-3d-nodes.md** | Camera, ScanlineRender, Project3D | 3D compositing |
| **11-quick-reference.md** | Common workflows, hotkeys, patterns | Quick lookups |

## Quick Node Finder

### Most Common Nodes
- **Read/Write** -> 01-essential-nodes.md
- **Grade/ColorCorrect** -> 02-color-nodes.md
- **Primatte/Keylight** -> 03-keyer-nodes.md
- **Transform/Crop** -> 04-transform-nodes.md
- **Blur/Defocus** -> 05-filter-nodes.md
- **Roto/RotoPaint** -> 06-draw-paint-nodes.md
- **Merge** -> 07-merge-composite-nodes.md

### By Workflow
- **Green screen keying** -> 03-keyer-nodes.md (Keylight, Primatte)
- **Color grading** -> 02-color-nodes.md (Grade, ColorCorrect)
- **Motion blur** -> 05-filter-nodes.md (MotionBlur, VectorBlur)
- **Retiming** -> 08-time-nodes.md (Retime, OFlow, Kronos)
- **Rotoscoping** -> 06-draw-paint-nodes.md (Roto, RotoPaint)
- **3D camera projection** -> 10-3d-nodes.md (Camera, Project3D)

## Search Examples

```bash
# Find specific node documentation
grep -r "Keylight" reference/

# Find blend modes
grep -r "blend mode\|operation" reference/07-merge-composite-nodes.md

# Find color space info
grep -r "color space\|OCIO" reference/02-color-nodes.md

# Find keying techniques
grep -r "despill\|screen\|matte" reference/03-keyer-nodes.md
```

## Context Efficiency

**vs. Loading Full PDF:**
- Full PDF: 1371 pages, ~10MB
- This database: 11 files, ~500 lines each = ~5,500 lines total
- **Load only what you need:** 200-500 lines per topic vs 1371 pages
- **~90% context reduction** for typical node lookups

## Source

Extracted from: `Nuke/documentation/referenceGuide/Nuke15.0v4_ReferenceGuide.pdf`
**Version:** Nuke 15.0v4
**Pages:** 1371
**Last Updated:** 2026-02-04

## Maintenance

When Foundry releases new Nuke versions:
1. Download new reference guide PDF
2. Extract updated node documentation
3. Update version references
4. Keep files < 500 lines (Article III compliance)
