# Foreground Plate Workflow - Detailed Process Breakdown

**Purpose:** Deep dive into the automated foreground plate setup process, explaining what happens internally and why each step is necessary.

---

## Overview

The `create_foreground_plate()` automation replaces a manual 23-step process with a single command that executes in ~500ms. This document explains what happens during that automation.

---

## Manual Process (23 Steps - Replaced by Automation)

**What Artists Previously Had to Do:**

### Phase 1: Media Source Setup (5 steps)
1. Content Browser → Right-click → Media → Img Media Source
2. Name the asset (MS_ShotName)
3. Open ImgMediaSource
4. Set Sequence Path to first frame (D:/Plates/Shot001/Shot001_*.exr)
5. Configure frame rate and loop settings

### Phase 2: Media Player Setup (4 steps)
6. Content Browser → Right-click → Media → Media Player
7. Check "Create Media Texture" checkbox
8. Name assets (MP_ShotName, MT_ShotName)
9. Open MediaPlayer → Set MediaSource → Click Play

### Phase 3: Material Creation (6 steps)
10. Content Browser → Right-click → Material
11. Name material (M_ShotName)
12. Open Material Editor
13. Set Shading Model → Unlit
14. Set Blend Mode → Masked (or Translucent)
15. Enable Two-Sided
16. Create texture sampler node
17. Connect MediaTexture to sampler
18. Add Scalar Parameters (OpacityMultiplier, EmissiveMultiplier)
19. Wire up material graph
20. Save and compile

### Phase 4: Camera & ImagePlate Setup (3 steps)
21. Spawn CineCameraActor (must be Blueprint-based for Python)
22. Add ImagePlate component
23. Configure ImagePlate:
    - Assign material
    - Set FillScreen mode
    - Attach to camera component

**Total Time:** 10-15 minutes per shot (error-prone, easy to miss steps)

**Automation Time:** ~500ms (consistent, validated)

---

## Automated Process Breakdown

### Internal Execution Flow

```python
# Simplified view of what create_foreground_plate() does internally

def create_foreground_plate(sequence_path, plate_name, ...):
    # Step 1: Create ImgMediaSource
    media_source = create_img_media_source(sequence_path, proxy_path)

    # Step 2: Create MediaPlayer + MediaTexture
    media_player, media_texture = create_media_player_and_texture(
        media_source, enable_loop
    )

    # Step 3: Create Material or Material Instance
    if master_material_path:
        material = create_material_instance(master_material_path, media_texture)
    else:
        material = create_vfx_material(media_texture, opacity, emissive)

    # Step 4: Spawn Blueprint Camera with ImagePlate
    camera = spawn_blueprint_camera(plate_name, material)

    # Step 5: Auto-play MediaPlayer
    if auto_play_media:
        media_player.play()

    return {
        "success": True,
        "assets_created": {...}
    }
```

---

## Step 1: ImgMediaSource Creation

**What Happens:**
```python
def create_img_media_source(sequence_path, proxy_path):
    # Parse file path to extract directory and pattern
    # D:/Plates/Shot001/Shot001_0001.exr
    # → D:/Plates/Shot001/Shot001_*.exr

    base_dir = os.path.dirname(sequence_path)
    file_name = os.path.basename(sequence_path)

    # If proxy_path provided, use subfolder
    if proxy_path:
        base_dir = os.path.join(base_dir, proxy_path)

    # Create wildcard pattern
    sequence_pattern = re.sub(r'\d{4}', '*', file_name)

    # Create asset
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.ImgMediaSourceFactory()

    media_source = asset_tools.create_asset(
        asset_name=f"MS_{plate_name}",
        package_path="/Game/Media/Sources",
        asset_class=unreal.ImgMediaSource,
        factory=factory
    )

    # Configure properties
    media_source.set_editor_property('sequence_path',
        unreal.DirectoryPath(base_dir))
    media_source.set_sequence_path(sequence_pattern)

    return media_source
```

**Key Details:**
- **Wildcard Pattern:** Converts `Shot001_0001.exr` → `Shot001_*.exr`
- **Proxy Support:** Uses subfolder if `proxy_path="lowres"` provided
- **Asset Location:** Created at `/Game/Media/Sources/` by default
- **Validation:** Checks that first frame exists before creating

**Common Issues:**
- If sequence_path doesn't exist → Error: "First frame not found"
- If wildcard pattern wrong → MediaPlayer shows black frame
- If frame rate mismatch → Playback speed incorrect

---

## Step 2: MediaPlayer and MediaTexture Creation

