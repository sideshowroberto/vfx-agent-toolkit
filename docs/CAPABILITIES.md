# Capabilities index (public toolkit)

GENERATED 2026-11-09 by `ClaudeCode/scripts/gen_capabilities.py` from plugins/registry.json, the skill and agent files, .mcp.json and the script folders. Do not edit; it is rewritten on every /sync-plugins. Registry 2.0.4, updated 2026-11-08.

**How to use it:** ask your agent "what can we do for <task>?" - it should read this file and name the skill, agent, tool or script to reach for. Each line is: name, then what it does and the phrases that trigger it.

## Skills, by plugin

### vfx-core (v2.11.0, public)

Foundation package - install first. Cross-application skills and agents: search, documentation, testing, Python, planning, skill/agent creation, git safety guardrails, and session wrap-up. Registers core MCP servers (brave-search, context7, desktop-commander).

MCP servers: `brave-search`, `context7`, `desktop-commander`

- **skill-creation-update** [scripts] - Writes, updates and validates Claude Code skills (SKILL.md) to the house standard - one-line YAML description, no retired top-level keys, traps-first body under 500 lines, retirement outside .claude/. Use when creating a skill, fixing or migrating an old-format one, or checking skills before a sync.
- **development-management** - Runs Specification-Driven Development (spec-kit) workflows - agent creation, constitutional governance, roadmaps, specs and validation. Use when creating or auditing agents, writing a constitution, or validating compliance.
- **brave-search** [scripts] - Researches VFX topics with Brave Search - MCP web search for filtered URL lists, an LLM Context script for deep research with extracted page content, and image search for references. Use when searching for tutorials, docs, errors, plugins or software updates.
- **grill-me** - Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
- **gap-check** - Audits Claude's own knowledge gaps against a settled plan before building - sorts confident from guessed, researches public gaps, and lists unknowns for the user. Use after /grill-me, before a build session, or on 'gap-check' or 'check your assumptions'.
- **vfx-plan** - Plans complex VFX builds by choosing Iterative, Spec-Driven or Safety-First mode, running an adversarial plan review and writing an actionable brief. Use on "help me plan" or "vfx plan", or before any multi-file or multi-system build.
- **git-guardrails-claude-code** [scripts] - Sets up a Claude Code PreToolUse hook that blocks destructive git commands (push, reset --hard, clean -f, branch -D, checkout/restore .) before they run, with a Python hook that fails closed. Use when the user wants git safety hooks or to block git push/reset in Claude Code.
- **wrap-session** - Runs the end-of-session wrap-up before clearing context - saves durable facts to memory, folds gotchas into skills, writes the session log and a handoff plan, cleans temp files. Use before /clear, when context runs low, or on "wrap up this session".
- **qwen-delegate** [scripts] - Delegates tasks to the local Qwen model on Ollama so file content stays on the machine and out of Claude's context. Use for "ask Qwen" or "do this locally", NDA-safe file analysis, large-file summaries, boilerplate and BlinkScript drafts.
- **task-observer** [scripts] - Logs skill lessons (user corrections, broken rules, better workflows) to the observation log as they happen; applied only after owner review. Use when a skill is corrected, a documented rule fails, a better workflow emerges, or for "observation log" and "skill review". Session-start status comes from the SessionStart hook.
- **youtube-transcript** [scripts] - Retrieve available YouTube captions with timestamps and provenance, or analyze a video from its transcript. Use for YouTube links and transcript requests; this does not watch video frames or transcribe uncaptained audio.
- **vfx-research** - Research VFX application APIs, errors, workflow integrations, and library examples using Brave Search and Context7. Use for Blender, Nuke, Houdini, Unreal, ComfyUI, and related development questions that need external evidence.
- **vfx-workflow** - Apply this toolkit's audited application lessons when scripting DCC scenes, running ComfyUI workflows, or preparing cross-application VFX handoffs. Use for execution and integration work; use vfx-research for documentation lookup.
- **loop-gauntlet** [scripts] - Runs a build-until-it-matches loop in a DCC - an agent rebuilds a scene from reference images, scoring renders against a human-authored rubric until a stop rule fires. Use for 'iterate until it matches', Blender set rebuilds from refs, or writing or judging such a loop prompt.
- **agent: search-specialist** - Expert VFX research specialist using Brave Search API for technical documentation, tutorials, problem-solving, and industry intelligence across Unreal Engine, Blender, Houdini, Nuke, and ComfyUI
- **agent: documentation-specialist** - Index-driven documentation updates for VFX application projects. Reads DOCUMENTATION_INDEX.md to understand structure, maintains consistency across related files, updates progress trackers, and creates session summaries. Use with "update documentation," "document session," or "index-driven update.
- **agent: testing-specialist** - Testing and validating Python scripts, skill scripts, and agent outputs. Use when requests include "test", "validate", "verify", "check", or "pytest". Validates JSON outputs, error handling, script independence, and generates test reports. Proactively invoked after refactoring to ensure functionality.
- **agent: python-specialist** - Python specialist for systematic multi-file work. Use when applying agent-skill templates ({{PLACEHOLDER}} substitution), batch search/replace or migrating code patterns across files, parameterizing per-asset scripts into one generic script, adding type hints (mypy strict, Protocols, TypedDict), converting I/O-bound code to async, vectorizing pandas/numpy, or building pytest suites (fixtures, parametrize, mocks).

