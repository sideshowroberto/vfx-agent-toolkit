---
name: unreal-pcg-automation
description: Automate PCG (Procedural Content Generation) graph creation, node configuration, and asset integration in Unreal Engine 5.8. Use when creating PCG graphs, configuring nodes, debugging PCG, or when user mentions pcg, procedural generation, pcg graph, scatter, pcg node, procedural content, point cloud.
allowed-tools: mcp__ue58-mcp__execute_python_code,mcp__ue58-mcp__call_tool,Read,Write,Grep
---

# unreal-pcg-automation

**Skill Version:** 2.0.0
**Last Updated:** 2026-07-06
**Dependencies:** Unreal Engine 5.8+, UE 5.8 native MCP (HTTP, port 8000)
**Status:** Production-ready

---

## Execution Model: Direct MCP Connection

**CRITICAL:** This skill assumes Claude Code is **connected to a running Unreal Engine instance via native MCP**.

**What This Means:**
- Execute Python directly in Unreal using `mcp__ue58-mcp__execute_python_code`
- NO script generation - execute immediately
- Check Unreal Output Log for results (see Debugging section)
- Use multi-phased execution for complex graphs (see below)

**Multi-Phased Workflow Pattern:**

For complex PCG graphs, use **3 separate executions** to avoid crashes and timeouts:

```python
# PHASE 1: Create all nodes (separate execution)
graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(...)
node1, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
node2, _ = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
# ... create all nodes
print(f"Created {len(graph.nodes)} nodes")

# PHASE 2: Connect all nodes (separate execution)
graph = unreal.load_asset('/Game/PCG/MyGraph')
graph.add_edge(graph.nodes[0], unreal.Name("Out"), graph.nodes[1], unreal.Name("Surface"))
# ... all connections (NO CODE AFTER LAST add_edge!)

# PHASE 3: Configure properties (separate execution)
graph = unreal.load_asset('/Game/PCG/MyGraph')
s1 = graph.nodes[1].get_settings()  # Use .get_settings() for existing graphs
s1.points_per_squared_meter = 0.05
# ... all property configurations
print("Configuration complete")
```

**Why 3 Phases:**
- Overwrite popups can interrupt node creation
- `add_edge()` triggers async validation (Silent Execution)
- Settings access differs between creation vs existing graphs

---

## UE 5.4+ BREAKING CHANGE: Landscape Input

**CHANGED:** Input node no longer has "Landscape" output pin

**5.4+ (Current Pattern):**
```python
# Must use Get Landscape Data node
get_landscape, _ = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
graph.add_edge(get_landscape, unreal.Name("Out"), surface_sampler, unreal.Name("Surface"))
```

**Impact:** All landscape scatter workflows now require `PCGGetLandscapeSettings` node.

---

## CRITICAL: Unreal Uses Z-Up Coordinate System

**PROBLEM:** Unreal uses Z-axis as UP (not Y like most 3D software)

**Impact on Rotations:**

```python
# unreal.Rotator(X, Y, Z) - Direct axis rotations!
# - X rotation (1st param) = rotation around X axis (roll/tilt)
# - Y rotation (2nd param) = rotation around Y axis (pitch forward/back)
# - Z rotation (3rd param) = rotation around Z axis (vertical spin - UP in Z-up!)
```

**Common Mistake: Random Rotation Around Vertical Axis**

```python
# WRONG - This is what you'd do in Y-up software (Blender, Maya)
settings.rotation_max = unreal.Rotator(0, 360, 0)  # Y rotation = pitching!

# CORRECT - For random vertical spin in Z-up Unreal
settings.rotation_max = unreal.Rotator(0, 0, 360)  # Z rotation = vertical spin
```

**Quick Reference:**
- **Vertical rotation (trees/rocks spinning):** `Rotator(0, 0, 360)` - Z axis
- **Forward/back tilt:** `Rotator(0, 360, 0)` - Y axis
- **Side-to-side tilt:** `Rotator(360, 0, 0)` - X axis

---

## Reference Documentation

**[Advanced Patterns](reference/advanced_patterns.md)** - INFERRED mode, multi-input exclusions, noise workflow
**[Common Nodes](reference/common_nodes.md)** - 25+ PCG node types, properties, pin names
**[Advanced Nodes](reference/advanced_nodes.md)** - 8 production nodes (SelfPruning, Collapse, etc.)
**[Workflows](reference/workflows.md)** - 7 complete workflows (scatter, exclusion, road system)
**[Production Patterns](reference/production_patterns.md)** - Multi-layer vegetation, external assets
**[Troubleshooting](reference/troubleshooting.md)** - 12 common issues with solutions
**[API Limitations](reference/api_limitations.md)** - Python API constraints and workarounds
**[Property Verification](reference/property_verification.md)** - Timeout != Success workflow
**[Pin Discovery](reference/pin_discovery_patterns.md)** - Find pin names, avoid connection errors
**[Silent Execution](reference/silent_execution_deep_dive.md)** - Async execution patterns
**[Landscape Scatter](reference/landscape_scatter_workflow.md)** - UE 5.4+ landscape patterns
**[Complete Templates](reference/complete_graph_template.md)** - Working PCG examples

---

## Quick Start

