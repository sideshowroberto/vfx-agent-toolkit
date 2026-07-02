# Blender Rendering: Detailed Workflows

## Workflow 1: Production Cycles Setup

**Use When:** Need photorealistic rendering with path tracing

**Steps:**

1. **Switch to Cycles Engine**
   ```python
   import bpy
   scene = bpy.context.scene
   scene.render.engine = 'CYCLES'
   cycles = scene.cycles
   ```

2. **Configure Performance Settings**
   ```python
   # Sampling
   cycles.samples = 128              # Render samples
   cycles.preview_samples = 32       # Viewport samples
   cycles.use_denoising = True       # Enable AI denoising
   cycles.denoiser = 'OPENIMAGEDENOISE'

   # Device (GPU acceleration)
   cycles.device = 'GPU'
   ```

3. **Set Light Path Quality**
   ```python
   # Light bounces
   cycles.max_bounces = 12           # Total light bounces
   cycles.diffuse_bounces = 4        # Diffuse surfaces
   cycles.glossy_bounces = 4         # Reflective surfaces
   cycles.transmission_bounces = 12  # Glass/transparent
   cycles.volume_bounces = 2         # Volumetric fog
   ```

---

## Workflow 2: EEVEE_NEXT Real-Time Rendering

**Use When:** Need fast previews or real-time rendering for animation

**Steps:**

1. **Configure EEVEE_NEXT Engine**
   ```python
   scene = bpy.context.scene
   scene.render.engine = 'BLENDER_EEVEE_NEXT'
   eevee = scene.eevee

   # Quality settings
   eevee.taa_render_samples = 64     # Final render quality
   eevee.taa_samples = 16            # Viewport preview
   ```

2. **Enable Lighting Features**
   ```python
   # Ambient occlusion
   eevee.use_gtao = True
   eevee.gtao_distance = 0.2
   eevee.gtao_factor = 1.0
   ```

3. **Setup Compositor for Post-Effects**
   ```python
   # Enable compositor
   scene.use_nodes = True
   tree = scene.node_tree
   tree.nodes.clear()

   # Add render input
   render_layers = tree.nodes.new('CompositorNodeRLayers')

   # Add bloom effect
   bloom = tree.nodes.new('CompositorNodeGlare')
   bloom.glare_type = 'BLOOM'
   bloom.threshold = 0.8
   bloom.size = 6

   # Add output
   composite = tree.nodes.new('CompositorNodeComposite')

   # Connect nodes
   tree.links.new(render_layers.outputs['Image'], bloom.inputs['Image'])
   tree.links.new(bloom.outputs['Image'], composite.inputs['Image'])
   ```

---

## Workflow 3: Material Creation (4.5.0 Compatible)

**Use When:** Creating materials that work in both Cycles and EEVEE_NEXT

**Steps:**

1. **Create Base Material**
   ```python
   import bpy

   # Create material
   mat = bpy.data.materials.new(name="MyMaterial")
   mat.use_nodes = True
   nodes = mat.node_tree.nodes
   links = mat.node_tree.links

   # Get Principled BSDF
   bsdf = nodes.get("Principled BSDF")
   ```

2. **Configure Material Properties (4.5.0 Syntax)**
   ```python
   # Base color
   bsdf.inputs["Base Color"].default_value = (0.8, 0.2, 0.1, 1.0)

   # Metallic/Roughness
   bsdf.inputs["Metallic"].default_value = 0.0
   bsdf.inputs["Roughness"].default_value = 0.3

   # Glass material (NEW input names)
   bsdf.inputs["Transmission Weight"].default_value = 1.0  # 4.5.0+
   bsdf.inputs["IOR"].default_value = 1.5

   # Subsurface scattering (NEW input name)
   bsdf.inputs["Subsurface Weight"].default_value = 0.2   # 4.5.0+
   bsdf.inputs["Subsurface Radius"].default_value = (1,1,1)

   # Emission (NEW input name)
   bsdf.inputs["Emission Color"].default_value = (1,1,1,1)  # 4.5.0+
   bsdf.inputs["Emission Strength"].default_value = 2.0
   ```

3. **Assign to Object**
   ```python
   # Get object
   obj = bpy.context.active_object

   # Assign material (avoid operators)
   if obj.data.materials:
       obj.data.materials[0] = mat
   else:
       obj.data.materials.append(mat)

   # Enable smooth shading (HTTP Bridge safe)
   mesh = obj.data
   for poly in mesh.polygons:
       poly.use_smooth = True
   mesh.update()
   ```
