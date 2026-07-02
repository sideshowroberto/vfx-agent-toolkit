# BlinkScript Kernel Variables

## Variable Visibility

Kernel variables have two visibility levels:

### param
- Similar to **public** member variables in C++
- Values accessible from **outside the kernel**
- Used for user-controllable parameters
- Exposed in BlinkScript node UI

### local
- Equivalent to **private** member variables
- Used and accessed **only within the kernel**
- For internal calculations and caching

## Variable Declaration

Both types declared in blocks with same visibility:

```cpp
class MyKernel : public Kernel<eComponentWise> {
    Image<eWrite> dst;
    
    param:
        float myParameter1;
        int myParameter2;
    
    local:
        int myVariable1;
        float myVariable2;
    
    void process() {
        dst() = (float)(myParameter2 * myVariable1) + 
                myParameter2 * myVariable2;
    }
};
```

## Variable Types

### Standard C++ Types
- `float`, `int`, `bool`
- Arrays: `float[]`, `int[]`, `bool[]`

### Vector Types
- `int1`, `int2`, `int3`, `int4`
- `float1`, `float2`, `float3`, `float4`

**Component Access:**
```cpp
float3 vec;
float x = vec.x;  // First component
float y = vec.y;  // Second component
float z = vec.z;  // Third component
float w = vec.w;  // Fourth component (for vec4)
```

### Rectangle Types

**recti** - Integer coordinates
**rectf** - Floating-point coordinates

```cpp
recti myRect(int x1, int y1, int x2, int y2);
// Bottom left: (x1, y1)
// Top right: (x2, y2)

// Access coordinates:
int left = myRect.x1;
int bottom = myRect.y1;
int right = myRect.x2;
int top = myRect.y2;
```

## The define() Method

Provides metadata about kernel parameters. Should **only** contain `defineParam()` calls.

### defineParam() Syntax

```cpp
defineParam(paramName, "externalParamName", defaultValue);
```

### Example

```cpp
kernel MyKernel : ImageComputationKernel<ePixelWise> {
    param:
        float size;
        int iterations;
        bool enabled;
    
    void define() {
        defineParam(size, "Radius", 10.0f);
        defineParam(iterations, "Iterations", 5);
        defineParam(enabled, "Enable Effect", true);
    }
    
    // ... rest of kernel
};
```

**When called:** Once when kernel is first created.

**Purpose:**
- Set external parameter names (shown in UI)
- Provide default values
- Define parameter metadata

## Image Properties

Available in both `init()` and `process()` functions:

```cpp
image.kMin          // Minimum possible component value
image.kMax          // Maximum possible component value
image.kWhitePoint   // White point (e.g., 1.0 for float images)
image.kComps        // Number of components
image.kClamps       // Whether data should be clamped
image.bounds        // Image bounds (recti)
image.ValueType     // Component data type
image.SampleType    // Pixel data type (vector of ValueType)
```

### Accessing Bounds

```cpp
int width = image.bounds.x2 - image.bounds.x1;
int height = image.bounds.y2 - image.bounds.y1;
int left = image.bounds.x1;
int bottom = image.bounds.y1;
```

## Quick Reference

**Variable Visibility:**
- `param:` - Public, UI-exposed
- `local:` - Private, internal only

**Vector Component Access:**
- `.x`, `.y`, `.z`, `.w`

**Rectangle Access:**
- `.x1`, `.y1` (bottom-left)
- `.x2`, `.y2` (top-right)

**define() Function:**
- Called once at kernel creation
- Use `defineParam()` to set names and defaults
