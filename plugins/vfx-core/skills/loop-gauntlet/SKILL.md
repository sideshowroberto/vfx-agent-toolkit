---
name: loop-gauntlet
description: Run a build-until-it-matches loop in a DCC - an agent builds a scene from reference images, renders matched camera views every iteration, compares each render to its reference side by side, scores it against a rubric the HUMAN authored, logs read-back evidence, and a stop rule decides when it is done. Use when asked to rebuild an environment or set from concept art or photos in Blender (Houdini and Unreal later), to "keep iterating until it matches", to write the prompt another agent (Codex, Claude Code, OpenCode) will run for such a loop, or to judge a finished run. Triggers on "loop gauntlet", "gauntlet loop", "match the reference", "build it from these refs", "keep checking against the ref", "iterate until it matches", "reference match loop", "astra loop".
user-invocable: true
---

# Loop Gauntlet

**Version:** 1.0.0 | **Created:** 2026-09-09 | **Status:** public-safe (no studio paths; the run evidence lives in the workspace session log)

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
   comparison uses the tile, not the sheet.
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
   four of six views were still improving.

All five live in one spec file: `templates/gauntlet_spec.example.json`.
The scripts read it, the prompt generator reads it, and a reviewer can diff it.

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
# 3. LOOK at compare/iter03_<view>.png for every view, then write compare/iter03_review.json:
#    {"tag":"iter03","scores":{"hero":[3,4,2,2,2,4], ...},"gaps":["..","..",".."],"next":"..."}
# 4. log (refuses a tag already logged; refuses a tag with no readback file) and get the stop decision
python <skill>/scripts/log_iteration.py --spec gauntlet_spec.json --tag iter03
# 5. fix the three biggest gaps in priority order, save an increment, go again
```

Scores are the builder's judgement of the comparison image. A score that
jumps without a visible change is a reason to look again. There is no
numeric score on purpose: `--metric` adds an edge-map correlation to the
readback, and on the first run's real renders it read 0.01 to 0.08 on every
view at iter01 AND iter07 - it did not track the progress the eye saw. Use
it only as a copy alarm (a value near 1.0 means the "render" is the
reference), never as a score.

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
| `scripts/compare_views.py` | renders vs references: 3-panel comparisons, contact sheet, readback JSON with suspect-blank flag, optional edge metric |
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

**v1.0.0** (2026-09-09) - First release, from the Codex/Astra museum run
(observation #26). Contract, prompt generator, comparison and logging
scripts with the dual stall rule, Blender patterns, first-run lessons.
