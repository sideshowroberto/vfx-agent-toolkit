---
name: blender-sculpting
description: Terrain creation, organic modeling, and surface details using Blender sculpting tools. Use for terrain, organic shapes, sculpted details, or when user mentions "sculpt," "terrain," or "organic."
allowed-tools: Read,Write
---

# Blender Sculpting Skill

**Version:** 2.0.0
**Last Updated:** 2026-06-10
**Dependencies:** Blender 5.1+

---

## API Notes (5.1+)

**Viewport shading change (4.5.0+):**
```python
import bpy

# ❌ OLD
# space.shading.type = 'MATERIAL_PREVIEW'

# ✅ NEW (4.5.0+)
space.shading.type = 'MATERIAL'

# Valid modes: 'WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED'
```

**Sculpting operators require Blender context** — use the Blender MCP's `execute_blender_code` tool, which has full context. For high-resolution mesh deformation, direct vertex manipulation is more reliable than sculpt brush operators.

---

## QUICK START

### Create Base Terrain Mesh

```python
import bpy

# Remove existing terrain
for obj in [o for o in bpy.data.objects if o.name.startswith('Terrain')]:
    bpy.data.objects.remove(obj, do_unlink=True)

# Create 100x100 grid terrain
size = 100
subdivisions = 100
vertices = []
faces = []

for y in range(subdivisions + 1):
    for x in range(subdivisions + 1):
        x_pos = (x / subdivisions - 0.5) * size
        y_pos = (y / subdivisions - 0.5) * size
        vertices.append((x_pos, y_pos, 0.0))

for y in range(subdivisions):
    for x in range(subdivisions):
        i = y * (subdivisions + 1) + x
        faces.append([i, i + 1, i + subdivisions + 2, i + subdivisions + 1])

mesh = bpy.data.meshes.new('TerrainMesh')
mesh.from_pydata(vertices, [], faces)
mesh.update()

obj = bpy.data.objects.new('Terrain', mesh)
bpy.context.collection.objects.link(obj)

for poly in mesh.polygons:
    poly.use_smooth = True

print(f'Terrain created: {len(vertices)} vertices, {len(faces)} faces')
```

### Add Multires Modifier

```python
import bpy

terrain = bpy.data.objects.get('Terrain')
if terrain:
    multires = terrain.modifiers.new('Multires', 'MULTIRES')
    print(f'Multires added to {terrain.name}')
    # To subdivide: use Blender UI or bpy.ops.object.multires_subdivide
    # after setting active object and entering Object mode
```

---

## STANDARD WORKFLOWS

### Workflow 1: Direct Vertex Terrain Sculpting

**Step 1: Create Height Variation**

```python
import bpy
import math

terrain = bpy.data.objects.get('Terrain')
mesh = terrain.data

zones = {
    'peak':   {'center': (25, 25),   'radius': 15, 'height': 30},
    'valley': {'center': (-20, -20), 'radius': 10, 'height': -15},
    'ridge':  {'center': (0, 30),    'radius': 20, 'height': 20}
}

for v in mesh.vertices:
    x, y = v.co.x, v.co.y
    height = 0

    for zone in zones.values():
        cx, cy = zone['center']
        radius = zone['radius']
        dist = math.sqrt((x - cx)**2 + (y - cy)**2)
        if dist < radius:
            falloff = 1.0 - (dist / radius)
            height += zone['height'] * falloff

    v.co.z = height

mesh.update()
print(f'Height variation applied to {len(mesh.vertices)} vertices')
```

**Step 2: Apply Erosion Patterns**

```python
import bpy
import math

terrain = bpy.data.objects.get('Terrain')
mesh = terrain.data

for v in mesh.vertices:
    x, y = v.co.x, v.co.y
    noise = 0
    noise += math.sin(x * 0.1) * 2.0
    noise += math.sin(y * 0.15) * 1.5
    noise += math.sin(x * 0.3 + y * 0.3) * 0.8
    v.co.z += noise

mesh.update()
print('Erosion patterns applied')
```

**Step 3: Smooth Terrain**

