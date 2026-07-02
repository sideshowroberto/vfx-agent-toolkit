# Connectors

Connectors register MCP (Model Context Protocol) servers that bridge Claude
Code to your applications. Plugins teach Claude the techniques; connectors
let it act on the running app - create nodes, query scenes, trigger renders.

Every connector ends by registering its MCP server with Claude Code. Some
also install bridge code inside the application first. Run the script for
each app you use, then restart Claude Code (MCP servers load at startup).

Plugin `install.ps1` files do not duplicate this logic - they delegate to
the scripts in this directory.

| App | Script | What installs | Prerequisites |
|-----|--------|---------------|---------------|
| Nuke | `nuke\install.ps1` | Python bridge into `~\.nuke` + Node MCP server + registration | Nuke 14+, Node.js 18+ |
| Houdini | `houdini\install.ps1` | Bridge files + MCP registration (uv-based server) | Houdini 20+, uv, Python 3.12+ |
| Unreal | `unreal\install.ps1` | Bridge into the UE project + MCP registration | Unreal Engine 5.5, uv, Python 3.12+ |
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
