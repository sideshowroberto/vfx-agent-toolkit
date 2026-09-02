# Capabilities index (public toolkit)

GENERATED 2026-09-02 by `ClaudeCode/scripts/gen_capabilities.py` from plugins/registry.json, the skill and agent files, .mcp.json and the script folders. Do not edit; it is rewritten on every /sync-plugins. Registry 2.0.3, updated 2026-09-01.

**How to use it:** ask your agent "what can we do for <task>?" - it should read this file and name the skill, agent, tool or script to reach for. Each line is: name, then what it does and the phrases that trigger it.

## Skills, by plugin

### vfx-core (v2.3.2, public)

Foundation package - install first. Cross-application skills and agents: search, documentation, testing, Python, planning, skill/agent creation, git safety guardrails, and session wrap-up. Registers core MCP servers (brave-search, context7, desktop-commander).

MCP servers: `brave-search`, `context7`, `desktop-commander`

- **agent-creation-update** [scripts] - Create and update VFX agents with constitutional compliance. Use when creating agents, updating agents, validating agents, or managing agent versions.
- **skill-creation-update** [scripts] - Standardized workflow for creating and updating VFX Agent Skills with constitutional validation, progressive disclosure enforcement, and automated template application. Use when creating skills, validating compliance, testing scripts, updating skill versions, or when user mentions "create skill", "validate skill", "skill template", "constitutional compliance", "skill testing".
- **development-management** - Specification-Driven Development (SDD) workflows for VFX pipeline using spec-kit methodology. Covers agent creation, constitutional governance, roadmaps, specs, and validation. Use when user requests development work, agent audits, skill creation, constitutional compliance checks, or mentions 'how do I create agent', 'audit agents', 'spec-kit', 'development process', 'validate this', 'create constitution', 'governance rules'.
- **brave-search** [scripts] - VFX-focused web research using Brave Search API. Two modes: MCP web_search for filtered URL results, LLM Context script for deep research with actual extracted page content. Use when searching for tutorials, documentation, errors, plugins, software updates, or any VFX research task.
- **vfx-documentation** - Index-driven documentation system for VFX applications. Use with "document this," "create documentation index," "update docs," or when starting documentation for Nuke, Houdini, Blender, Unreal, or multi-app VFX pipelines.
- **grill-me** - Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
- **gap-check** - Audit Claude's own knowledge gaps against a settled plan before building. Claude categorizes what it knows confidently vs. guesses at, launches search-specialist agents to fill gaps, and surfaces unknowns for the user to answer. Use after /grill-me when scope is settled, before any planning or build session, or when user says "gap-check", "check your assumptions", "what don't you know about this".
- **vfx-plan** - VFX planning framework - guides selecting the right planning mode (Iterative, Spec-Driven, or Safety-First) for a given task, runs adversarial plan review, and structures the output as an actionable brief. Use when user says "help me plan", "let's plan this out", "vfx plan", "plan this task", or before any complex multi-file or multi-system build.
- **git-guardrails-claude-code** [scripts] - Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
- **wrap-session** - End-of-session wrap-up ritual before clearing context. Reviews the session for durable facts to save to memory, updates skills with newly discovered gotchas, writes a session log for substantial project work, cleans up temp files, and writes a handoff plan so the next session can resume without re-discovery. Use when the user is about to /clear, when context is running low, or at the natural end of a work session. Triggers on "/wrap-session", "wrap up this session", "we're running low on context", "prepare to clear context", "before we clear".
- **qwen-delegate** [scripts] - Delegate tasks from a Claude Code session to the local Qwen model on Ollama (port 11434) - the same model the team's OpenCode / Qwen Code installs use. Use when user says "ask Qwen", "have Qwen do this", "delegate to local model", "use local LLM", "keep this NDA-safe", "do this locally". Also use proactively for NDA-sensitive file analysis, large-file summarization, boilerplate generation, BlinkScript drafts, or batch text transforms where privacy and Claude-token savings matter more than deep reasoning.
- **task-observer** [scripts] - Watches every tool-using session for skill lessons and writes each one to the observation log the moment it happens - user corrections, rules the agent broke, better workflows, sibling skills that need the same fix, sections nobody uses. Nothing is applied until a review the skill owner approves. Invoke before the FIRST tool call of any session and run its Session Start Protocol (status, scan, review trigger); loading alone activates nothing. Also triggers on "observation log", "any observations logged", "skill review", "task observer", "log that as an observation", "review the backlog".
- **agent: search-specialist** - Expert VFX research specialist using Brave Search API for technical documentation, tutorials, problem-solving, and industry intelligence across Unreal Engine, Blender, Houdini, Nuke, and ComfyUI
- **agent: documentation-specialist** - Index-driven documentation updates for VFX application projects. Reads DOCUMENTATION_INDEX.md to understand structure, maintains consistency across related files, updates progress trackers, and creates session summaries. Use with "update documentation," "document session," or "index-driven update.
- **agent: testing-specialist** - Testing and validating Python scripts, skill scripts, and agent outputs. Use when requests include "test", "validate", "verify", "check", or "pytest". Validates JSON outputs, error handling, script independence, and generates test reports. Proactively invoked after refactoring to ensure functionality.
- **agent: python-specialist** - Applying templates, systematic refactoring, type safety (mypy, type hints, protocols), async programming (AsyncIO, concurrent.futures), data science workflows (pandas, numpy vectorization), and testing methodology (pytest, fixtures, parameterized tests). Use when applying agent-skill templates, migrating code patterns, refactoring with type hints, optimizing with async/vectorization, or performing systematic code transformation across multiple files.
- **agent: python-refactoring-specialist** - Python refactoring specialist for applying templates, batch search/replace, and systematic code refactoring. Use when applying agent-skill templates, migrating code patterns, or performing systematic refactoring across multiple files.

