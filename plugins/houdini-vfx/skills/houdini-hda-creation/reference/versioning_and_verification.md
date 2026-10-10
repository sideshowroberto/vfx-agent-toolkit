# HDA Versioning and Delivery Verification

**Part of:** houdini-hda-creation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-09

Four traps that each produced a confident, wrong "verified" result. Every one is
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
