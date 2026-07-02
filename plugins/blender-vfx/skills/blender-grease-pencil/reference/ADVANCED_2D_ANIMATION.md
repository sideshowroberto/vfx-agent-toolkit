# Blender Grease Pencil - Advanced 2D Animation

**Part of:** blender-grease-pencil skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2025-10-24

---

## Overview

This reference covers advanced 2D animation techniques for Grease Pencil, including traditional animation workflows, timing principles, onion skinning configuration, and complex keyframe management.

**When to Use This Reference:**
- Creating complex character animation
- Implementing traditional animation principles
- Managing large frame counts
- Fine-tuning animation timing
- Working with multiple characters/elements

---

## Traditional Animation Workflow

### Timing Charts and Spacing

**12 Principles of Animation Application:**

```python
import bpy

def create_timing_chart(layer, start_frame, end_frame, ease_in_frames=4, ease_out_frames=4):
    """
    Create keyframes with proper spacing for traditional animation timing

    Easing pattern:
    - Ease In: 4 frames (slow start)
    - Middle: Linear spacing
    - Ease Out: 4 frames (slow stop)
    """
    total_frames = end_frame - start_frame
    middle_frames = total_frames - ease_in_frames - ease_out_frames

    keyframes = []

    # Ease in (slow spacing)
    for i in range(ease_in_frames):
        # Quadratic easing
        progress = (i / ease_in_frames) ** 2
        frame_num = start_frame + int(progress * ease_in_frames)
        keyframes.append(frame_num)
        layer.frames.new(frame_num)

    # Middle (linear spacing)
    for i in range(middle_frames):
        frame_num = start_frame + ease_in_frames + i
        keyframes.append(frame_num)
        layer.frames.new(frame_num)

    # Ease out (slow spacing)
    for i in range(ease_out_frames):
        progress = 1 - ((ease_out_frames - i) / ease_out_frames) ** 2
        frame_num = end_frame - ease_out_frames + int(progress * ease_out_frames)
        keyframes.append(frame_num)
        layer.frames.new(frame_num)

    return keyframes

# Example usage
obj = bpy.data.objects['GPencil_Character']
layer = obj.data.layers['WalkCycle']
timing = create_timing_chart(layer, start_frame=1, end_frame=24)
print(f"Keyframes created at: {timing}")
```

**Frame Rate Standards:**
- **24 fps (Film):** Traditional animation standard
- **12 fps (TV Animation):** "Animation on twos" (drawings held 2 frames)
- **8 fps (Limited Animation):** "Animation on threes" (drawings held 3 frames)

---

## Onion Skinning Configuration

### Detailed Onion Skin Settings

```python
import bpy

def configure_onion_skinning(layer, mode='default'):
    """
    Configure onion skinning for different animation workflows

    Modes:
    - default: 2 frames before/after
    - detailed: 4 frames before/after (for timing refinement)
    - minimal: 1 frame before/after (for cleanup)
    - custom: Asymmetric (more frames before than after)
    """
    layer.use_onion_skinning = True

    if mode == 'default':
        layer.onion_before_range = 2
        layer.onion_after_range = 2
        layer.use_onion_fade = True

    elif mode == 'detailed':
        layer.onion_before_range = 4
        layer.onion_after_range = 4
        layer.use_onion_fade = True
        layer.onion_factor = 0.7  # Higher opacity for better visibility

    elif mode == 'minimal':
        layer.onion_before_range = 1
        layer.onion_after_range = 1
        layer.use_onion_fade = False

    elif mode == 'custom':
        # More frames before (for reference to previous work)
        layer.onion_before_range = 3
        layer.onion_after_range = 1
        layer.use_onion_fade = True

    # Set custom colors for onion skin (optional)
    layer.before_color = (0.0, 0.5, 1.0)  # Blue for before frames
    layer.after_color = (1.0, 0.5, 0.0)   # Orange for after frames

    print(f"Onion skinning configured: {mode}")

# Example: Setup for character animation
obj = bpy.data.objects['Character_GP']
char_layer = obj.data.layers['Character']
configure_onion_skinning(char_layer, mode='detailed')
```

---

## Complex Layer Setups

### Multi-Character Animation

