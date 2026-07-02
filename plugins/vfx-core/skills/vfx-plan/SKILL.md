---
name: vfx-plan
description: VFX planning framework — guides selecting the right planning mode (Iterative, Spec-Driven, or Safety-First) for a given task, runs adversarial plan review, and structures the output as an actionable brief. Use when user says "help me plan", "let's plan this out", "vfx plan", "plan this task", or before any complex multi-file or multi-system build.
allowed-tools: Read,Write,Bash,Glob,Grep,Agent
---

# VFX Plan Skill

## Purpose

Guides you to the right planning mode for a VFX task, helps clarify requirements before work begins, and optionally runs an adversarial review pass. Prevents the two most common planning failures: over-planning simple tasks and under-planning complex ones.

## Usage

Invoke this skill when:
- Starting a new tool, script, or pipeline component
- Requirements feel ambiguous ("make it better", "set this up")
- The task touches multiple apps or files
- Getting it wrong means significant rework
- You don't fully understand the solution space yet

**Simple questions with clear answers don't need planning.** "What's the Python call to get selected objects in Blender?" — just ask.

---

## Step 1 — Choose Your Mode

Answer: **how well do I understand what I'm building?**

### Mode 1: Iterative
*"I know what I want, not exactly how"*

Use when requirements will evolve as you build. Discovery is part of the process.

**VFX signals:**
- Building a Houdini terrain generator — node network constraints emerge as you build
- Prototyping a ComfyUI workflow — which parameters matter reveals itself through iteration
- Writing a new Blender addon — UX changes based on what you see working
- Any first-time exploration of an API or tool

**Process:**
1. State the broad goal clearly
2. Build the first working version
3. Observe what's actually needed
4. Iterate toward stability
5. Formalize as a skill when the pattern is proven

Keep planning docs short — guides, not contracts. The plan will change.

---

### Mode 2: Spec-Driven
*"I know exactly what I need to build"*

Use when requirements are locked and you want zero gaps before writing code.

**VFX signals:**
- "Build a Nuke comp: Read → ACES → Grade → DeepMerge → Write, with these exact specs"
- "Export these 12 shots to these exact paths via Sequencer"
- "Batch render a folder of .blend files to EXR with these settings"
- Delivering a tool to a client or another team member

**Process:**
1. Write the spec first — inputs, outputs, constraints, edge cases
2. Claude drafts against the spec
3. Validate output matches spec — the spec is the test
4. Done

The spec becomes your acceptance criteria. *Did we build what we planned?*

**Spec template:**
```
## What it does
[One paragraph — inputs, outputs, purpose]

## Constraints
- [App version, API limitations]
- [File format requirements]
- [Performance requirements]

## Edge cases to handle
- [What happens if X is missing]
- [What happens if Y fails]

## Out of scope
- [Explicitly excluded features]
```

---

### Mode 3: Safety-First
*"Getting this wrong is expensive"*

Use when a mistake is hard to undo or has downstream consequences.

**VFX signals:**
- Batch operations on render sequences (wrong path = deleted frames)
- Scripts that write to shared network storage
- Tools that submit jobs to a render farm
- Any destructive operation on production files

**Process:**
1. Define what "correct" looks like **before writing any code**
2. Write the validation criteria first
3. Build to pass them
4. Run `testing-specialist` agent before shipping

**Required pre-checks:**
- Dry run mode first (list what *would* be affected — don't act)
- Confirm target paths explicitly before any write/delete
- Log all operations with before/after state
- Test on a single item before batch

---

## Step 2 — Clarify Requirements (Optional but Recommended)

Before writing the plan, run `/grill-me` to stress-test your requirements.

Claude will interrogate until every branch of the decision tree is resolved:
- What's the actual input/output?
- Which app version?
- What should happen when it fails?
- What's explicitly out of scope?

The plan you produce after `/grill-me` will be substantially better than the plan you'd produce without it.

---

## Step 3 — Adversarial Review

After writing the plan, switch perspective:

> "Now act as a skeptical technical reviewer. What's wrong with this plan?"

Claude will find:
- Missing error handling
- API version assumptions
- Missing cleanup on failure
- Paths that don't exist
- Race conditions in parallel operations

The plan that survives review is significantly better than one that didn't go through it. You've caught the issues before writing a single line.

**With sub-agents (parallel):**
- Spawn a `search-specialist` to verify the API surface
- Ask the main session to review the plan as a skeptic simultaneously
- Merge findings before starting implementation

---

## Step 4 — Output Format

After planning, produce a brief in this format:

```markdown
## Task
[One sentence — what gets built]

## Mode
[Iterative / Spec-Driven / Safety-First — and why]

## Inputs
[What this takes as input]

## Outputs
[What this produces]

## Implementation steps
1. [First step]
2. [Second step]
...

## Risks flagged
- [Risk 1 and mitigation]
- [Risk 2 and mitigation]

## Out of scope
- [Explicit exclusions]
```

---

## Planning Teaches You

An underrated benefit: planning sessions teach you the API surface as a byproduct.

"I know what I want in Blender. I don't know the Python."

Planning closes that gap. Describe the outcome, Claude explains the path. By the time you're done planning, you understand the territory well enough to direct the build and read what gets produced.

The sessions building this pipeline taught more about Houdini's USD system, Nuke's BlinkScript model, and Unreal's Python API than any documentation would have — because the learning came from solving specific real problems, not reading reference material abstractly.

That's not a side effect of planning. That's the point of it.

---

## Quick Decision Guide

| Situation | Mode |
|-----------|------|
| First time using an API | Iterative |
| Exploring a new tool | Iterative |
| Defined inputs/outputs, locked requirements | Spec-Driven |
| Delivering to another person/team | Spec-Driven |
| Writing to shared/production storage | Safety-First |
| Batch operations on render files | Safety-First |
| Farm submission scripts | Safety-First |
| Anything irreversible | Safety-First |
