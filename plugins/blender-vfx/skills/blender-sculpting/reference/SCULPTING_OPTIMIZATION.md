# Blender Sculpting - Optimization and Workflows

**Part of:** blender-sculpting skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

Performance optimization strategies, dynamic topology workflows, remeshing techniques, and export workflows. Use this reference when:
- Working with high-resolution sculpts (>1M vertices)
- Experiencing performance issues
- Preparing sculpts for game engines or 3D printing
- Optimizing topology for animation
- Exporting to other applications

---

## Performance Optimization

### **Vertex Count Management**

**Target Vertex Counts by Purpose:**
- Game engines (real-time): 5k-50k vertices
- Film/VFX (offline): 500k-5M vertices
- 3D printing: 100k-1M vertices (manifold required)
- Sculpting preview: 100k-500k vertices
- Final detail sculpt: 1M-10M vertices

**Check Current Vertex Count:**
```python
import requests

code = """
import bpy

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        vertex_count = len(obj.data.vertices)
        face_count = len(obj.data.polygons)
        print(f'{obj.name}: {vertex_count:,} vertices, {face_count:,} faces')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **Memory-Efficient Sculpting**

**Step 1: Monitor Memory Usage**
```python
code = """
import bpy
import sys

# Calculate mesh memory usage
total_memory = 0
for mesh in bpy.data.meshes:
    # Approximate: vertices + faces + edges
    vertex_mem = len(mesh.vertices) * 12  # 3 floats per vertex
    face_mem = len(mesh.polygons) * 16    # Approx per face
    edge_mem = len(mesh.edges) * 8        # 2 ints per edge

    mesh_mem = (vertex_mem + face_mem + edge_mem) / (1024 * 1024)  # MB
    total_memory += mesh_mem

    if mesh_mem > 10:  # Only show meshes > 10MB
        print(f'{mesh.name}: {mesh_mem:.1f} MB')

print(f'Total mesh memory: {total_memory:.1f} MB')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Step 2: Reduce Memory Footprint**
```python
code = """
import bpy

# Remove unused mesh data
for mesh in bpy.data.meshes:
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# Remove unused materials
for mat in bpy.data.materials:
    if mat.users == 0:
        bpy.data.materials.remove(mat)

# Remove unused images
for img in bpy.data.images:
    if img.users == 0:
        bpy.data.images.remove(img)

print('Unused data removed')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **Viewport Performance Optimization**

**Reduce Viewport Display Complexity:**
```python
code = """
import bpy

# Set viewport display to optimal settings
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                # Reduce anti-aliasing
                space.shading.use_scene_lights = False
                space.shading.use_scene_world = False

                # Simplify shading
                space.shading.color_type = 'MATERIAL'

                # Disable overlays for performance
                space.overlay.show_wireframes = False
                space.overlay.show_floor = False
                space.overlay.show_axis_x = False
                space.overlay.show_axis_y = False

print('Viewport optimized for performance')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Dynamic Topology Strategies

### **Dyntopo vs Multires**

**When to Use Dyntopo:**
- Early concept sculpting
- Freedom to add detail anywhere
- Changing silhouette frequently
- Don't need to preserve base mesh

**When to Use Multires:**
- Preserving base topology for animation
- Need subdivision levels for export
- Working from established base mesh
- Need to bake detail to normal maps

### **Manual Dynamic Topology**

For programmatic control without relying on interactive mode toggling, implement manual dynamic subdivision:

```python
code = """
import bpy
import numpy as np

def subdivide_long_edges(obj, max_edge_length):
    '''Manually subdivide edges that exceed threshold'''
    mesh = obj.data
    edges_to_subdivide = []

    # Identify long edges
    for edge in mesh.edges:
        v1 = mesh.vertices[edge.vertices[0]].co
        v2 = mesh.vertices[edge.vertices[1]].co
        length = (v1 - v2).length

        if length > max_edge_length:
            edges_to_subdivide.append(edge.index)

    print(f'Long edges found: {len(edges_to_subdivide)}')
    print(f'Note: Actual subdivision must be done in Blender UI')
    print(f'Select edges and use Edge > Subdivide')

    return edges_to_subdivide

terrain = bpy.data.objects.get('Terrain')
long_edges = subdivide_long_edges(terrain, 2.0)
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **Constant Detail Resolution**

Maintain consistent polygon density across surface:

```python
code = """
import bpy

