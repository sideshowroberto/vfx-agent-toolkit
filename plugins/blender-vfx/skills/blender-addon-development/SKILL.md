---
name: blender-addon-development
description: Blender addon development — operator design, UI panels, bpy.props, poll() methods, and registration systems. Use when creating addons, building operators, designing UI panels, or when user mentions "addon," "operator," "UI panel," or "Blender Python."
allowed-tools: Read,Write
---

# Blender Addon Development Skill

**Version:** 2.1.0
**Last Updated:** 2026-06-10
**Dependencies:** Blender 5.1+, Python 3.11+

---

## Blender 5.1+ Notes

```python
# Modifier type (5.1+, also valid from 4.5+)
modifier = obj.modifiers.new("GeoNodes", type='NODES')  # Not 'GEOMETRY_NODES'

# Render engine (5.1+)
context.scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Not 'BLENDER_EEVEE'

# Version check pattern
if bpy.app.version >= (4, 5, 0):
    engine = 'BLENDER_EEVEE_NEXT'
```

---

## QUICK START

### Create Basic Addon with Panel

```python
bl_info = {
    "name": "My Addon",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > My Addon",
    "description": "Addon description",
    "category": "3D View"
}

import bpy

class MY_PT_Panel(bpy.types.Panel):
    """Main UI Panel"""
    bl_label = "My Addon"
    bl_idname = "MY_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'My Addon'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Hello World!")
        layout.operator("my.operator")

class MY_OT_Operator(bpy.types.Operator):
    """Main Operator"""
    bl_idname = "my.operator"
    bl_label = "Run Action"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        mesh = bpy.data.meshes.new("MyMesh")
        obj = bpy.data.objects.new("MyObject", mesh)
        context.collection.objects.link(obj)
        self.report({'INFO'}, "Action completed!")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MY_PT_Panel)
    bpy.utils.register_class(MY_OT_Operator)

def unregister():
    bpy.utils.unregister_class(MY_PT_Panel)
    bpy.utils.unregister_class(MY_OT_Operator)

if __name__ == "__main__":
    register()
```

**Install:** Edit > Preferences > Add-ons > Install (select the .py file), then enable it.
**Test:** Press `N` in 3D Viewport, look for the "My Addon" tab.

---

## STANDARD WORKFLOWS

### Workflow 1: Addon with PropertyGroup

```python
import bpy

class MyAddonProperties(bpy.types.PropertyGroup):
    count: bpy.props.IntProperty(
        name="Count",
        default=5,
        min=1,
        max=100,
        description="Number of objects to create"
    )
    size: bpy.props.FloatProperty(
        name="Size",
        default=1.0,
        min=0.1,
        description="Object size"
    )
    use_random: bpy.props.BoolProperty(
        name="Random Placement",
        default=True
    )

class MY_PT_Panel(bpy.types.Panel):
    bl_label = "My Addon"
    bl_idname = "MY_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'My Addon'

    def draw(self, context):
        layout = self.layout
        props = context.scene.my_addon

        layout.prop(props, "count")
        layout.prop(props, "size")
        layout.prop(props, "use_random")
        layout.operator("my.create_objects")

class MY_OT_CreateObjects(bpy.types.Operator):
    bl_idname = "my.create_objects"
    bl_label = "Create Objects"

    def execute(self, context):
        props = context.scene.my_addon
        import random

        for i in range(props.count):
            mesh = bpy.data.meshes.new(f"Mesh_{i}")
            obj = bpy.data.objects.new(f"Object_{i}", mesh)
            context.collection.objects.link(obj)

            if props.use_random:
                obj.location = (
                    random.uniform(-5, 5),
                    random.uniform(-5, 5),
                    0
                )
            obj.scale = (props.size,) * 3

        self.report({'INFO'}, f"Created {props.count} objects")
        return {'FINISHED'}

classes = (MyAddonProperties, MY_PT_Panel, MY_OT_CreateObjects)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.my_addon = bpy.props.PointerProperty(type=MyAddonProperties)

def unregister():
    del bpy.types.Scene.my_addon
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
```

---

### Workflow 2: Geometry Nodes Integration

**Use Case:** Addon-controlled procedural assets

```python
import bpy

def create_scatter_modifier(obj, collection=None):
    """Create geometry nodes scatter modifier on obj."""
    # NODES modifier (5.1+, also 4.5+)
    geo_mod = obj.modifiers.new("Scatter", type='NODES')

    node_tree = bpy.data.node_groups.new("ScatterNodes", 'GeometryNodeTree')
    geo_mod.node_group = node_tree

    input_node = node_tree.nodes.new('NodeGroupInput')
    output_node = node_tree.nodes.new('NodeGroupOutput')
    distribute = node_tree.nodes.new('GeometryNodeDistributePointsOnFaces')

    links = node_tree.links
    links.new(input_node.outputs[0], distribute.inputs['Mesh'])
    links.new(distribute.outputs['Points'], output_node.inputs[0])

    return geo_mod
```

---

### Workflow 3: Procedural Material from Addon

