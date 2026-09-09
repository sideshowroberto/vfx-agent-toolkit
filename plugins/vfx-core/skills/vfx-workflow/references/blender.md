# Blender

Provenance: audited 2026-09 in the vfx-agent-toolkit-codex repository; its docs/,
codex/tests/ and codex/recipes/ hold the evidence records and probes named below.

Select renderer identifiers from the installed RNA enum. The 5.2.1 audit rejected
BLENDER_EEVEE_NEXT and found BLENDER_EEVEE; do not generalize either identifier
across releases. The same build lacked Action.fcurves and frame.strokes and had
frame.drawing. Replacement layered-action/channelbag and drawing.add_strokes
recipes passed save/reopen on Windows Blender 5.1.2 in
the native probe.

The tested multilayer EXR compositor output accepted MULTI_LAYER_IMAGE. Inspect
the current compositor API and actual output passes before promising a handoff.
Use a separate output version and inspect a small render before a costly batch.

Blender/ComfyUI audit holds probe provenance
and remaining recipe gaps. Those API probes did not render or validate a full
Blender-to-generation-to-compositing workflow.

The later pass configuration
rendered clay, Z and normal multilayer EXR on 5.1.2. Nuke inspected actual
channels and pixels, with fixed near=3/far=12 depth mapping for the test scene.
Use scene-appropriate fixed bounds across a sequence, not per-frame extrema.
Two clay crops were edited via Comfy and reconstructed in Nuke, exposing a
material continuity failure. See evidence.
