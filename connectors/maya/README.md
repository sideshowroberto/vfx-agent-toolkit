# maya — MCP Connector

Connects Claude Code to a live Maya session via Maya's built-in `commandPort`.

**Port:** `7001`
**Bridge:** [PatrickPalmer/MayaMCP](https://github.com/PatrickPalmer/MayaMCP) — no Maya plugin required

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Maya 2023 or 2025 | Tested on both |
| Python 3.10+ | For the MCP server process (outside Maya) |
| [uv](https://docs.astral.sh/uv/) | `winget install astral-sh.uv` |
| [git](https://git-scm.com) | For cloning the bridge |
| Claude Code | `npm install -g @anthropic-ai/claude-code` |

---

## Fresh Install

Run this once on a new machine. It handles everything:

```powershell
.\maya\install.ps1
```

What it does:
1. Clones [PatrickPalmer/MayaMCP](https://github.com/PatrickPalmer/MayaMCP) to `D:\GITHUB\maya-mcp`
2. Installs Python dependencies via `uv sync`
3. Creates `%USERPROFILE%\Documents\maya\scripts\userSetup.mel` with an auto-start `commandPort` entry
4. Sets `MAYA_MCP_SERVER_PATH`, `MAYA_HOST`, `MAYA_PORT` as user env vars
5. Registers the `maya` MCP server with Claude Code

Then open (or restart) Maya. The commandPort opens automatically — no manual steps needed.

### Custom paths

```powershell
# Different bridge location or Maya version
.\maya\install.ps1 -BridgeDir "C:\tools\maya-mcp" -MayaScripts "C:\Users\you\Documents\maya\2025\scripts"
```

---

## Re-register After Machine Rebuild

If the bridge is already cloned and `userSetup.mel` is already configured, just re-register with Claude Code:

```powershell
.\maya\register.ps1
```

---

## How It Works

```
Claude Code
    ↕ stdio
MCP server  (uv run python src/maya_mcp_server.py — spawned by Claude Code)
    ↕ TCP socket
Maya commandPort  (localhost:7001 — auto-opened by userSetup.mel on every Maya launch)
```

**Why this is the simplest bridge in the stack:**
- `commandPort` is built into Maya — no plugin installs, no shelf buttons
- Claude Code manages the MCP server process automatically
- Once installed, both sides start themselves — nothing for the user to do

---

## First-Connection Note

The first time Claude Code connects to Maya's commandPort, Maya may show a firewall or "Allow incoming connections" dialog. Click **Allow**. This only happens once per machine.

---

## Verify It Works

**1. Check Maya's Script Editor**

After opening Maya you should see:
```
// [MayaMCP] commandPort opened on localhost:7001
```

**2. Manual socket test** (run in any Python terminal, Maya must be open)

```python
import socket
s = socket.socket()
s.connect(('localhost', 7001))
s.send(b'import maya.cmds as cmds; print(cmds.ls())\n')
print(s.recv(4096))
s.close()
```

**3. Check Claude Code registration**

```powershell
claude mcp list
# Should include: maya
```

**4. Ask Claude**

> "List all objects in the Maya scene"

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Connection refused` on port 7001 | Maya is not open, or `userSetup.mel` didn't run — check Script Editor for errors |
| `commandPort` error in Script Editor | Port already in use from a previous session; the `if (!commandPort -q ...)` guard handles this automatically |
| `uv: command not found` | Install uv: `winget install astral-sh.uv` then restart terminal |
| Maya not in `C:\Users\...\Documents\maya\scripts` | Run `install.ps1 -MayaScripts "your\scripts\path"` |
| Claude can't find `maya` in MCP list | Run `register.ps1` to re-register |

---

## Env Vars Set by install.ps1

| Var | Value |
|-----|-------|
| `MAYA_MCP_SERVER_PATH` | `D:\GITHUB\maya-mcp\src\maya_mcp_server.py` |
| `MAYA_HOST` | `localhost` |
| `MAYA_PORT` | `7001` |

---

## Skills & Agents

This connector only handles MCP registration. For Maya skills and agents (scene manipulation, materials, rigging), use `claude-plugins-marketplace/plugins/maya-vfx/`.
