# Roto shapes from Python (nuke.rotopaint)

Every item below accepted bad input without an error; each was found by measuring the render. Prove each construct on a deliberately failing case (overlapping shapes, a shape outside the keep area, a frame BETWEEN keys) before building on it.

## Recipe

```python
import nuke.rotopaint as rp
# curves = the Roto node's curves knob
shape = rp.Shape(curves, type='bezier')
for (x, y) in points:            # plate pixels, y is UP from the bottom
    shape.append((x, y))         # plain float tuples, sharp corners (static shape)
curves.rootLayer.append(shape)
curves.changed()                 # at the end

# animated point: key it BEFORE appending
cp = rp.ShapeControlPoint()
cp.center.addPositionKey(frame, nuke.math.Vector2(x, y))
shape.append(cp)
```

- Key only `center`. `featherCenter` is an OFFSET from the centre: keying it with the absolute position made a 10 000 px shape cover 29 000 px.
- **Keys go on the point BEFORE it is appended.** `shape.append(cp)` stores its own copy, so keys added to the local `cp` afterwards are silently lost and animated shapes render static at their first key. Test frames that sit on key frames pass; check frames between keys against a reference. (Keying through the stored point, `shape[i].center`, works.) Add a position key for every point at every key frame (linear between keys).
- **Draw order is reversed:** the shape appended FIRST is drawn LAST, so append remove shapes before keep shapes.

## Blend mode and attributes

- `AnimAttributes.set` is `set(time, name_or_index, value)`. The two-argument `set(name, value)` raised nothing and did nothing (every blend mode "tested" identically), and a constant needs the time form too.
- Blend ids are NOT the dropdown order. Read them from the knob at runtime: `roto['blending_mode'].values()` lists `name<TAB>id` (observed list: over 0, max 1, multiply 2, color-burn 3, min 4, screen 5, color-dodge 6, plus 7, overlay 8, soft-light 9, hard-light 10, from 11, minus 12, difference 13, exclusion 14). Do not hardcode; re-read the list on each Nuke version.
- Subtract with the id of "minus" (12): `shape.getAttributes().set(1, rp.AnimAttributes.kBlendingModeAttribute, 12.0)`. Mode 11 ("from") behaved like XOR: two overlapping remove shapes flip back to 1, and a remove shape outside the keep area ADDS alpha. A probe with a remove shape fully inside the keep shape gave identical results for modes 11-14 and hid this.
- Minus leaves negative alpha: put a `Clamp` (alpha 0-1) after the Roto.
- Gate a shape on and off with `attrs.set(frame, rp.AnimAttributes.kOpacityAttribute, value)`.
- Prove a blend choice by writing the Roto to a float EXR and sampling inside the removed shape; JPG/PNG views hide negatives and holes.
