# VFX General Rules

## File Format Standards

| Source -> Target | Formats |
|----------------|---------|
| Houdini -> Unreal | `.hda`, `.fbx` (SM_, SK_, M_, T_ naming) |
| Blender -> Unreal | `.fbx` (M_ materials, UCX_/UBX_/USP_ collision) |
| Unreal -> Nuke | `.exr` multi-channel, ACES color space |

## Asset Naming

```
Static Meshes:    SM_AssetName
Skeletal Meshes:  SK_AssetName
Materials:        M_AssetName
Textures:         T_AssetName
Blueprints:       BP_AssetName
Collision:        UCX_/UBX_/USP_AssetName
```

## MCP Image Viewing Pattern

All MCP render tools return a `filepath` (not base64). Use the `Read` tool to view:
```python
result = render_tool(...)  # Returns {"filepath": "C:/temp/render.jpg"}
# Then Read("C:/temp/render.jpg") to view the image
```

## Code Style

- Clear, well-commented code
- Maintainability over clever one-liners
- No hard-coded absolute paths
- Team-shareable solutions
