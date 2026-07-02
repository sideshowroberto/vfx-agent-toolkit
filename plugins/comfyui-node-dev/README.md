# comfyui-node-dev

Claude Code plugin for ComfyUI custom node development, centered on the modern **V3 API** (`io.ComfyNode`, `io.Schema`, `ComfyExtension`).

## Skills

| Skill | Covers |
|---|---|
| `comfyui-node-basics` | V3 node structure, Schema, registration, V3 vs V1 |
| `comfyui-node-datatypes` | IMAGE / LATENT / MASK / CONDITIONING / model / audio / video / 3D types, tensor shapes, custom types |
| `comfyui-node-inputs` | Widget inputs (INT, FLOAT, STRING, COMBO...), hidden inputs, optional and lazy inputs, force_input |
| `comfyui-node-outputs` | NodeOutput, UI previews (image/mask/audio/video/text/3D), saving files |
| `comfyui-node-lifecycle` | Execution order, caching (fingerprint_inputs), validation, lazy evaluation, list processing |
| `comfyui-node-advanced` | MatchType, MultiType, Autogrow, DynamicCombo, node expansion, async execute, NodeReplace |
| `comfyui-node-frontend` | JavaScript extensions: hooks, custom widgets, sidebar tabs, commands, settings, toasts, dialogs |
| `comfyui-node-migration` | V1 to V3 migration guide with full property and input type mapping |
| `comfyui-node-packaging` | Project structure, __init__.py, requirements.txt, pyproject.toml, registry publishing |

## Install

Install `claude-vfx-base` first, then this plugin. Skills load on demand when you work on ComfyUI custom node code.

No MCP server or external tools required - these are pure knowledge skills.
