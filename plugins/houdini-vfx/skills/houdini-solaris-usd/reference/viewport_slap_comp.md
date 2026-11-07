# Driving a Copernicus viewport slap comp from Python

**Part of:** houdini-solaris-usd skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Grading a Karma viewport render live with Houdini 21 COPs (slap comp / Filter List) from an agent.
**Fragility warning:** the only HOM entry point is the private method `SceneViewer._setSlapcomp(node)`, and everything
here was measured on ONE build (Houdini 21.0.596). Re-test after any Houdini update and treat it as unsupported API.
Common principle: when a feature has one blessed path (the tool the UI runs), take that path from code too; when the
viewport shows "no change", read the log before concluding the change did nothing.

---

## Recipe

1. Build the Filter List through SideFX's own tool path, in the order the filters should run:
   `coptoolutils.genericTool(kwargs, '<type>')` with
   `kwargs = {'pane': imagefilterlist.imagefilterlist.FakePane(list_node), 'do_not_jump_to_child': True}`. This leaves
   the display flag on the FIRST node and signatures on auto. Then set parms with `set_parameters`.
2. Point the viewer at the list with `_setSlapcomp(list)`; turn it off with `_setSlapcomp(None)`.
3. Read errors from the log: attach `hou.logging.MemorySink()` to 'Karma Rendering', re-trigger the slap comp, read
   `stealLogEntries()`. The viewport itself just shows the ungraded image.

## Traps

- `_setSlapcomp` refuses a Block End ("must be a COP2NET node") and silently does nothing with a plain copnet that
  holds a registered slap comp block. A `copnet_filterlist` in /img works.
- A Filter List built by `build_network` (unwired nodes, display flag on the LAST node, Bright left on auto signature)
  failed every frame with "Slap Comp error: Error from node X: source is missing", shown only in the Log Viewer.
  Setting RGBA signatures did not fix it, and neither did chaining; the genericTool rebuild did. Which of the two
  differences mattered was not isolated.
- `build_network` does not run the steps the UI tool runs when it creates a COP node. Three nodes came out unusable:
  a File COP with 0 AOVs (no outputs; downstream "getInputLayer(0, 0) is missing"), a ROP Image with no AOV ("No valid
  output AOVs specified"), and an Invoke Block with no ports ("Requested output port is out of range"). After
  `build_network`, set File `aovs` 1 + `aov1` C, set the ROP's `aov1`, press `setports`, and read the output names back
  before baking.
- Building inside /img through `build_network` moved the Scene Viewer and one network editor into that network, so a
  capture grabbed the COP viewer. Stash each pane's pwd and `visibleBounds()` before building and put both back after.
  (createNode + applyToolRecipe + genericTool in one `execute_python` call did not move any pane.)
- A contrast in ACEScct log space crushes the darks (the linear toe goes below zero); ACEScc avoided that offline but
  the viewport still crushed it. A power curve in linear (Bright 1/pivot -> Gamma with Invert -> Bright pivot with a
  tint) needs no OCIO and matched in both paths.

See verification_instruments.md section 7 before measuring shadow levels from a viewport capture.
