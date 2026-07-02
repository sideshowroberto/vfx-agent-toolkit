# maya/register.ps1
# Re-registers the Maya MCP server with Claude Code.
# Run this after a machine rebuild if Maya userSetup.mel is already configured.

param([string]$MayaPort = "7001")

Write-Host "=== Maya MCP — Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
if (-not (Test-Command "uv")) { Write-Error "uv not found."; exit 1 }

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
