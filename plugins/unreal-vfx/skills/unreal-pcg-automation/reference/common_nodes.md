# Common PCG Node Types - Pin Reference

**Last Updated:** 2025-11-17
**Verified:** Unreal Engine 5.5
**Breaking Changes:** UE 5.4+ landscape input patterns documented

**See Also:** [advanced_nodes.md](advanced_nodes.md) - 8 new advanced nodes from production graph analysis (SelfPruning, Collapse, NamedReroute, DensityFilter, etc.)

---

## Source Nodes (No Input Connections)

### PCGGetSplineSettings
**Purpose:** Extract spline component from input actor

**Input Pins:**
- Overrides
- ActorFilter
- ActorSelection
- ComponentSelection
- (20+ settings pins - query for full list)

**Output Pins:**
- Out

**Usage:**
```python
node, settings = graph.add_node_of_type(unreal.PCGGetSplineSettings)
# No configuration needed - auto-finds spline in scene
```

### PCGGetLandscapeSettings
**Purpose:** Get landscape data for surface sampling (REQUIRED in UE 5.4+)

**🚨 UE 5.4+ BREAKING CHANGE:** Input node no longer provides landscape output. Must use this node instead.

**Input Pins:**
- Overrides

**Output Pins:**
- **Out** - Landscape data (connects to Surface Sampler "Surface" pin)

**Common Properties:**
```python
settings.allowed_grids = unreal.int32  # Grid size filter
settings.components_must_overlap_self = True  # Only overlapping components
settings.also_output_single_point_data = False  # Single point at actor location
```

**Usage (UE 5.4+):**
```python
# Create Get Landscape Data node
get_landscape, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)

# Connect to Surface Sampler
graph.add_edge(get_landscape, unreal.Name("Out"), surface_sampler, unreal.Name("Surface"))
```

**Pre-5.4 Pattern (DEPRECATED):**
```python
# OLD: Input node had "Landscape" output - NO LONGER WORKS
# graph.add_edge(input_node, unreal.Name("Landscape"), surface_sampler, unreal.Name("Surface"))
```

**When to use:**
- All landscape scatter workflows (UE 5.4+)
- Custom bounds control
- Specific landscape actor selection

**Alternative:** Surface Sampler can auto-detect landscape when PCG Volume is over terrain (simpler for basic scatter)

---

## Sampling Nodes

### PCGSplineSamplerSettings
**Purpose:** Generate points along spline at regular intervals

**Key Input Pins:**
- Spline (connect from Get Spline Data)
- Bounding Shape
- Overrides
- DistanceIncrement
- SubdivisionsPerSegment

**Output Pins:**
- Out

**Configuration:**
```python
node, settings = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)
settings.sampler_params.distance_increment = 100.0  # 1m spacing
settings.sampler_params.subdivisions_per_segment = 1
```

**Common Settings:**
- `distance_increment`: Spacing between points (cm)
- `fill`: Sampling pattern (use FILL_EDGE_BOUND_2D for splines)
- `mode`: Sampling mode (Subdivision, Distance)

### PCGSurfaceSamplerSettings
**Purpose:** Sample points on landscape or surface (UE 5.4+ landscape scatter)

**Key Input Pins:**
- **Surface** - Landscape data from Get Landscape Data (UE 5.4+)
- Bounding Shape
- Overrides
- PointsPerSquaredMeter
- PointExtents
- Looseness

**Output Pins:**
- Out

**Configuration:**
```python
node, settings = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
settings.points_per_squared_meter = 0.5  # Density (0.1 = sparse, 5.0+ = dense)
settings.point_steepness = 0.5  # [0.0-1.0] Slope tolerance
settings.unbounded = False  # WARNING: True can generate massive point counts
settings.use_seed = True  # Deterministic generation
```

**Density Guide:**
- Sparse scatter (rocks): 0.1 - 0.3
- Medium (vegetation): 1.0 - 2.0
- Dense (grass): 5.0 - 10.0

