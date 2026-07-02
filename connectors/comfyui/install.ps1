# comfyui/install.ps1
# Installs and registers the ComfyUI MCP server (comfyui-mcp via npx) with Claude Code.
# Checks prerequisites (Node.js/npx, optional Comfy CLI), validates the ComfyUI
# install path, then calls register.ps1 to do the actual registration.

param([string]$ComfyUIPath = "")

Write-Host "=== ComfyUI MCP - Install ===" -ForegroundColor Cyan
Write-Host "Registers the comfyui-mcp server (runs via npx, talks to a local ComfyUI on port 8188)."
Write-Host ""

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

if (-not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code"
    exit 1
}

if (-not (Test-Command "node")) {
    Write-Error "Node.js not found. Install from https://nodejs.org"
    exit 1
}
if (-not (Test-Command "npx")) {
    Write-Error "npx not found. It ships with Node.js - reinstall from https://nodejs.org"
    exit 1
}
Write-Host "  [OK] Node.js and npx found" -ForegroundColor Green

# Comfy CLI is optional but recommended for headless generation (comfy generate --api-key)
if (Test-Command "comfy") {
    Write-Host "  [OK] Comfy CLI found" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Comfy CLI not found (optional). For headless generation install it with:" -ForegroundColor Yellow
    Write-Host "         pip install comfy-cli" -ForegroundColor Yellow
}

# Resolve the ComfyUI path
if (-not $ComfyUIPath) {
    Write-Host ""
    Write-Host "Enter the path to your ComfyUI folder (the one containing main.py)."
    Write-Host "For a portable install this is the ComfyUI folder INSIDE the portable directory."
    $ComfyUIPath = Read-Host "ComfyUI path"
}

if (-not $ComfyUIPath -or -not (Test-Path $ComfyUIPath)) {
    Write-Error "ComfyUI path not found: $ComfyUIPath"
    exit 1
}
if (-not (Test-Path (Join-Path $ComfyUIPath "main.py"))) {
    Write-Error "main.py not found in: $ComfyUIPath - this does not look like a ComfyUI install."
    exit 1
}
Write-Host "  [OK] ComfyUI: $ComfyUIPath" -ForegroundColor Green

# Register the MCP server
& (Join-Path $PSScriptRoot "register.ps1") -ComfyUIPath $ComfyUIPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "=== ComfyUI MCP Ready ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. Start ComfyUI (it must be listening on http://localhost:8188)"
Write-Host "  2. In Claude Code: /mcp to verify comfyui is connected"