obj = bpy.data.objects.get('Sculpture')
mesh = obj.data

# Calculate average edge length
total_length = 0
for edge in mesh.edges:
    v1 = mesh.vertices[edge.vertices[0]].co
    v2 = mesh.vertices[edge.vertices[1]].co
    total_length += (v1 - v2).length

avg_edge_length = total_length / len(mesh.edges)

print(f'Average edge length: {avg_edge_length:.4f}')
print(f'Total edges: {len(mesh.edges):,}')
print(f'Mesh resolution: {"Low" if avg_edge_length > 1.0 else "Medium" if avg_edge_length > 0.1 else "High"}')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Remeshing Workflows

### **Voxel Remeshing**

**When to Use:**
- Merge multiple objects into single sculpt
- Fix topology issues
- Uniform polygon distribution
- Preparing for 3D printing

**Voxel Remesh Setup:**
```python
code = """
import bpy

obj = bpy.data.objects.get('Sculpture')

# Add voxel remesh modifier
remesh = obj.modifiers.new('VoxelRemesh', 'REMESH')
remesh.mode = 'VOXEL'
remesh.voxel_size = 0.05  # Smaller = higher resolution

# Voxel size guidelines:
# 0.5 = Very coarse (preview)
# 0.1 = Medium (mid-res sculpting)
# 0.05 = High (detail work)
# 0.01 = Very high (final detail)

print(f'Voxel remesh added - size: {remesh.voxel_size}')
print(f'Estimated vertices: {int(1 / remesh.voxel_size**3)}')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Calculate Optimal Voxel Size:**
```python
code = """
import bpy

obj = bpy.data.objects.get('Sculpture')

# Calculate object bounds
vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
min_x = min(v.x for v in vertices)
max_x = max(v.x for v in vertices)
min_y = min(v.y for v in vertices)
max_y = max(v.y for v in vertices)
min_z = min(v.z for v in vertices)
max_z = max(v.z for v in vertices)

# Dimensions
width = max_x - min_x
height = max_y - min_y
depth = max_z - min_z
max_dim = max(width, height, depth)

# Target vertex count
target_vertices = 500000  # 500k vertices

# Calculate voxel size
# Approximate: vertices ≈ (dimension / voxel_size)³
voxel_size = max_dim / (target_vertices ** (1/3))

print(f'Object dimensions: {width:.2f} x {height:.2f} x {depth:.2f}')
print(f'Recommended voxel size for {target_vertices:,} vertices: {voxel_size:.4f}')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **Quad Remeshing**

**For Animation-Friendly Topology:**
```python
code = """
import bpy

obj = bpy.data.objects.get('Sculpture')

# Add remesh modifier in BLOCKS mode (quad-based)
remesh = obj.modifiers.new('QuadRemesh', 'REMESH')
remesh.mode = 'BLOCKS'
remesh.octree_depth = 6  # Higher = more detail (range 1-12)

# Octree depth guidelines:
# 4 = Very coarse (1-5k vertices)
# 6 = Medium (20-50k vertices)
# 8 = High (100-500k vertices)
# 10 = Very high (1M+ vertices)

estimated_verts = 4 ** remesh.octree_depth
print(f'Quad remesh added - octree depth: {remesh.octree_depth}')
print(f'Estimated vertices: ~{estimated_verts:,}')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Export Workflows

### **Game Engine Export (FBX)**

