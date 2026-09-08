# Source Registry

last_verified: 2026-05-30

Use this registry before making factual claims about Seedance 2.0 platform behavior. Prefer primary public sources, attach a verification date, and mark volatile claims as recheck-required. This file is a claim-boundary map, not a guarantee of access on every product surface or region.

## Evidence Labels

| Label | Meaning | Required wording |
|---|---|---|
| `confirmed` | Directly visible in a primary public source at the verification date. | `Public sources state... as of [date].` |
| `volatile` | Likely to change by surface, account, region, pricing page, or model update. | `Recheck before giving numbers or promises.` |
| `field-observed` | Repeated creator/practitioner pattern but not official platform truth. | `Field observation, not guaranteed platform behavior.` |
| `unverified` | Plausible but not confirmed by a primary source. | `Requires testing or owner confirmation.` |
| `internal` | Repository guidance derived from this skill package. | `Use as workflow guidance, not external fact.` |

## Primary Source Hierarchy

| Topic | Preferred source | Evidence label | Verification note | Claim boundary |
|---|---|---|---|---|
| Core model capabilities | ByteDance Seedance 2.0 official page: https://seed.bytedance.com/en/seedance2_0 | confirmed | Recheck before release notes, API claims, or marketing copy. | Use for broad public capability framing only. |
| Launch capabilities and known limits | ByteDance Seedance 2.0 official launch post: https://seed.bytedance.com/en/blog/seedance-2-0-official-launch | confirmed | Recheck when discussing multimodal references, editing, audio, and platform examples. | Do not turn launch examples into guaranteed behavior on every surface. |
| Model card and paper | arXiv model card: https://arxiv.org/abs/2604.14148 | confirmed | Useful for model-family context and benchmark caveats. | Provider-authored paper; do not use as current commercial access proof. |
| API tutorial and platform docs | BytePlus ModelArk and Volcengine Ark docs: https://docs.byteplus.com/en/docs/ModelArk/2291680, https://www.volcengine.com/docs/82379/1520757?lang=zh, and https://www.volcengine.com/docs/82379/2291680?lang=zh | volatile | Recheck endpoints, request fields, model IDs, task flow, and pricing before procedural API guidance. | API shape may differ by region, account, or release channel. |
| Video generation task lifecycle | Volcengine video-generation tutorial: https://www.volcengine.com/docs/82379/2298881?lang=zh | volatile | Recheck create/query/list/cancel-delete flow, first/last-frame roles, return-last-frame, tools, and file-reference rules before implementation. | Official surface, but fields and account support can change. |
| Model IDs and pricing | Volcengine model list/pricing and BytePlus pricing pages | volatile | Always recheck immediately before quoting numbers or IDs. | Volcengine prices may be cited only with date, currency, model, surface, and caveat; never infer BytePlus pricing from incomplete JS-rendered pages. |
| API-service ecosystem news | Volcengine developer article: https://developer.volcengine.com/articles/7628567056649125942 | volatile | Use as official ecosystem/news evidence for API-service rollout, safety standards, portrait authorization, virtual portraits, and BytePlus overseas-service statements. Recheck docs/console for implementation. | Not an API contract, price table, or entitlement guarantee. |
| BytePlus pricing pages | BytePlus ModelArk pricing docs: https://docs.byteplus.com/en/docs/ModelArk/1099320 | volatile | Recheck live official pages or console before quoting Seedance 2.0 pricing, quotas, or model IDs. | Some pages are JavaScript-rendered in static fetches; do not infer current Seedance 2.0 pricing from incomplete static content. |
| Prompting guide | Volcengine Seedance 2.0 prompt guide: https://www.volcengine.com/docs/82379/2222480?lang=zh | confirmed | Recheck when adding multimodal reference wording or prompt examples. | Prompting advice is official guidance, not a guarantee that every surface exposes every control. |
| First/last frame workflow | Volcengine tutorial and ComfyUI partner docs: https://www.volcengine.com/docs/82379/2298881?lang=zh and https://docs.comfy.org/zh/tutorials/partner-nodes/bytedance/seedance-2-0 | volatile | Volcengine documents first/last-frame roles; ComfyUI uses FLF2V workflow vocabulary. Recheck active surface before using exact fields. | The `FLF2V` label is surface-specific, but first/last-frame capability is documented on Volcengine. |
| Face, portrait, and voice behavior | Active product surface, official policy, and user authorization | volatile | Recheck current surface behavior and authorization context. | Do not infer consent from a file upload. |
| Runway Seedance 2 surface | Runway API and help docs: https://docs.dev.runwayml.com/guides/seedance/ and https://help.runwayml.com/hc/en-us/articles/50488490233363-Creating-with-Seedance-2-0 | volatile | Recheck duration, ratios, audio/reference combination rules, region availability, plan requirements, and SDK support before production use. | Official Runway surface, not a ByteDance/Volcengine API contract. |
| Agent Skills structure | OpenAI Codex Agent Skills docs: https://developers.openai.com/codex/skills, OpenAI Academy plugins/skills explainer: https://openai.com/academy/codex-plugins-and-skills/, OpenAI Codex Plugins docs, and Agent Skills open standard: https://agentskills.io/ | confirmed | Recheck before changing install guidance or root skill layout. | Packaging guidance, not Seedance platform capability. |
| Runway MCP agent surface | Runway MCP announcement: https://runwayml.com/news/mcp | confirmed | Use for agent-surface availability only. | Does not change Seedance model capability; plan and connector access are Runway-specific. |
| Audio-video eval vocabulary | AVBench and VABench papers: https://arxiv.org/abs/2605.24652 and https://openaccess.thecvf.com/content/CVPR2026/papers/Hua_VABench_A_Comprehensive_Benchmark_for_Audio-Video_Generation_CVPR_2026_paper.pdf | field-observed | Use for eval dimensions such as audio-video sync and cross-modal consistency. | Benchmark framing, not product access or official Seedance performance proof. |
| Professional shot language | ASC camera-movement education and production shot-list practice: https://theasc.com/article/shot-craft-camera-movement/ and https://www.studiobinder.com/blog/shot-list-template-free-download/ | field-observed | Use for shot contracts, camera movement, and shot-list fields. | Industry workflow guidance, not Seedance capability proof. |
| Continuity practice | ScreenSkills script-supervisor role: https://www.screenskills.com/job-profiles/browse/film-and-tv-drama/technical/script-supervisor-film-and-tv-drama/ | field-observed | Use for continuity anchors such as wardrobe, props, eyeline, screen direction, and notes. | Role guidance, not platform behavior. |
| Color management and ACES | ACES docs and AMF specification: https://docs.acescentral.com/background/overview/ and https://docs.acescentral.com/amf/specification/ | confirmed | Use for color pipeline vocabulary and handoff metadata. | A prompt can describe a look; it cannot certify ACES compliance. |
| Aspect ratio and delivery containers | DCI, ISDCF, and buyer/platform specs: https://www.dcimovies.com/dci-specification/ and https://registry-page.isdcf.com/ | field-observed | Use for aspect-ratio/container separation and naming caution. | Always follow the contracted delivery spec. |
| Subtitles and captions | Netflix timed text, WebVTT, and accessibility rules: https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements, https://w3c.github.io/webvtt/, and https://www.law.cornell.edu/cfr/text/47/79.1 | volatile | Use for subtitle/SDH/forced-narrative planning and caption-safe framing. Recheck buyer, language, region, and platform requirements. | Delivery requirements vary by buyer, language, region, and platform. |
| Audio loudness and post | ITU BS.1770, EBU R128, ATSC A/85, and buyer sound specs: https://www.itu.int/rec/R-REC-BS.1770, https://tech.ebu.ch/fr/publications/r128, https://www.atsc.org/atsc-documents/a85-techniques-for-establishing-and-maintaining-audio-loudness-for-digital-television/, and https://partnerhelp.netflixstudios.com/hc/en-us/articles/360001794307-Netflix-Sound-Mix-Specifications-Best-Practices-v1-6 | volatile | Use for stems, M&E, sync, loudness, and mix handoff language. Recheck the target buyer or platform spec. | Prompt audio is not a certified final mix. |
| Delivery and QC | SMPTE IMF, DPP specs, Netflix delivery specs, and MovieLabs OMC: https://www.smpte.org/standards/st2067, https://www.thedpp.com/specs/, https://partnerhelp.netflixstudios.com/hc/en-us/sections/10066414335891-Delivery-Specifications, and https://movielabs.com/ontology-for-media-creation/ | volatile | Use for delivery preflight and metadata/versioning guidance. Recheck contracted platform specs before final delivery. | Contracted platform specs override generic guidance. |
| Community practice | Douyin, Bilibili, CSDN, Reddit, Habr, creator notes, workflow screenshots | field-observed | Use only as practitioner guidance. | Mark as non-official; do not state as model guarantee. |
| Localized and mixed-language prompting | Japanese, Korean, Spanish, Russian, and multilingual community guides plus forum observations | field-observed | Recheck public pages before release; use for vocabulary and example structure only. | Code-mixing can clarify safe prompts, but never treat it as official filter behavior or safety evasion. |
| Community prompt corpora | YouMind/OpenLab, public prompt galleries, forum collections | field-observed | Mine structure, timing, vocabulary, and failure patterns only after safety classification. | Do not copy unsafe, IP-sensitive, or real-person prompts into active examples. |
| Repository guidance | README, SKILL.md, references, evals | internal | Keep aligned with source registry and API status. | Workflow guidance, not an external source of platform facts. |

## Required Claim Patterns

When answering platform-status questions, say: `As of 2026-05-30, public official sources describe Seedance 2.0 as supporting text, image, audio, and video inputs, including multimodal references for composition, camera language, motion rhythm, visual effects, and sound. Volcengine documents first/last-frame roles and Runway documents a Seedance 2 surface, but access, pricing, model IDs, upload limits, regions, resolution, audio-combination rules, and authorization behavior remain surface-specific and should be rechecked.`

When answering pricing, quota, upload-limit, model-ID, or regional-availability questions, do not guess. State that those values are volatile and require checking the current official surface.

When answering likeness, portrait, and voice questions, separate three things: technical surface support, rights/authorization, and prompt safety. Do not infer consent from a file upload.

When using community sources, say: `Field observation, not guaranteed platform behavior.`
