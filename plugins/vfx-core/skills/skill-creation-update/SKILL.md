---
name: skill-creation-update
description: "Writes, updates and validates Claude Code skills (SKILL.md) to the house standard - one-line YAML description, no retired top-level keys, traps-first body under 500 lines, retirement outside .claude/. Use when creating a skill, fixing or migrating an old-format one, or checking skills before a sync."
when_to_use: Triggers on "write a skill", "new skill", "update this skill", "fix the frontmatter", "validate the skill", "migrate SKILL.md", "retire a skill".
metadata:
  version: 2.0.0
  updated: 2026-11-09
---

# skill-creation-update

The rules live in `ClaudeCode/development/SKILL_AND_AGENT_STANDARD.md` (it supersedes the
frontmatter and archiving articles of the constitution). This skill is the traps that keep
getting missed plus the scripts that enforce them. Script paths below are relative to this
skill's folder (`<skill-dir>`).

## Traps (read first)

1. **A folded or multi-line description breaks harnesses.** `description: >`, `>-`, `|`, or a
   description that wraps onto an indented next line. YAML parses all of these, so a parse
   check passes them; OpenCode drops the skill and Claude Code can list it with an empty
   description. In the 2026-11-09 eval BOTH arms (with and without this skill) kept a folded
   description while updating an old skill (case sk2). When you update a skill, rewrite the
   description line itself - moving the other keys is not enough. One line; double-quote it.
2. **No top-level `version`, `last_updated`, `status`, `triggers`, `tags`, `author`.** Claude Code
   ignores them. The retired agent-creation-update kept them and scored worse than no skill.
   Bookkeeping goes under `metadata:` (or git history); trigger phrases go in `when_to_use`.
   Do not add "Skill Version / Last Updated" header lines or a Version History section to the
   body either - git is the history.
3. **An unquoted `: ` inside a value is a YAML error, and a skill that fails to parse is dropped
   silently** (observation 440: two agents vanished from the list). Quote the value.
4. **No `<` or `>` in description or when_to_use** - they render as `&lt;`. Write `[name]`.
5. **Retiring = moving the folder out of `.claude/`** to `archive/skills/<name>/`. A folder named
   `archive` inside `.claude/skills` is still scanned. To hide a skill without retiring it, use
   `skillOverrides` (standard, section 5). Confirm in a fresh session's listing, not the folder.
6. **A validator that examined nothing has not passed.** `validate_skill.py` takes a name or a
   path and exits 1 when it finds no skill; read the exit code, not just the last line.
7. `model` / `effort` are valid skill fields (the old "model causes a 404" rule is retired); use
   them only for a deliberate reason.

## Create a skill

```bash
python <skill-dir>/scripts/create_skill.py my-skill \
  --description "Does X for Y. Use when Z." --when-to-use "Triggers on 'phrase'." \
  [--paths "**/*.nk"] [--manual] [--reference] [--scripts] [--skills-path DIR] [--dry-run]
```

It writes a quoted one-line description, `metadata:` bookkeeping and a traps-first skeleton,
then runs the validator. Replace every `FILL:` line (the validator warns while any remain).
Content rules (standard, section 3): first clause says what it does, second says when; third
person; 150-400 chars. Body: hard rules and the mandatory first step in the first ~40 lines;
only what Claude does not already know; detail in `reference/*.md`, linked one level deep,
with a table of contents on any reference file over 100 lines.

## Update or migrate an existing skill

1. `python <skill-dir>/scripts/update_skill.py NAME --migrate --dry-run`, then without
   `--dry-run`. It moves retired and undocumented top-level keys under `metadata:` (triggers
   into `when_to_use`), joins a folded description onto one line, leaves the body byte-exact,
   and re-validates. It drops frontmatter comments (it says so).
2. Read the frontmatter back, then rewrite the description wording yourself - the script only
   joins lines; it does not front-load "what" before "when".
3. Move critical rules into the first screen; cut tutorial content the model already knows.
4. Version: `update_skill.py NAME --version X.Y.Z` sets `metadata.version` and `updated`.
   A skill that ships in a plugin also needs that plugin's version bumped in the registry -
   the operator's step in the sync workflow, not this script's.

## Validate

```bash
python <skill-dir>/scripts/validate_skill.py NAME_OR_PATH     # one skill, exit 1 on FAIL
python <skill-dir>/scripts/batch_validate.py [--quiet]        # every skill + archive folders
python <skill-dir>/scripts/selftest_validate.py               # after changing any script here
```

FAIL: missing skill, no or unparseable frontmatter, multi-line description or when_to_use,
retired or undocumented top-level keys, `<`/`>` in description, over the 1,536-char listing
cap, non-ASCII or control bytes in shipped scripts. WARN: body over 500 lines, description
over 400 chars or not front-loaded, name differs from folder, long reference without a TOC,
absolute paths in scripts, unfilled `FILL:` lines.

The validator is necessary, not sufficient. The manual checks (documented flags vs `--help`,
shipped defaults, scripts that download or walk a share, the self-containment check) are in
`reference/validation_checks.md`. The full release checklist is the standard's section 8.

## Prove the skill helps

A general-know-how skill must beat a no-skill baseline before it is kept (standard, section
7: `claude plugin eval`, with and without, read the WITH vs W/OUT table). Read section 7
before building cases - it records the traps (MCP ablation, `--runs`, pinned `--model`). Both
arms passing means the skill is not what made it pass: cut it down to the house knowledge.

## Scripts

| Script | Does |
|---|---|
| `scripts/create_skill.py` | scaffold a skill in the standard format, then validate |
| `scripts/update_skill.py` | `--migrate` old frontmatter, `--version` bump under metadata |
| `scripts/validate_skill.py` | one skill against the standard (exit 0 / 1, 2 = no PyYAML) |
| `scripts/batch_validate.py` | all skills in a folder, plus archive folders that still load |
| `scripts/selftest_validate.py` | two-way test: clean skills pass, folded descriptions and retired keys fail |
| `scripts/test_skill.py` | optional smoke test: run a skill's main script against 3+ targets |
