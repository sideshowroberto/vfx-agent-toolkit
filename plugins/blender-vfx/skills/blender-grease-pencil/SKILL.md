---
name: blender-grease-pencil
description: Verified Grease Pencil v3 traps on Blender 4.3+/5.1 - legacy frame.strokes, points.add, line_width and GP_* modifier ids raise errors, and Line Art silently makes 0 strokes without target layer, material and camera. Use when scripting Grease Pencil strokes, GP modifiers or Line Art.
metadata:
  version: 4.0.0
  updated: 2026-11-09
---

# Blender Grease Pencil - traps

Every trap measured headless on Blender 5.1.2 (blender-round3 probes, 2026-11-08). Blender 4.3 replaced
Grease Pencil with GPv3; the 2.8-4.2 API is GONE, not deprecated. Still valid: `bpy.data.grease_pencils.new()`,
object type `'GREASEPENCIL'`, `gp.layers.new(name)`, `layer.frames.new(n)`, `layer.blend_mode`, onion skinning,
`bpy.data.materials.create_gpencil_data(mat)`, `stroke.material_index`.

1. **Strokes live on the frame's drawing.** Wrong: `frame.strokes.new()` (AttributeError: 'GreasePencilFrame'
   has no attribute 'strokes'). Right: `d = layer.frames.new(1).drawing; d.add_strokes([n_points]); s = d.strokes[-1]`.
   Verify: `[(f.frame_number, [len(s.points) for s in f.drawing.strokes]) for f in layer.frames]`.

2. **Points are added on the stroke and positioned with `position`.** Wrong: `stroke.points.add(count=3)`,
   `point.co`. Right: `stroke.add_points(n)` (appends), `point.position = (x, y, z)` (object space).
   Verify: read `p.position` back for every point.

3. **Thickness is per-point radius.** Wrong: `stroke.line_width = 10` (AttributeError). Right: `point.radius`
   in world units; new points default to 0.01, so set it explicitly. Verify: read `p.radius` back.

4. **GP modifiers are ordinary modifiers with new ids.** Wrong: `obj.grease_pencil_modifiers.new(..., 'GP_NOISE')`
   (attribute absent) and `'GP_LINEART'` (TypeError: enum not found). Right: `obj.modifiers.new(name,
   'GREASE_PENCIL_NOISE')`, ids `GREASE_PENCIL_` + NOISE/OFFSET/TIME/SIMPLIFY/SMOOTH/THICKNESS/TINT/OPACITY/
   ARRAY/BUILD/LENGTH/MIRROR/... and `'LINEART'`. Their property names changed too. Verify: list
   `mod.bl_rna.properties` before setting anything; `obj.shader_effects` is unchanged.

5. **Line Art produces NOTHING, silently, unless it has `target_layer` AND `target_material` AND the scene has
   a camera.** Measured: 0 strokes in each failure case, no error; 2 strokes / 9 points when all three are set.
   Right: `md = ob.modifiers.new("LineArt", 'LINEART'); md.source_type = 'COLLECTION'; md.source_collection = src;
   md.target_layer = "Lines"; md.target_material = m` with `scene.camera` set. Verify on the EVALUATED object,
   never `ob.data`: `dg = bpy.context.evaluated_depsgraph_get(); dg.update(); ev = ob.evaluated_get(dg).data`,
   then count `len(L.current_frame().drawing.strokes)` per layer.

6. **Render engine id on 5.x is `'BLENDER_EEVEE'`.** Wrong: `'BLENDER_EEVEE_NEXT'` (TypeError; the 5.x enum is
   BLENDER_EEVEE / BLENDER_WORKBENCH / CYCLES). EEVEE on 5.1.2 also has no `use_bloom` / `bloom_*` /
   `use_gtao` properties, so older NPR recipes fail on them. Verify: `scene.render.engine` read-back, and
   `hasattr(scene.eevee, name)` before setting any EEVEE property from an older recipe.