### nuke-vfx (v1.1.2, public)

Nuke compositing pipeline: node graphs, BlinkScript, Cattery AI inference, Python scripting, tiling tool, and batch shot setup.

MCP servers: `nuke`
Requires: vfx-core

- **nuke-blinkscript** - BlinkScript kernel development for Nuke with GPU acceleration, composition grids, procedural patterns, and custom effects. Use when creating BlinkScript kernels, GPU-accelerated effects, or when user mentions blinkscript, blink kernel, nuke kernel, custom kernel, GPU effect.
- **nuke-particle-blinkscript** - ParticleBlinkScript node development for NukeX 16+ - custom particle systems, GPU particle physics, and Foundry gadget templates. Also covers procedural BlinkScript atmospheric effects (snow, embers, dust) that bypass the particle system entirely. Use when user mentions particle blinkscript, ParticleBlinkScript node, custom particles nuke, blinkscript particles, GPU particles nuke, particle gadgets, procedural snow nuke, atmospheric blinkscript.
- **nuke-cattery-inference** - PyTorch model integration in Nuke via CatFileCreator and Inference nodes. Use when tracing ML models for Nuke, setting up depth estimation, AI-powered effects, or when user mentions CatFileCreator, .cat file, Inference node, cattery, TorchScript, depth model, DA3, DepthAnything, or ML inference in Nuke.
- **nuke-compositing** [scripts] - Node graph compositing workflows for Nuke including Read/Write setup, grading, merging, keying, and multi-layer comp patterns. Use when setting up comps, creating node graphs, or when user mentions nuke comp, node graph, grade, merge, keying, aov.
- **nuke-node-tree-patterns** - Production-tested patterns for creating robust Nuke node trees programmatically. Use for avoiding auto-connection issues, dynamic positioning, expression masks, and gradient blending.
- **nuke-python-scripting** [scripts] - Python scripting for Nuke with NukeMCPLogger integration, script templates, and automation patterns. Use when writing Nuke Python scripts, using NukeMCPLogger, automating comps, or when user mentions nuke python, nuke script, nuke logger, nuke automation.
- **nuke-tiling-tool** [scripts] - Automated image tiling for ML processing in Nuke with seamless gradient blending. Use for large plates (4K+) through ML nodes (ViTMatte) optimized for 1K-2K tiles.
- **nuke-shot-setup** - Batch shot setup for Nuke comp projects. Parses a ShotGrid CSV export, reads plate metadata from a plates CSV (or scans plates on disk), creates per-shot folder structures, generates Nuke v001 visdev/comp files with plates auto-connected (Read + Stamp/Anchor with proper ACES colorspace), and produces a Google Sheets-ready CSV shot tracker. Supports multiple sequences at once, show-specific config (OCIO, LUT, compression), and configurable work context (visdev, comp). Use when the user wants to set up shots, run a batch shot setup, start a new sequence, onboard plates, build a shot tracker CSV, or create comps from a CSV. Triggers on "set up shots", "batch shot setup", "new sequence", "onboard plates", "shot tracker csv", "create comps from csv", "shot setup from ShotGrid", "visdev setup".
- **agent: nuke-specialist** - Nuke compositing expert coordinating node graph operations, Python scripting, and ComfyUI integration. Use when user mentions nuke, compositing, nodes, grade, merge, multi-shot, or nuke python.

