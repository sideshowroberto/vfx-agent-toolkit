# VEX Wrangle Traps

Part of the houdini-vex-programming skill; each trap was measured in a live session.

## Contents
1. set*attrib() writes are deferred
2. point() / prim() / detail() inside a ternary
3. An empty group pattern means ALL elements (and find() not-found value)
4. A wrangle made from Python does not bind bare globals
5. nearpoints() includes the point itself
6. chs() is stale when spare parms are added after the wrangle cooked

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

> **NOT REPRODUCED 2026-11-08:** the snippet below returned the correct tags in hython
> H20.5.613 and H21.0.596. Kept for history only; not a rule in SKILL.md. Delete if a
> future build does not show it either.

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

**Fix:** guard parameter-driven patterns with `if (pat != "")`.

**Related - find() not-found value:** in H21 `find()` on an array returns `-(len+1)` for a
missing value (-2 for a one-element array; re-checked in hython 2026-11-08), not -1. Test
`find(...) >= 0` (or `< 0`), never `== -1`.

**First diagnostic when a wrangle's logic "does nothing":** write a debug attribute for
every intermediate value and read them back.

---

## Trap 4: a wrangle made from Python does not bind bare globals

**Rule:** an `attribwrangle` created with `hou` in hython fails at cook with "Reference
to undefined variable: P" for `P.y = 1;`. Write `@P.y`. The error shows only in
`node.errors()` and in a `hou.OperationFailed` from `cook(force=True)`, so a script that
never force-cooks each node saves a broken hip.

---

## Trap 5: nearpoints() includes the point itself

**Rule:** `nearpoints(0, @P, r)` searches the same geometry the point lives on, so the
current point is always in the result (distance 0). A neighbour count is one too high and a
neighbour average is pulled towards the point. The skill's old Workflow 2.3 snippet had
exactly this bug.

**Fix:**

```vex
int near[] = nearpoints(0, @P, chf("radius"));
int count = 0;
vector sum = {0, 0, 0};
foreach (int pt; near) {
    if (pt == @ptnum) continue;          // skip self
    sum += point(0, "P", pt);
    count++;
}
i@neighbor_count = count;
if (count > 0) v@neighbor_avg = sum / count;
```

**Read-back that proves it:** an isolated point must report 0 neighbours, not 1.

---

## Trap 6: chs() is stale when spare parms are added after the wrangle cooked

**Rule:** building a wrangle (e.g. Houdini MCP `build_network`) cooks it immediately. Spare
parms added afterwards (`create_spare_parameters`) do not trigger a recook of the code that
reads them, so `chs()`/`chf()` return empty or default values and the first result is wrong.
In the 2026-11-08 eval this hit 9 of 9 runs (121 points kept instead of 81); each lost 8-15
turns, and 5 of 9 then reported an invented cause ("removepoint needs and_prims",
"`protected` is a reserved name").

**Fix:** create the spare parms before setting the snippet, or re-set the snippet / force a
cook after adding them. Then re-read the counts before diagnosing anything.

**Tell:** a result that matches "parameter empty or zero" exactly, which changes when the
snippet is re-set with no edit.

(Observation 442.)
