# Scripted Boolean carves that fail silently

Moved out of SKILL.md (Troubleshooting Issue 3) to keep the skill under 500 lines; observation 64.

## Scripted Boolean carve reports success but produced nothing

**Symptoms:** a script that carves a host with a Boolean modifier (Exact solver, often a
collection operand) and then reads the evaluated mesh finishes with no error, and the
result has the host's polygon count unchanged, or 0 polygons.

**Two silent causes (measured with a Boolean modifier on Blender 5.1; the first applies by the
same mechanism to any modifier, including `NODES`):**

1. **The host sits in a collection that is EXCLUDED from the view layer.** `obj.evaluated_get(depsgraph)`
   then returns the mesh WITHOUT its modifiers (386 polygons in, 386 out, zero seconds), and
   `view_layer.update()` does not help. Un-exclude the collection before creating or evaluating
   the host, and restore it afterwards.
2. **A cutter is inside-out.** `bmesh.ops.recalc_face_normals` on a freshly built closed solid
   returned inside-out cutters for some parameter values (same code, different radii). An
   inside-out cutter makes the Exact solver return an EMPTY mesh for a Difference, and with a
   collection operand one bad cutter empties the whole result. Wind the faces explicitly instead
   of relying on the normals recalculation.

```python
import bpy, bmesh

def assert_cutter_ok(bm, name):
    """Every cutter: positive signed volume and no open edges."""
    if bm.calc_volume(signed=True) <= 0:
        raise RuntimeError(name + ": inside-out cutter (signed volume <= 0)")
    if [e for e in bm.edges if not e.is_manifold]:
        raise RuntimeError(name + ": non-manifold cutter")

POLY_FLOOR = 1000        # from the plan: fewer evaluated polygons than this means the carve failed
host_eval = host.evaluated_get(bpy.context.evaluated_depsgraph_get())
if len(host_eval.data.polygons) < POLY_FLOOR:
    raise RuntimeError("carve produced %d polygons" % len(host_eval.data.polygons))
```

**Diagnose:** when the floor trips, set the modifier to `operand_type = 'OBJECT'` and test the
cutters ONE AT A TIME (evaluate, read the polygon count, restore the modifier in a `finally`);
the cutter whose count collapses is the bad one. A procedural build step needs its own
produced-something assertion (polygon count, signed volume), because Blender reports success for
an evaluated mesh that skipped its modifiers or a boolean that returned nothing.
