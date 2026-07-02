# Blender Compositing: Detailed Workflows

## Workflow 1: Color Correction Pipeline

**Use When:** Adjusting exposure, contrast, color balance, or saturation

**Steps:**

1. **Setup Base Nodes**
   ```python
   scene = bpy.context.scene
   scene.use_nodes = True
   compositor = scene.node_tree
   compositor.nodes.clear()

   render_layers = compositor.nodes.new('CompositorNodeRLayers')
   composite = compositor.nodes.new('CompositorNodeComposite')
   ```

2. **Add Color Correction**
   ```python
   # Brightness/Contrast
   bright_contrast = compositor.nodes.new('CompositorNodeBrightContrast')
   bright_contrast.location = (200, 0)
   bright_contrast.inputs['Bright'].default_value = 0.1  # Brighten
   bright_contrast.inputs['Contrast'].default_value = 10  # Add contrast

   # RGB Curves for fine control
   rgb_curves = compositor.nodes.new('CompositorNodeCurveRGB')
   rgb_curves.location = (400, 0)
   ```

3. **Add Saturation**
   ```python
   # Hue/Saturation/Value
   hue_sat = compositor.nodes.new('CompositorNodeHueSat')
   hue_sat.location = (600, 0)
   hue_sat.inputs['Saturation'].default_value = 1.2  # Boost saturation
   ```

4. **Connect Pipeline**
   ```python
   links = compositor.links
   links.new(render_layers.outputs['Image'], bright_contrast.inputs['Image'])
   links.new(bright_contrast.outputs['Image'], rgb_curves.inputs['Image'])
   links.new(rgb_curves.outputs['Image'], hue_sat.inputs['Image'])
   links.new(hue_sat.outputs['Image'], composite.inputs['Image'])
   ```

**Success Criteria:**
- [ ] All nodes created without errors
- [ ] Nodes connected in sequence
- [ ] Image flows from render layers to composite
- [ ] Color adjustments visible in rendered output

---

## Workflow 2: Glare/Bloom Effects

**Use When:** Adding cinematic glow, lens flares, or light streaks

**Steps:**

1. **Create Base Setup**
   ```python
   scene.use_nodes = True
   compositor = scene.node_tree

   render_layers = compositor.nodes.new('CompositorNodeRLayers')
   composite = compositor.nodes.new('CompositorNodeComposite')
   ```

2. **Add Glare Node**
   ```python
   glare = compositor.nodes.new('CompositorNodeGlare')
   glare.location = (200, 0)
   glare.glare_type = 'GHOSTS'  # Options: GHOSTS, STREAKS, FOG_GLOW, SIMPLE_STAR
   glare.quality = 'HIGH'
   glare.threshold = 0.8  # Only bright areas glow
   glare.mix = 0.5  # Blend amount
   ```

3. **Mix with Original**
   ```python
   mix = compositor.nodes.new('CompositorNodeMixRGB')
   mix.location = (400, 0)
   mix.blend_type = 'ADD'
   mix.inputs['Fac'].default_value = 0.3  # Subtle effect

   links = compositor.links
   links.new(render_layers.outputs['Image'], glare.inputs['Image'])
   links.new(render_layers.outputs['Image'], mix.inputs[1])  # Original
   links.new(glare.outputs['Image'], mix.inputs[2])  # Glare
   links.new(mix.outputs['Image'], composite.inputs['Image'])
   ```

**Glare Type Options:**
- `GHOSTS`: Lens flare style (cinematic)
- `STREAKS`: Anamorphic lens streaks
- `FOG_GLOW`: Soft bloom (replaces old EEVEE bloom)
- `SIMPLE_STAR`: Star-shaped flares

**Success Criteria:**
- [ ] Glare only affects bright areas (threshold working)
- [ ] Effect subtle and realistic (not overpowering)
- [ ] Original image detail preserved in dark areas

---

## Workflow 3: Render Pass Compositing

**Use When:** Combining separate render passes for maximum control

**Steps:**

1. **Enable Required Passes**
   ```python
   view_layer = bpy.context.view_layer
   view_layer.use_pass_diffuse_direct = True
   view_layer.use_pass_diffuse_indirect = True
   view_layer.use_pass_glossy_direct = True
   view_layer.use_pass_glossy_indirect = True
   view_layer.use_pass_emit = True
   view_layer.use_pass_environment = True
   ```

2. **Create Render Layer Node**
   ```python
   render_layers = compositor.nodes.new('CompositorNodeRLayers')
   render_layers.location = (0, 0)

   # Available outputs:
   # - 'DiffDir' (Diffuse Direct)
   # - 'DiffInd' (Diffuse Indirect)
   # - 'GlossDir' (Glossy Direct)
   # - 'GlossInd' (Glossy Indirect)
   # - 'Emit' (Emission)
   # - 'Env' (Environment)
   ```

3. **Combine Passes**
   ```python
   # Add diffuse passes
   add_diffuse = compositor.nodes.new('CompositorNodeMixRGB')
   add_diffuse.blend_type = 'ADD'
   add_diffuse.location = (200, 100)

   links.new(render_layers.outputs['DiffDir'], add_diffuse.inputs[1])
   links.new(render_layers.outputs['DiffInd'], add_diffuse.inputs[2])

   # Add glossy passes
   add_glossy = compositor.nodes.new('CompositorNodeMixRGB')
   add_glossy.blend_type = 'ADD'
   add_glossy.location = (200, -100)

   links.new(render_layers.outputs['GlossDir'], add_glossy.inputs[1])
   links.new(render_layers.outputs['GlossInd'], add_glossy.inputs[2])

   # Combine all lighting
   combine = compositor.nodes.new('CompositorNodeMixRGB')
   combine.blend_type = 'ADD'
   combine.location = (400, 0)

   links.new(add_diffuse.outputs['Image'], combine.inputs[1])
   links.new(add_glossy.outputs['Image'], combine.inputs[2])
   ```

**Success Criteria:**
- [ ] All passes rendering correctly
- [ ] Passes combine to match beauty pass
- [ ] Individual pass control available
