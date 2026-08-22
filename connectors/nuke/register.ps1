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

# Ensure Node dependencies exist next to the server. A fresh clone has no
# node_modules, and without it the server dies at startup with
# ERR_MODULE_NOT_FOUND (@modelcontextprotocol/sdk) - in some MCP clients
# that shows only as a red "failed" indicator with no error text.
$bridgeDir = Split-Path (Split-Path $ServerPath -Parent) -Parent
if ((Test-Path (Join-Path $bridgeDir "package.json")) -and
    -not (Test-Path (Join-Path $bridgeDir "node_modules"))) {
    if (-not (Test-Command "npm")) {
        Write-Error "node_modules missing in $bridgeDir and npm not found. Install Node.js 18+ from https://nodejs.org, then re-run."
        exit 1
    }
    Write-Host "  node_modules missing - running npm install in $bridgeDir ..." -ForegroundColor Yellow
    Push-Location $bridgeDir
    npm install --no-fund --no-audit
    $npmExit = $LASTEXITCODE
    Pop-Location
    if ($npmExit -ne 0 -or -not (Test-Path (Join-Path $bridgeDir "node_modules"))) {
        Write-Error "npm install failed in $bridgeDir (exit $npmExit). Fix and re-run."
        exit 1
    }
    Write-Host "  [OK] Node dependencies installed" -ForegroundColor Green
}

[System.Environment]::SetEnvironmentVariable("NUKE_MCP_SERVER_PATH", $ServerPath, "User")

claude mcp add --transport stdio nuke --scope user -- node $ServerPath
Write-Host "  [OK] nuke registered" -ForegroundColor Green
claude mcp list