### houdini-vfx (v1.0.2, public)

Houdini VFX pipeline: procedural generation, USD/Solaris, VEX, Python automation, HDA creation.

MCP servers: `houdini`
Requires: vfx-core

- **houdini-hda-creation** [scripts] - Create and manage Houdini Digital Assets (HDAs) including parameter interfaces, compilation, versioning, and asset organization. Use when authoring reusable Houdini tools. Triggers: hda creation, digital asset, hda compile, hda parameters, create hda
- **houdini-procedural-generation** [scripts] - Create procedural geometry workflows using SOPs including scattering, copying, instancing, and parametric modeling. Use for procedural modeling workflows. Triggers: procedural generation, scatter, copy to points, procedural modeling, sops
- **houdini-python-automation** [scripts] - Automate Houdini workflows using Python (HOM - Houdini Object Model) including node creation, parameter manipulation, scene management, and batch processing. Use when scripting Houdini workflows. Triggers: houdini python, hom, python script, automate houdini, batch process
- **houdini-solaris-usd** [scripts] - Work with USD (Universal Scene Description) in Houdini Solaris including stage creation, layer composition, variants, and USD export workflows. Use for USD workflows and Solaris. Triggers: solaris, usd, stage, layer, variant, usd export
- **houdini-vex-programming** [scripts] - Write VEX code for Houdini including wrangles, custom operations, attribute manipulation, and performance optimization. Use when writing VEX scripts or custom operations. Triggers: vex, wrangle, vex code, attribute wrangle, point wrangle

### unreal-vfx (v2.0.2, public)

Unreal Engine 5.8 VFX pipeline via the native UE MCP (ModelContextProtocol plugin + VibeUE toolsets): Blueprint automation, PCG, actor operations, Sequencer, Python scripting.

MCP servers: `ue58-mcp`
Requires: vfx-core

