---
name: nuke-python-scripting
description: Traps for scripting Nuke through the MCP bridge - Roto shapes via nuke.rotopaint (animated points, subtract shapes), Merge2 on alpha-only channels, sampling per frame, tuple kwargs corrupting nuke.views(), headless -t, version-up. Use before writing nuke Python, scripted Roto, or a bridge read-back.
allowed-tools: Read,Write,Bash
---

# nuke-python-scripting

**Version:** 2.0.0 (staged 2026-11-08, baseline eval nuke-round2)
Every trap below was reproduced on NukeX 17.0v2 through the bridge. Prove each construct by READING BACK pixels or knobs, never by the absence of an error.

## Bridge basics
- `runPythonScript` returns the variable `result`, not printed output. First call of a session: return `nuke.root().name()` and the node count (two GUI Nukes can share port 8765; see reference/api_traps.md).
- Keep read-backs to about 10 samples, upstream of heavy nodes.

## Traps that return confident wrong numbers
1. **Sampling a frame**: `nuke.frame(f)` then `node.sample(...)` returned the frame-0 value for every f (0.0, 0.0, 0.0 for a ramp that is 0.2/0.5/0.8). Use `node.sample(chan, x, y, 1, 1, f)` with the frame explicit. `nuke.sample()` takes no frame.
2. **Merge2 with alpha-only channels** (`Achannels`/`Bchannels`/`output` = alpha): `mask` and `in` give 0.0 and `stencil` leaves B (0.8) unchanged where 0.4 is right; `multiply` and `max` are right. Leave the channel set at rgba for mask/stencil/in/out, or multiply. Both arms of the eval followed a spec that asked for alpha-only, reported 0.0 and could not name the cause.
3. **A tuple or list as a node kwarg is parsed as TEXT**: `nuke.nodes.Crop(box=(100,100,400,300))` left the box 0,0,0,0 AND turned `nuke.views()` into `['main', '100,', '400,']`, which later makes `nuke.execute` fail with "multiple views". Set vectors with `node['box'].setValue([...])`; read `nuke.views()` back after any create that passed a knob value as a kwarg. (Repair: `nuke.root()['views'].fromScript('{main ""}')`.)
4. **Roto from Python** (`import nuke.rotopaint as rp`) - recipe and traps in reference/roto_from_python.md. The ones that decide the result: key a point (`cp.center.addPositionKey`) BEFORE `shape.append(cp)` (keys added after are lost and the shape is empty/static: alpha 0 at every frame); the first shape appended is drawn LAST, so append remove shapes before keep shapes; subtract is blend id 12 ("minus"), not 11 ("from" flips overlaps back to 1); follow minus with a Clamp (overlapping removes give alpha -1).
5. **Write/Read paths**: forward slashes. **Headless**: `nuke -t --safe`, one token for frame args (`frames=1000:1010`).
6. **`createNode` wires to the selection, `nuke.nodes.X()` does not** (measured: input 0 stays empty even with a node selected). Prefer `nuke.nodes.X()` for graph building.
7. **Re-saving an artist's script** silently changes old nodes: use reference/version_up_method.md and scripts/nk_version_up.py.

## NukeMCPLogger (optional)
`from nuke_mcp_logger import NukeMCPLogger` (installed in ~/.nuke) wraps results as `{status, logs, errors, stats}`. 0 of 44 valid Opus eval runs imported it; plain `result = {...}` works the same.

## References
reference/api_traps.md, reference/roto_from_python.md, reference/version_up_method.md, scripts/nk_version_up.py (append, compose, diff, lint, outputs, reads, verify).
