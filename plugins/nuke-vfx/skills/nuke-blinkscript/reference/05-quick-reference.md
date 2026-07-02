# BlinkScript Quick Reference Cheat Sheet

## Kernel Structure Template

```cpp
kernel MyKernel : ImageComputationKernel<GRANULARITY> {
    // 1. Image specifications (first)
    Image<eRead, ACCESS_PATTERN, EDGE_METHOD> src;
    Image<eWrite> dst;
    
    // 2. Parameters (public)
    param:
        float myParam;
    
    // 3. Local variables (private)
    local:
        float myLocal;
    
    // 4. define() - Set parameter metadata
    void define() {
        defineParam(myParam, "My Parameter", 1.0f);
    }
    
    // 5. init() - Setup and initialization (optional)
    void init() {
        myLocal = myParam * 2.0f;
    }
    
    // 6. process() - Main kernel logic
    void process() {
        dst() = src() * myLocal;
    }
};
```

## Granularity Options

| Type | Description | Use When |
|------|-------------|----------|
| `eComponentWise` | Process one channel at a time | Working on individual channels |
| `ePixelWise` | Process all channels together | Need access to multiple channels |

## Image Specification

```cpp
Image<ReadSpec, AccessPattern, EdgeMethod> name;
```

### ReadSpec
- `eRead` - Read-only (default)
- `eWrite` - Write access

### AccessPattern
| Pattern | Description | Init Required |
|---------|-------------|---------------|
| `eAccessPoint` | Current position only | No |
| `eAccessRanged1D` | 1D range (line) | Yes - `setAxis()`, `setRange()` |
| `eAccessRanged2D` | 2D range (rectangle) | Yes - `setRange()` |
| `eAccessRandom` | Any pixel | No |

### EdgeMethod
- `eEdgeNone` - Undefined outside (fastest, default)
- `eEdgeClamped` - Repeat edge values
- `eEdgeConstant` - Return zeros outside

## Image Access Syntax

| Access Pattern | Syntax | Example |
|----------------|--------|---------|
| Point | `image()` | `src()` |
| Point + component | `image(c)` | `src(0)` |
| Ranged1D | `image(offset)` | `src(-1)` |
| Ranged1D + component | `image(offset, c)` | `src(-1, 0)` |
| Ranged2D | `image(xOff, yOff)` | `src(-1, 1)` |
| Ranged2D + component | `image(xOff, yOff, c)` | `src(-1, 1, 0)` |
| Random | `image(x, y)` | `src(100, 200)` |
| Random + component | `image(x, y, c)` | `src(100, 200, 0)` |
| Bilinear | `image.bilinear(x, y)` | `src.bilinear(10.5f, 20.7f)` |
| Bilinear + component | `image.bilinear(x, y, c)` | `src.bilinear(10.5f, 20.7f, 0)` |

## Common Functions

### Vector
```cpp
float dot(float3 a, float3 b);
float3 cross(float3 a, float3 b);
float length(float3 a);
float3 normalize(float3 a);
```

### Math
```cpp
// Trig: sin, cos, tan, asin, acos, atan, atan2
// Exponential: exp, log, log2, log10
// Rounding: floor, ceil, round
// Powers: pow, sqrt, rsqrt
// Range: min, max, clamp
```

## Common Patterns

### 3x3 Box Blur (2D Ranged)
```cpp
kernel BoxBlur : ImageComputationKernel<ePixelWise> {
    Image<eRead, eAccessRanged2D, eEdgeClamped> src;
    Image<eWrite> dst;
    
    void init() {
        src.setRange(-1, 1);  // 3x3 neighborhood
    }
    
    void process() {
        float4 sum = float4(0.0f);
        for (int y = -1; y <= 1; y++) {
            for (int x = -1; x <= 1; x++) {
                sum += src(x, y);
            }
        }
        dst() = sum / 9.0f;
    }
};
```

### Invert (Point Access)
```cpp
kernel Invert : ImageComputationKernel<eComponentWise> {
    Image<eRead> src;
    Image<eWrite> dst;
    
    void process() {
        dst() = 1.0f - src();
    }
};
```

### Position-Based Effect
```cpp
kernel PositionEffect : ImageComputationKernel<ePixelWise> {
    Image<eWrite> dst;
    
    void process(int2 pos) {
        float x = (float)pos.x / dst.bounds.width();
        float y = (float)pos.y / dst.bounds.height();
        dst() = float4(x, y, 0.0f, 1.0f);
    }
};
```

## Image Properties Quick Reference

```cpp
image.kMin          // Min component value
image.kMax          // Max component value
image.kWhitePoint   // White point value
image.kComps        // Number of components
image.bounds        // Image bounds (recti)
image.bounds.x1     // Left edge
image.bounds.y1     // Bottom edge
image.bounds.x2     // Right edge
image.bounds.y2     // Top edge
```

## Execution Flow

1. **define()** - Called once at kernel creation
2. **init()** - Called once before processing begins
3. **process()** - Called for every pixel/component in output

## Tips

- Use `eComponentWise` for per-channel effects (faster)
- Use `ePixelWise` when you need multiple channels
- `eEdgeNone` is fastest (no bounds checking)
- Calculate expensive operations in `init()`, not `process()`
- Use `local:` variables to cache calculations from `init()`
- Bilinear interpolation for smooth sub-pixel sampling