### nuke-vfx (v1.2.0, public)

Nuke compositing pipeline: node graphs, BlinkScript, Cattery AI inference, Python scripting, and tiling tool.

MCP servers: `nuke`
Requires: vfx-core

- **nuke-blinkscript** - Verified BlinkScript traps in Nuke 17 - kernelSource.setValue silently keeps the default kernel, a compile error in the GUI raises a modal dialog that wedges the MCP bridge, param knobs are Kernel_param, eAccessPoint takes no coordinates, eAccessRanged2D without setRange segfaults. Use when writing, loading or debugging a BlinkScript or .blink kernel from Python or the MCP.
- **nuke-particle-blinkscript** - Verified ParticleBlinkScript and procedural-particle traps in Nuke - loads kernels via kernelFile + loadKernelFile and makes no param knobs headless, bundled Particle* gizmo params have no kernel prefix (paDirection), ParticleEmitter takes emit geo on input 1, image y points up. Use for custom Nuke particles, Particle* gizmos, or BlinkScript snow, embers, dust or sparks overlays.
- **nuke-cattery-inference** - Verified Cattery traps in Nuke 17 - CatFileCreator knob is torchScriptFile (capital S), Inference tileSize only takes None/1024/2048/4096 (512 errors), torch is not importable from Nuke Python, cat.json minimum_nuke_version_required gates discovery, setting modelFile blocks the bridge. Use when tracing a PyTorch model for Nuke, building a .cat, installing a Cattery package or setting up an Inference node.
- **nuke-node-tree-patterns** - Verified patterns for building Nuke node trees from Python - what auto-connects, cropping with Reformat 'to box', blending overlapping pre-masked tiles with an Expression mask, Premult and a plus Merge. Use when a script must wire, position or blend generated nodes, or for tile-and-blend tools.
- **nuke-python-scripting** [scripts] - Traps for scripting Nuke through the MCP bridge - Roto shapes via nuke.rotopaint (animated points, subtract shapes), Merge2 on alpha-only channels, sampling per frame, tuple kwargs corrupting nuke.views(), headless -t, version-up. Use before writing nuke Python, scripted Roto, or a bridge read-back.

### houdini-vfx (v1.3.0, public)

Houdini VFX pipeline: procedural generation, USD/Solaris, VEX, Python automation, HDA creation.

MCP servers: `houdini`
Requires: vfx-core

