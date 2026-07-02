# PCG Spline Workflows

**Last Updated:** 2025-11-17
**Source:** YouTube transcript analysis + production testing
**Unreal Version:** 5.4+

---

## Overview

Complete workflows for using splines with PCG for exclusion zones, paths, roads, and spatial masking.

**Key Concepts:**
- **Tag-Based Selection:** Find splines by tag name
- **Difference Binary Mode:** Critical for point exclusion
- **Unbounded Sampling:** Allow splines outside PCG Volume
- **Fill Modes:** Interior vs Edge sampling

**Advanced Patterns:**
- **Multi-Layer Vegetation:** Splines can be used with multi-layer vegetation systems (see [production_patterns.md](production_patterns.md)) for exclusion zones that cascade through 4+ vegetation layers
- **Named Reroutes:** For complex spline-based workflows with multiple exclusion branches, use Named Reroutes to share spline data cleanly (see [advanced_nodes.md](advanced_nodes.md))

---

## Workflow 1: Forest Clearing (Closed Spline Exclusion)

**Goal:** Create clearing in dense forest using closed spline loop

### Step 1: Create Tagged Spline

**In Viewport:**
1. Modeling Mode → Draw Spline
2. Draw closed loop around clearing area
3. Click **"Loop"** button to close spline
4. Select spline in Outliner
5. Details panel → **Tags** section → Click **"+"**
6. Add tag: `"Clearing"`

### Step 2: Python - Create Graph Structure

```python
import unreal

# Create graph
graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_ForestClearing",
    package_path="/Game/PCG",
    asset_class=unreal.PCGGraph,
    factory=unreal.PCGGraphFactory()
)

# Forest branch (main)
get_landscape, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
surface_sampler, sampler_settings = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
sampler_settings.points_per_squared_meter = 2.0  # Dense forest

# Clearing branch (exclusion)
get_spline, spline_settings = graph.add_node_of_type(unreal.PCGGetSplineSettings)
spline_sampler, spline_sampler_settings = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)

# Difference for exclusion
difference, diff_settings = graph.add_node_of_type(unreal.PCGDifferenceSettings)

# Transform and spawn
transform, transform_settings = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
tree_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

# Position nodes
get_landscape.set_node_position(-900, 0)
surface_sampler.set_node_position(-600, 0)
difference.set_node_position(-300, 0)
get_spline.set_node_position(-600, -300)  # Below main flow
spline_sampler.set_node_position(-300, -300)
transform.set_node_position(0, 0)
tree_spawner.set_node_position(300, 0)

unreal.EditorAssetLibrary.save_loaded_asset(graph)
```

### Step 3: Configure Spline Selection (Tag-Based)

```python
g = unreal.load_asset('/Game/PCG/PCG_ForestClearing')
get_spline_settings = g.nodes[3].get_settings()  # Adjust index if needed

# CRITICAL: Set to All World Actors
get_spline_settings.set_editor_property('actor_filter', unreal.PCGActorFilter.ALL_WORLD_ACTORS)

# Set tag to find spline
get_spline_settings.set_editor_property('actor_selection_tag', "Clearing")

unreal.EditorAssetLibrary.save_loaded_asset(g)
```

### Step 4: Configure Spline Sampler (Fill Interior)

```python
spline_sampler_settings = g.nodes[4].get_settings()

# Fill interior of closed loop
spline_sampler_settings.set_editor_property('fill', unreal.PCGSplineSamplingFill.FILL_INTERIOR)

# CRITICAL: Enable unbounded
spline_sampler_settings.set_editor_property('unbounded', True)

# Interior point spacing (larger = fewer points = faster)
spline_sampler_settings.set_editor_property('interior_sample_spacing', 100.0)

unreal.EditorAssetLibrary.save_loaded_asset(g)
```

### Step 5: Configure Difference (Binary Mode)

```python
diff_settings = g.nodes[2].get_settings()

# MUST be Binary for exclusion
diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)

unreal.EditorAssetLibrary.save_loaded_asset(g)
```

### Step 6: Connect Nodes (Silent Execution)

