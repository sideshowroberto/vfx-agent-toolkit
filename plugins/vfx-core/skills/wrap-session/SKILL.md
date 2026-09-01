---
name: wrap-session
description: End-of-session wrap-up ritual before clearing context. Reviews the session for durable facts to save to memory, updates skills with newly discovered gotchas, writes a session log for substantial project work, cleans up temp files, and writes a handoff plan so the next session can resume without re-discovery. Use when the user is about to /clear, when context is running low, or at the natural end of a work session. Triggers on "/wrap-session", "wrap up this session", "we're running low on context", "prepare to clear context", "before we clear".
---

# Wrap Session

Execute this checklist decisively, in order. Do the work - don't ask permission for each step. Only pause to ask if something is genuinely ambiguous (e.g., unsure whether a temp script is still needed).

## 1. Memory

Review the full session for durable facts not yet saved to memory:

- **Project facts** - fps, resolution, colorspace, drive layout, folder conventions, naming schemes, tool versions, decisions made
- **Feedback and corrections** - anything the user corrected you on, preferences they stated, approaches they rejected
- **Gotchas discovered** - API quirks, version incompatibilities, workarounds that took effort to find

Write or update the relevant memory files and keep the memory index current.

**Explicit check:** Does the active job have its loader skill (`project-<job>`) and is the canonical brief `...\sandbox\AGENT\PROJECT.md` current with what happened this session (decisions ledger, shot ledger, open obligations, hard rules)? If not, update them now. Job facts live THERE, not in a `project_<job>.md` memory file - memory keeps only a one-line pointer. If the JOB itself is finishing, run `/project-wrap` (`project-lifecycle` skill) before this wrap.

## 2. Skills

**First, flush task-observer:** write any pending observations to the log
(`observe.sh next-id`, one file each), run `observe.sh status`, and surface
the grouped summary (ids + titles, per skill) FROM THE LOG - not from memory.
They stay logged for the next review; do not apply them here unless the
review is due and Rob opts in. If nothing was logged all session, say why.

Did this session discover anything that belongs in an existing skill?

- Gotchas or workarounds relevant to a skill's domain
- API or version changes that make a skill's guidance stale
- Trigger phrases the user said that *should* have fired a skill but didn't - add them to that skill's description

If the edit is small, make it now. If it needs real rework, list the needed changes clearly so the user can act on them later.

## 3. Session Log

If the session did substantial work (not just Q&A or trivial edits), write a session log. **These records are DATA, not exhaust** - the fine-tune pilot mined its best training trajectories from session logs, and future analysis depends on one crawlable corpus. Capture generously: failures and dead ends are as valuable as wins.

**Canonical home (2026-08-20, Rob's direction - one place, always):**

```
Documentation/sessions/YYYY-MM-DD_<topic>_session.md
```

with the frontmatter convention in `Documentation/sessions/INDEX.md` (date, topic, apps, outcome). Multi-session efforts may use a subfolder there.

**Exception (hard rule unchanged):** client-job sessions go in the job sandbox agent folder as before - but add a one-line pointer to the INDEX.md pointer log so the corpus knows they exist.

Cover: what was attempted, what worked, what failed and why, key decisions.

### Harvest checklist (fine-tune corpus - capture the SCARCE shapes)

The 2026-08 pilot's verdict: the corpus did not need more trajectories, it
needed specific shapes it almost never had. Every session log includes a
`## Harvest` section capturing whichever of these occurred - verbatim, not
paraphrased:

1. **Contradiction moments** (the #1 scarce shape - 2 of 57 records had
   one): a readback/measurement CONTRADICTED the plan or an assumption.
   Record the triplet: what was believed -> the actual read-back value ->
   the re-derivation that followed. Instrument-was-wrong moments double here.
2. **Verify-act-readback arcs**: the real tool name AS INVOKED (server-
   prefixed - 19 corpus calls used a tool that did not exist), real args,
   real returned values. Paraphrase is corpus poison.
3. **Fact/path provenance**: for load-bearing paths and values - given by
   operator, returned by a tool, or derived? Flag any invention that got
   corrected (the corpus had 8 invented paths per grounded one).
4. **Blocked/denied calls + recovery**: exact denial message -> what the
   agent did next (rephrase within policy vs loop vs abandon).
5. **Stop-and-ask moments**: the question as asked AND the operator's
   actual answer - decision data is unminable if only the outcome is logged.
6. **Dead ends with their disproof**: what was tried, what measurement
   killed it. Negatives teach what confident completion never does.
7. **Operator corrections**: what the user corrected, before -> after.

Rate the log's `harvest-yield: high|medium|low` in its frontmatter (the
lane-A inventory had to guess this per file after the fact - pre-rating at
write time makes the future inventory step free). Hygiene (client names,
path genericisation) happens at HARVEST time per the corpus pipeline, not
at write time - log truthfully here. If live captures exist for the session
(session-capture skill / OpenCode plugin), name the capture dir in the log.

### Retroactive runs (resumed old sessions): HARVEST-ONLY

Running this skill in a RESUMED old session: do ONLY step 3 (the log +
Harvest section) and SKIP steps 1, 2, 4 and 5 entirely - an old session's
worldview predates later corrections, so its memory/skill edits would
overwrite newer truth, and its cleanup targets are long gone. Two more
guards: (a) if the session was compacted, verbatim tool calls are GONE from
context - mark the log `harvest-yield: low (compacted - paraphrase only)`
and do not reconstruct calls from memory; (b) prefer the transcript-miner
backfill (see Documentation/sessions/INDEX.md) over manual resumes - the
raw JSONL transcripts in ~/.claude/projects/ hold the verbatim record that
a resumed session cannot reproduce.

## 4. Tmp Cleanup

Review `tmp/` and any scratch files created this session:

- **Delete** dead diagnostic scripts, intermediate payloads, and outputs no longer needed
- **Promote** anything reusable to its proper home per workspace rules (e.g., `[App]/scripts/` or the project's `scripts/` directory)
- **Consolidate** iterative diagnostic scripts (`probe.py`, `probe2.py`, `probe3.py`) into one parameterized script if worth keeping

## 5. Handoff Plan

Write a concise next-session plan file to the canonical home: `Documentation/sessions/YYYY-MM-DD_<topic>_handoff.md` (job work: the job sandbox, with an INDEX.md pointer). Never tmp/ - handoffs are part of the session corpus. Cover:

- **Completed** - what got done this session
- **In flight** - what's partially done and its current state
- **Next steps** - exact, actionable steps in order (not vague goals)
- **Context needed** - the specific files/paths the next session should read first

Tell the user exactly where the handoff file is.

## 6. Confirm

Summarize in a short table or list: what was saved, and where - memory updates, skill edits, session log, promoted/deleted files, handoff plan location.

Then confirm explicitly: **"Safe to /clear."** (Or state what's still unresolved if anything blocked a step.)
