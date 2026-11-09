---
name: nuke-cattery-inference
description: Verified Cattery traps in Nuke 17 - CatFileCreator knob is torchScriptFile (capital S), Inference tileSize only takes None/1024/2048/4096 (512 errors), torch is not importable from Nuke Python, cat.json minimum_nuke_version_required gates discovery, setting modelFile blocks the bridge. Use when tracing a PyTorch model for Nuke, building a .cat, installing a Cattery package or setting up an Inference node.
metadata:
  version: 2.0.0
  updated: 2026-11-09
---

# Nuke Cattery / Inference - traps

Traps 1-4 measured on NukeX 17.0v2 (nuke-round3 probes and evals, 2026-11-08/09;
ClaudeCode/evals/nuke-round3/ANALYSIS.md). Traps 5-8 are production lessons from the 2026-03 DA3 depth
integration and obs 267, not re-measured in the evals.

1. **CatFileCreator knob is `torchScriptFile`.** Wrong: `cat['torchscriptFile']` (raises). Right:
   `torchScriptFile` (File_Knob), with `catFile`, `channelsIn`, `channelsOut`, `modelId`, `outputScale`, and
   the button `createCatFile`. Inference knobs: `modelFile`, `useGPUIfAvailable`, `halfPrecision`,
   `channelsIn`, `channelsOut`, `tileSize`, `tileOverlap`, `gpuName`. Verify: `node.knob(name)` is not None
   before setting.

2. **Inference `tileSize` is an enumeration.** Wrong: `inf['tileSize'].setValue(512)` - errors. Right: one of
   `None`, `1024`, `2048`, `4096` (e.g. `setValue('1024')`), plus `tileOverlap` as a number. Tiling large
   frames is built in - no hand-made tile tree is needed. Verify: `inf['tileSize'].value()` reads the string
   you set.

3. **`import torch` in Nuke's Python fails** (ModuleNotFoundError) - torch ships only as DLLs in the install
   root (torch.dll, torch_cpu.dll, torch_cuda.dll). Find the bundled PyTorch version from Foundry's release
   notes and trace in a separate venv to match: Nuke 15.0 cannot load 2.x TorchScript; 15.1+ / 16 / 17 take
   `torch==2.1.1+cpu` traces; .cat files from 13.x do not load in 14+. Verify: reload the .pt with
   `torch.jit.load` in the tracing venv, then load the .cat in Nuke.

4. **Cattery package discovery is gated by cat.json.** Wrong: an invented schema (Nuke finds 0 packages), or a
   `minimum_nuke_version_required` that does not match the target (min 15.0 is found in 15.0 and hidden in 14.9;
   min 13.2 also shows in 14.9). Right: copy the installed
   packages' shape - `{"minimum_nuke_version_required": 15.1, "version": 1, "category": "...",
   "description": "...", "cats": [{"filepath": "MyModel.gizmo", "name": "MyModel", "icon": "MyModel.png"}]}` in
   `~/.nuke/Cattery/<Model>/`. `cats[].filepath` may be a gizmo wrapping Inference OR the .cat itself (Nuke
   pastes an Inference node for a .cat). The package is listed only when the running Nuke meets the minimum
   version. Verify: `nukescripts.cattery.discover_packages` lists it in the target version, not by eye. A .cat
   referenced by path in Inference's `modelFile` works without any cat.json.

5. **Setting `modelFile` / `torchScriptFile` blocks Nuke's main thread.** Large models take minutes to load
   and the MCP bridge times out (ECONNRESET) though the load still completes. Right: create and wire every node
   and set the other knobs in one call, set the model file LAST in its own call, and do not kill Nuke while
   CatFileCreator writes. Verify: the .cat exists and Inference reports no error after the load.

6. **`torch.jit.trace` freezes the input resolution, and a different size crashes Nuke** (hard crash, not an
   error). Right: prefer `torch.jit.script`; with trace, Reformat the Inference input to the exact traced size
   and back after. Never use `torch.jit.optimize_for_inference` - on 2.1.1 the saved .pt then fails to load
   ("required keyword attribute 'value' undefined"). Verify: reload the .pt before building the .cat.

7. **Channel names must be predefined Nuke channels.** Custom names (`da.r`, `other.1`) gave "invalid
   map<K, T> key" at runtime. Right: full dot names, comma-separated - `rgba.red,rgba.green,rgba.blue` in,
   `depth.Z` (capital Z) out; spare vessels are default channels such as `forward.u`, `backward.v`,
   `disparityL.x`, `mask.a`. Verify: the name is in `nuke.channels()` and the Inference output channel holds
   data.

8. **Headless runs need `--gpu`.** Under `nuke -t --safe` alone ML nodes report `gpuName: Not available` and
   run on the CPU, so timings (and possibly results) differ from the GUI. Right: `nuke -t --safe --gpu`.
   Verify: read the node's `gpuName` knob.
