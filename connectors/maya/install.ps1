# maya/install.ps1
# Installs Maya MCP bridge + copies agents/skills into Claude Code config
#
# NOTE (migration): the previous version of this script hardcoded
# D:\GITHUB\maya-mcp and a self-referencing path into the private
# claude-mcp-connectors checkout. It now uses the bridge bundled with
# this connector and standard user-level Claude Code config paths.

param(
    # Bridge is bundled with this connector; override for an external clone
    [string]$BridgeDir = (Join-Path $PSScriptRoot "bridge"),
    [string]$MayaScripts = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent

Write-Host "=== Maya VFX Plugin Install ===" -ForegroundColor Cyan

# --- 1. Register the MCP server (bundled bridge) -------------------------------

if (-not (Test-Path (Join-Path $BridgeDir "maya_mcp_server.py"))) {
    Write-Error "Maya MCP bridge not found at: $BridgeDir (expected maya_mcp_server.py). Pass -BridgeDir to point at your maya-mcp checkout."
    exit 1
}

$registerScript = Join-Path $scriptDir "register.ps1"
if (Test-Path $registerScript) {
    & $registerScript
} else {
    Write-Host "  register.ps1 not found next to this script - run it separately to register the MCP server." -ForegroundColor Yellow
}

# NOTE: Maya-side setup (userSetup.mel opening commandPort 7001) is not
# automated here. See README.md for the userSetup.mel snippet, or pass
# -MayaScripts to indicate where your Maya scripts directory lives.
if ($MayaScripts) {
    Write-Host "  Maya scripts dir: $MayaScripts" -ForegroundColor Gray
    Write-Host "  Ensure userSetup.mel there opens commandPort 7001 (see README.md)." -ForegroundColor Yellow
}

# --- 2. Copy agent into Claude Code config ------------------------------------

# User-level Claude Code config (works for any user, any workspace)
$agentDest = Join-Path $env:USERPROFILE ".claude\agents"
if (-not (Test-Path $agentDest)) { New-Item -ItemType Directory -Path $agentDest -Force | Out-Null }

$agentSrc = Join-Path $scriptDir "agents\maya-specialist.md"
if (Test-Path $agentSrc) {
    Copy-Item $agentSrc $agentDest -Force
    Write-Host "  [OK] Copied maya-specialist agent" -ForegroundColor Green
}

# --- 3. Copy skills into Claude Code config -----------------------------------

$skillsDest = Join-Path $env:USERPROFILE ".claude\skills"
foreach ($skill in @("maya-scene", "maya-materials")) {
    $skillSrc = Join-Path $scriptDir "skills\$skill"
    $skillDest = Join-Path $skillsDest $skill
    if (Test-Path $skillSrc) {
        Copy-Item $skillSrc $skillDest -Recurse -Force
        Write-Host "  [OK] Copied $skill skill" -ForegroundColor Green
    }
}

Write-Host "`n=== Maya VFX Plugin Install Complete ===" -ForegroundColor Cyan
