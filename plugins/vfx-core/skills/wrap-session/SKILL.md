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

**Explicit check:** Does the active project have a project-facts memory file? Is it current with what happened this session? If not, create or update it now.

## 2. Skills

Did this session discover anything that belongs in an existing skill?

- Gotchas or workarounds relevant to a skill's domain
- API or version changes that make a skill's guidance stale
- Trigger phrases the user said that *should* have fired a skill but didn't - add them to that skill's description

If the edit is small, make it now. If it needs real rework, list the needed changes clearly so the user can act on them later.

## 3. Session Log

If the session did substantial project work (not just Q&A or trivial edits), write a session log to the app-specific location per workspace rules:

```
[App]/[project]/development/Session_YYYY-MM-DD_topic.md
```

Cover: what was attempted, what worked, what failed and why, key decisions.

## 4. Tmp Cleanup

Review `tmp/` and any scratch files created this session:

- **Delete** dead diagnostic scripts, intermediate payloads, and outputs no longer needed
- **Promote** anything reusable to its proper home per workspace rules (e.g., `[App]/scripts/` or the project's `scripts/` directory)
- **Consolidate** iterative diagnostic scripts (`probe.py`, `probe2.py`, `probe3.py`) into one parameterized script if worth keeping

## 5. Handoff Plan

Write a concise next-session plan file (e.g., `tmp/handoff_YYYY-MM-DD.md` or the project's development folder if it should persist). Cover:

- **Completed** - what got done this session
- **In flight** - what's partially done and its current state
- **Next steps** - exact, actionable steps in order (not vague goals)
- **Context needed** - the specific files/paths the next session should read first

Tell the user exactly where the handoff file is.

## 6. Confirm

Summarize in a short table or list: what was saved, and where - memory updates, skill edits, session log, promoted/deleted files, handoff plan location.

Then confirm explicitly: **"Safe to /clear."** (Or state what's still unresolved if anything blocked a step.)
