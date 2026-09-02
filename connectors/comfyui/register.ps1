# comfyui/register.ps1
# Registers the ComfyUI MCP server with Claude Code.
# Use this directly for re-registration (e.g. after moving ComfyUI or switching
# projects); run install.ps1 for the full prerequisite check.

param(
    [string]$ComfyUIPath = "",
    # "claude" (default) registers with Claude Code; anything else prints the
    # server definition for that harness instead. -NoRegister = -Harness none.
    [ValidateSet("claude", "opencode", "qwen", "none")]
    [string]$Harness = "claude",
    [switch]$NoRegister
)

if ($NoRegister) { $Harness = "none" }
. (Join-Path $PSScriptRoot "..\mcp-harness.ps1")

Write-Host "=== ComfyUI MCP - Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

if ($Harness -eq "claude" -and -not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code, or pass -Harness opencode|qwen|none."
    exit 1
}
if (-not (Test-Command "npx")) {
    Write-Error "npx not found. Install Node.js from https://nodejs.org"
    exit 1
}

# Resolve the ComfyUI path
if (-not $ComfyUIPath) {
    $ComfyUIPath = Read-Host "Enter path to your ComfyUI folder (the one containing main.py)"
}

if (-not $ComfyUIPath -or -not (Test-Path $ComfyUIPath)) {
    Write-Error "ComfyUI path not found: $ComfyUIPath"
    exit 1
}
Write-Host "  [OK] ComfyUI: $ComfyUIPath" -ForegroundColor Green

if ($Harness -eq "claude") {
    Write-Host "Registering ComfyUI MCP server..."
    claude mcp add --transport stdio comfyui --scope project --env COMFYUI_URL=http://localhost:8188 --env COMFYUI_PATH=$ComfyUIPath -- cmd /c npx -y comfyui-mcp
    Write-Host "  [OK] comfyui registered" -ForegroundColor Green
    claude mcp list
} else {
    Write-McpServerConfig -Harness $Harness -Name "comfyui" -Command "cmd" -Arguments @("/c", "npx", "-y", "comfyui-mcp") `
        -Environment @{ COMFYUI_URL = "http://localhost:8188"; COMFYUI_PATH = (Resolve-Path $ComfyUIPath).Path }
}
