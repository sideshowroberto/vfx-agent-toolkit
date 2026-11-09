---
name: houdini-solaris-usd
description: "Verified traps for Solaris, Karma and USD export in Houdini: how light and camera values land on the stage, time samples, instance proxies, loose points, GeomSubsets, savestyle. Use when authoring or checking a LOP stage, Karma lights, or a USD export."
metadata:
  version: 2.0.0
  updated: 2026-11-08
---

# Solaris / USD - traps and house rules

Staged by the 2026-11-08 round-2 baseline eval (ClaudeCode/evals/houdini-round2/ANALYSIS.md): with only the
Houdini MCP the model passed both Solaris cases 4/4 (spot-light cone angle, single-sided disk light); the skill
was never opened. The USD primer (layers, variants, composition arcs, LOP node reference) is cut as general
know-how. What stays is what the house measured. Karma light facts come from reference/karma_lights.md.

Use the MCP first: create_lop_node, get_stage_info, get_usd_prim, get_usd_attribute, get_usd_composition,
inspect_usd_layer, set_usd_attribute.

## Traps (details and code in reference/)

1. **Read the COMPOSED stage at the frame, not default time.** SOP Import authors mesh topology only as a time
   sample (`Get()` returned None for 14,536 of 14,536 meshes); Camera LOP holds a fallback focal 50 plus one sample.
   `Usd.TimeCode(hou.frame())` on every Get; report GetNumTimeSamples. reference/stage_readback.md section 1.
2. **Light LOP shaping:** `shaping:cone:angle` is a half-angle in degrees off the axis and is written only when
   `spotlightenable` is on (off: attribute not authored, reads None). Measured: spotlightenable on, parm 25 ->
   stage 25.0. The OBJ-level hlight is different: angle = coneangle/2 + conedelta. reference/karma_lights.md 1, 9.
3. **Disk/grid/rect area lights are double-sided by default**; turn `singlesided` on and read
   `inputs:karma:light:singlesided` True off the stage. reference/karma_lights.md 3.
4. **Karma falls off with distance squared** whatever atten_type says (`light_exposure = log2(d^2)`); Houdini
   intensity is multiplied by 2 pi on the stage; an env light is invisible to camera until Render Light Geometry.
5. **Instances:** assign materials on the ancestor, not `/root/**` (instance-proxy error); count meshes with
   `Usd.TraverseInstanceProxies()` AND visibility, and say both (a packed-prim stage reads N instances plus the
   prototype mesh). reference/stage_readback.md 2, from_obj_to_solaris.md 2.
6. **Export checks:** loose points become a Points prim Karma draws as spheres (list non-Mesh gprims, delete
   unreferenced points); re-parenting a mesh must move its GeomSubsets; an invalid usd_rop `savestyle` token
   leaves a ~700-byte stub; Houdini winding is left-handed (set USD orientation from a measured test).
   reference/usd_export_checks.md.
7. **A Material Library built by script can come up with assign1 OFF**; check ComputeBoundMaterial on the
   downstream render LOP. World-space Transform LOP on animated prims is exact at one frame only.
8. **Karma ROP:** USD Render ROP renderer must be BRAY_HdKarmaXPU; verify from the EXR Software header
   (scripts/karma_rop.py). Imported cameras carry DOF; set enabledof off for grey passes.

## Scripts and reference

scripts/stage_digest.py (compare composed stages per prim, with a canary), scripts/karma_rop.py. reference/:
from_obj_to_solaris, karma_lights, stage_readback, stills_per_shot, usd_export_checks, verification_instruments,
viewport_slap_comp.
