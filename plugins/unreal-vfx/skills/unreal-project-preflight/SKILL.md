---
name: unreal-project-preflight
description: Verify and batch-fix the Unreal project prerequisites a plan depends on - plugins, project settings, editor config - as a mandatory Step 0 between plan approval and execution, so a build never dies mid-task on a disabled plugin or a setting that needs a restart. Use after any Unreal plan is approved, before the first build step, whenever a task will touch MegaPlants/PVE, PCG interops, Water, Landscape Patches, Movie Render Queue, cryptomatte, ImagePlate, Substrate, ray tracing or the MCP server, and whenever an error says a class, node or plugin is missing. Triggers on "preflight", "check the project settings", "which plugins do we need", "is nanite foliage on", "enable the plugin", "why is the class missing", "restart the editor", "project prerequisites", "before we build".
allowed-tools: Read,Bash,Grep,mcp__ue58-mcp__execute_python_code
---

# unreal-project-preflight

**Version:** 1.0.0
**Last Updated:** 2026-09-08
**Dependencies:** Unreal Engine 5.8 (launcher install), Python 3.10+, curl on PATH, UE 5.8 native MCP on the project's configured port for `--live`
**Status:** Production-ready (probed against two real 5.8 projects on 2026-09-08)

---

## Why this skill exists

Every Unreal build session that went wrong in the same way: the plan was
approved, the agent started creating things, and the first real step failed
because a plugin was off (ImagePlate, ProceduralVegetationEditor,
MovieRenderPipeline), a project setting was not on (Nanite Foliage for
MegaPlants, SM6 for Nanite), or the fix needed an editor restart that then
lost unsaved component edits. The unreal-* skills document APIs, not the
switches those APIs sit behind.

This skill puts ONE pass between "plan approved" and "step 1": read what the
project actually has, list every change the plan needs, apply them as a
batch, restart ONCE, read the result back, and only then start building.

---

## CRITICAL: MANDATORY FIRST STEP

Run the checker against the project the plan targets before writing any
Step 0 by hand. Never list prerequisites from memory.

```bash
# The editor is running: ask it which project it has open and read plugins back
python <skill-dir>/scripts/ue_preflight.py --live --features <feature,list> --plan-block

# The editor is closed: check the files the next launch will load
python <skill-dir>/scripts/ue_preflight.py --project <path>/Show.uproject --features <feature,list> --plan-block
```

Read the `project :` line. If `--live` reports the editor has a DIFFERENT
project open than the one the plan targets, stop: the live readings describe
the other project, and building would land in the wrong place. (This
happened during the skill's own commissioning: the production project was
the intended target, the editor had a dev-tests project open.)

---

## Standard Workflows

### Workflow 1: The ritual (where it sits in a plan)

1. **Plan is written and approved** (vfx-plan, goal-criteria-planning, or a
   plain plan in chat).
2. **Derive the feature list** from the plan's steps. Every step that names
   an Unreal subsystem maps to one or more catalog features
   (`--list-features`). "Forest with a road through it" is at least
   `pcg,megaplants,landscape-patch` and usually `mrq` for the check render.
   Add ad-hoc `--require` specs for anything the catalog lacks.
3. **Run the checker** (above) and paste its `--plan-block` output into the
   plan as **Step 0 - Environment preflight**. The block already contains the
   change list, the restart plan and the feature notes.
4. **Get the operator's OK on Step 0** - plugin toggles and renderer
   settings are project-wide and land in source control.
5. **Execute Step 0 as written:** save, operator closes the editor, `--apply`,
   relaunch, `--live` re-run must report `0 need changes`. That read-back is
   the gate; a summary line with anything but 0 means Step 1 does not start.
6. Only now Step 1.

**Mid-task rule:** any error of the shape "class not found", "unknown node
type", "plugin not enabled", "setting requires restart" sends you back to
this ritual with the missing feature added - never improvise a runtime
toggle and keep going. A console CVar set at runtime is volatile and lies to
the next session.

---

### Workflow 2: Mid-task recovery