```python
import bpy

def create_procedural_material(name="Procedural"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    output = nodes.new('ShaderNodeOutputMaterial')
    noise = nodes.new('ShaderNodeTexNoise')
    color_ramp = nodes.new('ShaderNodeValToRGB')

    noise.inputs['Scale'].default_value = 10.0
    color_ramp.color_ramp.elements[0].color = (0.1, 0.2, 0.05, 1.0)

    links.new(noise.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat
```

### Workflow: Async cloud/API calls without freezing the UI

bpy is not thread-safe. The production pattern (from the `ai_tools` addon,
live-verified 2026-07):

```python
import queue, threading
import bpy

_QUEUE = queue.Queue()

def _worker(job):
    # HTTP/urllib/SDK calls only - NEVER touch bpy from this thread
    result_path = call_cloud_api(job)
    _QUEUE.put(("done", result_path))

def _drain():
    # runs on the main thread via bpy.app.timers - safe to touch bpy
    try:
        while True:
            kind, payload = _QUEUE.get_nowait()
            if kind == "done":
                bpy.data.images.load(payload)
    except queue.Empty:
        pass
    return 0.4  # keep polling; return None to stop

# In the operator: capture inputs synchronously (renders etc.), then:
threading.Thread(target=_worker, args=(job,), daemon=True).start()
bpy.app.timers.register(_drain, first_interval=0.4)
```

Full implementation: `Blender/ai_tools/ops.py` (status/progress/cancel/
multi-result variants). Related patterns proven there:

- **Drag-and-drop from Explorer** (4.1+): subclass `bpy.types.FileHandler`
  with `bl_import_operator` + `bl_file_extensions`; `poll_drop` gates by
  area type. See `AITOOLS_FH_drop` in `Blender/ai_tools/ops.py`.
- **Third-party deps without touching Blender's python**: pip-install with
  `--target` into a per-user dir (`%APPDATA%\<addon>\site-packages\pyXY`),
  `sys.path.insert` at import time. Survives Blender upgrades, no admin.
  See `Blender/ai_tools/deps_install.py`. Note: agent-shell pip runs get
  sandbox-virtualized - run installs from inside Blender.
- **Hot-reload discipline**: never `importlib.reload` individual submodules
  (poisons the class registry). Full cycle only: disable addon -> purge
  `sys.modules` entries -> enable. Details: compatibility DB change #15.

---

## TROUBLESHOOTING

### Issue 1: Module Registration Failures

**Symptoms:** Addon installs but doesn't appear in UI / `AttributeError: 'module' has no attribute 'register'`

```python
import bpy

# REQUIRED registration pattern
classes = (
    MY_PT_Panel,
    MY_OT_Operator,
    MyAddonProperties
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.my_addon = bpy.props.PointerProperty(type=MyAddonProperties)

def unregister():
    del bpy.types.Scene.my_addon
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
```

**Prevention:**
- Always include `register()` and `unregister()`
- Register in forward order, unregister in reversed order
- Unregister scene properties before unregistering the PropertyGroup class

---

### Issue 2: Blender 5.1 Compatibility

**Symptoms:** Addon works in 4.x but fails in 5.1

```python
import bpy

# Render engine (5.1+)
context.scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Not 'BLENDER_EEVEE'

# Modifier type (5.1+)
modifier = obj.modifiers.new("GeoNodes", type='NODES')  # Not 'GEOMETRY_NODES'
```

---

### Issue 3: poll() Best Practices

```python
import bpy

class MY_OT_Operator(bpy.types.Operator):
    bl_idname = "my.operator"
    bl_label = "My Operator"

    @classmethod
    def poll(cls, context):
        # Operator only active when a mesh is selected
        return (
            context.active_object is not None
            and context.active_object.type == 'MESH'
        )

    def execute(self, context):
        obj = context.active_object
        # Direct data API — no operators needed
        for poly in obj.data.polygons:
            poly.use_smooth = True
        obj.data.update()
        return {'FINISHED'}
```

---

## VALIDATION CHECKLIST

- [ ] `bl_info` metadata complete
- [ ] Registration functions include `register()` and `unregister()`
- [ ] `classes` tuple registers in forward order, unregisters in reverse
- [ ] Scene properties unregistered before their PropertyGroup class
- [ ] `poll()` method added to operators where context requirements exist
- [ ] Blender 5.1+ compatibility (NODES, BLENDER_EEVEE_NEXT)
- [ ] Panel appears in expected location (press `N` in 3D View)

---

## VERSION HISTORY

**v2.1.0** (2026-07-10) - Cloud-API addon patterns
- Added: async worker/queue/bpy.app.timers pattern for cloud API calls
- Added: FileHandler drag-and-drop, per-user pip-target dependency install
- Added: hot-reload discipline (full disable/purge/enable cycle)
- Source: ai_tools addon development (see blender-ai-tools skill)

**v2.0.0** (2026-06-10) - MCP migration
- Removed HTTP Bridge as addon content (retired)
- Removed HTTP Bridge integration from description and workflows
- Removed curl health-check steps and `import requests` wrappers
- Updated target: Blender 5.1+
- Kept: operator design, UI panels, bpy.props, poll() methods, registration

**v1.0.0** (2025-10-24) - Initial release

---

**Status:** Production Ready
**Maintainer:** VFX Pipeline Team
**Dependencies:** Blender 5.1+, Python 3.11+
