# loop-gauntlet version history

Newest first. SKILL.md carries the current version line and points here.

**v1.6.0** (2026-10-10) - Skill review wave 2 (owner-approved observations).
- Contract authoring moved to `reference/contract_authoring.md`: plan and
  layout drawings as measuring references (obs 59); classify the bands of a
  generated "orthographic" elevation as geometry or projection (114);
  lead-supplied reference set prep - allowlist, crops, padding in the
  photo's colour, client images as views (91); reference-versus-render_size
  aspect check and the `ref_aspect_mismatch` flag (61); human-stated up axis
  and units with the optional spec `scene` block (60); solve repeated-element
  hero views before iteration one (65); a "Which subjects to loop" routing
  table (92).
- Rubric instruments, one principle - every element needs an instrument that
  can fail: clay pass for mirror-finish subjects, both directions (49);
  unscored survey cameras, "a pixel or a ray shows it", render gated on the
  geometry read-back (66); own grey for thin negative features (112);
  `lighting_target` spec block with box means for balance and feature checks
  for placement (117); lighting feasibility traced through the real openings
  (116); pointers to `reference/lighting_match.md`,
  `scripts/scratch_luminance.py`, `scripts/solve_light_mix.py`.
- Scoring default (107, owner decision): the builder self-scores each
  iteration; a fresh cheaper sub-agent that sees only the comparison panel,
  references and rubric scores every 3rd iteration and before any STOP,
  pipelined behind the next build.
- Operator notes and bench conditions: "Writing a note" - restore point,
  checkable target, deciding metric, verify-against-photo, scratch comparison
  when the geometry already scores 3, withdraw a wrong note by name (62,
  merged 50); identical notes for every comparison leg (46); read back the
  skill copy the harness actually loads (45); reference files become
  numbered steps (47); Codex parallel DCC chains disable the other MCP
  servers per run (90); iteration cap sized against the runner's remaining
  budget, deliverables floor, resume document (63).
- New "Stand-in / grey-pass production mode" section, with the
  `min_iterations` versus cap note.
- Delivery record: `templates/final_delivery.example.json` - axes, units,
  ground, member nodes, hidden-but-render-enabled objects, per-object
  read-back (102, merged 99).
- Houdini patterns are live-verified; the "not yet exercised" text is gone.
- Version history moved out of SKILL.md into this file.

**v1.5.0** (2026-09-12) - Houdini support: reference/houdini_loop_patterns.md
(live-verified on 21.0.596) and a dcc=houdini branch in gauntlet_prompt.py;
save-before-render rule.

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
