# VFX Pipeline Workspace

This is a Claude Code project pre-loaded with VFX pipeline skills and agents.

---

## Tools

- **Unreal Engine 5.8** - cinematics, PCG, Sequencer
- **Nuke** - compositing
- **Blender** - 3D modeling, animation, simulation
- **Houdini** - procedural generation, FX
- **ComfyUI** - AI image generation
- **Python** - cross-application scripting

---

## Working Style

- Maintainability over clever code - production environments need readable, team-shareable solutions
- Prefer Blueprint solutions in Unreal (use C++ only when necessary)
- No hard-coded absolute paths - use relative paths or environment variables
- Windows environment (PowerShell, backslash paths)
- Clear, well-commented code

---

## Cross-Application File Formats

| Source -> Target | Formats |
|----------------|---------|
| Houdini -> Unreal | `.hda`, `.fbx` (SM_, SK_, M_, T_ naming) |
| Blender -> Unreal | `.fbx` (M_ materials, UCX_/UBX_/USP_ collision) |
| Unreal -> Nuke | `.exr` multi-channel, ACES color space |

## Asset Naming

```
Static Meshes:    SM_AssetName
Skeletal Meshes:  SK_AssetName
Materials:        M_AssetName
Textures:         T_AssetName
Blueprints:       BP_AssetName
Collision:        UCX_/UBX_/USP_AssetName
```

---

## MCP Servers

MCP servers connect Claude directly to VFX applications. Run `/mcp` to see active servers.

**Base servers** (registered by `install.ps1`):
- `brave-search` - web research
- `context7` - library documentation lookup
- `desktop-commander` - file and process operations

**App servers** (registered via `connectors/<app>` in vfx-agent-toolkit):
- `nuke` - Nuke compositing control (port 8765)
- `houdini` - Houdini scene control (port 9876)
- `ue58-mcp` - Unreal Engine 5.8 control (native MCP, HTTP port 8000)
- `comfyui` - AI image generation

**Note on Blender:** Uses the official Blender MCP (blender.org). Enable the MCP add-on in Blender preferences and register via `connectors\blender\register.ps1`.

**MCP image pattern:** Render tools return a `filepath`, not base64. Use the `Read` tool to view the image after a render call.

---

## Skills

Run `/skills` to see all available skills. Core skills pre-loaded in this project:

| Skill | What it does |
|-------|-------------|
| `git-guardrails-claude-code` | Block destructive git operations before they execute |
| `grill-me` | Stress-test a plan before building - surfaces assumptions and gaps |
| `gap-check` | Audit Claude's knowledge gaps against a plan before implementing |
| `vfx-plan` | Structured planning framework for VFX tasks |
| `brave-search` | AI-enhanced web research via Brave Search API |
| `vfx-documentation` | Generate and maintain VFX documentation |
| `agent-creation-update` | Create and update VFX agents |
| `skill-creation-update` | Create and update VFX skills |
| `development-management` | Spec-driven development workflows |
| `wrap-session` | End-of-session wrap-up: save memories, session log, handoff plan |

App-specific skills (Nuke, Houdini, Unreal, Blender, etc.) are installed via the vfx-agent-toolkit marketplace: `/plugin install <app>-vfx@vfx-agent-toolkit`.

---

## Agents

Agents are auto-delegated when relevant - no manual invocation needed.

| Agent | Triggered for |
|-------|--------------|
| `search-specialist` | Deep web research, technical documentation |
| `documentation-specialist` | Generating and updating project docs |
| `testing-specialist` | Validating scripts and checking outputs |
| `python-specialist` | Type safety, async, testing methodology |
| `python-refactoring-specialist` | Systematic code refactoring across files |

---

## Getting Help

- `/help` - Claude Code help
- `/skills` - list available skills
- `/mcp` - verify MCP server connections
- `/grill-me` - stress-test your plan before building
- `/gap-check` - audit unknowns before implementing
- `/vfx-plan` - structured planning for complex tasks
