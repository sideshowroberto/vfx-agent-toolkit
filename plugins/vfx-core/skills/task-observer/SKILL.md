---
name: task-observer
description: Watches every tool-using session for skill lessons and writes each one to the observation log the moment it happens - user corrections, rules the agent broke, better workflows, sibling skills that need the same fix, sections nobody uses. Nothing is applied until a review the skill owner approves. Invoke before the FIRST tool call of any session and run its Session Start Protocol (status, scan, review trigger); loading alone activates nothing. Also triggers on "observation log", "any observations logged", "skill review", "task observer", "log that as an observation", "review the backlog".
---

# Task Observer

Adapted from **"One Skill to Rule Them All" by Eoghan Henn / rebelytics.com**
(github.com/rebelytics/one-skill-to-rule-them-all, CC BY 4.0) - see
`ATTRIBUTION.md`. Methodology credit stays with the author; the adaptations
are listed at the end of this file.

Skills improve from friction noticed during real work, not from sitting
down to "improve a skill". This skill makes that noticing a same-turn write
to disk, so a lesson survives the session ending, context compacting, or an
end-of-session wrap-up never running.

## Two roles

- **Contributor** (most team members): your skills arrive through a plugin
  and are read-only to you. You LOG observations; the skill owner reviews
  them and folds accepted lessons into the shared skills. You never edit a
  plugin skill.
- **Owner** (the pipeline lead, or anyone who authors skills in an editable
  skills directory): you also run the review (`references/review.md`),
  stage edits, and install them.

The workflow below is identical for both until "Acting on observations".

## Workspace

Resolved by the helper script, never from the current working directory:

1. `TASK_OBSERVER_WS` environment variable. The token `{user}` expands to
   the current username, so a team can share one value such as
   `<team share>/skill-observations/{user}` and each person gets a private
   folder that the owner's review can sweep.
2. Default: `~/.claude/skill-observations`.

```
<workspace>/
  observation-log/            the log IS this directory: one file per observation
    NNNN-short-slug.md
    archive/                  resolved entries + .id-floor (highest id ever issued)
  cross-cutting-principles.md rules that apply to every skill (checklist when authoring)
  skill-families.md           declared families: members, shared vs member-specific
  skill-updates/<date>/<skill>/   STAGED edits awaiting the owner's approval (owner only)
  last-review-date.txt        a date, or the literal `never`
  checkpoints.log             append-only "no observations" acknowledgements
```

**Helper:** `scripts/observe.sh {status|init|scan|next-id|archive}` next to
this file. The SessionStart hook runs `status` and its first output line
prints the helper's full path - use that path for the other subcommands.
Every field and rule: `references/log-format.md`.

**Unreachable workspace.** If `status` reports UNREACHABLE (a team share
not mounted), skip logging for this session and say so once. Never create
a second log elsewhere - a fork is worse than a gap.

## Session Start Protocol (run it, do not just load this file)

1. **Status.** Read the hook's output, or run `observe.sh status`. If it
   reports MISSING, run `observe.sh init` once and re-run status. It
   reports open/parked counts, last review, staged updates, unresolved
   targets, and missing sibling checks.
2. **Scan.** If there are open observations, run `observe.sh scan` and hold
   the `skill:`, `proposes_skill:` and `title` values in awareness. When you
   later load any skill, apply its OPEN observations to the work even though
   the skill file is unchanged. **An empty scan over a log known to be
   non-empty is a broken command, never "no observations"** - the helper
   exits 1 in that case; stop and fix it.
3. **Review trigger (owner only).** If status says the backlog has never
   been reviewed, or the last review is 7+ days old with open items, offer
   the review in ONE line and proceed with the user's task unless they opt
   in. Never gate their work on it. Contributors skip this step: their
   backlog is reviewed by the owner.
4. **Staged work (owner only).** If `skill-updates/` has dated folders, say
   so in one line - they are edits waiting for approval and installation.

## When to observe

