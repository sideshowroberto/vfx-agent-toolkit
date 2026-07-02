# nuke-vfx installer
# Installs Nuke MCP server for Claude Code

param(
    [string]$NukePrefs = ""
)

Write-Host "=== Nuke VFX Plugin Setup ===" -ForegroundColor Cyan
Write-Host "Connects Claude Code to Nuke via MCP.`n"

# --- Helpers ------------------------------------------------------------------

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

# --- 1. Prerequisites ---------------------------------------------------------

if (-not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code and run plugins\vfx-core\install.ps1 first."
    exit 1
}
if (-not (Test-Command "node")) {
    Write-Error "Node.js not found. Install from https://nodejs.org (v18+) then re-run."
    exit 1
}

# --- 2. Install Node.js dependencies for the MCP server ----------------------

$serverDir = Join-Path $PSScriptRoot "bridge"
$resolved  = Resolve-Path $serverDir -ErrorAction SilentlyContinue
if ($resolved) { $serverDir = $resolved.Path }

# Expose bridge directory to Python so nuke_bridge.py can find source files in dev mode
[System.Environment]::SetEnvironmentVariable("NUKE_MCP_BRIDGE_DIR", $serverDir, "User")
Write-Host "  Set NUKE_MCP_BRIDGE_DIR = $serverDir" -ForegroundColor Green

if (-not (Test-Path (Join-Path $serverDir "src\index.js"))) {
    Write-Error "Nuke MCP server not found at: $serverDir\src\index.js"
    exit 1
}

Write-Host "Installing Nuke MCP server dependencies (npm install)..." -ForegroundColor White
Push-Location $serverDir
npm install --silent
Pop-Location
Write-Host "  [OK] Dependencies installed" -ForegroundColor Green

# --- 3. Find .nuke prefs folder -----------------------------------------------

if (-not $NukePrefs) {
    $NukePrefs = Join-Path $env:USERPROFILE ".nuke"
}

if (-not (Test-Path $NukePrefs)) {
    New-Item -ItemType Directory -Path $NukePrefs -Force | Out-Null
    Write-Host "Created: $NukePrefs" -ForegroundColor Green
}

# --- 4. Copy Python bridge files into .nuke -----------------------------------

Write-Host "Copying bridge files to $NukePrefs ..." -ForegroundColor White

$bridgeFiles = @(
    "nuke_bridge.py",
    "nuke_bridge_server.py",
    "nuke_bridge_core.py",
    "nuke_bridge_vfx.py"
)

foreach ($file in $bridgeFiles) {
    $src = Join-Path $serverDir $file
    if (Test-Path $src) {
        Copy-Item $src $NukePrefs -Force
        Write-Host "  [OK] $file" -ForegroundColor Green
    }
}

# --- 5. Create/update .nuke/menu.py to auto-start the bridge -----------------
# menu.py runs at Nuke startup (after GUI is ready), so the server starts
# automatically every time Nuke opens -- no manual steps required.

$menuPy = Join-Path $NukePrefs "menu.py"
$menuEntry = @"

# --- NukeMCP Server (added by vfx-pipeline-tools installer) ---
# Auto-starts the MCP bridge on port 8765 whenever Nuke opens.
import os
_bridge = os.path.join(os.path.expanduser("~"), ".nuke", "nuke_bridge.py")
if os.path.exists(_bridge):
    exec(open(_bridge).read())
else:
    print("[NukeMCP] Warning: nuke_bridge.py not found at " + _bridge)
# --- End NukeMCP Server ---
"@

if (Test-Path $menuPy) {
    $existing = Get-Content $menuPy -Raw
    if ($existing -notmatch "NukeMCP Server") {
        Add-Content $menuPy $menuEntry
        Write-Host "  [OK] Added auto-start to existing menu.py" -ForegroundColor Green
    } else {
        Write-Host "  [OK] menu.py already has NukeMCP entry - skipping" -ForegroundColor Green
    }
} else {
    Set-Content $menuPy $menuEntry -Encoding UTF8
    Write-Host "  [OK] Created $menuPy with auto-start" -ForegroundColor Green
}

# --- 6. Register MCP server with Claude Code ----------------------------------

$serverScript = Join-Path $serverDir "src\index.js"
[System.Environment]::SetEnvironmentVariable("NUKE_MCP_SERVER_PATH", $serverScript, "User")
Write-Host "  Set NUKE_MCP_SERVER_PATH = $serverScript" -ForegroundColor Green

Write-Host "`nRegistering nuke MCP server..."
claude mcp add --transport stdio nuke --scope user -- node $serverScript

# --- 7. Verify ----------------------------------------------------------------

Write-Host "`n=== Installed MCP Servers ===" -ForegroundColor Green
claude mcp list

Write-Host "`n=== Nuke VFX Plugin Setup Complete ===" -ForegroundColor Cyan
Write-Host "Next steps:"
Write-Host "  1. Open Nuke (restart if already open)"
Write-Host "     The MCP bridge starts automatically on port 8765 -- no extra steps needed."
Write-Host "  2. In Claude Code run /mcp to verify nuke is connected"
Write-Host "  3. Ask Claude: 'List all nodes in the current Nuke script'"
Write-Host ""
Write-Host "If the bridge did not start, run this in Nuke's Script Editor:" -ForegroundColor Yellow
Write-Host "  exec(open(r'~/.nuke/nuke_bridge.py').read())" -ForegroundColor White
