# magnific-vfx plugin installer
# Registers the Magnific HTTP MCP server with Claude Code.
# Magnific uses OAuth browser auth - no API key needed during install.

Write-Host "=== Magnific VFX Plugin ===" -ForegroundColor Cyan
Write-Host "Registers the Magnific MCP server (https://mcp.magnific.com)."
Write-Host ""

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

if (-not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code"
    exit 1
}

Write-Host "Registering Magnific MCP server..."
claude mcp add --transport http magnific https://mcp.magnific.com --scope local
Write-Host "  [OK] magnific registered" -ForegroundColor Green

Write-Host ""
Write-Host "=== Magnific VFX Plugin Ready ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. In Claude Code: /mcp to verify magnific is connected"
Write-Host "  2. On first use, Claude Code will open a browser for Magnific OAuth login"
Write-Host "  3. Requires a Magnific account - https://www.magnific.com"
Write-Host ""
Write-Host "Skills installed:"
Write-Host "  - magnific-image-gen   : image generation, models, upscale, variations"
Write-Host "  - magnific-local-upload: local file upload + download pipeline"
Write-Host "  - magnific-video-gen   : video generation from images or prompts"
