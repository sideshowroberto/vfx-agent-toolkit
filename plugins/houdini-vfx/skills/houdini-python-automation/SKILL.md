---
name: houdini-python-automation
description: "Verified traps for scripting Houdini with hou/hython: ROP frame ranges, object_merge transforms, fake export formats, spare parms, Python SOP code, display-node read-back. Use when scripting Houdini, exporting geometry from hython, or verifying a scripted build."
metadata:
  version: 2.0.0
  updated: 2026-11-08
---

# Houdini Python - traps and house rules

Staged by the 2026-11-08 round-2 baseline eval (ClaudeCode/evals/houdini-round2/ANALYSIS.md): with only the
Houdini MCP the model passed both cases 4/4 (ROP frame range, object_merge world position); the skill was never
opened. The MCP tools already carry part of the guard (set_parameters reports `expression_kept` and takes
`override_expression`; export_file reports `wrote_files`). The Python tutorial (batch node creation, parameter
animation, scene I/O, callbacks) is cut. What stays are the measured traps.

Order of preference: MCP tool > build_network > execute_python (execute_python for what no tool does, e.g.
running a ROP with an explicit range or writing a read-back file from inside Houdini).

## Traps (details and code in reference/)

1. **A new ROP's f1/f2 hold `$FSTART`/`$FEND` expressions and `parm.set()` does not replace them** (measured:
   set 1001-1010 wrote 240 files, the scene range). `deleteAllKeyframes()` on f1/f2/f3 first, or the MCP's
   `override_expression=true`; count the files on disk. reference/headless_build_checks.md.
2. **object_merge `xformtype` defaults to index 2 ("object"), not "Into This Object"** (measured: a box at
   world x=5 merged into an object at ty=10 came out at world (0,10,0); xformtype=1 gives (5,0,0)). Set it and
   check the merged bounding box against the source pushed through its world transform.
   reference/geometry_export.md section 3.
3. **`geometry.saveToFile()` writes fake files for any extension but obj/ply/stl/abc/bgeo/geo**; filmboxfbx
   `exportkind` default 1 is ASCII, which Blender refuses. Read the first bytes of every export.
   reference/geometry_export.md.
4. **Spare parms added after a node cooked leave it reading stale values** (obs 442: a wrangle's `chs()` returned
   empty after create_spare_parameters; 9/9 vex-eval runs lost 8-15 turns and 5/9 blamed the wrong cause).
   Add the parms first, or re-set the snippet to force a recook, then re-read before diagnosing.
5. **Spare-parm folders:** append by folder LABEL (`appendToFolder`), do not reuse a FolderParmTemplate handle;
   call `setParmTemplateGroup` once. Idempotent builders change nothing that already exists.
6. **Cook every node and print `node.errors()`**; "it cooked" is not a correctness signal. Grid/Sphere
   rows/cols are POINT counts. Check face direction.
7. **Verify through the display node**, not only the edited node (caches, freezes, load-from-disk downstream).
   reference/verify_through_display_node.md.
8. **Python SOP / injected code:** forward slashes in code written into a string parm; read back with
   `unexpandedString()`; `hou.pwd().inputGeometry(i)` follows the wire; exec'd helpers clobber caller globals.
   reference/python_sop_traps.md.
9. **Measure point-to-SURFACE with xyzdist, not point-to-point**; prove the instrument on a known contact.
   reference/measure_without_nodes.md.

## Scripts and reference

scripts/geo_digest.py (prove two SOP outputs match, by attribute name), scripts/hip_provenance.py (stamp a render
record with the hip's hash). reference/: geometry_export, headless_build_checks, python_sop_traps, editable_proxies,
takes, measure_without_nodes, verify_through_display_node.
