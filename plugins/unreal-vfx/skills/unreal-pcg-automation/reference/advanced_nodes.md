# Advanced PCG Nodes Reference

**Version:** 1.5.0
**Last Updated:** 2025-11-17
**Source:** Production graph analysis (PCG_forest_basic_v001)
**Complexity:** 60-node forest system
**Status:** Production-validated patterns from real projects

New nodes discovered through analysis of production-grade PCG graphs.

---

## Table of Contents

1. [PCGSelfPruningSettings](#pcgselfpruningsettings)
2. [PCGCollapseSettings (ToPoint)](#pcgcollapsesettings-topoint)
3. [PCGNamedRerouteDeclarationSettings + Usage](#pcgnamedreroutedeclarationsettings--pcgnamedrerouteusagesettings)
4. [PCGDensityFilterSettings](#pcgdensityfiltersettings)
5. [PCGFilterByTypeSettings](#pcgfilterbytypesettings)
6. [PCGCopyPointsSettings](#pcgcopypointssettings)
7. [PCGLoadDataAssetSettings](#pcgloaddataassetsettings)
8. [PCGPointExtentsModifierSettings](#pcgpointextentsmodifiersettings)

---

## PCGSelfPruningSettings

**Purpose:** Prevent overlapping points (clustering prevention)

**Input Pins:**
- `In` - Points to prune
- `Overrides` - Parameter overrides

**Output Pins:**
- `Out` - Pruned points

**Key Properties:**
```python
settings.pruning_type = unreal.PCGSelfPruningType.LARGE_TO_SMALL
settings.radius_similarity_factor = 0.25
settings.comparison_source = unreal.PCGSelfPruningComparisonSource.BOUNDS
```

**Connection Pattern:**
```python
# Typical workflow
surface_sampler -> transform -> self_pruning -> bounds_modifier -> difference
```

**Use Cases:**
- Large vegetation (trees) - prevent unrealistic clustering
- Rock scatter - ensure minimum spacing
- Building placement - avoid overlaps

**Production Example (Forest Graph):**
```python
# Node 8 in PCG_forest_basic_v001
# Large tree layer with self-pruning
sampler -> transform -> self_pruning -> bounds_modifier -> difference -> collapse -> spawner
```

**Key Settings:**
- **Pruning Type:** `LARGE_TO_SMALL` (removes smaller points near larger ones)
- **Radius Similarity Factor:** 0.25 = 25% of point bounds (adjust for density)
- **Comparison Source:** `BOUNDS` (uses point bounds for overlap detection)

**Key Insight:** Self pruning BEFORE bounds modifier creates clean exclusion zones for multi-layer vegetation.

---

## PCGCollapseSettings (ToPoint)

**Purpose:** Convert point cloud to single point (centroid/center)

**Input Pins:**
- `In` - Points to collapse
- `Overrides` - Parameter overrides

**Output Pins:**
- `Out` - Single point

**Key Properties:**
```python
settings.mode = unreal.PCGCollapseMode.AVERAGE  # Or FIRST, LAST, etc.
```

**Connection Pattern:**
```python
# Typical workflow
difference -> collapse -> static_mesh_spawner
```

**Use Cases:**
- Single spawn from exclusion zone
- Center point of scattered data
- Consolidate multi-point results

**Production Example (Forest Graph):**
```python
# Found 5 times in forest graph!
# Nodes 13, 19, 26, 28, 57

# Pattern: Each vegetation layer collapses after difference
difference -> collapse -> spawner
```

**Collapse Modes:**
- `AVERAGE` - Centroid of all points
- `FIRST` - First point in set
- `LAST` - Last point in set
- `CLOSEST_TO_ORIGIN` - Nearest to world origin

**Key Insight:** Critical for multi-layer systems - converts exclusion data to spawn point. Without collapse, spawner receives point cloud instead of single location.

---

## PCGNamedRerouteDeclarationSettings + PCGNamedRerouteUsageSettings

**Purpose:** Graph organization (reusable data streams, like variables)

**Named Reroute Declaration:**
- **Input:** Source data
- **Output:** Named stream

**Named Reroute Usage:**
- **Input:** None (references declaration by name)
- **Output:** Same data as declaration

**Key Properties:**
```python
# Declaration
declaration_settings.name = "SplineData"

# Usage (multiple instances can reference same name)
usage_settings.declaration_name = "SplineData"
```

**Connection Pattern:**
```python
# One source, multiple destinations
source -> named_reroute_declaration ->
  +-> named_reroute_usage -> branch_1
  +-> named_reroute_usage -> branch_2
  +-> named_reroute_usage -> branch_3
```

**Use Cases:**
- Clean graph layout (no wire crossing)
- Reuse expensive operations (landscape sampling)
- Share spline data across multiple branches
- Organize complex graphs (60+ nodes)

**Production Example (Forest Graph):**
```python
# Node 34: Declaration
# Nodes 35, 46, 47, 48: Usages

# Pattern: Spline extents shared across filter operations
spline_sampler -> extents_modifier -> named_reroute_declaration ->
  +-> named_reroute_usage -> filter_type (trees)
  +-> named_reroute_usage -> filter_type (rocks)
  +-> named_reroute_usage -> filter_type (grass)
```

**Workflow:**
1. Create Named Reroute Declaration node
2. Set `name` property (e.g., "SplineData")
3. Connect source data to declaration input
4. Create Named Reroute Usage nodes wherever you need the data
5. Set `declaration_name` on each usage to match declaration

**Benefits:**
- Reduces visual clutter in large graphs
- Makes complex graphs maintainable
- Enables parallel processing of same data stream

**Key Insight:** Essential for readable graphs at scale (60+ nodes). Without named reroutes, forest graph would have 50+ crossing wires.

---

## PCGDensityFilterSettings

**Purpose:** Randomly thin out points by percentage

**Input Pins:**
- `In` - Points to filter
- `Overrides` - Parameter overrides

**Output Pins:**
- `Out` - Filtered points

**Key Properties:**
```python
settings.lower_bound = 0.0  # Minimum density threshold (0.0-1.0)
settings.upper_bound = 1.0  # Maximum density threshold (0.0-1.0)
```

**Connection Pattern:**
```python
# Typical workflow
collapse -> density_filter -> transform -> spawner
```

**Use Cases:**
- Multiple density variations from single source
- Sparse/medium/dense variations
- Random point thinning
- Performance optimization (reduce point count)

**Production Example (Forest Graph):**
```python
# 3 density levels from one undergrowth layer
# Nodes 54, 55, 56

# Pattern: Single source -> 3 density variations
collapse ->
  +-> density_filter(0.2-0.4) -> transform -> spawner  # Sparse
  +-> density_filter(0.4-0.7) -> transform -> spawner  # Medium
  +-> density_filter(0.7-1.0) -> transform -> spawner  # Dense
```

**Density Ranges:**
- **Sparse:** `lower_bound=0.2, upper_bound=0.4` (20-40% of points)
- **Medium:** `lower_bound=0.4, upper_bound=0.7` (40-70% of points)
- **Dense:** `lower_bound=0.7, upper_bound=1.0` (70-100% of points)

**Key Insight:** Single source -> 3 density variations = better performance than 3 separate surface samplers. Reduces computational cost while maintaining variety.

---

## PCGFilterByTypeSettings

**Purpose:** Filter specific data types (splines, volumes, points)

**Input Pins:**
- `In` - Mixed data types
- `Overrides` - Parameter overrides

**Output Pins:**
- `Out` - Filtered data (only selected type)

**Key Properties:**
```python
settings.target_filter_type = unreal.PCGDataType.SPLINE  # Or VOLUME, POINT, etc.
```

**Connection Pattern:**
```python
# Typical workflow
named_reroute -> filter_type -> difference
```

**Use Cases:**
- Separate different input data streams cleanly
- Extract splines from mixed input
- Isolate volumes from point data

**Production Example (Forest Graph):**
```python
# Nodes 35, 46, 47, 48

# Pattern: Separate spline data for different exclusion layers
named_reroute_usage -> filter_by_type(SPLINE) -> difference(trees)
named_reroute_usage -> filter_by_type(SPLINE) -> difference(rocks)
named_reroute_usage -> filter_by_type(SPLINE) -> difference(grass)
```

**Filter Types:**
- `SPLINE` - Spline actors/components
- `VOLUME` - Volume primitives
- `POINT` - Point data
- `SURFACE` - Surface data
- `RENDER_TARGET` - Render target data

**Key Insight:** Enables clean separation of data types when using multi-input workflows (e.g., landscape + spline + volume).

---

## PCGCopyPointsSettings

**Purpose:** Copy point attributes to different locations

**Input Pins:**
- `Source` - Point data to copy FROM
- `Target` - Location to copy TO
- `Overrides` - Parameter overrides

**Output Pins:**
- `Out` - Points with copied attributes

**Key Properties:**
```python
settings.rotation_inheritance = unreal.PCGCopyPointsInheritanceMode.RELATIVE
settings.scale_inheritance = unreal.PCGCopyPointsInheritanceMode.RELATIVE
```

**Connection Pattern:**
```python
# Typical workflow
load_data_asset -> copy_points(source) + spline_points(target) -> transform -> spawner
```

**Use Cases:**
- Apply external scatter patterns to spline paths
- Reuse pre-authored point distributions
- Transfer attributes between point sets

**Production Example (Forest Graph):**
```python
# Nodes 40, 41

# Pattern: External asset integration
load_data_asset -> copy_points(source) +
spline_points(target) -> transform -> spawner
```

**Inheritance Modes:**
- `RELATIVE` - Combine source and target transforms
- `SOURCE` - Use source transform only
- `TARGET` - Use target transform only

**Key Insight:** Enables artist-authored scatter patterns to be applied to procedural paths (splines, curves).

---

## PCGLoadDataAssetSettings

**Purpose:** Load external PCG data assets (reusable templates)

**Input Pins:**
- `Overrides` - Parameter overrides

**Output Pins:**
- `Out` - Loaded point data

**Key Properties:**
```python
settings.data_asset = unreal.load_asset('/Game/PCG/ScatterPatterns/ForestPattern')
```

**Connection Pattern:**
```python
# Typical workflow
load_data_asset -> copy_points -> transform -> spawner
```

**Use Cases:**
- Reusable scatter distributions
- Artist-authored point patterns
- Template-based workflows
- Consistency across projects

**Production Example (Forest Graph):**
```python
# Nodes 38, 39

# Pattern: Reusable scatter template
load_data_asset(forest_pattern) -> copy_points -> transform -> spawner
```

**Workflow:**
1. Create PCG Data Asset in Content Browser
2. Author point distribution (surface sampler, transforms, etc.)
3. Save as reusable asset
4. Load via LoadDataAssetSettings in other graphs

**Benefits:**
- Consistency across multiple graphs
- Artist-controlled distributions
- No need to recreate complex scatter patterns
- Version control for scatter templates

**Key Insight:** Found 2 instances in forest graph - indicates mature production workflow using reusable asset templates.

---

## PCGPointExtentsModifierSettings

**Purpose:** Change point size/bounds (area of influence)

**Input Pins:**
- `In` - Points to modify
- `Overrides` - Parameter overrides

**Output Pins:**
- `Out` - Points with modified extents

**Key Properties:**
```python
settings.extents = unreal.Vector(500, 500, 100)  # X, Y, Z bounds
settings.mode = unreal.PCGPointExtentsModifierMode.SET  # Or ADD, MULTIPLY
```

**Connection Pattern:**
```python
# Typical workflow
spline_sampler -> point_extents_modifier -> filter/spawn
```

**Use Cases:**
- Control spacing/overlap detection radius per point
- Adjust exclusion zone size
- Modify collision bounds for scatter

**Production Example (Forest Graph):**
```python
# Node 34

# Pattern: Spline extents for exclusion control
spline_sampler -> point_extents_modifier -> named_reroute_declaration
```

**Modifier Modes:**
- `SET` - Replace extents with specified value
- `ADD` - Add to existing extents
- `MULTIPLY` - Scale existing extents
- `MIN` - Use minimum of current and specified
- `MAX` - Use maximum of current and specified

**Key Settings:**
- **Extents:** Size of point influence (X, Y, Z)
- **Mode:** How to modify (SET, ADD, MULTIPLY)

**Key Insight:** Critical for controlling exclusion zone size in multi-layer workflows. Larger extents = larger exclusion radius.

---

## Production Workflow Integration

These advanced nodes enable complex production patterns:

**Multi-Layer Vegetation:**
```
Surface Sampler -> Self Pruning -> Bounds Modifier -> Difference -> Collapse -> Spawner
```

**Density Variations:**
```
Collapse -> Density Filter (3 ranges) -> Transform -> Spawner (sparse/medium/dense)
```

**External Asset Integration:**
```
Load Data Asset -> Copy Points + Spline -> Transform -> Spawner
```

**Graph Organization:**
```
Source -> Named Reroute Declaration -> Named Reroute Usage (multiple branches)
```

---

**See Also:**
- [production_patterns.md](production_patterns.md) - Complete multi-layer workflows
- [common_nodes.md](common_nodes.md) - Basic PCG nodes

---

**End of Advanced Nodes Reference**
