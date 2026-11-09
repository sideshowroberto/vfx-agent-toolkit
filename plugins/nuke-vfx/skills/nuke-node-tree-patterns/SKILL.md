---
name: nuke-node-tree-patterns
description: Verified patterns for building Nuke node trees from Python - what auto-connects, cropping with Reformat 'to box', blending overlapping pre-masked tiles with an Expression mask, Premult and a plus Merge. Use when a script must wire, position or blend generated nodes, or for tile-and-blend tools.
allowed-tools: Read,Write,Bash
---

# Nuke node-tree patterns

**Version:** 2.0.0 (staged 2026-11-08, baseline eval nuke-round2). The long 1.0.0 text is kept in reference/original_SKILL_2026-11-08.md (tiling-tool code, positioning offsets). Statements below were re-measured on NukeX 17.0v2.

## Wiring
- `nuke.createNode(cls)` wires input 0 to the SELECTED node and selects the new node, so consecutive createNode calls chain. `inpanel=False` does not stop it.
- `nuke.nodes.X()` never connects: with a node selected, a new Transform had input 0 empty (measured). The 1.0.0 claim that it "may still auto-connect" was WRONG. Deselecting is harmless but not needed.
- Position with `setXYpos()` relative to the input (`xpos()+200`, `ypos()+100`), then `setInput()` explicitly.

## Crop a frame without scaling
`Reformat`: `type = 'to box'`, `box_width`, `box_height`, `box_fixed = True`, `resize = 'none'`, `center = True` (default). Measured: a 1920x1080 white ramp (0 at x=0, 1 at x=1920) through a 1024x1024 box read 0.28542 at output pixel (100,500), i.e. input pixel (548,528) = the middle crop; `resize = 'width'` scaled it (0.0979) and `center = False` read 0.0521 (bottom-left crop).

## Blending overlapping tiles (seamless)
1. Per-tile weight with an Expression node writing the MASK channel: `channel3 = 'mask'` (assigning `'mask.a'` is normalised to `mask` and gives the same result - the 1.0.0 "Pitfall 4" is not a pitfall), `expr3 = smoothstep(a, b, x)`, `channel0..2 = 'none'`.
2. `Premult` with `alpha = 'mask.a'`, `channels = 'all'`.
3. Combine tiles with `Merge2 operation = 'plus'` (weights sum to 1 in the overlap). Measured with tile colours 0.2 and 0.8 and a 100-200 smoothstep: 0.2 / 0.5 / 0.8 at x = 50 / 150 / 250. (Not measured here: `over` on the same tiles.)

## Checklist
- Read back `node.input(0).name()` for every node you wired; sample three known pixels of the final node.
