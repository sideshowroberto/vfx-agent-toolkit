---
name: loop-gauntlet
description: Run a build-until-it-matches loop in a DCC - an agent builds a scene from reference images, renders matched camera views every iteration, compares each render to its reference side by side, scores it against a rubric the HUMAN authored, logs read-back evidence, and a stop rule decides when it is done. Use when asked to rebuild an environment or set from concept art or photos in Blender (Houdini and Unreal later), to "keep iterating until it matches", to write the prompt another agent (Codex, Claude Code, OpenCode) will run for such a loop, or to judge a finished run. Triggers on "loop gauntlet", "gauntlet loop", "match the reference", "build it from these refs", "keep checking against the ref", "iterate until it matches", "reference match loop", "astra loop".
user-invocable: true
---

# Loop Gauntlet

**Version:** 1.4.1 | **Created:** 2026-09-09 | **Last updated:** 2026-09-11 | **Status:** public-safe (no studio paths; the run evidence lives in the workspace session log)

A gauntlet loop is a builder that keeps going until an authored quality bar
says stop. The pattern comes from the "builder plus fresh-eyes critic" idea
and from this workspace's fine-tune lane C, whose first lesson is the whole
skill in one line: **the checks are authored by the human before the loop
starts; the builder never invents its own.** A builder that writes its own
rubric grades itself against whatever it happened to do.

First run (2026-09-09, GPT-6 Astra in Codex driving a live Blender 5.1
through MCP, six matched views of a three-zone museum environment): seven
reviewed iterations, 42 loop renders plus six finals, visible progress every
iteration, and an honest stop under the stall rule with the target NOT met.
The lessons from that run are folded in below and in
`reference/first_run_lessons.md`.

## The contract - five things the human authors before the loop

1. **Reference set.** Clean plates only: remove people (Magnific edit, see
   `magnific-local-upload`), copy to one folder, and SETTLE DISAGREEMENTS
   between references before the loop. Two refs that disagree on an object
   count or a hero prop shape cannot both be matched by one scene; the first
   run lost a view to exactly that.
2. **Matched views.** One camera per reference, named `CAM_<view>`. A tile
   inside a contact sheet is a view too: give the crop box in the spec so the
   comparison uses the tile, not the sheet. **Lighting feasibility
   pre-check:** for each view, list the key lit surfaces the reference
   shows and confirm the planned key light can reach them (normal dot
   light direction), or record in the spec that the view will be scored
   with that limitation. Two views of the same curved corridor from
   opposite ends cannot both show a sunlit wall from one sun; catching this
   before the loop starts (not after several lighting-only iterations)
   turned out to require moving a camera, not tweaking the light.
3. **Rubric.** Fixed criteria scored 1 to 5 per view, a pass score, and a
   priority order for fixes (composition > scale > inventory > lighting >
   materials > detail). Materials are never polished while geometry is wrong.
4. **Evidence rule.** An iteration counts only when every render file has
   been read back (path, bytes, mtime, pixels) and the comparison image has
   been LOOKED AT. `compare_views.py` also flags a suspect-blank render;
   a blank frame is a valid PNG of plausible size (operating rule 8).
5. **Stop rules.** Target met (all views, all criteria >= pass for N
   consecutive iterations), max iterations, or STALLED. Stalled means neither
   the global minimum nor the total score improved for K iterations - the
   dual rule exists because a minimum-only rule froze the first run while
   four of six views were still improving. `min_iterations` is the floor
   below which a stall cannot fire: with composition fixed first, a builder
   plateaus on structure early, and one round-2 run stalled at iteration 5
   before the materials tier had a single iteration of its own.

All five live in one spec file: `templates/gauntlet_spec.example.json`.
The scripts read it, the prompt generator reads it, and a reviewer can diff it.

### Three more contract rules (props bench, 2026-09-11)

- **A frozen criterion still needs a real score against the reference, or
  it must be excluded from the total.** "4 = unchanged" as a rubric
  description rewarded an oversized plinth that had simply never been
  touched. Freezing a criterion means "verify it did not drift", not
  "assume it still matches" - see Continuation and refinement runs below.
