# Verify Through the Display Node

**Part of:** houdini-python-automation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-09

**Rule:** after editing a network, verify the result on the node that carries the
display / render flag, not only on the node you edited. A load-from-disk cache or a
freeze downstream of your edit turns every correct change into an invisible one.

**Why:** in the originating case four successive versions of a scene were verified on the
edited nodes and on a render taken with the display flag MOVED to the live node. The
object's real display and render flag sat on a `timeshift` after a `filecache` with Load
from Disk on and a basename hardened to an older version (`cache_v028`). The display node
held 23,695 polys with no new attributes against 61,104 on the live node; anyone opening
the newer versions saw the old result. A compaction summary had even carried the belief
"no cache exists, the display is empty" - a carried belief is a hypothesis, so re-walk
the live scene.

---

## Step 1 - before the first edit: find what the viewer actually sees

Find the node with the display / render flag and walk its inputs upstream for freezes:
`filecache`, `file`, `timeshift`, `object_merge` pulling from disk.

```python
def display_chain(container):
    shown, render = container.displayNode(), container.renderNode()
    seen, stack, rows = set(), [shown, render], []
    while stack:
        n = stack.pop()
        if n is None or n.path() in seen:
            continue
        seen.add(n.path())
        info = {k: n.parm(k).eval() for k in ("loadfromdisk", "basename", "file") if n.parm(k)}
        rows.append((n.type().name(), n.path(), info))
        stack.extend(n.inputs())
    return shown, render, rows
```

Flag any row whose type is a cache or freeze, and any `loadfromdisk` that is on. The
Houdini MCP equivalents are `get_network_overview` + `get_cache_status`.

## Step 2 - after the edits: compare the display node with the edited node

```python
def summarize(node):
    g = node.geometry()
    return {"points": len(g.points()), "prims": len(g.prims()),
            "pointattrs": sorted(a.name() for a in g.pointAttribs()),
            "primattrs": sorted(a.name() for a in g.primAttribs())}
print("edited:", summarize(edited_node)); print("shown :", summarize(shown))
```

The display node must contain the attributes you added and a count of the same order as
the edited node. Any difference needs a named downstream node that explains it; "the
cache is probably fine" is not an explanation.

## Step 3 - if a cache sits in between, re-writing it is part of the deliverable

- Write the cache again under a NEW basename / version. Never write over the old one.
- Read back THROUGH the display node (poly count, attributes), and render with the flag
  where it really lives.
- A material assignment can sit upstream of the cache too, so the cache bakes the
  material mode: changing materials downstream or on the live branch changes nothing in
  the cached result until the cache is re-written.
- Never move the display flag to verify without moving it back. Record the original and
  re-check it:

```python
orig = container.displayNode()
...                                  # temporary flag move, if you must
orig.setDisplayFlag(True)
assert container.displayNode() == orig
```

The same walk applies in Solaris: the stage the viewport or Karma shows may be a cached
or sublayered file, so walk the display LOP's inputs for sublayers / references of an
older written layer.

---

## Reading viewport captures (obs 160)

- A viewport capture is RGBA. Where nothing is drawn, alpha is 0 and RGB is 0, which
  viewers show as white. A semi-transparent object over the empty viewport therefore read
  alpha 128 / RGB near white and looked like a wrong blend. Judge transparency only over
  geometry, or put an opaque backdrop behind the subject.
- Hash successive captures. If a change that must alter the image leaves the hash
  identical, stop: something (an object covering the camera view, a frozen view) is
  hiding the change. Seven captures over four different materials were byte-identical
  because a camera icon filled the frame.
- Compare sampled pixels with known source values (a test plate with markers and straight
  alpha), not by eye.
