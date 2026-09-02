---
name: blender-api-compatibility
description: Blender API compatibility across versions (4.2 -> 5.1+), breaking changes detection, and migration strategies. Use for API errors, version migration, breaking changes, or when user mentions "compatibility," "breaking change," "migration," "API error," or "doesn't work in newer Blender."
allowed-tools: Read,Write
---

# Blender API Compatibility Skill

**Version:** 3.1.0
**Last Updated:** 2026-09-02
**Dependencies:** Blender 5.1+

---

## Breaking Changes (4.2 -> 5.1)

All changes below are tested and confirmed. The Blender MCP has full context, so **`bpy.ops` works normally** - the old HTTP Bridge limitation of 80% operator failure no longer applies.

---

## QUICK START

### API Error Diagnosis

**Step 1: Identify the error pattern**
```python
# Common error signatures:
# AttributeError involving 'BLENDER_EEVEE'  -> Render engine renamed
# KeyError: 'GEOMETRY_NODES'                -> Modifier type renamed
# KeyError/AttributeError on BSDF inputs    -> Input names changed
# RuntimeError: "Cannot find node type"     -> Node type removed/renamed
# TypeError: enum "FFMPEG" not found        -> Set media_type = 'VIDEO' first (5.0+)
# AttributeError on 'sequences'             -> VSE renamed to strips/strips_all (5.0+)
```

**Step 2: Apply the correct migration pattern** (see workflows below)

**Step 3: Verify in Blender**
```python
import bpy

# Quick test: check current render engine
print(bpy.context.scene.render.engine)  # Should print BLENDER_EEVEE_NEXT or CYCLES
```

---

## STANDARD WORKFLOWS

### Workflow 1: EEVEE -> EEVEE_NEXT Migration

**Use When:** Code references BLENDER_EEVEE or old EEVEE properties

```python
import bpy

# [FAIL] REMOVED in 4.5.0+
# bpy.context.scene.render.engine = 'BLENDER_EEVEE'
# scene.eevee.use_bloom = True
# scene.eevee.use_ssr = True
# scene.eevee.use_motion_blur = True

# [OK] Render engine
bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'

# [OK] Bloom -> Compositor Glare node
scene = bpy.context.scene
scene.use_nodes = True
nodes = scene.node_tree.nodes
links = scene.node_tree.links
glare = nodes.new(type='CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'   # closest to old EEVEE bloom
glare.threshold = 0.8

# [OK] Motion blur -> render settings
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.5

# [OK] Screen space reflections -> ray tracing
scene.eevee.use_raytracing = True
```

---

### Workflow 2: GEOMETRY_NODES -> NODES Modifier

**Use When:** Creating geometry nodes modifiers

```python
import bpy

# [FAIL] BROKEN in 4.5.0+ (KeyError)
# modifier = obj.modifiers.new(name="GeoNodes", type='GEOMETRY_NODES')

# [OK] WORKING in 4.5.0+
modifier = obj.modifiers.new(name="GeoNodes", type='NODES')
modifier.node_group = node_tree   # Same property, still works

# Version-safe helper (for code that needs to run on older Blender too)
def add_geometry_nodes_safe(obj, name="GeoNodes"):
    try:
        return obj.modifiers.new(name=name, type='NODES')           # 4.5+
    except KeyError:
        return obj.modifiers.new(name=name, type='GEOMETRY_NODES')  # <4.5
```

---

### Workflow 3: CompositorNodeColorRamp Removed

**Use When:** Creating color ramp nodes in compositor

```python
import bpy

# [FAIL] BROKEN in 4.5.0+ (RuntimeError: Cannot find node type)
# color_ramp = compositor.nodes.new('CompositorNodeColorRamp')

# [OK] WORKING - identical API
color_ramp = compositor.nodes.new('ShaderNodeValToRGB')
color_ramp.color_ramp.elements.new(0.5)
color_ramp.color_ramp.elements[0].color = (1.0, 0.0, 0.0, 1.0)
```

---

### Workflow 4: Principled BSDF Input Name Changes (4.5+)

```python
import bpy

# [FAIL] OLD (Blender 4.2-4.4)
# bsdf.inputs["Transmission"].default_value = 1.0
# bsdf.inputs["Subsurface"].default_value = 0.2
# bsdf.inputs["Emission"].default_value = (1,1,1,1)

# [OK] NEW (4.5.0+)
bsdf.inputs["Transmission Weight"].default_value = 1.0
bsdf.inputs["Subsurface Weight"].default_value = 0.2
bsdf.inputs["Emission Color"].default_value = (1, 1, 1, 1)

# Always use input names, not indices:
bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.1, 1.0)  # Safe
# bsdf.inputs[0].default_value = ...  # Fragile - index order can change
```

---

### Workflow 5: Viewport Shading Type

```python
import bpy

# [FAIL] BROKEN in 4.5.0+
# space.shading.type = 'MATERIAL_PREVIEW'

# [OK] WORKING (4.5.0+)
space.shading.type = 'MATERIAL'

# Valid shading modes in 5.1+:
# 'WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED'
```

