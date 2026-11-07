# Measure Geometry Without Nodes

**Part of:** houdini-python-automation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

## Clearance is point-to-SURFACE, not point-to-point

A clearance check between items using point-to-point distance (sampled point clouds)
returned nothing for a plaque standing on a bevelled-box plinth: low-poly items have
points only at their corners, so no point was near the contact. Every low-poly item
(plinths, shelves, brackets) was invisible to it.

**Method:** run `xyzdist` through a compiled verb, in memory, both ways (A to B and B
to A).

- `nodeVerb("attribwrangle")` returns None: the Attribute Wrangle is an HDA, not a
  compiled verb. List verbs with `nodeVerbs()`.
- The compiled core is the `attribvop` verb: `vexsrc` 3, `vexsnippet` set, `bindclass`
  2. Snippet `f@surf_d = xyzdist(1, @P);`, then `verb.execute(out, [items_a, items_b])`.

**Prove it on one known contact before believing a zero or an empty result.** Controls
matched known answers (a plaque on a plinth 0.31 mm, a ball on a shelf 0.0 mm, a gap
measured 61.59 mm vs 61.6 mm by another method).
