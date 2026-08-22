# Getting Started

First-time setup for the vfx-agent-toolkit, written for VFX artists who may
be new to Claude Code. Budget 15-20 minutes for the core setup, plus a few
minutes per application connector.

## Prerequisites

Install these before anything else:

| Tool | Why | Install |
|------|-----|---------|
| Claude Code | Runs everything | https://claude.com/claude-code |
| Node.js 18+ | Nuke MCP server, npx-based connectors | https://nodejs.org (LTS) |
| Python 3.12+ | Bridge scripts, ComfyUI tooling | https://python.org (check "Add to PATH") |
| uv | Python-based MCP servers (Houdini, Maya, Blender) | https://docs.astral.sh/uv/getting-started/installation/ |
| Git | Cloning this repo for connector setup | https://git-scm.com |

Verify from PowerShell:

```powershell
claude --version
node --version     # v18 or higher
python --version   # 3.12 or higher (note: the command is python, not python3)
uv --version
```

Windows note: `python3` does not exist on Windows. If a guide or script says
`python3`, use `python`.

## Step 1: Add the marketplace

Inside a Claude Code session:

```
/plugin marketplace add sideshowroberto/vfx-agent-toolkit
```

Expected output: a confirmation that the `vfx-agent-toolkit` marketplace was
added. You can also add a local clone by path instead:

```
/plugin marketplace add C:\path\to\vfx-agent-toolkit
```

## Step 2: Install vfx-core, then app plugins

The foundation plugin goes first - other plugins assume its skills exist:

```
/plugin install vfx-core@vfx-agent-toolkit
```

Then install plugins per project. Only install what you use; every plugin
adds skills that Claude scans on startup:

```
/plugin install nuke-vfx@vfx-agent-toolkit
/plugin install houdini-vfx@vfx-agent-toolkit
```

Run `/plugin` at any time to see what is installed, update, or uninstall.

## Step 3: Run the core installer

One-time setup that registers the shared MCP servers and optionally copies
workspace templates (a starter CLAUDE.md and Windows gotchas reference):

```powershell
plugins\vfx-core\install.ps1
```

What it registers:

| MCP server | Purpose | Key needed? |
|------------|---------|-------------|
| brave-search | Web search for docs and troubleshooting | Free API key from https://brave.com/search/api |
| context7 | Up-to-date library documentation lookup | No |
| desktop-commander | File and process operations | No |

The script prompts for the Brave key. You can skip it and re-run later.

After the script finishes, restart Claude Code, then confirm with:

```
/mcp
```

Expected: brave-search, context7, and desktop-commander listed as connected.

## Step 4: Connector setup per application

Connectors need a local clone of the repo:

```powershell
git clone https://github.com/sideshowroberto/vfx-agent-toolkit.git
cd vfx-agent-toolkit
```

The bridges do not ship their third-party dependencies, so install those
next - one pass covers every connector:

```powershell
powershell -ExecutionPolicy Bypass -File connectors\setup-deps.ps1
```

This runs `npm install` for the Node bridges (Nuke) and pre-warms the
uv-managed Python environments (Houdini, Maya). Skipping it is the number
one cause of a bridge that registers fine but dies the moment it starts
(ERR_MODULE_NOT_FOUND - see Troubleshooting). It matters double if you
point another MCP client (not Claude Code) at these bridges, because only
the scripts in this repo know to install the deps for you.

Then run the section for each app you use. All connectors register the MCP
server with Claude Code; some also copy bridge files into the application.

### Nuke

```powershell
connectors\nuke\install.ps1
```

Copies the Python bridge into your `.nuke` preferences folder (pass
`-NukePrefs` to override the location), installs the MCP server's Node
dependencies, and registers the Nuke MCP. Start Nuke, then start Claude Code;
Claude talks to the running Nuke session.

### Houdini

```powershell
connectors\houdini\install.ps1
```

