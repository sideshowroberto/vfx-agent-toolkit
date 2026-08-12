# PCG Workflows Reference

**Version:** 1.5.0
**Last Updated:** 2025-11-17
**Context:** Production-validated workflows for PCG graph creation

Complete workflows extracted from unreal-pcg-automation skill for on-demand reference.

---

## Table of Contents

1. [Build Complete 6-Node Landscape Deformation Graph](#workflow-1-build-complete-6-node-landscape-deformation-graph)
2. [Node Layout Patterns](#node-layout-patterns)
3. [Discover Pin Names for Any Node](#workflow-2-discover-pin-names-for-any-node)
4. [Add Custom Node Types](#workflow-3-add-custom-node-types)
5. [Point Exclusion (Trees vs Rocks)](#workflow-4-point-exclusion-trees-vs-rocks)
6. [Spline-Based Point Exclusion](#workflow-5-spline-based-point-exclusion)
7. [Road Environment System (Landscape Spline + PCG)](#workflow-6-road-environment-system-landscape-spline--pcg)
8. [Modify Existing Graph](#workflow-7-modify-existing-graph)

---

## Workflow 1: Build Complete 6-Node Landscape Deformation Graph

**Steps:**
1. **Create graph asset:**
   ```python
   import unreal
   graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
       asset_name="PCG_LandscapeDeform",
       package_path="/Game/PCG",
       asset_class=unreal.PCGGraph,
       factory=unreal.PCGGraphFactory()
   )
   ```

2. **Add all nodes (returns tuple!):**
   ```python
   get_spline, _ = graph.add_node_of_type(unreal.PCGGetSplineSettings)
   sampler, sampler_s = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)
   get_land, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
   projection, _ = graph.add_node_of_type(unreal.PCGProjectionSettings)
   transform, transform_s = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
   spawn, _ = graph.add_node_of_type(unreal.PCGSpawnActorSettings)
   ```

3. **Position nodes in readable Y-pattern:**
   ```python
   get_spline.set_node_position(-600, -100)
   sampler.set_node_position(-300, -100)
   get_land.set_node_position(-600, 100)
   projection.set_node_position(0, 0)
   transform.set_node_position(300, 0)
   spawn.set_node_position(600, 0)
   ```

4. **Configure settings:**
   ```python
   sampler_s.sampler_params.distance_increment = 100.0
   transform_s.offset_min = unreal.Vector(0, 0, -30)
   transform_s.offset_max = unreal.Vector(0, 0, -30)
   ```

5. **Query pin names (if unsure):**
   ```python
   for pin in projection.input_pins:
       print(f"Projection input: {pin.properties.label}")
   ```

6. **Connect nodes (separate script for Silent Execution):**
   ```python
   g = unreal.load_asset('/Game/PCG/PCG_LandscapeDeform')
   n = g.nodes
   g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Spline"))
   g.add_edge(n[1], unreal.Name("Out"), n[3], unreal.Name("In"))
   g.add_edge(n[2], unreal.Name("Out"), n[3], unreal.Name("Projection Target"))
   g.add_edge(n[3], unreal.Name("Out"), n[4], unreal.Name("In"))
   g.add_edge(n[4], unreal.Name("Out"), n[5], unreal.Name("In"))
   g.add_edge(n[5], unreal.Name("Out"), g.get_output_node(), unreal.Name("Out"))
   ```

**Output:** Complete PCG graph ready for spline-based landscape deformation

**Performance:** ~4ms total execution time

---

## Node Layout Patterns

### Horizontal Flow Layout
**Pattern:** Left to right, 300-unit spacing
**Use for:** Linear processing chains

```python
# Example: 3-node chain
node1.set_node_position(-300, 0)
node2.set_node_position(0, 0)
node3.set_node_position(300, 0)
```

### Dual-Input Layout (Y-Pattern)
**Pattern:** Two sources converge to center node
**Use for:** Projection workflows (Spline + Landscape)

```python
# Top source
get_spline.set_node_position(-600, -100)
sampler.set_node_position(-300, -100)

# Bottom source
get_land.set_node_position(-600, 100)

# Center (receives both)
projection.set_node_position(0, 0)

# Right flow
transform.set_node_position(300, 0)
spawn.set_node_position(600, 0)
```

**Spacing:** 300 units horizontal, 200 units vertical. Related nodes 100-150 units closer.

**Benefits:** Easier debugging, team collaboration, faster understanding. Position before connecting for cleaner lines.

---

## Workflow 2: Discover Pin Names for Any Node

**Steps:**
1. **Create or load graph:**
   ```python
   import unreal
   g = unreal.load_asset('/Game/PCG/MyGraph')
   ```

2. **Add node to inspect:**
   ```python
   node, settings = g.add_node_of_type(unreal.PCGProjectionSettings)
   ```

3. **List all input pins:**
   ```python
   print("Input pins:")
   for pin in node.input_pins:
       print(f"  - {pin.properties.label}")
   ```

4. **List all output pins:**
   ```python
   print("Output pins:")
   for pin in node.output_pins:
       print(f"  - {pin.properties.label}")
   ```

5. **Find specific pin:**
   ```python
   spline_pin = next((p for p in node.input_pins if p.properties.label == "Spline"), None)
   if spline_pin:
       print(f"Found Spline pin!")
   ```

**Output:** Complete list of available pins for connections

**When to use:** Always before connecting unfamiliar nodes

---

## Workflow 3: Add Custom Node Types

**Steps:**
1. **Load graph:**
   ```python
   import unreal
   g = unreal.load_asset('/Game/PCG/MyGraph')
   ```

2. **Add custom node (find class name in Unreal docs):**
   ```python
   # Example: Difference node
   diff_node, diff_settings = g.add_node_of_type(unreal.PCGDifferenceSettings)

   # Example: Attribute Transfer
   transfer_node, transfer_settings = g.add_node_of_type(unreal.PCGAttributeTransferSettings)
   ```

3. **Configure custom settings:**
   ```python
   # Check available properties
   props = [p for p in dir(diff_settings) if not p.startswith('_')]
   print(props)

   # Set specific property
   diff_settings.set_editor_property('property_name', value)
   ```

4. **Query pins before connecting:**
   ```python
   for pin in diff_node.input_pins:
       print(f"{pin.properties.label}")
   ```

5. **Connect with unreal.Name():**
   ```python
   g.add_edge(prev_node, unreal.Name("Out"), diff_node, unreal.Name("In"))
   ```

**Output:** Custom node integrated into graph

**Common custom nodes:** Attribute nodes, Filter nodes, Transform nodes, Debug nodes

---

## Workflow 4: Point Exclusion (Trees vs Rocks)

**Problem:** Generate rocks that don't spawn where trees are located

**Solution:** Use Difference node in Binary mode to subtract tree points from rock points

**Steps:**

1. **Create dual-density setup:**
   ```python
   import unreal
   graph = unreal.load_asset('/Game/PCG/MyGraph')

   # Tree branch (sparse)
   get_landscape_trees, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
   surface_sampler_trees, tree_sampler_settings = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
   tree_sampler_settings.points_per_squared_meter = 0.1  # Sparse trees

   transform_trees, tree_transform = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
   tree_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

   # Rock branch (dense)
   get_landscape_rocks, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
   surface_sampler_rocks, rock_sampler_settings = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
   rock_sampler_settings.points_per_squared_meter = 2.0  # Dense rocks

   # CRITICAL: Difference node for exclusion
   difference, diff_settings = graph.add_node_of_type(unreal.PCGDifferenceSettings)

   transform_rocks, rock_transform = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
   rock_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
   ```

2. **Position nodes (Y-pattern with exclusion):**
   ```python
   # Tree branch (top)
   get_landscape_trees.set_node_position(-600, -200)
   surface_sampler_trees.set_node_position(-300, -200)
   transform_trees.set_node_position(0, -200)
   tree_spawner.set_node_position(300, -200)

   # Rock branch (bottom, with difference)
   get_landscape_rocks.set_node_position(-600, 200)
   surface_sampler_rocks.set_node_position(-300, 200)
   difference.set_node_position(0, 200)  # Exclusion happens here
   transform_rocks.set_node_position(300, 200)
   rock_spawner.set_node_position(600, 200)
   ```

3. **Configure Difference node (CRITICAL - must be Binary):**
   ```python
   # Set to Binary mode for subtraction (not Minimum!)
   diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
   ```

4. **Connect nodes (separate script for Silent Execution):**
   ```python
   g = unreal.load_asset('/Game/PCG/MyGraph')
   o = g.get_output_node()
   n = g.nodes

   # Tree branch: Landscape -> Sampler -> Transform -> Tree Spawner -> Output
   g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Surface"))
   g.add_edge(n[1], unreal.Name("Out"), n[2], unreal.Name("In"))
   g.add_edge(n[2], unreal.Name("Out"), n[3], unreal.Name("In"))
   g.add_edge(n[3], unreal.Name("Out"), o, unreal.Name("Out"))

   # Rock branch: Landscape -> Sampler -> Difference -> Transform -> Rock Spawner -> Output
   g.add_edge(n[4], unreal.Name("Out"), n[5], unreal.Name("Surface"))
   g.add_edge(n[5], unreal.Name("Out"), n[6], unreal.Name("In"))  # Rocks to Difference

   # Tree points to Difference (subtraction input)
   g.add_edge(n[2], unreal.Name("Out"), n[6], unreal.Name("Source"))  # Trees subtract from rocks

   # Continue rock flow
   g.add_edge(n[6], unreal.Name("Out"), n[7], unreal.Name("In"))
   g.add_edge(n[7], unreal.Name("Out"), n[8], unreal.Name("In"))
   g.add_edge(n[8], unreal.Name("Out"), o, unreal.Name("Out"))
   # NO CODE AFTER
   ```

**How it works:**
- Trees generate at low density (0.1 pts/m^2)
- Rocks generate at high density (2.0 pts/m^2)
- Difference node removes any rock points near tree points
- Result: Dense rocks with gaps where trees are

**Key Discovery:** Difference mode MUST be **Binary** (not Minimum) for point exclusion to work!

**Output:** Two spawners that respect each other's space

**See Also:** [spline_workflows.md](spline_workflows.md) for spline-based exclusion

---

## Workflow 5: Spline-Based Point Exclusion

**Problem:** Remove points inside/outside a closed spline boundary

**Solution:** Use tagged spline + Difference node in Binary mode

**Steps:**

1. **Create spline in viewport:**
   - Modeling mode -> Draw Spline -> Draw closed loop -> Click "Loop" to close
   - Name: SplineActor (or any name)
   - Add Tag: In Outliner -> Select spline -> Details -> Tags -> Add "ExclusionZone"

2. **Add spline data node:**
   ```python
   import unreal
   graph = unreal.load_asset('/Game/PCG/MyGraph')

   # Get spline by tag
   get_spline, spline_settings = graph.add_node_of_type(unreal.PCGGetSplineSettings)

   # Spline sampler (fills interior)
   spline_sampler, sampler_settings = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)

   # Difference for exclusion
   difference, diff_settings = graph.add_node_of_type(unreal.PCGDifferenceSettings)
   ```

3. **Configure Get Spline (tag-based selection):**
   ```python
   # CRITICAL: Must set to All World Actors to find tagged splines
   spline_settings.set_editor_property('actor_filter', unreal.PCGActorFilter.ALL_WORLD_ACTORS)
   spline_settings.set_editor_property('actor_selection_tag', "ExclusionZone")
   ```

4. **Configure Spline Sampler:**
   ```python
   # Fill interior of closed spline
   sampler_settings.set_editor_property('fill', unreal.PCGSplineSamplingFill.FILL_INTERIOR)

   # CRITICAL: Enable unbounded for splines outside PCG Volume
   sampler_settings.set_editor_property('unbounded', True)

   # Interior spacing (larger = fewer points, faster)
   sampler_settings.set_editor_property('interior_sample_spacing', 100.0)
   ```

5. **Configure Difference (Binary mode):**
   ```python
   # MUST be Binary for exclusion
   diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
   ```

6. **Connect flow:**
   ```python
   # Main point flow (e.g., Surface Sampler) -> Difference
   # Spline points -> Difference "Source" input
   # Difference removes main points where spline points exist
   ```

**Key Settings:**
- **Actor Filter:** All World Actors (required for tag-based selection)
- **Fill Mode:** Interior (fills closed spline)
- **Unbounded:** True (allows splines outside PCG Volume)
- **Difference Mode:** Binary (NOT Minimum)

**Output:** Points with spline-shaped exclusion zone

**Use Cases:** Roads through forests, clearings, exclusion zones, safe areas

---

## Workflow 6: Road Environment System (Landscape Spline + PCG)

**Problem:** Spawn props along both sides of a road (street lamps, signs, barriers, vegetation)

**Solution:** Hybrid workflow - Landscape Spline for road, PCG for props

**Use Case:** Car commercial environments, city streets, highways, forest roads

**Prerequisites:**
- Landscape with Landscape Spline created (Landscape Mode -> Spline Tool)
- Landscape spline can sculpt terrain automatically
- Road mesh assigned to landscape spline (see tutorial reference)

**Steps:**

1. **Create PCG graph:**
   ```python
   import unreal
   graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
       asset_name="PCG_RoadEnvironment",
       package_path="/Game/PCG",
       asset_class=unreal.PCGGraph,
       factory=unreal.PCGGraphFactory()
   )
   ```

2. **Add nodes:**
   ```python
   # Get landscape spline
   get_spline, _ = graph.add_node_of_type(unreal.PCGGetSplineSettings)

   # Sample along spline
   spline_sampler, _ = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)

   # Transform left side
   transform_left, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)

   # Transform right side
   transform_right, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)

   # Spawn meshes
   mesh_spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
   ```

3. **Configure Get Spline for Landscape (CRITICAL):**
   ```python
   # MUST use BY_CLASS for landscape splines (not ALL_WORLD_ACTORS)
   actor_selector = get_spline.get_settings().actor_selector
   actor_selector.actor_selection = unreal.PCGActorSelection.BY_CLASS
   actor_selector.actor_selection_class = unreal.Landscape

   # [WARN] VERIFY settings were applied (see Property Verification Workflow)
   # Re-load graph and check if properties stuck
   ```

4. **Configure Spline Sampler:**
   ```python
   sampler_settings = spline_sampler.get_settings()
   sampler_params = sampler_settings.sampler_params

   # Distance mode for even spacing
   sampler_params.mode = unreal.PCGSplineSamplingMode.DISTANCE
   sampler_params.distance_increment = 1000.0  # 10m spacing (adjust per use case)
   sampler_params.unbounded = True  # Beyond PCG volume
   ```

5. **Configure Transforms:**
   ```python
   # Left side: offset -9m (negative Y)
   left_settings = transform_left.get_settings()
   left_settings.offset_min = unreal.Vector(0, -900, 0)
   left_settings.offset_max = unreal.Vector(0, -900, 0)
   left_settings.absolute_scale = True  # Prevents mesh deformation

   # Right side: offset +9m, rotate 180 deg
   right_settings = transform_right.get_settings()
   right_settings.offset_min = unreal.Vector(0, 900, 0)
   right_settings.offset_max = unreal.Vector(0, 900, 0)
   right_settings.rotation_min = unreal.Rotator(0, 0, 180)
   right_settings.rotation_max = unreal.Rotator(0, 0, 180)
   right_settings.absolute_scale = True
   ```

6. **Connect nodes:**
   ```python
   i = graph.get_input_node()
   o = graph.get_output_node()
   n = graph.nodes

   # Input -> Get Spline -> Spline Sampler -> Split to both transforms -> Merge at spawner -> Output
   graph.add_edge(i, unreal.Name("In"), n[0], unreal.Name("In"))
   graph.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Spline"))
   graph.add_edge(n[1], unreal.Name("Out"), n[2], unreal.Name("In"))  # Left transform
   graph.add_edge(n[1], unreal.Name("Out"), n[3], unreal.Name("In"))  # Right transform
   graph.add_edge(n[2], unreal.Name("Out"), n[4], unreal.Name("In"))  # Left -> Spawner
   graph.add_edge(n[3], unreal.Name("Out"), n[4], unreal.Name("In"))  # Right -> Spawner
   graph.add_edge(n[4], unreal.Name("Out"), o, unreal.Name("Out"))
   # NO CODE AFTER
   ```

7. **Position nodes (optional):**
   ```python
   n[0].set_node_position(300, 0)   # Get Spline
   n[1].set_node_position(600, 0)   # Sampler
   n[2].set_node_position(900, -150)  # Transform Left
   n[3].set_node_position(900, 150)   # Transform Right
   n[4].set_node_position(1200, 0)  # Spawner
   # NO CODE AFTER
   ```

8. **UI Configuration (REQUIRED):**
   - Open `/Game/PCG/PCG_RoadEnvironment` in Unreal
   - Verify Get Spline Data node: Actor Selection = "By Class", Class = "Landscape"
   - Select Static Mesh Spawner node
   - Details panel -> Mesh Entries -> Add mesh (street lamp, sign, etc.)
   - Drag graph into level -> Should auto-detect landscape spline!

**Key Settings:**
- **Actor Selection:** `BY_CLASS` (not ALL_WORLD_ACTORS for landscape splines)
- **Actor Selection Class:** `Landscape`
- **Distance Increment:** 1000 = 10m spacing (500 = 5m for dense)
- **Offset:** 900 = 9m from road centerline (adjust for road width)
- **Absolute Scale:** True (prevents point shape deformation)

**Variations:**

**Forest Road:**
```python
# Dense trees on one side
left_settings.offset_min = unreal.Vector(0, -1500, 0)
sampler_params.distance_increment = 300.0  # 3m spacing
```

**Desert Highway:**
```python
# Sparse cacti/rocks far from road
left_settings.offset_min = unreal.Vector(0, -2000, 0)
sampler_params.distance_increment = 2000.0  # 20m spacing
```

**City Street:**
```python
# Close street lamps
left_settings.offset_min = unreal.Vector(0, -600, 0)
sampler_params.distance_increment = 800.0  # 8m spacing
```

**Output:** Props spawned along both sides of landscape spline road

**Reference:** YouTube tutorial "How To Make Roads with Landscape Splines"

---

## Workflow 7: Modify Existing Graph

**Steps:**
1. **Load existing graph:**
   ```python
   import unreal
   g = unreal.load_asset('/Game/PCG/ExistingGraph')
   ```

2. **List current nodes:**
   ```python
   print(f"Graph has {len(g.nodes)} nodes")
   for i, node in enumerate(g.nodes):
       print(f"{i}: {type(node.get_settings()).__name__}")
   ```

3. **Add new node to middle of chain:**
   ```python
   new_node, new_settings = g.add_node_of_type(unreal.PCGFilterByTagSettings)
   new_settings.tag_filter = "MyTag"
   ```

4. **Remove old connection (if needed):**
   ```python
   # Note: remove_edge requires exact pin names
   g.remove_edge(g.nodes[2], unreal.Name("Out"), g.nodes[3], unreal.Name("In"))
   ```

5. **Add new connections:**
   ```python
   g.add_edge(g.nodes[2], unreal.Name("Out"), new_node, unreal.Name("In"))
   g.add_edge(new_node, unreal.Name("Out"), g.nodes[3], unreal.Name("In"))
   ```

**Output:** Modified graph with new node inserted

**Warning:** Always query pins before modifying connections

---

**End of Workflows Reference**
