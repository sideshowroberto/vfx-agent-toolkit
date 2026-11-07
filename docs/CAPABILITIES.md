# Capabilities index (public toolkit)

GENERATED 2026-11-06 by `ClaudeCode/scripts/gen_capabilities.py` from plugins/registry.json, the skill and agent files, .mcp.json and the script folders. Do not edit; it is rewritten on every /sync-plugins. Registry 2.0.4, updated 2026-10-30.

**How to use it:** ask your agent "what can we do for <task>?" - it should read this file and name the skill, agent, tool or script to reach for. Each line is: name, then what it does and the phrases that trigger it.

## Skills, by plugin

### vfx-core (v2.10.4, public)

Foundation package - install first. Cross-application skills and agents: search, documentation, testing, Python, planning, skill/agent creation, git safety guardrails, and session wrap-up. Registers core MCP servers (brave-search, context7, desktop-commander).

MCP servers: `brave-search`, `context7`, `desktop-commander`

- **agent-creation-update** [scripts] - Create and update VFX agents with constitutional compliance. Use when creating agents, updating agents, validating agents, or managing agent versions.
- **skill-creation-update** [scripts] - Creates, validates and versions VFX Agent Skills against the skill constitution using template scripts (create_skill, validate_skill, test_skill). Use when creating or updating a skill, checking compliance, or bumping a skill version.
- **development-management** - Runs Specification-Driven Development (spec-kit) workflows - agent creation, constitutional governance, roadmaps, specs and validation. Use when creating or auditing agents, writing a constitution, or validating compliance.
- **brave-search** [scripts] - Researches VFX topics with Brave Search - MCP web search for filtered URL lists, an LLM Context script for deep research with extracted page content, and image search for references. Use when searching for tutorials, docs, errors, plugins or software updates.
- **vfx-documentation** - Index-driven documentation system for VFX applications. Use with "document this," "create documentation index," "update docs," or when starting documentation for Nuke, Houdini, Blender, Unreal, or multi-app VFX pipelines.
- **grill-me** - Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
- **gap-check** - Audits Claude's own knowledge gaps against a settled plan before building - sorts confident from guessed, researches public gaps, and lists unknowns for the user. Use after /grill-me, before a build session, or on 'gap-check' or 'check your assumptions'.
- **vfx-plan** - Plans complex VFX builds by choosing Iterative, Spec-Driven or Safety-First mode, running an adversarial plan review and writing an actionable brief. Use on "help me plan" or "vfx plan", or before any multi-file or multi-system build.
- **git-guardrails-claude-code** [scripts] - Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
- **wrap-session** - Runs the end-of-session wrap-up before clearing context - saves durable facts to memory, folds gotchas into skills, writes the session log and a handoff plan, cleans temp files. Use before /clear, when context runs low, or on "wrap up this session".
- **qwen-delegate** [scripts] - Delegates tasks to the local Qwen model on Ollama so file content stays on the machine and out of Claude's context. Use for "ask Qwen" or "do this locally", NDA-safe file analysis, large-file summaries, boilerplate and BlinkScript drafts.
- **task-observer** [scripts] - Logs skill lessons (user corrections, broken rules, better workflows) to the observation log as they happen; applied only after owner review. Invoke before the first tool call of any session and run its Session Start Protocol. Also "observation log", "skill review".
- **youtube-transcript** [scripts] - Retrieve available YouTube captions with timestamps and provenance, or analyze a video from its transcript. Use for YouTube links and transcript requests; this does not watch video frames or transcribe uncaptained audio.
- **vfx-research** - Research VFX application APIs, errors, workflow integrations, and library examples using Brave Search and Context7. Use for Blender, Nuke, Houdini, Unreal, ComfyUI, and related development questions that need external evidence.
- **vfx-workflow** - Apply this toolkit's audited application lessons when scripting DCC scenes, running ComfyUI workflows, or preparing cross-application VFX handoffs. Use for execution and integration work; use vfx-research for documentation lookup.
- **loop-gauntlet** [scripts] - Runs a build-until-it-matches loop in a DCC - an agent rebuilds a scene from reference images, scoring renders against a human-authored rubric until a stop rule fires. Use for 'iterate until it matches', Blender set rebuilds from refs, or writing or judging such a loop prompt.
- **agent: search-specialist** - Expert VFX research specialist using Brave Search API for technical documentation, tutorials, problem-solving, and industry intelligence across Unreal Engine, Blender, Houdini, Nuke, and ComfyUI
- **agent: documentation-specialist** - Index-driven documentation updates for VFX application projects. Reads DOCUMENTATION_INDEX.md to understand structure, maintains consistency across related files, updates progress trackers, and creates session summaries. Use with "update documentation," "document session," or "index-driven update.
- **agent: testing-specialist** - Testing and validating Python scripts, skill scripts, and agent outputs. Use when requests include "test", "validate", "verify", "check", or "pytest". Validates JSON outputs, error handling, script independence, and generates test reports. Proactively invoked after refactoring to ensure functionality.
- **agent: python-specialist** - Applying templates, systematic refactoring, type safety (mypy, type hints, protocols), async programming (AsyncIO, concurrent.futures), data science workflows (pandas, numpy vectorization), and testing methodology (pytest, fixtures, parameterized tests). Use when applying agent-skill templates, migrating code patterns, refactoring with type hints, optimizing with async/vectorization, or performing systematic code transformation across multiple files.
- **agent: python-refactoring-specialist** - Python refactoring specialist for applying templates, batch search/replace, and systematic code refactoring. Use when applying agent-skill templates, migrating code patterns, or performing systematic refactoring across multiple files.

