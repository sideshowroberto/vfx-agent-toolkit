# blender/register.ps1
# Registers the official Blender MCP server with Claude Code.
#
# This is the OFFICIAL Blender MCP (blender.org's blender-mcp). It ships with
# Blender 4.5+ and is also available from blender.org. The server is run from
# a local checkout/install directory via uv.
#
# IMPORTANT: The Blender-side MCP add-on must be enabled in Blender
# (Edit > Preferences > Add-ons) for the connection to work.

param(
    [string]$BlenderMcpDir = "",
    # "claude" (default) registers with Claude Code; anything else prints the
    # server definition for that harness instead. -NoRegister = -Harness none.
    [ValidateSet("claude", "opencode", "qwen", "none")]
    [string]$Harness = "claude",
    [switch]$NoRegister
)

if ($NoRegister) { $Harness = "none" }
. (Join-Path $PSScriptRoot "..\mcp-harness.ps1")

Write-Host "=== Blender MCP - Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

if ($Harness -eq "claude" -and -not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code, or pass -Harness opencode|qwen|none for another harness."
    exit 1
}

if (-not (Test-Command "uv")) {
    Write-Error "uv not found. Install it first: https://docs.astral.sh/uv/"
    exit 1
}
Write-Host "  [OK] uv found" -ForegroundColor Green

# Resolve the Blender MCP directory
if (-not $BlenderMcpDir) {
    $BlenderMcpDir = Read-Host "Enter path to the Blender MCP directory (the folder containing the blender-mcp project)"
}

if (-not $BlenderMcpDir -or -not (Test-Path $BlenderMcpDir)) {
    Write-Error "Blender MCP directory not found: $BlenderMcpDir"
    exit 1
}
Write-Host "  [OK] Blender MCP dir: $BlenderMcpDir" -ForegroundColor Green

if ($Harness -eq "claude") {
    Write-Host "Registering Blender MCP server..."
    claude mcp add --transport stdio blender --scope project -- uv --directory $BlenderMcpDir run blender-mcp
    Write-Host "  [OK] blender registered" -ForegroundColor Green
} else {
    Write-McpServerConfig -Harness $Harness -Name "blender" -Command "uv" `
        -Arguments @("--directory", (Resolve-Path $BlenderMcpDir).Path, "run", "blender-mcp")
}

Write-Host ""
Write-Host "=== Blender MCP Ready ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. In Blender: Edit > Preferences > Add-ons, enable the Blender MCP add-on"
if ($Harness -eq "claude") {
    Write-Host "  2. In Claude Code: /mcp to verify blender is connected"
    claude mcp list
} else {
    Write-Host "  2. Add the server definition printed above to your harness config and restart it"
}
