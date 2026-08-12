# Complete PCG Graph Creation Template

**Copy-Paste Ready Workflow**
**Performance:** ~10ms total execution time

---

## Phase 1: Create Graph + Add Nodes + Position

```python
import unreal

# Create graph
graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_YourGraphName",
    package_path="/Game/PCG",
    asset_class=unreal.PCGGraph,
    factory=unreal.PCGGraphFactory()
)

# Add nodes (returns tuple: node, settings)
get_spline, _ = graph.add_node_of_type(unreal.PCGGetSplineSettings)
sampler, sampler_s = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)
get_land, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
projection, _ = graph.add_node_of_type(unreal.PCGProjectionSettings)
transform, transform_s = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
spawn, _ = graph.add_node_of_type(unreal.PCGSpawnActorSettings)

# Position nodes in Y-pattern (readable layout)
get_spline.set_node_position(-600, -100)   # Top left
sampler.set_node_position(-300, -100)      # Top center-left
get_land.set_node_position(-600, 100)      # Bottom left
projection.set_node_position(0, 0)         # Center (dual input)
transform.set_node_position(300, 0)        # Center-right
spawn.set_node_position(600, 0)            # Right
```

---

## Phase 2: Configure Settings

```python
import unreal

g = unreal.load_asset('/Game/PCG/PCG_YourGraphName')
n = g.nodes

# Configure Spline Sampler (spacing between points)
n[1].get_settings().sampler_params.distance_increment = 100.0  # 1m spacing

# Configure Transform Points (offset depth)
n[4].get_settings().offset_min = unreal.Vector(0, 0, -30)  # 30cm below surface
n[4].get_settings().offset_max = unreal.Vector(0, 0, -30)  # Consistent depth

# Configure Spawn Actor (Blueprint template)
# NOTE: Requires Blueprint to exist first!
# bp = unreal.load_asset('/Game/Blueprints/BP_LandscapePatch')
# n[5].get_settings().template_actor_class = bp.generated_class()
```

---

## Phase 3: Query Pin Names (Optional - First Time Only)

```python
import unreal

g = unreal.load_asset('/Game/PCG/PCG_YourGraphName')

# Query specific node to verify pin names
node = g.nodes[3]  # Projection node
print("Projection inputs:")
for pin in node.input_pins:
    print(f"  {pin.properties.label}")

# Output:
# In
# Projection Target
# Overrides
# ...
```

---

## Phase 4: Connect Nodes (Silent Execution)

```python
import unreal
g = unreal.load_asset('/Game/PCG/PCG_YourGraphName')
o = g.get_output_node()
n = g.nodes

# CRITICAL: Use unreal.Name() for ALL pin labels!
g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Spline"))
g.add_edge(n[1], unreal.Name("Out"), n[3], unreal.Name("In"))
g.add_edge(n[2], unreal.Name("Out"), n[3], unreal.Name("Projection Target"))
g.add_edge(n[3], unreal.Name("Out"), n[4], unreal.Name("In"))
g.add_edge(n[4], unreal.Name("Out"), n[5], unreal.Name("In"))
g.add_edge(n[5], unreal.Name("Out"), o, unreal.Name("Out"))

# NO CODE AFTER THIS - Silent Execution!
```

---

## Node Position Reference

### Y-Pattern Layout (Dual Input Convergence)

```
Get Spline (-600, -100) -> Sampler (-300, -100) +
                                                 +-> Projection (0, 0) -> Transform (300, 0) -> Spawn (600, 0) -> Output
Get Landscape (-600, 100) ----------------------+
```

**Spacing:**
- Horizontal: 300 units
- Vertical: 200 units
- Related nodes: 100-150 units

### Horizontal Layout (Linear Chain)

```
Node1 (-400, 0) -> Node2 (0, 0) -> Node3 (400, 0)
```

**Use for:** Simple linear processing chains

---

## Common Parameter Values

### Spline Sampler - Distance Increment
- **Roads:** 100-200cm (1-2m spacing)
- **Rivers:** 50-100cm (0.5-1m spacing)
- **Vegetation:** 200-500cm (2-5m spacing)

