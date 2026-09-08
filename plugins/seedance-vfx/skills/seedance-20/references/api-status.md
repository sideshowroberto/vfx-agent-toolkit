# Seedance 2.0 API and Platform Status

last_verified: 2026-05-30
confidence: public-source snapshot as of the verification date; not a guarantee of access, pricing, model IDs, upload limits, authorization behavior, or regional availability on every surface

## Confirmed From Public Sources

- ByteDance's official Seedance 2.0 page describes a unified multimodal audio-video architecture that supports text, image, audio, and video inputs.
- ByteDance's launch post says Seedance 2.0 can use up to 9 images, 3 video clips, 3 audio clips, plus natural-language instructions.
- Official material says references can guide visual composition, camera language, motion rhythm, visual effects, and sound characteristics.
- Official material describes video extension and editing as supported creative workflows.
- Official material describes 15-second multi-shot audio-video output and dual-channel audio.
- The arXiv model card is useful for model-family context, including 4-15 second audio-video generation, native 480p/720p framing in the paper, and a Fast variant.
- Volcengine/Ark docs publish Seedance 2.0 tutorial and video-generation API navigation, including create/query/list/cancel-delete task flows, but exact schemas, prices, model IDs, regions, and limits must be rechecked live.
- Volcengine's model-list page was observed updated on 2026-05-29.
- Volcengine's Seedance 2.0 tutorial was observed updated on 2026-05-29 and still listed `doubao-seedance-2-0-260128` and `doubao-seedance-2-0-fast-260128`.
- Volcengine's general video-generation tutorial was observed updated on 2026-05-29 and is the current first-party place to recheck task lifecycle, first/last-frame roles, return-last-frame, web-search tools, and file/reference combinations.
- Volcengine's prompt guide was observed updated on 2026-05-15 and reinforces multimodal reference prompting.
- Volcengine's pricing page was observed updated on 2026-05-28. Quote Volcengine prices only with surface, date, currency, model/resolution/duration context, and a recheck warning. Keep the stronger no-quote caveat for JavaScript-rendered BytePlus pages that are not live-verified.
- A Volcengine developer-community article says Seedance 2.0 API service is online and mentions portrait/copyright safety standards, face verification, portrait authorization, virtual portrait assets, and BytePlus overseas API service. Treat this as official ecosystem/news evidence, not the API contract.
- Public BytePlus pages may be JavaScript-rendered in static fetches. Do not quote Seedance 2.0 BytePlus pricing or model IDs from such pages without live official verification.
- Runway's official Seedance 2 API guide documents model `seedance2`, 5-15 second duration, image/video/audio references, upload handling through `runway://`, audio-combination rules, and SDK-type lag for `referenceAudio`.
- Partner workflow docs such as ComfyUI expose T2V, R2V, and FLF2V workflow vocabulary, but those docs are surface-specific.
- Recent AV-generation benchmark papers, including AVBench and VABench, are useful for eval vocabulary around audio-video consistency, but they are not Seedance platform-access sources.

## Operational Wording

Use this wording unless newer primary sources say otherwise:

> As of 2026-05-30, public ByteDance sources describe Seedance 2.0 as a unified multimodal audio-video generation model with text, image, audio, and video inputs. Official launch and model-card material says references can include up to 9 images, 3 video clips, and 3 audio clips. Volcengine/Ark and Runway publish current Seedance 2 documentation, but access, model IDs, pricing, file limits, regional availability, resolution, audio-combination rules, and portrait authorization remain surface-specific and must be rechecked before production use.

## Model Naming Rule

- Use `Seedance 2.0` for the official video model line.
- Use `Seedance 2.0 Fast` only when the active surface exposes a Fast variant.
- Use `seedance2` only for Runway's API surface.
- Do not call `Seedance 2.0 Pro` the official video-model name without a current source. Treat it as ambiguous wrapper or community wording.
- Do not confuse `Seed2.0 Pro` or Doubao/Seed general model names with Seedance video generation.

See [`model-name-map.md`](model-name-map.md).

## Claim Boundaries

- Say that API availability, pricing, model IDs, upload limits, entitlement rules, rate limits, and regional availability must be checked against current primary sources.
- Avoid claiming that an API is globally available or unavailable unless a current primary source says so.
- Avoid claiming that face or portrait uploads are universally supported or universally blocked unless a current primary source says so.
- Separate model capability from product-surface behavior. Dreamina/Jimeng, Doubao, Volcengine/Ark, BytePlus/ModelArk, ComfyUI, and third-party wrappers can differ.
- Treat third-party wrapper prices and model aliases as wrapper-specific, not official.

## Known Limit Categories

Official/provider material and field observations point to these areas as fragile:

- detail stability,
- hyper-realism,
- dynamic vitality,
- multi-subject consistency,
- text rendering,
- complex editing,
- audio distortion,
- multi-speaker lip-sync,
- product/logo preservation,
- real-person authorization and surface gating.

## Real-Person, Portrait, and Voice Rule

Real-person face, portrait, and voice workflows require authorization, legal/ethical compliance, and platform-specific support. Do not infer permission from an uploaded asset. Do not help imitate a public figure, private person, celebrity, or voice without a clearly authorized workflow that complies with applicable rules and user consent requirements.

## Primary Sources To Recheck

- https://seed.bytedance.com/en/seedance2_0
- https://seed.bytedance.com/en/blog/seedance-2-0-official-launch
- https://arxiv.org/abs/2604.14148
- https://www.volcengine.com/docs/82379/1330310?redirect=1&lang=zh
- https://www.volcengine.com/docs/82379/1520757?lang=zh
- https://www.volcengine.com/docs/82379/2291680?lang=zh
- https://www.volcengine.com/docs/82379/2298881?lang=zh
- https://www.volcengine.com/docs/82379/2222480?lang=zh
- https://www.volcengine.com/docs/82379/1544106?lang=zh
- https://developer.volcengine.com/articles/7628567056649125942
- https://docs.byteplus.com/en/docs/ModelArk/2291680
- https://docs.byteplus.com/en/docs/ModelArk/1099320
- https://docs.dev.runwayml.com/guides/seedance/
- https://help.runwayml.com/hc/en-us/articles/50488490233363-Creating-with-Seedance-2-0
- https://docs.comfy.org/zh/tutorials/partner-nodes/bytedance/seedance-2-0
- https://arxiv.org/abs/2605.24652
- https://openaccess.thecvf.com/content/CVPR2026/papers/Hua_VABench_A_Comprehensive_Benchmark_for_Audio-Video_Generation_CVPR_2026_paper.pdf
