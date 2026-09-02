# houdini-vfx installer
# Installs Houdini MCP server for Claude Code

param(
    [string]$ServerPath = "",
    [string]$HoudiniVersion = "",
    # Target harness. "claude" (default) registers with Claude Code. Any other
    # value skips registration and prints the server definition to paste into
    # that harness's config. -NoRegister is shorthand for -Harness none.
    [ValidateSet("claude", "opencode", "qwen", "none")]
    [string]$Harness = "claude",
    [switch]$NoRegister
)

if ($NoRegister) { $Harness = "none" }
. (Join-Path $PSScriptRoot "..\mcp-harness.ps1")

Write-Host "=== Houdini VFX Plugin Setup ===" -ForegroundColor Cyan
Write-Host "Connects Claude Code to Houdini via MCP.`n"

# --- Helpers ------------------------------------------------------------------

function Test-Command($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue }

# --- 1. Prerequisites ---------------------------------------------------------

if ($Harness -eq "claude" -and -not (Test-Command "claude")) {
    Write-Error "Claude Code not found. Install from https://claude.ai/code, or pass -Harness opencode|qwen|none for another harness."
    exit 1
}
if (-not (Test-Command "uv")) {
    Write-Error "uv not found. Install vfx-base first: ..\vfx-base\install.bat"
    exit 1
}

# --- 2. Detect Houdini prefs folder -------------------------------------------

$docsPath = [Environment]::GetFolderPath("MyDocuments")

if ($HoudiniVersion) {
    $houdiniPrefs = Join-Path $docsPath "houdini$HoudiniVersion"
} else {
    # Auto-detect: find the newest houdiniX.X folder in Documents
    $houdiniPrefs = Get-ChildItem $docsPath -Directory -Filter "houdini*" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^houdini\d+\.\d+$' } |
        Sort-Object Name -Descending |
        Select-Object -First 1 |
        Select-Object -ExpandProperty FullName -ErrorAction SilentlyContinue
}

if (-not $houdiniPrefs -or -not (Test-Path $houdiniPrefs)) {
    Write-Host "Could not auto-detect Houdini prefs folder." -ForegroundColor Yellow
    Write-Host "Expected: $docsPath\houdini20.5 (or similar)"
    $houdiniPrefs = Read-Host "Enter path to your Houdini prefs folder (e.g. $docsPath\houdini20.5)"
    if (-not $houdiniPrefs -or -not (Test-Path $houdiniPrefs)) {
        Write-Error "Houdini prefs folder not found: $houdiniPrefs"
        exit 1
    }
}

Write-Host "Houdini prefs: $houdiniPrefs" -ForegroundColor Green

# --- 3. Copy MCP server files into Houdini prefs ------------------------------

# Bridge files are bundled with this connector
$sourceDir = Join-Path $PSScriptRoot "bridge"

if (-not (Test-Path (Join-Path $sourceDir "houdini_mcp_server.py"))) {
    Write-Error "Houdini MCP server source not found at: $sourceDir"
    exit 1
}

$targetDir = Join-Path $houdiniPrefs "scripts\python\houdinimcp"

if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "Created: $targetDir" -ForegroundColor Green
}

Write-Host "Copying MCP server files to Houdini prefs..." -ForegroundColor White

$filesToCopy = @(
    "__init__.py",
    "server.py",
    "houdini_mcp_server.py",
    "HoudiniMCPRender.py",
    "main.py",
    "pyproject.toml"
)

foreach ($file in $filesToCopy) {
    $src = Join-Path $sourceDir $file
    if (Test-Path $src) {
        Copy-Item $src $targetDir -Force
        Write-Host "  [OK] $file" -ForegroundColor Green
    }
}

$installedServerPath = Join-Path $targetDir "houdini_mcp_server.py"

if (-not (Test-Path $installedServerPath)) {
    Write-Error "Install failed - houdini_mcp_server.py not found after copy."
    exit 1
}

# --- 4. Create Houdini packages entry (auto-loads plugin at Houdini startup) --

$packagesDir = Join-Path $houdiniPrefs "packages"
if (-not (Test-Path $packagesDir)) {
    New-Item -ItemType Directory -Path $packagesDir -Force | Out-Null
}

$packageJson = "{`n  `"env`": [`n    {`n      `"PYTHONPATH`": {`n        `"value`": `"$($houdiniPrefs.Replace('\','/'))/scripts/python`",`n        `"method`": `"prepend`"`n      }`n    }`n  ]`n}"

$packageFile = Join-Path $packagesDir "houdinimcp.json"
Set-Content -Path $packageFile -Value $packageJson -Encoding UTF8
Write-Host "  [OK] Houdini package config: $packageFile" -ForegroundColor Green

# --- 5. Create shelf tool (auto-appears in Houdini after restart) -------------

$toolbarDir = Join-Path $houdiniPrefs "toolbar"
if (-not (Test-Path $toolbarDir)) {
    New-Item -ItemType Directory -Path $toolbarDir -Force | Out-Null
}

$shelfXml = @'
<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
  <tool name="houdinimcp_toggle" label="MCP" icon="MISC_python">
    <toolMenuContext name="viewer">
      <contextNetType>OBJ</contextNetType>
      <contextNetType>SOP</contextNetType>
      <contextNetType>DOP</contextNetType>
      <contextNetType>COP2</contextNetType>
      <contextNetType>SHOP</contextNetType>
      <contextNetType>VOP</contextNetType>
      <contextNetType>CHOP</contextNetType>
    </toolMenuContext>
    <script scriptType="python"><![CDATA[
import hou
import houdinimcp

if hasattr(hou.session, "houdinimcp_server") and hou.session.houdinimcp_server:
    houdinimcp.stop_server()
    hou.ui.displayMessage("Houdini MCP Server stopped")
else:
    houdinimcp.start_server()
    hou.ui.displayMessage("Houdini MCP Server started on localhost:9876")
    ]]></script>
  </tool>
  <toolshelf name="houdinimcp" label="Claude MCP">
    <memberTool name="houdinimcp_toggle"/>
  </toolshelf>
