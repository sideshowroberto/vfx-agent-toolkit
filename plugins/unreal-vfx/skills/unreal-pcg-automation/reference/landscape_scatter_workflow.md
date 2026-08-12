# Landscape Scatter Workflow (UE 5.4+)

**Last Updated:** 2025-11-17
**Unreal Version:** 5.4+
**Workflow Type:** Hybrid Python + UI
**Status:** Production-ready

---

## Overview

Complete workflow for creating landscape scatter PCG graphs using **UE 5.4+ patterns** with Get Landscape Data node.

**Graph Structure:**
```
Get Landscape Data -> Surface Sampler -> Transform Points -> Static Mesh Spawner -> Output
```

**Workflow Phases:**
1. [OK] **Python Phase:** Graph creation, node connections, Transform configuration
2. [FAIL] **UI Phase:** Surface Sampler density, Mesh Spawner entries (required)

---

## Python Phase: Automated Graph Creation

### Phase 1: Create Graph + Add Nodes

```python
import unreal

# Create new PCG graph asset
graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_LandscapeScatter",
    package_path="/Game/PCG",
    asset_class=unreal.PCGGraph,
    factory=unreal.PCGGraphFactory()
)

# Add nodes (UE 5.4+ pattern with Get Landscape Data)
get_landscape, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
surface_sampler, _ = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
transform_points, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
mesh_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

# Position nodes for readability
get_landscape.set_node_position(-600, 0)
surface_sampler.set_node_position(-300, 0)
transform_points.set_node_position(0, 0)
mesh_spawner.set_node_position(300, 0)

# Save asset
unreal.EditorAssetLibrary.save_loaded_asset(graph)
print("Phase 1 complete: Graph created with 4 nodes")
```

**Output:** Graph created with positioned nodes (not yet connected)

---

### Phase 2: Connect Nodes (Separate Script - Silent Execution)

**CRITICAL:** Run this as a separate script to avoid Silent Execution timeout!

```python
import unreal

# Load graph
g = unreal.load_asset('/Game/PCG/PCG_LandscapeScatter')
o = g.get_output_node()
n = g.nodes

# Connect nodes with unreal.Name() - UE 5.4+ pin names
g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Surface"))
g.add_edge(n[1], unreal.Name("Out"), n[2], unreal.Name("In"))
g.add_edge(n[2], unreal.Name("Out"), n[3], unreal.Name("In"))
g.add_edge(n[3], unreal.Name("Out"), o, unreal.Name("Out"))

# NO CODE AFTER THIS - Silent Execution pattern
```

**Why separate script:** `add_edge()` triggers async graph validation that blocks subsequent Python access.

**Output:** All nodes connected (no print output = success)

---

### Phase 3: Configure Transform Points

```python
import unreal

# Load graph
g = unreal.load_asset('/Game/PCG/PCG_LandscapeScatter')
transform_settings = g.nodes[2].get_settings()

# Scale randomization (0.18 to 1.55 for high variation)
transform_settings.set_editor_property('scale_min', unreal.Vector(0.18, 0.18, 0.18))
transform_settings.set_editor_property('scale_max', unreal.Vector(1.55, 1.55, 1.55))

# Random Z rotation (0-360 deg for natural scatter)
# CRITICAL: Use Rotator not Vector!
transform_settings.set_editor_property('rotation_min', unreal.Rotator(0, 0, 0))
transform_settings.set_editor_property('rotation_max', unreal.Rotator(0, 0, 360))

# Save changes
unreal.EditorAssetLibrary.save_loaded_asset(g)
print("Phase 3 complete: Transform Points configured")
```

**Common Gotcha:** `rotation_max` requires `unreal.Rotator()` not `unreal.Vector()` or you'll get TypeError!

---

## UI Phase: Manual Configuration (Required)

### Step 1: Open Graph in Unreal Editor

1. Navigate to `/Game/PCG/` in Content Browser
2. Double-click `PCG_LandscapeScatter` to open PCG Graph Editor
3. Verify all nodes are connected (green lines between nodes)

---

### Step 2: Configure Surface Sampler

**Node:** Surface Sampler
**Location:** Second node from left

**Settings to Configure:**

1. **Points Per Squared Meter:**
   - Sparse scatter: `0.1 - 0.5`
   - Medium density: `1.0 - 2.0`
   - Dense scatter: `5.0+`

2. **Point Steepness (optional):**
   - Default: `0.5`
   - Flat surfaces only: `0.0 - 0.3`
   - Slopes allowed: `0.5 - 0.9`

