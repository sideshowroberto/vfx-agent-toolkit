---
name: comfyui-node-advanced
description: ComfyUI advanced node patterns - MatchType, Autogrow, DynamicCombo, node expansion, MultiType, wildcard inputs. Use when building complex nodes with dynamic inputs, type matching, or node expansion.
---

# ComfyUI Advanced Node Patterns (V3)

V3 provides advanced input patterns for dynamic, type-safe, and flexible node designs.

## MatchType - Generic Type Connections

`MatchType` ensures that inputs and outputs sharing a template have the same type at connection time. Like generics in typed languages.

```python
class PassThrough(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        # Template(template_id, allowed_types=AnyType) - optional type constraint
        template = io.MatchType.Template("T")
        return io.Schema(
            node_id="PassThrough",
            display_name="Pass Through",
            category="utils",
            inputs=[
                io.MatchType.Input("value", template=template),
            ],
            outputs=[
                io.MatchType.Output(template=template, display_name="output"),
            ],
        )

    @classmethod
    def execute(cls, value):
        return io.NodeOutput(value)
```

When the user connects an IMAGE to the input, the output automatically becomes IMAGE type.

### Switch Node Pattern

```python
class Switch(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.MatchType.Template("switch")
        return io.Schema(
            node_id="Switch",
            display_name="Switch",
            category="logic",
            inputs=[
                io.Boolean.Input("switch"),
                io.MatchType.Input("on_false", template=template, lazy=True),
                io.MatchType.Input("on_true", template=template, lazy=True),
            ],
            outputs=[
                io.MatchType.Output(template=template, display_name="output"),
            ],
        )

    @classmethod
    def check_lazy_status(cls, switch, on_false=None, on_true=None):
        if switch and on_true is None:
            return ["on_true"]
        if not switch and on_false is None:
            return ["on_false"]

    @classmethod
    def execute(cls, switch, on_true, on_false):
        return io.NodeOutput(on_true if switch else on_false)
```

## MultiType - Accept Multiple Types

A single input that accepts several different types:

```python
io.MultiType.Input("data",
    types=[io.Image, io.Mask, io.Latent],
    optional=True,
)
```

## Autogrow - Dynamic Growing Inputs

Inputs that automatically add more slots as the user connects to them. Two template modes:

### TemplatePrefix (numbered slots)

```python
class ConcatImages(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="ConcatImages",
            display_name="Concat Images",
            category="image",
            inputs=[
                io.Autogrow.Input("images",
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Image.Input("img"),  # template for each slot
                        prefix="image_",              # slot names: image_0, image_1, ...
                        min=2,                        # minimum visible slots (default 1)
                        max=16,                       # maximum slots (default 10, hard limit 100)
                    ),
                ),
            ],
            outputs=[io.Image.Output("IMAGE")],
        )

    @classmethod
    def execute(cls, images: io.Autogrow.Type):
        # images is a dict: {"image_0": tensor, "image_1": tensor, ...}
        tensors = [v for v in images.values() if v is not None]
        return io.NodeOutput(torch.cat(tensors, dim=0))
```

### TemplateNames (named slots)

```python
io.Autogrow.Input("inputs",
    template=io.Autogrow.TemplateNames(
        input=io.Float.Input("val"),
        names=["red", "green", "blue", "alpha"],  # specific slot names
        min=3,  # first 3 are required
    ),
)
# Creates slots: "red" (required), "green" (required), "blue" (required), "alpha" (optional)
```

**Key behaviors**:
- Widget inputs in template are forced to connection-only (`force_input=True`)
- Slots below `min` are required; above `min` are optional
- Maximum 100 names total

### Calling an Autogrow node from API-format JSON

The sections above are the node-author view. Calling one headless via `POST /prompt` is
where it bites. **Address each slot with a DOT PATH - `<container>.<slot_name>`.**

```json
"7": {
  "class_type": "MiniMaxH3ReferenceToVideo",
  "inputs": {
    "ref_images.ref_image_0": ["6", 0],
    "ref_videos.ref_video_0": ["9", 0],
    "ref_audios.ref_audio_0": ["11", 0]
  }
}
```

Two wrong forms, and the second is genuinely dangerous:

