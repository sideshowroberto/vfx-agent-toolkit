# Nuke

Provenance: audited 2026-09 in the vfx-agent-toolkit-codex repository; its docs/,
codex/tests/ and codex/recipes/ hold the evidence records and probes named below.

Use explicit graph inputs and preserve the artist's comp. Isolate scriptClear
batch recipes. Source encoding, working space, premultiplication and viewer
transforms are distinct; do not label every input ACEScg.

The bundled bridge returns the Python variable `result`; it does not capture
stdout. Its GUI timeout means completion is unknown and a mutation may still
execute. Inspect state before repeating it. An external logger is optional.

The nuke-tiling-tool skill's auto_tile_processor.py
has corrected grid/mask math with overlap limited to half a tile. Native
identity reconstruction passed 80 rendered Nuke 17.0v2 cases after repairing
tile-origin translation, Reformat centering and explicit mask alpha channels.
An additional 4096x2160 case passed. Processed RGBA is copied onto the original
input so auxiliary source channels remain unchanged. Two model-edited tiles
showed a material mismatch that blending did not repair; see
continuation evidence.
Do not use the duplicated legacy mask examples as repaired implementations.
Blink kernels and CatFileCreator/Inference examples need the installed build's
API and actual compilation/load/inference checks. DA3 channel/export lessons
retain their original model/version scope.

Evidence: Nuke findings N1-N4,
repair status and tests.
Windows runtime tests on 2026-09-08 passed
licensed Nuke 17.0v2 headless/GUI dispatch, exception and late-completion checks.
Initial native tiling failures and corrected renders are retained as evidence.
Standalone MCP calls, Codex discovery and native active-task calls passed after
full application restart. CPU ranged Blink and synthetic two-size CAT inference also passed;
GPU ranged-filter tests subsequently passed with terminal `--gpu`; the earlier
unavailable-device result omitted that flag. Particle compilation/simulation
remain unverified. NukeX terminal features need `--nukex -i`. Tested scaffolds are in
codex/recipes/nuke and native probes in codex/tests.
