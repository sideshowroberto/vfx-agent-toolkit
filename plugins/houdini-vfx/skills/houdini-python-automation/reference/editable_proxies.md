# Procedural Output to Editable Objects

**Part of:** houdini-python-automation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

**Goal:** let people click and move individual items of a procedurally baked layout
(one packed prim per item) without breaking the procedural source and without sliders.

## Recipe

1. One /obj geo object per layout item. Its geometry is that item from the baked
   output, frozen with a timeshift and translated so the placement point sits at the
   object origin; the object transform puts it back.
2. Parent each object to a null baked on the container's transform, or to its support
   item from the layout's own relations.
3. Inside the container node: an object_merge of the item objects with "Into Specified
   Object" set to the null (gives back container-local space), then pack (pivot
   origin), then attribute copies of the outer prim / point / detail attributes, then
   a Switch (baked | edited) driven by a toggle on the null.

**Cycle rule:** items read from UPSTREAM of the switch; the slot transform is baked,
never read back from the output.

## Proof (all three, every time)

Snapshot identity with the toggle off AND on, a deliberate move visible downstream, and a
restore that returns to identity.

## Pitfalls

- An unfrozen source re-imports per frame (seconds per frame step).
- The container object stays selectable and steals viewport clicks; turn its Selectable
  flag off.
- A downstream check through whole-container bounds, or a same-named USD prototype, is
  blind to item moves. A container holding ONE packed prim per item also hides an item
  moving inside it from a point-position sum: read the item inside
  `getEmbeddedGeometry()`.
- A shot's first frame may not contain the item at all; image-check on a frame where the
  item is in shot.

## Variant twins

When an item has an alternate placement (a duplicate object with a suffix, one hidden):
an Object Merge ignores display flags and a wildcard does not recook when a new matching
object appears, so the viewport kept the old result while a fresh load carried BOTH
twins.

**Fix:** never feed edit objects through a wildcard. Put a toggle on the slot null and a
Python expression on the merge's object path that returns an explicit space-separated
list (twin when the toggle is on, original when off), and have the twins' display
parms follow the toggle. For per-shot use of the toggle see `takes.md`.
