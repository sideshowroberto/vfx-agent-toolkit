---
name: gap-check
description: Audit Claude's own knowledge gaps against a settled plan before building. Claude categorizes what it knows confidently vs. guesses at, launches search-specialist agents to fill gaps, and surfaces unknowns for the user to answer. Use after /grill-me when scope is settled, before any planning or build session, or when user says "gap-check", "check your assumptions", "what don't you know about this".
---

You are about to audit your own knowledge against the current plan. The goal is to surface silent assumptions and fill gaps with research BEFORE planning or building begins.

## Step 1 — State the plan

In one sentence, restate the settled scope from the current conversation so the user can confirm it's correct before proceeding.

## Step 2 — Self-audit

Go through every technical component of the plan. For each, honestly categorize your knowledge:

**✓ Confident** — You have seen this documented or used it correctly in verified contexts. State your source if possible.

**~ Uncertain** — You know the general shape but are fuzzy on specifics, version details, or edge cases. State what you're unsure about.

**✗ Guessing** — You are inferring from related knowledge or pattern-matching. You could be wrong. State the assumption explicitly.

Be ruthless. The most common failure mode is treating ~ and ✗ items as ✓. If you haven't verified it recently or it's version-sensitive, it's not ✓.

## Step 3 — Classify gaps by who can fill them

After the audit, sort the ~ and ✗ items into three buckets:

**Search-specialist can answer** — Public API docs, version changelogs, GitHub issues, library behavior. Launch a search-specialist agent for each cluster of related questions. Run them in parallel where possible.

**User must answer** — Studio-specific preferences, internal pipeline details, decisions only the user can make. Ask these as a short list — don't guess.

**Testable locally** — Things that can be verified with a quick command or code snippet. Flag these for the user to test before the build session.

## Step 4 — Launch research

For any items in the "search-specialist can answer" bucket, immediately dispatch search-specialist agents in parallel. Be specific in the agent prompts — include the exact version, platform, and context so results are actionable.

## Step 5 — Deliver validated summary

Once research returns, deliver a clean summary:

```
VALIDATED KNOWLEDGE
✓ [item] — [source or confidence reason]
✓ [item] — [source or confidence reason]

GAPS FILLED BY RESEARCH
✓ [item] — [what research found]
~ [item] — [what research found, still some uncertainty]

GAPS REQUIRING USER INPUT
? [question]
? [question]

GAPS TO TEST LOCALLY
⚡ [what to test] — [one-liner or command]

STILL UNKNOWN
✗ [item] — [why it couldn't be resolved and what the risk is if assumed]
```

Do not proceed to planning until the user has reviewed this summary and either filled the remaining gaps or explicitly accepted the risk of the unknowns.