- **houdini-hda-creation** - Verified traps for authoring and versioning Houdini Digital Assets (HDAs): version pinning, int-menu storage, delivery read-back, in-place updates. Use when building, versioning or updating an HDA, or comparing two versions of one.
- **houdini-python-automation** [scripts] - Verified traps for scripting Houdini with hou/hython: ROP frame ranges, object_merge transforms, fake export formats, spare parms, Python SOP code, display-node read-back. Use when scripting Houdini, exporting geometry from hython, or verifying a scripted build.
- **houdini-solaris-usd** [scripts] - Verified traps for Solaris, Karma and USD export in Houdini: how light and camera values land on the stage, time samples, instance proxies, loose points, GeomSubsets, savestyle. Use when authoring or checking a LOP stage, Karma lights, or a USD export.
- **houdini-vex-programming** - Verified Houdini VEX traps for wrangles - find() return value, deferred set*attrib writes, empty group patterns, nearpoints self-hits, stale chs() after spare parms, bare globals from Python. Use when writing or debugging a wrangle whose result looks wrong with a clean cook.

### unreal-vfx (v2.3.0, public)

Unreal Engine 5.8 VFX pipeline via the native UE MCP (ModelContextProtocol plugin + VibeUE toolsets): Blueprint automation, PCG, actor operations, Sequencer, Python scripting.

MCP servers: `ue58-mcp`
Requires: vfx-core

- **unreal-blueprint-automation** - Verified UE 5.8 Blueprint Python traps - bp.simple_construction_script and KismetSystemLibrary do not exist (use VibeUE BlueprintService), variables from add_member_variable are not instance-editable until set_blueprint_variable_instance_editable, EdGraphPinType(...) resets the MCP. Use when creating a Blueprint, adding components or variables, or setting per-instance values.
- **unreal-pcg-automation** - Verified UE 5.8 PCG Python traps - add_edge with a wrong pin label adds no edge and raises nothing, pin.label is protected (read it via properties), mesh entries ARE settable but descriptor needs get_editor_property, count instances on the volume ISM. Use when wiring PCG graph nodes, setting Static Mesh Spawner meshes, or checking what a PCG graph generated.
- **unreal-project-preflight** [scripts] - Checks and batch-fixes the Unreal project prerequisites a plan needs (plugins, project settings, editor config) as Step 0 before building. Use once an Unreal plan is approved, before MegaPlants, PCG, MRQ or ImagePlate work, or when a class, node or plugin is missing.
- **unreal-sequencer-automation** - Verified UE 5.8 Sequencer Python traps - add_key(FrameNumber(n)) keys DISPLAY-rate frame n (not ticks), get_channel_by_name does not exist, section.cast raises TypeError, cut cameras compare by guid, reads over MCP need a scrub first, ImagePlate is off by default. Use when keying channels, adding camera cuts, animating a camera property, or reading a Level Sequence back.
- **agent: unreal-blueprint-specialist** - Expert in automating Unreal Engine Blueprint creation and compilation using Silent Execution pattern
- **agent: unreal-pcg-specialist** - Expert in Unreal Engine PCG system for procedural terrain, vegetation, and asset placement with Python automation

### blender-vfx (v2.1.0, public)

Blender VFX pipeline via the official Blender MCP (blender.org): modeling, animation, materials, geometry nodes, physics, rendering, sculpting, grease pencil, and ControlNet pass rendering for AI generation.

MCP servers: `blender`
Requires: vfx-core

