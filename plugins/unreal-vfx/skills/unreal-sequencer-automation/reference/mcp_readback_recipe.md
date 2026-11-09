# Read-back Recipe (over MCP)

**Purpose:** read a level sequence back (bound objects, cameras, world state) and
grab shot-camera stills through the UE 5.8 native MCP server, without being
fooled by "nothing" results.
**Added:** 2026-10-09 (observation 140)

## Contents

1. Open, scrub, read bindings
2. Spawnables
3. The 30-second MCP limit
4. Screenshots that never draw
5. Many stills: run the loop inside the editor
6. Related

Reading a sequence back through the editor bridge fails silently: a read that
runs before the first evaluation, a list that skips transient actors and a
latent request that waits for a redraw all return "nothing" instead of an
error. Verify the product (the bound object, the file) after every step, never
the call's return.

---

## 1. Open, scrub, read bindings

```python
import unreal

lsel = unreal.LevelSequenceEditorBlueprintLibrary
lsel.open_level_sequence(seq)
lsel.set_current_time(frame)          # scrub FIRST - spawnables do not exist before this
for b in seq.get_bindings():
    # Pass the binding ID, not the binding proxy: get_bound_objects(b) raises
    # "Cannot nativize MovieSceneBindingProxy".
    objs = lsel.get_bound_objects(seq.get_binding_id(b))
    print(b.get_name(), [o.get_name() for o in objs])
```

`seq.get_binding_id(b)` is the same call as
`unreal.MovieSceneSequenceExtensions.get_binding_id(seq, b)` (SKILL.md trap 3).

- **Scrub before listing cameras.** A spawnable camera is only spawned by the
  first `set_current_time`. Until then the camera-cut camera list is EMPTY, and
  a "cameras: []" summary taken before scrubbing looks like a whole project of
  broken shots. Read back at the frame you care about, per sample.

## 2. Spawnables

`unreal.EditorActorSubsystem.get_all_level_actors()` (and
`EditorLevelLibrary.get_all_level_actors()`) do NOT return sequencer
spawnables. After scrubbing, list them from the world:

```python
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
```

Filter by class. A "not a level actor" test for spawnables also catches engine
helper actors (WorldSettings, Brush, nav data, visualizers), so test for the
classes you expect (characters, props) rather than by exclusion.

## 3. The 30-second MCP limit

The server answers "Python execution exceeded 30000ms" at about 30 s, **but the
script keeps running in the editor.** A timeout is not a failure.

- Keep each call under 30 s: batch a few shots per call. Opening a heavy shot
  (ten MetaHuman-class characters) took more than 30 s on its own.
- After a timeout, read the state back (open sequence, file on disk) before
  deciding anything.

## 4. Screenshots that never draw

`AutomationLibrary.take_high_res_screenshot(..., camera=...)` only writes on the
next viewport redraw. With the editor window in the background no redraw
happens, and grabs silently never land (every second one in the session this
came from).

1. Request the screenshot.
2. Call `unreal.EditorLevelLibrary.editor_invalidate_viewports()` (repeat for a
   few ticks) so a redraw happens.
3. Check the image file exists AND has content: open it, check it is not blank
   and shows the right subject (a blank frame is a valid image of plausible
   size).
4. On a miss, re-open the sequence (switch away and back) and retry - the
   reliable reset. Invalidating alone helped only for a while.

Focusing the editor from the desktop: `open_application` on the engine's
start-menu entry launches a NEW project browser rather than focusing the running
editor.

## 5. Many stills: run the loop inside the editor

Per-call stepping cost about 90 s per plate. The fast path is one MCP call that
registers `unreal.register_slate_post_tick_callback` and lets the editor walk a
job list on its own ticks:

1. open the shot, set the frame,
2. hide what must be absent from the plate (spawned characters and spawned
   static/skeletal-mesh props),
3. `editor_invalidate_viewports()` for about 12 ticks,
4. `take_high_res_screenshot`,
5. keep invalidating until the file exists, then move to the next job.

39 plates took about 60 s this way. Two traps:

- Filter hidden actors by class (see section 2), not by "not a level actor".
- One plate in 39 still showed the actors that should have been hidden. Inspect
  every plate's content before delivery; do not trust the loop's "done".

---

## Related

- Port 8000 not listening although the plugin is enabled (no auto-start on the
  project): run `ModelContextProtocol.StartServer 8000` in the editor console.
  Preflight should check the server is LISTENING, not only that the plugin is
  enabled (`unreal-project-preflight`).
- Possess, keying and camera-cut traps: SKILL.md traps 1-5.
