# BlinkScript Built-in Functions

## Vector Functions

Available vector types: `int1`, `int2`, `int3`, `int4`, `float1`, `float2`, `float3`, `float4`

```cpp
scalar dot(vec a, vec b);
// Returns dot product of vector a with vector b

vec cross(vec a, vec b);
// Returns cross product of vector a with vector b

scalar length(vec a);
// Returns the length of vector a

vec normalize(vec a);
// Returns vector a divided by its length
```

**Note:** `scalar` is `int` for int vectors, `float` for float vectors.

## Math Functions

Available for all scalar and vector types.

### Trigonometric Functions

```cpp
type sin(type a);
type cos(type a);
type tan(type a);
type asin(type a);
type acos(type a);
type atan(type a);
type atan2(type a, type b);
```

### Logarithmic and Exponential Functions

```cpp
type exp(type a);      // e^a
type log(type a);      // Natural logarithm
type log2(type a);     // Base-2 logarithm
type log10(type a);    // Base-10 logarithm
```

### Rounding Functions

```cpp
type floor(type a);
type ceil(type a);
int_type round(type a);      // Rounds to nearest integer
```

### Powers and Roots

```cpp
type pow(type a, type b);    // a^b
type sqrt(type a);           // Square root
type rsqrt(type a);          // 1 / sqrt(a)
```

### Absolute Values

```cpp
type fabs(type a);           // Floating-point absolute
int_type abs(int_type a);    // Integer absolute
```

### Min/Max/Clamp

```cpp
type min(type a, type b);
type max(type a, type b);
type clamp(type a, type min, type max);  // Clamp a between min and max
```

### Integer and Fractional Parts

```cpp
type fmod(type a, type b);   // Floating-point modulo
type modf(type a, type *b);  // Split into integer and fractional parts
```

### Sign and Reciprocal

```cpp
type sign(type a);           // Returns -1, 0, or 1
type rcp(type a);            // Reciprocal: 1/a
```

## Atomic Functions

**For integers only.** Thread-safe operations for parallel processing.

```cpp
void atomicAdd(int_type* ptr, int val);
// Atomically increment value at ptr by val

void atomicInc(int_type* ptr);
// Atomically increment value at ptr by 1
```

**Use case:** When multiple threads might write to same memory location.

## Statistical Functions

```cpp
scalar median(scalar data[], int size);
// Finds median value in array of length size
```

**Example:**
```cpp
float values[9];
// Fill values array from 3x3 neighborhood
float medianValue = median(values, 9);
```

## Rectangle Functions

Available on `recti` and `rectf` types.

### Constructors

```cpp
rect();                                      // Uninitialized
rect(scalar x1, scalar y1, scalar x2, scalar y2);  // Bottom-left to top-right
```

### Bounds Functions

```cpp
rect grow(scalar x, scalar y);
// Grow bounds by x horizontally and y vertically

bool inside(scalar x, scalar y);
// Check if position (x, y) is inside rectangle

bool inside(vec v);
// Check if position represented by vector v is inside
```

### Size Functions

```cpp
scalar width();      // Return width of rectangle
scalar height();     // Return height of rectangle
vec size();          // Return vector(width, height)
```

## Quick Reference by Category

**Vector Math:**
- `dot()`, `cross()`, `length()`, `normalize()`

**Trigonometry:**
- `sin()`, `cos()`, `tan()`, `asin()`, `acos()`, `atan()`, `atan2()`

**Logarithms:**
- `exp()`, `log()`, `log2()`, `log10()`

**Rounding:**
- `floor()`, `ceil()`, `round()`

**Roots:**
- `sqrt()`, `rsqrt()`, `pow()`

**Range:**
- `min()`, `max()`, `clamp()`

**Other:**
- `abs()`, `fabs()`, `sign()`, `rcp()`, `fmod()`, `modf()`

**Specialized:**
- `atomicAdd()`, `atomicInc()` - Thread-safe
- `median()` - Statistical
- Rectangle functions - Bounds and size calculations
