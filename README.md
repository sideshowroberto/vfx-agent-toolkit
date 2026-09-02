# vfx-agent-toolkit

Claude Code plugins and MCP connectors for VFX production. One clone gets you
skills, agents, and app bridges for Nuke, Houdini, Unreal Engine, Blender,
ComfyUI, Maya, Magnific, and Seedance.

**Skills teach the agent the craft; connectors give it hands in the running
applications.** That split is the whole design.

Built by [Rob Williams](https://github.com/sideshowroberto), a lead VFX
artist working in production - every skill in here has shipped real work.
Open-sourced so you can use it, fork it, and improve it. MIT licensed.

## What is this?

Two things in one repo:

- **Plugins** (`plugins\`) teach Claude Code how to do VFX work. Each plugin is
  a bundle of skills (production-tested knowledge loaded on demand) and agents
  (specialized handlers for delegated tasks).
- **Connectors** (`connectors\`) wire Claude Code to your running applications
  via MCP (Model Context Protocol), so Claude can create nodes in Nuke, drive
  Houdini, control Unreal, and so on.

## What it looks like in use

You say, in Claude Code with Nuke running:

> "Set up comps for the 12 shots in this CSV - plates connected, our standard
> grade/denoise front end, and give me a contact sheet of first frames."

The agent parses the CSV, scans the plates on disk, builds a v001 comp per
shot over the Nuke MCP (Read nodes, Stamp/Anchor wiring, the front-end
template), renders first-frame thumbnails, and writes a tracker CSV back to
disk. That workflow is `nuke-shot-setup`, one of 70+ skills in the toolkit -
the same pattern (knowledge in the skill, hands via the connector) drives
Houdini scatter setups, UE PCG graphs, ComfyUI generation batches, and
Blender ControlNet pass renders.

## Quickstart

1. Add the marketplace inside Claude Code:

   ```
   /plugin marketplace add sideshowroberto/vfx-agent-toolkit
   ```

2. Install the foundation plugin first, then the app plugins you need:

   ```
   /plugin install vfx-core@vfx-agent-toolkit
   /plugin install nuke-vfx@vfx-agent-toolkit
   ```

3. Run the core setup script once to register the shared MCP servers
   (brave-search, context7, desktop-commander) and optionally copy workspace
   templates:

   ```powershell
   plugins\vfx-core\install.ps1
   ```

   brave-search needs a free API key from https://brave.com/search/api.
   context7 and desktop-commander need nothing.

4. For plugins that talk to a running application (Nuke, Houdini, Unreal,
   Blender, Maya, ComfyUI), clone this repo and run the matching connector
   installer:

   ```powershell
   git clone https://github.com/sideshowroberto/vfx-agent-toolkit.git
   cd vfx-agent-toolkit
   connectors\nuke\install.ps1
   ```

5. Restart Claude Code. MCP servers load at startup, so any config change
   needs a restart.

The installers are PowerShell, so setup is Windows-first. The skills and
agents themselves are plain markdown and work anywhere Claude Code runs.

Full walkthrough with expected output: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)

## Plugins

Install `vfx-core` first. Everything else is per-project, install what you use.
The full skill-by-skill index with trigger phrases is generated into
[docs/CAPABILITIES.md](docs/CAPABILITIES.md) on every release.

| Plugin | What it covers |
|--------|----------------|
| `vfx-core` | Foundation package - install first. Cross-application skills and agents: search, documentation, testing, Python, planning, skill/agent creation, git safety guardrails, and session wrap-up. Registers core MCP servers (brave-search, context7, desktop-commander). |
| `nuke-vfx` | Nuke compositing pipeline: node graphs, BlinkScript, Cattery AI inference, Python scripting, tiling tool, batch shot setup, and Magnific-in-Nuke. |
| `houdini-vfx` | Houdini VFX pipeline: procedural generation, USD/Solaris, VEX, Python automation, HDA creation. |
| `unreal-vfx` | Unreal Engine 5.8 VFX pipeline via the native UE MCP (ModelContextProtocol plugin + VibeUE toolsets): Blueprint automation, PCG, actor operations, Sequencer, Python scripting. |
| `blender-vfx` | Blender VFX pipeline via the official Blender MCP (blender.org): modeling, animation, materials, geometry nodes, physics, rendering, sculpting, grease pencil, and ControlNet pass rendering for AI generation. |
| `comfyui-vfx` | ComfyUI pipeline via the ComfyUI MCP and Comfy CLI: workflow analysis, node/model requirements mapping, and headless generation guidance. |
| `comfyui-node-dev` | ComfyUI custom node development: V3 API node structure, schemas, datatypes, inputs/outputs, execution lifecycle, frontend extensions, V1-to-V3 migration, and packaging/publishing. |
| `maya-vfx` | Maya pipeline via MCP: scene control, geometry creation, materials (Arnold/USD), transforms, and FBX import/export. |
| `magnific-vfx` | Magnific AI generation via MCP: image generation with model selection and references, local file upload/download pipelines, and video generation. |
| `seedance-vfx` | Seedance 2.0 video generation direction: prompt writing, camera, lighting, motion, characters, style, VFX, troubleshooting, and production recipes. |

## Connectors

Connectors register MCP servers that bridge Claude Code to your applications.
Details and per-app notes: [connectors/README.md](connectors/README.md)

| Connector | What it does | Notes |
|-----------|--------------|-------|
| `connectors\nuke` | Installs bundled bridge files into `~\.nuke` and registers the Nuke MCP | Bridge code included in this repo |
| `connectors\houdini` | Installs the Houdini bridge and registers the Houdini MCP | Bridge code included in this repo |
| `connectors\unreal` | Registers the UE 5.8 NATIVE MCP (ModelContextProtocol plugin, HTTP port 8000) | UE 5.8 with the plugin enabled; VibeUE from Fab recommended |
| `connectors\maya` | Installs the Maya bridge and registers the Maya MCP | Bridge code included in this repo |
| `connectors\blender` | Registers the official Blender MCP from blender.org | Add-on ships with Blender 4.5+; register.ps1 only |
| `connectors\comfyui` | Registers the ComfyUI MCP (`npx comfyui-mcp`) | Comfy CLI (`pip install comfy-cli`) recommended for headless generation |
| `connectors\magnific` | Registers the hosted Magnific MCP at https://mcp.magnific.com | Needs a Magnific account; OAuth in browser on first use |

## Requirements

| Requirement | Needed for |
|-------------|-----------|
| [Claude Code](https://claude.com/claude-code) | Everything |
| Node.js 18+ | Nuke MCP server, npx-based connectors |
| Python 3.12+ | Bridge scripts, ComfyUI tooling |
| [uv](https://docs.astral.sh/uv/) | Python-based MCP servers (Houdini, Blender) |
| Windows + PowerShell | The installers (skills/agents work on any OS) |

Per-application: Nuke 14+, Houdini 20+, Unreal Engine 5.8, Blender 4.5+
(for the bundled MCP add-on), Maya 2024+, a local ComfyUI install, and a
Magnific account for the Magnific connector.

## Repo layout

```
vfx-agent-toolkit\
+-- .claude-plugin\
|   +-- marketplace.json      Marketplace manifest (what /plugin reads)
+-- plugins\
|   +-- vfx-core\             Foundation: skills, agents, install.ps1, templates
|   +-- nuke-vfx\             Per-app plugins: skills\ + agents\ + plugin.json
|   +-- houdini-vfx\
|   +-- unreal-vfx\
|   +-- blender-vfx\
|   +-- comfyui-vfx\
|   +-- comfyui-node-dev\
|   +-- maya-vfx\
|   +-- magnific-vfx\
|   +-- seedance-vfx\
+-- connectors\
|   +-- nuke\                 install.ps1 + register.ps1 + bridge\
|   +-- houdini\
|   +-- unreal\
|   +-- maya\
|   +-- blender\              register.ps1 only (official Blender MCP)
|   +-- comfyui\
|   +-- magnific\
+-- docs\
|   +-- GETTING-STARTED.md
|   +-- ARCHITECTURE.md
+-- LICENSE
```

## Attribution and provenance

This toolkit is a working collection: the majority of the skills, agents, and
scripts are original creations, built and battle-tested in production. A
handful are adapted from open source tools, community resources, and prompts
we found useful along the way - some used as-is, some heavily modified. This
collection grew organically inside a working pipeline, so the exact origin of
every piece was not always tracked.

No claim of original authorship is made over anything that came from someone
else. If you recognize your work in here and want credit added, a license
noted, or the content removed, please open an issue - it will be handled
promptly and gladly.

The MCP servers that the connectors register are separate projects by their
own authors, not part of this toolkit:

| Server | Author / Source |
|--------|-----------------|
| Blender MCP | Official Blender MCP (blender.org, ships with Blender 4.5+) |
| UE 5.8 ModelContextProtocol | Epic Games (built into Unreal Engine 5.8) |
| VibeUE | VibeUE (Fab marketplace) |
| comfyui-mcp | npm package by its author |
| ComfyUI_FL-MCP | filliptm (github.com/filliptm/ComfyUI_FL-MCP) |
| Comfy CLI | Comfy Org |
| Magnific MCP | Hosted by Magnific (mcp.magnific.com) |

Third-party tools keep their own licenses; the MIT license in this repo covers
the original content of the toolkit itself.

## Contributing

PRs welcome. Skills follow the standard Claude Code SKILL.md format: a
`skills\<skill-name>\SKILL.md` file with `name` and `description` YAML
frontmatter. Keep everything that ships ASCII-only and free of personal or
studio-specific paths. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for
the plugin format and a PR checklist.

## License

MIT. See [LICENSE](LICENSE).