The whole session: execution, post-task feedback, review discussion,
meta-discussion about skills or methodology. **Review-phase feedback is
often the highest-signal input; the mindset does not switch off when the
work is done.** Inactive only for casual chat and quick factual questions
with no tools or deliverables.

## What to watch for

- **New skill:** a reusable multi-step workflow; a methodology the user
  explains that no skill captures ("I always do it this way"); a recurring
  task type.
- **Improve a skill:** the agent violated a documented rule (the skill needs
  enforcement, not louder wording); a correction revealed a missing rule or
  edge case; a better workflow emerged than the skill recommends; a wrong
  assumption (API name, default, port, path); new tooling obsoleted a step.
- **Simplify a skill:** a section never relevant across many sessions; a
  rule from one unvalidated observation; contradictory rules; a rule the
  agent consistently fails to follow (convert to a checklist, a verification
  step, or a script - or remove it). Ask "what can we remove?" as
  deliberately as "what should we add?".
- **Family propagation:** an insight found in one member of a family (the
  same method for different DCCs, the same structure for different models)
  usually applies to the rest. Test: could this sentence survive having the
  tool's or subject's name removed? If yes it belongs to every sibling.

**Do NOT log:** one-off corrections that do not generalise; preferences a
skill already captures; tool bugs unrelated to methodology; anything that
already has a home in a rules file, a memory note, or a project brief -
cite that home instead of duplicating it. The generalisability test when
unsure: would this still make sense on another job, for another task using
the same skill, and is it likely to recur? Mostly no = task context, not an
observation. Full catalogue: `references/signals.md`.

Observations are about SKILLS. A platform trap belongs in the environment
rules; a user preference in memory; a job fact in the job's brief.

## How to log

Write the file **silently, within the same turn or the next**. Never batch
mentally for later; the act of writing is the enforcement.

1. `id=$(observe.sh next-id)` - once per file, at the moment of that file's
   write (never pre-compute a range for a batch). The helper fails loudly on
   a populated log with no ids or an unreachable workspace; treat that as a
   stop signal, not a reason to start from 0001.
2. Validate the target: every name in `skill:` must be a skill that exists
   now (status reports names that do not resolve). If it does not, the
   observation goes under `proposes_skill:` instead.
3. Check siblings against `skill-families.md` and record the verdict in
   `siblings_checked:` - including "checked, instance-specific, no
   propagation". The field is mandatory because a one-entry `skill:` list is
   byte-identical whether siblings were evaluated or never considered.
4. Write `observation-log/NNNN-short-slug.md` (ASCII only):

```markdown
---
id: N
title: Short descriptive title
status: open            # open | actioned | declined | superseded | parked
type: internal          # public | internal  (public = could ship in a public skill pack)
skill: [existing-skill-a, existing-skill-b]   # always a list; first = primary; may be []
proposes_skill: []      # working names of new skills this argues for
siblings_checked: "family: members evaluated - verdict"   # MANDATORY, never blank; `none` only if no family
area: which section or workflow of the skill
date: YYYY-MM-DD
author: username        # who logged it (helps the owner's review across a team)
session_context: what task was being worked on (job names are fine for internal type)
parked_until:           # MANDATORY when parked: the condition that unparks it
resolved:               # YYYY-MM-DD, only when actioned/declined/superseded
resolution:             # what was done, same time as resolved
reference:              # optional path to saved evidence (session log, readback)
---

**Issue:** What happened - specific enough to understand weeks later without
the conversation. Include the read-back or error that proved it.

**Suggested improvement:** Concrete change. Existing skill: name the section
or rule. New skill: scope and key components.

**Principle:** The generalisable takeaway - the most important field. For
`type: public`, no client names, job numbers, studio drives or personal paths.
```

**Flush points - concrete tool events, not judgement calls.** Write any
pending observations (or append one line `YYYY-MM-DD HH:MM no observations`
to `checkpoints.log`) at each of these:
- after every 3rd completed todo item;
- whenever a major deliverable is handed over (file, render, handoff
  package, staged skill, session log);
- before any project-completing command: a commit or push, a release or
  deploy, an end-of-session wrap-up.
A session with no todos has only the last two; apply them deliberately.

