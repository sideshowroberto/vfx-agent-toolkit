# Material Patterns - Unreal Engine 5.5 Python

**Document Version:** 1.0.0
**Target:** Unreal Engine 5.5+
**Last Updated:** 2025-10-25
**Python Version:** 3.11 (UE built-in)

---

## Overview

### Purpose

Material and material instance creation workflows for Unreal Engine Python API.

**Key Topics:**
- Material creation (basic)
- Material instance creation (primary workflow)
- Parameter overrides (Texture, Scalar, Vector)
- MaterialEditingLibrary usage
- Master material + instance pattern

---

## Material Creation (Limited in Python)

### Basic Material Creation

**What Works:**
```python
import unreal

# Get AssetTools
tools = unreal.AssetToolsHelpers.get_asset_tools()

# Create material
material = tools.create_asset(
    asset_name="M_MyMaterial",
    package_path="/Game/Materials",
    asset_class=unreal.Material,
    factory=unreal.MaterialFactoryNew()
)

# Set basic properties
material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
material.set_editor_property('two_sided', True)
```

**What's Limited:**
- Cannot build material graph (nodes, connections)
- MaterialExpression API not fully exposed
- Node-based construction C++ only

**Recommendation:** Create master materials in editor, use instances in Python

---

### Material Properties

**Shading Models:**
```python
# Set shading model
material.set_editor_property('shading_model',
    unreal.MaterialShadingModel.MSM_UNLIT)        # No lighting
    # unreal.MaterialShadingModel.MSM_DEFAULT_LIT  # Standard PBR
    # unreal.MaterialShadingModel.MSM_SUBSURFACE   # Skin, wax
    # unreal.MaterialShadingModel.MSM_CLEAR_COAT   # Car paint
```

**Blend Modes:**
```python
# Set blend mode
material.set_editor_property('blend_mode',
    unreal.BlendMode.BLEND_OPAQUE)       # Solid, no transparency
    # unreal.BlendMode.BLEND_MASKED        # Hard alpha cutout
    # unreal.BlendMode.BLEND_TRANSLUCENT   # Soft alpha blending
    # unreal.BlendMode.BLEND_ADDITIVE      # Additive blending (lights)
```

**Additional Properties:**
```python
# Two-sided rendering
material.set_editor_property('two_sided', True)

# Disable depth test (render on top)
material.set_editor_property('disable_depth_test', True)
```

---

## Material Instance Creation

### MaterialInstance vs MaterialInstanceConstant

**MaterialInstanceConstant:**
- Created at editor-time
- Saved to disk as asset
- Can be referenced in Blueprints
- **Use for VFX workflows**

**MaterialInstanceDynamic:**
- Created at runtime
- Not saved to disk
- Used in Blueprint/C++ game logic
- Not suitable for editor workflows

**Recommendation:** Always use MaterialInstanceConstant for VFX

---

### Creation Pattern

**Complete Workflow:**
```python
import unreal

# Load master material
master = unreal.load_asset("/Game/Materials/M_Master")

# Get AssetTools
tools = unreal.AssetToolsHelpers.get_asset_tools()

# Create instance
instance = tools.create_asset(
    asset_name="MI_Instance",
    package_path="/Game/Materials/Instances",
    asset_class=unreal.MaterialInstanceConstant,
    factory=unreal.MaterialInstanceConstantFactoryNew()
)

# Assign parent
instance.set_editor_property('parent', master)

# Save asset
unreal.EditorAssetLibrary.save_loaded_asset(instance)
```

---

### Assign Parent Material

**Two Methods:**

**Method 1: set_editor_property (Recommended)**
```python
instance.set_editor_property('parent', master)
```

**Method 2: Factory initial parent (During creation)**
```python
factory = unreal.MaterialInstanceConstantFactoryNew()
factory.set_editor_property('initial_parent', master)

instance = tools.create_asset(
    "MI_Instance", "/Game/Materials/Instances",
    unreal.MaterialInstanceConstant, factory
)
```

**Result:** Instance inherits all parameters and graph from master

---

## Parameter Types

### 1. Texture Parameters

**Set Texture Parameter:**
```python
# Load texture
texture = unreal.load_asset("/Game/Textures/T_BaseColor")

# Set parameter
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    instance, 'BaseColor', texture
)
```

**Common Texture Parameters:**
- `BaseColor` - Diffuse/albedo texture
- `Normal` - Normal map
- `Roughness` - Roughness map
- `Metallic` - Metallic map
- `Emissive` - Emissive texture
- `Opacity` - Alpha/opacity texture

---

### 2. Scalar Parameters

