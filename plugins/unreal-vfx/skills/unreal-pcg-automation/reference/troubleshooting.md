# PCG Troubleshooting Guide

**Version:** 1.5.0
**Last Updated:** 2025-11-17
**Context:** Complete troubleshooting reference for PCG automation

Extended troubleshooting issues extracted from unreal-pcg-automation skill.

---

## Quick Reference

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Connection doesn't appear | String literals instead of unreal.Name() | Use unreal.Name() |
| Timeout on add_edge | Silent Execution (normal) | Proceed to next phase |
| AttributeError: tuple | Not unpacking add_node_of_type() | Unpack: `node, settings =` |
| Property not found | Nested in parameter struct | Check for `_params` properties |
| Property verification fails | Timeout != success | Always verify critical properties |

---

## Top 3 Issues (Quick Reference)

For the most common issues, see SKILL.md. The issues below are less common but still important.

---

## Issue 4: Settings Property Not Found

**Symptom:** `AttributeError: 'PCGSplineSamplerSettings' object has no attribute 'distance_increment'`

**Cause:** Settings properties are nested in parameter structs

**Fix:**
```python
# [FAIL] WRONG - Direct property access
sampler_settings.distance_increment = 100.0  # Doesn't exist!

# [OK] CORRECT - Nested in sampler_params
sampler_settings.sampler_params.distance_increment = 100.0  # Works!
```

**Discovery pattern:**
```python
# List all properties
props = [p for p in dir(settings) if not p.startswith('_')]
for prop in props:
    print(prop)

# Look for nested structs (often end in _params, _properties, etc.)
```

**Common nested structures:**
- `sampler_params` - Spline Sampler settings
- `projection_params` - Projection settings
- `spawn_params` - Spawn Actor settings
- `actor_selector` - Actor selection settings

**Prevention:** Always inspect settings properties before setting values.

---

## Issue 5: Graph Not Updating in UI

**Symptom:** Changes made via Python don't appear in Unreal Editor UI

**Cause:** Asset not marked dirty or editor not refreshed

**Fix:**
```python
import unreal

# After making changes to graph
graph = unreal.load_asset('/Game/PCG/MyGraph')

# Mark asset as modified
unreal.EditorAssetLibrary.save_loaded_asset(graph)

# Or force save
unreal.EditorAssetLibrary.save_asset('/Game/PCG/MyGraph')
```

**Alternative:** Close and reopen the graph in Unreal Editor

---

## Issue 6: Pin Name Case Sensitivity

**Symptom:** Connection works in some cases but not others

**Cause:** Pin names are case-sensitive

**Fix:**
```python
# [FAIL] WRONG - Wrong case
g.add_edge(node1, unreal.Name("out"), node2, unreal.Name("in"))  # Fails!

# [OK] CORRECT - Exact case match
g.add_edge(node1, unreal.Name("Out"), node2, unreal.Name("In"))  # Works!
```

**Discovery pattern:**
```python
# Always query exact pin names
for pin in node.output_pins:
    print(f"Output: '{pin.properties.label}'")  # Note exact casing
```

**Prevention:** Never guess pin names, always query them first.

---

## Issue 7: Node Position Doesn't Update

**Symptom:** `set_node_position()` executes but node stays in same place

**Cause:** Position set before node is fully initialized

**Fix:**
```python
# [FAIL] WRONG - Set position immediately after creation
node, settings = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)
node.set_node_position(300, 0)  # May not stick!

# [OK] CORRECT - Set position in separate phase
# Phase 1: Add all nodes
node1, _ = graph.add_node_of_type(unreal.PCGSplineSamplerSettings)
node2, _ = graph.add_node_of_type(unreal.PCGTransformPointsSettings)

# Phase 2: Position nodes (separate script or after delay)
graph = unreal.load_asset('/Game/PCG/MyGraph')
graph.nodes[0].set_node_position(300, 0)
graph.nodes[1].set_node_position(600, 0)
```

**Prevention:** Separate node creation from positioning into different scripts.

---

## Issue 8: Mesh Spawner Not Spawning

**Symptom:** Mesh spawner node connected but no meshes appear

**Cause:** No meshes configured (Python API limitation)

**Fix:**
```python
# Python can create spawner but NOT configure meshes (UE 5.4+)

# Step 1: Create graph structure via Python
spawner, _ = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)

# Step 2: Configure meshes manually in UI (REQUIRED)
# Open graph -> Select spawner -> Details -> Mesh Entries -> Add mesh
```

**See Also:** [api_limitations.md](api_limitations.md) for full explanation

---

## Issue 9: Unbounded Setting Ignored

**Symptom:** Spline sampler only works inside PCG Volume bounds

**Cause:** `unbounded` property not set correctly

**Fix:**
```python
# [FAIL] WRONG - Property path incorrect
sampler_settings.unbounded = True  # Doesn't exist at this level!

# [OK] CORRECT - Nested in sampler_params
sampler_settings.sampler_params.unbounded = True  # Works!
```

**Verification:**
```python
# Read back to confirm
graph = unreal.load_asset('/Game/PCG/MyGraph')
settings = graph.nodes[1].get_settings()
print(f"Unbounded: {settings.sampler_params.unbounded}")
```

