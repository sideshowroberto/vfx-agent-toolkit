# connectors/setup-deps.ps1
# One-pass dependency install for every bundled connector bridge.
#
# Run once after cloning this repo (or after pulling a bridge update),
# BEFORE registering any MCP servers:
#
#   powershell -ExecutionPolicy Bypass -File connectors\setup-deps.ps1
#
# Why this exists: the bridges do not ship their third-party dependencies.
# A Node bridge started without node_modules dies instantly with
# ERR_MODULE_NOT_FOUND - some MCP clients show that only as a red "failed"
# indicator with no error text. This script closes that gap for every
# bridge in one pass, for ANY MCP client (Claude Code, or others you
# configure by hand).
#
# Safe to re-run; pass -Force to reinstall even when deps look present.

param([switch]$Force)

# Keep EAP at Continue: under PowerShell 5.1, Stop turns redirected native
# stderr into a terminating error. Exit codes are checked explicitly.
$ErrorActionPreference = "Continue"

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

$connectorsRoot = $PSScriptRoot
$failures = @()

Write-Host "=== Connector Dependencies - One-Pass Setup ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. Node bridges: any connector with bridge\package.json needs npm install

$nodeBridges = @(Get-ChildItem $connectorsRoot -Directory | ForEach-Object {
    $pkg = Join-Path $_.FullName "bridge\package.json"
    if (Test-Path $pkg) { Split-Path $pkg -Parent }
})

if ($nodeBridges.Count -gt 0 -and -not (Test-Command "npm")) {
    Write-Host "[FAIL] npm not found. Node bridges need Node.js 18+ (https://nodejs.org):" -ForegroundColor Red
    $nodeBridges | ForEach-Object { Write-Host "       $_" -ForegroundColor Red }
    $failures += "npm not installed"
} else {
    foreach ($dir in $nodeBridges) {
        $modulesDir = Join-Path $dir "node_modules"
        if ((Test-Path $modulesDir) -and -not $Force) {
            Write-Host "[OK]   $dir (node_modules already present)" -ForegroundColor Green
            continue
        }
        Write-Host "[NPM]  Installing dependencies in $dir ..." -ForegroundColor White
        Push-Location $dir
        npm install --no-fund --no-audit
        $npmExit = $LASTEXITCODE
        Pop-Location
        # Verify the product, not the exit code alone: node_modules must exist.
        if ($npmExit -eq 0 -and (Test-Path $modulesDir)) {
            Write-Host "[OK]   $dir" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] npm install did not produce node_modules in $dir (exit $npmExit)" -ForegroundColor Red
            $failures += $dir
        }
    }
}

# --- 2. Python bridges: uv resolves bridge\pyproject.toml deps on first
#        launch. Pre-warm the environment here so the first real launch
#        works even without network access.

$pyBridges = @(Get-ChildItem $connectorsRoot -Directory | ForEach-Object {
    $proj = Join-Path $_.FullName "bridge\pyproject.toml"
    if (Test-Path $proj) { Split-Path $proj -Parent }
})

if ($pyBridges.Count -gt 0) {
    Write-Host ""
    if (-not (Test-Command "uv")) {
        Write-Host "[WARN] uv not found - Python bridges resolve their deps via uv at first" -ForegroundColor Yellow
        Write-Host "       launch. Install uv (https://docs.astral.sh/uv/) before registering:" -ForegroundColor Yellow
        $pyBridges | ForEach-Object { Write-Host "       $_" -ForegroundColor Yellow }
    } else {
        foreach ($dir in $pyBridges) {
            Write-Host "[UV]   Pre-warming Python env for $dir ..." -ForegroundColor White
            uv run --directory $dir python -c "import mcp; print('mcp import OK')"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK]   $dir" -ForegroundColor Green
            } else {
                Write-Host "[FAIL] uv could not resolve dependencies for $dir (exit $LASTEXITCODE)" -ForegroundColor Red
                $failures += $dir
            }
        }
    }
}

# --- 3. Summary ----------------------------------------------------------------

Write-Host ""
if ($failures.Count -gt 0) {
    Write-Host "=== Setup finished with $($failures.Count) failure(s) ===" -ForegroundColor Red
    $failures | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}
Write-Host "=== All connector dependencies ready ===" -ForegroundColor Green
Write-Host "Next: run the install.ps1 / register.ps1 for each app you use"
Write-Host "(see connectors\README.md), then restart Claude Code."
exit 0