- **A materials or render criterion needs a stated lighting target in the
  brief:** the world type and strength, the key light position, and a
  measured target luminance for the hero surface. Two refinement runs
  stalled with the exposure moved in opposite directions because the
  brief left the target for the builder to solve.
- **A human-authored count in a brief is a hypothesis until measured on
  the reference, not a given.** A brief specified six rim loops on a net;
  the reference photo showed nine. Treat counts and orientations the same
  way as any other claim - verify before building to them (see the
  camera-projection fit method in `reference/blender_loop_patterns.md`).

## Workflow

### 1. Prepare references and the spec

```bash
# copy the example, fill it in (forward slashes, no personal paths)
cp .claude/skills/loop-gauntlet/templates/gauntlet_spec.example.json <working_folder>/gauntlet_spec.json
```

- `reference_dir` holds the clean plates; each view names its file and an
  optional `crop` `[x0, y0, x1, y1]` for contact-sheet tiles.
- `render_size` is the loop size (1376x768 worked: fast in EEVEE, legible
  in the three-panel comparison).
- `brief_file` is a scene description the builder reads first: zones, how
  they connect, materials in value/hue families, lighting, hard constraints
  from the client. Give real-world anchors (bench 0.45 m, door 2.1 m) so
  scale is derived, not guessed - and say which reference wins when two
  disagree.

### 2. Generate the prompt (or run it yourself)

```bash
python .claude/skills/loop-gauntlet/scripts/gauntlet_prompt.py --spec <working_folder>/gauntlet_spec.json --harness codex --out <working_folder>/PROMPT.md
# --harness claude   when Claude Code runs the loop itself (this skill is the runbook)
# --harness opencode for the packaged-workflow runner
```

The prompt carries the contract verbatim plus the harness rules: live DCC
session so the operator can watch, incremental saves, named collections,
read state back before creating (no Cube.001), copy-only on job shares,
report a hung DCC instead of relaunching it, test a failing API call with a
known-good call before blaming the bridge. For Codex it adds: attach the
reference images to the message as well as giving paths, use cmd.exe or
python for shell steps, reasoning effort high.

### 3. Run the loop - the per-iteration ritual

Every iteration, in this order, no skipping:

```bash
# 1. render every matched view to renders/<tag>_<view>.png (DCC side; Blender pattern in reference/blender_loop_patterns.md)
# 2. compare + read back (exit 2 if any render is missing)
python <skill>/scripts/compare_views.py --spec gauntlet_spec.json --tag iter03
# 3. LOOK at compare/iter03_<view>_5.png for every view (5 panels: reference,
#    blend, render, edge overlay, difference), then write compare/iter03_review.json:
#    {"tag":"iter03","scores":{"hero":[3,4,2,2,2,4], ...},"gaps":["..","..",".."],"next":"..."}
# 4. log (refuses a tag already logged; refuses a tag with no readback file) and get the stop decision
python <skill>/scripts/log_iteration.py --spec gauntlet_spec.json --tag iter03
# 5. fix the three biggest gaps in priority order, save an increment, go again
```

Scores are the builder's judgement of the comparison image. A score that
jumps without a visible change is a reason to look again. There is no
numeric score on purpose.

`compare_views.py` writes two comparison instruments per view, each scoring
what the rubric scores separately (observation 0042: a 50 percent blend
mixes alignment and exposure into one soft double image and neither reads
cleanly). Look at the 5-panel `compare/<tag>_<view>_5.png`, not just the
3-panel image:

- **Edge overlay** (panel 4) is the silhouette/alignment instrument:
  reference edges cyan, render edges red, edges that coincide within 2px
  white, background black. A close match reads as mostly white. Quote
  `edge_iou` (intersection over union of the two dilated edge masks) and
  `edge_ref_covered` (fraction of reference edges within 2px of a render
  edge) in the review JSON's gaps when silhouette is in question - "edge
  overlay mostly white, edge_iou 0.71" is a real anchor; "the blend reads
  as one image" is not.
