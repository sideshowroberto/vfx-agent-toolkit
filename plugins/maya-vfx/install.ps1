# maya-vfx installer (vfx-agent-toolkit)
# Delegates to the maya MCP connector, which installs the bridge and
# registers the MCP server with Claude Code. Extra arguments pass through
# to the connector: -Harness opencode|qwen|none (or -NoRegister) prints the
# MCP server config for another harness instead of registering with Claude.

$connector = Join-Path $PSScriptRoot "..\..\connectors\maya\install.ps1"
if (-not (Test-Path $connector)) {
    # register.ps1-only connectors (no bridge payload)
    $connector = Join-Path $PSScriptRoot "..\..\connectors\maya\register.ps1"
}
if (Test-Path $connector) {
    & $connector @args
    exit $LASTEXITCODE
} else {
    Write-Host "Connector not found: connectors\maya" -ForegroundColor Red
    Write-Host "This installer expects to run from a full vfx-agent-toolkit clone:" -ForegroundColor Yellow
    Write-Host "  git clone https://github.com/sideshowroberto/vfx-agent-toolkit" -ForegroundColor Cyan
    Write-Host "  vfx-agent-toolkit\connectors\maya\install.ps1" -ForegroundColor Cyan
    exit 1
}
