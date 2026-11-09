---
name: houdini-hda-creation
description: "Verified traps for authoring and versioning Houdini Digital Assets (HDAs): version pinning, int-menu storage, delivery read-back, in-place updates. Use when building, versioning or updating an HDA, or comparing two versions of one."
metadata:
  version: 2.0.0
  updated: 2026-11-08
---

# HDA creation - traps and house rules

Staged by the 2026-11-08 round-2 baseline eval (ClaudeCode/evals/houdini-round2/ANALYSIS.md): with only
the Houdini MCP, the model built, versioned and read back HDAs correctly 4/4; the skill was never opened.
The tutorial body (create / version / organize / callbacks) is cut. What stays is what the eval measured
or the house hit.

Use the MCP first: create_hda, update_hda, reload_hda, install_hda, get_hda_sections, set_hda_section_content,
get_hda_info, list_hda_versions. Drop to hou.HDADefinition only for what they do not cover.

## Traps (details and code in reference/versioning_and_verification.md)

1. **A bare type name resolves to the NEWEST installed version.** After `my_asset::2.0` is installed,
   `createNode("my_asset")` builds 2.0. For a regression reference or old-vs-new comparison create with
   `exact_type_name=True` and assert `node.type().name()`. Measured in the eval: 3 of 4 default runs built the
   "old" instance with the bare name and got the new version's 8 points instead of 33 (Opus 5.5: 2 of 4); each
   noticed only because both counts matched, and spent 5-15 turns recovering (clean runs: 4-5 turns).
2. **An INT menu parm stores the picked item's POSITION, not its token.** Sparse ids (1-11, 13-23) put every
   pick after the gap off by one or two. List every value in order so position == id, or use a string parm; test
   by setting the parm to each POSITION and reading the output. (The eval's 4 runs read back by position and
   passed; keep the rule, it is cheap.)
3. **Force-cook every output and every member node before delivery** and record counts or errors per output;
   an output with no measured count is a FAIL. Lazy cooking hides VEX compile errors.
4. **Verify through the node the artist sees** (display flag, caches, freezes): the
   verify-through-display-node reference in the houdini-python-automation skill.
5. **Updating a live asset:** dry-run in a scratch subnet first, digest old vs new, then updateFromNode; check
   `matchesCurrentDefinition()` on every live instance; after `changeNodeType(keep_parms=True)` list
   `spareParms()`. See reference/in_place_update.md and reference/versioning_and_verification.md sections 5-6.
6. **Spare-parm folders:** append by folder LABEL (`appendToFolder`), never reuse a FolderParmTemplate handle
   across appends; call `setParmTemplateGroup` once.
7. **Build off the team share:** every definition save writes backups next to the library and
   `copyToHDAFile` writes first; build and test locally, copy only a passing file.

## Reference (load on demand)

versioning_and_verification.md (traps 1-3, 5, 6) - in_place_update.md - override_layers.md -
asset_interface_design.md - viewport_image_assets.md - text_and_engraving.md (font and engraving
solids, Boolean-then-slice triangulation; moved here 2026-11-09 from the retired houdini-procedural-generation).