```python
g = unreal.load_asset('/Game/PCG/PCG_ForestClearing')
o = g.get_output_node()
n = g.nodes

# Main forest flow: Landscape → Sampler → Difference → Transform → Spawner → Output
g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Surface"))
g.add_edge(n[1], unreal.Name("Out"), n[2], unreal.Name("In"))
g.add_edge(n[2], unreal.Name("Out"), n[5], unreal.Name("In"))
g.add_edge(n[5], unreal.Name("Out"), n[6], unreal.Name("In"))
g.add_edge(n[6], unreal.Name("Out"), o, unreal.Name("Out"))

# Clearing exclusion: Spline → Sampler → Difference "Source"
g.add_edge(n[3], unreal.Name("Out"), n[4], unreal.Name("Spline"))
g.add_edge(n[4], unreal.Name("Out"), n[2], unreal.Name("Source"))
# NO CODE AFTER
```

### Result

Dense forest with spline-shaped clearing. Trees removed where spline interior is sampled.

---

## Workflow 2: Road Through Forest (Path with Width)

**Goal:** Create road that cuts through forest with defined width

### Step 1: Create Non-Closed Spline Path

**In Viewport:**
1. Modeling Mode → Draw Spline
2. Draw path (do NOT close loop)
3. Select spline in Outliner
4. Details panel → Tags → Add `"Road"`

### Step 2: Python - Create Road Graph

```python
import unreal

graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_ForestRoad",
    package_path="/Game/PCG",
    asset_class=unreal.PCGGraph,
    factory=unreal.PCGGraphFactory()
)

# Forest branch
get_landscape_forest, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
surface_sampler_forest, forest_settings = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
forest_settings.points_per_squared_meter = 2.0

# Road branch
get_spline, spline_settings = graph.add_node_of_type(unreal.PCGGetSplineSettings)
spline_sampler, sampler_settings = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)
bounds_modifier, bounds_settings = graph.add_node_of_type(unreal.PCGBoundsModifierSettings)
projection, _ = graph.add_node_of_type(unreal.PCGProjectionSettings)

# Difference for road exclusion
difference, diff_settings = graph.add_node_of_type(unreal.PCGDifferenceSettings)

# Forest transform/spawn
transform_forest, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
tree_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

# Road transform/spawn
transform_road, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
road_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

unreal.EditorAssetLibrary.save_loaded_asset(graph)
```

### Step 3: Configure Get Spline (Tag-Based)

```python
g = unreal.load_asset('/Game/PCG/PCG_ForestRoad')
get_spline_settings = g.nodes[2].get_settings()

get_spline_settings.set_editor_property('actor_filter', unreal.PCGActorFilter.ALL_WORLD_ACTORS)
get_spline_settings.set_editor_property('actor_selection_tag', "Road")

unreal.EditorAssetLibrary.save_loaded_asset(g)
```

### Step 4: Configure Spline Sampler (Distance Mode)

```python
sampler_settings = g.nodes[3].get_settings()

# Use distance mode for even path spacing
sampler_settings.set_editor_property('mode', unreal.PCGSplineSamplingMode.DISTANCE)

# Point every 100cm along path
sampler_settings.set_editor_property('distance_increment', 100.0)

# Critical for splines outside volume
sampler_settings.set_editor_property('unbounded', True)

unreal.EditorAssetLibrary.save_loaded_asset(g)
```

### Step 5: Configure Bounds Modifier (Road Width)

```python
bounds_settings = g.nodes[4].get_settings()

# 4m wide road (2m each side)
bounds_settings.set_editor_property('bounds_min', unreal.Vector(-200, -200, 0))
bounds_settings.set_editor_property('bounds_max', unreal.Vector(200, 200, 0))

unreal.EditorAssetLibrary.save_loaded_asset(g)
```

### Step 6: Configure Difference (Binary)

```python
diff_settings = g.nodes[6].get_settings()
diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)

unreal.EditorAssetLibrary.save_loaded_asset(g)
```

### Step 7: Connect Nodes

