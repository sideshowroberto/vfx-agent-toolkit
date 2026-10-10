# Geometry Export From hython - Traps

**Part of:** houdini-python-automation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-09

Measured headless on Houdini 21.0.596 while exporting a batch of scenes to OBJ and
testing FBX / glTF / USD routes. Each item below would have shipped a wrong file or a
wrong claim. The common principle: an API that succeeds for every input proves nothing -
open the artefact (magic bytes, counts read back) before treating "the call returned" as
"the file exists in that format".

---

## 1. geometry.saveToFile() writes a fake file for ANY extension

`hou.Geometry.saveToFile(path)` has real translators only for `.obj`, `.ply`, `.stl`,
`.abc` and `.bgeo` / `.geo`. For every other extension it writes Houdini's own geo
content under the name you gave it, and the call "succeeds":

| Extension asked for | What was actually written |
|---|---|
| `.usd` `.usda` `.usdc` `.fbx` `.dae` | `PGEOMETRY V5` ASCII (about 8.6 MB for the test scene) |
| `.glb` `.gltf` `.3ds` | Houdini JSON geo (about 9 MB) |

**Rule:** use `saveToFile` only for the five real formats. For FBX / glTF / USD use the
matching ROP (filmboxfbx, gltf, usd_rop) or a converter, then read the first bytes.

```python
MAGIC = {".ply": b"ply", ".glb": b"glTF", ".fbx": b"Kaydara FBX Binary",
         ".usdc": b"PXR-USDC", ".usda": b"#usda"}
def check_format(path):
    ext = os.path.splitext(path)[1].lower()
    head = open(path, "rb").read(32)
    assert not head.startswith(b"PGEOMETRY"), "Houdini geo under a fake extension: " + path
    if ext in MAGIC:
        assert head.startswith(MAGIC[ext]), "%s: unexpected header %r" % (path, head[:16])
    return head
```

---

## 2. The OBJ writer: per-face materials need a PRIM attribute

Houdini's OBJ writer emits `usemtl <shop_materialpath>` per primitive (prims regrouped by
material), de-duplicates `vt`, writes `vn` per vertex and reverses `f v/vt/vn` to CCW. So
per-face materials survive only if `shop_materialpath` is a primitive attribute; an
object-level material parm is invisible to the writer. Stamp it onto the prims first:

```vex
// Primitive wrangle, run over Primitives, before the export
if (s@shop_materialpath == "") s@shop_materialpath = "/mat/my_material";
```

Read-back: grep the written file for `usemtl` and count the distinct names.

---

## 3. ROP menu parms: do not trust index or default

Integer menu parms on ROPs are enum indices whose order and default are not what the
label suggests. Set the item you mean explicitly (by token where the menu has tokens),
read `parm.evalAsString()` back, and check the output file's header.

- `filmboxfbx` `exportkind`: 0 = binary, 1 (the DEFAULT) = ASCII, which Blender's FBX
  importer refuses. The file is written in metres but unit-flagged cm, so it arrives
  at 0.01x scale - check the imported size, not just that it imported.
- `gltf` `exporttype` menu is [auto, gltf, glb]. From a SOP path it produced no
  materials - confirm materials in the file before promising them.
- `object_merge` `xformtype` menu is [none, local ("Into This Object"), object]. The
  DEFAULT is index 2, not 1. Set it, then verify the merged bounding box against the
  source box pushed through the source's world transform (measured deviation 0 to 3e-7 m):

```python
def world_corners(geo, xf):
    lo, hi = geo.boundingBox().minvec(), geo.boundingBox().maxvec()
    return [hou.Vector3(x, y, z) * xf for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
pts = world_corners(src_node.geometry(), src_obj.worldTransform())
lo = [min(p[i] for p in pts) for i in range(3)]
hi = [max(p[i] for p in pts) for i in range(3)]
got = merged_node.geometry().boundingBox()
dev = max(max(abs(lo[i] - got.minvec()[i]), abs(hi[i] - got.maxvec()[i])) for i in range(3))
assert dev < 1e-5, dev
```

- For `usd_rop` `savestyle` tokens (an invalid token fails silently) see the
  houdini-solaris-usd skill, `houdini-solaris-usd/reference/usd_export_checks.md`.

---

## 4. Bulk topology calls you remember may not exist

On 21.0.596 `hou.Geometry` raised `AttributeError` for `primVertexCounts` and
`vertexPointNumbers`. Probe with `hasattr(hou.Geometry, name)` on the build in use before
writing code around a bulk call from memory. What worked:

- Bulk vertex data: `vertexFloatAttribValues(name)`, which returns values in linear
  vertex order.
- Topology: loop `prim.vertices()` (about 1 s per 300k prims).

---

## 5. Scratch networks stay in memory; prove the source hip was not touched

An in-memory container (for example `/obj/__EXPORT__`) under a loaded hip is enough
scratch space for a batch export. Never `hou.hipFile.save()`. Proof that the source file
was left alone is a before/after `os.stat` of its mtime and size:

```python
before = os.stat(hip_path)
# ... run the export ...
after = os.stat(hip_path)
assert (before.st_mtime, before.st_size) == (after.st_mtime, after.st_size)
```