- **unreal-actor-operations** [scripts] - Spawn, manipulate, and query actors in Unreal Engine via Python. Use when spawning actors, setting transforms, getting/setting properties, or when user mentions "actor", "spawn", "transform", "location", "rotation", "static mesh actor", "blueprint actor".
- **unreal-blueprint-automation** - Automate Blueprint creation, component addition, property configuration, and compilation in Unreal Engine 5.8 using phased execution pattern. Use when creating Blueprints, adding components, setting properties, debugging Blueprint crashes, or when user mentions blueprint, create blueprint, compile blueprint, add component, blueprint property, set component property, blueprint automation.
- **unreal-pcg-automation** [scripts] - Automate PCG (Procedural Content Generation) graph creation, node configuration, and asset integration in Unreal Engine 5.8. Use when creating PCG graphs, configuring nodes, debugging PCG, or when user mentions pcg, procedural generation, pcg graph, scatter, pcg node, procedural content, point cloud.
- **unreal-python-scripting** - Python API patterns for Unreal Engine 5.8 including Blueprint spawning, material workflows, component manipulation, and API limitations workarounds. Use when scripting Unreal, creating Python tools, encountering API limitations, or when user mentions unreal python, blueprint spawning, material instance, component properties, python api limitations, ue python.
- **unreal-sequencer-automation** [scripts] - Automate Level Sequence creation, camera cuts, transform animation, and VFX plate workflows via Python. Use when creating sequences, adding tracks, setting keyframes, camera cuts, ImagePlate, or when user mentions "sequencer", "level sequence", "animation", "keyframe", "cinematic", "camera cut", "foreground plate".
- **unreal-vfx-automation** - Automate VFX workflows in Unreal Engine 5.8 including foreground plates, image sequences, and multi-shot production. Use when setting up ImagePlate, creating foreground plates, batch processing shots, or when user mentions unreal foreground plate, image sequence, vfx set extension, imageplate setup, foreground plate, vfx automation, unreal vfx, set extension, multi shot.
- **agent: unreal-blueprint-specialist** - Expert in automating Unreal Engine Blueprint creation and compilation using Silent Execution pattern
- **agent: unreal-pcg-specialist** - Expert in Unreal Engine PCG system for procedural terrain, vegetation, and asset placement with Python automation

### blender-vfx (v2.0.5, public)

Blender VFX pipeline via the official Blender MCP (blender.org): modeling, animation, materials, geometry nodes, physics, rendering, sculpting, grease pencil, and ControlNet pass rendering for AI generation.

MCP servers: `blender`
Requires: vfx-core

- **blender-addon-development** - Blender addon development - operator design, UI panels, bpy.props, poll() methods, and registration systems. Use when creating addons, building operators, designing UI panels, or when user mentions "addon," "operator," "UI panel," or "Blender Python.
- **blender-animation** - Keyframe animation, rigging, constraints, and armatures in Blender. Use for animation, rigging, camera movement, or when user mentions "animate," "keyframe," "rig," or "armature.
- **blender-api-compatibility** - Blender API compatibility across versions (4.2 -> 5.1+), breaking changes detection, and migration strategies. Use for API errors, version migration, breaking changes, or when user mentions "compatibility," "breaking change," "migration," "API error," or "doesn't work in newer Blender.
- **blender-compositing** - Compositor nodes, post-processing, and color grading in Blender. Use for compositing workflows, render pass integration, post-processing, color correction, or when user mentions "compositor," "post-process," "color grade," or "render passes.
- **blender-geometry-nodes** - Procedural modeling using Geometry Nodes in Blender. Use for scattering systems, node trees, parametric design, or when user mentions "procedural," "geometry nodes," "scattering," or "instances.
- **blender-grease-pencil** - 2D animation and Grease Pencil workflows in Blender. Use for 2D animation, hand-drawn animation, mixed media, stroke creation, layer management, or when user mentions "2D," "grease pencil," "hand drawn," "traditional animation," "NPR rendering," or "stylized animation.
- **blender-materials-shaders** - Shader nodes, PBR materials, and procedural textures in Blender. Use for material creation, shader setups, PBR workflows, cross-engine compatibility (EEVEE_NEXT/Cycles), or when user mentions "material," "shader," "PBR," "texture," "node tree," or "Principled BSDF.
- **blender-physics-simulation** - Physics simulations including particles, fluids (Mantaflow), rigid/soft body, and cloth in Blender. Use for physics, particles, fluid simulations, or when user mentions "physics," "particle," "fluid," "rigid body," "soft body," "cloth," "fire," "smoke," or "hair.
- **blender-rendering** - EEVEE_NEXT and Cycles rendering, lighting, and render optimization in Blender. Use for rendering setup, lighting, render settings, or when user mentions "render," "lighting," "EEVEE," "Cycles," or "materials.
- **blender-sculpting** - Terrain creation, organic modeling, and surface details using Blender sculpting tools. Use for terrain, organic shapes, sculpted details, or when user mentions "sculpt," "terrain," or "organic.
- **blender-controlnet-passes** - Set up and render ControlNet conditioning passes from a Blender scene for AI image/video generation - grey clay override, compositor-normalized depth, cryptomatte EXR, optional wireframe overlay for temporal consistency. Wraps Blender/scripts/setup_controlnet_passes.py (Blender 5.x APIs, test-slice discipline, trailing-dot File Output naming). Use when preparing depth/edge conditioning inputs, clay renders for video models, or crypto mattes for comp. Triggers: \"controlnet passes\", \"render depth pass\", \"clay render\", \"grey shade render\", \"render passes for AI\", \"control net setup blender\".
- **agent: blender-specialist** - Expert in Blender workflows via official Blender MCP. Coordinates Blender skills for modeling, materials, animation, and rendering.

