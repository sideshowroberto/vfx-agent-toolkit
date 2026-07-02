# Property Type Safety - Blueprint Automation

## Current Limitations (MCP C++ Bug)

**❌ CRASH RISK:** The following property types currently cause Blueprint corruption and crashes:

- **FColor:** `LightColor` on light components
- **FLinearColor:** Color-related properties on various components
- **Other StructProperty types:** Untested, may crash

**Root Cause:** MCP C++ code (`UnrealMCPCommonUtils.cpp`) missing StructProperty serialization for color types. Failed property sets corrupt Blueprint → crash on compile.

**Status:** Bug documented in `Session_2025-10-26_BlueprintAutomation_Testing.md`, fix planned.

## Safe Property Types ✅

**These property types work reliably:**

**Scalars (Float, Int):**
- `Intensity` - Light brightness
- `AttenuationRadius` - Light falloff distance
- `Mass` - Physics mass
- `TargetArmLength` - SpringArm distance

**Booleans:**
- `CastShadows` - Shadow casting
- `bGenerateOverlapEvents` - Overlap detection
- `bVisible` - Visibility

**Vectors (FVector):**
- `RelativeLocation` - Position
- `RelativeScale3D` - Scale
- `BoxExtent` - Box collision size

**Rotators (FRotator):**
- `RelativeRotation` - Rotation

**Objects (Asset References):**
- `StaticMesh` - Via `set_static_mesh_properties` tool
- `Material` - Material assignments (untested but likely works)

## Workaround Pattern

**Until FColor/FLinearColor fix is deployed:**

```python
# Phase 1-3: Create Blueprint, add components, set SAFE properties only
create_blueprint(...)
add_component_to_blueprint(...)
set_static_mesh_properties(...)  # ✅ Safe
set_component_property("Intensity", "5000.0")  # ✅ Safe
set_component_property("RelativeLocation", "[0,0,150]")  # ✅ Safe

# SKIP color properties to avoid crash
# set_component_property("LightColor", "...")  # ❌ DON'T DO THIS

# Phase 4: Compile
compile_blueprint(...)  # ✅ No crash (no failed property sets)

# Phase 5: Manual color setting (temporary)
# Open Blueprint in Unreal Editor
# Select Light component
# Manually set Light Color in Details panel
```

## Future: Property Introspection

**Planned Tool:** `get_blueprint_component_properties`

**Purpose:** Query component properties before setting to avoid crashes.

**Usage (when available):**
```python
# Query component to discover properties and types
result = get_blueprint_component_properties(
    blueprint_name="BP_MyActor",
    component_name="Light"  # Optional - omit for all components
)

# Returns property info with safety indicators
{
    "Light": {
        "class": "PointLightComponent",
        "properties": {
            "Intensity": {
                "type": "FloatProperty",
                "value": "5000.0",
                "safe": true
            },
            "LightColor": {
                "type": "StructProperty:FColor",
                "value": "(R=255,G=255,B=255,A=255)",
                "safe": false  # ← Indicates crash risk
            }
        }
    }
}

# Safe automation pattern
props = result["Light"]["properties"]
for prop_name, prop_info in props.items():
    if prop_info["safe"]:
        set_component_property(prop_name, desired_value)
    else:
        print(f"Skipping {prop_name} - type not yet supported")
```

**Status:** C++ implementation in progress. See testing session for details.
