# ComfyUI

Provenance: audited 2026-09 in the vfx-agent-toolkit-codex repository; its docs/,
codex/tests/ and codex/recipes/ hold the evidence records and probes named below.

Prefer comfy-cli when artist interaction is unnecessary. Use the UI for mask
painting and similar input. Discover the server URL; Desktop and standalone
launches may use different ports. A CLI installation does not establish model,
node or backend availability.

Distinguish editor workflow JSON from executable API prompt JSON. Inspect node
schemas and required model filenames before queuing. Track the submitted job to
a terminal result and inspect its artifacts. Preserve workflow, seed and relevant
model/node provenance alongside accepted output.

CLI setup records the verified commands and local
smoke-test scope. Audit records missing
ControlNet support and schema/API gaps. The later CLI skill test verified one Gemini
partner image through the local graph, plus template editing/conversion. Hosted
workflow execution was subscription-blocked. Local diffusion model inference
and a complete headless backend installation remain unverified.