- **Difference panel** (panel 5) is the exposure/materials instrument: the
  absolute luminance difference through a black -> blue -> red -> yellow
  heat ramp, with the signed mean difference (render minus reference)
  printed in its header. Quote `mean_signed_lum_diff` and
  `mean_abs_lum_diff` from the readback when exposure or value match is in
  question.
- The **blend panel** (panel 2) stays only as a quick glance aid for
  gross composition sanity - it is not the instrument for either
  silhouette or exposure and should not be cited as evidence for either.

The older `--metric` flag still adds a separate edge-map correlation
(`edge_similarity`) to the readback, and on the first run's real renders it
read 0.01 to 0.08 on every view at iter01 AND iter07 - it did not track the
progress the eye saw. Use it only as a copy alarm (a value near 1.0 means
the "render" is the reference), never as a score.

A downsized comparison panel (viewed at roughly 600 px per panel) is a
steering aid, not a measuring instrument. Before moving geometry more than
0.5 m for composition, confirm the offset with a luminance row profile or
the projected camera position - never from the panel alone. One run read a
frieze as a full band too high and prescribed a 1.5 m move by eye; a row
profile and the analytic projection both showed the actual offset was
inside tolerance, and the same eye-read missed a real 15 percent luminance
drop between two iterations that a mean-luminance readback would have
caught immediately.

### 4. Finish

- Render finals with the SAME engine the loop used, then one pass with the
  hero engine (Cycles) as a separate, labelled comparison. The first run's
  Cycles finals regressed two corridor views' lighting from 2 to 1; a
  renderer switch at the end is a new variable, not a polish step.
- Build the final contact sheet, save the final increment, and end the log
  with an honest summary: what matches, what does not and why, settled
  dimensions, first objects to touch next.
- `python <skill>/scripts/stop_check.py --spec gauntlet_spec.json` prints
  the whole trajectory as a table - paste it into the session log.

### Continuation and refinement runs

A leg that continues or refines an existing scene (rather than building
from scratch) shares a live DCC session with the run that came before it,
and that changes the opening step: **before opening the working file,
read back the currently open file's path, `bpy.data.is_dirty`, and its
last-save time (mtime), and confirm the other run's LOOP_LOG ends with a
STOP decision.** If the scene is dirty, or the mtime does not match the
file's own last save, or the log has no stop decision, report and wait -
do not open the file. A live DCC is shared state; opening a file is a
destructive act on whatever is loaded.

A refinement run that freezes some criteria (camera, scale, composition)
still owes those criteria a real score against the reference, or they must
be excluded from the total - never scored as an automatic pass. A round-3
lesson: a rubric description of "4 = unchanged" rewarded an oversized
plinth that had simply never been touched. A frozen criterion means
"verify it did not drift" (a `matrix_world` compare, or a re-read of the
same measurement used to accept it originally), not "assume it still
matches."

**Open follow-ups, not yet implemented in the scripts:** a spec `mode`
field (`build` / `continue` / `refine`) so the generated prompt's opening
paragraph and "Where to work" section describe the actual task instead of
always reading as a from-scratch build; and `gauntlet_prompt.py` emitting
the dual stall rule verbatim into the brief so the prompt and
`log_iteration.py` can never disagree (they diverged once: the brief's
older min-only wording said STOP while the script's dual rule said
CONTINUE).

### Operator nudge channel

A headless loop has no input channel after launch, so give the operator one
file the builder is required to read: `<working_folder>/OPERATOR_NOTES.md`.
`log_iteration.py` prints its contents after every logged iteration, so the
operator watching the DCC or the console can drop a correction in at any
time without touching the running session. Read it before planning every
iteration; a note in it overrides the brief where the two conflict.
Date-stamp each note so the builder (and the log) can tell which iteration
it landed on.

The channel only updates at an iteration boundary, so a note written mid
iteration is not seen until the next `log_iteration.py` call. Two
consequences for the operator: send a note at least two iterations before
`no_improvement_streak` could fire the stall rule, or raise
`no_improvement_streak` for that run when you know you plan to nudge partway
through - a note that lands one iteration before a stall fires cannot save
the run.

