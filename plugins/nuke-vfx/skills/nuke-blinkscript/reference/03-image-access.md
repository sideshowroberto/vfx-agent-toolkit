# BlinkScript Image Access

## Overview

Image access from inside the `process()` function depends on:
1. **Kernel granularity** (eComponentWise or ePixelWise)
2. **Image specification** (AccessPattern and EdgeMethod)

Certain access types must be configured in the `init()` method.

## The init() Method

Called **before** `process()` runs. Used for:
- Setting up ranged image access
- Initializing local variables

**Optional** - only needed if you have setup/initialization to do.

### Configuring Ranged Image Access

#### 1D Ranged Access Setup

**Step 1:** Specify axis (horizontal or vertical)
```cpp
void init() {
    src.setAxis(eX);  // eX = horizontal, eY = vertical
}
```

**Step 2:** Set range
```cpp
void init() {
    src.setAxis(eX);
    src.setRange(-5, 5);  // Access 5 pixels left and right
}
```

#### 2D Ranged Access Setup

**Symmetric bounds** (same range for both axes):
```cpp
void init() {
    src.setRange(-3, 3);  // 3 pixels in all directions
}
```

**Asymmetric bounds** (different ranges per axis):
```cpp
void init() {
    src.setRange(-5, -3, 5, 3);  // Different X and Y ranges
    // X range: -5 to 5 (11 pixels wide)
    // Y range: -3 to 3 (7 pixels tall)
}
```

**Note:** Ranges are **inclusive** on both sides.

### Point and Random Access

**No initialization required** for:
- `eAccessPoint` - Access current position only
- `eAccessRandom` - Access any position

### Setting Local Variables

Use `init()` to set local variables **once** instead of recalculating in every `process()` call:

```cpp
local:
    float scaledRadius;

void init() {
    // Calculate once, use in every process() call
    scaledRadius = radius * dst.bounds.width();
}
```

## Image Access from process()

Access syntax depends on **AccessPattern** and **Granularity**.

### eAccessPoint - Current Position Only

**ComponentWise:**
```cpp
dst() = src();  // Returns single float/int value
```

**PixelWise:**
```cpp
dst() = src();  // Returns float3/float4 (all components)

// Or access single component:
dst(0) = src(0);  // Red channel
dst(1) = src(1);  // Green channel
```

### eAccessRanged1D - Line of Pixels

**First parameter:** Offset along chosen axis (relative to current position)

```cpp
// If axis is eX (horizontal):
float left = src(-1);    // 1 pixel to the left
float right = src(1);    // 1 pixel to the right
float current = src(0);  // Current pixel

// PixelWise with component:
float redLeft = src(-1, 0);  // Red channel, 1 pixel left
```

### eAccessRanged2D - Rectangle of Pixels

**First two parameters:** X and Y offsets (relative to current position)

```cpp
// Access 3x3 neighborhood:
float topLeft = src(-1, 1);
float top = src(0, 1);
float topRight = src(1, 1);
float left = src(-1, 0);
float center = src(0, 0);
float right = src(1, 0);
float bottomLeft = src(-1, -1);
float bottom = src(0, -1);
float bottomRight = src(1, -1);

// PixelWise with component:
float3 centerPixel = src(0, 0);        // All components
float redCenter = src(0, 0, 0);        // Just red
```

### eAccessRandom - Any Position

**First two parameters:** Absolute X and Y coordinates

```cpp
// Access specific pixel coordinates:
float pixel = src(100, 200);  // Pixel at (100, 200)

// PixelWise:
float3 pixel = src(100, 200);     // All components
float red = src(100, 200, 0);     // Red channel at (100, 200)
```

## Return Types

All image accesses return **references** (can read and write).

### ComponentWise
Returns `image.ValueType` (e.g., `float`)

### PixelWise (no component specified)
Returns `image.SampleType` (e.g., `float3`, `float4`)

### PixelWise (component specified)
Returns `image.ValueType` (e.g., `float`)

## Bilinear Interpolation

Access pixels at **non-integer positions** with automatic interpolation.

### ComponentWise
```cpp
float value = img.bilinear(10.5f, 20.7f);
// Interpolates from 4 nearest pixels
```

### PixelWise (all components)
```cpp
float3 pixel = img.bilinear(10.5f, 20.7f);
// Returns interpolated float3
```

### PixelWise (single component)
```cpp
float red = img.bilinear(10.5f, 20.7f, 0);
// Interpolates red channel only
```

## Quick Reference

**Access Patterns:**
- Point: `image()`
- Ranged1D: `image(offset)`
- Ranged2D: `image(xOffset, yOffset)`
- Random: `image(x, y)`

**Add component for PixelWise:**
- `image(component)`
- `image(offset, component)`
- `image(xOffset, yOffset, component)`
- `image(x, y, component)`

**Bilinear:**
- `image.bilinear(x, y)` or `image.bilinear(x, y, component)`