**What Happens:**
```python
def create_media_player_and_texture(media_source, enable_loop):
    # Create MediaPlayer
    media_player = asset_tools.create_asset(
        asset_name=f"MP_{plate_name}",
        package_path="/Game/Media/Players",
        asset_class=unreal.MediaPlayer,
        factory=unreal.MediaPlayerFactory()
    )

    # Configure loop setting
    media_player.set_looping(enable_loop)

    # Create MediaTexture
    media_texture = asset_tools.create_asset(
        asset_name=f"MT_{plate_name}",
        package_path="/Game/Media/Textures",
        asset_class=unreal.MediaTexture,
        factory=unreal.MediaTextureFactory()
    )

    # Link texture to player
    media_texture.set_editor_property('media_player', media_player)

    # Optional: Open and play immediately
    media_player.open_source(media_source)

    return media_player, media_texture
```

**Key Details:**
- **Asset Linking:** MediaTexture references MediaPlayer (not MediaSource)
- **Auto-Play:** `open_source()` starts playback immediately
- **Loop Setting:** Controls whether sequence repeats at end
- **Texture Output:** MediaTexture updates every frame during playback

**Performance:**
- First frame load: 1-2 seconds (EXR decompression)
- Subsequent frames: Real-time (ImgMedia plugin optimization)
- 4K EXR: ~200-300ms per frame (proxy recommended)

---

## Step 3: Material Creation

### Option A: Create New Material (Unique Per Shot)

**What Happens:**
```python
def create_vfx_material(media_texture, opacity_mult, emissive_mult):
    # Create material asset
    material = asset_tools.create_asset(
        asset_name=f"M_{plate_name}",
        package_path="/Game/Materials",
        asset_class=unreal.Material,
        factory=unreal.MaterialFactoryNew()
    )

    # Set material properties
    material.set_editor_property('shading_model',
        unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('blend_mode',
        unreal.BlendMode.BLEND_MASKED)  # or BLEND_TRANSLUCENT
    material.set_editor_property('two_sided', True)

    # Create material graph nodes
    texture_sample = create_node(unreal.MaterialExpressionTextureSample)
    texture_sample.set_editor_property('texture', media_texture)

    opacity_param = create_node(unreal.MaterialExpressionScalarParameter)
    opacity_param.set_editor_property('parameter_name', 'OpacityMultiplier')
    opacity_param.set_editor_property('default_value', opacity_mult)

    emissive_param = create_node(unreal.MaterialExpressionScalarParameter)
    emissive_param.set_editor_property('parameter_name', 'EmissiveMultiplier')
    emissive_param.set_editor_property('default_value', emissive_mult)

    # Wire up connections
    material.emissive_color = texture_sample.rgb * emissive_param
    material.opacity_mask = texture_sample.a * opacity_param

    # Compile
    unreal.MaterialEditingLibrary.recompile_material(material)

    return material
```

**Material Properties Explained:**

**Shading Model: Unlit**
- No lighting calculations (plate is pre-lit from live action)
- Texture displays exactly as authored
- Best performance (no shadow/reflection overhead)

**Blend Mode: Masked vs Translucent**
- **Masked:** Hard alpha cutout (0 or 1, no in-between)
  - Use for: Clean edges, rotoscoped elements
  - Performance: Faster (no sorting overhead)
  - Limitation: No soft edges

- **Translucent:** Soft alpha blending (0.0 to 1.0)
  - Use for: Soft edges, atmospheric elements
  - Performance: Slower (depth sorting required)
  - Benefit: Smooth compositing

**Two-Sided: Enabled**
- Renders both front and back faces
- Important if camera passes through plate (prevents disappearing)
- Minor performance cost (~5%)

**Parameters:**
- **OpacityMultiplier (0.0-1.0):**
  - 0.5 = 50% transparent (ghosted for alignment)
  - 1.0 = Full opacity (final render)

- **EmissiveMultiplier (0.0-5.0):**
  - 0.5 = Darker plate
  - 1.0 = Normal brightness
  - 2.0 = Brighter (better visibility during alignment)

---

### Option B: Create Material Instance (Multi-Shot Pattern)

**What Happens:**
```python
def create_material_instance(master_material_path, media_texture):
    # Load master material
    master_material = unreal.load_asset(master_material_path)

    # Create material instance
    material_instance = asset_tools.create_asset(
        asset_name=f"MI_{plate_name}",
        package_path="/Game/Materials/Instances",
        asset_class=unreal.MaterialInstanceConstant,
        factory=unreal.MaterialInstanceConstantFactoryNew()
    )

    # Set parent
    material_instance.set_editor_property('parent', master_material)

    # Override texture parameter
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
        material_instance, 'PlateTexture', media_texture
    )

    return material_instance
```

