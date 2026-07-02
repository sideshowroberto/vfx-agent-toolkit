---
name: blender-materials-shaders
description: Shader nodes, PBR materials, and procedural textures in Blender. Use for material creation, shader setups, PBR workflows, cross-engine compatibility (EEVEE_NEXT/Cycles), or when user mentions "material," "shader," "PBR," "texture," "node tree," or "Principled BSDF."
allowed-tools: Read,Write
---

# Blender Materials & Shaders Skill

**Version:** 2.0.0
**Last Updated:** 2026-06-10
**Dependencies:** Blender 5.1+

---

## Breaking Changes (4.5+ / 5.1+)

```python
import bpy

# Render engine (5.1+)
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Not 'BLENDER_EEVEE'

# Principled BSDF input names changed in 4.5.0 — use names not indices
bsdf.inputs['Transmission Weight'].default_value = 1.0  # was 'Transmission'
bsdf.inputs['Subsurface Weight'].default_value = 0.2    # was 'Subsurface'
bsdf.inputs['Emission Color'].default_value = (1,1,1,1) # was 'Emission'
bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)
```

---

## QUICK START

### Create PBR Material

```python
import bpy

mat = bpy.data.materials.new("PBR_Material")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)
bsdf.inputs['Roughness'].default_value = 0.5
bsdf.inputs['Metallic'].default_value = 0.0

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

# Assign to active object
obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    obj.data.materials.append(mat)
    print(f"Material '{mat.name}' assigned to '{obj.name}'")
```

---

## STANDARD WORKFLOWS

### Workflow 1: Procedural Texture (No Image Files)

**Use When:** Natural materials (stone, wood, rust) without image textures

```python
import bpy

mat = bpy.data.materials.new("Procedural_Stone")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

texcoord = nodes.new('ShaderNodeTexCoord')
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 5.0
noise.inputs['Detail'].default_value = 8.0
noise.inputs['Roughness'].default_value = 0.6

ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.2, 0.2, 0.2, 1.0)  # dark stone
ramp.color_ramp.elements[1].color = (0.7, 0.7, 0.7, 1.0)  # light stone

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Roughness'].default_value = 0.85

output = nodes.new('ShaderNodeOutputMaterial')

links.new(texcoord.outputs['Object'], noise.inputs['Vector'])
links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

print("Procedural stone material created")
```

---

### Workflow 2: Glass / Transparent Material

```python
import bpy

mat = bpy.data.materials.new("Glass")
mat.use_nodes = True
mat.blend_method = 'BLEND'
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Transmission Weight'].default_value = 1.0   # 4.5+ name
bsdf.inputs['IOR'].default_value = 1.45
bsdf.inputs['Roughness'].default_value = 0.0

output = nodes.new('ShaderNodeOutputMaterial')
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

# EEVEE_NEXT: enable ray tracing for refractions
bpy.context.scene.eevee.use_raytracing = True

print("Glass material created")
```

---

### Workflow 3: Material Layering with Mix Shader

**Use When:** Combining materials (metal + rust, clean + dirty, worn + fresh)

```python
import bpy

mat = bpy.data.materials.new("Layered_Metal")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

# Clean metal
bsdf_metal = nodes.new('ShaderNodeBsdfPrincipled')
bsdf_metal.inputs['Metallic'].default_value = 1.0
bsdf_metal.inputs['Roughness'].default_value = 0.2
bsdf_metal.inputs['Base Color'].default_value = (0.7, 0.7, 0.7, 1.0)

# Rust / weathering layer
bsdf_rust = nodes.new('ShaderNodeBsdfPrincipled')
bsdf_rust.inputs['Base Color'].default_value = (0.5, 0.2, 0.1, 1.0)
bsdf_rust.inputs['Roughness'].default_value = 0.9

# Noise-based mask
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 10.0

mix = nodes.new('ShaderNodeMixShader')

output = nodes.new('ShaderNodeOutputMaterial')

links.new(noise.outputs['Fac'], mix.inputs['Fac'])
links.new(bsdf_metal.outputs['BSDF'], mix.inputs[1])
links.new(bsdf_rust.outputs['BSDF'], mix.inputs[2])
links.new(mix.outputs['Shader'], output.inputs['Surface'])

print("Layered metal/rust material created")
```

---

### Workflow 4: Reusable Node Group

```python
import bpy

# Create a reusable weathering node group
group = bpy.data.node_groups.new("Weathering", 'ShaderNodeTree')
group_in = group.nodes.new('NodeGroupInput')
group_out = group.nodes.new('NodeGroupOutput')

# Interface (5.1+ uses interface API)
iface = group.interface
iface.new_socket("Scale", in_out='INPUT', socket_type='NodeSocketFloat')
iface.new_socket("Mask", in_out='OUTPUT', socket_type='NodeSocketColor')

noise = group.nodes.new('ShaderNodeTexNoise')
group.links.new(group_in.outputs['Scale'], noise.inputs['Scale'])
group.links.new(noise.outputs['Color'], group_out.inputs['Mask'])

# Use the group in a material
mat = bpy.data.materials.new("Weathered")
mat.use_nodes = True
nodes = mat.node_tree.nodes
node_group = nodes.new('ShaderNodeGroup')
node_group.node_tree = group
node_group.inputs['Scale'].default_value = 5.0

print(f"Node group '{group.name}' created and referenced")
```

---

## ADVANCED TECHNIQUES

### Cross-Engine Optimization

```python
import bpy

engine = bpy.context.scene.render.engine

if engine == 'BLENDER_EEVEE_NEXT':
    # EEVEE: performance-conscious, keep it simple
    mat.refraction_depth = 0.1
    # Real-time: avoid expensive SSS and volumetrics unless needed
else:  # CYCLES
    # Full ray tracing — enable SSS, caustics, etc.
    bsdf.inputs['Subsurface Weight'].default_value = 0.1
    bsdf.inputs['Subsurface Radius'].default_value = (0.1, 0.05, 0.03)
```

---

## TROUBLESHOOTING

### Material Not Appearing in Viewport

```python
import bpy

# Set viewport to Material Preview or Rendered shading
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'  # NOT 'MATERIAL_PREVIEW' (4.5+)
```

### Shader Socket AttributeError

```python
# 'NodeSocketShader' has no default_value — it only accepts links
# ❌ bsdf.outputs['BSDF'].default_value = ...
# ✅ Just connect it:
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
```

### Material Renders Black

```python
import bpy

nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Verify output node exists
output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
if not output:
    output = nodes.new('ShaderNodeOutputMaterial')

# Ensure BSDF is connected to surface
if not output.inputs['Surface'].is_linked:
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        print("Fixed: reconnected BSDF to output")
```

---

## VALIDATION CHECKLIST

- [ ] Engine set (`BLENDER_EEVEE_NEXT` or `CYCLES`)
- [ ] BSDF inputs use 4.5+ naming convention
- [ ] Material Output node connected
- [ ] Viewport shading = `MATERIAL` (not `MATERIAL_PREVIEW`)
- [ ] Test render validates appearance

---

## VERSION HISTORY

**v2.0.0** (2026-06-10) - MCP migration
- Removed HTTP Bridge requirements and curl steps
- Removed `import requests` / `requests.post()` wrappers
- Added `import bpy` to all code blocks
- Updated target: Blender 5.1+
- Added node group workflow with 5.1+ interface API

**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+, Python 3.11+