**A denied or failed write is not a read-only log.** Retry once, then try a
second tool that reaches the same path. Report "failed N times", never
"cannot be done" - unless status said UNREACHABLE, in which case skipping
was the correct call.

**Type = confidentiality boundary.** `public` means the Principle could
ship in a public skill pack. Default to `internal` when in doubt; promote
later. Under-classifying leaks, over-classifying only costs reach.

## Surfacing

Default: at end of session (and inside any wrap-up ritual), a grouped
summary - improvements grouped by skill, new-skill candidates listed
separately, one sentence each with ids - then state that they are logged
for the next review and STOP. Do not offer "apply now vs later" per item.
Surface earlier only when an observation needs the user's input to be
complete, when a skill is actively producing wrong output, or when
observations cluster on one skill.

Before writing "let's wait for more data" into any recommendation, name
which specific observation would change the decision and when it could
arrive. If you cannot, the evidence is already conclusive: act, or log and
defer - but do not defer by argument.

## Acting on observations

**Contributors: log, do not act.** The one exception is an in-session
correction when a skill is producing wrong output the user should know
about now - say so, log it, and work around it for this task only.

**Owners** act in three contexts: (1) the review (`references/review.md`);
(2) an explicit request ("act on #12", "update skill X"); (3) the same
in-session correction. Otherwise log, do not act.

When acting, **stage, never edit live**: copy the full skill directory to
`skill-updates/<date>/<skill>/`, edit the copy from a fresh read of the
live file, ASCII-scan it, and hand it over for installation. Small additive
fixes (a new rule, a clarification, a factual fix) may be staged outside a
review; restructures and new skills go through the review. Read the full
observation body before resolving, dismissing or citing it - the title is
an index entry, not the content. Set `status`/`resolved`/`resolution` in
the same turn you act; the bookkeeping is the half that gets dropped.

`parked` = decided but blocked on an external precondition (`parked_until:`
mandatory). It leaves the queue, is never re-escalated, and never archives
until genuinely resolved.

## Archival

Before writing a new observation, run `observe.sh archive`: it moves files
whose status is actioned/declined/superseded AND whose `resolved:` date is
before today into `archive/`. Files resolved today stay until tomorrow;
parked files never move. If the workspace is under version control, commit
observations with the session's other changes.

## Quick reference

| Question | Answer |
|---|---|
| When do I observe? | Whole session, including feedback and discussion phases |
| How do I log? | Silently, same turn, one file per observation, id from `observe.sh next-id` |
| Flush points? | 3rd todo done, deliverable handed over, before commit/push/deploy/wrap-up |
| Siblings? | Resolve against `skill-families.md` BEFORE writing; record `siblings_checked:` always |
| Empty scan on a populated log? | Broken command - stop, fix, never "no observations" |
| Workspace UNREACHABLE? | Skip logging this session, say so once, never fork the log |
| public or internal? | Boundary = what could ship publicly; default internal, promote later |
| I am a contributor - can I fix the skill? | No. Log it; the owner's review folds it in |
| Review? | Owner offers it when never / 7+ days with open items; `references/review.md` |
| Not a skill lesson? | Environment rules, memory, or the job brief - cite, don't duplicate |

## Adaptations from upstream (provenance)

- Single-line `description:` (a folded block makes some harnesses drop the
  skill or load it with an empty description).
- Core trimmed from 524 to ~250 lines; the scan/id/archive/init shell moved
  into `scripts/observe.sh` so the agent runs one command per step.
- Workspace resolved from `TASK_OBSERVER_WS` (with a `{user}` token for team
  shares) or a home-directory default; explicit UNREACHABLE fail-soft
  instead of creating a fork.
- Contributor / owner roles for plugin-distributed skill packs.
- `type:` values are `public | internal`; an `author:` field was added.
- Activation = an instruction in the harness config file plus a SessionStart
  hook that injects `observe.sh status` (upstream's tier 3, the only
  enforced tier).
- Scheduled autonomous reviews, migration, handoff-doc mode and
  Cowork-specific material dropped.
