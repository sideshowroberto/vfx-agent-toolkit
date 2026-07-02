# Blender Grease Pencil: Detailed Workflows

## 🔧 STANDARD WORKFLOWS

### **Workflow 1: Frame-by-Frame Animation**

**Use When:** Creating traditional hand-drawn animation

**Steps:**

1. **Create Animation Setup**
   ```python
   import bpy

   gpencil = bpy.data.grease_pencils.new("Animation")
   obj = bpy.data.objects.new("Animation_Obj", gpencil)
   bpy.context.scene.collection.objects.link(obj)

   layer = gpencil.layers.new("MainLayer")

   # Enable onion skinning
   layer.use_onion_skinning = True
   layer.onion_before_range = 2  # Show 2 frames before
   layer.onion_after_range = 2   # Show 2 frames after
   ```
   **Why:** Onion skinning shows previous/next frames for reference

2. **Create Keyframes**
   ```python
   # Frame 1
   frame1 = layer.frames.new(1)
   stroke1 = frame1.strokes.new()
   stroke1.points.add(count=2)
   stroke1.points[0].co = (0, 0, 0)
   stroke1.points[1].co = (1, 0, 0)

   # Frame 12 (pose at 0.5 seconds at 24fps)
   frame12 = layer.frames.new(12)
   stroke12 = frame12.strokes.new()
   stroke12.points.add(count=2)
   stroke12.points[0].co = (0, 1, 0)
   stroke12.points[1].co = (1, 1, 0)

   # Frame 24
   frame24 = layer.frames.new(24)
   stroke24 = frame24.strokes.new()
   stroke24.points.add(count=2)
   stroke24.points[0].co = (0, 0, 0)
   stroke24.points[1].co = (1, 0, 0)
   ```
   **Why:** Keyframe-based animation following traditional 12 principles

3. **Preview Animation**
   ```bash
   # Render playblast for review
   # Render a preview via the Blender MCP render tools
     -H "Content-Type: application/json" \
     -d '{"start_frame": 1, "end_frame": 24, "output": "/tmp/anim_preview.mp4"}'
   ```
   **Why:** Verify timing and motion before final render

**Success Criteria:**
- [ ] Onion skinning shows previous/next frames
- [ ] Keyframes created at proper intervals
- [ ] Animation playback smooth in viewport
- [ ] Playblast captures intended motion

---

### **Workflow 2: Layer Management for Complex Scenes**

**Use When:** Managing multiple drawing elements (characters, backgrounds, effects)

**Steps:**

1. **Create Layer Structure**
   ```python
   import bpy

   gpencil = bpy.data.grease_pencils.new("Composition")
   obj = bpy.data.objects.new("Comp_Obj", gpencil)
   bpy.context.scene.collection.objects.link(obj)

   # Background layer
   bg_layer = gpencil.layers.new("Background")
   bg_layer.opacity = 0.8

   # Character layer
   char_layer = gpencil.layers.new("Character")

   # Effects layer
   fx_layer = gpencil.layers.new("Effects")
   fx_layer.blend_mode = 'ADD'  # Additive blending for glow effects
   ```
   **Why:** Separate layers allow independent animation and editing

2. **Set Layer Ordering and Properties**
   ```python
   # Layer order (top to bottom in UI)
   # Effects (front)
   # Character (middle)
   # Background (back)

   # Lock background layer to prevent accidental edits
   bg_layer.lock = True

   # Set character layer as active
   gpencil.layers.active = char_layer
   ```
   **Why:** Proper layer organization prevents editing mistakes

3. **Apply Layer-Specific Materials**
   ```python
   # Create materials for different layers
   mat_bg = bpy.data.materials.new("Mat_BG")
   mat_bg.grease_pencil.color = (0.5, 0.5, 0.5, 1.0)  # Gray

   mat_char = bpy.data.materials.new("Mat_Char")
   mat_char.grease_pencil.color = (1.0, 0.0, 0.0, 1.0)  # Red

   mat_fx = bpy.data.materials.new("Mat_FX")
   mat_fx.grease_pencil.color = (1.0, 1.0, 0.0, 1.0)  # Yellow
   mat_fx.grease_pencil.show_fill = False  # Line only

   # Assign to object
   obj.data.materials.append(mat_bg)
   obj.data.materials.append(mat_char)
   obj.data.materials.append(mat_fx)
   ```
   **Why:** Material assignment controls visual appearance per layer

**Success Criteria:**
- [ ] Layers ordered correctly (background to foreground)
- [ ] Layer properties set appropriately
- [ ] Materials assigned and visible
- [ ] Locked layers prevent accidental edits

---

### **Workflow 3: Mixed Media (2D + 3D Integration)**

**Use When:** Combining 2D animation with 3D scenes

**Steps:**

1. **Setup 3D Environment**
   ```python
   import bpy

   # Add 3D reference mesh (e.g., building for character to walk past)
   bpy.ops.mesh.primitive_cube_add(location=(5, 0, 0), scale=(1, 1, 3))
   building = bpy.context.active_object
   building.name = "Building_3D"
   ```

2. **Create 2D Character with Proper Depth**
   ```python
   # Create Grease Pencil character
   gpencil = bpy.data.grease_pencils.new("Character2D")
   obj = bpy.data.objects.new("Character2D_Obj", gpencil)
   bpy.context.scene.collection.objects.link(obj)

   # Position in 3D space
   obj.location = (0, -2, 1)  # In front of 3D building

   # Create animation layer
   layer = gpencil.layers.new("CharacterLayer")
   frame = layer.frames.new(1)

   # Add strokes for character
   stroke = frame.strokes.new()
   stroke.points.add(count=4)
   # Define character silhouette
   ```

3. **Setup Camera and Render Settings**
   ```python
   # Configure camera for mixed media
   camera = bpy.data.objects['Camera']
   camera.location = (-5, -5, 3)
   camera.rotation_euler = (1.1, 0, -0.8)

   # Set EEVEE_NEXT for real-time stylized rendering
   bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'

   # Enable ambient occlusion for depth
   bpy.context.scene.eevee.use_gtao = True

   # Enable bloom for 2D glow effects
   bpy.context.scene.eevee.use_bloom = True
   ```

**Success Criteria:**
- [ ] 2D and 3D elements integrated in scene
- [ ] Proper depth sorting (2D in front/behind 3D)
- [ ] Camera captures both 2D and 3D
- [ ] Render settings optimize for mixed media

**Advanced:** See `reference/NPR_RENDERING.md` for camera setup, lighting, cel-shading

---
