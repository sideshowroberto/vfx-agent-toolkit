# unreal-vfx/install.ps1
# Registers the Unreal Engine MCP server with Claude Code.
# See README.md for guidance on which UE project type suits your role.

param(
    [string]$ServerPath = ""
)

Write-Host ""
Write-Host "=== Unreal VFX Plugin Installer ===" -ForegroundColor Cyan
Write-Host "Connects Claude Code to Unreal Engine 5.5 via MCP."
Write-Host ""
Write-Host "NOTE: Before continuing, make sure you have read README.md." -ForegroundColor Yellow
Write-Host "Your UE project type (Artist / TD / Developer) affects how you use this plugin." -ForegroundColor Yellow
Write-Host ""

# --- Check prerequisites -------------------------------------------------------

function Test-Command([string]$cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

if (-not (Test-Command "claude")) {
    Write-Host "Claude Code not found. Run vfx-base/install.bat first." -ForegroundColor Red
    exit 1
}
if (-not (Test-Command "uv")) {
    Write-Host "uv not found. Run vfx-base/install.bat first." -ForegroundColor Red
    exit 1
}

# --- Find MCP Python server ----------------------------------------------------

if (-not $ServerPath) {
    # Search common locations — bundled bridge first, then standalone clones
    $candidates = @(
        # Bundled with this connector (vfx-agent-toolkit\connectors\unreal\bridge)
        (Join-Path $PSScriptRoot "bridge"),
        # Environment variable from a previous install
        $env:UNREAL_MCP_SERVER_PATH,
        # Common standalone clone locations
        (Join-Path $env:USERPROFILE "Documents\unreal-mcp-main\Python"),
        (Join-Path $env:USERPROFILE "Desktop\unreal-mcp-main\Python")
    ) | Where-Object { $_ }

    $ServerPath = $candidates | Where-Object {
        Test-Path (Join-Path $_ "unreal_mcp_server.py")
    } | Select-Object -First 1

    if (-not $ServerPath) {
        Write-Host "Could not auto-detect the Unreal MCP server." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "The MCP server is in the 'unreal-mcp-main' repository." -ForegroundColor White
        Write-Host "If you don't have it, ask your pipeline lead for the repo location." -ForegroundColor White
        Write-Host ""
        $ServerPath = Read-Host "Enter full path to the unreal-mcp-main\Python directory"
    }
}

# Resolve to absolute path
$resolved = Resolve-Path $ServerPath -ErrorAction SilentlyContinue
if ($resolved) { $ServerPath = $resolved.Path }

$ServerScript = Join-Path $ServerPath "unreal_mcp_server.py"
if (-not (Test-Path $ServerScript)) {
    Write-Host "unreal_mcp_server.py not found in: $ServerPath" -ForegroundColor Red
    exit 1
}

Write-Host "  [OK] MCP server: $ServerPath" -ForegroundColor Green
[System.Environment]::SetEnvironmentVariable("UNREAL_MCP_SERVER_PATH", $ServerPath, "User")
Write-Host "  Set UNREAL_MCP_SERVER_PATH = $ServerPath" -ForegroundColor Green

# --- Install Python dependencies -----------------------------------------------

Write-Host ""
Write-Host "Installing Python dependencies..."
Push-Location $ServerPath
uv sync
Pop-Location
Write-Host "  [OK] Dependencies installed" -ForegroundColor Green

# --- Register MCP server -------------------------------------------------------

Write-Host ""
$existing = claude mcp list 2>&1
if ($existing -match "unreal-mcp") {
    Write-Host "  [OK] unreal-mcp already registered - updating path..." -ForegroundColor Green
    claude mcp remove unreal-mcp --scope user 2>&1 | Out-Null
}

claude mcp add --transport stdio unreal-mcp --scope user -- cmd /c "cd /d `"$ServerPath`" && uv run unreal_mcp_server.py"
Write-Host "  [OK] unreal-mcp registered" -ForegroundColor Green

# --- Next steps ----------------------------------------------------------------

Write-Host ""
Write-Host "=== Unreal VFX Plugin Ready ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Open UE 5.5 with your project (see README.md for project type guidance)" -ForegroundColor Gray
Write-Host "  2. Enable the UnrealMCP plugin: Edit > Plugins > search 'UnrealMCP' > Enable > Restart" -ForegroundColor Gray
Write-Host "  3. Open Claude Code and run /mcp to verify unreal-mcp shows as connected" -ForegroundColor Gray
Write-Host "  4. Test: ask Claude 'List all actors in the current level'" -ForegroundColor Gray
Write-Host ""
Write-Host "Skills installed: blueprint-automation, actor-operations, pcg-automation," -ForegroundColor Gray
Write-Host "                  sequencer-automation, python-scripting, vfx-automation, mcp-development" -ForegroundColor Gray
Write-Host ""
