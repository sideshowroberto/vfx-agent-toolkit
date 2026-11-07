---
name: comfy-cli-skills
description: Installs comfy-cli's bundled agent skills into any harness and sets the zero-cost validate gate and credit audit for paid ComfyUI runs. Use when setting up comfy-cli, when comfy skills are missing, or before a workflow run that bills partner-node credits.
---

# comfy-cli skills

comfy-cli (Comfy-Org, GPL-3.0) ships its own agent skills for driving ComfyUI
from an agent: `comfy` (run and edit workflows), `comfy-build`, `comfy-debug`,
`comfy-deploy`, `comfy-director` (multi-shot narrative) and `comfy-relay` (media
presentation). They are not vendored in this MIT toolkit; install them from the
CLI so every harness reads the same text.

## Install

```sh
pip install --upgrade comfy-cli
comfy --version
comfy skills install
```

`comfy skills install` needs comfy-cli 1.20 or newer; older builds expose the
same step inside the `comfy setup` wizard. Afterwards confirm the six `comfy*`
entries appear in the harness's skill catalog (restart the client if it caches).
The skills document a 1.20 command baseline: on an older CLI, read `comfy --help`
before using a command they name.

## House rules around a PAID run

Partner nodes (Kling, Seedance, MiniMax, Veo, Gemini image) bill credits the
moment a graph is accepted. Two zero-cost steps come first, every time:

1. **Validate, then print without posting.** `comfy validate --workflow api.json
   --where local` must be clean, then `comfy run --workflow api.json
   --print-prompt --json` logs the exact graph. This catches wrong input names
   and DynamicCombo dot-path mistakes for free. "Clean" means `valid=true`,
   `error_count=0` and every warning READ, not merely counted. Known false
   positive (comfy validate 1.11.1): an `edge_type_mismatch` warning when the
   expected input is a type UNION that already contains the produced type
   (e.g. "expects MESH,FILE_3D_GLB,...,FILE_3D but X produces FILE_3D_GLB") -
   the validator compares the whole comma-joined union as one string. That one
   warning is acceptable; any other warning stops the run. The validator can
   also be wrong the other way (pass a graph the server rejects), so the real
   pass is the expected output file on disk after the run, never the status.
2. **Read the balance before and after.** `GET https://api.comfy.org/customers/balance`
   with header `X-API-KEY: <key>`; `effective_balance_micros` is US CENTS despite the name:
   value / 100 = USD, USD x 211 = credits (docs.comfy.org billing reference; comfy-cli PR #926).
   Reconcile the delta against the price badges. A larger drop than predicted
   means stop and find what else billed. The ledger settles a few seconds after
   the run: an AFTER read taken in the same command as `comfy run --wait` can
   return the BEFORE value exactly. If the delta is zero for a run with a
   non-zero price badge, re-read after about 30 s before concluding anything
   (obs 269). On a shared account the delta can include other people's jobs:
   read the billing activity feed before blaming your run.

Submit with `comfy run --workflow api.json --wait --json --timeout 600`. Feed the
workflow's API-format export; UI-format graphs with Get/Set virtual nodes or
subgraphs only resolve in the frontend and cannot run headless. Keep the API key
in the environment (`COMFY_API_KEY`), never in a workflow file or a chat message.

## Native 3D template nodes are browser-only for saving

`Save3DAdvanced` and `Preview3DAdvanced` (the bundled native 3D templates,
e.g. Trellis2 image-to-model) require a `viewport_state` input of type
`LOAD_3D` that only the browser supplies, and they write nothing headless
even when the job reports `completed`. Swap in `SaveGLB` instead (mesh or
`FILE_3D` in, `filename_prefix`) - it needs no viewport state and writes the
file. Verify any headless 3D-template run by checking the outputs list for
the expected file extension; `ok: true` alone is not proof anything was
written.

## UI-to-API conversion can drop widget values on native 3D nodes

`comfy run` converts a UI-format workflow client-side, but on the native 3D
nodes some combo/int widgets arrive wrong: Trellis2UpsampleStage.target_resolution
came through as the string "1536" and the width of Preview3DAdvanced and
Save3DAdvanced as "" (four shape_mismatch errors). Fix: take the API prompt
from the run's `prompt_preview` event, patch the values, and submit that API
file instead of the UI file. Validate it with `comfy validate --where local`
before the run.

## Checks the validator cannot make (obs 157, 223, 68)

`comfy validate` only knows the constraints it is fed. `scripts/comfy_gate.py` enforces the checks below: run `pre` on the workflow before a paid run and `post` on the saved `comfy run --wait --json` output after it. Its limits table is stamped with the ComfyUI version it was read from.

- **Partner-node limits live in the node's execute code, not object_info.**
  Output pixel caps (Seedream 5.0 Pro: 4.19 MP on ComfyUI 0.37, 4.62 MP on 0.43,
  while its width/height ranges allow more; the limits move between versions) and reference-image aspect ranges (for
  example 1:3 to 3:1 on one version, 1:16 to 16:1 on the next) pass validate and fail at execution. Check every partner
  node's size and every reference image's aspect against the cap before submit.
- **One paid partner node per prompt.** ComfyUI aborts the whole prompt at the
  first node error, so one bad size cancels the other paid node. A failed run
  can still exit 0; judge by the envelope's `ok` and the files on disk.
- **Read the `data` object of the validate envelope** (`data.valid`,
  `data.error_count`), not the top level.
- **Upload inputs to the TOP of the input folder.** LoadImage and LoadVideo
  option lists hold only top-level files; a subfolder path fails validate as
  `unknown_enum_value`. Use unique names and read back by hash.
- **"completed" is not a result.** The server drops every output node that
  depends on an invalid node and still runs the rest. After a run, read the
  run's `queued` event: `validation_warnings` must be empty or explained, the
  output node the run exists to produce (SaveImage, SaveVideo, SaveGLB) must be
  in `executed_node_ids`, and the file must exist. A template saved before a
  ComfyUI upgrade can be missing newly required inputs; diff its node inputs
  against `/object_info` before the first run.
- **Autogrow input shape is node-specific.** Some nodes want one flattened key
  per slot, others a nested dict (`"ref_images": {"ref_image0": ["15", 0]}`),
  and the validator's hint can be wrong. When a validated graph dies at
  runtime with an unexpected-keyword error, read the node's `execute()`
  signature in `comfy_extras/`; it is the ground truth for argument shape.

## Long local batches (obs 56)

Design so any single process (the agent, the server, the GPU) can die at any
second and the only loss is the clip in flight.

- Submit in small chunks; copy and probe each output as it lands. Never batch
  the read-backs at the end.
- Derive resumption from what is on disk (the missing list), tolerant of
  partial chunks, not from a plan.
- Record GPU telemetry beside the job
  (`nvidia-smi --query-gpu=... -l 5` to a CSV) so a fault leaves evidence.
- If the card runs at its power limit, gate on temperature between gens with a
  cooldown, and ask the operator for a lower power limit. Breaks change the
  duty cycle; the cap changes the peaks. Failure signatures: see comfy-debug.