**Set Scalar Parameter:**
```python
# Set single float value
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'Opacity', 1.0
)
```

**Common Scalar Parameters:**
```python
# Opacity (0.0 = transparent, 1.0 = opaque)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'Opacity', 1.0
)

# Metallic (0.0 = dielectric, 1.0 = metal)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'Metallic', 0.0
)

# Roughness (0.0 = smooth, 1.0 = rough)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'Roughness', 0.5
)

# Emissive multiplier
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'EmissiveMultiplier', 2.0
)
```

---

### 3. Vector Parameters

**Set Vector Parameter:**
```python
# Create linear color (RGBA, 0.0-1.0)
color = unreal.LinearColor(1.0, 0.0, 0.0, 1.0)  # Red

# Set parameter
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, 'TintColor', color
)
```

**Common Vector Parameters:**
```python
# Tint color (red)
red = unreal.LinearColor(1.0, 0.0, 0.0, 1.0)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, 'TintColor', red
)

# Emissive color (warm white)
warm_white = unreal.LinearColor(1.0, 0.9, 0.8, 1.0)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, 'EmissiveColor', warm_white
)

# Custom RGB value
custom = unreal.LinearColor(0.5, 0.7, 0.3, 1.0)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, 'CustomColor', custom
)
```

**LinearColor Components:**
- `r` - Red (0.0 to 1.0)
- `g` - Green (0.0 to 1.0)
- `b` - Blue (0.0 to 1.0)
- `a` - Alpha (0.0 to 1.0, often unused in material parameters)

---

## MaterialEditingLibrary vs set_editor_property

### Critical Difference

**Material parameters are NOT editor properties**

**Why MaterialEditingLibrary?**
- Material parameters stored in override arrays
- `set_editor_property` doesn't handle arrays correctly
- MaterialEditingLibrary manages array internally

---

### Wrong Approach

```python
# [FAIL] WRONG: Doesn't work for parameters
instance.set_editor_property('BaseColor', texture)
instance.set_editor_property('Opacity', 1.0)
instance.set_editor_property('TintColor', color)

# No error, but parameters NOT set
```

---

### Correct Approach

```python
# [OK] CORRECT: Use MaterialEditingLibrary
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    instance, 'BaseColor', texture
)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'Opacity', 1.0
)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, 'TintColor', color
)
```

---

### When to Use set_editor_property

**Use for material instance properties (not parameters):**
```python
# [OK] Parent assignment
instance.set_editor_property('parent', master)

# [OK] Physical material
instance.set_editor_property('phys_material', phys_mat)

# [OK] Blend mode override (if enabled)
instance.set_editor_property('override_blend_mode', True)
instance.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
```

---

## Master Material + Instance Pattern

### Concept

**Workflow:**
1. Create master material in editor (define graph, parameters)
2. Create material instances in Python (override parameters per shot/asset)
3. Each instance lightweight (inherits graph from master)

**Benefits:**
- Master defines material logic once
- Instances override only parameters (fast)
- Changes to master propagate to all instances
- Hundreds of instances minimal overhead

---

### Master Material Setup (Editor)

**Create in Unreal Editor:**

**Material:** `M_ForegroundPlate_Master`

**Properties:**
- Shading Model: Unlit
- Blend Mode: Masked
- Two-Sided: True

**Parameters:**
1. **PlateTexture** (Texture2D)
   - Default: Black texture
   - Usage: Connect to Emissive Color (RGB)
   - Usage: Connect to Opacity Mask (Alpha)

2. **OpacityMultiplier** (Scalar, 0-1)
   - Default: 1.0
   - Usage: Multiply PlateTexture.Alpha

3. **EmissiveMultiplier** (Scalar, 0-5)
   - Default: 1.0
   - Usage: Multiply PlateTexture.RGB

**Material Graph:**
```
PlateTexture (Texture2D Parameter)
+- RGB -> Multiply (EmissiveMultiplier) -> Emissive Color
+- Alpha -> Multiply (OpacityMultiplier) -> Opacity Mask
```

**Save:** `/Game/Materials/M_ForegroundPlate_Master`

---

### Python: Create Instances

**Single Instance:**
```python
import unreal

# Load master
master = unreal.load_asset("/Game/Materials/M_ForegroundPlate_Master")

# Get tools
tools = unreal.AssetToolsHelpers.get_asset_tools()

# Create instance
instance = tools.create_asset(
    "MI_Shot001",
    "/Game/Materials/Instances",
    unreal.MaterialInstanceConstant,
    unreal.MaterialInstanceConstantFactoryNew()
)

# Set parent
instance.set_editor_property('parent', master)

# Load texture
texture = unreal.load_asset("/Game/Textures/Shot001/T_Plate")

# Override parameters
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    instance, 'PlateTexture', texture
)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'OpacityMultiplier', 1.0
)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'EmissiveMultiplier', 1.0
)

# Save
unreal.EditorAssetLibrary.save_loaded_asset(instance)
```