An error naming a missing class, node type or plugin during a build is a
prerequisite failure, not a code bug. Stop the step, map the missing thing
to a feature (or an ad-hoc `--require`), re-run the checker with the FULL
original feature list plus the new one, and re-enter Workflow 1 at step 3.
The re-run must include the original list so the single restart covers
everything, not just the newest miss.

### Workflow 3: Commissioning a project for the agent

New job, fresh project: run `--features mcp,python,pcg` plus whatever the
job's environment pipeline needs (see the job's `AGENT/PROJECT.md`), apply,
restart once, and file the `--json` read-back with the job's first session
log. Every later plan on that job inherits a project that already passes.

---

## Quick Start

```bash
# What can it check?
python scripts/ue_preflight.py --list-features

# Forest-with-road plan, editor running
python scripts/ue_preflight.py --live --features pcg,megaplants,landscape-patch,mrq --plan-block

# Something the catalog does not know yet
python scripts/ue_preflight.py --live --require plugin:SomePlugin \
    --require "ini:DefaultEngine:/Script/Engine.RendererSettings:r.Some.Setting=1"

# Apply the change list (editor closed), then read back after relaunch
python scripts/ue_preflight.py --project <path>/Show.uproject --features pcg,megaplants,landscape-patch,mrq --apply
python scripts/ue_preflight.py --live --features pcg,megaplants,landscape-patch,mrq

# Keep the evidence with the session log
python scripts/ue_preflight.py --live --features ... --json <session-dir>/preflight_readback.json
```

Exit codes: `0` everything satisfied, `1` changes needed (or apply refused),
`2` error. Every flag above exists in `--help`; the doc and the script were
diffed on 2026-09-08.

**Expected output shape:**

```
project     : <path>/Show.uproject
engine root : <engine root>  (registry EngineAssociation=5.8; 895 plugin descriptors indexed)
live editor : 5.8.0-...  project=<path>/Show.uproject  enabled plugins=249

REQUIREMENT                                   STATUS   CURRENT                                 RESTART  FIX
plugin:ProceduralVegetationEditor             MISSING  disabled (off by default); live disabled  yes    add {"Name": ...} to Plugins in the .uproject
plugin:PCG                                    OK       enabled (descriptor default); live enabled -
ini:DefaultEngine:/Script/Engine.RendererSettings:r.Nanite.Foliage=True  MISSING  (absent)  yes  DefaultEngine.ini: add ...

summary     : 6 checked, 3 ok, 3 need changes, 0 not verified; restart needed: YES
```

---

## What it reads, and what it trusts

| Source | What it proves | Trust |
|---|---|---|
| `<project>.uproject` Plugins array | what the NEXT launch enables/disables explicitly | primary |
| engine + project `.uplugin` descriptors | `EnabledByDefault`, experimental/beta flags, dependency lists (closure computed - a plugin pulled in by another counts as enabled) | primary |
| `Config/Default*.ini` | renderer / target-platform / editor project settings the next launch loads | primary |
| `Saved/Config/WindowsEditor/*.ini` | per-user settings set through the UI (accepted as a fallback via `StemA|StemB` specs) | fallback |
| live editor (`--live`) | what THIS session actually has: open project, enabled plugin names, CVar values | read-back |

Facts the design rests on (all probed 2026-09-08 on 5.8):

- `unreal.PluginBlueprintLibrary.get_enabled_plugin_names()` and
  `is_plugin_mounted()` exist; there is NO enable/disable API from Python.
  Enabling a plugin is a `.uproject` edit plus a restart, full stop.
- `RendererSettings` is not reflected into Python (`unreal.RendererSettings`
  is missing; the CDO via `load_class` has no readable properties). Project
  settings are read from the ini, never from the editor.
- `SystemLibrary.get_console_variable_int_value` returns `0` for a variable
  that does not exist. A live `0` is therefore never a finding on its own -
  the ini decides, the CVar only confirms.
- Every `.uproject` or `Default*.ini` change needs a restart to take effect
  for the session. Some settings prompt for it in the UI and some do not;
  the checker marks all of them `RESTART yes` on purpose.

