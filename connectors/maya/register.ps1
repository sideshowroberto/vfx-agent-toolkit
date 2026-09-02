# maya/register.ps1
# Re-registers the Maya MCP server with Claude Code.
# Run this after a machine rebuild if Maya userSetup.mel is already configured.

param(
    [string]$MayaPort = "7001",
    # "claude" (default) registers with Claude Code; anything else prints the
    # server definition for that harness instead. -NoRegister = -Harness none.
    [ValidateSet("claude", "opencode", "qwen", "none")]
    [string]$Harness = "claude",
    [switch]$NoRegister
)

if ($NoRegister) { $Harness = "none" }
. (Join-Path $PSScriptRoot "..\mcp-harness.ps1")

Write-Host "=== Maya MCP - Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
if (-not (Test-Command "uv")) { Write-Error "uv not found."; exit 1 }
if ($Harness -eq "claude" -and -not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code, or pass -Harness opencode|qwen|none."
    exit 1
}

# Prefer bundled bridge/, then fall back to env var path
$BridgeDir = Join-Path $PSScriptRoot "bridge"
if (-not (Test-Path (Join-Path $BridgeDir "maya_mcp_server.py"))) {
    # Fall back to path set by a previous install
    $fromEnv = $env:MAYA_MCP_SERVER_PATH
    if ($fromEnv -and (Test-Path $fromEnv)) {
        $BridgeDir = Split-Path $fromEnv -Parent
    } else {
        Write-Host "Bridge not found. Run install.ps1 for full setup." -ForegroundColor Yellow
        exit 1
    }
}

$ServerScript = Join-Path $BridgeDir "maya_mcp_server.py"
Write-Host "  [OK] Bridge: $BridgeDir" -ForegroundColor Green

[System.Environment]::SetEnvironmentVariable("MAYA_MCP_SERVER_PATH", $ServerScript, "User")
[System.Environment]::SetEnvironmentVariable("MAYA_HOST", "localhost", "User")
[System.Environment]::SetEnvironmentVariable("MAYA_PORT", $MayaPort, "User")

if ($Harness -ne "claude") {
    # Other harnesses get the equivalent "uv run --directory" form: same
    # effect as the cmd /c "cd /d ..." wrapper used for Claude Code below,
    # without the shell indirection.
    $resolvedBridge = (Resolve-Path $BridgeDir).Path
    Write-McpServerConfig -Harness $Harness -Name "maya" -Command "uv" `
        -Arguments @("run", "--directory", $resolvedBridge, "python", (Join-Path $resolvedBridge "maya_mcp_server.py")) `
        -Environment @{ MAYA_HOST = "localhost"; MAYA_PORT = $MayaPort }
    exit 0
}

$existing = claude mcp list 2>&1
if ($existing -match "\bmaya\b") {
    claude mcp remove maya --scope user 2>&1 | Out-Null
}

claude mcp add --transport stdio maya --scope user `
    --env MAYA_HOST=localhost `
    --env MAYA_PORT=$MayaPort `
    -- cmd /c "cd /d `"$BridgeDir`" && uv run python maya_mcp_server.py"

Write-Host "  [OK] maya registered" -ForegroundColor Green
claude mcp list