### comfyui-vfx (v2.2.3, public)

ComfyUI pipeline via the ComfyUI MCP and Comfy CLI, with optional ComfyUI_FL-MCP for live canvas operations: workflow analysis, node/model requirements mapping, and headless generation guidance, plus the previs-to-photoreal anchor keyframe recipe for reference-guided video generation.

MCP servers: `comfyui`
Requires: vfx-core

- **comfyui-workflow-analysis** - Analyze downloaded ComfyUI workflow JSON files to extract required custom nodes and models, map them to correct install locations, and generate a setup checklist. Use when user shares a workflow JSON, asks "what nodes does this need", "what models does this use", "help me set up this workflow", or "analyze this comfy workflow".
- **previs-anchor-keyframes** - Generate photoreal anchor keyframes from CG previs for reference-guided video generation (Seedance-class models). Covers previs shading for AI readability, anchor frame selection, bootstrapping action-pose reference sets from a single reference, lighting-accurate prompt language, and validation. Use when converting previs/CG animation to photoreal video, preparing anchor/reference frames for a video model, or when generations ignore CG placement or pose. Triggers on "anchor keyframes", "anchor frames", "previs to photoreal video", "reference frames for video gen", "generations not following the CG".

### comfyui-node-dev (v1.1.1, public)

ComfyUI custom node development: V3 API node structure, schemas, datatypes, inputs/outputs, execution lifecycle, frontend extensions, V1-to-V3 migration, and packaging/publishing.
Requires: vfx-core

- **comfyui-node-basics** - ComfyUI custom node fundamentals - V3 node structure, Schema, inputs/outputs, registration. Use when creating new ComfyUI custom nodes, defining node classes, or setting up a custom node project.
- **comfyui-node-advanced** - ComfyUI advanced node patterns - MatchType, Autogrow, DynamicCombo, node expansion, MultiType, wildcard inputs. Use when building complex nodes with dynamic inputs, type matching, or node expansion.
- **comfyui-node-datatypes** - ComfyUI data types - IMAGE, LATENT, MASK, CONDITIONING, MODEL, CLIP, VAE, AUDIO, VIDEO, 3D types, widget types, and custom types. Use when working with ComfyUI tensors, model types, or defining input/output data types.
- **comfyui-node-inputs** - ComfyUI node input types - INT, FLOAT, STRING, BOOLEAN, COMBO widgets, hidden inputs, optional inputs, lazy inputs, force_input. Use when configuring node inputs, adding widgets, or customizing input behavior.
- **comfyui-node-outputs** - ComfyUI node output types - NodeOutput, UI outputs, PreviewImage, PreviewMask, SavedImages, PreviewAudio, PreviewText, PreviewVideo. Use when returning results from nodes, displaying previews, or saving output files.
- **comfyui-node-lifecycle** - ComfyUI node execution lifecycle - caching, fingerprint_inputs/IS_CHANGED, validate_inputs/VALIDATE_INPUTS, check_lazy_status, execution order. Use when debugging execution, implementing caching control, input validation, or understanding execution flow.
- **comfyui-node-frontend** - ComfyUI frontend JavaScript extensions - hooks, widgets, sidebar tabs, commands, settings, toasts, dialogs. Use when adding UI features to custom nodes, creating custom widgets, or extending the ComfyUI frontend.
- **comfyui-node-migration** - ComfyUI V1 to V3 node migration - converting legacy nodes to the V3 API. Use when migrating existing custom nodes from V1 to V3, understanding differences between API versions, or modernizing node code.
- **comfyui-node-packaging** - ComfyUI custom node project structure - directory layout, __init__.py, registration, requirements.txt, publishing, WEB_DIRECTORY. Use when setting up a new custom node project, packaging nodes, or publishing to the registry.

