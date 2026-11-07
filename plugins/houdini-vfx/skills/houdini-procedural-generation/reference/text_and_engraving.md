# Text, Engraving and Boolean Slicing

**Part of:** houdini-procedural-generation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

---

## 1. Judge a font by measuring the solids it builds (obs 280)

Whether a font "builds clean" was once settled by eye after a failed carve. Before
carving, inlaying or extruding text with an untested font, run a headless test per word
with the exact production verb chain (font with hole=1, then divide convex, then
polyextrude, then a self-union Boolean).

- **Area ratio** = union front area / signed Font SOP area (overlapping outlines count
  twice).
- **Cut ratio** = volume removed from a slab / letter volume inside it. The letters must
  break the slab face, or the test measures a cavity.
- **Open edges** after the union.
- Run one known-good and one known-bad font as controls in the same run. A known-good
  font measured 1.000 / 1.000 / 0 open edges; a known-bad one measured area 0.954 to
  1.038 and cut up to 2.00. A font that looks the most "carved" left 78 open edges and a
  2.00 cut ratio on every word with a B.
- An unknown font name errors in the Font SOP verb ("Unable to read file"), but compare
  text widths across fonts anyway to catch a silent fallback.

## 2. Place engraving and decals on the REAL surface (obs 282)

**Rule:** offset from the surface as modelled, never from an analytic stand-in (cylinder,
plane, sphere). Letters bent onto the nominal cylinder of a wall built from flat vertical
facets sat up to 2.6 cm off the real face, so 1 cm cutters missed it over long stretches.
The Boolean reported no error, and an area comparison was inconclusive because the wall
polygons were large and non-planar.

**Fix:** ray-cast or `xyzdist` each vertex onto the target faces (target faces only),
then apply the depth / proud offset along the normal.

**Verify from the viewer side:** from a short distance in front of every piece, shoot at
the wall and check the first hit. The first hit must be the intended material at the
expected depth. Run a control region that must read the opposite way. Before the fix 848
of 3073 pieces hit uncut stone first (the control band read 40/40 stone); after, 3059 of
3073 hit the inlay first, the rest being zero-area slivers. Do not judge a cut by area
totals on non-planar input.

## 3. Boolean then Divide / Clip / bend: keep cut faces triangulated (obs 204)

A Boolean with Detriangulate = All Polygons can emit ONE n-gon with two bridged holes
(63 vertices, 4 repeated points). A following brick Divide then produced a slice spanning
the opening and the niche rendered as a solid wall. With one hole it sliced correctly, and
with a flat wall the Divide never ran, so the bug showed only for one parameter
combination.

**Fix:** use Detriangulate = Only Unchanged Polygons (or None) when the next node slices
or bends; cut faces stay triangles and untouched faces keep their quads. Or verify with a
ray / point-in-face test through every hole.

**Test the parameter combination that switches the slicer on** (for example a bend
radius above zero), not only the defaults, whenever a feature adds geometry to an
existing Boolean (a second cutter, a hole). A ray traced node by node locates the first
node whose output covers the opening.
