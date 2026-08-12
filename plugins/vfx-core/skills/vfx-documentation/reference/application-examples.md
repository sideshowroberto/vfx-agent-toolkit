# VFX Documentation: Application-Specific Examples

## Nuke

**Common Tasks:**
- Render shot with specific AOVs
- Debug Gizmo/Plugin
- Set up shot template
- Fix color space issues
- Integrate with Shotgun

**Key Files:**
- `~/.nuke/init.py` - Startup scripts
- `~/.nuke/menu.py` - Menu customization
- Custom gizmo files
- Render settings presets

## Houdini

**Common Tasks:**
- Create new HDA
- Debug geometry nodes
- Set up PDG/TOPs pipeline
- Export to game engine
- Fix viewport performance

**Key Files:**
- HDA `OnCreated.py` - HDA initialization
- HDA `PythonModule` - Helper functions
- PDG scheduler nodes
- Export SOPs

## Blender

**Common Tasks:**
- Create addon with MCP integration
- Debug API breaking changes (4.2 -> 4.5+)
- Set up Geometry Nodes
- Export to game engine
- Fix EEVEE_NEXT issues

**Key Files:**
- Addon `__init__.py` - Registration
- Addon operators - Tool implementation
- MCP integration
- Export scripts

## Unreal

**Common Tasks:**
- Add new MCP command
- Debug build failure
- Fix connection issue
- Understand plugin architecture
- Get quick reference

**Key Files:**
- `UnrealMCPBridge.cpp` - Command routing
- `UnrealMCPEditorCommands.cpp` - Handlers
- Python MCP tools

## Multi-Application Projects

### Structure

For VFX pipelines spanning multiple applications:

```
VFX_Pipeline/
+-- MASTER_DOCUMENTATION_INDEX.md        <- Links all apps
+-- UnrealEngine/
|   +-- unreal-mcp-main/
|       +-- DEVELOPMENT_DOCUMENTATION_INDEX.md
+-- Nuke/
|   +-- nuke-scripts/
|       +-- DEVELOPMENT_DOCUMENTATION_INDEX.md
+-- Houdini/
|   +-- hda-library/
|       +-- DEVELOPMENT_DOCUMENTATION_INDEX.md
+-- Blender/
    +-- pipeline-tools/
        +-- DEVELOPMENT_DOCUMENTATION_INDEX.md
```

### Master Index Contents

```markdown
# VFX Pipeline Documentation Index

## Application Documentation

### Unreal Engine MCP
- Index: `UnrealEngine/.../DEVELOPMENT_DOCUMENTATION_INDEX.md`
- Status: Production-ready
- Last Updated: 2025-10-25
- Quick Link: [I Need To...](path/to/index#quick-navigation)

### Nuke Scripts
- Index: `Nuke/.../DEVELOPMENT_DOCUMENTATION_INDEX.md`
- Status: In Development
- Last Updated: 2025-10-24
- Quick Link: [I Need To...](path/to/index#quick-navigation)
```

**Benefits:**
- One master entry point for entire pipeline
- Each application maintains independence
- Cross-application workflow documentation
- Consistent structure everywhere
