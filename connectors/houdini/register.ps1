# houdini/register.ps1
# Registers the Houdini MCP server with Claude Code.
# Assumes bridge is already installed in Houdini prefs.

param(
    [string]$ServerPath = "",
    # "claude" (default) registers with Claude Code; anything else prints the
    # server definition for that harness instead. -NoRegister = -Harness none.
    [ValidateSet("claude", "opencode", "qwen", "none")]
    [string]$Harness = "claude",
    [switch]$NoRegister
)

if ($NoRegister) { $Harness = "none" }
. (Join-Path $PSScriptRoot "..\mcp-harness.ps1")

Write-Host "=== Houdini MCP - Register ===" -ForegroundColor Cyan

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }
if (-not (Test-Command "uv")) { Write-Error "uv not found. Run: pip install uv"; exit 1 }
if ($Harness -eq "claude" -and -not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code, or pass -Harness opencode|qwen|none."
    exit 1
}

if (-not $ServerPath) { $ServerPath = $env:HOUDINI_MCP_SERVER_PATH }

if (-not $ServerPath -or -not (Test-Path $ServerPath)) {
    # Search Houdini prefs
    $docsPath = [Environment]::GetFolderPath("MyDocuments")
    $candidates = Get-ChildItem $docsPath -Directory -Filter "houdini*" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^houdini\d+\.\d+$' } | Sort-Object Name -Descending
    foreach ($v in $candidates) {
        $candidate = Join-Path $v.FullName "scripts\python\houdinimcp\houdini_mcp_server.py"
        if (Test-Path $candidate) { $ServerPath = $candidate; break }
    }
}

if (-not $ServerPath -or -not (Test-Path $ServerPath)) {
    $ServerPath = Read-Host "Enter path to houdini_mcp_server.py"
    if (-not $ServerPath) { Write-Host "Run install.ps1 for full bridge setup."; exit 1 }
}

Write-Host "  [OK] Server: $ServerPath" -ForegroundColor Green
[System.Environment]::SetEnvironmentVariable("HOUDINI_MCP_SERVER_PATH", $ServerPath, "User")

# --directory makes uv resolve dependencies from the bridge's own
# pyproject.toml (installed next to the server script). Without it the
# server dies with ModuleNotFoundError: mcp.
$serverDir = Split-Path $ServerPath -Parent
if ($Harness -eq "claude") {
    claude mcp add --transport stdio houdini --scope user -- uv run --directory $serverDir python $ServerPath
    Write-Host "  [OK] houdini registered" -ForegroundColor Green
    claude mcp list
} else {
    Write-McpServerConfig -Harness $Harness -Name "houdini" -Command "uv" `
        -Arguments @("run", "--directory", $serverDir, "python", $ServerPath)
}
