# Headless Build Checks

**Part of:** houdini-python-automation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

"The node cooked" is a completion signal, not a correctness signal. A scripted SOP build
(hython or the MCP) can cook cleanly and still hold broken geometry. Read counts and
normals back before trusting it or its USD export.

---

## 1. Cook every node and print its errors

Call `node.cook(force=True)` on every node you built and print `node.errors()`. Without
it a script saves a hip with broken nodes. A wrangle made from Python also does not bind
bare globals (`P.y = 1;` fails, `@P.y` works) - see
`houdini-vex-programming/reference/wrangle_traps.md`.

## 2. Grid and Sphere `rows` / `cols` are POINT counts

A 1 x 1 grid is ONE point, so 30 "flags" came out as 30 prims with 1 vertex each: the
prim count looked right and nothing rendered. One quad needs rows = cols = 2.

**Check:** a histogram of vertices per prim (tri / quad / n-gon) per part.

## 3. Check face direction, do not assume it

A Revolve SOP faces INWARD for a bottom-to-top profile. Compare `prim.normal()` with the
radial direction and reverse the profile order if it points in. Houdini winding is
left-handed against USD's right-handed default, so author the USD mesh orientation from
a measured winding test, not by assumption.

## 4. A new ROP's frame range is an expression, not a plain value

A ROP made with `createNode` holds `$FSTART` / `$FEND` expressions in `f1` / `f2`, and
`parm.set()` did not replace them: a shot longer than the scene range exported
truncated. Call `deleteAllKeyframes()` on `f1`, `f2` and `f3` first, set the values, then
read each back. Verify the WRITTEN file's time range, not the knob. The trap only shows
when the job range exceeds the scene range.

## Idempotent builders on a live scene (obs 200)

Set inputs and connections ONLY on nodes the call creates. Re-running a build() to add a knob must change nothing that already exists, including wiring - re-pointing an existing leaf with setInput silently undid a later step that had re-wired it through new nodes. Check: re-run the builder and read back that every pre-existing node's inputs are unchanged. (Not covered by obs 196, which is the folder-handle rule already staged on 2026-10-20.)