---

### Batch Create Instances (Multi-Shot)

**Pattern:**
```python
import unreal

# Load master once
master = unreal.load_asset("/Game/Materials/M_ForegroundPlate_Master")
tools = unreal.AssetToolsHelpers.get_asset_tools()

# Process shots
for shot_num in range(1, 51):
    # Create instance
    instance = tools.create_asset(
        f"MI_Shot{shot_num:03d}",
        "/Game/Materials/Instances",
        unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew()
    )

    # Set parent
    instance.set_editor_property('parent', master)

    # Load shot-specific texture
    texture = unreal.load_asset(f"/Game/Textures/Shot{shot_num:03d}/T_Plate")

    # Override texture
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
        instance, 'PlateTexture', texture
    )

    # Default scalar parameters
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, 'OpacityMultiplier', 1.0
    )
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, 'EmissiveMultiplier', 1.0
    )

    # Save
    unreal.EditorAssetLibrary.save_loaded_asset(instance)

    print(f"Created MI_Shot{shot_num:03d}")

print("Batch creation complete")
```

**Result:** 50 material instances created in seconds

---

### Instance Independence

**Each instance is independent:**
```python
# Create two instances
instance1 = tools.create_asset("MI_Shot001", ...)
instance2 = tools.create_asset("MI_Shot002", ...)

# Set different parameters
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance1, 'OpacityMultiplier', 1.0  # Fully opaque
)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance2, 'OpacityMultiplier', 0.5  # 50% transparent
)

# Instances have different values (independent)
```

---

## Parameter Validation

### Check if Parameter Exists

**Texture Parameters:**
```python
# Get parameter names
param_names = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_names(instance)

# Check if parameter exists
if 'BaseColor' in param_names:
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
        instance, 'BaseColor', texture
    )
else:
    print("Parameter 'BaseColor' not found in material")
```

**Scalar Parameters:**
```python
param_names = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_names(instance)

if 'Opacity' in param_names:
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, 'Opacity', 1.0
    )
```

**Vector Parameters:**
```python
param_names = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_names(instance)

if 'TintColor' in param_names:
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        instance, 'TintColor', color
    )
```

---

### List All Parameters

**Debug: List all available parameters:**
```python
def list_material_parameters(instance):
    """List all parameters in material instance."""

    # Texture parameters
    tex_params = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_names(instance)
    print("Texture Parameters:")
    for param in tex_params:
        print(f"  - {param}")

    # Scalar parameters
    scalar_params = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_names(instance)
    print("Scalar Parameters:")
    for param in scalar_params:
        print(f"  - {param}")

    # Vector parameters
    vector_params = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_names(instance)
    print("Vector Parameters:")
    for param in vector_params:
        print(f"  - {param}")

# Usage
instance = unreal.load_asset("/Game/Materials/Instances/MI_Shot001")
list_material_parameters(instance)
```

---

## Advanced Patterns

### Dynamic Parameter Adjustment

**Runtime parameter changes:**
```python
# Get material instance
instance = unreal.load_asset("/Game/Materials/Instances/MI_Shot001")

# Adjust opacity (ghosting effect)
for opacity in [1.0, 0.8, 0.6, 0.4, 0.2]:
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, 'OpacityMultiplier', opacity
    )
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    print(f"Opacity: {opacity}")
```

---

### Parameter Presets

**Create parameter preset function:**
```python
def apply_preset_ghosted(instance):
    """Apply 'ghosted' preset to material instance."""
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, 'OpacityMultiplier', 0.3
    )
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, 'EmissiveMultiplier', 0.5
    )

def apply_preset_normal(instance):
    """Apply 'normal' preset to material instance."""
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, 'OpacityMultiplier', 1.0
    )
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, 'EmissiveMultiplier', 1.0
    )

# Usage
instance = unreal.load_asset("/Game/Materials/Instances/MI_Shot001")
apply_preset_ghosted(instance)
unreal.EditorAssetLibrary.save_loaded_asset(instance)
```

---

### Copy Parameters Between Instances

