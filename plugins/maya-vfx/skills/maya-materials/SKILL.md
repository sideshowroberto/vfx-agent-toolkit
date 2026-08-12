---
name: maya-materials
description: Create and assign materials in Maya via MCP - Arnold (aiStandardSurface), Lambert, Blinn, and USD Preview Surface. Use for shader creation, texture assignment, material assignment to geometry, and look dev workflows. Triggers on "maya material", "assign shader", "aiStandardSurface", "maya texture", "look dev".
allowed-tools: Read,Write,Bash
---

# Maya Materials Skill

Creates and assigns shaders in a live Maya session via the commandPort bridge.

## Prerequisites

- Maya is open with commandPort active
- For Arnold shaders: Arnold for Maya (MtoA) loaded

## Standard Surface (Arnold - preferred for production)

```python
import maya.cmds as cmds

# Create shader + shading group
shader = cmds.shadingNode('aiStandardSurface', asShader=True, name='hero_mat')
sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='hero_matSG')
cmds.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader')

# Set base color
cmds.setAttr(f'{shader}.baseColor', 0.8, 0.2, 0.1, type='double3')
cmds.setAttr(f'{shader}.metalness', 0.0)
cmds.setAttr(f'{shader}.specularRoughness', 0.3)

# Assign to geometry
cmds.sets('hero_geo', edit=True, forceElement='hero_matSG')
```

## File Texture

```python
import maya.cmds as cmds

file_node = cmds.shadingNode('file', asTexture=True, name='diffuse_tex')
p2d = cmds.shadingNode('place2dTexture', asUtility=True)
cmds.connectAttr(f'{p2d}.outUV', f'{file_node}.uvCoord')
cmds.setAttr(f'{file_node}.fileTextureName', r'D:/textures/hero_diffuse.png', type='string')
cmds.connectAttr(f'{file_node}.outColor', f'{shader}.baseColor')
```

## Lambert (fast lookdev)

```python
import maya.cmds as cmds

shader = cmds.shadingNode('lambert', asShader=True, name='quick_mat')
sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='quick_matSG')
cmds.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader')
cmds.setAttr(f'{shader}.color', 0.5, 0.7, 0.9, type='double3')
cmds.sets('hero_geo', edit=True, forceElement='quick_matSG')
```

## Gotchas

- **Arnold plugin** must be loaded: `cmds.loadPlugin('mtoa', quiet=True)` before using `aiStandardSurface`
- **ColorSpace** - set `file_node.colorSpace` to `'sRGB'` for diffuse, `'Raw'` for normal/roughness maps
- **UDP paths** - use forward slashes or raw strings for texture paths on Windows