```python
g = unreal.load_asset('/Game/PCG/PCG_ForestRoad')
o = g.get_output_node()
n = g.nodes

# Forest flow: Landscape → Sampler → Difference → Transform → Tree Spawner → Output
g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Surface"))
g.add_edge(n[1], unreal.Name("Out"), n[6], unreal.Name("In"))
g.add_edge(n[6], unreal.Name("Out"), n[7], unreal.Name("In"))
g.add_edge(n[7], unreal.Name("Out"), n[8], unreal.Name("In"))
g.add_edge(n[8], unreal.Name("Out"), o, unreal.Name("Out"))

# Road flow: Spline → Sampler → Bounds → Projection → Difference "Source"
g.add_edge(n[2], unreal.Name("Out"), n[3], unreal.Name("Spline"))
g.add_edge(n[3], unreal.Name("Out"), n[4], unreal.Name("In"))
g.add_edge(n[4], unreal.Name("Out"), n[5], unreal.Name("In"))

# Projection needs landscape
g.add_edge(n[0], unreal.Name("Out"), n[5], unreal.Name("Projection Target"))

# Road exclusion to forest
g.add_edge(n[5], unreal.Name("Out"), n[6], unreal.Name("Source"))

# Road spawner branch (optional - for road meshes)
g.add_edge(n[5], unreal.Name("Out"), n[9], unreal.Name("In"))
g.add_edge(n[9], unreal.Name("Out"), n[10], unreal.Name("In"))
g.add_edge(n[10], unreal.Name("Out"), o, unreal.Name("Out"))
# NO CODE AFTER
```

### Result

Forest with 4m wide road carved through. Road follows landscape terrain via Projection.

---

## Workflow 3: Multi-Object Exclusion (Trees, Rocks, Grass)

**Goal:** Three layers with mutual exclusion (no overlap)

### Hierarchy

1. **Trees** (0.1/m²) - Sparse, largest objects
2. **Rocks** (2.0/m²) - Dense, exclude trees
3. **Grass** (10.0/m²) - Very dense, exclude trees + rocks

### Python Setup

```python
import unreal

graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_MultiLayer",
    package_path="/Game/PCG",
    asset_class=unreal.PCGGraph,
    factory=unreal.PCGGraphFactory()
)

# Shared landscape source
get_landscape, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)

# Tree layer (sparse)
tree_sampler, tree_sampler_settings = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
tree_sampler_settings.points_per_squared_meter = 0.1
tree_transform, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
tree_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

# Rock layer (dense, exclude trees)
rock_sampler, rock_sampler_settings = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
rock_sampler_settings.points_per_squared_meter = 2.0
rock_difference, rock_diff_settings = graph.add_node_of_type(unreal.PCGDifferenceSettings)
rock_diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
rock_transform, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
rock_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

# Grass layer (very dense, exclude trees + rocks)
grass_sampler, grass_sampler_settings = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
grass_sampler_settings.points_per_squared_meter = 10.0
grass_difference_trees, grass_diff_tree_settings = graph.add_node_of_type(unreal.PCGDifferenceSettings)
grass_diff_tree_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
grass_difference_rocks, grass_diff_rock_settings = graph.add_node_of_type(unreal.PCGDifferenceSettings)
grass_diff_rock_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
grass_transform, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
grass_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

unreal.EditorAssetLibrary.save_loaded_asset(graph)
```

### Connection Pattern

