---
name: blender-addon-development
description: Verified Blender 4.2+/5.1 add-on and extension traps - bl_info-only zips fail extension validate without blender_manifest.toml, assignment-style bpy.props register silently and do not exist, BLENDER_EEVEE_NEXT raises TypeError. Use when writing or packaging a Blender add-on, extension, operator or panel.
metadata:
  version: 3.0.0
  updated: 2026-11-09
---

# Blender Add-on Development - traps

Traps 1-4 measured on Blender 5.1.2 (blender-round3 probes, 2026-11-08). Traps 5-6 come from building the
production cloud-generation add-on (2026-07), not from the eval.

1. **A 4.2+ extension needs `blender_manifest.toml`.** Wrong: a zip holding only a `bl_info` add-on - `blender
   --command extension validate <zip>` exits 1 with "archive has no manifest". Right: `__init__.py` (register /
   unregister, no bl_info needed) plus a manifest at the zip root or in one top-level folder:
   ```toml
   schema_version = "1.0.0"
   id = "my_tool"
   version = "1.0.0"
   name = "My Tool"
   tagline = "Spawns empties"
   maintainer = "Name <name@example.com>"
   type = "add-on"
   blender_version_min = "4.2.0"
   license = ["SPDX:GPL-3.0-or-later"]
   ```
   `bl_info` is only for legacy add-ons (Install from Disk of a plain .py). Verify: `blender --command
   extension validate my_tool.zip` exits 0 ("Success parsing TOML").

2. **Properties must be annotations.** Wrong: `count = bpy.props.IntProperty()` - registers WITHOUT error and the
   property silently does not exist. Right: `count: bpy.props.IntProperty()`. Verify: `'count' in
   Op.bl_rna.properties` is True after `register_class`.

3. **Registration does not catch naming mistakes.** A Panel `bl_idname` without `_PT_` only prints a warning and
   still registers. Verify: read the warning output, and check `cls.is_registered` for every class in `classes`
   after register (True) and after unregister (False).

4. **Render engine id on 5.x is `'BLENDER_EEVEE'`.** Wrong: `'BLENDER_EEVEE_NEXT'` (TypeError; the 5.x enum is
   BLENDER_EEVEE / BLENDER_WORKBENCH / CYCLES). The Geometry Nodes modifier type is `'NODES'`, not
   `'GEOMETRY_NODES'`. Verify: read `scene.render.engine` and `mod.type` back.

5. **Hot reload: never `importlib.reload` single submodules** - it poisons the class registry. Run the full cycle:
   disable the add-on, purge its `sys.modules` entries, enable. Verify: the operator's `bl_rna` reflects the
   edit after re-enable.

6. **Third-party deps: pip `--target` a per-user folder and `sys.path.insert` it at import**, never into
   Blender's bundled python. A pip install run from the agent shell can be sandbox-virtualized and never land
   (windows-gotchas.md) - run it from inside Blender. Verify: import the package from Blender's own console.