**Auto-Detection:** Can work without Surface input when PCG Volume is over landscape (simpler for basic scatter).

**UE 5.4+ Connection:**
```python
# Get landscape data → Surface Sampler
graph.add_edge(get_landscape, unreal.Name("Out"), surface_sampler, unreal.Name("Surface"))
```

---

## Transform Nodes

### PCGProjectionSettings
**Purpose:** Project points onto surface (landscape/mesh)

**Key Input Pins:**
- In (points to project)
- Projection Target (surface to project onto)
- Overrides

**Output Pins:**
- Out

**Configuration:**
```python
node, settings = graph.add_node_of_type(unreal.PCGProjectionSettings)
# Connects: Sampler → "In", Landscape → "Projection Target"
```

### PCGTransformPointsSettings
**Purpose:** Offset points in world space

**Key Input Pins:**
- In
- Overrides
- OffsetMin
- OffsetMax

**Output Pins:**
- Out

**Configuration:**
```python
node, settings = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
settings.offset_min = unreal.Vector(0, 0, -30)  # 30cm down
settings.offset_max = unreal.Vector(0, 0, -30)  # Consistent depth
```

**Common Offsets:**
- Roads: `Vector(0, 0, -30)` to `Vector(0, 0, -50)`
- Rivers: `Vector(0, 0, -50)` to `Vector(0, 0, -100)`
- Paths: `Vector(0, 0, -10)` to `Vector(0, 0, -20)`

---

## Spawn Nodes

### PCGSpawnActorSettings
**Purpose:** Spawn Blueprint actors at each point

**Key Input Pins:**
- In
- Overrides

**Output Pins:**
- Out

**Configuration:**
```python
node, settings = graph.add_node_of_type(unreal.PCGSpawnActorSettings)
bp = unreal.load_asset('/Game/Blueprints/MyActor')
settings.template_actor_class = bp.generated_class()
settings.option = unreal.EPCGSpawnActorOption.COLLAPSEACTOR
```

**Spawn Options:**
- `COLLAPSEACTOR`: Spawns into PCG component's actor
- `KEEPACTOR`: Spawns as separate actors

### PCGStaticMeshSpawnerSettings
**Purpose:** Spawn static meshes at each point with Instance/HISM optimization

**Key Input Pins:**
- In
- Overrides
- TargetActor
- Seed

**Output Pins:**
- Out

**⚠️ PYTHON API LIMITATION (UE 5.4+):**

Mesh entries CANNOT be configured via Python. Must use UI.

**Removed in UE 5.4:**
```python
# ❌ PCGStaticMeshSpawnerEntry - Class doesn't exist
# ❌ settings.meshes - Property doesn't exist
```

**Read-Only Properties:**
```python
settings.mesh_selector_type          # Read-Write ✅
settings.mesh_selector_parameters    # Read-Only ❌ (mesh entries live here)
```

**Python Configuration (Limited):**
```python
node, settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
# Can only set instance packer type, NOT mesh entries
settings.set_instance_packer_type(unreal.PCGInstancePackerType.NAIVE)
```

**UI Configuration (REQUIRED for mesh entries):**
1. Open PCG graph in Unreal Editor
2. Select Static Mesh Spawner node
3. Details panel → Mesh Entries section
4. Click "+" to add mesh entry
5. Select mesh and set weight

**Mesh Entry Example (UI only):**
- Mesh: `/Engine/BasicShapes/Cube`
- Weight: 100 (or distribute across multiple meshes)

**Multiple Meshes:**
- Entry 1: Rock (60 weight) → 60% probability
- Entry 2: Boulder (30 weight) → 30% probability
- Entry 3: Pebble (10 weight) → 10% probability

**Workaround:** Create template graphs with pre-configured mesh lists, then reference from Python.

**See Also:** [landscape_scatter_workflow.md](landscape_scatter_workflow.md) - Complete hybrid Python + UI workflow

---

## Spatial Operation Nodes