### 5. Judge the run (human)

The agent's self-scores are its steering signal, not the verdict. Read the
final contact sheet yourself (`compare/final_contactsheet.jpg`), score it
blind against the same rubric, and compare with the log. For a bench across
harnesses or models, keep the spec, refs and brief byte-identical and
compare: iterations to stop, human final scores, object naming hygiene,
interventions, wall-clock, tokens.

## Operator watch-list while it runs

- Iterations narrated but never rendered: no `renders/iterNN_*.png` and no
  readback JSON behind a log entry. Stop it. (Astra has a documented
  narrate-and-report-done failure mode.)
- Score inflation without visible change in `compare/`.
- Duplicate objects (`.001` suffixes) - the read-state-back rule is in the
  prompt; glance at the outliner.
- Material or haze work while composition is still scoring 2.
- Any delete, move or rename on a job share - it is copy-only for agents.
- A hung DCC: the prompt says report, not relaunch; increments mean a kill
  costs one iteration at most.

## Harness notes

| Harness | How the loop runs | Notes |
|---|---|---|
| Codex (GPT-6 Astra) | paste the generated prompt into the GUI, attach refs | high reasoning; managed policy hook applies; the DCC must already be open (harness mode blocks app launches); MCP calls need an approval mode that does not click per call |
| Claude Code | this skill is the runbook; run the ritual above | incremental saves during ALL Blender work (house rule); build in the live session so the operator can watch |
| OpenCode | packaged-workflow runner | shell-only steps fine; DCC MCP through its plugin |

### Isolation between legs on the same harness

A harness that auto-loads its own workspace docs at session start (Codex
reading `HANDOFF.md`/`AGENTS.md`, or any harness reading a memory file) makes
every earlier leg part of the next leg's brief. A leg whose brief
deliberately withholds information (a "find the dimensions yourself" test),
or any second leg run on the same harness after a first one, MUST run from
an isolated profile with no workspace docs in it - a fresh working folder is
not enough, because the workspace-level handoff file is still there to be
read. Before launching leg N, grep the harness's auto-loaded docs for leg
N-1's object name to confirm nothing leaked.

Verified isolated Codex launch (2026-09-09, reconfirmed 2026-09-11): build a
throwaway `CODEX_HOME` with its own `config.toml` (model, model_reasoning_effort,
the Blender MCP server entry, `[features]` `hooks=true`, and a
`[projects.'<cwd>']` `trust_level = "trusted"` entry) plus a copy of
`auth.json`, then run from an empty cwd:

```
codex --search exec --skip-git-repo-check --approve-for-me --add-dir <work> -i <ref> - < PROMPT.md
```

`--search` is a top-level flag - `codex exec` rejects it if placed after
`exec`. An untrusted/empty cwd needs `--skip-git-repo-check` (or the
`trust_level = "trusted"` entry above). The sandbox reports itself as
read-only in this profile; writes still land because `--approve-for-me`
grants them.

## DCC specifics

- **Blender:** `reference/blender_loop_patterns.md` - non-blocking render
  queue on `bpy.app.timers` with a status JSON (an MCP call that renders six
  views inline times out), the image-pixel persistence trap (assign colour
  space BEFORE writing pixels, pack, then verify nonzero pixels after save),
  EEVEE for the loop, incremental save before every render.
- **Houdini / Unreal:** not exercised yet. The contract and scripts are
  DCC-agnostic; only the render step changes. Add a reference file when the
  first run happens.

## Scripts

| Script | What it does |
|---|---|
| `scripts/gauntlet_prompt.py` | spec + brief -> paste-ready prompt for codex / claude / opencode |
| `scripts/compare_views.py` | renders vs references: 3-panel comparison (compatibility) plus a 5-panel instrument image (edge overlay, difference heatmap), contact sheet, readback JSON with suspect-blank flag, edge/difference metrics, optional edge_similarity metric |
| `scripts/log_iteration.py` | appends the iteration to LOOP_LOG.md from review + readback, runs the stop rule |
| `scripts/stop_check.py` | trajectory table and the continue/stop decision (dual stall rule) |
| `scripts/test_loop_scripts.py` | self-test on synthetic images; run it after any edit |
| `templates/gauntlet_spec.example.json` | the contract, as a file |

