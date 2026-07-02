---
name: maya-scene
description: Query and manipulate Maya scene objects, transforms, hierarchy, and attributes via MCP commandPort. Use for listing scene contents, creating geometry, setting transforms, parenting objects, selecting, importing/exporting FBX. Triggers on "maya scene", "list objects", "create sphere", "cmds.ls", "FBX export from Maya".
allowed-tools: Read,Write,Bash
---

# Maya Scene Skill

Queries and modifies a live Maya session via the commandPort bridge on `localhost:7001`.

## Prerequisites

- Maya is open with commandPort active (auto-started by `userSetup.mel`)
- Maya MCP bridge running (`D:\GITHUB\maya-mcp`)
- Claude Code MCP entry for `maya` configured

## Common Operations

### Query scene
```python
import maya.cmds as cmds
print(cmds.ls(dag=True, long=True))
```

### Create geometry
```python
import maya.cmds as cmds
sphere = cmds.polySphere(radius=1, subdivisionsX=20, subdivisionsY=20, name='hero_geo')[0]
cmds.setAttr(f'{sphere}.translateY', 1.0)
```

### Parent objects
```python
import maya.cmds as cmds
cmds.parent('child_geo', 'parent_grp')
```

### Export FBX
```python
import maya.cmds as cmds
cmds.loadPlugin('fbxmaya', quiet=True)
cmds.select('hero_geo')
cmds.file(r'C:/exports/hero.fbx', exportSelected=True, type='FBX export', force=True)
```

## Gotchas

- **PyMEL is dead** — always use `maya.cmds` or `maya.api.OpenMaya as om2`
- **Long names** — use `cmds.ls(long=True)` to avoid name conflicts in complex scenes
- **Undo** — wrap destructive operations in `cmds.undoInfo(openChunk=True)` / `closeChunk`
