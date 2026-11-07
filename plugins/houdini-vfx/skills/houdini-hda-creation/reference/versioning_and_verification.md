# HDA Versioning and Delivery Verification

**Part of:** houdini-hda-creation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Six traps that each produced a confident, wrong "verified" result. Every one is
cheap to guard against and none of them raises an error.

---

## 1. An unversioned createNode() resolves to the NEWEST installed version

**Rule:** after you install `my_asset::2.0` next to the unversioned `my_asset`, a call
to `createNode("my_asset")` builds the newest version, not the old one. Any node that
must be a SPECIFIC version (a regression reference, an old-vs-new comparison, a rebuild
of an older parent asset) is created with `exact_type_name=True`, and its
`type().name()` is asserted.

**Why:** the unversioned name is a moving reference. A "v1 reference" built with the
unversioned name was really a second v2.0, so the comparison against the new version
reported identical part counts and identical frames. It was caught only because the
counts could not be true: the old version has geometry the new one removed.

```python
old = parent.createNode("my_asset",      "ref_old", exact_type_name=True)
new = parent.createNode("my_asset::2.0", "ref_new", exact_type_name=True)
assert old.type().name() == "my_asset",      old.type().name()
assert new.type().name() == "my_asset::2.0", new.type().name()
print(old.type().namespaceOrder())   # ['my_asset::2.0', 'my_asset'] = how a bare name resolves
```

**After every version install:** grep the build scripts and any parent-asset builders
for unversioned `createNode("my_asset"` calls and decide per call whether it must pin
the old version or is meant to follow the latest. Existing code such as
`sub.createNode("my_asset", "inst")` inside another asset's source silently changes
meaning the moment `::2.0` is installed.

**Comparison steps assert a NON-EMPTY result first.** The frame values were Detail
attributes; reading them as point attributes returned `{}` for both nodes, and
`{} == {}` printed "equal". An equality between two things you did not prove non-empty
is not a result. Also look for a free canary: if the new version is supposed to differ
from the old one and the comparison finds no difference anywhere, suspect the
instrument before the asset.

```python
a, b = read_frames(old), read_frames(new)       # your read-back helper
assert a and b, "empty read-back: wrong attribute class or wrong node"
assert a == b
```

---

## 2. An INT menu parameter stores the picked item's POSITION, not its token

**Rule:** for an integer parm with a menu, Houdini stores the position of the picked
item. If the tokens are sparse (valid ids 1..11 and 13..23 listed; 0 and 12 left out of
the menu), every pick after a skipped value lands one or two slots off, the first item
stores 0, and the last id can never be chosen.

**Why it hides:** values set by script are right (the script sets the id, not a
position), so everything passes until a person uses the dropdown.

**Fix:**
- List every value in order so position == value, and label the invalid ones
  ("12 - not selectable"), or use a STRING parm when the tokens are sparse.
- Write item generators in Python (item generator script language set to Python), not
  HScript loops; an HScript `for`/`echo` generator emitted its last line twice.
- Test the menu by what it STORES, not by what it shows:

```python
parm = node.parm("slot")
for pos, tok in enumerate(parm.menuItems()):
    # a dropdown pick stores `pos`; it must equal the id the label promises
    assert pos == int(tok), "item %d carries token %s" % (pos, tok)
parm.set(5); print(parm.evalAsString(), parm.menuLabels()[5])   # id and label agree
```

`parm.set(<int>)` on a menu parm also sets by position, so script-driven tests of
the UI path need the position/token comparison above.

---

## 3. The delivery read-back must force-cook EVERY output and every member node

**Rule:** before saving the definition or writing a delivery record, force-cook each
output index 0..N-1 and each member node, and record the point/prim counts or the
error per output. An output listed in the record without a measured count is a FAIL.

**Why:** Houdini cooks lazily. An output that nothing displays or reads never compiles,
so a wrangle with a VEX compile error can sit unnoticed for as long as nobody asks that
output for geometry. In the originating case an asset had two outputs that cooked and a
third that raised a compiler error on the first forced cook, a day after it had been
delivered.

```python
rep = {}
for i in range(len(asset.outputNames())):          # every output index
    try:
        asset.cook(force=True)
        g = asset.geometry(output_index=i)         # SOP asset; read the inner Output SOP if unavailable
        rep[i] = None if g is None else (len(g.points()), len(g.prims()))
    except hou.OperationFailed as e:
        rep[i] = "ERROR: %s" % e
members = {n.path(): n.errors() for n in asset.allSubChildren() if n.errors()}
assert rep and all(isinstance(v, tuple) for v in rep.values()), (rep, members)
```

