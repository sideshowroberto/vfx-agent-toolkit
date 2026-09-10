# First run lessons - 2026-09-09

Builder: GPT-6 Astra in Codex (GUI), live Blender 5.1 through the official
Blender MCP, operator watching. Task: a three-zone environment (a circular
display chamber with an oculus, two barrel-vaulted connecting hallways, a
curved outer corridor) from five client-approved reference images, six
matched views. Working folder on the job share; all outputs preserved.

## Numbers (from the run's own read-backs)

| | |
|---|---|
| Reviewed iterations | 7 (stalled rule) |
| Loop renders / finals | 42 / 6 (plus 48 three-panel comparisons) |
| Scene increments | v001 to v064, 667 named objects, no auto-suffixed names |
| Global minimum | 1 (iter01-03) -> 2 (iter04-07) |
| Total score, 36 cells | 66 (iter01) -> 101 (iter07) |
| Target (all >= 4) | not met; builder said so |

The first three iterations' minimum of 1 was a single blank frieze band
(a texture whose pixels were never packed); the builder found it by pixel
read-back, not by looking, and fixed it in iter04.

## What the loop got right

- Real, visible progress every iteration: cameras handed the right way,
  friezes placed, the podium fixed, the oculus beam appearing, coursing on
  the stone. The iter01 and final contact sheets read as the same building
  becoming recognisable.
- Every iteration carried file read-backs (path, bytes, mtime, pixels) and
  a statement that all comparisons were opened. No narrated-only rounds.
- The builder wrote its own non-blocking render queue on Blender timers with
  a status JSON, because an inline six-view render through MCP would time
  out. Kept as `blender_loop_patterns.md`.
- It refused to inflate scores: "constraint score rose only because the
  formerly blank bands are now visible", "small roughness changes do not
  justify a material score increase". The final Cycles pass regressed two
  corridor views' lighting and it reported the regression as a regression.
- It stopped under the rule, said the target was not met, and listed the
  first objects to touch next.

## What to change in the contract (now in the skill)

1. **Stop on the dual rule, not the minimum.** The minimum-only rule stopped
   the run at global min 2 while four of six views were still improving and
   the total was climbing. Stalled now means neither minimum nor total moved.
2. **Settle reference disagreements before iteration one.** Two chamber refs
   implied different niche counts and a different podium; a third showed a
   narrow lectern where the client wanted a round podium. One shared layout
   cannot score above 2 on composition for both. The human picks.
3. **Finals in the loop engine first.** The Cycles finals were a new variable
   at the very end. Render finals with the loop engine, then a labelled
   hero-engine pass.
4. **A structurally wrong view stalls everything.** The curved corridor's
   tower vista never matched because the plan (a concentric ring) was the
   wrong mass, not because of lighting. That is a plan problem; the fix is
   to park the view or rework the plan, never to widen the rubric.
5. **Nominal anchors lose to image-space proportions.** The builder moved
   the hallway frieze from a nominal 2.8 m base to 0.85 m because the
   low-camera references demanded it, and said so in the brief. Give anchors
   as hints and let the reference win, but require the number be written.

## Lens for judging any run

Read the final contact sheet yourself and score it blind; then read the log.
The builder's scores are steering, the human's are the verdict. In this run
the human read agreed with the builder's ordering (chamber views closest,
curved corridor furthest) and with its own "not met".
