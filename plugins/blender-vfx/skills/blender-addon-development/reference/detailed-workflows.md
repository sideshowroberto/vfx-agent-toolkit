# Blender Addon Development: Detailed Workflows

## Workflow 1: HTTP Bridge-Compatible Operator

**Use When:** Creating operators that work via HTTP Bridge

**Steps:**
1. **Avoid `bpy.ops` - Use Direct API**
   ```python
   class MY_OT_CreateMesh(bpy.types.Operator):
       bl_idname = "my.create_mesh"
       bl_label = "Create Mesh"

       def execute(self, context):
           # ❌ FAILS: bpy.ops.mesh.primitive_cube_add()

           # ✅ WORKS: Direct mesh creation
           vertices = [(0,0,0), (1,0,0), (1,1,0), (0,1,0)]
           faces = [[0,1,2,3]]

           mesh = bpy.data.meshes.new("MyMesh")
           mesh.from_pydata(vertices, [], faces)
           mesh.update()

           obj = bpy.data.objects.new("MyObject", mesh)
           context.collection.objects.link(obj)

           return {'FINISHED'}
   ```
   **Why:** HTTP Bridge lacks operator context; direct API always works

2. **Use `poll()` for Validation**
   ```python
   @classmethod
   def poll(cls, context):
       # Validate context before execution
       return context.mode == 'OBJECT'
   ```
   **Why:** Prevents execution in invalid contexts

3. **Proper Error Handling**
   ```python
   def execute(self, context):
       try:
           # Your code here
           return {'FINISHED'}
       except Exception as e:
           self.report({'ERROR'}, f"Operation failed: {str(e)}")
           return {'CANCELLED'}
   ```

**Success Criteria:**
- [ ] No `bpy.ops` calls in operator
- [ ] Direct API used for all operations
- [ ] Error handling in place
- [ ] Works via HTTP Bridge

---

## Workflow 2: UI Panel with Properties

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

---

## Workflow 3: HTTP Bridge Integration

**Use When:** Creating addons that communicate with external tools

**Pattern:**
1. **HTTP Server in Addon**
   ```python
   import http.server
   import threading

   class MyHTTPHandler(http.server.BaseHTTPRequestHandler):
       def do_POST(self):
           # Execute in main thread
           result_container = ResultContainer()

           def execute_wrapper():
               result_container.result = self._execute_code()
               result_container.ready = True
               return None

           bpy.app.timers.register(execute_wrapper, first_interval=0.0)

           # Wait for result
           while not result_container.ready:
               time.sleep(0.01)

           self.send_response(200)
           self.end_headers()

   def start_server():
       server = http.server.HTTPServer(('localhost', 8089), MyHTTPHandler)
       thread = threading.Thread(target=server.serve_forever)
       thread.daemon = True
       thread.start()
   ```

2. **Main Thread Safety Pattern**
   ```python
   class ResultContainer:
       def __init__(self):
           self.result = None
           self.ready = False
   ```

3. **Operator Integration**
   ```python
   class MY_OT_StartServer(bpy.types.Operator):
       bl_idname = "my.start_server"
       bl_label = "Start HTTP Server"

       def execute(self, context):
           start_server()
           self.report({'INFO'}, "Server started on port 8089")
           return {'FINISHED'}
   ```

**Success Criteria:**
- [ ] Main thread execution pattern
- [ ] Thread-safe result handling
- [ ] Proper error propagation
- [ ] Clean shutdown handling