- **blender-addon-development** - Verified Blender 4.2+/5.1 add-on and extension traps - bl_info-only zips fail extension validate without blender_manifest.toml, assignment-style bpy.props register silently and do not exist, BLENDER_EEVEE_NEXT raises TypeError. Use when writing or packaging a Blender add-on, extension, operator or panel.
- **blender-animation** - Keyframe animation, rigging, constraints, and armatures in Blender. Use for animation, rigging, camera movement, or when user mentions "animate," "keyframe," "rig," or "armature.
- **blender-api-compatibility** - Diagnoses and migrates Blender Python API breakage across versions 4.2 to 5.1+ (EEVEE_NEXT, renamed modifier types and BSDF inputs, VSE strips). Use when a bpy script errors on a newer Blender, or for breaking changes and migration.
- **blender-compositing** - Compositor nodes, post-processing, and color grading in Blender. Use for compositing workflows, render pass integration, post-processing, color correction, or when user mentions "compositor," "post-process," "color grade," or "render passes.
- **blender-geometry-nodes** - Procedural modeling using Geometry Nodes in Blender. Use for scattering systems, node trees, parametric design, or when user mentions "procedural," "geometry nodes," "scattering," or "instances.
- **blender-grease-pencil** - Verified Grease Pencil v3 traps on Blender 4.3+/5.1 - legacy frame.strokes, points.add, line_width and GP_* modifier ids raise errors, and Line Art silently makes 0 strokes without target layer, material and camera. Use when scripting Grease Pencil strokes, GP modifiers or Line Art.
- **blender-materials-shaders** - Creates Blender shader node trees, PBR materials and procedural textures, with EEVEE_NEXT and Cycles compatibility notes. Use for material creation, shader setups, Principled BSDF inputs, or procedural texturing of parametric geometry.
- **blender-physics-simulation** - Verified Blender 5.1 physics traps - fluid domains default to REPLAY so bake_all writes 1 frame, rigid bodies read wrong unless frames step in order or are baked, obj.collision is None without a COLLISION modifier, particles exist only on the evaluated object, free plus re-bake in one call crashed the GUI. Use when scripting or baking fluid, smoke, rigid body, cloth or particles.
- **blender-rendering** - EEVEE_NEXT and Cycles rendering, lighting, and render optimization in Blender. Use for rendering setup, lighting, render settings, or when user mentions "render," "lighting," "EEVEE," "Cycles," or "materials.
- **blender-sculpting** - Verified Blender 5.1 sculpting traps - setting Multires levels clamps to 0 (use multires_subdivide), the sculpt mask is the .sculpt_mask point attribute (not a vertex group, not sculpt_mask), shading id is MATERIAL, edge-scan smoothing stalls big grids. Use when scripting Multires, sculpt masks or terrain displacement.
- **blender-controlnet-passes** [scripts] - Renders ControlNet conditioning passes from a Blender scene for AI image and video generation - grey clay, normalized depth, cryptomatte EXR, optional wireframe. Use when preparing depth, edge or clay inputs for video models, or crypto mattes for comp.

### comfyui-vfx (v2.3.5, public)

ComfyUI pipeline via the ComfyUI MCP and Comfy CLI, with optional ComfyUI_FL-MCP for live canvas operations: workflow analysis, node/model requirements mapping, and headless generation guidance, plus the previs-to-photoreal anchor keyframe recipe for reference-guided video generation.

MCP servers: `comfyui`
Requires: vfx-core

- **comfyui-workflow-analysis** - Analyzes a downloaded ComfyUI workflow JSON to list required custom nodes and models, install locations and a setup checklist. Use when the user shares a workflow JSON or asks 'what nodes does this need' or 'help me set up this workflow'.
- **previs-anchor-keyframes** - Generates photoreal anchor keyframes from CG previs for reference-guided video models such as Seedance - previs shading, frame choice, pose reference sets. Use for "anchor keyframes", "previs to photoreal video", or generations that ignore the CG pose.
- **comfy-cli-skills** [scripts] - Installs comfy-cli's bundled agent skills into any harness and sets the zero-cost validate gate and credit audit for paid ComfyUI runs. Use when setting up comfy-cli, when comfy skills are missing, or before a workflow run that bills partner-node credits.

### comfyui-node-dev (v1.1.3, public)

ComfyUI custom node development: V3 API node structure, schemas, datatypes, inputs/outputs, execution lifecycle, frontend extensions, V1-to-V3 migration, and packaging/publishing.
Requires: vfx-core