**Copy parameters from one instance to another:**
```python
def copy_material_parameters(source_instance, target_instance):
    """Copy all parameter overrides from source to target."""

    # Copy texture parameters
    tex_params = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_names(source_instance)
    for param in tex_params:
        # Get value from source (requires MaterialEditingLibrary method not exposed)
        # Workaround: Manually copy known parameters
        pass

    # Copy scalar parameters
    scalar_params = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_names(source_instance)
    for param in scalar_params:
        # Similar limitation
        pass

# Note: Parameter value retrieval not fully exposed in Python
# Workaround: Manually specify parameters to copy
```

**Limitation:** Getting parameter values not fully exposed. Must manually specify parameters.

---

## Common Material Workflows

### Workflow 1: Plate Material (VFX)

**Master Material:**
- Unlit, Masked, Two-Sided
- Parameters: PlateTexture, Opacity, Emissive

**Python:**
```python
master = unreal.load_asset("/Game/Materials/M_Plate_Master")
instance = create_material_instance("MI_Shot001", master)

texture = unreal.load_asset("/Game/Textures/T_Plate")
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    instance, 'PlateTexture', texture
)
```

---

### Workflow 2: PBR Material

**Master Material:**
- Default Lit
- Parameters: BaseColor, Normal, Roughness, Metallic

**Python:**
```python
master = unreal.load_asset("/Game/Materials/M_PBR_Master")
instance = create_material_instance("MI_Asset", master)

# Set textures
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    instance, 'BaseColor', unreal.load_asset("/Game/Textures/T_Albedo")
)
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    instance, 'Normal', unreal.load_asset("/Game/Textures/T_Normal")
)

# Set scalars
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'Roughness', 0.5
)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'Metallic', 0.0
)
```

---

### Workflow 3: Emissive Material (Lights)

**Master Material:**
- Unlit
- Parameter: EmissiveColor, EmissiveIntensity

**Python:**
```python
master = unreal.load_asset("/Game/Materials/M_Emissive_Master")
instance = create_material_instance("MI_Light", master)

# Set emissive color
color = unreal.LinearColor(1.0, 0.8, 0.6, 1.0)  # Warm white
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, 'EmissiveColor', color
)

# Set intensity
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
    instance, 'EmissiveIntensity', 10.0
)
```

---

## Troubleshooting

### Parameter Not Updating

**Symptom:** Set parameter but material doesn't change

**Fixes:**
1. Use MaterialEditingLibrary (NOT `set_editor_property`)
2. Check parameter name (case-sensitive)
3. Verify parameter exists in master material
4. Save asset after setting parameter

```python
# [OK] CORRECT
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(...)
unreal.EditorAssetLibrary.save_loaded_asset(instance)
```

---

### Parent Material Not Set

**Symptom:** Instance has no parent, appears broken

**Fix:**
```python
# Set parent before setting parameters
instance.set_editor_property('parent', master)
```

---

### Texture Parameter Shows Black

**Causes:**
1. Texture not loaded correctly
2. Parameter name wrong
3. Texture format incompatible

**Fix:**
```python
# Verify texture loaded
texture = unreal.load_asset("/Game/Textures/T_Texture")
if texture is None:
    print("Texture not found")

# Check parameter exists
params = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_names(instance)
if 'BaseColor' not in params:
    print("Parameter 'BaseColor' not in material")
```

---

## Best Practices

### 1. Create Master Materials in Editor

**Don't:** Build material graph in Python (limited API)

**Do:** Create master in editor, instances in Python

---

### 2. Always Set Parent First

```python
# [OK] CORRECT order
instance = tools.create_asset(...)
instance.set_editor_property('parent', master)  # Parent first
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(...)  # Then parameters
```

---

### 3. Save After Changes

```python
# Set parameters
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(...)

# Save asset
unreal.EditorAssetLibrary.save_loaded_asset(instance)
```

---

### 4. Use Consistent Naming

```python
# Good naming
"MI_Shot001"  # Material Instance, Shot 001
"MI_Prop_Red"  # Material Instance, Prop, Red variant
"MI_Character_Skin"  # Material Instance, Character, Skin

# Avoid
"MaterialInstance1"  # Not descriptive
"mat_shot_001"  # Inconsistent prefix
```

---

## References

### Related Documentation
- **api_limitations_ue55.md** - Material graph construction limitations
- **SKILL.md** - Quick start patterns
- **component_patterns.md** - Assigning materials to components

### Official Documentation
- Unreal Engine - MaterialEditingLibrary API
- Epic Games - Material instance best practices

---

**Document Status:** Production-ready
**Tested:** UE 5.5.0, Windows 11, 2025-10-25
**Coverage:** Material creation, instance patterns, parameter overrides

---

*Material Patterns - Unreal Engine 5.5 Python*
*Last Updated: 2025-10-25*