---

## Requirement spec grammar

```
plugin:<Name>                                  .uplugin basename (case-sensitive)
ini:<Stem>:<Section>:<Key>=<Value>             Default* stems -> Config/<Stem>.ini
                                               other stems   -> Saved/Config/WindowsEditor/<Stem>.ini
ini:<StemA|StemB>:<Section>:<Key>=<Value>      either file satisfies it; --apply writes StemA
ini:<Stem>:<Section>:+<Key>=<Value>            list-valued key must contain Value (+Key lines)
cvar:<r.Name>=<Value>                          live read-back only; SKIPPED offline
```

Values compare case-insensitively with `True`/`1` and `False`/`0`
equivalent. Real examples from the catalog:

```
plugin:ProceduralVegetationEditor
ini:DefaultEngine:/Script/Engine.RendererSettings:r.Nanite.Foliage=True
ini:DefaultEngine:/Script/WindowsTargetPlatform.WindowsTargetSettings:+D3D12TargetedShaderFormats=PCD3D_SM6
ini:DefaultEditorPerProjectUser|EditorPerProjectUserSettings:/Script/UnrealEd.EditorModelContextProtocolSettings:Port=8000
```

---

## Catalog features (reference/requirements_catalog.json)

`--list-features` is authoritative; this is the map. Aliases such as `pve`,
`cryptomatte`, `foreground-plate` resolve to the canonical names.

| Feature | Requires (summary) |
|---|---|
| `pcg` | PCG plugin |
| `pcg-geometry` / `pcg-water` / `pcg-biome` / `pcg-niagara` | the interop plugin + its partner (GeometryScripting, Water, ...) |
| `megaplants` | ProceduralVegetationEditor + PCG + `r.Nanite.Foliage=True` + SM6 + DX12 |
| `nanite` / `lumen` / `vsm` / `substrate` / `raytracing` | the RendererSettings keys each needs (+ SM6/DX12 where relevant) |
| `water` / `landscape-patch` / `landmass` | the plugin |
| `mrq` / `mrq-cryptomatte` / `ocio` | MovieRenderPipeline, MoviePipelineMaskRenderPass, OpenColorIO |
| `imageplate` | ImagePlate (experimental, off by default - needed by the sequencer and vfx skills) |
| `sequencer-python` / `python` / `geometry-scripting` / `modeling` | the scripting-side plugins |
| `mcp` / `vibeue` | ModelContextProtocol (+ its ini keys), VibeUE from Fab |
| `niagara-fluids`, `hair-strands`, `usd`, `alembic`, `datasmith`, `livelink`, `takes`, `virtual-camera`, `composure`, `camera-calibration`, `cine-camera-rigs`, `template-sequence`, `virtual-heightfield` | the plugin (+ skin cache for hair) |

Each feature can carry `notes` - production lessons the plan should inherit
(MegaPlants presets bake UI-only, MRQ ObjectId skips skinned instances,
Substrate toggles recompile every shader, ...). `--plan-block` prints them.

**Extending the catalog:** add a feature with `summary`, `requires`, and
`notes`. Plugin names must be `.uplugin` basenames that exist in the engine
or the project - run the checker once against a project; `NOT_IN_ENGINE`
on a name you expected in the engine means a typo, not a missing install.

---

## Restart policy

- **One restart per plan.** Collect every restart-requiring change into
  Step 0. A second restart mid-build is a planning failure, not bad luck.
- **Save first.** Unsaved component edits (stencil flags, cull distances,
  anything set through MCP) do not survive a restart - one production's
  render nights lost the same edits twice this way.
- **The operator closes the editor.** The agent never kills a live editor
  it did not launch; it asks, waits, then runs `--apply`.
- **`--apply` refuses while the editor has the project open** (the editor
  can rewrite `.uproject` and the ini on exit and silently undo the edit).
  `--apply-while-running` exists for the case where the operator has
  accepted that risk; say so in the plan if you use it.