**Why UI required:** These settings work in Python too, but mesh spawner requires UI anyway, so batch all UI configuration together.

---

### Step 3: Configure Static Mesh Spawner (REQUIRED - No Python API)

**Node:** Static Mesh Spawner
**Location:** Fourth node from left

**CRITICAL:** This step CANNOT be done via Python API (see Python API Limitations section in SKILL.md)

**Configuration Steps:**

1. Select Static Mesh Spawner node
2. In Details panel, find **Mesh Entries** section
3. Click **"+"** button to add new mesh entry
4. Configure entry:
   - **Mesh:** Click dropdown -> Navigate to `/Engine/BasicShapes/Cube` (or your mesh)
   - **Weight:** `100` (or distribute weights across multiple meshes)
5. (Optional) Add more mesh entries for variety

**Multiple Meshes Example:**
- Entry 1: Rock mesh, Weight: 60
- Entry 2: Boulder mesh, Weight: 30
- Entry 3: Pebble mesh, Weight: 10

**Result:** Random selection weighted by values (60% rocks, 30% boulders, 10% pebbles)

---

### Step 4: Attach to PCG Volume

**Option A: Drag and Drop**
1. Drag `PCG_LandscapeScatter` from Content Browser
2. Drop onto PCG Volume in viewport
3. Graph auto-assigns to volume

**Option B: Manual Assignment**
1. Select PCG Volume in viewport
2. Details panel -> PCG Component section
3. **Graph** property -> Select `PCG_LandscapeScatter`

---

### Step 5: Generate!

1. Select PCG Volume in viewport
2. Details panel -> PCG Component section
3. Click **"Generate"** button
4. Wait for generation to complete
5. Verify meshes scattered on landscape

**Troubleshooting:** If no meshes appear, see Troubleshooting section below.

---

## Configuration Value Recommendations

### Surface Sampler

| Use Case | Points Per Sq Meter | Point Steepness |
|----------|---------------------|-----------------|
| Sparse rocks | 0.1 - 0.3 | 0.5 |
| Medium vegetation | 1.0 - 2.0 | 0.7 |
| Dense grass | 5.0 - 10.0 | 0.9 |
| Flat areas only | Any | 0.0 - 0.3 |

### Transform Points

| Property | Realistic Variation | High Variation | Uniform |
|----------|---------------------|----------------|---------|
| Scale Min | (0.8, 0.8, 0.8) | (0.18, 0.18, 0.18) | (1.0, 1.0, 1.0) |
| Scale Max | (1.2, 1.2, 1.2) | (1.55, 1.55, 1.55) | (1.0, 1.0, 1.0) |
| Rotation Min | (0, 0, 0) | (0, 0, 0) | (0, 0, 0) |
| Rotation Max | (0, 0, 360) | (0, 0, 360) | (0, 0, 0) |

**Note:** Rotation is in degrees. Z-axis rotation (Yaw) creates natural randomness for ground scatter.

---

## Optional: Density Filter

Add between Surface Sampler and Transform Points for controlled distribution:

```python
# In Phase 1, after creating surface_sampler:
density_filter, filter_settings = graph.add_node_of_type(unreal.PCGDensityFilterSettings)
density_filter.set_node_position(-150, 0)

# Configure in separate script:
filter_settings.set_editor_property('lower_bound', 0.5)  # Remove 50% darkest
filter_settings.set_editor_property('upper_bound', 1.0)  # Keep all bright areas
```

**When to use:** Control scatter based on landscape paint layers or density masks.

---

## Troubleshooting

### No Meshes Appear After Generate

**Possible Causes:**

1. **No mesh entries configured**
   - Solution: Check Static Mesh Spawner -> Mesh Entries -> Add at least one mesh

2. **Points Per Squared Meter too low**
   - Solution: Increase to 0.5+ in Surface Sampler settings

3. **PCG Volume not over landscape**
   - Solution: Move PCG Volume to overlap landscape terrain

4. **Debug visualization disabled**
   - Solution: PCG Volume -> Details -> Show Debug -> Enable

5. **Transform offset pushing meshes underground**
   - Solution: Check Transform Points offset values (should be near zero or small positive Z)

---

### TypeError: Cannot nativize 'Vector' as 'Rotator'

**Cause:** Using `unreal.Vector()` for rotation properties

**Fix:**
```python
# WRONG
transform_settings.set_editor_property('rotation_max', unreal.Vector(0, 0, 360))

# CORRECT
transform_settings.set_editor_property('rotation_max', unreal.Rotator(0, 0, 360))
```

---

### LogPCG: Error: "does not have the X label"

