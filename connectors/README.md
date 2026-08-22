# Connectors

Connectors register MCP (Model Context Protocol) servers that bridge Claude
Code to your applications. Plugins teach Claude the techniques; connectors
let it act on the running app - create nodes, query scenes, trigger renders.

Every connector ends by registering its MCP server with Claude Code. Some
also install bridge code inside the application first. Run the script for
each app you use, then restart Claude Code (MCP servers load at startup).

Plugin `install.ps1` files do not duplicate this logic - they delegate to
the scripts in this directory.

## Install dependencies first (fresh clone)

The bundled bridges do not ship their third-party dependencies. After
cloning (or after pulling a bridge update), install them in one pass:

```powershell
powershell -ExecutionPolicy Bypass -File connectors\setup-deps.ps1
```

- **Node bridges** (Nuke): need `npm install` inside `connectors\<app>\bridge`.
  Without node_modules the server dies at startup with ERR_MODULE_NOT_FOUND -
  some MCP clients show that only as a red "failed" indicator with no error
  text.
- **Python bridges** (Houdini, Maya): dependencies resolve automatically via
  `uv` from the bridge's pyproject.toml. setup-deps.ps1 pre-warms the
  environment so the first launch works even offline.
- **npx-based and hosted servers** (ComfyUI, Magnific, Unreal, Blender):
  nothing to install here; npx fetches on demand (first run needs network).

Each app's `install.ps1` also installs its own bridge deps, and `register.ps1`
scripts check for missing Node deps - but if you point a DIFFERENT MCP client
(not Claude Code) at a bridge in this repo, nothing runs those scripts for
you: run `setup-deps.ps1` yourself after cloning.

| App | Script | What installs | Prerequisites |
|-----|--------|---------------|---------------|
| Nuke | `nuke\install.ps1` | Python bridge into `~\.nuke` + Node MCP server + registration | Nuke 14+, Node.js 18+ |
| Houdini | `houdini\install.ps1` | Bridge files + MCP registration (uv-based server) | Houdini 20+, uv, Python 3.12+ |
| Unreal | `unreal\register.ps1` | Registers the UE 5.8 native MCP (HTTP :8000/mcp) | UE 5.8 with ModelContextProtocol plugin enabled; VibeUE recommended |
| ComfyUI FL (optional) | `comfyui\register-fl.ps1` | Registers ComfyUI_FL-MCP - live canvas operations (100+ tools) | ComfyUI_FL-MCP custom node installed in ComfyUI |
| Maya | `maya\install.ps1` | Bridge (commandPort) + MCP registration - see `maya\README.md` | Maya 2024+ |
| Blender | `blender\register.ps1` | Registration only - uses the official Blender MCP from blender.org | Blender 4.5+ with the bundled MCP add-on enabled in Preferences |
| ComfyUI | `comfyui\install.ps1` | Registers the ComfyUI MCP (`npx comfyui-mcp`) | Local ComfyUI install, Node.js 18+; `COMFYUI_URL` defaults to `http://localhost:8188`; Comfy CLI (`pip install comfy-cli`) recommended for headless generation |
| Magnific | `magnific\install.ps1` | Registers the hosted MCP at `https://mcp.magnific.com` | Magnific account; OAuth opens in your browser on first use |

Step-by-step per-app instructions with expected output:
[docs/GETTING-STARTED.md](../docs/GETTING-STARTED.md)

Notes:

- The DCC servers (Nuke, Houdini, Unreal, Maya, Blender) only show as
  connected while the application is running with its bridge active.
- If a hand-edited config uses an HTTP transport, the type is `"http"`,
  not `"streamable-http"`.
- On Windows the Python command is `python`, never `python3`.