### nuke-vfx (v1.1.12, public)

Nuke compositing pipeline: node graphs, BlinkScript, Cattery AI inference, Python scripting, and tiling tool.

MCP servers: `nuke`
Requires: vfx-core

- **nuke-blinkscript** - Writes GPU-accelerated BlinkScript kernels for Nuke - composition grids, procedural patterns, custom pixel effects. Use when creating a BlinkScript or "blink kernel", or a custom GPU effect the standard Nuke nodes cannot do.
- **nuke-particle-blinkscript** - Builds particle effects in Nuke with the ParticleBlinkScript node (NukeX 16+) or procedural BlinkScript for snow, embers and dust on any Nuke. Use when asked for custom GPU particles, particle gadgets or atmospheric particle effects in Nuke.
- **nuke-cattery-inference** - Brings PyTorch models into Nuke via TorchScript export, CatFileCreator .cat files and the Inference node, e.g. DepthAnything depth. Use when tracing an ML model for Nuke, building a .cat file, or running ML inference in a comp.
- **nuke-compositing** [scripts] - Node graph compositing workflows for Nuke including Read/Write setup, grading, merging, keying, and multi-layer comp patterns. Use when setting up comps, creating node graphs, or when user mentions nuke comp, node graph, grade, merge, keying, aov.
- **nuke-node-tree-patterns** - Production-tested patterns for creating robust Nuke node trees programmatically. Use for avoiding auto-connection issues, dynamic positioning, expression masks, and gradient blending.
- **nuke-python-scripting** [scripts] - Writes Nuke Python automation scripts using the NukeMCPLogger pattern so results and logs return through the MCP bridge. Use when scripting Nuke, automating comps, or when "nuke python", "nuke script" or the nuke logger come up.
- **nuke-tiling-tool** [scripts] - Automated image tiling for ML processing in Nuke with seamless gradient blending. Use for large plates (4K+) through ML nodes (ViTMatte) optimized for 1K-2K tiles.
- **agent: nuke-specialist** - Nuke compositing expert coordinating node graph operations, Python scripting, and ComfyUI integration. Use when user mentions nuke, compositing, nodes, grade, merge, multi-shot, or nuke python.

### houdini-vfx (v1.1.5, public)

Houdini VFX pipeline: procedural generation, USD/Solaris, VEX, Python automation, HDA creation.

MCP servers: `houdini`
Requires: vfx-core

- **houdini-hda-creation** - Creates and manages Houdini Digital Assets (HDAs) - parameter interfaces, compilation, versioning and asset organization. Use when authoring reusable Houdini tools or asked about HDA creation, HDA parameters or compiling an HDA.
- **houdini-procedural-generation** - Create procedural geometry workflows using SOPs including scattering, copying, instancing, and parametric modeling. Use for procedural modeling workflows. Triggers: procedural generation, scatter, copy to points, procedural modeling, sops
- **houdini-python-automation** [scripts] - Automates Houdini with Python (HOM) - node creation, parameter manipulation, scene management and batch processing. Use when scripting Houdini workflows, e.g. 'houdini python', 'hom script', 'automate houdini' or batch processing hip files.
- **houdini-solaris-usd** [scripts] - Work with USD (Universal Scene Description) in Houdini Solaris including stage creation, layer composition, variants, and USD export workflows. Use for USD workflows and Solaris. Triggers: solaris, usd, stage, layer, variant, usd export
- **houdini-vex-programming** - Write VEX code for Houdini including wrangles, custom operations, attribute manipulation, and performance optimization. Use when writing VEX scripts or custom operations. Triggers: vex, wrangle, vex code, attribute wrangle, point wrangle

### unreal-vfx (v2.2.1, public)

Unreal Engine 5.8 VFX pipeline via the native UE MCP (ModelContextProtocol plugin + VibeUE toolsets): Blueprint automation, PCG, actor operations, Sequencer, Python scripting.

MCP servers: `ue58-mcp`
Requires: vfx-core

