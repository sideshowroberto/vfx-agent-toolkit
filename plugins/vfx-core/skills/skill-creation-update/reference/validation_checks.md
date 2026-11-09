# Manual validation checks

`validate_skill.py` checks the frontmatter, size and script bytes. These checks it cannot
do; run the ones that apply before a skill ships.

## Bundled scripts

- **Every flag a SKILL.md example shows must exist in that script's `--help`.** Run the help
  and compare. qwen-delegate shipped a phantom `--file` flag and a dead default port for
  weeks because nobody ran the script from the doc (observation 4).
- **Shipped defaults:** grep `scripts/` for drive letters, usernames and version-pinned
  install paths in defaults and module constants
  (`grep -nE "[A-Za-z]:[/\]|Users|[0-9]+[.][0-9]+ ?v[0-9]" scripts/*.py`). Each hit becomes an
  argument or a config file the workflow passes, and the run prints the effective value.
  nuke-shot-setup shipped a dead personal OCIO path and Nuke 15 as defaults (observation 9).
- **A skill documents its own scripts as `<skill-dir>/scripts/...`**, never by an absolute
  path, and a link into ANOTHER skill names that skill (`<skill>/reference/x.md`); a bare
  `reference/...` always means this skill's folder (observation 152).
- **Self-containment:** run `python ClaudeCode/scripts/check_skill_self_contained.py` (and the
  team-gate patterns) against every new or restructured skill, whatever its distribution
  tier. It is the publish gate's cheapest check; run at authoring time it costs seconds,
  run first at release it costs a failed release (observations 19, 152).

## Scripts that walk a share or folder tree at run time

The drive-policy hook sees only the command line, not what the launched program opens. A
shipped script that enumerates a share must apply the policy itself: allowlisted roots or
the policy's folder pattern checked before it opens anything, named folders opened
directly instead of listing the root. Review contributed script packages against a hostile
fixture - a folder it must not read (holding a marker line that must never appear in the
output), a misnamed file, a character outside cp1252 - not against the author's examples.
One such fixture caught three faults a roll-up script's own examples had passed
(observation 131).

## Scripts that fetch remote content

The "only download with the user's OK" rule must be structural in the script:

1. Plan is the default: with no flag the script prints the plan (items, licence field,
   sizes, total) and downloads nothing. `--go` does the work and is refused without
   `--approved-by`, which is recorded in the per-item record.
2. Never overwrite, delete or rename.
3. Write a source and licence record next to every download.
4. Test the safety claims against a local fake API on 127.0.0.1 serving good AND hostile
   archives (no real download): no overwrite, bytes vs API size, checksum, testzip, no
   traversal / absolute / drive / symlink members, disallowed licence refused, plan mode
   creates no folder.
5. Where remote or untrusted text is printed, use `sys.stdout.reconfigure(errors="replace")`
   so a non-cp1252 character cannot crash a cp1252 pipe.

## After any change to this skill's scripts

Run `scripts/selftest_validate.py`. It must report every case behaved; it checks both
directions (clean skills pass, folded descriptions and retired keys fail), so a validator
that passes everything or fails everything cannot score full marks.
