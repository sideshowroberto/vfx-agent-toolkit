# vfx-core installer (vfx-agent-toolkit foundation)
# Registers core MCP servers (brave-search, context7, desktop-commander) with Claude Code
# and optionally copies workspace templates (CLAUDE.md, rules) into your project.
# Skills and agents are installed by Claude Code's plugin system -- no extra step needed.

param(
    [switch]$SkipBraveSearch,
    [switch]$SkipContext7,
    [switch]$SkipDesktopCommander,
    [string]$WorkspacePath = ""
)

Write-Host "=== vfx-core Setup (vfx-agent-toolkit) ===" -ForegroundColor Cyan
Write-Host "Registers core MCP servers and offers workspace templates."
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Prerequisites
# ---------------------------------------------------------------------------

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

$errors = @()
if (-not (Test-Command "claude")) { $errors += "Claude Code not found. Install from https://claude.ai/code" }
if (-not (Test-Command "node"))   { $errors += "Node.js not found. Install from https://nodejs.org (v18+)" }
if (-not (Test-Command "python")) { $errors += "Python not found. Install from https://python.org (3.12+)" }
if (-not (Test-Command "uv"))     { $errors += "uv not found. Install: https://docs.astral.sh/uv/" }

if ($errors.Count -gt 0) {
    Write-Host "`nMissing prerequisites:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "Prerequisites OK" -ForegroundColor Green
Write-Host ""

# ---------------------------------------------------------------------------
# 2. MCP server registration (user scope - available in all projects)
# ---------------------------------------------------------------------------

Write-Host "Registering MCP servers (user scope)..." -ForegroundColor Cyan
Write-Host ""

if (-not $SkipBraveSearch) {
    Write-Host "Brave Search adds web search capability to Claude." -ForegroundColor White
    Write-Host "API key available at: https://brave.com/search/api/" -ForegroundColor Gray
    $braveKey = Read-Host "Enter Brave Search API key (or press Enter to skip)"
    if ($braveKey) {
        claude mcp add --transport stdio brave-search --scope user --env "BRAVE_API_KEY=$braveKey" -- cmd /c npx -y @modelcontextprotocol/server-brave-search
        [System.Environment]::SetEnvironmentVariable("BRAVE_API_KEY", $braveKey, "User")
        Write-Host "  [OK] brave-search registered" -ForegroundColor Green
    } else {
        Write-Host "  Skipped brave-search (re-run install.ps1 to add later)" -ForegroundColor Yellow
    }
    Write-Host ""
}

if (-not $SkipContext7) {
    Write-Host "  Adding context7 (library docs lookup - no API key required)..."
    claude mcp add --transport http context7 https://mcp.context7.com/mcp --scope user
    Write-Host "  [OK] context7 registered" -ForegroundColor Green
}

if (-not $SkipDesktopCommander) {
    Write-Host "  Adding desktop-commander..."
    claude mcp add --transport stdio desktop-commander --scope user -- cmd /c npx @wonderwhy-er/desktop-commander@latest
    Write-Host "  [OK] desktop-commander registered" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 3. Workspace templates (optional)
# ---------------------------------------------------------------------------

$templates = Join-Path $PSScriptRoot "templates"
if (Test-Path $templates) {
    Write-Host ""
    if (-not $WorkspacePath) {
        $WorkspacePath = Read-Host "Copy workspace templates (CLAUDE.md, rules) into a project? Enter path or press Enter to skip"
    }
    if ($WorkspacePath) {
        if (Test-Path $WorkspacePath) {
            $claudeMd = Join-Path $WorkspacePath "CLAUDE.md"
            if (Test-Path $claudeMd) {
                Write-Host "  CLAUDE.md already exists in target - not overwriting" -ForegroundColor Yellow
            } else {
                Copy-Item (Join-Path $templates "CLAUDE.md") $claudeMd
                Write-Host "  [OK] CLAUDE.md template copied" -ForegroundColor Green
            }
            $rulesDir = Join-Path $WorkspacePath ".claude\rules"
            New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null
            Get-ChildItem $templates -Filter "*.md" | Where-Object { $_.Name -ne "CLAUDE.md" } | ForEach-Object {
                Copy-Item $_.FullName $rulesDir -Force
                Write-Host "  [OK] rule copied: $($_.Name)" -ForegroundColor Green
            }
        } else {
            Write-Host "  Path not found: $WorkspacePath" -ForegroundColor Yellow
        }
    }
}

# ---------------------------------------------------------------------------
# 4. Verify + next steps
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "=== Registered MCP Servers ===" -ForegroundColor Green
claude mcp list

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Run /mcp in Claude Code to verify servers are active" -ForegroundColor Gray
Write-Host "  2. Install app plugins per project:" -ForegroundColor Gray
Write-Host "       /plugin install nuke-vfx@vfx-agent-toolkit" -ForegroundColor Cyan
Write-Host "       /plugin install blender-vfx@vfx-agent-toolkit" -ForegroundColor Cyan
Write-Host "  3. App plugins that talk to a DCC also need their connector:" -ForegroundColor Gray
Write-Host "       run connectors\<app>\install.ps1 from your vfx-agent-toolkit clone" -ForegroundColor Cyan