---

## Issue 10: Difference Node Doesn't Exclude Points

**Symptom:** Difference node connected but no points excluded

**Cause:** Difference mode set to MINIMUM instead of BINARY

**Fix:**
```python
# [FAIL] WRONG - MINIMUM mode (default) doesn't exclude
diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.MINIMUM)

# [OK] CORRECT - BINARY mode for exclusion
diff_settings.set_editor_property('density_mode', unreal.PCGDifferenceMode.BINARY)
```

**Modes:**
- `MINIMUM` - Takes minimum density (doesn't exclude completely)
- `BINARY` - Binary subtraction (full exclusion)

**Use BINARY for:** Point exclusion, clearings, road exclusions
**Use MINIMUM for:** Density blending, soft transitions

---

## Issue 11: Actor Selector Not Finding Landscape Spline

**Symptom:** Get Spline Data node can't find landscape spline

**Cause:** Wrong actor selection mode or class

**Fix:**
```python
# For LANDSCAPE SPLINES (not regular spline actors):

actor_selector = get_spline_settings.actor_selector

# MUST use BY_CLASS for landscape splines
actor_selector.actor_selection = unreal.PCGActorSelection.BY_CLASS
actor_selector.actor_selection_class = unreal.Landscape  # Not LandscapeSplineActor!

# [WARN] Verify settings stuck (see property_verification.md)
```

**For REGULAR SPLINE ACTORS:**
```python
# Use ALL_WORLD_ACTORS + tag
spline_settings.set_editor_property('actor_filter', unreal.PCGActorFilter.ALL_WORLD_ACTORS)
spline_settings.set_editor_property('actor_selection_tag', "YourTag")
```

**See Also:** [property_verification.md](property_verification.md)

---

## Issue 12: Performance Degradation with Many Points

**Symptom:** Graph execution slow or freezes editor

**Cause:** Too many points generated, excessive mesh spawning

**Fix:**

**Optimization 1: Reduce surface sampler density**
```python
# Before: 5.0 pts/m^2 (very dense)
sampler_settings.points_per_squared_meter = 5.0  # Slow!

# After: 0.5 pts/m^2 (optimized)
sampler_settings.points_per_squared_meter = 0.5  # Faster!
```

**Optimization 2: Use Density Filter**
```python
# Single dense source -> filtered variations (34% faster)
sampler_settings.points_per_squared_meter = 2.0
# Then use PCGDensityFilterSettings to thin out
```

**Optimization 3: Enable distance culling**
```python
# Cull points beyond certain distance
distance_cull, cull_s = graph.add_node_of_type(unreal.PCGDistanceCullSettings)
cull_s.max_distance = 10000.0  # 100m
```

**Benchmark:**
- 0.1 pts/m^2 = ~10ms execution (sparse)
- 1.0 pts/m^2 = ~50ms execution (medium)
- 5.0 pts/m^2 = ~250ms execution (dense)

---

## Debugging Workflow

**Step 1: Check Unreal Output Log**
```python
import os, glob

log_dir = "<workspace>/UnrealEngine/MCPGameProject/Saved/Logs"
logs = glob.glob(f"{log_dir}/*.log")
latest_log = max(logs, key=os.path.getmtime)

# Read last 100 lines for errors
with open(latest_log, 'r', encoding='utf-8') as f:
    for line in f.readlines()[-100:]:
        if 'LogPCG' in line or 'Error' in line or 'Warning' in line:
            print(line.strip())
```

**Step 2: Verify Property Values**
```python
# Read back properties to confirm they stuck
graph = unreal.load_asset('/Game/PCG/MyGraph')
settings = graph.nodes[0].get_settings()

# Print all properties
props = [p for p in dir(settings) if not p.startswith('_')]
for prop in props:
    try:
        value = getattr(settings, prop)
        if not callable(value):
            print(f"{prop}: {value}")
    except:
        pass
```

**Step 3: Test Graph Incrementally**
```python
# Add nodes one at a time, test after each
# Isolate which node causes the issue
```

**Step 4: Check Pin Connections**
```python
# List all edges in graph
for node in graph.nodes:
    for out_pin in node.output_pins:
        for edge in out_pin.edges:
            print(f"{node} -> {edge.input_pin.node}")
```

---

## Common Error Messages

**"From node MyNode does not have the Out label"**
- **Cause:** Wrong pin name or not using unreal.Name()
- **Fix:** Query pin names, use unreal.Name()

**"Cannot add edge: Incompatible pin types"**
- **Cause:** Connecting incompatible data types
- **Fix:** Check node documentation for valid pin connections

**"PCG graph execution failed"**
- **Cause:** Runtime error in node settings
- **Fix:** Check Unreal Output Log for specific error

**"Property 'meshes' not found"**
- **Cause:** Using deprecated API (UE 5.4+)
- **Fix:** See [api_limitations.md](api_limitations.md)

---

**See Also:**
- [property_verification.md](property_verification.md) - Verification workflow
- [api_limitations.md](api_limitations.md) - Known Python API constraints
- SKILL.md - Top 3 most common issues

---

**End of Troubleshooting Guide**
