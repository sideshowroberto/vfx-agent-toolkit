# The observation log - layout, fields, families, archival

Adapted from Eoghan Henn's task-observer (CC BY 4.0). Load when setting
up the workspace, when an id or frontmatter looks wrong, when declaring a
family, or before changing how anything reads the log.

## Layout

```
<workspace>/                 resolved by scripts/observe.sh (TASK_OBSERVER_WS, else ~/.claude/skill-observations)
  observation-log/           one file per observation - the directory listing is the index
    0001-short-slug.md
    archive/
      .id-floor              highest id ever issued; the counter never drops below it
      0001-short-slug.md     resolved entries, moved here after the grace period
  cross-cutting-principles.md
  skill-families.md
  skill-updates/<YYYY-MM-DD>/<skill-name>/   staged full skill directories (owner only)
  last-review-date.txt       `never` until a review has actually run
  checkpoints.log            append-only "no observations" acknowledgements
```

`observe.sh init` creates this layout (with template principles and
families files) and verifies every file landed - a network share can
accept a mkdir and silently drop the files that follow.

No central index exists to keep in sync: the frontmatter is the metadata,
and `observe.sh scan` reads only the header block of each file so the
scan stays cheap at hundreds of entries.

## Frontmatter fields

| Field | Meaning |
|---|---|
| `id` | Integer; matches the `NNNN-` filename prefix. Never reused. |
| `title` | Short descriptive title. |
| `status` | `open`, `actioned`, `declined`, `superseded` (a later observation found this one's fix does not work; `resolution` names it), `parked`. A MISSING status is read as `open`, never as nonexistent. |
| `type` | `public` (could ship in a public skill pack) or `internal`. Default internal. |
| `skill` | Always a list, even with one entry; first entry is primary; may be `[]`. Every name must exist at write time. |
| `proposes_skill` | Working names of new skills this argues for; may be `[]`. |
| `siblings_checked` | MANDATORY, never blank. Family name + members evaluated + verdict, e.g. `"gen-batch: nb2-batch, veo-batch - shared, both added"` or `"blender: checked - instance-specific, no propagation"`. Literal `none` only when the target belongs to no family. |
| `area` | Which section or workflow of the skill. |
| `date` | YYYY-MM-DD written. |
| `author` | Username of the person whose session logged it. |
| `session_context` | What task was being worked on. Job names are fine for `internal`. |
| `parked_until` | MANDATORY when parked: one line naming the condition that unparks it, phrased so a later session can answer whether it has happened. Empty otherwise. |
| `resolved` | YYYY-MM-DD; set only when actioned/declined/superseded. |
| `resolution` | What was done; set at the same time as `resolved`. |
| `reference` | Optional path to saved evidence (a session log, a readback dump, a render). |

Body: **Issue** / **Suggested improvement** / **Principle**. The Principle
is the field a review acts on; for `type: public` it must be fully
generalised - no client names, job numbers, studio drives, personal paths.

## Assigning an id

`observe.sh next-id` prints the zero-padded id and updates
`archive/.id-floor`. The id is max(highest prefix in observation-log,
highest in archive, .id-floor) + 1. The floor file exists so the counter
cannot restart from 1 when every active file has been archived.

Run it once per file at that file's write time. A batch of N observations
is N separate id races; pre-computing a range and hardcoding sequential
numbers collapses them into one stale read. Ids are unique per workspace,
not across a team: two contributors both have a #0007, which is why the
`author` field exists and why a review cites `author/#id`.

**An empty probe over a populated log is a stop signal, not a create.** If
the directory you wrote to earlier has vanished, or `next-id` reports
"ID COMMAND BROKEN", halt and re-probe the layout. Never let a write
silently recreate a missing target.

## Skill families and the sibling check

Where several skills implement one idea, the shared part drifts by
default: each member is maintained only in the sessions that use it and
nobody looks at the set. Measured upstream in real libraries: a rule that
applied to every member of a five-skill family was present in one of five.
In a VFX skill pack the same shape appears wherever one method is
implemented per DCC, or one structure per generation model.

`skill-families.md` holds one entry per family:

```markdown
## family-name
**Members:** skill-a, skill-b, skill-c
**Coherence model:** synced-duplicates | shared-core
**Shared:** the material every member should carry
**Member-specific:** what legitimately differs, and why
```

| Coherence model | Meaning | Fixing drift means |
|---|---|---|
| `synced-duplicates` | each member is self-contained and shared sections are kept in sync | edit every member |
| `shared-core` | one skill or file holds the common material; the others point at it | edit the core once, check the pointers |

Logging-time check: resolve the target against the registry. If it is in
a family, evaluate each sibling and either add it to `skill:` or state in
the body why it does not apply. If the target is in NO declared family,
still scan the installed skill names for a shared prefix or subject,
evaluate against that set, and propose the registry entry in the
observation.

Two cheap tests decide the verdict:
- Could this sentence survive having the tool's, client's or subject's
  name removed? If yes it belongs to every sibling.
- Does the rule declare its own generality ("this applies to any batch
  script, not just X")? Treat that phrasing as an automatic multi-skill
  flag.

Record the verdict in `siblings_checked:` even when it is "no
propagation". Recording does not make the judgement better; it makes its
ABSENCE visible, which is the only property that lets `observe.sh status`
report "N logged without a sibling check".

## Editing an existing observation

Re-read that one file first (a parallel review may have resolved it).
Edit only the frontmatter fields you are changing (`status`,
`parked_until`, `resolved`, `resolution`). Never batch-rewrite the
directory.

## Archival

`observe.sh archive` moves files with status actioned/declined/superseded
AND a `resolved:` date strictly before today into `archive/`. Files
resolved today stay until tomorrow no matter which session resolved them -
the grace period lives in the file, not in session memory. A resolved
file with no `resolved:` date is reported, not moved: set today's date and
it archives tomorrow. `parked` is exempt by design: it is decided, not
resolved, and the review must keep re-checking its `parked_until:`.

## Version control and shares

If the workspace is inside a git repository, commit observations with the
session's other changes; before any `git clean`, stash, worktree teardown
or checkout that touches it, confirm the log has no untracked files - an
untracked observation is the only kind a git operation can destroy.

If the workspace is on a network share, the helper's UNREACHABLE check is
the safety net: an unmounted share must produce a skipped session, never
a fresh log in the home directory. Do not "fix" an unreachable share by
pointing `TASK_OBSERVER_WS` somewhere local for the day.

## Why the flush points are writes, not questions

"Ask yourself whether anything is pending" fails under load exactly when
it matters. A write to disk - an observation file, or a one-line
`no observations` marker in `checkpoints.log` - is objectively visible in
the tool record, so a review can see that a session ran the check. Bind
flush points to events that are also visible in the tool record (a todo
completion, a file handed over, a commit) rather than to the agent
noticing that a moment qualifies.
