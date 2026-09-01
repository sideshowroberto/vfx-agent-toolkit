# Signals - what to watch for, in full

Adapted from Eoghan Henn's task-observer (CC BY 4.0). Load when unsure
whether something is worth logging, when a session is producing many
candidates and you want to sort them, or during a review when deciding
what a skill should LOSE as well as gain.

## Signals for a NEW skill

A reusable multi-step workflow; a methodology the user explains that no
existing skill captures; a recurring task type with similar structure; a
process with clear inputs, phases, outputs; "I always do it this way"; a
structured approach that emerged naturally during work (a contact-sheet
review layout or a batch-submission script usually starts this way).

When one fires, `proposes_skill:` names the candidate by a working name.
Check existing candidates in the log first and reuse a fitting name -
independently logged proposals for one skill rarely share a name.

## Signals for IMPROVING an existing skill

- the agent violated a documented rule (the skill needs enforcement - a
  checklist line, a read-back step, a script - not louder wording);
- a user correction revealed a missing rule or edge case;
- a better workflow emerged than the skill recommends;
- a technique worked well enough to promote from incidental to recommended;
- an undocumented use case;
- a wrong assumption baked into the skill (API name, default, port, path);
- new tooling obsoletes a step (a CLI replacing a browser bridge, say);
- corrections forming a pattern across sessions;
- a principle that applies to other skills too (cross-cutting candidate);
- a trigger phrase the user used that SHOULD have fired the skill and did
  not (add to the description);
- a naming, framing or structural suggestion, even a conversational one.

## Signals for SIMPLIFYING a skill

A section never relevant across many sessions; a rule from a single
unvalidated observation; workflows the user consistently shortcuts;
sections loaded but never acted on; contradictory rules; "just in case"
complexity that never triggered; a rule the agent consistently fails to
follow (convert to structural enforcement or remove). Treat these as a
review checklist.

## The generalisability test

Before recording a candidate, ask: (1) would this still make sense on
another job? (2) would it apply to another task using the same skill?
(3) does it identify a missing rule, workflow step or principle, rather
than merely fix this task? (4) is there evidence it will recur? Mostly
no = task-specific context, not an observation.

A workaround that only applies to one shot, a preference specific to one
job, a decision forced by a temporary constraint - these look like skill
improvements while the task is happening and are not. Instead of "the
user preferred the 4:3 render for this spot", log "the skill lacks
guidance for choosing render aspect when the model will reframe".
Over-learning from isolated examples is how a skill drifts into
over-specific complexity.

## Do NOT log

- one-off corrections that do not generalise;
- preferences already captured in a skill, a memory note, or the
  environment rules - cite the home instead;
- tool bugs unrelated to methodology (those belong in the environment
  rules or the tool's own troubleshooting section; they are worth an
  observation ONLY if a skill should teach the workaround);
- job facts (those belong in the job's brief);
- observations that would need client-identifying detail to be useful in
  a public skill (log as `type: internal` if an internal skill is the home).

## Where the observation mindset stays on

Active for the entire task session: execution, post-task feedback and
review discussion, meta-discussion about skills or methodology, and
strategy conversations about how work should be done. Review-phase
feedback is often the highest-signal input. Inactive only for casual
conversation and quick factual questions with no tools or deliverables.