---

### Workflow 6: Render Output media_type Gates file_format (5.0+)

**Use When:** Setting `file_format` fails with `enum "..." not found` (e.g. FFMPEG for video output)

Blender 5.0 added `image_settings.media_type` (`IMAGE` / `MULTI_LAYER_IMAGE` / `VIDEO`). The `file_format` enum is **filtered by the active media_type** - video formats are only valid in VIDEO mode, image formats only in IMAGE mode.

```python
import bpy

scene = bpy.context.scene

# [X] BROKEN in 5.x - scene in default IMAGE mode
# scene.render.image_settings.file_format = 'FFMPEG'
# TypeError: enum "FFMPEG" not found in ('BMP', 'IRIS', 'PNG', ...)

# [OK] WORKING - set media_type FIRST (portable 4.x/5.x pattern)
if hasattr(scene.render.image_settings, "media_type"):  # 5.0+
    scene.render.image_settings.media_type = 'VIDEO'
scene.render.image_settings.file_format = 'FFMPEG'

# Same in reverse - scene configured for video, switching to stills:
if hasattr(scene.render.image_settings, "media_type"):
    scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
```

**Save/restore gotcha:** code that snapshots and restores `image_settings` must restore `media_type` BEFORE `file_format`, or the restore itself throws - keep the property keys in an ordered sequence with `media_type` first.

---

### Workflow 7: VSE sequences -> strips Rename (5.0+)

**Use When:** VSE code raises AttributeError on `sequences` / `sequences_all`

```python
import bpy

se = bpy.context.scene.sequence_editor

# [X] BROKEN in 5.x - old names removed
# for strip in se.sequences: ...
# all_strips = se.sequences_all

# [OK] WORKING - portable via hasattr
strips = se.strips if hasattr(se, "strips") else se.sequences
all_strips = se.strips_all if hasattr(se, "strips_all") else se.sequences_all
```

**CRITICAL - never use `or` fallbacks here:**

```python
# [X] SUBTLE BUG - an EMPTY strips collection is falsy, so this falls
# through to the missing 'sequences' attribute and returns None on a
# valid (but empty) 5.x sequence editor. Survives testing on non-empty
# scenes and only fails on empty ones.
strips = getattr(se, "strips", None) or getattr(se, "sequences", None)
```

Branch on attribute **existence** (`hasattr`), never on truthiness.

---

## ADVANCED TECHNIQUES

### Capability Detection (Preferred over Version Checking)

```python
import bpy

def detect_blender_capabilities():
    """Detect API capabilities rather than version numbers."""
    caps = {
        'blender_version': bpy.app.version,
        'has_eevee_next': False,
        'geometry_nodes_type': None
    }

    # Test EEVEE_NEXT
    try:
        current = bpy.context.scene.render.engine
        bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
        caps['has_eevee_next'] = True
        bpy.context.scene.render.engine = current
    except Exception:
        pass

    # Test geometry nodes modifier type
    test_mesh = bpy.data.meshes.new("_cap_test")
    test_obj = bpy.data.objects.new("_cap_test", test_mesh)
    try:
        mod = test_obj.modifiers.new("test", type='NODES')
        caps['geometry_nodes_type'] = 'NODES'
        test_obj.modifiers.remove(mod)
    except Exception:
        try:
            mod = test_obj.modifiers.new("test", type='GEOMETRY_NODES')
            caps['geometry_nodes_type'] = 'GEOMETRY_NODES'
        except Exception:
            pass
    finally:
        bpy.data.objects.remove(test_obj, do_unlink=True)
        bpy.data.meshes.remove(test_mesh)

    return caps
```

### Migration Wrapper

```python
import bpy

def set_render_engine_safe(preference):
    engine_map = {
        'EEVEE': 'BLENDER_EEVEE_NEXT',
        'BLENDER_EEVEE': 'BLENDER_EEVEE_NEXT',
        'CYCLES': 'CYCLES',
        'WORKBENCH': 'BLENDER_WORKBENCH',
    }
    target = engine_map.get(preference, preference)
    try:
        bpy.context.scene.render.engine = target
        return True
    except TypeError:
        return False
```

---

## TROUBLESHOOTING

### "BLENDER_EEVEE" ValueError

**Cause:** BLENDER_EEVEE completely removed in 4.5.0
**Fix:** `bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'`

---

### KeyError: 'GEOMETRY_NODES'

**Cause:** Modifier type renamed in 4.5.0
**Fix:** `obj.modifiers.new(name="GeoNodes", type='NODES')`

---

### KeyError on BSDF Input Names

**Cause:** Input names changed in 4.5.0
**Fix:** Use new names - `"Transmission Weight"`, `"Subsurface Weight"`, `"Emission Color"`

---

### TypeError: enum "FFMPEG" not found (file_format)

**Cause:** Blender 5.0+ filters the `file_format` enum by `media_type`; the scene is in IMAGE mode
**Fix:** `scene.render.image_settings.media_type = 'VIDEO'` before setting `file_format = 'FFMPEG'` (and `'IMAGE'` before PNG/JPEG etc. if the scene was set up for video)

