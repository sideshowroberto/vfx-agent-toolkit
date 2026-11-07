# Validation checks (supplement to Workflow 2)

The validator pass is necessary, not sufficient. These are the extra checks.

## Article VIII is a literal heading check

`validate_skill.py` looks for a Version line, "Last Updated", "Dependencies"
and `##` headings matching: Quick Start, (Standard) Workflows, Troubleshooting,
Reference Documentation, Constitutional Compliance, Version History.

A header-style skill that already has the version and dependencies lines and
the workflow and troubleshooting headings typically lacks exactly three:
Quick Start (a short command block), Reference Documentation (a file list) and
Constitutional Compliance (one paragraph). About 25 lines turned a FAIL into
`Overall: PASS (5/6)`. A task whose done-criterion is "the skill validates"
cannot be met by calling the FAIL drift. Read what a check tests before
labelling it broken; an instrument you excuse is an instrument you stop reading.

## Scripts that fetch remote content

Applies to any shipped script that downloads. The rule "only download with the
user's OK" must be structural in the script, not prose around it:

1. Plan is the default: with no flag the script prints the plan (items, licence
   field, sizes, total) and downloads nothing. `--go` does the work and is
   refused without `--approved-by`, which is recorded in the per-item record.
2. Never overwrite, delete or rename.
3. Write a source and licence record next to every download.
4. Test the safety claims against a local fake API on 127.0.0.1 serving good
   AND hostile archives (no real download): no overwrite, bytes vs API size,
   checksum, testzip, no traversal / absolute / drive / symlink members,
   disallowed licence refused, plan mode creates no folder. Run it as part of
   the validator step.
5. Where text from the remote or from untrusted files is printed, use
   `sys.stdout.reconfigure(errors="replace")` so a non-cp1252 character cannot
   crash a cp1252 pipe.

A hostile-fixture test also finds the author's own bugs (a local variable
shadowing a parameter crashed every run of a hardening patch).
