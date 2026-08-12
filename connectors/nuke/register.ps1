# nuke/register.ps1
# Registers the Nuke MCP server with Claude Code.
# Assumes bridge files are already in ~/.nuke/ and server script exists.

param([string]$ServerPath = "")

Write-Host "=== Nuke MCP - Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
if (-not (Test-Command "node")) { Write-Error "Node.js not found."; exit 1 }

# Resolve server path
if (-not $ServerPath) { $ServerPath = $env:NUKE_MCP_SERVER_PATH }

if (-not $ServerPath -or -not (Test-Path $ServerPath)) {
    $nukePrefs = Join-Path $env:USERPROFILE ".nuke"
    $candidates = @(
        (Join-Path $PSScriptRoot "bridge\src\index.js"),   # bundled (preferred)
        (Join-Path $nukePrefs "nuke-mcp\src\index.js"),    # previously installed location
        (Join-Path $env:USERPROFILE "Documents\nuke-mcp-main\src\index.js")
    )
    $ServerPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $ServerPath -or -not (Test-Path $ServerPath)) {
    $ServerPath = Read-Host "Enter path to nuke-mcp/src/index.js"
    if (-not $ServerPath -or -not (Test-Path $ServerPath)) {
        Write-Host "Not found. Run install.ps1 for full bridge setup." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "  [OK] Server: $ServerPath" -ForegroundColor Green
[System.Environment]::SetEnvironmentVariable("NUKE_MCP_SERVER_PATH", $ServerPath, "User")

claude mcp add --transport stdio nuke --scope user -- node $ServerPath
Write-Host "  [OK] nuke registered" -ForegroundColor Green
claude mcp list