```python
g = unreal.load_asset('/Game/PCG/PCG_MultiLayer')
o = g.get_output_node()
n = g.nodes

# Tree layer (straightforward)
g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Surface"))  # Landscape → Tree Sampler
g.add_edge(n[1], unreal.Name("Out"), n[2], unreal.Name("In"))        # Tree Sampler → Transform
g.add_edge(n[2], unreal.Name("Out"), n[3], unreal.Name("In"))        # Transform → Spawner
g.add_edge(n[3], unreal.Name("Out"), o, unreal.Name("Out"))          # Spawner → Output

# Rock layer (exclude trees)
g.add_edge(n[0], unreal.Name("Out"), n[4], unreal.Name("Surface"))  # Landscape → Rock Sampler
g.add_edge(n[4], unreal.Name("Out"), n[5], unreal.Name("In"))        # Rock Sampler → Difference
g.add_edge(n[2], unreal.Name("Out"), n[5], unreal.Name("Source"))    # Tree Transform → Difference (exclusion)
g.add_edge(n[5], unreal.Name("Out"), n[6], unreal.Name("In"))        # Difference → Transform
g.add_edge(n[6], unreal.Name("Out"), n[7], unreal.Name("In"))        # Transform → Spawner
g.add_edge(n[7], unreal.Name("Out"), o, unreal.Name("Out"))          # Spawner → Output

# Grass layer (exclude trees AND rocks)
g.add_edge(n[0], unreal.Name("Out"), n[8], unreal.Name("Surface"))  # Landscape → Grass Sampler
g.add_edge(n[8], unreal.Name("Out"), n[9], unreal.Name("In"))        # Grass Sampler → Difference (trees)
g.add_edge(n[2], unreal.Name("Out"), n[9], unreal.Name("Source"))    # Tree Transform → Difference
g.add_edge(n[9], unreal.Name("Out"), n[10], unreal.Name("In"))       # Difference → Difference (rocks)
g.add_edge(n[6], unreal.Name("Out"), n[10], unreal.Name("Source"))   # Rock Transform → Difference
g.add_edge(n[10], unreal.Name("Out"), n[11], unreal.Name("In"))      # Difference → Transform
g.add_edge(n[11], unreal.Name("Out"), n[12], unreal.Name("In"))      # Transform → Spawner
g.add_edge(n[12], unreal.Name("Out"), o, unreal.Name("Out"))         # Spawner → Output
# NO CODE AFTER
```

### Result

Three non-overlapping layers with proper size hierarchy and density control.

---

## Key Discoveries (YouTube Transcript)

### 1. Binary Mode is Critical

**From transcript:** "you need to come here and change this from minimum to Binary"

```python
# WRONG - Won't work for exclusion
diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.MINIMUM)

# CORRECT - Required for point exclusion
diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
```

### 2. Unbounded for World Splines

**From transcript:** "you need to turn on Unbound and what that means is now you'll see it"

Without unbounded, splines outside PCG Volume won't generate points.

### 3. Distance Mode for Even Path Spacing

**From transcript:** "you want to change it from subdivision mode to distance okay and that's going to fix this problem"

Subdivision mode causes uneven spacing on paths - use Distance mode instead.

### 4. Actor Filter Must Be "All World Actors"

**From transcript:** "come up here to actor filter and I'm going to change this to all World actors"

Required for tag-based spline selection to work.

### 5. Projection Makes Splines Follow Terrain

**From transcript:** "we need to do something similar and so I'm going to go ahead and type projection"

Road/path splines need Projection → Landscape to follow terrain properly.

---

## Troubleshooting

### Spline Not Found (Warning in Graph)

**Symptom:** Yellow warning triangle on Get Spline node

**Causes:**
1. Actor Filter not set to "All World Actors"
2. Wrong tag name (case-sensitive)
3. Spline doesn't have tag applied

**Fix:**
```python
spline_settings.set_editor_property('actor_filter', unreal.PCGActorFilter.ALL_WORLD_ACTORS)
spline_settings.set_editor_property('actor_selection_tag', "YourTagName")  # Match exactly
```

### No Points Generated from Spline

**Symptom:** Spline sampler shows no points in debug mode

**Causes:**
1. Unbounded not enabled
2. Wrong fill mode (using Edge for closed spline)
3. PCG Volume doesn't overlap spline area (even with unbounded)

**Fix:**
```python
sampler_settings.set_editor_property('unbounded', True)
sampler_settings.set_editor_property('fill', unreal.PCGSplineSamplingFill.FILL_INTERIOR)  # For closed loops
```

### Exclusion Not Working (Points Still Overlap)

**Symptom:** Trees spawn where rocks are (or vice versa)

**Cause:** Difference mode is Minimum instead of Binary

**Fix:**
```python
diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
```

### Road Doesn't Follow Terrain

**Symptom:** Road floats above/below landscape

**Cause:** Missing Projection node

**Fix:** Add Projection node after Bounds Modifier, connect Landscape to Projection Target input.

---

## See Also

- [SKILL.md](../SKILL.md) - Workflows 4-5 for complete examples
- [common_nodes.md](common_nodes.md) - Detailed node reference
- [landscape_scatter_workflow.md](landscape_scatter_workflow.md) - Surface sampling patterns

---

**Source:** YouTube tutorial "Unreal Engine 5 PCG Landscape and Spline" transcript analysis + production validation