**Optimize for Real-Time:**
```python
code = """
import bpy

sculpture = bpy.data.objects.get('Sculpture')

# Step 1: Create decimated version
decimated = sculpture.copy()
decimated.data = sculpture.data.copy()
decimated.name = f'{sculpture.name}_GameRes'
bpy.context.collection.objects.link(decimated)

# Step 2: Add decimate modifier
decimate = decimated.modifiers.new('Decimate', 'DECIMATE')
decimate.ratio = 0.1  # 10% of original vertices
decimate.use_collapse_triangulate = True

print(f'Game-res version created: {decimated.name}')
print(f'Original vertices: {len(sculpture.data.vertices):,}')
print(f'Target vertices: ~{int(len(sculpture.data.vertices) * decimate.ratio):,}')

# Step 3: Bake normal map from high-res to low-res
# (Must be done in Blender UI - requires baking)
print('Next: Bake normal map in Blender (Render Settings > Bake)')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **3D Printing Export (STL)**

**Ensure Manifold Geometry:**
```python
code = """
import bpy

obj = bpy.data.objects.get('Sculpture')
mesh = obj.data

# Check for non-manifold geometry
non_manifold_verts = []
non_manifold_edges = []

# Check vertex valence (each vertex should have even number of edges)
for v in mesh.vertices:
    edge_count = sum(1 for e in mesh.edges if v.index in e.vertices)
    if edge_count < 3:  # Boundary or loose vertex
        non_manifold_verts.append(v.index)

# Check edges (each edge should be used by exactly 2 faces)
for e in mesh.edges:
    face_count = sum(1 for f in mesh.polygons if
                     e.vertices[0] in f.vertices and e.vertices[1] in f.vertices)
    if face_count != 2:
        non_manifold_edges.append(e.index)

if non_manifold_verts or non_manifold_edges:
    print(f'⚠️ Non-manifold geometry detected:')
    print(f'  Vertices: {len(non_manifold_verts)}')
    print(f'  Edges: {len(non_manifold_edges)}')
    print(f'Fix in Blender: Mesh > Clean Up > Merge By Distance, then Fill Holes')
else:
    print(f'✅ Mesh is manifold - suitable for 3D printing')

# Check for loose geometry
loose_verts = [v.index for v in mesh.vertices if not any(v.index in e.vertices for e in mesh.edges)]
if loose_verts:
    print(f'⚠️ Loose vertices: {len(loose_verts)} (remove before export)')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

**Fix Common Issues:**
```python
code = """
import bpy

mesh = bpy.data.objects.get('Sculpture').data

# Remove doubles (merge close vertices)
threshold = 0.0001
verts_to_merge = []

for i, v1 in enumerate(mesh.vertices):
    for v2 in list(mesh.vertices)[i+1:]:
        dist = (v1.co - v2.co).length
        if dist < threshold:
            verts_to_merge.append((v1.index, v2.index))

if verts_to_merge:
    print(f'Vertices to merge: {len(verts_to_merge)}')
    print('Use Mesh > Clean Up > Merge By Distance in Blender')
else:
    print('No duplicate vertices found')

# Recalculate normals
# NOTE: bpy.ops.mesh.normals_make_consistent() requires edit-mode context
print('Recalculate normals in Blender: Edit Mode > Mesh > Normals > Recalculate Outside')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **Unreal Engine Export**

