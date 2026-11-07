# Headless Karma: renderer rule, logs, and one still per shot

**Part of:** houdini-solaris-usd skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Rendering from a saved hip with hython, without touching an artist's open session. Measured on Houdini 21.0.596.

---

## 1. The USD Render ROP picks the delegate, not the render settings (obs 186, 294)

**Rule:** a `usdrender_rop` renders Karma CPU unless its `renderer` parm is `BRAY_HdKarmaXPU`. The Karma Render
Settings `engine = xpu` does NOT change it. Set the parm explicitly (a Karma LOP sets both; a separate
karmarendersettings + usdrender_rop pair does not), read it back, and verify on the first frame from the EXR header
(`hoiiotool --info -v <exr>`: Software "Karma (xpu)", renderTime, xpu_devices) or from the husk command line
(`-R BRAY_HdKarmaXPU`). A CPU render shows `Software: Karma (cpu)`, `-R BRAY_HdKarma`, xpu_device_count 0.

**Script:** `scripts/karma_rop.py meta <exr> --expect xpu` reads all of this with plain Python, including the
per-device share, so "Karma (xpu)" with no GPU samples fails. A 0.2 s render did exactly that (Optix 0, Embree 100)
because it ended before the GPU joined, so judge on a real frame, not a tiny test. `audit` lists every ROP's
delegate; a live session can call `audit_scene("xpu", fix=True)`.

**Why:** a 2304 x 1582 frame (32 spp, OptiX denoiser, 2 lights) took 309.6 s on CPU and froze the artist's UI for
about 5 minutes in a foreground render; with the XPU delegate it took 11.3 s with an identical image (mean luma 76.6
in both). A 1920 x 1080 frame was quoted at about 52 minutes on CPU and took 1:20 on XPU. A foreground CPU render also
queues every MCP call behind it. Do a low-resolution draft first: the delegate shows in seconds.

## 2. Headless husk output does not reach hython stdout (obs 249)

With the ROP's defaults (husk_log off, verbose 0) husk's output goes nowhere a headless run can read, so a grep of the
hython log for texture errors would report a clean render whatever happened. Turn on `husk_log` and send
`husk_stdout` / `husk_stderr` to files. On Houdini 21.0.596 XPU one missing map logs "Texture missing/error: <path>",
"Unable to load texture" and "KarmaXPU: Failed to load texture"; filter benign echoes such as "failure_retries : 0".
Prove the scan once with a deliberate failure, and treat an EMPTY husk log as a failed check.

**Script:** `scripts/karma_rop.py render SCENE.hip --rop <path> --frames A B --output <path> --expect xpu` sets the
delegate and the logs, refuses output files that already exist, then fails on log trouble, an empty log, a missing
or blank image, or the wrong engine. It never saves the hip. `scan <log>` runs the log check alone.

With `allframesatonce` one husk process ignores the ROP's `outputimage`, so the path must go on the Karma node's
`picture` (`--all-at-once` does this). A `$F4` pattern loses half frames: the tool stops before rendering; use a
padzero expression in `--output`.

**Timing:** a 4-image test read 7.8 to 9.3 s per image and about 26 s to the first image. A 258-image run then sat
7 min 17 s with no husk process, because `allframesatonce` cooks the stage at every time sample first. Time a long
run from two lengths with `karma_rop.py estimate A_report.json B_report.json --images N`, the longer 20+ images.

---

## 3. One still per shot from a saved hip

Eight frames at 1920 x 1080 took 734 s (80 to 97 s each) with nothing changed in the session or on disk.

- Give each shot its own camera by copying the working Scene Import per shot (`copyTo`, `setInput`, `objects` = the
  OBJ camera), leaving the branch untouched.
- The camera prim path cannot be built from the node name: OBJ parents become prims
  (`/<parent>/<null>/<camera>`). Search the cooked stage for a Camera prim of that name and stop unless there is
  exactly one match.
- Build every node and set every parm while Main is the current take. Switch takes only to read back or render.
- An /out `usdrender` takes `loppath`; its `render(frame_range=...)` blocks with `soho_foreground` on. Set `renderer`
  to `BRAY_HdKarmaXPU` (section 1).
- The hip's own COP grade can bake each EXR in the same process: set the File COP name and press the ROP Image's
  `execute`, then compare with an independent numpy model of the grade.
- Keep logs and partial files on a local drive when the output folder is on a share where agents cannot delete. Set
  `PYTHONDONTWRITEBYTECODE=1` before importing a script from the share, or a `__pycache__` stays behind.

## 4. Prove a take with one pixel comparison

A parm read-back of the take proves the parm, not the render. Before frames go to a client, render one shot under
Main as well: a close-up showed an object 0.32 m higher, which proved the ROP's `take` parm reached husk. When a switch
must change a picture, test the picture once with the switch off.

## 5. A new USD ROP frame range (obs 253)

A new USD ROP (like any new ROP made from Python) can hold `$FSTART` / `$FEND`
expressions in its `f1` / `f2` frame range; `deleteAllKeyframes()` on `f1`, `f2`, `f3`
before setting, then read back and verify the written range. See
`houdini-python-automation/reference/headless_build_checks.md`.
