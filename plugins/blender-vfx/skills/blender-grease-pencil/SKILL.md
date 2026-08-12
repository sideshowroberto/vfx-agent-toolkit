---
name: blender-grease-pencil
description: 2D animation and Grease Pencil workflows in Blender. Use for 2D animation, hand-drawn animation, mixed media, stroke creation, layer management, or when user mentions "2D," "grease pencil," "hand drawn," "traditional animation," "NPR rendering," or "stylized animation."
allowed-tools: Read,Write
---

# Blender Grease Pencil Skill

**Version:** 2.0.0
**Last Updated:** 2026-06-10
**Dependencies:** Blender 5.1+

---

## API Stability (5.1+)

Core Grease Pencil API is stable across 4.x -> 5.1:
- `bpy.data.grease_pencils` - data creation
- `gpencil.layers` - layer management
- `layer.frames` - frame management
- `frame.strokes` - stroke data
- Material slots and properties

---

## QUICK START

### Create Basic 2D Animation

```python
import bpy

# Create new Grease Pencil data
gpencil = bpy.data.grease_pencils.new("Animation_GP")

# Create object and link to scene
obj = bpy.data.objects.new("Animation_Object", gpencil)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj

# Add drawing layer
layer = gpencil.layers.new("DrawingLayer")

# Create frame at frame 1
frame = layer.frames.new(1)

# Create stroke
stroke = frame.strokes.new()
stroke.points.add(count=3)

# Set point coordinates
stroke.points[0].co = (0, 0, 0)
stroke.points[1].co = (1, 1, 0)
stroke.points[2].co = (2, 0, 0)

stroke.line_width = 10

print(f"Created GP object with {len(frame.strokes)} stroke(s)")
```

---

## STANDARD WORKFLOWS

### Workflow 1: Frame-by-Frame Animation

```python
import bpy

gpencil = bpy.data.grease_pencils.new("Anim_GP")
obj = bpy.data.objects.new("Anim_Object", gpencil)
bpy.context.scene.collection.objects.link(obj)

layer = gpencil.layers.new("DrawingLayer")
layer.use_onion_skinning = True  # Enable onion skinning

# Frame 1 - starting position
f1 = layer.frames.new(1)
s1 = f1.strokes.new()
s1.points.add(count=2)
s1.points[0].co = (0, 0, 0)
s1.points[1].co = (1, 0, 0)
s1.line_width = 10

# Frame 12 - midpoint
f12 = layer.frames.new(12)
s12 = f12.strokes.new()
s12.points.add(count=2)
s12.points[0].co = (0, 0.5, 0)
s12.points[1].co = (1, 0.5, 0)
s12.line_width = 10

# Frame 24 - end position
f24 = layer.frames.new(24)
s24 = f24.strokes.new()
s24.points.add(count=2)
s24.points[0].co = (0, 1, 0)
s24.points[1].co = (1, 1, 0)
s24.line_width = 10

# Set scene frame range
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 24

print(f"Frame-by-frame animation: {len(layer.frames)} frames created")
```

---

### Workflow 2: Layer Management

```python
import bpy

gpencil = bpy.data.grease_pencils.new("LayeredAnim")
obj = bpy.data.objects.new("LayeredAnim", gpencil)
bpy.context.scene.collection.objects.link(obj)

# Background layer (drawn first, at bottom of stack)
bg_layer = gpencil.layers.new("Background")
bg_layer.blend_mode = 'REGULAR'

# Character layer
char_layer = gpencil.layers.new("Character")
char_layer.blend_mode = 'REGULAR'

# Effects layer (drawn on top)
fx_layer = gpencil.layers.new("Effects")
fx_layer.blend_mode = 'ADD'
fx_layer.opacity = 0.7

# Add material for each layer
mat = bpy.data.materials.new("GP_Line")
bpy.data.materials.create_gpencil_data(mat)
mat.grease_pencil.color = (0.1, 0.1, 0.1, 1.0)
gpencil.materials.append(mat)

# Add stroke to character layer frame 1
frame = char_layer.frames.new(1)
stroke = frame.strokes.new()
stroke.points.add(count=3)
stroke.points[0].co = (0, 0, 0)
stroke.points[1].co = (0.5, 1, 0)
stroke.points[2].co = (1, 0, 0)
stroke.material_index = 0

print(f"Layers: {[l.name for l in gpencil.layers]}")
```