**Cause:** Wrong pin name used in connection

**Fix:** Run pin discovery to find correct names:
```python
import unreal
g = unreal.load_asset('/Game/PCG/PCG_LandscapeScatter')

# Check Unreal Output Log after running this:
for pin in g.nodes[0].output_pins:
    print(f"Output: {pin.properties.label}")
```

**Then check log file:**
```bash
# Find latest log
ls -t "<workspace>/UnrealEngine/MCPGameProject/Saved/Logs"/*.log | head -1

# Read output
tail -50 <latest_log> | grep "LogPython:"
```

---

### Connection Script Times Out

**Cause:** Code after `add_edge()` calls (Silent Execution issue)

**Fix:** Ensure connection script ends immediately after last `add_edge()`:
```python
# Phase 2 should end like this:
g.add_edge(n[3], unreal.Name("Out"), o, unreal.Name("Out"))
# NO print(), NO save(), NO verification - script ends here
```

---

## Alternative: Surface Sampler Auto-Detection

Surface Sampler can work **without** explicit landscape connection when PCG Volume is over terrain:

**Simplified Pattern:**
```python
# Skip Get Landscape Data node entirely
surface_sampler, _ = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
transform_points, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
mesh_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

# Connect: Sampler -> Transform -> Spawner -> Output
# Surface Sampler auto-detects landscape under PCG Volume
```

**When to use:** Simple scatter on default landscape
**When NOT to use:** Custom bounds, specific actors, advanced landscape control (use Get Landscape Data)

---

## Complete All-in-One Script (Phases 1-3)

**Warning:** May timeout due to Silent Execution. Prefer separate scripts for production.

```python
import unreal

# Phase 1: Create + Position
graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_LandscapeScatter_Complete",
    package_path="/Game/PCG",
    asset_class=unreal.PCGGraph,
    factory=unreal.PCGGraphFactory()
)

get_landscape, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
surface_sampler, _ = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
transform_points, transform_settings = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
mesh_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

get_landscape.set_node_position(-600, 0)
surface_sampler.set_node_position(-300, 0)
transform_points.set_node_position(0, 0)
mesh_spawner.set_node_position(300, 0)

# Phase 3: Configure Transform (before connecting)
transform_settings.set_editor_property('scale_min', unreal.Vector(0.18, 0.18, 0.18))
transform_settings.set_editor_property('scale_max', unreal.Vector(1.55, 1.55, 1.55))
transform_settings.set_editor_property('rotation_min', unreal.Rotator(0, 0, 0))
transform_settings.set_editor_property('rotation_max', unreal.Rotator(0, 0, 360))

unreal.EditorAssetLibrary.save_loaded_asset(graph)

# Phase 2: Connect (in separate script in production!)
# Included here for reference only - may cause timeout
g = unreal.load_asset('/Game/PCG/PCG_LandscapeScatter_Complete')
o = g.get_output_node()
n = g.nodes

g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Surface"))
g.add_edge(n[1], unreal.Name("Out"), n[2], unreal.Name("In"))
g.add_edge(n[2], unreal.Name("Out"), n[3], unreal.Name("In"))
g.add_edge(n[3], unreal.Name("Out"), o, unreal.Name("Out"))
# Script ends - Silent Execution
```

---

## Pin Reference (UE 5.4+)

| Node | Input Pins | Output Pins |
|------|------------|-------------|
| Get Landscape Data | (none) | `"Out"` |
| Surface Sampler | `"Surface"` | `"Out"` |
| Transform Points | `"In"` | `"Out"` |
| Static Mesh Spawner | `"In"` | `"Out"` |

**Breaking Change:** Pre-5.4 Input node had `"Landscape"` output. UE 5.4+ requires Get Landscape Data with `"Out"` pin.

---

## See Also

- [SKILL.md](../SKILL.md) - Main PCG automation documentation
- [common_nodes.md](common_nodes.md) - Detailed node property reference
- [pin_discovery_patterns.md](pin_discovery_patterns.md) - How to find pin names
- [silent_execution_deep_dive.md](silent_execution_deep_dive.md) - Understanding async behavior

---

## Session Reference

**Source:** `UnrealEngine/unreal-mcp-main/development/Session_2025-11-17_PCG_Landscape_Scatter.md`

**Working Example:** `/Game/PCG/PCG_LandscapeScatter_Complete` (created during testing)

**Key Discoveries:**
- Get Landscape Data required in UE 5.4+
- Mesh spawner mesh entries require UI (Python API read-only)
- Print output goes to Unreal logs (not MCP)
- Rotator vs Vector for rotation properties