- **`--apply` backs up** each touched file next to itself
  (`<file>.bak_<stamp>`) and only adds or replaces the exact keys it
  reported. Ini encoding (BOM) and line endings are preserved.
- **Read-back after relaunch is the gate**, not "the editor came up".
  Re-run with `--live`; the summary line must say `0 need changes`.

---

## Troubleshooting

- **Live project mismatch.** The editor may have a different project open
  than the plan targets (probe-verified). The checker warns and ignores
  live readings in that case; do not proceed on them.
- **`plugin:X` MISSING but the feature works in the editor?** X is enabled
  through a dependency the offline closure could not see (an engine plugin
  outside the indexed roots, or a `--engine-root` mismatch). `--live`
  resolves it: live enabled overrides the offline verdict.
- **`NOT_IN_ENGINE`** means no descriptor was found anywhere - a Fab or
  marketplace plugin that is not installed, or an unresolved engine root
  (`engine root : UNRESOLVED` on the header line). Fix the root first.
- **MCP ini keys absent** on a project whose MCP still answers: the plugin
  defaults apply. Prove the server with a netstat on the port or a
  successful `--live`, not with the ini rows.
- **Per-landscape switches are not project settings.** Landscape Patches
  need Edit Layers on the landscape ACTOR; Water Bodies need a Water Zone in
  the level. The catalog notes say so; check them in the level.
- **CVars set at runtime are volatile.** `r.Nanite.MaxPixelsPerEdge` for a
  render lives in the MRQ preset; a project-wide setting lives in the ini.
  A `cvar:` spec only reads back, it never persists.
- **Windows paths in specs** go through the shell - quote any spec that
  contains `=` or `|` in PowerShell.

---

## Verification (what "done" reads back as)

| Step | Read-back |
|---|---|
| checker ran | header shows the intended project path and a resolved engine root with a descriptor count |
| plan block pasted | Step 0 in the plan lists the same change count the checker printed |
| `--apply` | its log names each backup file and each key it wrote; `git diff` / P4 diff on `.uproject` and the ini shows only those lines |
| relaunch | `--live` summary: `N checked, N ok, 0 need changes` |
| evidence | `--json` file saved with the session log for job work (job sandbox, never claudeFiles) |

---

## Reference Documentation

- `reference/requirements_catalog.json` - the feature -> requirements map
  this skill ships (aliases, `requires` specs, production notes per feature).
- `scripts/ue_preflight.py --help` - every flag, the spec grammar and exit
  codes; the examples in this file were diffed against it.
- `.claude/rules/unreal.md` - the hard rule that makes Step 0 mandatory, plus
  the MRQ / PCG / Nanite gotchas the catalog notes summarise.
- Epic docs: Project Settings > Rendering (Nanite, Lumen, Substrate, VSM),
  Plugins browser, and the per-plugin `.uplugin` descriptors under
  `<engine>/Engine/Plugins/` (the `EnabledByDefault`, `IsExperimentalVersion`
  and `Plugins` dependency fields the checker reads).

---

## Constitutional Compliance

- **Article I (general-purpose scripts):** `ue_preflight.py` takes the
  project, engine root and MCP URL as arguments or environment; no drive
  letters, usernames or job names are built in; tested on two projects.
- **Article II (MCP vs direct):** file state is read directly from disk;
  the editor is consulted only through the native MCP for the live read-back.
- **Article III (progressive disclosure):** the catalog and the CLI help
  carry the detail; this file stays under 300 lines.
- **Article IV (test independently):** offline mode needs no editor; the
  live probe degrades to a warning when the server is unreachable.
- **Article VI (context efficiency):** one command replaces reading the
  `.uproject`, three ini files and ~900 plugin descriptors into context.
- **Article VIII (documentation):** flags verified against `--help`,
  read-back named for every step, ASCII-only.

---

## Version History

- **1.0.0** (2026-09-08) - Initial release. Catalog of 37 features verified
  against the 5.8 launcher plugin set; checker probed live against a
  dev-tests project (dependency closure matches the editor's own enabled
  list) and offline against a production project; `--apply` proven
  idempotent on a scratch copy.
