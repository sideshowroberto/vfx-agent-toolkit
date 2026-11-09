---
name: blender-sculpting
description: Verified Blender 5.1 sculpting traps - setting Multires levels clamps to 0 (use multires_subdivide), the sculpt mask is the .sculpt_mask point attribute (not a vertex group, not sculpt_mask), shading id is MATERIAL, edge-scan smoothing stalls big grids. Use when scripting Multires, sculpt masks or terrain displacement.
metadata:
  version: 3.0.0
  updated: 2026-11-09
---

# Blender Sculpting - traps

Every trap measured headless on Blender 5.1.2 (blender-round3 probes, 2026-11-08).

1. **Multires levels come from subdividing, not from setting `levels`.** Wrong: `mod.levels = 2` on a fresh
   Multires - `total_levels` stays 0, the levels clamp to 0, a cube stays 8 verts. Right: call
   `bpy.ops.object.multires_subdivide(modifier=mod.name, mode='CATMULL_CLARK')` once per level with the object
   active (`with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob]):` works
   headless). Verify: `mod.total_levels == 2` and the EVALUATED vertex count
   (`len(ob.evaluated_get(dg).data.vertices)`) - a 2 m cube gives 98 at level 2; the base mesh stays at 8.

2. **The sculpt mask is the float POINT attribute `.sculpt_mask` (leading dot, hidden in the UI list).**
   Wrong: a vertex group named "Mask", or an attribute `sculpt_mask` without the dot (the bundled manual's table
   spells it that way). Right, without entering Sculpt Mode:
   `a = me.attributes.new(".sculpt_mask", 'FLOAT', 'POINT'); a.data.foreach_set("value", values)`.
   Verify: `me.vertex_paint_mask` (the RNA view of the sculpt mask) returns that layer - it is None when only
   `sculpt_mask` exists - and count values above 0. Face sets are `.sculpt_face_set` (INT, FACE) per the manual.

3. **Viewport shading ids on 5.1.2 are 'WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED'.** Wrong:
   `'MATERIAL_PREVIEW'` (not a member). Verify: `space.shading.type` read-back.

4. **A per-vertex scan over `mesh.edges` stalls on real grids.** Wrong: smoothing by looping every edge for
   every vertex - measured 1.56 s per iteration at 1,681 verts, growing with verts x edges (roughly a minute
   per iteration at 101 x 101, extrapolated), which can time out an MCP call. Right: build an adjacency list
   once, or use `bmesh.ops.smooth_vert`. Verify: time one iteration on the real vertex count first.

5. **Brush-stroke operators need a 3D Viewport context.** Sculpt brushes are assets since 4.3
   (`bpy.ops.brush.asset_activate` exists on 5.1.2), but stroke operators fail from a script without a viewport;
   scripted displacement of `mesh.vertices` (then `mesh.update()`) is the reliable path. Verify: read vertex
   positions back after the edit.
