# Per-Shot Variants with Takes (from Python)

**Part of:** houdini-python-automation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Takes are the Houdini way to keep a close-up's placements apart from the wide in one hip.
Keep the variation in the scene and make the take a single switch; a take holding every
moved transform is a second copy of the layout nobody can review.

## Build

- The alternate placement lives in a twin object (`<item>_CU`) whose display is driven by
  one toggle parm on the owning node; the original's display is the inverse. The merge
  expression picks twin or original from the same toggle (see `editable_proxies.md`).
- Each variant take holds ONLY that toggle.
- Pin each shot ROP's `take` parm (the variant take for the close-up, `Main` for the
  wide) instead of leaving `_current_`.

## API

- `hou.Take.addParm` does not exist; use `take.addParmTuple(hou.parmTuple(path))`.
- New take: `hou.takes.rootTake().addChildTake(name)`. It must be current
  (`hou.takes.setCurrentTake`) while its value is set; restore Main in a `finally`.
- Any later parm edit lands in whichever take is current, and the current take is saved
  with the hip: confirm Main is current before editing or saving.

**Check:** switch to each take, read the merged item list and display flags, then back to
Main.