Every flag above exists in the script's `--help`; the self-test proves the
three loop scripts agree on the spec shape.

## Troubleshooting

**Suspect-blank render flagged.** `unique_values` under 8 means a flat or
black frame: wrong active camera, render layer disabled, or the render
never wrote. Do not score it; fix the render and re-run compare. A pass
scored on a blank frame is the false PASS that operating rule 8 is about.

**Stalled by one hard view.** The dual stop rule still stops when total and
minimum are both flat. If one view has a structural mismatch (the first
run's curved corridor) while the rest climb, it is a reference or plan
problem, not a loop problem: park that view (remove it from the spec with
a note in the log) or fix the plan, then continue. Never widen the rubric.

**References disagree.** Two refs imply different object counts or a
different hero prop. The loop cannot resolve this; the human picks the
canonical one before iteration one and the brief says so.

**Final render regressed.** Switching engine for finals changed lighting.
Report it as a regression (the first run did), keep the loop-engine finals
as the match evidence, and treat the hero-engine pass as a new task.

**Render call times out through MCP.** Use the timer-based queue pattern;
poll the status JSON; never re-submit a render while one is running.

## Version History

**v1.4.1** (2026-09-11) - Observation 0042: `compare_views.py` adds a
5-panel instrument image (`compare/<tag>_<view>_5.png`, kept separate from
the unchanged 3-panel image for compatibility) with an edge overlay
(cyan=reference-only, red=render-only, white=coincident within 2px) and a
black-blue-red-yellow difference heatmap, plus four new readback metrics
(`edge_iou`, `edge_ref_covered`, `mean_signed_lum_diff`,
`mean_abs_lum_diff`). SKILL.md step 3 now points at the 5-panel image and
names the edge overlay / difference panel as the silhouette / exposure
instruments respectively, with the blend panel demoted to a glance aid.

**v1.4.0** (2026-09-11) - Props bench lessons. Added the operator nudge
channel (`OPERATOR_NOTES.md`, printed by `log_iteration.py` every
iteration, notes override the brief, timing rule against the stall
streak) to SKILL.md and to the generated prompt. Added the harness
isolation rule for legs that withhold information or repeat on the same
harness, with the verified vanilla Codex launch line. Added three
contract rules: a frozen criterion must still be scored or excluded from
the total; a materials/render criterion needs a stated lighting target
(world, key position, measured hero-surface luminance); human-authored
counts in a brief are hypotheses to verify on the reference. Added a
"Fit before render" camera-projection method and the render-pipeline
scratch-test rule to `reference/blender_loop_patterns.md`.

**v1.3.0** (2026-09-10) - Round-3 lessons. Lighting-feasibility pre-check
added to the matched-views contract step. Composition moves above 0.5 m
now require a row-profile or projection check, not a panel eyeball.
Continuation/refinement runs get a shared-live-DCC opening check
(is_dirty, mtime, other run's stop decision) and a rule that frozen
criteria must still be scored, not auto-passed. Noted open follow-ups: a
spec `mode` field and the generator emitting the dual stall rule verbatim
(not yet implemented).

**v1.2.0** (2026-09-10) - Round-2 bench lessons. `stop.min_iterations`
floor for the stall rule (stop_check + prompt). Generator v1.1.0 fields
`tools[]` and `spend_cap_usd` (tool-surface section, spend contract with
zero-cost gate, balance read-back, GEN_LEDGER.md, no real marks). Rubric
anchors recommended in every `desc` (they tightened self-calibration from
a 40-point gap to within 5 points across two builders).

**v1.0.0** (2026-09-09) - First release, from the Codex/Astra museum run
(observation #26). Contract, prompt generator, comparison and logging
scripts with the dual stall rule, Blender patterns, first-run lessons.