### PCGDifferenceSettings
**Purpose:** Subtract one point set from another (point exclusion, spatial masking)

**Key Input Pins:**
- **In** - Main point set (points that flow through)
- **Source** - Subtraction point set (defines exclusion zones)
- Overrides

**Output Pins:**
- Out

**⚠️ CRITICAL: Difference Mode Settings**

**Density Mode Property:**
```python
diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
```

**Modes:**
- **BINARY** (Required for point exclusion):
  - Removes main points where Source points exist
  - Boolean operation (point removed or kept)
  - Use for: Trees vs rocks, spline exclusions, clearings

- **MINIMUM**:
  - Density-based reduction
  - Keeps points but reduces density values
  - Different use case than exclusion

**Python Configuration:**
```python
node, settings = graph.add_node_of_type(unreal.PCGDifferenceSettings)

# MUST set to Binary for point exclusion
settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
```

**Connection Pattern:**
```python
# Main points (e.g., rocks) → Difference → Continue
# Exclusion points (e.g., trees) → Difference "Source" input

graph.add_edge(rock_sampler, unreal.Name("Out"), difference, unreal.Name("In"))
graph.add_edge(tree_transform, unreal.Name("Out"), difference, unreal.Name("Source"))
graph.add_edge(difference, unreal.Name("Out"), rock_transform, unreal.Name("In"))
```

**Common Use Cases:**
1. **Point-to-Point Exclusion (Trees vs Rocks):**
   - Generate sparse trees (0.1/m²)
   - Generate dense rocks (2.0/m²)
   - Use Difference to remove rocks where trees are

2. **Spline-Based Exclusion (Forest Clearings):**
   - Sample interior of closed spline
   - Use Difference to remove forest points inside spline
   - Creates roads, clearings, exclusion zones

3. **Multi-Layer Scatter:**
   - Layer 1: Large objects (trees)
   - Layer 2: Medium objects (rocks) - exclude trees
   - Layer 3: Small objects (grass) - exclude trees + rocks

**Key Discovery (YouTube Transcript):** Mode MUST be Binary for exclusion, not Minimum!

**See Also:** [spline_workflows.md](spline_workflows.md) - Complete exclusion workflows

### PCGBoundsModifierSettings
**Purpose:** Add width to non-closed splines (creates paths, roads)

**Key Input Pins:**
- In
- Overrides

**Output Pins:**
- Out

**Configuration:**
```python
node, settings = graph.add_node_of_type(unreal.PCGBoundsModifierSettings)

# Set path width
settings.set_editor_property('bounds_min', unreal.Vector(-100, -100, 0))  # Left side width
settings.set_editor_property('bounds_max', unreal.Vector(100, 100, 0))    # Right side width
```

**Use Cases:**
- **Roads:** Add width to spline path
- **Rivers:** Expand spline to river width
- **Walls:** Create boundaries along splines

**Connection Pattern:**
```python
# Spline Data → Spline Sampler → Bounds Modifier → Continue
# Creates wider area around spline line
```

**Width Settings:**
- **Min X:** Negative = left side width (-100 = 100cm left)
- **Max X:** Positive = right side width (100 = 100cm right)
- **Min/Max Y:** Front/back extension
- **Min/Max Z:** Height bounds

**Example (Road):**
```python
# 2m wide road (1m each side)
settings.set_editor_property('bounds_min', unreal.Vector(-100, -100, 0))
settings.set_editor_property('bounds_max', unreal.Vector(100, 100, 0))
```

**See Also:** [spline_workflows.md](spline_workflows.md) - Path creation workflows

---

## Advanced Spline Sampling

### PCGSplineSamplerSettings (Advanced)
**Purpose:** Generate points along or within splines

**Key Input Pins:**
- **Spline** - From Get Spline Data
- Bounding Shape
- Overrides

**Output Pins:**
- Out

**Fill Modes (Critical for closed splines):**
```python
sampler_settings.set_editor_property('fill', unreal.PCGSplineSamplingFill.FILL_INTERIOR)
```

