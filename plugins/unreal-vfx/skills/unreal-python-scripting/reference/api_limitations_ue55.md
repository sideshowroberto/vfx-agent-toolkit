# API Limitations - Unreal Engine 5.5 Python

**Document Version:** 1.0.0
**Target:** Unreal Engine 5.5.0
**Last Updated:** 2025-10-25
**Platform:** Windows 11
**Python Version:** 3.11 (UE built-in)

---

## Overview

### Purpose

This document catalogs **methods and features NOT exposed to Python** in Unreal Engine 5.5. Each limitation includes:
- C++ signature (what's missing)
- Why it's needed
- Symptom when missing
- Workaround (if exists)
- Status (will it be fixed?)
- Discovery source

**Update Frequency:** Version-specific. Create new document for each UE version.

---

### Why Limitations Exist

**By Design:**
- Safety: Some methods can crash editor if misused
- Performance: C++ required for low-level operations
- Architecture: Component registration is runtime C++ domain
- Stability: Editor subsystems not fully exposed

**Not Bugs:** These are intentional omissions by Epic Games.

---

### How Limitations Were Discovered

**Sources:**
1. **Session_2025-10-25_ImagePlate.md** - ImagePlate component discovery
2. **Unreal Forums** - Community-reported limitations
3. **Epic Documentation** - Official Python API reference (lists what IS exposed)
4. **Trial-and-Error** - Production workflow testing

**Discovery Process:**
- Attempt C++ pattern in Python
- Encounter AttributeError or TypeError
- Search official docs (confirms not exposed)
- Find workaround (Blueprint, different API)
- Document here

---

## Component Limitations

### 1. register_component()

**C++ Signature:**
```cpp
void UActorComponent::RegisterComponent()
```

**Why Needed:**
- Registers component with actor's component system
- Makes component visible in editor
- Initializes component lifecycle
- Required for component to function

**Symptom When Missing:**
```python
component = unreal.new_object(unreal.ImagePlateComponent)
# Component created but:
# - Not visible in editor
# - Not functional in game
# - Not saved with actor
```

**Workaround:**
- Use Blueprint actor with pre-configured components
- Components in Blueprint are auto-registered at definition time
- Spawn Blueprint instance instead of creating component at runtime

**Example:**
```python
# ❌ DOESN'T WORK
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(...)
component = unreal.new_object(unreal.ImagePlateComponent)
# component.register_component()  # AttributeError: no such method

# ✅ WORKS
bp = unreal.load_class(None, "/Game/BP_WithComponent.BP_WithComponent_C")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
# Component already registered in Blueprint
```

**Status:** No Python solution as of UE 5.5.0. Unlikely to change (design decision).

**Source:** Session_2025-10-25_ImagePlate.md (lines 59-78)

---

### 2. setup_attachment()

**C++ Signature:**
```cpp
void USceneComponent::SetupAttachment(
    USceneComponent* InParent,
    FName InSocketName = NAME_None
)
```

**Why Needed:**
- Attaches component to parent component
- Defines component hierarchy
- Used in constructors to establish relationships
- Called BEFORE RegisterComponent()

**Symptom When Missing:**
```python
camera_component = actor.get_component_by_class(unreal.CineCameraComponent)
image_plate = unreal.new_object(unreal.ImagePlateComponent)
# image_plate.setup_attachment(camera_component)  # AttributeError
# Component created but not attached to hierarchy
```

**Workaround:**
- Define component hierarchy in Blueprint
- Spawn Blueprint instance with hierarchy already established
- Cannot dynamically modify hierarchy at runtime in Python

**Blueprint Pattern:**
```
Blueprint Editor:
1. Add CineCameraComponent (root)
2. Add ImagePlateComponent
3. Right-click ImagePlateComponent → Attach to → CineCameraComponent
4. Save Blueprint

Python:
bp = unreal.load_class(None, "/Game/BP_Camera.BP_Camera_C")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
# Hierarchy already established
```

**Status:** No Python solution as of UE 5.5.0. Use Blueprint-defined hierarchies.

**Source:** Session_2025-10-25_ImagePlate.md (lines 98-110)

---

### 3. attach_to_component()

**C++ Signature:**
```cpp
void USceneComponent::AttachToComponent(
    USceneComponent* Parent,
    const FAttachmentTransformRules& AttachmentRules,
    FName SocketName = NAME_None
)
```

**Why Needed:**
- Runtime attachment (vs setup_attachment at construction)
- Allows dynamic reparenting
- Used for parenting actors/components after spawn

**Symptom When Missing:**
```python
# Try to attach spawned component to existing actor
parent_comp = actor1.root_component
child_comp = actor2.root_component
# child_comp.attach_to_component(parent_comp, ...)  # AttributeError
```

**Workaround:**
- Use Blueprint hierarchy (no runtime reparenting in Python)
- For actor-to-actor attachment: Use `attach_to_actor()` (THIS works)

**Actor Attachment (Works):**
```python
# ✅ Actor-level attachment works
child_actor.attach_to_actor(
    parent_actor,
    unreal.AttachmentRule.SNAP_TO_TARGET,
    ""  # socket name
)
```

**Component Attachment (Doesn't Work):**
```python
# ❌ Component-level attachment doesn't work
# Must be defined in Blueprint
```

**Status:** Actor attachment works. Component attachment: Blueprint only.

**Source:** Session_2025-10-25_ImagePlate.md (lines 98-110)

---

### 4. add_instance_component()

**Expected Behavior:**
- Add component to actor instance at runtime
- Python equivalent of Blueprint "Add Component" button

**Status:** DOESN'T EXIST in UE 5.5

**Attempted Usage:**
```python
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(...)
# actor.add_instance_component(unreal.ImagePlateComponent)  # No such method
# actor.add_component(...)  # Also doesn't exist
```

**Workaround:**
- Modify Blueprint to include component
- Spawn different Blueprint with component already included
- No runtime component addition in Python

**Status:** Not available. Not planned by Epic.

**Source:** Session_2025-10-25_ImagePlate.md (lines 69-78)

---

### 5. rerun_construction_scripts()

**C++ Signature:**
```cpp
void AActor::RerunConstructionScripts()
```

**Why Needed:**
- Re-executes Blueprint construction script
- Updates components based on Blueprint logic
- Useful after changing actor properties

**Symptom When Missing:**
```python
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
actor.set_editor_property('some_variable', new_value)
# actor.rerun_construction_scripts()  # AttributeError
# Construction script doesn't re-run, component state stale
```

**Workaround:**
- Delete and re-spawn actor
- Or: Design Blueprint to not require construction script re-run

**Status:** Not exposed in Python. No current workaround except re-spawn.

**Source:** Session_2025-10-25_ImagePlate.md (line 75)

---

## Material Limitations

### 1. Material Graph Construction

**Category:** MaterialExpression node connections

**What's Limited:**
- Creating MaterialExpression nodes
- Connecting node pins
- Building material graph programmatically
- MaterialFunction creation

**Partially Available:**
```python
# ✅ Can create basic material
material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(...)

# ❌ Cannot build graph
# node1 = unreal.MaterialExpressionTextureSample(...)  # Limited API
# node2 = unreal.MaterialExpressionMultiply(...)
# node1.connect_to(node2)  # No such method
```

**Workaround:**
- Create master material in Unreal Editor
- Use Material Instances in Python
- Override parameters instead of building graph

**Material Instance Pattern (Recommended):**
```python
# Create master in editor with parameters
# M_Master with:
# - PlateTexture (Texture parameter)
# - Opacity (Scalar parameter)

# Python: Create instances
master = unreal.load_asset("/Game/Materials/M_Master")
instance = tools.create_asset(..., unreal.MaterialInstanceConstant, ...)
instance.set_editor_property('parent', master)

# Override parameters
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    instance, 'PlateTexture', texture
)
```

**Status:** Material creation works, graph construction severely limited. Use instances.

**Source:** Session_2025-10-25_ImagePlate.md (lines 176-191), production testing

---

### 2. MaterialExpression Property Access

**Issue:** MaterialExpression properties not fully exposed

**Example:**
```python
# Create texture sample node (limited support)
tex_node = material.Expressions.add(unreal.MaterialExpressionTextureSample)

# ❌ Cannot set properties reliably
# tex_node.Texture = my_texture  # May not work
# tex_node.SamplerType = ...     # May not work
```

**Workaround:**
- Create master material in editor
- All material graph work in editor
- Python only for material instances

**Status:** Extremely limited. Not production-ready for graph construction.

---

## ImagePlate Specific Limitations

### 1. ImagePlateComponent Creation

**Discovery:** ImagePlate is a COMPONENT, not an ACTOR

**Issue:** Cannot fully create and configure ImagePlateComponent at runtime

**What Works:**
```python
# ✅ Can create object
component = unreal.new_object(unreal.ImagePlateComponent)
```

**What Doesn't Work:**
```python
# ❌ Cannot register
component.register_component()  # AttributeError

# ❌ Cannot attach
component.setup_attachment(parent)  # AttributeError

# ❌ Result: Component exists but completely non-functional
```

**Workaround:**
- Create Blueprint with CineCameraActor base
- Add ImagePlateComponent in Blueprint editor
- Spawn Blueprint instance in Python
- Component pre-registered and functional

**Blueprint Pattern:**
```
Blueprint: BP_CameraWithPlate (based on CineCameraActor)
Components:
  - CineCameraComponent (default root)
  - ImagePlateComponent (added, attached to camera)

Python:
bp = unreal.load_class(None, "/Game/BP_CameraWithPlate.BP_CameraWithPlate_C")
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
image_plate = camera.get_components_by_class(unreal.ImagePlateComponent)[0]
# Component fully functional, ready to configure
```

**Status:** Blueprint-based approach is production-ready. Runtime creation impossible.

**Source:** Session_2025-10-25_ImagePlate.md (complete session)

---

### 2. ImagePlateFrustumComponent Auto-Creation

**Behavior:** ImagePlateFrustumComponent auto-created by ImagePlateComponent

**Issue:** Cannot control this creation in Python

**What Happens:**
```python
# When ImagePlate added in Blueprint:
# - ImagePlateComponent created
# - ImagePlateFrustumComponent auto-created (editor visualization)
# - Frustum component not exposed for configuration

# In Python:
image_plate = actor.get_components_by_class(unreal.ImagePlateComponent)[0]
frustum = actor.get_components_by_class(unreal.ImagePlateFrustumComponent)[0]
# frustum exists but minimal configuration available
```

**Status:** Auto-creation works. No configuration needed (editor-only visualization).

**Source:** Session_2025-10-25_ImagePlate.md (lines 375-390)

---

## Editor Subsystem Limitations

### 1. Custom Component Registration

**Issue:** Cannot register custom C++ components in Python

**Use Case:** Plugin defines custom component, want to add to actor in Python

**Status:** Must use Blueprint. Python cannot register custom types.

---

### 2. Low-Level Rendering Setup

**Category:** Rendering pipeline configuration

**Limited Areas:**
- Custom render targets
- Post-process material injection
- Custom mesh rendering
- SceneCapture configuration (partial)

**Workaround:** Use Blueprint or C++ plugin for rendering customization.

---

### 3. Plugin Module Initialization

**Issue:** Cannot initialize plugin modules from Python

**Example:**
```python
# ❌ Cannot enable plugins programmatically
# unreal.PluginManager.enable_plugin("ImagePlate")  # No such API
```

**Workaround:**
- Enable plugins manually in editor
- Or: Project settings → Plugins → Enable by default
- Python assumes plugins already enabled

**Status:** No Python API for plugin management.

---

## Recommended Workarounds by Category

### Component Hierarchies

**Problem:** Cannot create/attach components at runtime

**Solution:**
1. Create Blueprint with desired component hierarchy
2. Spawn Blueprint instance in Python
3. Access components via `get_components_by_class()`
4. Configure component properties with `set_editor_property()`

**Pattern:**
```python
# Blueprint: Define hierarchy
# Python: Spawn + configure
bp = unreal.load_class(None, "/Game/BP_Actor.BP_Actor_C")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp, ...)
component = actor.get_components_by_class(ComponentClass)[0]
component.set_editor_property('property', value)
```

---

### Materials

**Problem:** Cannot build material graph in Python

**Solution:**
1. Create master material in editor with parameters
2. Create material instances in Python
3. Override parameters with MaterialEditingLibrary

**Pattern:**
```python
# Editor: Create M_Master with parameters
# Python: Create instances
master = unreal.load_asset("/Game/Materials/M_Master")
instance = tools.create_asset(..., unreal.MaterialInstanceConstant, ...)
instance.set_editor_property('parent', master)
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
    instance, 'ParamName', texture
)
```

---

### Asset Creation

**Works Well:**
- Materials (basic)
- Material Instances
- Textures
- StaticMeshes (limited)
- Blueprints (structure only, not graph)

**Use:**
- `AssetToolsHelpers.get_asset_tools()`
- `create_asset()` method
- Factory classes (MaterialInstanceConstantFactoryNew, etc.)

---

## C++ Only Patterns

### Complex Material Graph Construction

**Status:** C++ only
**Reason:** MaterialExpression API not fully exposed
**Alternative:** Material instances

---

### Custom Component Registration

**Status:** C++ only
**Reason:** Component system is C++ runtime domain
**Alternative:** Blueprint-based components

---

### Low-Level Rendering Setup

**Status:** C++ only
**Reason:** Safety and performance
**Alternative:** Use existing rendering features via Blueprint/Python properties

---

### Plugin Module Initialization

**Status:** C++ only
**Reason:** Plugin system is editor-level C++
**Alternative:** Enable plugins manually or in project settings

---

## Testing & Validation

### How to Check if Method Exposed

**Method 1: dir() listing**
```python
import unreal
component = unreal.new_object(unreal.StaticMeshComponent)
methods = dir(component)
if 'register_component' in methods:
    print("Exposed")
else:
    print("Not exposed")  # This is the result
```

**Method 2: hasattr() check**
```python
if hasattr(component, 'setup_attachment'):
    component.setup_attachment(parent)
else:
    print("Method not available")
```

**Method 3: Try-Except**
```python
try:
    component.register_component()
except AttributeError as e:
    print(f"Not exposed: {e}")
```

---

### Common AttributeError Messages

**"AttributeError: 'ImagePlateComponent' object has no attribute 'register_component'"**
- Meaning: Method not exposed to Python
- Solution: Use Blueprint workaround

**"TypeError: 'NoneType' object is not callable"**
- Meaning: Method returned None (may not be exposed)
- Solution: Check if method exists before calling

**"AttributeError: property not found"**
- Meaning: Property name wrong or not exposed
- Solution: Use `dir(object)` to list available properties

---

## Version-Specific Notes

### Unreal Engine 5.5.0

**Tested:** 2025-10-25
**Platform:** Windows 11
**Python:** 3.11 (built-in)

**Known Working:**
- Blueprint spawning
- Material instance creation
- Component property access (exposed properties)
- Actor spawning/deletion
- Asset loading
- EditorLevelLibrary operations

**Known Broken:**
- Component registration
- Component attachment
- Material graph construction
- Plugin module management

---

### Future Unreal Versions

**Check for Updates:**
- Create `api_limitations_ue56.md` when UE 5.6 releases
- Test each limitation again (may be fixed)
- Update workarounds if new APIs exposed

**Unlikely to Change:**
- Component registration (design decision)
- Material graph construction (too complex for Python)

**Possible Improvements:**
- More component properties exposed
- Better material instance API
- Sequencer Python API expansion

---

## Discovery Protocol

### When You Find a New Limitation

**Document:**
1. Method name and signature (from C++ docs)
2. Why it's needed
3. Symptom when missing
4. Workaround (if found)
5. Source (session, forum post, etc.)

**Add to This Document:**
- Categorize appropriately
- Include code examples
- Test workaround before documenting
- Note UE version

**Update:**
- SKILL.md if common pattern
- This doc for detailed analysis
- Session logs for context

---

## References

### Session Documentation
- **Session_2025-10-25_ImagePlate.md** - Primary source for component limitations

### Official Documentation
- **Unreal Engine Python API Reference** - Lists what IS exposed (by omission, what isn't)
- **Epic Games Forums** - Community-reported limitations
- **Unreal Engine Source Code** - C++ signatures for missing methods

### Related Skills
- **unreal-python-scripting/SKILL.md** - Workflow patterns
- **unreal-python-scripting/reference/blueprint_patterns.md** - Blueprint workarounds
- **unreal-python-scripting/reference/component_patterns.md** - Component access patterns

---

**Document Status:** Production-ready
**Coverage:** Component, Material, Editor, ImagePlate limitations
**Workarounds:** Documented for all critical limitations
**Tested:** UE 5.5.0, Windows 11, 2025-10-25

---

*API Limitations Database - Unreal Engine 5.5 Python*
*Last Updated: 2025-10-25*