Copies the bridge files, registers the Houdini MCP (uv-based). Start Houdini
with the bridge active, then Claude Code.

### Unreal Engine

```powershell
connectors\unreal\register.ps1
```

Registers the UE 5.8 NATIVE MCP (no bridge needed). One-time editor setup first: enable the ModelContextProtocol plugin (Edit > Plugins), optionally install VibeUE from the Fab marketplace for 25+ extra toolsets, and set bAutoStartServer=True / Port=8000 / URLPath=/mcp in Config\DefaultEditorPerProjectUser.ini. The server runs inside the editor - tools connect while the editor is open. Full steps are in the register.ps1 header.

### Maya

```powershell
connectors\maya\install.ps1
```

Copies the bridge, registers the Maya MCP. Uses Maya's commandPort. See
`connectors\maya\README.md` for version notes.

### Blender

Blender is different: the MCP add-on is official and ships with Blender 4.5+,
so there is nothing to install - only enable and register.

1. In Blender: Edit > Preferences > Add-ons, search for "MCP", enable the
   MCP add-on, and start the connection.
2. Register the server with Claude Code:

```powershell
connectors\blender\register.ps1
```

### ComfyUI

```powershell
connectors\comfyui\install.ps1
```

Registers the ComfyUI MCP (runs via `npx comfyui-mcp`) and points it at your
ComfyUI install. The server URL defaults to `http://localhost:8188`; set
`COMFYUI_URL` if yours runs elsewhere. For headless generation without the
browser UI, install the Comfy CLI:

```powershell
pip install comfy-cli
```

### Magnific

```powershell
connectors\magnific\install.ps1
```

Registers the hosted Magnific MCP at https://mcp.magnific.com. You need a
Magnific account; the first time Claude uses a Magnific tool, an OAuth page
opens in your browser to authorize.

## Step 5: Verify

Restart Claude Code (required - see troubleshooting), then:

1. `/mcp` - every server you registered should show as connected. App
   servers (Nuke, Houdini, etc.) only connect while the app is running with
   its bridge active.
2. `/plugin` - your installed plugins are listed.
3. Ask Claude something app-specific, e.g. "create a Grade node in Nuke" -
   it should use the MCP tools rather than just describing steps.

## Troubleshooting

**MCP server not showing up after install.** MCP servers load when Claude
Code starts. Restart Claude Code after any config change - this is the
number one gotcha.

**HTTP server fails to connect with a transport error.** The transport type
in MCP config is `"http"`, not `"streamable-http"`. If you hand-edited a
config, check this field.

**`python3` is not recognized.** Windows has no `python3` command. Use
`python`. If `python` is also missing, reinstall Python with "Add python.exe
to PATH" checked.

**Server registers but fails instantly (red status, ERR_MODULE_NOT_FOUND).**
The bridge's dependencies were never installed - a fresh clone has no
node_modules. Run `connectors\setup-deps.ps1` (or `npm install` inside
`connectors\nuke\bridge`), then restart the MCP client. This applies to ANY
MCP client using these bridges, not just Claude Code; some clients show the
failure only as a red indicator with no error text - check the client's MCP
logs for ERR_MODULE_NOT_FOUND to confirm.

**App server shows disconnected.** The DCC bridges (Nuke, Houdini, Unreal,
Maya, Blender) only connect while the application is running with the bridge
loaded. Start the app first, then start (or restart) Claude Code.

**Brave search returns auth errors.** The API key was skipped or is wrong.
Re-run `plugins\vfx-core\install.ps1` or update the key in your MCP config,
then restart Claude Code.

**PowerShell blocks the script.** If you get an execution policy error, run:

```powershell
powershell -ExecutionPolicy Bypass -File connectors\nuke\install.ps1
```

## Next steps

- [ARCHITECTURE.md](ARCHITECTURE.md) - how plugins, skills, agents, and
  connectors fit together, and how to contribute your own.
- [connectors/README.md](../connectors/README.md) - connector reference table.