- **unreal-actor-operations** [scripts] - Spawns, transforms and queries actors in Unreal Engine 5.8 via Python over the MCP. Use when spawning actors, setting location or rotation, reading or setting actor properties, or placing static mesh and Blueprint actors.
- **unreal-blueprint-automation** - Creates and compiles Blueprints in Unreal Engine 5.8 via Python using phased Silent Execution (components, properties, compile). Use when creating a Blueprint, adding components, setting Blueprint properties, or debugging Blueprint compile crashes.
- **unreal-pcg-automation** [scripts] - Builds PCG (Procedural Content Generation) graphs in Unreal Engine 5.8 via Python - nodes, settings, asset integration, debugging. Use when creating or debugging PCG graphs, configuring PCG nodes, or scattering assets procedurally.
- **unreal-project-preflight** [scripts] - Checks and batch-fixes the Unreal project prerequisites a plan needs (plugins, project settings, editor config) as Step 0 before building. Use once an Unreal plan is approved, before MegaPlants, PCG, MRQ or ImagePlate work, or when a class, node or plugin is missing.
- **unreal-python-scripting** - Gives Unreal Engine 5.8 Python API patterns - Blueprint spawning, material instances, component properties, workarounds for API limits. Use when scripting Unreal in Python, writing Unreal Python tools, or hitting an Unreal Python API limitation.
- **unreal-sequencer-automation** [scripts] - Automates Level Sequences in Unreal Engine 5.8 via Python - tracks, keyframes, camera cuts, transform animation, ImagePlate plates. Use when creating a sequence, adding tracks, setting keyframes or camera cuts, or setting up foreground plates in Sequencer.
- **unreal-vfx-automation** - Automates VFX plate workflows in Unreal Engine 5.8 - ImagePlate and foreground plates, image sequences, multi-shot setups, set extension. Use when setting up an ImagePlate or foreground plate, loading image sequences, or batch-processing shots in Unreal.
- **agent: unreal-blueprint-specialist** - Expert in automating Unreal Engine Blueprint creation and compilation using Silent Execution pattern
- **agent: unreal-pcg-specialist** - Expert in Unreal Engine PCG system for procedural terrain, vegetation, and asset placement with Python automation

### blender-vfx (v2.0.12, public)

Blender VFX pipeline via the official Blender MCP (blender.org): modeling, animation, materials, geometry nodes, physics, rendering, sculpting, grease pencil, and ControlNet pass rendering for AI generation.

MCP servers: `blender`
Requires: vfx-core

- **blender-addon-development** - Guides Blender addon development - operators, UI panels, bpy.props, poll() methods and registration. Use when creating a Blender addon, building an operator or UI panel, or writing Blender Python for a tool.
- **blender-animation** - Keyframe animation, rigging, constraints, and armatures in Blender. Use for animation, rigging, camera movement, or when user mentions "animate," "keyframe," "rig," or "armature.
- **blender-api-compatibility** - Diagnoses and migrates Blender Python API breakage across versions 4.2 to 5.1+ (EEVEE_NEXT, renamed modifier types and BSDF inputs, VSE strips). Use when a bpy script errors on a newer Blender, or for breaking changes and migration.
- **blender-compositing** - Compositor nodes, post-processing, and color grading in Blender. Use for compositing workflows, render pass integration, post-processing, color correction, or when user mentions "compositor," "post-process," "color grade," or "render passes.
- **blender-geometry-nodes** - Procedural modeling using Geometry Nodes in Blender. Use for scattering systems, node trees, parametric design, or when user mentions "procedural," "geometry nodes," "scattering," or "instances.
- **blender-grease-pencil** - Builds 2D and mixed-media animation in Blender with Grease Pencil - strokes, layers, frame-by-frame animation, 2D/3D integration, NPR rendering. Use for 2D or hand-drawn animation, traditional animation, or any grease pencil request.
- **blender-materials-shaders** - Creates Blender shader node trees, PBR materials and procedural textures, with EEVEE_NEXT and Cycles compatibility notes. Use for material creation, shader setups, Principled BSDF inputs, or procedural texturing of parametric geometry.
- **blender-physics-simulation** - Sets up Blender physics simulations - particle systems, Mantaflow fluid, smoke and fire, rigid body, soft body, cloth and hair. Use for physics, particle, fluid, cloth or hair simulation requests in Blender.
- **blender-rendering** - EEVEE_NEXT and Cycles rendering, lighting, and render optimization in Blender. Use for rendering setup, lighting, render settings, or when user mentions "render," "lighting," "EEVEE," "Cycles," or "materials.
- **blender-sculpting** - Terrain creation, organic modeling, and surface details using Blender sculpting tools. Use for terrain, organic shapes, sculpted details, or when user mentions "sculpt," "terrain," or "organic.
- **blender-controlnet-passes** [scripts] - Renders ControlNet conditioning passes from a Blender scene for AI image and video generation - grey clay, normalized depth, cryptomatte EXR, optional wireframe. Use when preparing depth, edge or clay inputs for video models, or crypto mattes for comp.
- **agent: blender-specialist** - Expert in Blender workflows via official Blender MCP. Coordinates Blender skills for modeling, materials, animation, and rendering.

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
