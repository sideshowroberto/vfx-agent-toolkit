# unreal-vfx Plugin

Connects Claude Code to Unreal Engine 5.8 via MCP. Enables Blueprint creation, PCG automation, actor operations, Sequencer workflows, and Python scripting - all from Claude Code.

---

## Before You Install - What Kind of UE Project Do You Need?

The MCP connection works with **any running UE 5.8 Editor instance** with the plugin enabled. The question is what kind of project to run it against. This depends on your role:

---

### Artist

**You need:** A Blueprint-only UE project (your regular production project works fine)

**What Claude can do for you:**
- Answer questions about UE features, nodes, and workflows
- Help you understand Blueprints and explain what they do
- Do research ("how do I set up a camera rig in Sequencer?")
- Help you place and configure actors in your level
- Set up Sequencer tracks and keyframes
- Create simple Blueprints and PCG graphs on request

**What you don't need:** C++ compiler, Visual Studio, or a separate sandbox project.

**Recommended setup:**
- Run the plugin on your existing production project
- Or create a dedicated "sandbox" Blueprint project just for experimenting with Claude

---

### Technical Director / TD

**You need:** A dedicated Blueprint-only sandbox project (separate from production)

**What Claude can do for you:**
- Build and test Blueprint tools, PCG graphs, and automation scripts
- Help design and prototype pipeline workflows
- Create Python scripts for batch operations
- Test tools before migrating them to the production project

**Why a sandbox:** You want to experiment without risk to production assets. A dedicated test project gives you a clean slate. You can migrate working tools to production via standard UE content migration (right-click > Migrate in Content Browser).

**You might also consider a C++ project** (see below) if you plan to build custom C++ tools, extend the engine, or create compiled plugins.

---

### Developer / Pipeline Engineer

**You need:** A C++ UE 5.8 install as your primary sandbox

**What this gives you:**
- Full engine access - extend anything
- Compile custom C++ plugins and distribute them as `.uplugin` packages
- Build tools in C++ and expose them to Blueprints for artists
- Use the C++ project as a development environment, then migrate compiled output to artist BP projects

**The workflow:**
```
C++ UE project (your sandbox)
    Claude Code + MCP
    -> develop + test in C++ sandbox
    -> compile / package
    -> migrate to artist BP projects (no C++ required on their end)
```

**What you need installed:**
- Visual Studio 2022 (Community or higher) with "Game development with C++" workload
- UE 5.8 source build or the standard UE 5.8 install (either works - C++ game projects don't require a source build)

---

## How the MCP Connection Works

```
Claude Code
    -> HTTP (http://127.0.0.1:8000/mcp)
    -> ModelContextProtocol plugin (native, runs inside the UE 5.8 Editor)
    -> UE Python API / VibeUE toolset services
```

The MCP server runs INSIDE the editor - it serves whatever UE project is currently open. Switch projects by reopening UE; the connection follows. No external server process is needed.

---

## Prerequisites

- Unreal Engine 5.8 (any project type - see above)
- `uv` Python package manager (installed by vfx-base)
- The `unreal-mcp-main` Python server (see install notes below)

---

## Installation

```batch
install.bat
```

The installer will:
1. Auto-detect the MCP Python server location
2. Install Python dependencies via `uv`
3. Register the `unreal-mcp` MCP server with Claude Code

If the server can't be auto-detected, you'll be prompted for the path to the `unreal-mcp-main\Python` directory.

> **Getting the MCP server:** The `unreal-mcp-main` repository contains both the UE plugin and the Python MCP server. If you don't have it, clone it from the team repo or ask your pipeline lead.

---

## After Installation

1. Open UE 5.8 with your project
2. Enable the **ModelContextProtocol** plugin: Edit > Plugins > search "Model Context Protocol" > Enable > Restart (recommended: also install **VibeUE** from the Fab marketplace)
3. Set auto-start in Config/DefaultEditorPerProjectUser.ini: bAutoStartServer=True, Port=8000, URLPath=/mcp (see connectors/unreal/register.ps1 header)
4. Open Claude Code and run `/mcp` - `ue58-mcp` should show as connected
5. Test: ask Claude "List all actors in the current level"

---

## Migrating Tools to Artist Projects

When you've built and tested something in your sandbox:

**Blueprints:** Right-click in Content Browser > Migrate > select the destination project

**Python scripts:** Copy to the artist project's `Content/Python/` folder or share via your studio's script distribution system

**C++ plugins:** Package as `.uplugin` - artists enable it via Edit > Plugins, no C++ install needed on their end

---

## Skills Included

| Skill | What it does |
|-------|-------------|
| `unreal-blueprint-automation` | Create and configure Blueprints |
| `unreal-actor-operations` | Spawn, move, and query actors |
| `unreal-pcg-automation` | Build PCG graphs for procedural content |
| `unreal-sequencer-automation` | Level sequences, camera cuts, Sequencer tracks |
| `unreal-python-scripting` | Python API patterns and automation |
| `unreal-vfx-automation` | Foreground plates, image sequences, multi-shot VFX |
| `unreal-mcp-development` | Extend the MCP server itself (developers only) |

## Agents Included

| Agent | What it does |
|-------|-------------|
| `unreal-blueprint-specialist` | Deep Blueprint expertise, compilation, debugging |
| `unreal-pcg-specialist` | PCG graph construction and optimization |
