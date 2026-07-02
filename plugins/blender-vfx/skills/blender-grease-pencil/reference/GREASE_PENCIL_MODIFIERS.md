# Blender Grease Pencil - Modifier Workflows

**Part of:** blender-grease-pencil skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers Grease Pencil modifier workflows, including procedural animation, modifier stacking strategies, and time offset techniques.

**When to Use This Reference:**
- Automating repetitive animation tasks
- Creating complex deformations
- Adding procedural variation to hand-drawn animation
- Achieving effects difficult to animate manually

---

## Procedural Animation with Modifiers

### Noise Modifier: Organic Movement

```python
import bpy

def add_noise_animation(obj, layer_name=None, factor=0.1, step=4):
    """
    Add organic movement to Grease Pencil strokes

    Args:
        obj: Grease Pencil object
        layer_name: Target layer (None = all layers)
        factor: Noise intensity (0.0-1.0)
        step: Randomize every N frames (lower = more variation)
    """
    # Add Noise modifier
    noise_mod = obj.grease_pencil_modifiers.new("OrganicNoise", type='GP_NOISE')
    noise_mod.factor = factor
    noise_mod.use_random = True
    noise_mod.step = step
    noise_mod.seed = 42  # Set seed for repeatability

    # Target specific layer if specified
    if layer_name:
        noise_mod.layer = layer_name

    # Noise factor can be animated
    noise_mod.keyframe_insert(data_path='factor', frame=1)
    noise_mod.factor = factor * 2  # Double intensity
    noise_mod.keyframe_insert(data_path='factor', frame=24)

    print(f"Noise modifier added to {obj.name}")
    return noise_mod

# Example: Add subtle hand-drawn wobble
obj = bpy.data.objects['Character_GP']
noise_mod = add_noise_animation(obj, factor=0.05, step=2)
```

**Noise Parameters:**
- `factor`: Intensity of displacement (0.0 = none, 1.0 = extreme)
- `step`: Keyframe interval (1 = every frame, 4 = every 4 frames)
- `seed`: Random seed for consistent results
- `use_random`: Enable random variation per frame

---

### Offset Modifier: Motion Graphics

```python
import bpy

def create_offset_animation(obj, start_offset=(0,0,0), end_offset=(2,0,0),
                           start_frame=1, end_frame=24):
    """
    Animate position offset for motion graphics effects

    Use Case: Staggered text animation, echoes, trails
    """
    offset_mod = obj.grease_pencil_modifiers.new("MotionOffset", type='GP_OFFSET')

    # Set initial offset
    offset_mod.location = start_offset
    offset_mod.keyframe_insert(data_path='location', frame=start_frame)

    # Set final offset
    offset_mod.location = end_offset
    offset_mod.keyframe_insert(data_path='location', frame=end_frame)

    # Optional: Add rotation offset
    offset_mod.rotation = (0, 0, 0)
    offset_mod.keyframe_insert(data_path='rotation', frame=start_frame)
    offset_mod.rotation = (0, 0, 0.5)  # 0.5 radians
    offset_mod.keyframe_insert(data_path='rotation', frame=end_frame)

    print(f"Offset animation created: {start_offset} → {end_offset}")
    return offset_mod

# Example: Text sliding in from left
obj = bpy.data.objects['Title_GP']
offset_mod = create_offset_animation(obj, start_offset=(-5,0,0), end_offset=(0,0,0))
```

---

### Time Offset Modifier: Staggered Animation

```python
import bpy

def create_time_offset(obj, offset_frames=4, layer_name=None):
    """
    Delay animation playback for echo/trail effects

    Use Case: Multiple copies with staggered timing
    """
    time_mod = obj.grease_pencil_modifiers.new("TimeDelay", type='GP_TIME')
    time_mod.offset = offset_frames  # Delay by N frames
    time_mod.mode = 'FIX'  # Fixed offset

    if layer_name:
        time_mod.layer = layer_name

    print(f"Time offset: {offset_frames} frames")
    return time_mod

# Example: Create 3 duplicates with staggered timing
base_obj = bpy.data.objects['Character_GP']

for i in range(1, 4):
    # Duplicate object
    duplicate = base_obj.copy()
    duplicate.data = base_obj.data  # Share same grease pencil data
    duplicate.name = f"Character_Echo_{i}"
    bpy.context.scene.collection.objects.link(duplicate)

    # Add time offset
    create_time_offset(duplicate, offset_frames=i * 4)

    # Fade opacity for echo effect
    duplicate.color[3] = 1.0 / (i + 1)  # Progressively more transparent
```

---

## Modifier Stacking Strategies

### Order Matters: Modifier Stack Examples

