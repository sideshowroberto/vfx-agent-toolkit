---
name: blender-physics-simulation
description: Verified Blender 5.1 physics traps - fluid domains default to REPLAY so bake_all writes 1 frame, rigid bodies read wrong unless frames step in order or are baked, obj.collision is None without a COLLISION modifier, particles exist only on the evaluated object, free plus re-bake in one call crashed the GUI. Use when scripting or baking fluid, smoke, rigid body, cloth or particles.
metadata:
  version: 3.0.0
  updated: 2026-11-09
---

# Blender Physics Simulation - traps

Traps 1-5 measured headless on Blender 5.1.2 (blender-round3 probes, 2026-11-08); trap 6 is the live-GUI
crash from the round-3 ph2 run.

1. **Baking IS scriptable - but set `cache_type` first.** Wrong: assuming bakes are UI-only, or baking a
   domain left at the default `cache_type = 'REPLAY'` - `bpy.ops.fluid.bake_all()` then writes ONE data file
   (frame 1) while `has_cache_baked_data` still reads True. Right: `domain_settings.cache_type = 'ALL'` (or
   `'MODULAR'`), then `with bpy.context.temp_override(active_object=domain, object=domain):
   bpy.ops.fluid.bake_all()` (FINISHED, 5 vdb files for 5 frames at 16 divisions, 0.09 s). Rigid / particle /
   cloth point caches bake with `bpy.ops.ptcache.bake_all(bake=True)` (FINISHED, `point_cache.is_baked` True).
   Bakes block until done - keep scripted ones small. Verify: COUNT the files in
   `[cache_directory]/data`, never trust the baked flag.

2. **Rigid bodies only simulate when frames are stepped in order, or after a bake.** Wrong: `frame_set(1)`
   then `frame_set(20)` - a falling cube stays at z = 5.0. Right: step 1..20 sequentially (z = 1.9425 at 20,
   0.4983 at 40) or bake first. Verify: read `obj.matrix_world.translation` after the stepped `frame_set`.

3. **`obj.collision` is None until a Collision modifier exists.** Wrong: `ground.collision.use = True`
   (AttributeError). Right: `ground.modifiers.new("Collision", 'COLLISION')`, then set `ground.collision.*`.
   Verify: `ground.collision is not None` and the modifier is listed.

4. **Particles live on the EVALUATED object.** Wrong: `obj.particle_systems[0].particles` - 0 entries at frame
   5. Right: `obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).particle_systems[0].particles` - 100
   entries, 45 with `alive_state == 'ALIVE'`. Verify: count alive particles after `frame_set`.

5. **Old advice "Mantaflow cannot bake from Python / do not script ptcache.bake_all" is false** on 5.1.2 (both
   returned FINISHED in trap 1). Do not route a bake to the UI because of it.

6. **Never free and re-bake in the same `execute_blender_code` call on a live GUI.** Measured once: after a
   REPLAY bake, `free_all()` + `cache_type = 'ALL'` + `bake_all()` in one call closed the MCP socket
   (WinError 10054) and killed Blender; the same sequence headless finished. Right: free in one call, set
   `cache_type` and bake in the next; keep big bakes in a headless `blender -b` run. Verify: the Blender
   process is still resident and the data-file count matches the frame range.