- **comfyui-node-basics** - ComfyUI custom node fundamentals - V3 node structure, Schema, inputs/outputs, registration. Use when creating new ComfyUI custom nodes, defining node classes, or setting up a custom node project.
- **comfyui-node-advanced** - ComfyUI advanced node patterns - MatchType, Autogrow, DynamicCombo, node expansion, MultiType, wildcard inputs. Use when building complex nodes with dynamic inputs, type matching, or node expansion.
- **comfyui-node-datatypes** - ComfyUI data types - IMAGE, LATENT, MASK, CONDITIONING, MODEL, CLIP, VAE, AUDIO, VIDEO, 3D types, widget types, and custom types. Use when working with ComfyUI tensors, model types, or defining input/output data types.
- **comfyui-node-inputs** - ComfyUI node input types - INT, FLOAT, STRING, BOOLEAN, COMBO widgets, hidden inputs, optional inputs, lazy inputs, force_input. Use when configuring node inputs, adding widgets, or customizing input behavior.
- **comfyui-node-outputs** - ComfyUI node output types - NodeOutput, UI outputs, PreviewImage, PreviewMask, SavedImages, PreviewAudio, PreviewText, PreviewVideo. Use when returning results from nodes, displaying previews, or saving output files.
- **comfyui-node-lifecycle** - Explains the ComfyUI custom-node execution lifecycle - caching, fingerprint_inputs/IS_CHANGED, validate_inputs, check_lazy_status, execution order. Use when debugging node execution, controlling caching, or adding input validation.
- **comfyui-node-frontend** - ComfyUI frontend JavaScript extensions - hooks, widgets, sidebar tabs, commands, settings, toasts, dialogs. Use when adding UI features to custom nodes, creating custom widgets, or extending the ComfyUI frontend.
- **comfyui-node-migration** - ComfyUI V1 to V3 node migration - converting legacy nodes to the V3 API. Use when migrating existing custom nodes from V1 to V3, understanding differences between API versions, or modernizing node code.
- **comfyui-node-packaging** - ComfyUI custom node project structure - directory layout, __init__.py, registration, requirements.txt, publishing, WEB_DIRECTORY. Use when setting up a new custom node project, packaging nodes, or publishing to the registry.

### maya-vfx (v1.0.5, public)

Maya pipeline via MCP: scene control, geometry creation, materials (Arnold/USD), transforms, and FBX import/export.

MCP servers: `maya`
Requires: vfx-core

- **maya-scene** - Queries and edits a live Maya scene via the MCP commandPort - objects, transforms, hierarchy, attributes, selection, FBX import/export. Use for listing scene contents, creating geometry, parenting, setting transforms or exporting FBX from Maya.
- **maya-materials** - Creates and assigns Maya materials via MCP - Arnold aiStandardSurface, Lambert, Blinn and USD Preview Surface. Use for shader creation, texture assignment, assigning materials to geometry or look dev in Maya.
- **agent: maya-specialist** - Maya scene control, rigging, modeling, and animation automation via MCP. Auto-triggers on .ma/.mb files, maya.cmds, pymel, rigging, blend shapes, joints, and deformers. Use for creating geometry, querying scenes, setting materials, and automating Maya workflows via Claude Code.

### magnific-vfx (v1.1.5, public)

Magnific AI generation via MCP: image generation with model selection and references, local file upload/download pipelines, and video generation.

MCP servers: `magnific`
Requires: vfx-core

- **magnific-image-gen** - Generates images with the Magnific MCP (default image tool, Nano Banana 2) - concept art, product shots, references, variations and folders; no upscaling. Use for 'generate image', 'generate refs', 'concept art', 'nb2', 'nano banana' or 'magnific folder' requests.
- **magnific-local-upload** - Uploads local images to Magnific as generation references, moves them into folders, and downloads outputs to a local path. Use when using local photos as references, batch uploading a directory, or saving Magnific results to a local folder.
- **magnific-video-gen** - Generates video through the Magnific MCP - Seedance, Kling and Veo models, animating stills, start/end keyframes, camera motion, audio/lipsync and multishot. Use for 'magnific video', 'animate this image' or 'video from still'.

