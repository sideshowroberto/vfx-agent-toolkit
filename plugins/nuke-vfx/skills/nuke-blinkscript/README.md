# nuke-blinkscript Agent Skill

**Version:** 1.0.0
**Status:** Production-ready
**Last Updated:** 2025-02-04

---

## Overview

BlinkScript kernel development skill for Nuke, covering GPU-accelerated custom effects, composition grids, procedural patterns, and image processing.

**Key Achievement:** Developed from production-tested composition grids kernel (7 grid types, 4K tested, GPU accelerated).

---

## Skill Structure

```
.claude/skills/nuke-blinkscript/
├── SKILL.md                              # Main skill (495 lines, <500 limit)
├── README.md                             # This file
└── examples/
    └── simple_overlay_template.blink    # Starter template
```

---

## Critical Learnings Documented

1. **float4 Color Pickers** - Essential UX pattern (float4 creates native Nuke color picker)
2. **init() Optimization** - 1000x+ performance gains (expensive operations once, not per-pixel)
3. **Multi-Rotation Spiral** - Solve backwards from radius (allows 5+ rotations)
4. **Geometric Patterns** - Line equations, polar coordinates, distance fields
5. **GPU Acceleration** - Real-time performance at 4K with parallel processing

---

## Reference Files

**Comprehensive Documentation:**
- `<workspace>\Nuke\documentation\blinkscript\BlinkScript_Learning_Notes.md` (860 lines)
  - Complete BlinkScript reference
  - All patterns and techniques
  - Math functions, performance tips
  - Testing methodology

**Working Examples:**
- `~/.nuke\blinkscript\CompositionGrids.blink` (475 lines)
  - Production kernel with 7 grid types
  - All critical techniques demonstrated
  - Tested at 4K resolution

---

## Quick Start

### 1. Simple Overlay (Start Here!)

```bash
# Copy template to Nuke
cp examples/simple_overlay_template.blink ~/simple_test.blink
```

In Nuke:
1. Create BlinkScript node
2. Load `simple_test.blink`
3. Click "Recompile Kernel"
4. Adjust parameters (color picker, thickness, position)

### 2. Composition Grids (Advanced)

```bash
# Use production kernel
# Already located at: ~/.nuke\blinkscript\CompositionGrids.blink
```

In Nuke:
1. Create BlinkScript node
2. Load `CompositionGrids.blink`
3. Enable desired grids (Thirds, Golden Ratio, Spiral, etc.)
4. Customize colors and thickness

---

## Auto-Trigger Phrases

The skill auto-loads when you mention:
- "blinkscript"
- "blink kernel"
- "nuke kernel"
- "custom kernel"
- "GPU nuke"
- "procedural nuke"
- "composition grid"
- "blink code"

---

## Constitutional Compliance

**Article I (General Purpose):** ✅
- All kernels are parameterized
- Work on any image size/project

**Article III (Progressive Disclosure):** ✅
- SKILL.md: 495 lines (<500 limit)
- Reference docs loaded on-demand

**Article IV (Independent Testing):** ✅
- Tested in Nuke 15.0v5
- Validated at 1080p, 4K, 8K

**Article V (Official Patterns):** ✅
- Uses official BlinkScript API
- Follows Foundry documentation

**Article VI (Context Efficiency):** ✅
- Progressive disclosure
- Links to reference docs

**Article VIII (Documentation):** ✅
- YAML frontmatter complete
- All sections present

---

## Development History

**Context:** BlinkScript learning project for future agent skill development

**Session:** 2025-02-04
- Started with plan for NST_CompositionGrids.gizmo
- Pivoted to BlinkScript-only learning (no Group/Gizmo)
- Discovered critical patterns (float4, init() optimization)
- Implemented 7 grid types with multi-rotation spiral
- Documented all learnings comprehensively
- Created this agent skill

**Key Milestones:**
1. Basic kernel (Thirds + Golden Ratio)
2. Color picker discovery (float4 creates native UI!)
3. Added 3 more grid types (Center, Diagonals, Spiral)
4. Fixed spiral multi-rotation (solve backwards technique)
5. Added Triangle + Grid Diagonals
6. Complete documentation for skill creation
7. Agent skill development (this!)

**Testing:**
- GPU acceleration verified
- 4K resolution (2160×3840) real-time
- All 7 grids working simultaneously
- No performance issues

---

## Usage Examples

### Ask Claude:

**Basic:**
- "Create a simple BlinkScript kernel that draws a red line"
- "How do I add a color picker to my kernel?"
- "Make this kernel run faster"

**Intermediate:**
- "Create a composition grid with rule of thirds"
- "Add a diagonal line pattern to my kernel"
- "How do I blend colors in BlinkScript?"

**Advanced:**
- "Create a Fibonacci spiral with multi-rotation support"
- "Optimize this kernel for 4K performance"
- "How do polar coordinates work in BlinkScript?"

---

## Contributing

**Found a pattern worth documenting?**
Add to `BlinkScript_Learning_Notes.md` with:
- Pattern name
- Code example
- When to use it
- Performance notes

**Created a useful kernel?**
Add to `examples/` directory with:
- Clear comments
- Parameter descriptions
- Use case explanation

---

## Version History

**1.0.0 (2025-02-04):**
- Initial skill release
- Based on production composition grids project
- 3 critical techniques documented
- 4 standard patterns included
- Complete CompositionGrids.blink reference
- Simple overlay template
- Constitutional compliance validated

---

## License

Part of VFX Agent Skills system. See `ClaudeCode/development/VFX_SKILL_CONSTITUTION.md` for governance.