**Fill Options:**
- **FILL_EDGE_BOUND_2D** - Points along spline edge (default, for open splines)
- **FILL_INTERIOR** - Fill interior of closed spline (for loops, clearings)
- Other modes: Check Unreal docs

**Sampling Mode:**
```python
sampler_settings.set_editor_property('mode', unreal.PCGSplineSamplingMode.DISTANCE)
```

**Modes:**
- **SUBDIVISION** - Points per spline segment
- **DISTANCE** - Points at fixed distance intervals (better for paths)

**Unbounded (Critical for splines outside PCG Volume):**
```python
sampler_settings.set_editor_property('unbounded', True)
```

**Why Unbounded:**
- PCG Volume limits sampling by default
- Unbounded allows splines extending beyond volume
- Essential for world-space splines

**Interior Spacing (for FILL_INTERIOR):**
```python
# Larger spacing = fewer points = faster performance
sampler_settings.set_editor_property('interior_sample_spacing', 100.0)  # 100cm spacing
```

**Complete Closed Spline Setup:**
```python
node, settings = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)

# Fill interior of closed loop
settings.set_editor_property('fill', unreal.PCGSplineSamplingFill.FILL_INTERIOR)

# Allow splines outside PCG Volume
settings.set_editor_property('unbounded', True)

# Control interior point density
settings.set_editor_property('interior_sample_spacing', 100.0)
```

**Complete Path Setup:**
```python
node, settings = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)

# Sample along spline edge
settings.set_editor_property('fill', unreal.PCGSplineSamplingFill.FILL_EDGE_BOUND_2D)

# Use distance mode for even spacing
settings.set_editor_property('mode', unreal.PCGSplineSamplingMode.DISTANCE)

# Point spacing along path
settings.set_editor_property('distance_increment', 100.0)  # Point every 100cm
```

**Common Issues:**
- **No points appear:** Check unbounded = True
- **Points outside spline:** Wrong fill mode (use FILL_INTERIOR for closed)
- **Uneven distribution:** Switch to DISTANCE mode

**See Also:** [spline_workflows.md](spline_workflows.md) for complete examples

---

## Built-in Nodes

### Input Node
**Type:** `graph.get_input_node()`

**Output Pins:**
- In (counter-intuitive name!)

**Usage:**
```python
i = graph.get_input_node()
graph.add_edge(i, unreal.Name("In"), first_node, unreal.Name("In"))
```

### Output Node
**Type:** `graph.get_output_node()`

**Input Pins:**
- Out (counter-intuitive name!)

**Usage:**
```python
o = graph.get_output_node()
graph.add_edge(last_node, unreal.Name("Out"), o, unreal.Name("Out"))
```

---

## Pin Discovery Pattern

**Always query pins before connecting:**
```python
# List all input pins
for pin in node.input_pins:
    print(f"Input: {pin.properties.label}")

# List all output pins
for pin in node.output_pins:
    print(f"Output: {pin.properties.label}")

# Find specific pin
target_pin = next((p for p in node.input_pins if p.properties.label == "Spline"), None)
```

---

## Common Connection Patterns

### Spline Sampling Workflow
```
Input → Get Spline Data → Spline Sampler → Transform → Spawn Actor → Output
```

### Landscape Projection Workflow
```
Spline Sampler → Projection ← Get Landscape Data
                      ↓
                Transform Points
```

### Full Deformation Workflow
```
Get Spline → Sampler → Projection ← Get Landscape
                            ↓
                      Transform Points
                            ↓
                       Spawn Actor
                            ↓
                          Output
```

---

## Node Type Reference

**Find node class names:**
- Unreal Editor → PCG Graph → Add Node
- Python: `dir(unreal)` → search for `PCG*Settings`

**Common patterns:**
- `PCGGet*Settings`: Data source nodes
- `PCG*SamplerSettings`: Point generation nodes
- `PCG*TransformSettings`: Point manipulation nodes
- `PCG*FilterSettings`: Point filtering nodes