### seedance-vfx (v1.1.0, public)

Seedance 2.0 video generation direction: prompt writing, camera, lighting, motion, characters, style, VFX, troubleshooting, and production recipes.
Requires: vfx-core

- **seedance-20** - This skill should be used when directing Seedance 2.0 T2V, I2V, V2V, R2V, audio, safety, or API work.
- **seedance-filter** - This skill should be used when a Seedance 2.0 prompt is blocked, rejected, silently degraded, or likely to trigger a content filter; or when the user asks for a safer rewrite without losing the creative intent.
- **seedance-copyright** - This skill should be used when a Seedance 2.0 prompt mentions named characters, franchises, studios, celebrities, public figures, private people, brand logos, copyrighted scenes, songs, voices, or real-person likeness workflows and needs an IP-safe rewrite.
- **seedance-antislop** - This skill should be used when a Seedance 2.0 prompt contains generic AI filler, hollow superlatives, vague cinematic language, bloated adjectives, weak verbs, or needs sharper production-specific wording.
- **seedance-camera** - This skill should be used when the user asks for camera movement, shot scale, lens feel, framing, one-take direction, dolly, pan, tilt, push-in, handheld, aerial, macro, or camera-transfer guidance for Seedance 2.0.
- **seedance-characters** - This skill should be used when the user asks for character consistency, character tags, identity lock, multi-character blocking, wardrobe continuity, hand safety, expression control, or likeness-sensitive character guidance.
- **seedance-interview** - This skill should be used when the user has a vague Seedance 2.0 video idea and asks for creative guidance, story development, scene planning, a director interview, or help turning an undeveloped concept into a production-ready prompt.
- **seedance-interview-short** - This skill should be used when the user wants a fast Seedance 2.0 creative brief, a short interview, a compressed intake flow, or a quick director-style clarification before prompt writing.
- **seedance-lighting** - This skill should be used when the user asks for lighting design, atmosphere, time of day, color temperature, shadow, reflections, weather light, practical lights, or mood transitions in Seedance 2.0.
- **seedance-motion** - This skill should be used when the user asks for body action, choreography, physics, object movement, movement timing, action continuity, stunt direction, or motion-reference mapping in Seedance 2.0.
- **seedance-pipeline** - This skill should be used when the user asks about Seedance 2.0 workflow operations, API planning, BytePlus ModelArk, Dreamina/Jimeng surfaces, ComfyUI, post-production, stitching, batch workflow, or integration planning.
- **seedance-prompt** - This skill should be used when the user asks to write, improve, translate, compress, or debug a Seedance 2.0 video prompt; mentions T2V, I2V, V2V, R2V, camera direction, prompt quality, or provides reference assets for a production-ready prompt.
- **seedance-prompt-short** - This skill should be used when the user asks for a compact Seedance 2.0 prompt, short Chinese prompt, prompt compression, 30-100 word output, or removal of unnecessary prompt language.
- **seedance-recipes** - This skill should be used when the user asks for a Seedance 2.0 template, genre recipe, product ad, lifestyle video, drama scene, music video, landscape shot, commercial, animation scene, or reusable production pattern.
- **seedance-style** - This skill should be used when the user asks for visual style, art direction, render feel, period aesthetic, texture, animation style, realism level, or style-safe alternatives to studio or franchise references.
- **seedance-troubleshoot** - This skill should be used when a Seedance 2.0 output is blurry, jittery, off-prompt, morphing, blocked, visually generic, unstable, desynced, inconsistent, or otherwise fails and needs root-cause diagnosis.
- **seedance-vfx** - This skill should be used when the user asks for VFX, particles, energy, destruction, transformation, weather effects, magical effects, explosions, smoke, fire, water, or physically plausible effects in Seedance 2.0.

Connector setup per application: `connectors/<app>/`. Install: docs/GETTING-STARTED.md.
