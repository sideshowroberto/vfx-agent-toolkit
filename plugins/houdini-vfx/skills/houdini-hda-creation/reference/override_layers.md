# Override and Variant Layers

**Part of:** houdini-hda-creation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Adding per-shot move / rotate / hide / swap / add overrides on top of a procedurally
solved layout (obs 155).

**Principle:** an edit layer that feeds a solver is not an edit layer, it is a new input.
To change one thing and only that thing, edit after the solve.

1. **Apply overrides AFTER every stage whose output depends on the whole set** (solvers,
   packing, staggering, auto-sizing). A swap fed in before the solve re-sized a shelf and
   moved it and three untouched neighbours by 0.129 m. New items get their own small
   import branch and are placed against base anchors.
2. **Acceptance tests:** every item without an override is bit-identical to base
   (checked independently, for example in hython), and no active override means
   bit-identical to the previous asset version.
3. **Physical-plausibility checks need per-class exemptions decided before the check is
   written.** A "must rest on a support" check applied to every moved item flagged the
   wall-mounted shelf that was being moved on purpose.
