# BlinkScript Reference Database

This directory contains organized BlinkScript kernel documentation extracted from Foundry's official documentation (316-page PDF). Files are structured for **progressive disclosure** following VFX Skill Constitution Article III (<500 lines per file).

## File Structure

| File | Topics | Lines | Load When |
|------|--------|-------|-----------|
| **01-kernel-basics.md** | Kernel structure, granularity, Image specs, process() | ~132 | Creating any kernel |
| **02-kernel-variables.md** | param/local vars, types, define(), image properties | ~154 | Need parameters or variables |
| **03-image-access.md** | init(), access patterns, bilinear interpolation | ~198 | Working with neighborhoods or ranges |
| **04-built-in-functions.md** | Vector, math, trig, atomic, rect functions | ~181 | Need specific functions |
| **05-quick-reference.md** | Cheat sheet, templates, common patterns | ~178 | Quick syntax lookup |

## Total Size
- **5 files, ~843 lines total**
- **Context-efficient**: Load only what you need
- **Searchable**: Use Grep to find specific functions or patterns

## Usage with nuke-blinkscript Skill

The nuke-blinkscript skill references these files automatically:
- **Basic kernels** -> Load 01, 05
- **Parameter setup** -> Load 02
- **Blur/convolution** -> Load 03
- **Complex math** -> Load 04
- **Quick lookup** -> Load 05 only

## Search Examples

```bash
# Find all access pattern examples
grep -r "eAccessRanged2D" reference/

# Find bilinear interpolation usage
grep -r "bilinear" reference/

# Find all vector functions
grep -r "dot\|cross\|length\|normalize" reference/04-built-in-functions.md
```

## Benefits Over Original PDF

[OK] **No "PDF too large" errors** - Files under 200 lines each
[OK] **Faster search** - Grep through markdown faster than PDF
[OK] **Progressive disclosure** - Load only relevant sections
[OK] **Context-efficient** - ~75% reduction vs loading full 316-page PDF
[OK] **Always available** - No web dependency

## Source

Extracted from: `Nuke/documentation/blinkscript/docs-to-pdf-crawler/BlinkScript_Kernels_Complete.pdf`
Original source: https://learn.foundry.com/nuke/developers/80/BlinkKernels/

## Maintenance

When Foundry updates BlinkScript documentation:
1. Run PDF crawler on new docs
2. Extract new content using same structure
3. Update version date below
4. Keep file sizes < 500 lines (Article III compliance)

**Last Updated:** 2026-02-04
**BlinkScript Version:** Nuke 14.0+
**Documentation Source:** Foundry Learn Portal
