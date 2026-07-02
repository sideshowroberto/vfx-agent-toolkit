---
name: comfyui-workflow-analysis
description: Analyze downloaded ComfyUI workflow JSON files to extract required custom nodes and models, map them to correct install locations, and generate a setup checklist. Use when user shares a workflow JSON, asks "what nodes does this need", "what models does this use", "help me set up this workflow", or "analyze this comfy workflow".
allowed-tools: Read,Write
---

# ComfyUI Workflow Analysis

Reads a workflow JSON and produces a complete setup checklist: custom nodes to install and models to download/place.

---

## When to Use

- User shares a downloaded workflow JSON file
- User asks "what custom nodes does this need?"
- User asks "what models does this workflow use?"
- User wants to get a new workflow running

---

## Instructions

### Step 1 — Read the workflow JSON

Read the file and extract all unique `class_type` values from the nodes array.

### Step 2 — Separate built-in vs custom nodes

**Built-in nodes** (no install needed) include:
`KSampler`, `CLIPTextEncode`, `VAEDecode`, `VAEEncode`, `CheckpointLoaderSimple`, `LoraLoader`, `ControlNetLoader`, `ImageScale`, `SaveImage`, `PreviewImage`, `LoadImage`, `EmptyLatentImage`, `LatentUpscale`, `ConditioningCombine`, `ConditioningSetArea`, `CLIPSetLastLayer`, `UNETLoader`, `DualCLIPLoader`, `VAELoader`, `FluxGuidance`, `ModelSamplingFlux`, `BasicGuider`, `BasicScheduler`, `SamplerCustomAdvanced`, `RandomNoise`, `CFGGuider`

Everything else is likely a **custom node**.

### Step 3 — Map custom nodes to repos

Most follow the pattern `ComfyUI-RepoName` or similar. For each custom node class:
- Identify the likely repo name from the class prefix/naming
- Check if it matches any of the user's already-installed nodes in `D:\COMFYUI\ComfyUI_windows_portable\ComfyUI\custom_nodes\`
- Note whether it needs to be installed via ComfyUI Manager

### Step 4 — Extract model references

Scan node inputs for model filename references (`.safetensors`, `.ckpt`, `.pt`, `.onnx`, `.bin`).
Map each to the correct models subfolder:

| Filename pattern / node type | Destination |
|------------------------------|-------------|
| Checkpoint (SD, SDXL, Flux) | `models/checkpoints/` |
| LoRA | `models/loras/` |
| VAE | `models/vae/` |
| ControlNet | `models/controlnet/` |
| Upscaler | `models/upscale_models/` |
| CLIP / text encoder | `models/text_encoders/` or `models/clip/` |
| UNET / diffusion model | `models/diffusion_models/` or `models/unet/` |
| Embedding | `models/embeddings/` |

Models root: `D:\COMFYUI\ComfyUI_windows_portable\ComfyUI\models\`

### Step 5 — Output a setup checklist

Format the result as:

```
## Workflow: [filename]

### Custom Nodes to Install (via ComfyUI Manager)
- [ ] ComfyUI-ExampleNode — search "ExampleNode" in Manager
- [ ] ...

### Already Installed
- [x] ComfyUI-GGUF (found in custom_nodes/)
- ...

### Models Needed
- [ ] flux1-dev.safetensors → models/checkpoints/
- [ ] ae.safetensors → models/vae/
- ...

### Models Already Present
- [x] (check models/ subfolders against the list)
```

---

## Notes

- ComfyUI Manager is the easiest install path for custom nodes
- If a node repo is unknown, search for the class_type name on GitHub or Civitai
- Model download sources vary — Hugging Face, Civitai, or project GitHub releases
- After installing custom nodes, ComfyUI needs a restart to load them
