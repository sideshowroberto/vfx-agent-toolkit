# Python SOP and Injected-Code Traps

**Part of:** houdini-python-automation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

---

## 1. Code written into a string parm is string-expanded

**Rule:** Houdini expands a string parm when it evaluates, so a Windows path written as a
Python literal with doubled backslashes into a Python SOP's `python` parm arrives with
the backslashes collapsed, and `\f` or `\0` become control characters (an `OSError:
[Errno 22]` with odd bytes in the path).

**Fix:** use forward slashes inside injected code. Read existing code back with
`parm.unexpandedString()`, never `eval()`, before patching and setting it back - a
source with backslashes is corrupted by the round trip.

## 2. A Python SOP failure only surfaces through `node.errors()`

After setting code, check `node.geometry() is not None` and raise with `node.errors()`.
Otherwise the real traceback is lost and the caller dies a line later with an unrelated
`'NoneType' object has no attribute ...`.

## 3. Read the wired output, not output 0 of the input node

`node.inputs()[0].geometry()` returns the input NODE's output 0. When the input is a
multi-output node wired from another output, the code sees the wrong geometry. Use
`hou.pwd().inputGeometry(i)` (it follows the wire). Outside a cook, a node's own
`geometry(output_index)` takes the index explicitly.

## 4. Helper scripts exec'd into a shared namespace clobber the caller

`exec(open(helper).read())` runs in the caller's globals. A helper's loop variable
replaced the caller's output function, and its module-level node handle replaced the
caller's. Both failed loudly here; a clobbered name that still resolves (a node path to a
sibling with the same parm names) would give a wrong read-back with no error.

**Fix:** helpers keep module-level names private (prefix `_`) or wrap the body in a
function and expose one result name. Chained callers run each helper in its own
namespace (`exec(src, {"__name__": "helper", **inputs})`) and read the result from that
dict, passing inputs through the dict rather than ambient globals.
