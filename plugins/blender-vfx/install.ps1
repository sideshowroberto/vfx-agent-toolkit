# blender-vfx installer (vfx-agent-toolkit)
# Delegates to the blender MCP connector, which installs the bridge and
# registers the MCP server with Claude Code.

$connector = Join-Path $PSScriptRoot "..\..\connectors\blender\install.ps1"
if (-not (Test-Path $connector)) {
    # register.ps1-only connectors (no bridge payload)
    $connector = Join-Path $PSScriptRoot "..\..\connectors\blender\register.ps1"
}
if (Test-Path $connector) {
    & $connector
    exit $LASTEXITCODE
} else {
    Write-Host "Connector not found: connectors\blender" -ForegroundColor Red
    Write-Host "This installer expects to run from a full vfx-agent-toolkit clone:" -ForegroundColor Yellow
    Write-Host "  git clone https://github.com/sideshowroberto/vfx-agent-toolkit" -ForegroundColor Cyan
    Write-Host "  vfx-agent-toolkit\connectors\blender\install.ps1" -ForegroundColor Cyan
    exit 1
}
