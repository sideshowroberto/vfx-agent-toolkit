# API Workflow

last_verified: 2026-05-30

Use this reference for Seedance 2.0 operational planning on Volcengine, BytePlus, Runway, or wrappers. It is not a static API contract. Always recheck the active provider docs or console before implementation.

## Surface Gate

| Surface | Use when | Must recheck |
|---|---|---|
| Volcengine Ark | China-facing official Ark workflows, model IDs, task lifecycle, first/last-frame roles, `return_last_frame`, web-search tools, and virtual portrait assets. | model ID, region, entitlement, schema, pricing, duration, resolution, face/reference policy |
| BytePlus ModelArk | International BytePlus docs or console workflows. | JS-rendered pricing/model pages, account access, region, exact model ID, upload/file rules |
| Runway | Runway web/API/MCP workflow with `seedance2`, hosted uploads, and Runway plan/region constraints. | duration, ratios, plan, region, SDK field support, audio-reference combination rules |
| Wrapper APIs | Fast prototyping through a third-party provider. | whether names, prices, moderation, duration, or face support are wrapper-specific |

## Async Task Lifecycle

1. Create the task with source-dated model ID, prompt, duration, ratio/size, resolution, and reference files.
2. Store task ID, provider, request date, model ID, and prompt version.
3. Poll or use SDK wait helpers until completed or failed.
4. Retrieve output URL(s), optional last frame, logs/errors, and moderation/failure reason when provided.
5. Save output plus metadata for repeatability.
6. Cancel, delete, or list tasks only through the active provider's current docs.

## Request Checklist

- Prompt says one visible beat, one camera move, physical light, sound intent, and constraints.
- Mode is explicit: T2V, I2V, V2V, R2V, FLF2V, edit, or extend.
- Reference roles are explicit and legal: first frame, last frame, identity, product, motion, camera, timing, audio, or style.
- Audio references are paired with a text prompt and a valid image/video reference when the surface requires that combination.
- First/last-frame requests do not silently mix incompatible video/audio reference modes unless the active docs allow it.
- Real-person, face, portrait, and voice inputs have authorization and surface support.
- Pricing, duration, resolution, region, quotas, and model IDs have a verification date.

## Provider Notes

Volcengine docs are the current source for `doubao-seedance-2-0-260128`, `doubao-seedance-2-0-fast-260128`, first/last-frame roles, and Ark task flow. Quote prices only with date and caveat.

Runway docs are the current source for Runway's `seedance2` API surface, `runway://` uploads, duration, reference-count rules, and SDK caveats. Do not copy Runway field names into Volcengine examples or vice versa.

BytePlus pages can be JavaScript-rendered. Do not infer live pricing or model IDs from incomplete static fetches.

## Error and Risk Playbook

| Symptom | Likely cause | First repair |
|---|---|---|
| 403 or unavailable model | region, plan, entitlement, vendor licensing, or provider gate | check surface-specific access docs and account console |
| audio-only request fails | active surface requires image/video plus prompt with audio | add valid visual reference and state audio role |
| first/last frame rejected | incompatible mode mix or wrong role fields | use provider's first/last-frame field names and remove video/audio refs if required |
| face/portrait upload blocked | real-person policy, verification, or asset-library requirement | use authorized virtual portrait path or original character rewrite |
| output drifts after extension | weak last-frame continuity or too many changed variables | use returned last frame as next first frame and change one variable |
| price estimate wrong | stale pricing page or wrapper-specific billing | recheck provider pricing page/console before quoting |

## Production Readiness

Keep a run ledger with: provider, model ID, prompt, mode, references, duration, resolution, generated audio flag, task ID, output URL, last frame, verification date, and failure notes. This makes prompt repair possible and prevents stale source claims from leaking into user-facing guidance.