### Transform Points - Z Offset
- **Roads:** -30 to -50cm (carve shallow)
- **Rivers:** -50 to -100cm (carve deep)
- **Paths:** -10 to -20cm (subtle)
- **Berms/Walls:** +20 to +50cm (raise)

### Projection - Settings
- **Projection Target:** Usually from Get Landscape Data
- **Ray Origin:** ABOVE (project downward)
- **Target:** LANDSCAPE

---

## Performance Expectations

**Complete 6-Node Graph:**
- Phase 1 (Create + Add + Position): 2-6ms
- Phase 2 (Configure): 0.3-0.5ms
- Phase 4 (6 Connections): 1-2ms
- **Total: ~10ms**

---

## Troubleshooting Checklist

Before running scripts, verify:

- [ ] Graph name is unique (won't overwrite existing)
- [ ] Blueprint exists (if using Spawn Actor template)
- [ ] Pin labels use `unreal.Name()`
- [ ] No code after `add_edge()` calls
- [ ] Phases run as separate scripts

**After Phase 4:**
- [ ] Open graph in UI to verify connections
- [ ] Check Unreal Output Log for errors
- [ ] No "LogPCG: Error" messages = success!

---

## Quick Verification

```python
# After Phase 4, verify graph in separate script
import unreal
g = unreal.load_asset('/Game/PCG/PCG_YourGraphName')
print(f"Nodes: {len(g.nodes)}")
print(f"Expected: 6 nodes")
# Open graph in UI to visually verify connections
```

---

## Complete Example: Road Generation Graph

**Graph:** Creates road along spline with 1m spacing, 30cm carve depth

**Phase 1:**
```python
import unreal
graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_RoadGenerator",
    package_path="/Game/PCG",
    asset_class=unreal.PCGGraph,
    factory=unreal.PCGGraphFactory()
)
get_spline, _ = graph.add_node_of_type(unreal.PCGGetSplineSettings)
sampler, sampler_s = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)
get_land, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
projection, _ = graph.add_node_of_type(unreal.PCGProjectionSettings)
transform, transform_s = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
spawn, _ = graph.add_node_of_type(unreal.PCGSpawnActorSettings)

get_spline.set_node_position(-600, -100)
sampler.set_node_position(-300, -100)
get_land.set_node_position(-600, 100)
projection.set_node_position(0, 0)
transform.set_node_position(300, 0)
spawn.set_node_position(600, 0)
```

**Phase 2:**
```python
import unreal
g = unreal.load_asset('/Game/PCG/PCG_RoadGenerator')
n = g.nodes
n[1].get_settings().sampler_params.distance_increment = 100.0
n[4].get_settings().offset_min = unreal.Vector(0, 0, -30)
n[4].get_settings().offset_max = unreal.Vector(0, 0, -30)
```

**Phase 4:**
```python
import unreal
g = unreal.load_asset('/Game/PCG/PCG_RoadGenerator')
o = g.get_output_node()
n = g.nodes
g.add_edge(n[0], unreal.Name("Out"), n[1], unreal.Name("Spline"))
g.add_edge(n[1], unreal.Name("Out"), n[3], unreal.Name("In"))
g.add_edge(n[2], unreal.Name("Out"), n[3], unreal.Name("Projection Target"))
g.add_edge(n[3], unreal.Name("Out"), n[4], unreal.Name("In"))
g.add_edge(n[4], unreal.Name("Out"), n[5], unreal.Name("In"))
g.add_edge(n[5], unreal.Name("Out"), o, unreal.Name("Out"))
```

**Result:** Production-ready road generation graph in ~10ms!

---

## Related Documentation

**Main Skill:** `.claude/skills/unreal-pcg-automation/SKILL.md`
**Session:** `UnrealEngine/unreal-mcp-main/development/Session_2025-10-26_PCG_LandscapeDeformation.md`
**Test Assets:** `/Game/PCG/PCG_LandscapeDeform_Clean` (working example)