```python
import bpy

terrain = bpy.data.objects.get('Terrain')
mesh = terrain.data

iterations = 3
for _ in range(iterations):
    new_z = []
    for v in mesh.vertices:
        connected_heights = [v.co.z]
        for edge in mesh.edges:
            if v.index in edge.vertices:
                other_idx = edge.vertices[0] if edge.vertices[1] == v.index else edge.vertices[1]
                connected_heights.append(mesh.vertices[other_idx].co.z)
        new_z.append(sum(connected_heights) / len(connected_heights))

    for v, z in zip(mesh.vertices, new_z):
        v.co.z = z

mesh.update()
print(f'Smoothing applied ({iterations} iterations)')
```

---

### Workflow 2: Vertex Groups for Material Zones

```python
import bpy

terrain = bpy.data.objects.get('Terrain')
mesh = terrain.data

heights = [v.co.z for v in mesh.vertices]
min_h = min(heights)
max_h = max(heights)
h_range = max_h - min_h

groups = {
    'Valley': terrain.vertex_groups.new(name='Valley'),
    'Slope':  terrain.vertex_groups.new(name='Slope'),
    'Peak':   terrain.vertex_groups.new(name='Peak')
}

for v in mesh.vertices:
    norm = (v.co.z - min_h) / h_range if h_range > 0 else 0
    if norm < 0.3:
        groups['Valley'].add([v.index], 1.0, 'ADD')
    elif norm < 0.7:
        groups['Slope'].add([v.index], 1.0, 'ADD')
    else:
        groups['Peak'].add([v.index], 1.0, 'ADD')

print(f'Vertex groups created. Height range: {min_h:.2f} to {max_h:.2f}')
```

---

### Workflow 3: Organic Model Base Creation

**Pattern:** Create low-res base → Add Multires → Set up symmetry → Sculpt details

```python
import bpy
import math

segments = 8
rings = 8
vertices = []
faces = []

for ring in range(rings + 1):
    theta = math.pi * ring / rings
    for seg in range(segments):
        phi = 2 * math.pi * seg / segments
        x = math.sin(theta) * math.cos(phi)
        y = math.sin(theta) * math.sin(phi)
        z = math.cos(theta)
        vertices.append((x, y, z))

for ring in range(rings):
    for seg in range(segments):
        i = ring * segments + seg
        j = i + segments
        i_next = ring * segments + (seg + 1) % segments
        j_next = i_next + segments
        faces.append([i, i_next, j_next, j])

mesh = bpy.data.meshes.new('HeadBase')
mesh.from_pydata(vertices, [], faces)
mesh.update()

obj = bpy.data.objects.new('HeadBase', mesh)
bpy.context.collection.objects.link(obj)
multires = obj.modifiers.new('Multires', 'MULTIRES')

print(f'Organic base created: {len(vertices)} vertices')
```

---

## TROUBLESHOOTING

### Sculpting Operators Fail

For fine-grained sculpt brushes, use Blender's Sculpt Mode UI. For scripted terrain deformation, direct vertex manipulation is both more reliable and more controllable:

```python
import bpy

# Direct vertex modification — always works
mesh = bpy.data.objects['Terrain'].data
for v in mesh.vertices:
    v.co.z += some_height_function(v.co.x, v.co.y)
mesh.update()
```

### Multires Subdivision

`bpy.ops.object.multires_subdivide()` requires an active object in Object mode. With MCP (full context), this works:

```python
import bpy

terrain = bpy.data.objects.get('Terrain')
bpy.context.view_layer.objects.active = terrain
bpy.ops.object.multires_subdivide(modifier='Multires')
```

Alternatively, increase base mesh resolution (subdivisions = 200) instead of using Multires.

### Viewport Shading Not Updating

```python
import bpy

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'  # NOT 'MATERIAL_PREVIEW' (4.5+)
```

---

## VALIDATION CHECKLIST

- [ ] Base mesh created (verify vertex count)
- [ ] Smooth shading applied (`poly.use_smooth = True`)
- [ ] Height variations applied and visually correct
- [ ] Vertex groups created (if using material zones)
- [ ] No mesh errors (check for manifold issues if exporting)
- [ ] Viewport shading uses `'MATERIAL'` not `'MATERIAL_PREVIEW'`

---

## VERSION HISTORY

**v2.0.0** (2026-06-10) - MCP migration
- Removed HTTP Bridge section and curl health-check steps
- Removed `requests.post()` wrappers
- Added `import bpy` to all code blocks
- Updated target: Blender 5.1+
- Added note that bpy.ops sculpt operators work with MCP full context
- Removed absolute paths to blender-ai-compatibility

**v1.1.0** (2025-10-24) - Article III compliance
**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+