### Create PCG Graph
```python
import unreal

# Create graph
graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    asset_name="PCG_MyGraph", package_path="/Game/PCG",
    asset_class=unreal.PCGGraph, factory=unreal.PCGGraphFactory()
)

# Add nodes and configure
node1, s1 = graph.add_node_of_type(unreal.PCGGetLandscapeSettings)
node2, s2 = graph.add_node_of_type(unreal.PCGSurfaceSamplerSettings)
s2.points_per_squared_meter = 0.1  # Configure immediately during creation

# Connect (NO CODE AFTER!)
graph.add_edge(node1, unreal.Name("Out"), node2, unreal.Name("Surface"))
```

### Configure Existing Graph
```python
graph = unreal.load_asset('/Game/PCG/MyGraph')
s = graph.nodes[1].get_settings()  # Use .get_settings() for existing graphs
s.points_per_squared_meter = 0.05
```

**See:** [workflows.md](reference/workflows.md) for 7 complete workflows

---

## Property Verification

**CRITICAL:** Timeout != Success! Silent Execution timeouts mean "async started", not "operation succeeded".

**Verify complex properties in separate script:**
```python
graph = unreal.load_asset('/Game/PCG/MyGraph')
settings = graph.nodes[0].get_settings()
print(f"Verified: {settings.actor_selector.actor_selection}")
```

**Verify:** Actor selectors, nested properties
**Don't need to verify:** Simple numerics, vectors, booleans

---

## Research & API Documentation

**Two-Source Approach:**

1. **Context7** (Primary) - Official Epic docs, validate properties/classes
2. **Brave Search** - Community examples, workarounds, version issues

---

## Debugging: Unreal Output Log

**CRITICAL:** `print()` statements execute in Unreal Engine and output to **Unreal Output Log**, NOT MCP response!

**ALWAYS check the file with the latest timestamp** - active session creates new log file.

### Find and Read Latest Log

**RECOMMENDED: Use Desktop Commander (fastest)**
```python
mcp__desktop-commander__read_file(
    path="<project>/Saved/Logs/<project>.log",
    offset=-30  # Last 30 lines
)
```

**Look for:** `LogPython:` lines showing print() output, `LogTemp:` for execution status

---

## Top 3 Troubleshooting Issues

**For complete troubleshooting guides, see:** `reference/troubleshooting.md` (12 issues)

1. **Connection Doesn't Appear in Graph** - Use `unreal.Name()` not strings, verify pin names with `node.input_pins`
2. **Silent Execution Timeout** - Don't execute code after `add_edge()`, async graph validation blocks Python access
3. **AttributeError: 'tuple' object** - Unpack tuple from `add_node_of_type()`: `node, settings = graph.add_node_of_type(...)`

---

## Python API Limitations (Summary)

### Static Mesh Spawner Mesh Entries (UE 5.4+)

**CONFIRMED:** Mesh entries CANNOT be configured via Python API in UE 5.4+

**Required Workflow: Hybrid Python + UI**

1. **Python Phase (Automated):**
   - Create graph structure, add/position/connect nodes
   - Configure Transform Points (scale/rotation randomization)

2. **UI Phase (Manual - Required):**
   - Configure Surface Sampler density
   - Add mesh entries to Static Mesh Spawner
   - Select meshes and set weights

**See:** [api_limitations.md](reference/api_limitations.md)

---

## Advanced Multi-Layer Patterns

For complex vegetation systems with natural distribution:

**1. Difference Mode: INFERRED** (not DISCRETE)
```python
diff_s.mode = unreal.PCGDifferenceMode.INFERRED
```

**2. Multi-Input Cascading Exclusions**
```python
# All connect to SAME "Differences" pin
graph.add_edge(bounds_1, unreal.Name("Out"), diff_3, unreal.Name("Differences"))
graph.add_edge(bounds_2, unreal.Name("Out"), diff_3, unreal.Name("Differences"))
graph.add_edge(diff_2, unreal.Name("Out"), diff_3, unreal.Name("Differences"))
```

**3. Density Variation with Noise**
```python
# collapse -> noise -> density_filter -> transform -> spawner
graph.add_edge(collapse, unreal.Name("Out"), noise, unreal.Name("In"))
graph.add_edge(noise, unreal.Name("Out"), density_filter, unreal.Name("In"))
```

**See:** [advanced_patterns.md](reference/advanced_patterns.md)

---

## Constitutional Compliance

**Article I:** All scripts are parameterized (no hardcoded paths)
**Article III:** SKILL.md under 500 lines, progressive disclosure through reference files
**Article VI:** On-demand loading through progressive disclosure
**Article VIII:** Complete YAML frontmatter, all required sections

## Version History

**v2.0.0** (2026-07-06) - UE 5.8 Migration
- Migrated from community MCP (localhost:55557) to UE 5.8 native MCP (HTTP, port 8000)
- Updated allowed-tools to mcp__ue58-mcp__execute_python_code + call_tool
- Removed all references to old unreal-mcp server
- Updated description from "5.5" to "5.8"

**v1.6.0** (2025-11-20) - Execution-First Workflow & Production Validation
- Execution Model, Multi-Phased Workflow, Advanced Multi-Layer Patterns
- Z-up coordinate system, Settings access patterns, Property verification

**v1.5.0** (2025-11-17) - Major Refactoring: Progressive Disclosure
- Reduced SKILL.md from 1,128 to 321 lines (72% reduction)

**v1.0.0** (2025-10-26) - Initial Release
- PCG graph builder pattern, Silent Execution, pin discovery