```python
import bpy

def create_stylized_line_stack(obj):
    """
    Stack modifiers for stylized line art effect

    Stack order (top to bottom):
    1. Simplify - Reduce complexity
    2. Noise - Add hand-drawn feel
    3. Smooth - Soften noise
    4. Thickness - Vary line weight
    """
    # 1. Simplify first (reduce point count)
    simplify = obj.grease_pencil_modifiers.new("Simplify", type='GP_SIMPLIFY')
    simplify.factor = 0.1

    # 2. Add noise for hand-drawn feel
    noise = obj.grease_pencil_modifiers.new("HandDrawn", type='GP_NOISE')
    noise.factor = 0.03
    noise.use_random = True

    # 3. Smooth to reduce jitter
    smooth = obj.grease_pencil_modifiers.new("Smooth", type='GP_SMOOTH')
    smooth.factor = 0.5
    smooth.step = 2

    # 4. Vary thickness for style
    thickness = obj.grease_pencil_modifiers.new("LineWeight", type='GP_THICK')
    thickness.thickness_factor = 1.5
    thickness.use_uniform_thickness = False  # Vary by pressure

    print("Stylized line stack created")

# Example usage
obj = bpy.data.objects['Character_Lines']
create_stylized_line_stack(obj)
```

**Stack Order Best Practices:**
1. **Geometric Modifiers First** (Offset, Array, Mirror)
2. **Deformation Modifiers** (Noise, Lattice, Armature)
3. **Refinement Modifiers** (Smooth, Simplify)
4. **Visual Modifiers Last** (Tint, Opacity, Thickness)

---

### Tint Modifier: Color Animation

```python
import bpy

def animate_color_tint(obj, start_color=(1,1,1), end_color=(1,0,0),
                       start_frame=1, end_frame=24):
    """
    Animate color tint for mood/emphasis changes
    """
    tint_mod = obj.grease_pencil_modifiers.new("ColorShift", type='GP_TINT')
    tint_mod.factor = 1.0  # Full tint influence

    # Animate color
    tint_mod.color = start_color
    tint_mod.keyframe_insert(data_path='color', frame=start_frame)

    tint_mod.color = end_color
    tint_mod.keyframe_insert(data_path='color', frame=end_frame)

    print(f"Color tint animation: {start_color} → {end_color}")
    return tint_mod

# Example: Character turns red when angry
obj = bpy.data.objects['Character_GP']
tint_mod = animate_color_tint(obj, start_color=(1,1,1), end_color=(1,0.2,0.2))
```

---

## Advanced Modifier Combinations

### Echo Trail Effect

```python
import bpy

def create_echo_trail(base_obj, echo_count=3, time_offset=2, fade_factor=0.3):
    """
    Create motion trail effect with multiple echoes

    Combines: Time Offset + Opacity + Color Tint
    """
    echoes = []

    for i in range(1, echo_count + 1):
        # Duplicate object
        echo = base_obj.copy()
        echo.data = base_obj.data
        echo.name = f"{base_obj.name}_Echo_{i}"
        bpy.context.scene.collection.objects.link(echo)

        # Time offset
        time_mod = echo.grease_pencil_modifiers.new("TimeOffset", type='GP_TIME')
        time_mod.offset = i * time_offset

        # Opacity fade
        opacity_mod = echo.grease_pencil_modifiers.new("FadeOut", type='GP_OPACITY')
        opacity_mod.factor = 1.0 - (i * fade_factor)

        # Color tint (progressively more blue for "ghost" effect)
        tint_mod = echo.grease_pencil_modifiers.new("GhostTint", type='GP_TINT')
        tint_mod.color = (0.5, 0.5, 1.0)  # Blue tint
        tint_mod.factor = i * 0.3

        echoes.append(echo)

    print(f"Created {echo_count} echo trails")
    return echoes

# Example: Fast-moving character with trail
obj = bpy.data.objects['Speedster_GP']
echoes = create_echo_trail(obj, echo_count=4, time_offset=1, fade_factor=0.2)
```

---

## Modifier Performance Tips

**Optimization Strategies:**

1. **Use Layer Filters:** Apply modifiers only to necessary layers
2. **Disable in Viewport:** Turn off heavy modifiers during animation
3. **Simplify First:** Reduce point count before deformation modifiers
4. **Limit Stacking:** More modifiers = slower performance

```python
# Example: Layer-specific modifier
noise_mod = obj.grease_pencil_modifiers.new("Noise", type='GP_NOISE')
noise_mod.layer = "DetailLayer"  # Only affects this layer
noise_mod.show_viewport = False  # Disable in viewport for speed
```

---

## Reference: Common Modifier Types

| Modifier | Use Case | Performance Impact |
|----------|----------|-------------------|
| GP_NOISE | Hand-drawn feel, organic movement | Low |
| GP_SMOOTH | Reduce jitter, clean strokes | Low |
| GP_OFFSET | Motion graphics, position animation | Low |
| GP_TIME | Echo trails, timing adjustments | Low |
| GP_TINT | Color animation, mood changes | Very Low |
| GP_OPACITY | Fade effects, ghosting | Very Low |
| GP_THICK | Line weight variation | Low |
| GP_SIMPLIFY | Optimize stroke complexity | Medium |
| GP_ARRAY | Duplicate patterns | Medium-High |
| GP_LATTICE | Complex deformation | High |

---

**Return to:** `.claude/skills/blender-grease-pencil/SKILL.md`
