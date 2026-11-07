# VEX Wrangle Traps

**Part of:** houdini-vex-programming skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-09

---

## Trap 1: set*attrib() writes are deferred - reads in the same wrangle see the INPUT

**Rule:** `setprimattrib()`, `setpointattrib()` and `setdetailattrib()` write into the
output geometry, and the writes are applied after the wrangle finishes. `prim()`,
`point()` and `detail()` called in the same wrangle read the INPUT geometry. A read after
a write therefore returns the value the attribute had on the way in, never the value you
just set.

**Why it bites:** nothing errors. The code reads correctly and silently does less. A
Detail-mode wrangle set `support_depth` on fixtures in a first loop, then a second loop in
the same wrangle read it back with `prim()` to stack tiers on top of each other. Every
read returned the input value, so the tiers never accumulated and the fixtures kept their
first-pass depths.

**Fix:** keep the working state in local arrays for the whole wrangle and treat the
write as the LAST step. If the passes are genuinely separate, split them into chained
wrangles (the second one then reads the first one's output as its input).

```vex
// Detail wrangle: multi-pass logic with a single write at the end
float depth[];  resize(depth, nprimitives(0));
for (int f = 0; f < len(depth); f++) depth[f] = prim(0, "depth", f);      // seed once from the input
/* pass 1 and pass 2 read and update ONLY depth[] */
for (int f = 0; f < len(depth); f++) setprimattrib(0, "depth", f, depth[f], "set");  // write once
```

**Read-back that proves it:** after the cook, read the final values from the Geometry
Spreadsheet (or `geo.prims()[n].attribValue("depth")` in Python) and compare two or three
of them with values you worked out by hand for the second pass. Values equal to the
first-pass results (or to the input) are the signature of this trap.

**Tell:** a second loop that "does nothing", or a multi-pass result identical to the
single-pass result, with a clean cook and no warnings.

---

## Trap 2: point() / prim() / detail() inside a ?: ternary lose their string type

**Rule:** these lookups pick their return type from context, and inside a ternary the
context is ambiguous. `s@tag = src >= 0 ? point(1, "tag", src) : "";` compiles without a
warning and returns "" for every element.

**Fix:** put the result in a typed local first, then assign.

```vex
string t = "";
if (src >= 0) t = point(1, "tag", src);
s@tag = t;
```

**Read-back that proves it:** count elements per value (a histogram), not one sample.
An empty or zero value everywhere, with no error, is the signature. If a lookup returns
one value everywhere, also check that the id attribute it indexes with actually reached
the geometry (for example, carried through Copy to Points).

---

## Trap 3: an EMPTY group pattern means ALL elements

**Rule:** `expandpointgroup(0, "")` (and `expandprimgroup`, and SOP group fields) returns
every element when the pattern is empty. A parameter-driven list left blank therefore
selects everything and silently overrides lists applied before it.

**Fix:** guard parameter-driven patterns with `if (pat != "")`. `find()` on an int array
returned -2 (not -1) for "not found" when measured, so test `find(...) >= 0`, never `== -1`.

**First diagnostic when a wrangle's logic "does nothing":** write a debug attribute for
every intermediate value and read them back.

---

## Trap 4: a wrangle made from Python does not bind bare globals

**Rule:** an `attribwrangle` created with `hou` in hython fails at cook with "Reference
to undefined variable: P" for `P.y = 1;`. Write `@P.y`. The error shows only in
`node.errors()` and in a `hou.OperationFailed` from `cook(force=True)`, so a script that
never force-cooks each node saves a broken hip.
