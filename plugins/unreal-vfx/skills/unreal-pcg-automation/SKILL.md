---
name: unreal-pcg-automation
description: Verified UE 5.8 PCG Python traps - add_edge with a wrong pin label adds no edge and raises nothing, pin.label is protected (read it via properties), mesh entries ARE settable but descriptor needs get_editor_property, count instances on the volume ISM. Use when wiring PCG graph nodes, setting Static Mesh Spawner meshes, or checking what a PCG graph generated.
allowed-tools: mcp__ue58-mcp__execute_python_code,mcp__ue58-mcp__call_tool
metadata:
  version: 3.0.0
  updated: 2026-11-09
---

# Unreal PCG Automation - traps

Measured in UE 5.8.0 (editor probes + unreal-round2 pcg1/pcg2, 2026-11-08; unreal-round3 pcg3 traces,
2026-11-09; ClaudeCode/evals/unreal-round3/ANALYSIS.md, obs 448). Step 0 for any approved plan:
`unreal-project-preflight` (feature `pcg`).

1. **A wrong pin label silently adds NO edge.** Wrong: `graph.add_edge(a, "Out", density_filter, "InsideFilter")`
   - returns, raises nothing, wires nothing, and the spawner makes 0 instances. Right: `node, settings =
   graph.add_node_of_type(unreal.PCGTransformPointsSettings)` (a tuple), then `graph.add_edge(n1, "Out", n2,
   "In")` with labels you have read (trap 2). Code after `add_edge` in the same call is fine (round 3 printed the
   edge count right after wiring). Verify: `len(graph.get_all_edges())` equals the edges you meant to add.

2. **`pin.label` is protected - read pin names through `properties`.** Wrong: `pin.get_editor_property("label")`
   or `pin.label` - "PCGPin: Property 'Label' ... is protected and cannot be read" (both round-3 with-skills
   runs). Right (worked in round 3):
   `[p.get_editor_property("properties").get_editor_property("label") for p in node.get_editor_property("input_pins")]`
   and the same over `"output_pins"`. The list includes parameter override pins (`Overrides`, `Seed`, ...); the
   data pins read `In` / `Out` on Transform Points and Static Mesh Spawner, and Create Points Grid has `Out` but
   no `In`.

3. **Mesh entries CAN be set from Python** (the old "UI only since 5.4" claim is false), but entry structs need
   `get_editor_property`. Wrong: `entry.descriptor.static_mesh` - AttributeError (round 3). Right:
   ```python
   e = unreal.PCGMeshSelectorWeightedEntry(); d = e.get_editor_property("descriptor")
   d.set_editor_property("static_mesh", unreal.load_asset("/Engine/BasicShapes/Cube")); e.set_editor_property("descriptor", d)
   s.get_editor_property("mesh_selector_parameters").set_editor_property("mesh_entries", [e])   # s = spawner settings
   ```
   Verify: `s.get_editor_property("mesh_selector_parameters").get_editor_property("mesh_entries")[0]
   .get_editor_property("descriptor").get_editor_property("static_mesh")` is the mesh.

4. **Judge a graph by what it generated, not by the build call.** Right: spawn a `unreal.PCGVolume`, take its
   PCG component, `comp.set_graph(graph)`, `comp.generate(True)`; in the NEXT call count
   `InstancedStaticMeshComponent.get_instance_count()` on the volume actor and read instance transforms
   (round 3: 8 instances at z 250, scale 0.5). A dropped edge (trap 1) shows up here as 0 instances.

5. **Create Points `points_to_create` takes `unreal.PCGPoint`** objects with `density` and `transform` set
   (round 2, generation read back 3 instances).