</shelfDocument>
'@

$shelfFile = Join-Path $toolbarDir "houdinimcp.shelf"
Set-Content $shelfFile $shelfXml -Encoding UTF8
Write-Host "  [OK] Shelf tool: $shelfFile" -ForegroundColor Green
Write-Host "       -> 'Claude MCP' shelf appears automatically on next Houdini launch" -ForegroundColor Gray

# --- 6. Create Python Panel (dockable MCP controller with status) -------------

$panelsDir = Join-Path $houdiniPrefs "python_panels"
if (-not (Test-Path $panelsDir)) {
    New-Item -ItemType Directory -Path $panelsDir -Force | Out-Null
}

$panelXml = @'
<?xml version="1.0" encoding="UTF-8"?>
<pythonPanelDocument>
  <interface name="houdinimcp_panel" label="Claude MCP" icon="MISC_python" showNetworkEditorToolbar="0">
    <includeInToolbarMenu menu="viewer" subMenu=""/>
    <script><![CDATA[
from hutil.Qt import QtWidgets, QtCore
import hou

class MCPPanel(QtWidgets.QWidget):
    def __init__(self, **kwargs):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(8)

        title = QtWidgets.QLabel("<b>Claude MCP Server</b>")
        title.setAlignment(QtCore.Qt.AlignCenter)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

        self.start_btn = QtWidgets.QPushButton("Start MCP Server")
        self.stop_btn  = QtWidgets.QPushButton("Stop MCP Server")

        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn.clicked.connect(self.stop_server)

        port_label = QtWidgets.QLabel("Port: 9876  |  Connect: claude mcp list")
        port_label.setAlignment(QtCore.Qt.AlignCenter)
        port_label.setStyleSheet("color: gray; font-size: 10px;")

        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addSpacing(4)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()
        layout.addWidget(port_label)
        self.setLayout(layout)
        self.update_status()

    def update_status(self):
        running = hasattr(hou.session, "houdinimcp_server") and hou.session.houdinimcp_server
        if running:
            self.status_label.setText("Status: <span style='color:green;'>Running</span>")
        else:
            self.status_label.setText("Status: <span style='color:orange;'>Stopped</span>")

    def start_server(self):
        try:
            import houdinimcp
            houdinimcp.start_server()
        except Exception as e:
            hou.ui.displayMessage("Could not start MCP server: " + str(e))
        self.update_status()

    def stop_server(self):
        try:
            import houdinimcp
            houdinimcp.stop_server()
        except Exception as e:
            hou.ui.displayMessage("Could not stop MCP server: " + str(e))
        self.update_status()

def onCreateInterface():
    return MCPPanel()
    ]]></script>
    <help><![CDATA[Controls the Houdini MCP server for Claude Code.
Click Start to allow Claude to connect to this Houdini session on port 9876.]]></help>
  </interface>
</pythonPanelDocument>
'@

$panelFile = Join-Path $panelsDir "houdinimcp.pypanel"
Set-Content $panelFile $panelXml -Encoding UTF8
Write-Host "  [OK] Python Panel: $panelFile" -ForegroundColor Green
Write-Host "       -> Dock via: Windows menu -> Python Panel -> Claude MCP" -ForegroundColor Gray

# --- 7. Set environment variable ----------------------------------------------

[System.Environment]::SetEnvironmentVariable("HOUDINI_MCP_SERVER_PATH", $installedServerPath, "User")
Write-Host "Set HOUDINI_MCP_SERVER_PATH = $installedServerPath" -ForegroundColor Green

# --- 8. Register MCP server with Claude Code ----------------------------------

# --directory makes uv resolve dependencies from the bridge's own
# pyproject.toml (mcp[cli]). Without it, uv resolves from whatever
# directory the MCP client happens to launch the server in, and the
# server dies with ModuleNotFoundError: mcp.
if ($Harness -eq "claude") {
    Write-Host "`nRegistering houdini MCP server..."
    claude mcp add --transport stdio houdini --scope user -- uv run --directory $targetDir python $installedServerPath

    # --- 9. Verify ------------------------------------------------------------

    Write-Host "`n=== Installed MCP Servers ===" -ForegroundColor Green
    claude mcp list
} else {
    Write-McpServerConfig -Harness $Harness -Name "houdini" -Command "uv" `
        -Arguments @("run", "--directory", $targetDir, "python", $installedServerPath)
}

Write-Host "`n=== Houdini VFX Plugin Setup Complete ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. Restart Houdini"
Write-Host "     - 'Claude MCP' shelf appears automatically (click MCP to start server)"
Write-Host "     - Or: Windows -> Python Panels -> Claude MCP for a dockable panel"
Write-Host "  2. Click 'Start MCP Server' (shelf or panel)"
if ($Harness -eq "claude") {
    Write-Host "  3. In Claude Code: /mcp to verify houdini is connected"
} else {
    Write-Host "  3. Add the server definition printed above to your harness config and restart it"
}
Write-Host "  4. Ask the agent: 'Show me the Houdini scene'"