**Best Practices:**
```python
code = """
import bpy

sculpture = bpy.data.objects.get('Sculpture')

# 1. Scale to Unreal units (1 Blender unit = 100 Unreal units)
unreal_scale = 100
sculpture.scale = (unreal_scale, unreal_scale, unreal_scale)

# 2. Apply transforms
# NOTE: bpy.ops.object.transform_apply() requires the object to be selected and active
# Apply manually or do in Blender UI

# 3. Create LOD versions
def create_lod(source, level, ratio):
    lod = source.copy()
    lod.data = source.data.copy()
    lod.name = f'{source.name}_LOD{level}'
    bpy.context.collection.objects.link(lod)

    decimate = lod.modifiers.new('Decimate', 'DECIMATE')
    decimate.ratio = ratio

    return lod

# Create LOD chain
lod0 = sculpture  # Full detail
lod1 = create_lod(sculpture, 1, 0.5)   # 50%
lod2 = create_lod(sculpture, 2, 0.25)  # 25%
lod3 = create_lod(sculpture, 3, 0.1)   # 10%

print('Unreal LOD chain created:')
print(f'  LOD0: {len(lod0.data.vertices):,} vertices (full detail)')
print(f'  LOD1: ~{int(len(lod0.data.vertices) * 0.5):,} vertices')
print(f'  LOD2: ~{int(len(lod0.data.vertices) * 0.25):,} vertices')
print(f'  LOD3: ~{int(len(lod0.data.vertices) * 0.1):,} vertices')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Retopology for Animation

### **Manual Retopology Setup**

**Goal:** Create clean quad topology following edge flow

```python
code = """
import bpy

# Create shrinkwrap modifier for retopology reference
high_res = bpy.data.objects.get('Sculpture_HighRes')
low_res = bpy.data.objects.get('Sculpture_LowRes')

if high_res and low_res:
    # Add shrinkwrap to low-res mesh
    shrinkwrap = low_res.modifiers.new('Shrinkwrap', 'SHRINKWRAP')
    shrinkwrap.target = high_res
    shrinkwrap.wrap_method = 'PROJECT'
    shrinkwrap.use_negative_direction = True
    shrinkwrap.use_positive_direction = True

    print('Retopology setup complete')
    print('1. Model low-res topology in Blender (Edit Mode)')
    print('2. Shrinkwrap will project vertices onto high-res surface')
    print('3. Bake normal map from high-res to low-res when done')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

### **Topology Validation**

**Check for Good Topology:**
```python
code = """
import bpy

mesh = bpy.data.objects.get('Retopo').data

# Check for non-quads
quad_count = sum(1 for f in mesh.polygons if len(f.vertices) == 4)
tri_count = sum(1 for f in mesh.polygons if len(f.vertices) == 3)
ngon_count = sum(1 for f in mesh.polygons if len(f.vertices) > 4)

print('Topology Analysis:')
print(f'  Quads: {quad_count} ({quad_count/len(mesh.polygons)*100:.1f}%)')
print(f'  Tris: {tri_count} ({tri_count/len(mesh.polygons)*100:.1f}%)')
print(f'  N-gons: {ngon_count} ({ngon_count/len(mesh.polygons)*100:.1f}%)')

if quad_count / len(mesh.polygons) > 0.95:
    print('✅ Good quad topology for animation')
else:
    print('⚠️ Consider converting to quads for better deformation')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

## Batch Operations

### **Process Multiple Sculpts**

**Apply Same Operation to All Sculpts:**
```python
code = """
import bpy

# Define operation to apply
def optimize_sculpt(obj):
    '''Apply optimization to single object'''
    # Add remesh modifier
    if 'Remesh' not in [m.name for m in obj.modifiers]:
        remesh = obj.modifiers.new('Remesh', 'REMESH')
        remesh.mode = 'VOXEL'
        remesh.voxel_size = 0.05

    # Ensure smooth shading
    for poly in obj.data.polygons:
        poly.use_smooth = True

    return True

# Process all mesh objects
sculpts = [obj for obj in bpy.data.objects if obj.type == 'MESH' and 'Sculpt' in obj.name]

for sculpt in sculpts:
    optimize_sculpt(sculpt)
    print(f'Optimized: {sculpt.name}')

print(f'Processed {len(sculpts)} sculpts')
"""

# Run via the Blender MCP tool: execute_blender_code(code=code)
```

---

**Return to:** `.claude/skills/blender-sculpting/SKILL.md`
