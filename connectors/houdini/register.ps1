# houdini/register.ps1
# Registers the Houdini MCP server with Claude Code.
# Assumes bridge is already installed in Houdini prefs.

param([string]$ServerPath = "")

Write-Host "=== Houdini MCP - Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
if (-not (Test-Command "uv")) { Write-Error "uv not found. Run: pip install uv"; exit 1 }

if (-not $ServerPath) { $ServerPath = $env:HOUDINI_MCP_SERVER_PATH }

if (-not $ServerPath -or -not (Test-Path $ServerPath)) {
    # Search Houdini prefs
    $docsPath = [Environment]::GetFolderPath("MyDocuments")
    $candidates = Get-ChildItem $docsPath -Directory -Filter "houdini*" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^houdini\d+\.\d+$' } | Sort-Object Name -Descending
    foreach ($v in $candidates) {
        $candidate = Join-Path $v.FullName "scripts\python\houdinimcp\houdini_mcp_server.py"
        if (Test-Path $candidate) { $ServerPath = $candidate; break }
    }
}

if (-not $ServerPath -or -not (Test-Path $ServerPath)) {
    $ServerPath = Read-Host "Enter path to houdini_mcp_server.py"
    if (-not $ServerPath) { Write-Host "Run install.ps1 for full bridge setup."; exit 1 }
}

Write-Host "  [OK] Server: $ServerPath" -ForegroundColor Green
[System.Environment]::SetEnvironmentVariable("HOUDINI_MCP_SERVER_PATH", $ServerPath, "User")

# --directory makes uv resolve dependencies from the bridge's own
# pyproject.toml (installed next to the server script). Without it the
# server dies with ModuleNotFoundError: mcp.
$serverDir = Split-Path $ServerPath -Parent
claude mcp add --transport stdio houdini --scope user -- uv run --directory $serverDir python $ServerPath
Write-Host "  [OK] houdini registered" -ForegroundColor Green
claude mcp list
