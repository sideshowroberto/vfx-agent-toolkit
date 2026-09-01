# The review - cross-check the backlog, stage the fixes, hand them over

Adapted from Eoghan Henn's task-observer weekly review (CC BY 4.0).
**Owner role only.** Load when the Session Start Protocol offers a review
and the user opts in, or when the user asks for one ("review the
observations", "skill review"). Contributors never run this: their
observations are reviewed by the skill owner.

Reviews are INTERACTIVE. If a scheduled autonomous mode is ever added it
must run where it can reach every workspace it reviews, and it must
escalate rather than apply anything that creates a skill, removes content,
self-flags uncertainty, or conflicts with another entry.

## Sweeping a team

When contributors log to per-user folders under one root (the `{user}`
token in `TASK_OBSERVER_WS`), the review's queue is the union of every
`<root>/<user>/observation-log/` - run `observe.sh scan` once per folder
by setting `TASK_OBSERVER_WS` for each call, or list them directly. Each
user's `last-review-date.txt` is updated when their folder has been
swept, so the per-user session-start prompt goes quiet. Observations stay
in the contributor's folder; only their `status`/`resolved`/`resolution`
fields change.

## Approval policy

Present observations grouped by skill (id, author, title, one sentence),
flag judgement calls as "needs your input", and wait for blanket or
selective approval before staging anything. **Classify before you ask:**
any disposition offered (fold in, decline, route to skill X) must come from
the entries' BODIES, never from titles and `skill:` fields alone. Read,
bucket, present counts, then ask - never ask first. A dismissed prompt is
not approval and not a request to skip asking: stop and ask in plain text.

## Steps

**Step 1 - Load the queue.** `observe.sh archive` first (clears
yesterday's resolved files), then `observe.sh scan`. The work queue is
every file with `status: open` or no status field. For each `parked`
entry, check its `parked_until:` condition; if met, set it back to `open`
and queue it. **No open items and no outstanding principles: write
today's date to `last-review-date.txt` and stop here.**

**Step 2 - Inventory targets.** Three classes:
- *Owned*: skills in an editable skills directory - staged here.
- *Plugin-installed / read-only*: skills that arrive via a plugin or the
  harness. An observation aimed at one of these is routed to an owned
  wrapper skill, to the environment rules, or to the harness config file -
  never left targeting a file you do not control.
- *Gone*: a `skill:` value that no longer resolves. A corpus filed against
  one dead skill routinely splits across several live ones - read the
  bodies and re-route before offering "decline".

**Step 3 - Cross-check and cluster.** Read every open body. Group by
skill; merge duplicates (`superseded`, with `resolution` naming the
survivor); consolidate new-skill proposals under one working name each;
check family coverage - a multi-skill observation lists every sibling it
applies to, or the body says why not. Confidentiality: for anything with
`type: public`, check the Principle text against whatever publish gate
the skill pack uses - client names, job numbers, studio drives and
personal paths all disqualify it from public.

**Step 4 - Drift audit.** For each family in `skill-families.md` with
coherence model `synced-duplicates`, grep the shared rules across members
and list gaps. For `shared-core` families, verify the pointers still
resolve. This is the only step that catches drift predating the log or
introduced by a skill authored outside it. Cross-cutting principles: check
each `Propagation: immediate` principle is present in every skill it
applies to.

**Step 5 - Stage, never edit live.** For each skill receiving changes:
copy the FULL live directory to `skill-updates/<YYYY-MM-DD>/<skill>/`,
edit the copy from a fresh read, keep the description single-line, ASCII-
scan every touched file, and confirm the change is actually present in
the staged copy (grep for it - a staged directory identical to live is a
silent no-op). New skills are NOT created in a review: note the candidate
and its consolidated scope for the owner to action through the skill
authoring workflow.

**Step 6 - Present and wait.** Summary format below. Wait for approval
before installing anything. On approval: copy the staged directory over
the live skill, bump the plugin version if the skill ships in a plugin
(installs pick up the version, not the content), and note that the plugin
needs re-publishing before contributors see it.

**Step 7 - Bookkeeping in the same turn.** For each actioned observation
set `status`, `resolved` (today), `resolution`. Declined ones get
`status: declined` and a one-line reason. Write today's date to
`last-review-date.txt` ONLY after the review actually ran. Commit the
workspace if it is under version control.

## Summary format

```
## Skill review - YYYY-MM-DD

Updated skills (N observations, N principles applied):
**skill-name** - one-sentence change; observations #N (author), #N (author)

### Actioned
ids and titles

### Family coherence
each multi-skill observation: applied to all listed skills, or partial with the outstanding skill named
drift audit: gaps per family and how each was resolved
N observations logged without a sibling check

### Parked
#id - title - unparks when: condition

### Declined / needs input
items with reasons
```

## Constraints

- Do not modify observation files beyond `status`, `parked_until`,
  `resolved`, `resolution`.
- Do not create new skills in a review.
- Unsure how to integrate an observation: skip it and say so.
- Internal observations get the same rigour as public ones.
- Never edit a live skill during a review; staging only.
