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

## Second run, same day: the same builder with nothing installed

Same prompt, references and Blender session, but Codex launched from a
throwaway home with only the DCC MCP server - no skill packs, no project
instructions, headless. It reached the same ceiling (minimum 2), stopped
under the same rule with the same honesty, in 5 iterations and 26 minutes
against 7 and 64, and the human read of the two final sheets was within
two points of 180. Reading: when the contract is in the prompt, the skill
pack around the builder does not move match quality on a self-contained
loop; what moves it is the contract, the reference set and the plan. Two
independent builders also shared one blind spot (a curved corridor whose
plan was the wrong mass), which is evidence about the plan, not the
builders. Bench a change to the contract, not a change to the wrapper.

## Third run: a different builder, this skill in its hands

Claude Code (Fable, high effort, headless) with this skill available ran
the same prompt, invoked the skill on its own, wrote the spec, copied the
scripts, and ran 12 iterations. Two lessons:

1. **Self-scores do not transfer between builders.** Three builders, three
   calibrations: self totals 107, 115 and 137 against human reads of 102,
   100 and 97. The most generous scorer was furthest from the eye. The
   human read of the final sheet is the measurement; the log is steering.
2. **The prompt's rule beats the script's rule.** The run used the older
   prompt's minimum-only stall rule and stopped on it while the copied
   stop_check was printing CONTINUE under the dual rule. Whatever stop rule
   the prompt states is the one that will be obeyed, so generate the
   prompt from the same spec the scripts read (gauntlet_prompt.py does),
   and never hand-edit one without the other.

## Round 2: same contract, open tool surface, two builders

Both builders were given the installed DCC add-ons, a hosted image
generator, a spend cap with a ledger, rubric anchors, and a brief that
stated the plan the first round had missed.

1. **The priority order and the stall rule interact.** One builder followed
   "composition first" faithfully, plateaued on structure, and the stall
   rule fired at iteration 5 before the materials tier had an iteration of
   its own - it never touched the paid tools. Fix: `stop.min_iterations`, a
   floor below which a stall cannot fire (not a looser streak).
2. **Anchors fix calibration.** With "what a 4 means" written into each
   rubric description, self-scores landed within 2 and 5 points of the
   human read, against gaps of 5, 15 and 40 in round 1.
3. **One generated image can be the whole materials tier.** The other
   builder spent 75 credits on a single relief image before iteration 1,
   used it as colour and bump on every frieze band, and moved materials
   from 2 to 4 on every view. Hand the next builder that asset up front.
4. **The plan belongs in the brief.** The section the first round never
   built (towers over the corridor) was built by every run whose brief
   stated it. The loop converges on what the brief describes; it does not
   discover architecture.
5. **A ledger earns its keep when it reports what it cannot explain.** The
   builder's closing balance read showed a drop it had not caused and it
   said so rather than reconciling it away.

## Lens for judging any run

Read the final contact sheet yourself and score it blind; then read the log.
The builder's scores are steering, the human's are the verdict. In this run
the human read agreed with the builder's ordering (chamber views closest,
curved corridor furthest) and with its own "not met".
