# Blender Addon Development: Detailed Workflows

## Workflow 1: UI Panel with Properties

**Use When:** Creating addon settings and user input

**Steps:**
1. **Define Properties**
   ```python
   class MyAddonProperties(bpy.types.PropertyGroup):
       my_float: bpy.props.FloatProperty(
           name="Size",
           description="Object size",
           default=1.0,
           min=0.1,
           max=10.0
       )
       my_enum: bpy.props.EnumProperty(
           name="Type",
           items=[
               ('CUBE', "Cube", "Create cube"),
               ('SPHERE', "Sphere", "Create sphere")
           ]
       )
   ```

2. **Register Properties**
   ```python
   def register():
       bpy.utils.register_class(MyAddonProperties)
       bpy.types.Scene.my_addon = bpy.props.PointerProperty(
           type=MyAddonProperties
       )

   def unregister():
       del bpy.types.Scene.my_addon
       bpy.utils.unregister_class(MyAddonProperties)
   ```

3. **Display in Panel**
   ```python
   def draw(self, context):
       layout = self.layout
       props = context.scene.my_addon

       layout.prop(props, "my_float")
       layout.prop(props, "my_enum")
       layout.operator("my.create_object")
   ```

4. **Use in Operator**
   ```python
   def execute(self, context):
       props = context.scene.my_addon
       size = props.my_float
       obj_type = props.my_enum
       # Use properties...
   ```