---

### AttributeError: 'SequenceEditor' object has no attribute 'sequences'

**Cause:** VSE `sequences`/`sequences_all` renamed to `strips`/`strips_all` in 5.0
**Fix:** `se.strips if hasattr(se, "strips") else se.sequences` - never `getattr(...) or getattr(...)` (empty collections are falsy)

---

## COMPLETE BREAKING CHANGES REFERENCE (4.2 -> 5.1)

### Render Engine
1. `BLENDER_EEVEE` -> `BLENDER_EEVEE_NEXT` (complete removal in 4.5.0)
2. `scene.eevee.use_bloom` -> Compositor Glare node (`FOG_GLOW`)
3. `scene.eevee.use_ssr` -> `scene.eevee.use_raytracing`
4. `scene.eevee.use_motion_blur` -> `scene.render.use_motion_blur`
5. `scene.eevee.use_volumetric_lights` -> Removed

### Modifiers
6. `GEOMETRY_NODES` modifier type -> `NODES`

### Node Types (Compositor)
7. `CompositorNodeColorRamp` -> `ShaderNodeValToRGB`
8. `CompositorNodeComposite` -> Removed (no replacement - main output via `scene.render.filepath`)
9. `CompositorNodeMapRange` -> Removed (use `ShaderNodeMath` with MINIMUM/MAXIMUM/etc.)
10. `ShaderNodeMath` works in compositor context (shared node type)

### Compositor Architecture (5.1+)
11. `scene.node_tree` -> `scene.compositing_node_group` (must create `CompositorNodeTree` if None)
12. `OPEN_EXR_MULTILAYER` removed from main render format enum - only via File Output node
13. File Output node: `base_path` -> `directory`, `file_slots` -> `file_output_items`
14. File Output `file_name` appends scene frame number - add trailing `.` to prevent (e.g., `"out_0001."`)
15. File Output `file_output_items.new(socket_type, name)` - required for node to produce output

### Principled BSDF Inputs
16. `"Transmission"` -> `"Transmission Weight"`
17. `"Subsurface"` -> `"Subsurface Weight"`
18. `"Emission"` -> `"Emission Color"`
19. Use input names, not indices (indices can change between versions)

### Lighting
20. `light.use_contact_shadow` -> Removed

### Viewport Shading
21. `space.shading.type = 'MATERIAL_PREVIEW'` -> `'MATERIAL'`

### Cycles
22. `from bpy_types import CyclesRenderSettings` -> Use `bpy.context.scene.cycles` directly

### Render Output (5.0+)
23. New `image_settings.media_type` (`IMAGE` / `MULTI_LAYER_IMAGE` / `VIDEO`) - `file_format` enum is filtered by it; set `media_type` BEFORE `file_format` (both directions), guard with `hasattr` for 4.x

### Video Sequence Editor (5.0+)
24. `sequence_editor.sequences` / `sequences_all` -> `strips` / `strips_all` - portable fallback must use `hasattr`, never `or` (empty collections are falsy)

---

## VALIDATION CHECKLIST

- [ ] No `BLENDER_EEVEE` references (use `BLENDER_EEVEE_NEXT`)
- [ ] No `GEOMETRY_NODES` modifier type (use `NODES`)
- [ ] No `CompositorNodeColorRamp` (use `ShaderNodeValToRGB`)
- [ ] No `CompositorNodeComposite` (removed in 5.1)
- [ ] No `CompositorNodeMapRange` (use `ShaderNodeMath`)
- [ ] No `scene.node_tree` (use `scene.compositing_node_group`)
- [ ] BSDF inputs use 4.5+ naming convention
- [ ] EEVEE post-processing moved to compositor nodes
- [ ] File Output uses `directory`/`file_name` with trailing `.` for custom numbering
- [ ] `scene.cycles` used directly (not imported from bpy_types)
- [ ] Viewport shading uses `'MATERIAL'` not `'MATERIAL_PREVIEW'`
- [ ] `media_type` set before `file_format` when changing render output format (5.0+)
- [ ] VSE code uses `strips`/`strips_all` with `hasattr` fallback (no `or`-chain fallbacks)

---

## VERSION HISTORY

**v3.1.0** (2026-09-02) - Blender 5.x render output + VSE gotchas (ported from a stranded July worktree edit)
- Added Workflow 6: `image_settings.media_type` gates the `file_format` enum (5.0+) - set media_type before file_format, hasattr-guarded portable pattern
- Added Workflow 7: VSE `sequences`/`sequences_all` -> `strips`/`strips_all` rename, with the falsy-fallback hazard (`or`-chains break on empty collections)
- Both discovered live in Blender 5.1.2 during ai_tools addon development (2026-07-09); database entries #12/#13 in blender-ai-compatibility

**v2.0.0** (2026-06-10) - MCP migration
- Removed HTTP Bridge limitation section (bpy.ops works normally via MCP)
- Removed absolute path grep commands
- Removed curl verification steps
- Added Principled BSDF and viewport shading as separate workflows
- Updated target: Blender 5.1+

**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+
