# comfyui/register-fl.ps1
# OPTIONAL companion server: registers ComfyUI_FL-MCP (filliptm/ComfyUI_FL-MCP)
# alongside the main comfyui MCP. FL-MCP is installed as a ComfyUI custom node
# and adds 100+ tools including a browser bridge for LIVE canvas operations
# (create/connect nodes on the open canvas, manager operations, workflow files).
#
# Install the custom node first (ComfyUI Manager: search "FL-MCP", or):
#   git clone https://github.com/filliptm/ComfyUI_FL-MCP <ComfyUI>\custom_nodes\ComfyUI_FL-MCP
# Optional: enable workflow writes via .env in the custom node dir:
#   FL_MCP_ENABLE_WORKFLOW_WRITES=true

param(
    [string]$ComfyUIPath = "",
    [string]$ComfyUIUrl = "http://127.0.0.1:8188",
    [string]$Scope = "project",
    # "claude" (default) registers with Claude Code; anything else prints the
    # server definition for that harness instead. -NoRegister = -Harness none.
    [ValidateSet("claude", "opencode", "qwen", "none")]
    [string]$Harness = "claude",
    [switch]$NoRegister
)

if ($NoRegister) { $Harness = "none" }
. (Join-Path $PSScriptRoot "..\mcp-harness.ps1")

Write-Host "=== ComfyUI FL-MCP - Register (optional companion) ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
if ($Harness -eq "claude" -and -not (Test-Command "claude")) { Write-Error "Claude Code not found. Install from https://claude.ai/code, or pass -Harness opencode|qwen|none."; exit 1 }
if (-not (Test-Command "python")) { Write-Error "Python not found. Install from https://python.org (3.12+)"; exit 1 }

if (-not $ComfyUIPath) {
    $ComfyUIPath = Read-Host "Enter path to your ComfyUI folder (the one containing main.py and custom_nodes)"
}
$serverScript = Join-Path $ComfyUIPath "custom_nodes\ComfyUI_FL-MCP\backend\mcp_server.py"
if (-not (Test-Path $serverScript)) {
    Write-Error "FL-MCP not found at: $serverScript`nInstall the ComfyUI_FL-MCP custom node first (see header comment)."
    exit 1
}

if ($Harness -eq "claude") {
    claude mcp add --transport stdio comfyui-fl --scope $Scope --env "COMFYUI_SERVER_URL=$ComfyUIUrl" -- python $serverScript
    Write-Host "  [OK] comfyui-fl registered (scope: $Scope)" -ForegroundColor Green
} else {
    Write-McpServerConfig -Harness $Harness -Name "comfyui-fl" -Command "python" -Arguments @((Resolve-Path $serverScript).Path) `
        -Environment @{ COMFYUI_SERVER_URL = $ComfyUIUrl }
}
Write-Host "  Note: ComfyUI must be running for the tools to work." -ForegroundColor Gray
if ($Harness -eq "claude") { claude mcp list }
