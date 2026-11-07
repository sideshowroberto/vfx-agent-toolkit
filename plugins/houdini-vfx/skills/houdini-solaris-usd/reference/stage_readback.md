# Reading a LOP stage back

**Part of:** houdini-solaris-usd skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

How to read counts and values off `node.stage()` without fooling yourself. Common principle: a stage edit is done
only when the COMPOSED stage shows it on every frame and on every branch that renders; a node that cooks without an
error can still have done nothing, or done it once. Measured on Houdini 21.0.596.

---

## 1. Values are time samples: read at the frame

**Rule:** pass the frame time code to every `Get()`, `ComputeVisibility()` and `ComputeLocalToWorldTransform()`
(`Usd.TimeCode(hou.frame())`), and report `GetNumTimeSamples()` next to any value used for an export decision.

**Why:** SOP Import authors mesh topology ONLY as a time sample at the current frame, no default:
`GetFaceVertexCountsAttr().Get()` returned None for 14,536 of 14,536 meshes. Camera LOP cameras hold a fallback
(focalLength 50, horizontalAperture 20.955) plus one time sample with the real lens, so `Get()` reported 50 mm for a
29 mm camera. Before export to another app, bake single time samples to defaults; a reader at default time (or an
importer that does not pick the frame) gets empty meshes and a 50 mm lens.

A Scene Import LOP's stage carries only the sample of the frame it was cooked at, so cook at each test frame
(`hou.setFrame(f)`, then `node.stage()`) before comparing.

---

## 2. Count visible prims only, and say both numbers

**Rule:** count geometry over `Usd.TraverseInstanceProxies()` AND visible-only (`ComputeVisibility`), and report both.

**Why:** instance-proxy traversal of one dressing gave 1,760,324 faces; half were invisible copies
(`ComputeVisibility` = invisible on 880,162) and the visible half matched the SOP count exactly. Confirm every count
with an instrument on the other side of the export (the SOP geometry).

---

## 3. Prove a removal by diffing path sets, never totals

**Rule:** diff the traversed path SETS before and after, classify each removed path (under the target item / under
the root's `Prototypes` / other) and require other = 0 and appeared = 0. Check the OFF state against known values
first, so the check proves it can see the items before it proves they are gone. Run it in a no-render dry pass.

**Why:** hiding two items (180 + 2 = 182 instance-proxy prims) dropped the stage by 364, because SOP Import writes
each packed item's prototype under `<root>/Prototypes` and a prototype nobody instances any more leaves too. The
count check failed a correct scene.

---

## 4. Edits made from Python: read the composed result

- **World-space Transform LOP on animated prims is exact at one frame only.** It appends `xformOp:transform:<node>`
  AFTER the animated op, so it acts inside the prim's own animated transform with one sample computed for one frame
  (off by up to 0.94 matrix units over 24 frames, no error or warning). To move animated prims rigidly, PREPEND one
  constant op (`xf.SetXformOpOrder([op] + ops, xf.GetResetXformStack())`) or transform a parent Xform, and verify on
  several frames including subframes against a before snapshot.
- **A Material Library created and filled by script can come up with `assign1` OFF.** The prim stays bound to the
  parent's material with no warning. Check `UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()` on the
  downstream render LOP, not the parms you set.

---

## 5. Instancer prototypes left at the origin still render and emit

**Rule:** author prototypes under a deactivated scope, or Prune (deactivate) the proto ROOTS after the last Instancer
that reads them, and keep them away from the origin. After changing geometry near the origin, run a light / prim
census by 2-level root + computed visibility and look for prototype roots.

**Why:** three light prototypes sat at the origin upstream of their Instancers. One (a rect light with Render Light
Geometry on) was visible and lit the scene; a podium-sized object had hidden it for weeks, and a shorter replacement
exposed it as a bright vertical line. Pruning the three roots after the last instancer fixed it and the census was
otherwise identical (the referenced copies keep their own specs).

---

## 6. Compare composed stages per prim, with a canary

**Rule:** use `scripts/stage_digest.py digest SCENE.hip /stage/OUT --frame A --canary-frame B --out x.json`, then
`stage_digest.py compare before.json after.json`. Never hash `stage.ExportToString()`. Before trusting "identical",
show that the same digest flags a known change: another frame on an animated camera.

**Why:** a whole-stage export stopped at exactly 2,147,483,647 characters, took 87 to 101 s, and gave four md5s for
four stages that matched. A per-prim digest took 4 to 5 s, found them identical over 9,591 prims, and its canary (1006
against 1050) flagged exactly the 4 animated cameras. Hashing `numpy.asarray(v).tobytes()` on a string array would
have hashed object pointers, so object arrays hash as text.

**Prove it the other way too:** digest one hip twice and expect IDENTICAL. USD numbers `/__Prototype_N` afresh per
load, so the same hip read as 6,903 prims on each side until prototypes were keyed by content, and instances by
the prototype they point at. A changed prototype then lists as its whole subtree, not as the one mesh that moved.