```json
"ref_image_0": ["6", 0]                        // ERRORS - loud, harmless
"ref_images": { "ref_image_0": ["6", 0] }      // SILENTLY IGNORED - dangerous
```

- **Flat slot name** fails loudly with `execute() got an unexpected keyword argument
  'ref_image_0'. Did you mean 'ref_images'?` Easy to spot.
- **Dict value** passes validation, the workflow runs to completion, and the references are
  **dropped without any warning**. The node receives an empty container and generates from
  the text prompt alone. Nothing in the response indicates the references were lost.

**Verified 2026-08-04** on `MiniMaxH3ReferenceToVideo` (ComfyUI v0.30.0). This cost a full
day: two video generations (377s and 1001s) plus a whole model-comparison exercise were
invalidated because the dict form ran cleanly while binding nothing.

**How to prove references actually bound** - "it executed" is NOT evidence. A reference-
conditioned node VAE-encodes its references *before* text encoding, so the load order in
`ComfyUI/user/comfyui.log` is a free assertion:

```
Requested to load <Model>VideoVAE     <- references ARE being encoded
Requested to load <Model>TEModel_
```

If the VAE only appears later (at decode time), the references never bound. Cheap probe:
run the conditioning node alone with no sampler and watch that order - seconds, not minutes.

The same dot-path rule applies when an Autogrow sits inside a DynamicCombo, just with the
combo prefix too (`model.reference_images.image_1`) - see the DynamicCombo section below.

## DynamicCombo - Conditional Inputs

A combo dropdown where each option reveals different sub-inputs:

```python
class ProcessNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="ProcessNode",
            display_name="Process Node",
            category="processing",
            is_output_node=True,
            inputs=[
                io.DynamicCombo.Input("mode", options=[
                    io.DynamicCombo.Option("resize", [
                        io.Int.Input("width", default=512, min=1, max=8192),
                        io.Int.Input("height", default=512, min=1, max=8192),
                    ]),
                    io.DynamicCombo.Option("blur", [
                        io.Float.Input("radius", default=5.0, min=0.1, max=100.0),
                    ]),
                    io.DynamicCombo.Option("sharpen", [
                        io.Float.Input("amount", default=1.0, min=0.0, max=10.0),
                    ]),
                ]),
                io.Image.Input("image"),
            ],
            outputs=[io.Image.Output("IMAGE")],
        )

    @classmethod
    def execute(cls, mode: io.DynamicCombo.Type, image, **kwargs):
        # mode is a dict with the combo value + sub-inputs
        # key for selected option matches the DynamicCombo input ID
        if mode["mode"] == "resize":
            width = mode["width"]
            height = mode["height"]
            # ... resize logic
        return io.NodeOutput(image)
```

**Nested DynamicCombo**:
```python
io.DynamicCombo.Input("outer", options=[
    io.DynamicCombo.Option("option1", [
        io.DynamicCombo.Input("inner", options=[
            io.DynamicCombo.Option("sub1", [io.Float.Input("val")]),
            io.DynamicCombo.Option("sub2", [io.Int.Input("count")]),
        ])
    ]),
])
```

### DynamicCombo params are REQUIRED and invisible in source

A `DynamicCombo` shows up in `/object_info` as type `COMFY_DYNAMICCOMBO_V3`, but it is
**not** declared as a plain `io.<Type>.Input(...)`. Grepping a node's source for
`io.X.Input` therefore misses it entirely, and the omission only surfaces at execution:

```
SaveVideo.execute() missing 1 required positional argument: 'codec'
```

**Pass the option key as a plain string, and its sub-inputs with DOT NOTATION.**

When the chosen option declares no sub-inputs, the bare key is enough:

```json
"13": {
  "class_type": "SaveVideo",
  "inputs": {
    "video": ["12", 0],
    "filename_prefix": "test",
    "format": "auto",
    "codec": "auto"
  }
}
```

When it does declare sub-inputs, prefix each with the combo's input id:

```json
"2": {
  "class_type": "MinimaxHailuo03ReferenceNode",
  "inputs": {
    "model": "MiniMax H3",
    "model.prompt": "...",
    "model.resolution": "768P",
    "model.ratio": "16:9",
    "model.duration": 5,
    "model.reference_images.image_1": ["1", 0],
    "seed": 42,
    "watermark": false
  }
}
```

