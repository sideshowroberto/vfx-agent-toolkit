# BlinkScript Advanced Troubleshooting

**Part of:** nuke-blinkscript skill (extended reference)

## Additional Troubleshooting Issues

### Issue 5: Compile Error - "use of undeclared identifier 'setParameterRange'"

**Symptom:** Error when trying to set parameter min/max ranges

**Cause:** `setParameterRange()` does **not exist** in BlinkScript

```cpp
// [FAIL] WRONG - This function doesn't exist!
void define() {
  defineParam(thickness, "Thickness", 2.0f);
  setParameterRange(thickness, 0.5f, 10.0f);  // ERROR!
}

// [OK] CORRECT - Just use defineParam
void define() {
  defineParam(thickness, "Thickness", 7.0f);  // Set good default
}
```

**Note:** Users can always type values beyond slider limits directly into number fields.

### Issue 6: Parameter Controls Don't Work / Colors Don't Change

**Symptom:** Multiple grids using same controls, or controls don't affect output

**Cause:** Parameter name conflicts (multiple params with same display name)

```cpp
// [FAIL] WRONG - Name conflicts
defineParam(colorThirds, "Colour", ...);   // Conflict!
defineParam(colorGolden, "Colour", ...);   // Same name!
defineParam(colorSpiral, "Colour", ...);   // Same name!

// [OK] CORRECT - Unique names with prefixes
defineParam(colorThirds, "Thirds Colour", ...);
defineParam(colorGolden, "Golden Colour", ...);
defineParam(colorSpiral, "Spiral Colour", ...);
```

### Issue 7: 2D Point Not in Correct Position / Disappears When Moved

**Symptom:** float2 point parameter doesn't match visual position in viewer

**Cause:** float2 uses **pixel coordinates**, not normalized (0-1)

```cpp
// [FAIL] WRONG - Treating as normalized
param:
  float2 center;

void define() {
  defineParam(center, "Center", float2(0.5f, 0.5f));  // Normalized?
}

void init() {
  actualX = imgWidth * center.x;   // Multiplying normalized values
}

// [OK] CORRECT - Use pixel coordinates directly
param:
  float2 center;

void define() {
  defineParam(center, "Center", float2(960.0f, 540.0f));  // Pixels!
}

void init() {
  actualX = center.x;  // Already in pixels, use directly
}
```

**Key Learning:** float2 parameters are in **pixel space**, not normalized space!

---

## Best Practices

### 1. Visible Default Values

**Problem:** Default thickness of 2.0 is too thin to see on most displays.

**Solution:** Use visible defaults:
```cpp
defineParam(thickness, "Thickness", 7.0f);      // Lines clearly visible
defineParam(spiralThickness, "Thickness", 15.0f); // Spirals need more
```

**Guidelines:**
- Lines: 5.0 - 10.0
- Spirals/curves: 15.0 - 20.0
- Fine details: 3.0 - 5.0

### 2. Unique Parameter Names

**Always use prefixes** to avoid conflicts when multiple grids/effects use similar parameters:

```cpp
// [OK] GOOD - Unique names
defineParam(colorThirds, "Thirds Colour", ...);
defineParam(thicknessThirds, "Thirds Thickness", ...);
defineParam(colorSpiral, "Spiral Colour", ...);
defineParam(thicknessSpiral, "Spiral Thickness", ...);
```

### 3. Slider Limits Workaround

**BlinkScript doesn't support `setParameterRange()`**, but users can exceed slider limits:

**Tell users:**
> "To use values beyond the slider range (e.g., thickness > 50), click the number field and type the value directly."

### 4. UI Organization with Group Nodes

**BlinkScript's `define()` doesn't support:**
- Divider lines
- Tabs
- Custom layouts

**Solution:** Wrap BlinkScript node in a Nuke **Group node**:
1. Create Group node containing BlinkScript
2. Add User Knobs for organized UI
3. Link knobs to BlinkScript parameters
4. Add dividers, tabs, custom organization
5. Export as ToolSet for sharing

**Benefit:** Professional UI without BlinkScript limitations!

### 5. 2D Point Parameters (float2)

**Always remember:** float2 = **pixel coordinates**, not normalized!

```cpp
// Default to typical image center
defineParam(position, "Position", float2(960.0f, 540.0f));

// Use directly (already pixels)
void init() {
  actualX = position.x;  // No multiplication needed
  actualY = position.y;
}
```

### 6. Sharing BlinkScript Tools

**Two approaches:**

**A. Embedded Kernel (Easiest)**
- Kernel code embedded in .nk file
- Share single file
- No folder setup needed

**B. External Kernel**
- Kernel in separate .blink file
- Users copy to `~/.nuke/blinkscript/`
- Better for versioning/editing

**Recommendation:** Embed for simple sharing, external for team development.
