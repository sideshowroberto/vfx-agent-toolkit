---
name: unreal-sequencer-automation
description: Verified UE 5.8 Sequencer Python traps - add_key(FrameNumber(n)) keys DISPLAY-rate frame n (not ticks), get_channel_by_name does not exist, section.cast raises TypeError, cut cameras compare by guid, reads over MCP need a scrub first, ImagePlate is off by default. Use when keying channels, adding camera cuts, animating a camera property, or reading a Level Sequence back.
allowed-tools: mcp__ue58-mcp__execute_python_code,mcp__ue58-mcp__call_tool
metadata:
  version: 4.0.0
  updated: 2026-11-09
---

# Unreal Sequencer Automation - traps

Traps 1-5 measured in UE 5.8.0 (editor probes + unreal-round2 eval 2026-11-08, unreal-round3 seq3 2026-11-09;
ClaudeCode/evals/unreal-round3/ANALYSIS.md). Trap 6 is the obs 140 production read-back lesson; trap 7 is
from the round-3 vfx2 runs. Step 0 for any approved plan: `unreal-project-preflight`.

1. **Channel keys are in DISPLAY-rate frames, not ticks.** Wrong: `ch.add_key(unreal.FrameNumber(48*1000), 85.0)`
   assuming tick resolution - the key reads back at display frame 48000 (the one round-3 seq3 miss). The
   same run then "verified" it by dividing the read-back by the tick resolution, so the check agreed with the
   bug. Right: `ch.add_key(unreal.FrameNumber(48), 85.0)` after `seq.set_display_rate(unreal.FrameRate(24, 1))`.
   Verified route for a camera property (CurrentFocalLength 35 -> 85, both with-skills runs passed):
   `b = seq.add_possessable(cam)`; `cb = seq.add_possessable(cam.get_cine_camera_component())`;
   `t = cb.add_track(unreal.MovieSceneFloatTrack)`; `t.set_property_name_and_path("CurrentFocalLength",
   "CurrentFocalLength")`; `s = t.add_section(); s.set_range(0, 48)`; `ch = s.get_all_channels()[0]`.
   Verify: `[(k.get_time().frame_number.value, k.get_value()) for k in ch.get_keys()]` reads `(48, 85.0)` - take
   that number as the display frame, never rescale it.

2. **`MovieSceneSectionExtensions.get_channel_by_name` does not exist.** Right:
   `[c for c in unreal.MovieSceneSectionExtensions.get_all_channels(section) if str(c.channel_name) == "Location.Z"][0]`.
   Channels are NOT created lazily: a fresh transform section already reports all 9 (Location/Rotation/Scale
   .X/.Y/.Z) before any key - no "first key initialises the channels" step is needed. Verify:
   `len(get_all_channels(section)) == 9` on a transform section.

3. **`section.cast(unreal.MovieSceneCameraCutSection)` raises TypeError.** Right: `ct =
   seq.add_track(unreal.MovieSceneCameraCutTrack)`; the section from `ct.add_section()` already has
   `set_camera_binding_id(seq.get_binding_id(binding))` and `set_range(start, end)`. Bind the cut to the
   camera ACTOR binding, not the component binding. Verify with trap 4.

4. **`str()` of a Guid prints an empty struct.** Compare a cut's camera by
   `section.get_camera_binding_id().get_editor_property("guid").export_text()` against
   `binding.get_id().export_text()`. Verify: the matching binding's display name is the camera's label.

5. **`LevelSequenceEditorBlueprintLibrary.get_bound_objects(binding)` rejects the binding proxy** ("Cannot
   nativize MovieSceneBindingProxy"). Right: pass `seq.get_binding_id(binding)`.

6. **Read-backs over MCP fail as "nothing", not as an error** (obs 140, production). Open the sequence and
   `set_current_time(frame)` BEFORE listing cameras - a spawnable exists only after the first scrub, so an
   earlier "cameras: []" is not a broken shot. Spawnables are not in `get_all_level_actors()`; after the scrub
   use `unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)` and filter by class. MCP calls
   time out at ~30 s while the script keeps running - read the state back, do not re-run. A viewport
   screenshot writes on the next redraw: call `unreal.EditorLevelLibrary.editor_invalidate_viewports()` and
   check the file has content. Code and the in-editor batch loop: `reference/mcp_readback_recipe.md`.

7. **ImagePlate is an Experimental plugin, off by default** (preflight feature `imageplate`). In the round-3
   test project it was disabled: `hasattr(unreal, "ImagePlate")` False and
   `unreal.PluginBlueprintLibrary.is_plugin_mounted("ImagePlate")` False. Do not enable it at runtime - go back
   to preflight, or build the verified fallback card: `ImgMediaSource` (`sequence_path` +
   `frame_rate_override`) -> `MediaPlayer` -> `MediaTexture` (`media_player`) -> Material with
   `shading_model = MSM_UNLIT`, TextureSample (`sampler_type = SAMPLERTYPE_EXTERNAL`) RGB -> Emissive, on a
   plane scaled to the plate aspect. Verify: `get_material_property_input_node(m, MP_EMISSIVE_COLOR)` is the
   TextureSample holding the MediaTexture, and report ImagePlate as unavailable rather than faking it.