**Autogrow nested inside a DynamicCombo takes the FULL dot path to each slot** -
`model.<autogrow_id>.<slot_name>`. This is the same dot-path rule as a top-level Autogrow,
just with the combo id prepended - the two are consistent:

```json
"ref_images.ref_image_0": ["6", 0]                 top-level Autogrow
"model.reference_images.image_1": ["1", 0]         Autogrow inside a DynamicCombo
```

A dict value is silently ignored in BOTH positions. See the Autogrow section above for the
log-order check that proves references actually bound.

Passing a dict to the dot-prefixed name (`"model.reference_images": {...}`) is silently
ignored - the node then fails its own emptiness check (`At least one reference image or
video is required`) rather than reporting a binding error, which makes this one slow to
diagnose.

WRONG - a nested dict for the combo itself passes submission validation but dies at
execution with `execute() missing 1 required positional argument: 'model'`:

```json
"model": { "model": "MiniMax H3", "prompt": "...", "resolution": "768P" }
```

Inputs NOT declared inside the selected option stay top-level and are never dot-prefixed
(`seed`, `watermark` above; on Kling nodes `prompt`, `duration`, `generate_audio` are
top-level while Seedance nests the same names under `model.`). Read `/object_info` to see
which is which rather than assuming from another node's shape.

Verified 2026-08-04 on `SaveVideo` and `MinimaxHailuo03ReferenceNode` (ComfyUI v0.30.0).

## Building API-format workflows: validate against /object_info FIRST

**Do not build a workflow graph by reading node source.** The live schema is authoritative
and catches in one call what source-reading misses. This cost a 445-second generation that
had already succeeded at every step except the final save.

```python
import json, urllib.request
graph = json.load(open("workflow_api.json", encoding="utf-8"))
info = json.load(urllib.request.urlopen("http://127.0.0.1:8188/object_info", timeout=90))
for nid, node in graph.items():
    ct = node["class_type"]
    if ct not in info:
        print("node", nid, "class", ct, "NOT REGISTERED"); continue
    spec = info[ct]["input"]
    valid = set(spec.get("required", {})) | set(spec.get("optional", {}))
    missing = set(spec.get("required", {})) - set(node["inputs"])
    for key in node["inputs"]:
        if key not in valid:
            print("node", nid, "unknown input", repr(key))
    if missing:
        print("node", nid, "MISSING required", sorted(missing))
```

Checking for **missing required** inputs matters as much as unknown ones - that is exactly
the `codec` class of failure.

Other API-format traps:
- **UI-only widgets are rejected.** `LoadImage` accepts `image` but not `upload`; `upload`
  exists only in the UI.
- **UI-format JSON cannot run headless.** Graphs containing Get/Set virtual nodes or
  subgraphs only resolve in the frontend - always export API format.
- **Re-running is cheap after a late failure.** ComfyUI caches executed nodes, so fixing a
  final save node and re-queueing returns in seconds rather than re-sampling.

## Node Expansion - Subgraph Injection

Nodes can return a subgraph that replaces themselves during execution:

```python
from comfy_execution.graph_utils import GraphBuilder

class RepeatNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="RepeatNode",
            display_name="Repeat KSampler",
            category="sampling",
            enable_expand=True,
            inputs=[
                io.Model.Input("model"),
                io.Int.Input("repeat_count", default=2, min=1, max=10),
                io.Latent.Input("latent"),
            ],
            outputs=[io.Latent.Output("LATENT")],
        )

    @classmethod
    def execute(cls, model, repeat_count, latent):
        graph = GraphBuilder()
        current_latent = latent
        for i in range(repeat_count):
            sampler = graph.node("KSampler",
                model=model,
                latent_image=current_latent,
                # ... other params
            )
            current_latent = sampler.out(0)
        return io.NodeOutput(current_latent, expand=graph.finalize())
```

**Key rules for node expansion**:
- Set `enable_expand=True` in Schema
- Use `GraphBuilder` to construct subgraphs safely
- Return `io.NodeOutput(output_ref, expand=graph.finalize())`
- Node IDs in subgraph must be deterministic and unique
- Each subnode is cached separately

## Accept All Inputs

Accept arbitrary inputs not defined in the schema:

