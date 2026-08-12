# PCG Python API Limitations

**Version:** 1.5.0
**Last Updated:** 2025-11-17
**UE Version:** 5.5 (applies to 5.4+)
**Status:** Confirmed limitations

Known constraints and workarounds for PCG Python API in Unreal Engine 5.4+.

---

## Table of Contents

1. [Static Mesh Spawner: Read-Only Mesh Entries](#static-mesh-spawner-read-only-mesh-entries)
2. [Get Landscape Data: No Direct Configuration](#get-landscape-data-no-direct-configuration)
3. [Workarounds and Hybrid Workflows](#workarounds-and-hybrid-workflows)

---

## Static Mesh Spawner: Read-Only Mesh Entries

### Problem

**CONFIRMED:** Mesh entries CANNOT be configured via Python API in UE 5.4+

### What Was Removed in UE 5.4

**Removed Classes:**
- [FAIL] `PCGStaticMeshSpawnerEntry` - Completely removed
- [FAIL] `meshes` property on `PCGStaticMeshSpawnerSettings` - Completely removed

**Example of Removed API:**
```python
# [FAIL] THIS DOESN'T WORK IN UE 5.4+

# Old pattern (pre-5.4):
mesh_entry = unreal.PCGStaticMeshSpawnerEntry()  # Class doesn't exist!
mesh_entry.mesh = unreal.load_asset('/Engine/BasicShapes/Cube')
mesh_entry.weight = 1.0

spawner_settings.meshes = [mesh_entry]  # Property doesn't exist!
```

### Current API State (UE 5.4+)

**What's Available:**
```python
spawner_settings.mesh_selector_type          # Read-Write [OK]
spawner_settings.mesh_selector_parameters    # Read-Only [FAIL]
```

**Why It Doesn't Work:**
- Epic migrated to `mesh_selector_parameters` architecture
- Mesh entries live inside `mesh_selector_parameters`
- `mesh_selector_parameters` is read-only in Python
- No public API to modify mesh entries programmatically

**Evidence:**
```python
# You can read but not write
import unreal

graph = unreal.load_asset('/Game/PCG/MyGraph')
spawner_settings = graph.nodes[4].get_settings()

# Read mesh selector type
print(spawner_settings.mesh_selector_type)  # Works [OK]

# Read mesh selector parameters
print(spawner_settings.mesh_selector_parameters)  # Works [OK]

# Try to modify mesh selector parameters
spawner_settings.mesh_selector_parameters = new_value  # Fails! [FAIL]
# AttributeError: attribute 'mesh_selector_parameters' of 'PCGStaticMeshSpawnerSettings' object is not writable
```

---

## Required Workflow: Hybrid Python + UI

Since Python API can't configure mesh entries, use this two-phase workflow:

### Phase 1: Python (Automated)

**What Python CAN do:**
```python
import unreal

# [OK] Create graph structure
graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_MyGraph",
    package_path="/Game/PCG",
    asset_class=unreal.PCGGraph,
    factory=unreal.PCGGraphFactory()
)

# [OK] Add nodes
get_landscape, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
surface_sampler, _ = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
transform, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
mesh_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

# [OK] Position nodes
get_landscape.set_node_position(-600, 0)
surface_sampler.set_node_position(-300, 0)
transform.set_node_position(0, 0)
mesh_spawner.set_node_position(300, 0)

# [OK] Connect nodes
graph.add_edge(get_landscape, unreal.Name("Out"), surface_sampler, unreal.Name("Surface"))
graph.add_edge(surface_sampler, unreal.Name("Out"), transform, unreal.Name("In"))
graph.add_edge(transform, unreal.Name("Out"), mesh_spawner, unreal.Name("In"))

# [OK] Configure Transform Points (scale/rotation randomization)
transform_settings = transform.get_settings()
transform_settings.rotation_min = unreal.Rotator(0, 0, 0)
transform_settings.rotation_max = unreal.Rotator(0, 360, 0)
transform_settings.scale_min = unreal.Vector(0.8, 0.8, 0.8)
transform_settings.scale_max = unreal.Vector(1.2, 1.2, 1.2)
```

### Phase 2: UI (Manual - Required)

**What REQUIRES UI configuration:**
```
1. Open PCG graph in Unreal Editor
2. Click on Surface Sampler node
3. Details panel -> Points Per Squared Meter -> Set density (e.g., 1.0)
4. Click on Static Mesh Spawner node
5. Details panel -> Mesh Selector -> Mesh Entries -> Click "+"
6. Select mesh from asset browser (e.g., /Engine/BasicShapes/Cube)
7. Set weight (e.g., 1.0)
8. Add more meshes if desired
9. Save graph
```

**UI Configuration Screenshot Location:**
- Mesh Spawner -> Details -> Mesh Selector -> Mesh Entries array

---

## Workarounds Attempted (All Failed)

### Attempt 1: Create Mesh Entries Programmatically
```python
# [FAIL] FAILED
mesh_entry = unreal.PCGStaticMeshSpawnerEntry()
# AttributeError: module 'unreal' has no attribute 'PCGStaticMeshSpawnerEntry'
```
**Reason:** Class completely removed in UE 5.4+

### Attempt 2: Set meshes Property
```python
# [FAIL] FAILED
spawner_settings.meshes = [...]
# AttributeError: 'PCGStaticMeshSpawnerSettings' object has no attribute 'meshes'
```
**Reason:** Property completely removed in UE 5.4+

### Attempt 3: Modify mesh_selector_parameters
```python
# [FAIL] FAILED
spawner_settings.mesh_selector_parameters = new_params
# AttributeError: attribute 'mesh_selector_parameters' of 'PCGStaticMeshSpawnerSettings' object is not writable
```
**Reason:** Property is read-only in Python API

### Attempt 4: Use Deprecated API
```python
# [FAIL] FAILED
spawner_settings.set_editor_property('meshes', [...])
# RuntimeError: Property 'meshes' not found
```
**Reason:** Deprecated API completely removed, not just hidden

### Attempt 5: Direct Mesh Assignment
```python
# [FAIL] FAILED
mesh = unreal.load_asset('/Engine/BasicShapes/Cube')
spawner_settings.mesh = mesh
# AttributeError: 'PCGStaticMeshSpawnerSettings' object has no attribute 'mesh'
```
**Reason:** No direct mesh property exists

---

## Get Landscape Data: No Direct Configuration

### Problem

While `PCGGetLandscapeSettings` node can be created via Python, some configuration is limited.

### What Works
```python
# [OK] Create node
get_landscape, settings = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)

# [OK] Basic configuration works
settings.set_editor_property('get_height', True)
settings.set_editor_property('get_layer_weights', False)
```

### What's Limited
```python
# [WARN] May not stick - requires verification
# Layer weight configuration often needs UI
settings.set_editor_property('landscape_layer', "MyLayer")

# [WARN] Verify this property stuck
graph = unreal.load_asset('/Game/PCG/MyGraph')
read_back = graph.nodes[0].get_settings().get_editor_property('landscape_layer')
print(f"Verified: {read_back}")
```

### Workaround

For landscape layer configuration:
1. Create node via Python
2. Configure basic settings via Python
3. Open in UI to configure specific landscape layers
4. Verify in UI that settings stuck

**See Also:** [property_verification.md](property_verification.md)

---

## Workarounds and Hybrid Workflows

### General Pattern

**For Any Read-Only Property:**

1. **Identify what's automatable** (graph structure, basic settings)
2. **Automate via Python** (create nodes, connect, position)
3. **List manual steps** (mesh entries, specific properties)
4. **Document UI workflow** (exact steps to configure manually)
5. **Verify in UI** (confirm Python settings stuck)

### Benefits of Hybrid Approach

**Python Automation:**
- Graph structure creation
- Node positioning and layout
- Connections between nodes
- Basic numeric properties
- Repeatable workflows

**UI Configuration:**
- Mesh spawner meshes
- Complex nested properties
- Visual verification
- Testing and iteration

**Combined:**
- 80% automation (structure)
- 20% manual (content)
- Faster than pure UI
- More reliable than guessing API

---

## Validation Sources

**Tested:** Unreal Engine 5.5 (applies to 5.4+)

**Confirmed via:**
1. Direct API testing (all attempts failed)
2. Context7 API documentation (confirms read-only status)
3. Epic Developer Community forums (community confirms same limitation)
4. YouTube tutorials (recommend hybrid workflow)

**Epic's Reasoning:**
- Architecture change for better extensibility
- Mesh selector system more flexible than direct mesh array
- Python API access planned for future release (no ETA)

---

## Future API Improvements (Wishlist)

**What Would Help:**
```python
# Proposed API (doesn't exist yet)
mesh_entry = spawner_settings.add_mesh_entry()
mesh_entry.set_mesh('/Engine/BasicShapes/Cube')
mesh_entry.set_weight(1.0)

# Or
spawner_settings.configure_mesh_entries([
    {'mesh': '/Engine/BasicShapes/Cube', 'weight': 1.0},
    {'mesh': '/Engine/BasicShapes/Sphere', 'weight': 0.5}
])
```

**Status:** Feature request submitted to Epic (no response yet)

---

## Summary

**What Python CAN'T Do:**
- [FAIL] Configure mesh spawner mesh entries
- [FAIL] Modify mesh_selector_parameters
- [FAIL] Set specific landscape layers (unreliable)

**What Python CAN Do:**
- [OK] Create complete graph structure
- [OK] Add all node types
- [OK] Connect nodes
- [OK] Position nodes
- [OK] Configure basic numeric properties
- [OK] Configure Transform Points (scale/rotation)

**Required Hybrid Workflow:**
- Python: Automate graph structure (80%)
- UI: Configure meshes and complex properties (20%)

**Bottom Line:** PCG automation via Python is 80% possible. The remaining 20% (mesh configuration) requires manual UI steps in UE 5.4+.

---

**See Also:**
- [property_verification.md](property_verification.md) - Verification workflow
- [workflows.md](workflows.md) - Complete hybrid workflow examples
- [landscape_scatter_workflow.md](landscape_scatter_workflow.md) - Step-by-step with UI steps

---

**End of API Limitations Reference**