`None` means the output never produced geometry - also a FAIL.

**Type your reads before an overloaded setter.** An untyped `point()` / `prim()` call
passed straight into `setprimattrib()` is ambiguous and the wrangle fails to compile
(also check function names: the VEX function is `removepoint`, there is no `removepoints`).

```vex
vector nrm = point(0, "N", pt);                 // typed local first
setprimattrib(0, "n_copy", pr, nrm, "set");     // not: setprimattrib(0, "n_copy", pr, point(0, "N", pt), "set")
removepoint(0, pt);
```

---

## 4. Verify through the node the artist actually sees

An HDA's edited node is not always the node carrying the display/render flag; a cache or
freeze downstream can hide every edit. The rule and the walk are in the
houdini-python-automation skill, `houdini-python-automation/reference/verify_through_display_node.md`; apply them
before claiming a new version "works".

---

## 5. Fixing a behaviour of a live HDA as a minor version (obs 180)

Typical case: a per-frame recook hidden by a scene-level Time Shift (7.1-7.4 s per frame
step headless). Ship it as `name::N.1`, proven a no-op on content.

1. **Find the independent cause.** `node.isTimeDependent()` on every child plus
   `parm.isTimeDependent()` on each parm listed 46 time-dependent children, but only ONE
   had an independent cause (a USD Import SOP `importtime` = `$F`, its default); the rest
   were time dependent only because they read geometry downstream of it. Fix the one
   cause, not every symptom.
2. **Build off the team share.** Every definition save (`setParmTemplateGroup`,
   `updateFromNode`, a Help edit) writes a `backup/<file>_bakN.hda` next to the library,
   and `copyToHDAFile` writes the new file FIRST, before any of the script's own checks.
   Stage every build artifact locally (assert the output path is off the share), test it
   there, and copy only a passing file under a new name. On a no-delete folder a
   half-built file cannot be removed by an agent. Build inside a session with the
   production hip loaded so nested definitions match the scene.
3. **Locked-HDA contents load lazily** in hython: `allSubChildren()` is empty (a fresh
   instance showed 1 node) until the instance is synced. Call
   `node.syncDelayedDefinition()` first (it populates the contents WITHOUT cooking, right
   for an instance with no input that would fail to cook), `node.cook(force=True)` second.
   An audit or diff that reads "no internals" proves nothing; assert it is non-empty.
4. **Prove the new definition:** a node-by-node, parm-by-parm diff of a fresh instance of
   old vs new type must show exactly the intended changes (type name, the new parm, the
   changed expressions).
5. **Swap on a hip COPY:** `changeNodeType(new, keep_parms=True,
   keep_network_contents=False)` kept every parm including a Data parm holding a baked
   layout (proven by geometry digest before / after); the only state difference was the
   new parm at its default. Compare a content digest old vs new at the reference frame
(`houdini-python-automation/scripts/geo_digest.py` hashes per component and by attribute name)
   AND another frame, and the cook time per frame step.

---

## 6. After a version swap, check what the instance GAINED (obs 234)

`changeNodeType(..., keep_parms=True)` to a version that REMOVED parms leaves them on the
instance as SPARE parms: dead read-backs with expressions reading an attribute the new
version no longer writes, and an old tab-selector parm. Nothing errors and outputs are
right; only `node.spareParms()` shows them.

- List `instance.spareParms()` after the swap and compare with the spare parms before it.
  Remove dead read-backs through the parm template group
  (`parmTemplateGroup().remove()` then `setParmTemplateGroup`). Prefer read-back parm
  names that stay stable across versions so they map instead of turning spare.
- A leftover tab-selector (Houdini renames tab folders on save) is not a template in the
  group and `parmTuple()` returns None for it. It is NOT harmless: it lives in an
  instance-level parm layout written into the hip, and every open of the saved hip
  showed a load dialog "Skipping unrecognized parameter".
- A plain load and save dropped it (the re-saved copy reloaded with no warning and 141
  parm values identical). So after any swap: SAVE, then reload the saved file headless
  WITHOUT suppressing load warnings and require none. Tools that load hips must record
  the `hou.LoadWarning` text, never swallow it; a self-test loading with warnings
  ignored cannot see this.