### maya-vfx (v1.0.3, public)

Maya pipeline via MCP: scene control, geometry creation, materials (Arnold/USD), transforms, and FBX import/export.

MCP servers: `maya`
Requires: vfx-core

- **maya-scene** - Query and manipulate Maya scene objects, transforms, hierarchy, and attributes via MCP commandPort. Use for listing scene contents, creating geometry, setting transforms, parenting objects, selecting, importing/exporting FBX. Triggers on "maya scene", "list objects", "create sphere", "cmds.ls", "FBX export from Maya".
- **maya-materials** - Create and assign materials in Maya via MCP - Arnold (aiStandardSurface), Lambert, Blinn, and USD Preview Surface. Use for shader creation, texture assignment, material assignment to geometry, and look dev workflows. Triggers on "maya material", "assign shader", "aiStandardSurface", "maya texture", "look dev".
- **agent: maya-specialist** - Maya scene control, rigging, modeling, and animation automation via MCP. Auto-triggers on .ma/.mb files, maya.cmds, pymel, rigging, blend shapes, joints, and deformers. Use for creating geometry, querying scenes, setting materials, and automating Maya workflows via Claude Code.

### magnific-vfx (v1.1.2, public)

Magnific AI generation via MCP: image generation with model selection and references, local file upload/download pipelines, and video generation.

MCP servers: `magnific`
Requires: vfx-core

- **magnific-image-gen** - Magnific MCP image generation skill. Use when generating ANY images, concept art, product shots, reference images, or visual assets - Magnific is the default image generation tool. Also use for selecting models, resolution/aspect ratio, adding references, browsing/creating folders, upscaling, or generating variations. Triggers on: \"generate image\", \"generate images\", \"generate refs\", \"generate reference\", \"reference images\", \"image refs\", \"generate concept\", \"product shot\", \"concept art\", \"make me an image\", \"make references\", \"generate with magnific\", \"magnific image\", \"nb2\", \"nano banana\", \"magnific folder\", \"upscale\", \"magnific variations\", \"render me\", \"create an image\", \"hero shots\".
- **magnific-local-upload** - Upload local images to Magnific as references for generation, then download outputs to a local folder. Use when user wants to upload photos from a local folder or drive, use local files as image/style references in Magnific, batch upload from a directory, move uploads to a Magnific folder, or save/download Magnific generated images to a local path. Triggers: \"upload local images\", \"use local photos as reference\", \"upload from folder\", \"upload these images to magnific\", \"download magnific output\", \"save generated image to folder\", \"local ref upload\".
- **magnific-video-gen** - Magnific MCP video generation skill. Use when generating video via Magnific, selecting video models, animating stills, using start/end keyframes, camera motion, audio/lipsync, multishot, or video upscale. Triggers on: \"generate video with magnific\", \"magnific video\", \"animate this image\", \"magnific camera motion\", \"seedance\", \"kling video\", \"veo video\", \"video from still\".

### seedance-vfx (v1.0.2, public)

Seedance 2.0 video generation direction: prompt writing, camera, lighting, motion, characters, style, VFX, troubleshooting, and production recipes.
Requires: vfx-core

- **seedance-20** - This skill should be used when directing Seedance 2.0 T2V, I2V, V2V, R2V, audio, safety, or API work.
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