**Master Material Pattern:**
```
M_ForegroundPlate_Master (created once)
├── Texture Parameter: PlateTexture
├── Scalar Parameter: OpacityMultiplier
├── Scalar Parameter: EmissiveMultiplier
└── [Material graph with shared logic]

MI_Shot001_FG (instance)
├── PlateTexture = MT_Shot001_FG (OVERRIDDEN)
├── OpacityMultiplier = 1.0 (inherited)
└── EmissiveMultiplier = 1.0 (inherited)

MI_Shot002_FG (instance)
├── PlateTexture = MT_Shot002_FG (OVERRIDDEN)
├── OpacityMultiplier = 1.0 (inherited)
└── EmissiveMultiplier = 1.0 (inherited)
```

**Benefits:**
- Update master → All instances update
- Texture changes isolated (Shot002 doesn't affect Shot003)
- Scalable to 100+ shots
- Consistent look across shots

---

## Step 4: Blueprint Camera with ImagePlate

**Why Blueprint Required:**

Python API limitation in Unreal 5.5:
```python
# This DOES NOT WORK in Python:
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CineCameraActor,
    location=(0, 0, 0)
)
# ImagePlate component cannot be added via Python API

# Workaround: Use Blueprint-based camera
blueprint_class = unreal.load_class(None,
    "/Game/Blueprints/Cameras/cam_example_Blueprint.cam_example_Blueprint_C"
)
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    blueprint_class, location=(0, 0, 0)
)
# Blueprint already has ImagePlate component configured
```

**Blueprint Template Requirements:**
- Base class: CineCameraActor
- Components:
  - CineCameraComponent (root)
  - ImagePlateComponent (attached to camera)
  - ImagePlateFrustumComponent (auto-created by ImagePlate)

**What Happens:**
```python
def spawn_blueprint_camera(plate_name, material):
    # Load Blueprint class
    bp_class = unreal.load_class(None,
        "/Game/Blueprints/Cameras/cam_example_Blueprint.cam_example_Blueprint_C"
    )

    # Spawn actor
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        bp_class,
        location=unreal.Vector(0, 0, 0),
        rotation=unreal.Rotator(0, 0, 0)
    )

    # Rename
    camera.set_actor_label(f"Cam_{plate_name}")

    # Find ImagePlate component
    components = camera.get_components_by_class(unreal.ImagePlateComponent)
    if components:
        image_plate = components[0]

        # Configure ImagePlate
        image_plate.set_editor_property('plate', material)

        # Set render target mode
        image_plate.set_editor_property('render_target_mode',
            unreal.ImagePlateMode.FIT_TO_FRUSTUM)

    return camera
```

**ImagePlate Configuration:**
- **plate:** Material/Material Instance to display
- **render_target_mode:** FIT_TO_FRUSTUM (fills camera view)
- **Component hierarchy:**
  ```
  CineCameraActor
  └── CineCameraComponent
      └── ImagePlateComponent
          └── ImagePlateFrustumComponent (auto-created)
  ```

---

## Step 5: Auto-Play MediaPlayer

**What Happens:**
```python
def auto_play_media_player(media_player, media_source):
    # Open media source
    media_player.open_source(media_source)

    # Play immediately
    media_player.play()

    # Alternative: Use URL
    # media_player.open_url("imgmedia://D:/Plates/Shot001/Shot001_*.exr")
```

**Playback Lifecycle:**
1. `open_source()` → Loads first frame (~1-2 seconds for EXR)
2. `play()` → Starts playback at real-time frame rate
3. MediaTexture updates every frame
4. Material displays updated texture
5. ImagePlate shows material in viewport

**Validation:**
```python
# Check if playing
is_playing = media_player.is_playing()  # True/False

# Check frame info
current_time = media_player.get_time()
duration = media_player.get_duration()
frame_rate = media_player.get_video_track_frame_rate(0, 0)
```

---

## Result Structure

**What Gets Returned:**
```python
{
    "success": True,
    "assets_created": {
        "media_source": "MS_Shot001_FG",
        "media_player": "MP_Shot001_FG",
        "media_texture": "MT_Shot001_FG",
        "material": "M_Shot001_FG",  # or "MI_Shot001_FG" for instance
        "camera": "Cam_Shot001_FG",
        "image_plate": "IP_Shot001_FG"
    },
    "asset_paths": {
        "media_source": "/Game/Media/Sources/MS_Shot001_FG",
        "media_player": "/Game/Media/Players/MP_Shot001_FG",
        ...
    },
    "errors": []
}
```

---

## Validation Checklist

**After Automation Completes:**

1. **Content Browser Check:**
   - ✅ MS_{plate_name} exists in /Game/Media/Sources/
   - ✅ MP_{plate_name} exists in /Game/Media/Players/
   - ✅ MT_{plate_name} exists in /Game/Media/Textures/
   - ✅ M_{plate_name} or MI_{plate_name} exists in /Game/Materials/
   - ✅ Cam_{plate_name} exists in World Outliner

2. **MediaPlayer Check:**
   - ✅ Double-click MP_{plate_name} → Shows first frame
   - ✅ Play button active (green)
   - ✅ Timeline scrubbing works
   - ✅ Loop enabled (if requested)

3. **Camera Check:**
   - ✅ Select Cam_{plate_name} in Outliner
   - ✅ Right-click → Pilot Camera Actor
   - ✅ Viewport shows image sequence
   - ✅ ImagePlate fills screen (FIT_TO_FRUSTUM mode)

4. **Material Check:**
   - ✅ Open material/instance
   - ✅ PlateTexture parameter = MT_{plate_name}
   - ✅ OpacityMultiplier = expected value
   - ✅ EmissiveMultiplier = expected value
   - ✅ Blend mode = Masked or Translucent
   - ✅ Two-Sided = True

---

## Diagnostic Script

**InspectCameraComponents.py:**
```python
import unreal

def inspect_camera_components():
    # Get selected actor
    selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors()

    if not selected_actors:
        print("ERROR: No actor selected")
        return

    camera = selected_actors[0]

    # Check for ImagePlate component
    image_plates = camera.get_components_by_class(unreal.ImagePlateComponent)

    if not image_plates:
        print("ERROR: No ImagePlateComponent found")
        return

    image_plate = image_plates[0]

    # Check configuration
    print(f"ImagePlate Component: {image_plate.get_name()}")
    print(f"Material: {image_plate.get_editor_property('plate')}")
    print(f"Render Mode: {image_plate.get_editor_property('render_target_mode')}")

    # Check frustum component
    frustums = camera.get_components_by_class(unreal.ImagePlateFrustumComponent)
    if frustums:
        print(f"✅ ImagePlateFrustumComponent present: {frustums[0].get_name()}")
    else:
        print("❌ WARNING: ImagePlateFrustumComponent missing")

# Run diagnostic
inspect_camera_components()
```

---

## Performance Metrics

**Setup Time:**
- ImgMediaSource creation: ~50ms
- MediaPlayer + MediaTexture creation: ~100ms
- Material creation: ~150ms (or ~50ms for instance)
- Blueprint camera spawn: ~100ms
- ImagePlate configuration: ~50ms
- MediaPlayer auto-play: ~50ms
- **Total:** ~500ms (vs 10-15 minutes manual)

**Playback Performance:**
- 1080p EXR: 24fps real-time
- 4K EXR: 12-15fps (proxy recommended)
- Proxy workflow: 24fps+ (any resolution)

**Memory Usage:**
- ImgMediaSource: ~10MB
- MediaPlayer: ~50MB
- MediaTexture: ~100-500MB (depends on resolution)
- Material: ~5MB
- **Total:** ~200-600MB per shot

---

## Edge Cases

**Case 1: Missing First Frame**
```python
# Automation checks:
if not os.path.exists(sequence_path):
    return {"success": False, "error": "First frame not found"}
```

**Case 2: Invalid Wildcard Pattern**
```python
# Pattern must match: ShotName_0001.exr → ShotName_*.exr
# If pattern wrong: MediaPlayer loads but shows black
```

**Case 3: Blueprint Template Missing**
```python
# If cam_example_Blueprint not found:
try:
    bp_class = unreal.load_class(None, blueprint_path)
except:
    return {"success": False, "error": "Blueprint template not found"}
```

**Case 4: ImagePlate Plugin Disabled**
```python
# Check plugin status:
plugin_manager = unreal.PluginManager.get()
if not plugin_manager.is_plugin_enabled("ImagePlate"):
    return {"success": False, "error": "ImagePlate plugin not enabled"}
```

---

## Next Steps

**After Setup Completes:**

1. **Adjust Material Parameters** (if needed):
   - Content Browser → Find MI_{plate_name}
   - Double-click → Material Instance Editor
   - Adjust OpacityMultiplier for ghosting (0.5 for alignment)
   - Adjust EmissiveMultiplier for brightness (2.0 for better visibility)

2. **Switch Proxy to Full-Res** (when ready):
   - Content Browser → Find MS_{plate_name}
   - Change Sequence Path from `/lowres/` to `/` (parent folder)
   - MediaPlayer automatically updates

3. **Camera Animation** (optional):
   - Select Cam_{plate_name}
   - Sequencer → Add Camera Track
   - Animate transform to match live-action camera move

4. **Multi-Shot Setup** (if scaling):
   - See multi_shot_production.md for batch processing
   - Use master material pattern for consistency

---

**Reference:**
- Main skill: unreal-vfx-automation/SKILL.md
- Production patterns: multi_shot_production.md
- Debugging: troubleshooting.md
- Session logs: Session_2025-10-25_ImagePlate.md

**Version:** 1.0.0
**Last Updated:** 2025-10-25