---

### Workflow 3: Mixed Media (2D + 3D)

```python
import bpy

# Create 3D background object
bg_mesh = bpy.data.meshes.new("Background")
bg_verts = [(-5,-5,0), (5,-5,0), (5,5,0), (-5,5,0)]
bg_mesh.from_pydata(bg_verts, [], [[0,1,2,3]])
bg_mesh.update()
bg_obj = bpy.data.objects.new("Background", bg_mesh)
bpy.context.scene.collection.objects.link(bg_obj)

# Create Grease Pencil overlay
gpencil = bpy.data.grease_pencils.new("Overlay_GP")
gp_obj = bpy.data.objects.new("Overlay", gpencil)
bpy.context.scene.collection.objects.link(gp_obj)

# Place GP object slightly in front of background
gp_obj.location.z = 0.01

layer = gpencil.layers.new("Lines")
frame = layer.frames.new(1)

# Draw an arch across the background
stroke = frame.strokes.new()
stroke.points.add(count=5)
import math
for i, t in enumerate([0, 0.25, 0.5, 0.75, 1.0]):
    x = -4 + t * 8
    y = math.sin(t * math.pi) * 2
    stroke.points[i].co = (x, 0, y)
stroke.line_width = 20

# Set up camera for render
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (0, -10, 2)
cam_obj.rotation_euler = (1.1, 0, 0)
bpy.context.scene.camera = cam_obj

# Render settings for NPR/stylized output
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
bpy.context.scene.render.film_transparent = True

print("Mixed media scene configured")
```

---

## TROUBLESHOOTING

### Strokes Not Visible

```python
import bpy

# Verify stroke has points with valid coordinates
obj = bpy.data.objects.get('Animation_Object')
if obj and obj.data.layers:
    layer = obj.data.layers[0]
    if layer.frames:
        frame = layer.frames[0]
        for i, stroke in enumerate(frame.strokes):
            print(f"Stroke {i}: {len(stroke.points)} points")
            for j, pt in enumerate(stroke.points):
                print(f"  Point {j}: {pt.co}")
```

### Layer Not Animating

```python
import bpy

obj = bpy.data.objects.get('Animation_Object')
if obj:
    for layer in obj.data.layers:
        print(f"Layer '{layer.name}': locked={layer.lock}, "
              f"frames={[f.frame_number for f in layer.frames]}")
        if layer.lock:
            layer.lock = False
            print(f"  -> Unlocked")
```

### Materials Not Rendering

```python
import bpy

obj = bpy.data.objects.get('Animation_Object')
gpencil = obj.data

if len(gpencil.materials) == 0:
    mat = bpy.data.materials.new("GP_Default")
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color = (0.0, 0.0, 0.0, 1.0)
    gpencil.materials.append(mat)

# Assign material to strokes
for layer in gpencil.layers:
    for frame in layer.frames:
        for stroke in frame.strokes:
            stroke.material_index = 0
```

---

## VALIDATION CHECKLIST

- [ ] GP object linked to scene collection
- [ ] Layers created with distinct names
- [ ] Strokes have valid point coordinates (non-zero)
- [ ] Frame numbers span the timeline range
- [ ] Materials assigned to strokes if rendering
- [ ] `scene.frame_start` / `frame_end` match animation range

---

## VERSION HISTORY

**v2.0.0** (2026-06-10) - MCP migration
- Removed HTTP Bridge section and curl health-check steps
- Removed bridge endpoint curl commands
- Added `import bpy` to all code blocks
- Updated target: Blender 5.1+
- Removed absolute paths to blender-ai-compatibility
- Expanded workflow code examples

**v1.1.0** (2025-12-03) - Article III compliance
**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+
