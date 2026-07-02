# BlinkScript Kernel Basics

## Introduction

The Foundry's Blink is a C++-like language designed for Rapid Image Processing. It uses standard C++ syntax with a few keyword changes. At runtime, it uses the LLVM compiler to generate code for specific devices.

### Code Generation Types
- **Standard C++** for CPU
- **SIMD-optimised C++** for CPU (AVX or SSE2)
- **OpenCL** for GPU

Runtime compilation enables:
- Generate code only for specific input/output types needed
- Target hardware available at runtime
- Fast algorithm prototyping
- Code cached on disk for future use

## Kernel Concept

A Blink "kernel" is code that runs at each position in the iteration space. For image processing, the iteration space is usually the bounds of the output image. The kernel runs at every position to produce the output picture.

## Creating a Kernel

A Blink kernel is written like a C++ class, inheriting from `ImageComputationKernel` with `Granularity` as a template parameter:

```cpp
kernel BasicKernel : ImageComputationKernel<Granularity> {
    //Kernel body goes here
};
```

### Required Kernel Components

1. **At least one image specification** - Defines images read from and written to
   - By convention, these are the first members of the kernel

2. **A single process() method** - Called for each point in the iteration space
   - Reads from inputs and writes to outputs

## Kernel Granularity

Kernels iterate in either **componentwise** or **pixelwise** manner:

### eComponentWise
- Kernel executed **once per component** at every point
- Only current component's value accessible in input/output images
- Use for operations that work on individual channels

### ePixelWise
- Kernel executed **once per pixel** at every point
- All component values can be read from and written to
- Use for operations that need access to multiple channels

## Image Specification

Format:
```cpp
Image<ReadSpec, AccessPattern, EdgeMethod> myImage;
```

### ReadSpec
Specifies read/write access:
- **eRead** - Read-only access (default)
- **eWrite** - Write access required

### AccessPattern
Describes how kernel accesses pixels:
- **eAccessPoint** - Access only current position (default)
- **eAccessRanged1D** - One-dimensional range relative to current position
- **eAccessRanged2D** - Two-dimensional range relative to current position
- **eAccessRandom** - Access any pixel in iteration space

### EdgeMethod
Defines behavior when accessing data outside image bounds:

- **eEdgeClamped** - Edge values repeated outside bounds
- **eEdgeConstant** - Zero values returned outside bounds
- **eEdgeNone** - Values undefined outside bounds, no bounds checks (most efficient, default)

## The process() Method

The `process()` method runs at every point in the iteration space. Three possible signatures:

### void process()
```cpp
void process()
```
- Use for kernels with same processing regardless of position
- No position information needed

### void process(int2 pos)
```cpp
void process(int2 pos)
```
- Use when kernel needs to know position in iteration space
- `pos.x` = x coordinate
- `pos.y` = y coordinate

### void process(int3 pos)
```cpp
void process(int3 pos)
```
- **Only available for eComponentWise granularity**
- `(pos.x, pos.y)` = coordinates in iteration space
- `pos.z` = current component index

**Note:** If multiple process() functions defined with different signatures, only the first one is used.

## Basic Kernel Examples

### Example 1: ComponentWise Copy Kernel
```cpp
kernel CopyKernel : ImageComputationKernel<eComponentWise> {
    Image<eRead, eAccessPoint, eEdgeClamped> src;
    Image<eWrite> dst;
    
    void process() {
        dst() = src();
    }
};
```
- Access `src` and `dst` at current position/component using `()` operator

### Example 2: PixelWise Copy Kernel (Simple)
```cpp
kernel CopyKernel : ImageComputationKernel<ePixelWise> {
    Image<eRead, eAccessPoint, eEdgeClamped> src;
    Image<eWrite> dst;
    
    void process() {
        dst() = src();  // Copies all components
    }
};
```
- `src()` returns `SampleType(src)` - a vector of all component values
- Each value is of type `ValueType(src)`

### Example 3: PixelWise Copy Kernel (Per-Component)
```cpp
kernel CopyKernel : ImageComputationKernel<ePixelWise> {
    Image<eRead, eAccessPoint, eEdgeClamped> src;
    Image<eWrite> dst;
    
    void process() {
        for (int component = 0; component < dst.kComps; component++) {
            dst(component) = src(component);
        }
    }
};
```
- Access single component inside pixelwise kernel with `image(component)`
- `dst.kComps` = number of components in dst image

## Quick Reference

**Choose Granularity:**
- `eComponentWise` - Process one channel at a time
- `ePixelWise` - Process all channels together

**Image Specification Template:**
```cpp
Image<ReadSpec, AccessPattern, EdgeMethod> name;
```

**Access Current Pixel:**
- ComponentWise: `image()` returns single value
- PixelWise: `image()` returns vector of all components
- PixelWise single component: `image(component)`
