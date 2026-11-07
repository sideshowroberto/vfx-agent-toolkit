# Nuke Python API traps (headless and bridge)

Calls that "succeed" and mean something else. Measured on Nuke 17.0v2. The check for each is a read-back at every stage, never the exit code.

## Merge2 with alpha-only channels

- `Merge2(operation="mask"|"stencil"|"in"|"out"|"over"|"atop", Achannels="alpha", Bchannels="alpha", output="alpha")` has no alpha to read from the other input. On two constants (A alpha 0.5, B alpha 0.8): mask and in gave 0.0, stencil 0.8 (B unchanged), over 1.3; max (0.8) and multiply (0.4) were right. With the DEFAULT rgba channel set, mask and stencil gave the correct 0.4.
- Fix: leave the channel set at default for mask / stencil / in / out, or use `multiply` (and a `1 - a` Expression for subtraction) on alpha-only chains. Prove a merge chain by sampling every stage on a known point.
- A render of valid PNGs with identical byte sizes across frames is a blank render until pixels say otherwise.
- A bare `Invert` on a Roto only covers the Roto's bbox, so a following multiply zeroes everything outside it. Use Merge2 `from` over a full-format white Constant.

## Sampling

- `nuke.frame(f)` then `node.sample(...)` can return the same frame's values for every f (a check printed identical numbers for three frames). `node.sample(chan, x, y, 1, 1, f)` with an explicit frame is frame-aware. Any read-back that prints the same value for different frames is the instrument, not the data.
- Through the MCP bridge keep read-backs to a handful of samples (about 10), upstream of heavy nodes where possible (bbox, knob values, a few pixels). 240 samples through a full-resolution blur held the GUI main thread for over 5 minutes and every later call timed out, including `nuke.root().name()`. Do exhaustive checks in a headless `-t --safe` run of an exported node snippet (`nuke.nodeCopy`). Never run a long evaluation in a GUI whose script is unsaved.

## Node kwargs

- A Python tuple or list passed as a node kwarg is parsed as text: `nuke.nodes.Crop(box=some_knob.value())` corrupted the root view list (`nuke.views()` returned `['main', '0.0,', '4608.0,']`) and a later `nuke.execute` failed with "cannot be executed for multiple views". Pass strings, and read back `nuke.views()` after any node creation that took a knob value as a kwarg.
- A Write `file` knob given a backslash path eats the backslashes. Always pass forward slashes.

## Headless launch

- `nuke -t --safe script.py nodes.nk 1036 1396 2`: Nuke takes trailing numbers as ITS frame range and they are not forwarded to `sys.argv` (the script died on IndexError). Pass them as a single argument, for example `frames=1036:1396:2`.
- A Read pasted from the GUI with colourspace "default (scene_linear)" fails under `-t` with "Invalid LUT selected", even with the same custom OCIO config on Root. After `nodePaste`, set the actual colourspace name.

## Several GUI Nukes

- The MCP bridge port can be bound by two GUI Nukes at once; the client reaches either, silently. Before the first read or write, return `nuke.root().name()`, frame range and node count (assign `result = ...`; `runPythonScript` returns `result`, not printed output) and compare with the script the user named. On a mismatch run `netstat -ano | findstr :8765`: two LISTENING PIDs with window titles means two GUI Nukes, so ask the user to close the unused one. Do not retry until it lands.

## Saving over an opened shot script

Headless `scriptSaveAs` of an opened script silently changes OLD nodes (Viewer loses `viewerProcess`/`frame`, `note_font` and group-end lines drop, `in_colorspace`/`out_colorspace` lines appear, window layout and `#write_info` header vanish, CRLF becomes LF). Do not re-save an artist's script: see [version_up_method.md](version_up_method.md).
