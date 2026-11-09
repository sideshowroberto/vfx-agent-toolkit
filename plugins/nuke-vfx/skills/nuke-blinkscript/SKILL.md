---
name: nuke-blinkscript
description: Verified BlinkScript traps in Nuke 17 - kernelSource.setValue silently keeps the default kernel, a compile error in the GUI raises a modal dialog that wedges the MCP bridge, param knobs are Kernel_param, eAccessPoint takes no coordinates, eAccessRanged2D without setRange segfaults. Use when writing, loading or debugging a BlinkScript or .blink kernel from Python or the MCP.
metadata:
  version: 2.0.0
  updated: 2026-11-09
---

# Nuke BlinkScript - traps

Measured on NukeX 17.0v2 (nuke-round3 probes 2026-11-08, live GUI 2026-11-09; ClaudeCode/evals/nuke-round3/ANALYSIS.md)
unless a trap says otherwise.

1. **Never compile an untested kernel in an artist's live GUI.** Wrong: loading a new or edited kernel straight
   into the GUI session through the MCP. A compile error raises a MODAL dialog ("Error compiling kernel: File
   KPoint.blink, Line 5: no matching function for call to object of type 'Image'") and every later bridge call
   reports "still running after 30 s" while Nuke sits idle, until a person clicks OK. Right: compile the .blink
   headless first - `nuke -t --safe` with a script that loads it (trap 2) and renders one pixel; compile errors
   print only on that console, and `node.error()` is just a bool. Verify: the headless run shows no compile
   error, `kernelName` reads your kernel's name and a sampled pixel has the expected value - then load it in
   the GUI.

2. **`kernelSource.setValue()` does nothing.** Wrong: `node['kernelSource'].setValue(text)` +
   `node['recompile'].execute()` - the node stays on the default Swirlomatic kernel (GUI and `-t`; red 0.5
   where the test kernel gives 0.25), yet `kernelSource.value()` returns your text, so reading the source
   back lies. Right: write the kernel to a `.blink` file, set `node['kernelSourceFile']`, then
   `node['reloadKernelSourceFile'].execute()` - works in the GUI and in `nuke -t --safe` (param knobs are
   created headless too). Verify: `node['kernelName'].value()` and a pixel, never the source text. Working
   scripted build: `examples/glass_blink_build.py` with `examples/GlassRefract.blink`.

3. **Param knobs are `<KernelName>_<param>`.** Wrong: `node['thickness']` (does not exist). Right:
   `node['SimpleOverlay_thickness']`; per-input channel knobs are `<KernelName>_<input>` (e.g.
   `GlassRefract_src`). Types: float4 -> AColor_Knob (colour picker), float3 -> XYZ_Knob, float2 -> XY_Knob.
   Verify: list `[k for k in node.knobs() if k.startswith(kernelName + '_')]` before setting, and treat a
   missing knob as a failed compile, not a typo.

4. **`eAccessPoint` images take no coordinates.** Wrong: `Image<eRead, eAccessPoint> src;` then
   `src(pos.x - 50, pos.y)` - compile error "no matching function for call to object of type Image" (the
   KPoint.blink error in trap 1), wherever the call sits. Right: `src()` on eAccessPoint; `src(dx, dy)`
   relative on `eAccessRanged2D`; `src(x, y)` absolute on `eAccessRandom`. Verify: headless compile (trap 1).

5. **`eAccessRanged2D` without `setRange` can crash Nuke, not just fail to compile.** Wrong: a param-driven
   offset `src(-off, 0)` on eAccessRanged2D with no range declared - it compiled and then segfaulted headless
   Nuke (exit 139). Right: `void init() { src.setRange(-100, 0, 100, 0); }` covering the largest offset (then
   compiles and samples correctly), or use eAccessRandom with absolute coordinates. Verify: render a pixel at
   the maximum offset headless and compare to the input shifted by hand.

6. **Old advice that is false on 17.0v2 - do not design around it.** "No image access in helper functions":
   a member `float4 fetch(int x, int y) { return src(x, y); }` on an eAccessRandom image compiled and returned
   the right pixel. "eAccessRanged2D with a param offset fails to compile": it compiles (trap 5 is the real
   hazard). "`-t` never creates param knobs": `reloadKernelSourceFile` creates them headless.

7. **Do not name a helper `bilinear`.** Blink ships a built-in `bilinear(img, x, y)`; a member function of
   the same name clashes (GlassBlink build, 2026-11-06). Pick another name. Verify: headless compile.