```python
class FlexibleNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="FlexibleNode",
            display_name="Flexible Node",
            category="utils",
            accept_all_inputs=True,
            inputs=[io.Combo.Input("mode", options=["a", "b"])],
            outputs=[io.String.Output()],
        )

    @classmethod
    def validate_inputs(cls, mode, **kwargs):
        return True  # skip validation for dynamic inputs

    @classmethod
    def execute(cls, mode, **kwargs):
        # kwargs contains all dynamic inputs
        return io.NodeOutput(str(kwargs))
```

## Execution Blocking

Prevent downstream execution conditionally:

```python
class GateNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="GateNode",
            display_name="Gate",
            category="logic",
            inputs=[
                io.Boolean.Input("allow"),
                io.Image.Input("image"),
            ],
            outputs=[io.Image.Output("IMAGE")],
        )

    @classmethod
    def execute(cls, allow, image):
        if not allow:
            return io.NodeOutput(block_execution="Gate is closed")
        return io.NodeOutput(image)
```

## Async Execute

V3 natively supports async execution:

```python
class AsyncNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="AsyncNode",
            display_name="Async Node",
            category="utils",
            inputs=[io.String.Input("url")],
            outputs=[io.String.Output()],
        )

    @classmethod
    async def execute(cls, url):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                text = await response.text()
        return io.NodeOutput(text)
```

## Progress Reporting

Report progress during long operations:

```python
from comfy_api.latest import ComfyAPISync  # sync version; use ComfyAPI + await for async execute

class SlowNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="SlowNode",
            display_name="Slow Node",
            category="utils",
            inputs=[io.Int.Input("steps", default=100)],
            outputs=[io.String.Output()],
        )

    @classmethod
    def execute(cls, steps):
        api = ComfyAPISync()
        for i in range(steps):
            # ... do work ...
            api.execution.set_progress(i + 1, steps)
        return io.NodeOutput("done")
```

## NodeReplace - Migration Between Nodes

Register replacements so old workflows auto-migrate to new nodes:

```python
from typing_extensions import override
from comfy_api.latest import ComfyAPI, ComfyExtension, io

class MyExtension(ComfyExtension):
    @override
    async def on_load(self):
        api = ComfyAPI()
        await api.node_replacement.register(io.NodeReplace(
            new_node_id="MyNewNode_v2",
            old_node_id="MyOldNode",
            old_widget_ids=["width", "height", "mode"],  # positional widget order
            input_mapping=[
                {"new_id": "image_in", "old_id": "image"},     # rename input
                {"new_id": "size", "set_value": 512},           # set fixed value
            ],
            output_mapping=[
                {"new_idx": 0, "old_idx": 0},       # index-based, not name-based
            ],
        ))

    @override
    async def get_node_list(self):
        return [MyNewNodeV2]
```

**InputMap types**:
- `InputMapOldId`: `{"new_id": str, "old_id": str}` - map old input to new
- `InputMapSetValue`: `{"new_id": str, "set_value": Any}` - set fixed value on new
- Dot notation for autogrow inputs: `{"new_id": "images.image0", "old_id": "image1"}`

**OutputMap** (index-based, not name-based):
- `{"new_idx": int, "old_idx": int}` - map old output index to new

**old_widget_ids**: Required because workflow JSON stores widget values by position, not by ID. This list maps positional indexes to input IDs for correct migration.

## ComfyAPI - Runtime API

```python
from comfy_api.latest import ComfyAPI, ComfyAPISync

# In sync execute(): use ComfyAPISync (no await)
api = ComfyAPISync()
api.execution.set_progress(value=50, max_value=100)
api.execution.set_progress(
    value=50, max_value=100,
    node_id=None,                   # optional: defaults to current node
    preview_image=pil_image,        # PIL Image or ImageInput tensor
    ignore_size_limit=False,
)

# In async execute(): use ComfyAPI (with await)
api = ComfyAPI()
await api.execution.set_progress(value=50, max_value=100)

# Node replacement registration (in async on_load)
await api.node_replacement.register(io.NodeReplace(...))
```

## See Also

- `comfyui-node-basics` - Node fundamentals
- `comfyui-node-inputs` - Basic input types
- `comfyui-node-lifecycle` - Execution lifecycle and caching
- `comfyui-node-outputs` - Output types and UI helpers
