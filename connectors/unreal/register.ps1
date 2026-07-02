# unreal/register.ps1
# Registers the Unreal Engine MCP server with Claude Code.
# Assumes UnrealMCP plugin is already enabled in your UE project.

param([string]$ServerPath = "")

Write-Host "=== Unreal MCP — Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
if (-not (Test-Command "uv")) { Write-Error "uv not found. Run: pip install uv"; exit 1 }

if (-not $ServerPath) { $ServerPath = $env:UNREAL_MCP_SERVER_PATH }

if (-not $ServerPath -or -not (Test-Path (Join-Path $ServerPath "unreal_mcp_server.py"))) {
    $candidates = @(
        # Bundled with this connector (vfx-agent-toolkit\connectors\unreal\bridge)
        (Join-Path $PSScriptRoot "bridge"),
        # Common standalone clone location
        (Join-Path $env:USERPROFILE "Documents\unreal-mcp-main\Python")
    )
    $ServerPath = $candidates | Where-Object { Test-Path (Join-Path $_ "unreal_mcp_server.py") } | Select-Object -First 1
}

if (-not $ServerPath) {
    $ServerPath = Read-Host "Enter path to unreal-mcp-main/Python directory"
    if (-not $ServerPath) { exit 1 }
}

$resolved = Resolve-Path $ServerPath -ErrorAction SilentlyContinue
if ($resolved) { $ServerPath = $resolved.Path }

Write-Host "  [OK] Server: $ServerPath" -ForegroundColor Green
[System.Environment]::SetEnvironmentVariable("UNREAL_MCP_SERVER_PATH", $ServerPath, "User")

Write-Host "Installing Python dependencies..."
Push-Location $ServerPath
uv sync
Pop-Location

$existing = claude mcp list 2>&1
if ($existing -match "unreal-mcp") { claude mcp remove unreal-mcp --scope user 2>&1 | Out-Null }
claude mcp add --transport stdio unreal-mcp --scope user -- cmd /c "cd /d `"$ServerPath`" && uv run unreal_mcp_server.py"
Write-Host "  [OK] unreal-mcp registered" -ForegroundColor Green
claude mcp list