```python
import bpy

def create_multi_character_setup(gpencil, characters):
    """
    Create organized layer structure for multiple characters

    Args:
        gpencil: Grease Pencil data block
        characters: List of character names
    """
    for char_name in characters:
        # Create main character layer
        char_layer = gpencil.layers.new(f"{char_name}_Main")
        char_layer.use_onion_skinning = True

        # Create cleanup layer (refined drawings)
        cleanup_layer = gpencil.layers.new(f"{char_name}_Cleanup")
        cleanup_layer.opacity = 1.0

        # Create rough layer (initial animation)
        rough_layer = gpencil.layers.new(f"{char_name}_Rough")
        rough_layer.opacity = 0.3  # Dim for reference
        rough_layer.lock = True    # Lock after roughing stage

    # Create shared background layer
    bg_layer = gpencil.layers.new("Background")
    bg_layer.opacity = 0.6
    bg_layer.lock = True  # Prevent accidental edits

# Example usage
gpencil = bpy.data.grease_pencils['Animation']
characters = ['Hero', 'Villain', 'Sidekick']
create_multi_character_setup(gpencil, characters)
```

---

## Frame Interpolation Techniques

### Automatic Inbetweening

```python
import bpy
from mathutils import Vector

def interpolate_strokes(layer, start_frame, end_frame, inbetweens=2):
    """
    Create interpolated frames between two keyframes

    Note: Simplified interpolation - production tools use more sophisticated algorithms
    """
    start_fr = layer.frames.get(start_frame)
    end_fr = layer.frames.get(end_frame)

    if not start_fr or not end_fr:
        print("Start or end frame not found")
        return

    # Calculate frame spacing
    frame_step = (end_frame - start_frame) / (inbetweens + 1)

    for i in range(1, inbetweens + 1):
        # Create new frame
        new_frame_num = start_frame + int(frame_step * i)
        new_frame = layer.frames.new(new_frame_num)

        # Interpolate each stroke
        for start_stroke, end_stroke in zip(start_fr.strokes, end_fr.strokes):
            new_stroke = new_frame.strokes.new()
            new_stroke.points.add(count=len(start_stroke.points))

            # Interpolate point positions
            blend_factor = i / (inbetweens + 1)
            for idx, (start_pt, end_pt) in enumerate(zip(start_stroke.points, end_stroke.points)):
                new_stroke.points[idx].co = start_pt.co.lerp(end_pt.co, blend_factor)
                new_stroke.points[idx].pressure = (
                    start_pt.pressure * (1 - blend_factor) +
                    end_pt.pressure * blend_factor
                )

    print(f"Created {inbetweens} interpolated frames between {start_frame} and {end_frame}")

# Example: Add 2 inbetween frames
obj = bpy.data.objects['Character_GP']
layer = obj.data.layers['Walk']
interpolate_strokes(layer, start_frame=1, end_frame=12, inbetweens=2)
```

---

## Animation Cycles

### Creating Loop Animations

```python
import bpy

def create_animation_cycle(layer, start_frame, end_frame):
    """
    Create seamless animation loop by copying first frame to end
    """
    first_frame = layer.frames.get(start_frame)
    if not first_frame:
        print("Start frame not found")
        return

    # Create final frame matching first frame
    final_frame = layer.frames.new(end_frame)

    # Copy all strokes from first to last
    for stroke in first_frame.strokes:
        new_stroke = final_frame.strokes.new()
        new_stroke.points.add(count=len(stroke.points))

        # Copy point data
        for idx, point in enumerate(stroke.points):
            new_stroke.points[idx].co = point.co
            new_stroke.points[idx].pressure = point.pressure

        # Copy stroke properties
        new_stroke.line_width = stroke.line_width
        new_stroke.material_index = stroke.material_index

    print(f"Animation cycle created: {start_frame} to {end_frame}")
    print("Animation will loop seamlessly")

# Example: Create 24-frame walk cycle
obj = bpy.data.objects['Character_GP']
layer = obj.data.layers['WalkCycle']
create_animation_cycle(layer, start_frame=1, end_frame=24)
```

---

## Best Practices

**Animation Planning:**
1. Create thumbnail sketches (planning stage)
2. Block out key poses (rough layer)
3. Add breakdowns (major inbetweens)
4. Complete inbetweens
5. Cleanup pass (final layer)

**Layer Organization:**
- Separate rough, cleanup, and color layers
- Use layer colors for visual organization
- Lock layers after completion stages
- Name layers descriptively (e.g., "Hero_Walk_Rough")

**Performance Optimization:**
- Use simplified strokes for rough animation
- Add detail only on cleanup layer
- Delete unused frames and layers
- Use frame holding ("on twos" or "on threes") to reduce frame count

---

**Return to:** `.claude/skills/blender-grease-pencil/SKILL.md`
