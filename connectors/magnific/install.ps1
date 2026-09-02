# magnific-vfx plugin installer
# Registers the Magnific HTTP MCP server with Claude Code.
# Magnific uses OAuth browser auth - no API key needed during install.

param(
    # "claude" (default) registers with Claude Code; anything else prints the
    # server definition for that harness instead. -NoRegister = -Harness none.
    [ValidateSet("claude", "opencode", "qwen", "none")]
    [string]$Harness = "claude",
    [switch]$NoRegister
)

if ($NoRegister) { $Harness = "none" }
. (Join-Path $PSScriptRoot "..\mcp-harness.ps1")

Write-Host "=== Magnific VFX Plugin ===" -ForegroundColor Cyan
Write-Host "Registers the Magnific MCP server (https://mcp.magnific.com)."
Write-Host ""

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

if ($Harness -eq "claude" -and -not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code, or pass -Harness opencode|qwen|none for another harness."
    exit 1
}

$magnificUrl = "https://mcp.magnific.com"
if ($Harness -eq "claude") {
    Write-Host "Registering Magnific MCP server..."
    claude mcp add --transport http magnific $magnificUrl --scope local
    Write-Host "  [OK] magnific registered" -ForegroundColor Green
} else {
    Write-McpServerConfig -Harness $Harness -Name "magnific" -Url $magnificUrl
}

Write-Host ""
Write-Host "=== Magnific VFX Plugin Ready ===" -ForegroundColor Green
Write-Host "Next steps:"
if ($Harness -eq "claude") {
    Write-Host "  1. In Claude Code: /mcp to verify magnific is connected"
    Write-Host "  2. On first use, Claude Code will open a browser for Magnific OAuth login"
} else {
    Write-Host "  1. Add the server definition printed above to your harness config and restart it"
    Write-Host "  2. On first use, your harness must complete the Magnific OAuth login in a browser"
}
Write-Host "  3. Requires a Magnific account - https://www.magnific.com"
Write-Host ""
Write-Host "Skills installed:"
Write-Host "  - magnific-image-gen   : image generation, models, upscale, variations"
Write-Host "  - magnific-local-upload: local file upload + download pipeline"
Write-Host "  - magnific-video-gen   : video generation from images or prompts"
