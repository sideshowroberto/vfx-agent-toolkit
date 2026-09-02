# unreal/register.ps1
# Registers the UE 5.8 NATIVE MCP server with Claude Code.
#
# Unreal Engine 5.8 ships its own MCP server: the "ModelContextProtocol"
# editor plugin runs an HTTP MCP endpoint inside the editor. No bridge code
# or external server process is needed anymore.
#
# One-time setup inside your UE project (before running this script):
#   1. Enable the "ModelContextProtocol" plugin (built into UE 5.8):
#      Edit > Plugins > search "Model Context Protocol" > enable > restart editor.
#   2. RECOMMENDED: install the free "VibeUE" plugin from the Fab marketplace.
#      It extends the native MCP with 25+ toolset services (Blueprints, assets,
#      materials, etc.) exposed via the call_tool interface.
#   3. Configure auto-start in <YourProject>\Config\DefaultEditorPerProjectUser.ini:
#        [/Script/ModelContextProtocol.MCPServerSettings]
#        bAutoStartServer=True
#        Port=8000
#        URLPath=/mcp
#   4. If installing plugins by name in your .uproject, the correct names are
#      "ModelContextProtocol" and "ToolsetRegistry" (NOT "UnrealMCP").
#
# The server only runs while the editor is open. Claude Code connects over HTTP,
# so registration works even when the editor is closed - tools appear once the
# editor (and MCP server) is running.

param(
    [int]$Port = 8000,
    [string]$UrlPath = "/mcp",
    [string]$Scope = "project",
    # "claude" (default) registers with Claude Code; anything else prints the
    # server definition for that harness instead. -NoRegister = -Harness none.
    [ValidateSet("claude", "opencode", "qwen", "none")]
    [string]$Harness = "claude",
    [switch]$NoRegister
)

if ($NoRegister) { $Harness = "none" }
. (Join-Path $PSScriptRoot "..\mcp-harness.ps1")

Write-Host "=== Unreal Engine 5.8 Native MCP - Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
if ($Harness -eq "claude" -and -not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code, or pass -Harness opencode|qwen|none for another harness."
    exit 1
}

$url = "http://127.0.0.1:$Port$UrlPath"

if ($Harness -eq "claude") {
    # Remove any old registrations (community unreal-mcp is retired; re-register ue58-mcp cleanly)
    $existing = claude mcp list 2>&1
    if ($existing -match "unreal-mcp") {
        Write-Host "  Removing retired community 'unreal-mcp' registration..." -ForegroundColor Yellow
        claude mcp remove unreal-mcp 2>&1 | Out-Null
    }
    if ($existing -match "ue58-mcp") {
        claude mcp remove ue58-mcp 2>&1 | Out-Null
    }

    claude mcp add --transport http ue58-mcp $url --scope $Scope
    Write-Host "  [OK] ue58-mcp registered ($url, scope: $Scope)" -ForegroundColor Green
} else {
    Write-McpServerConfig -Harness $Harness -Name "ue58-mcp" -Url $url
}

# Probe: is the editor running with the MCP server up?
try {
    $null = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    Write-Host "  [OK] MCP endpoint is responding - editor is running" -ForegroundColor Green
} catch {
    Write-Host "  [INFO] Endpoint not responding yet. Start the UE editor (with the" -ForegroundColor Yellow
    Write-Host "         ModelContextProtocol plugin enabled) and tools will connect." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Key tools once connected:" -ForegroundColor White
Write-Host "  execute_python_code(code=...)   - run editor Python (import unreal directly)" -ForegroundColor Gray
Write-Host "  list_toolsets() / call_tool(...) - VibeUE toolset services" -ForegroundColor Gray
Write-Host "  discover_python_module/class/function - API discovery" -ForegroundColor Gray
if ($Harness -eq "claude") { claude mcp list }
