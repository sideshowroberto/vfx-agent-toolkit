---
name: unreal-blueprint-automation
description: Verified UE 5.8 Blueprint Python traps - bp.simple_construction_script and KismetSystemLibrary do not exist (use VibeUE BlueprintService), variables from add_member_variable are not instance-editable until set_blueprint_variable_instance_editable, EdGraphPinType(...) resets the MCP. Use when creating a Blueprint, adding components or variables, or setting per-instance values.
allowed-tools: mcp__ue58-mcp__execute_python_code,mcp__ue58-mcp__call_tool
metadata:
  version: 3.0.0
  updated: 2026-11-09
---

# Unreal Blueprint Automation - traps

Measured in UE 5.8.0 with VibeUE (editor probes + unreal-round2 bp1, 2026-11-08; unreal-round3 bp2,
2026-11-09; ClaudeCode/evals/unreal-round3/ANALYSIS.md, obs 447). Step 0 for any approved plan:
`unreal-project-preflight` (VibeUE is the `vibeue` feature).

1. **The SCS route is gone in 5.8.** Wrong: `bp.simple_construction_script`, `scs.create_node(...)`,
   `unreal.KismetSystemLibrary.compile_blueprint(bp)` - `Blueprint` has no such attribute and the module has no
   KismetSystemLibrary. Right (the route that cut round-3 UE calls 8.5 -> 5 and errors 2 -> 0.5):
   ```python
   import unreal
   f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.Actor)   # set the parent explicitly
   bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset("BP_X", "/Game/Blueprints", unreal.Blueprint, f)
   P = "/Game/Blueprints/BP_X"
   bs = unreal.BlueprintService                                  # VibeUE
   bs.add_component(P, "SceneComponent", "Pivot")                # first scene component becomes the root
   bs.add_component(P, "StaticMeshComponent", "Blade", "Pivot")  # 4th arg = parent component
   bs.set_component_property(P, "Blade", "StaticMesh", "/Engine/BasicShapes/Cube.Cube")
   bs.set_component_property(P, "Blade", "RelativeScale3D", "(X=2,Y=0.2,Z=0.1)")
   unreal.BlueprintEditorLibrary.compile_blueprint(bp)
   ```
   Verify: `bs.get_component_hierarchy(P)` (root + attach_parent), `bs.get_component_property(P, "Blade",
   "RelativeScale3D")`, and `bp.status == BlueprintStatus.BS_UP_TO_DATE`.

2. **Variables from `add_member_variable` are NOT instance-editable** (obs 447; 3 of 4 round-3 runs, both
   arms). Wrong: spawn, then `actor.set_editor_property("SpinSpeed", 180.0)` - raises "Property 'SpinSpeed' ...
   cannot be edited on instances". Right: `bel.set_blueprint_variable_instance_editable(bp, "SpinSpeed", True)`
   for each per-instance variable, compile, THEN set the value on the placed actor. Verify on the INSTANCE:
   `actor.get_editor_property("SpinSpeed")` reads 180 while the CDO still reads its default, and
   `bs.get_variable_info(P, "SpinSpeed")` shows `is_instance_editable: True`.

3. **Build pin types with `get_basic_type_by_name`, never `EdGraphPinType(...)`.** Wrong:
   `unreal.EdGraphPinType(pin_category="real", ...)` - the first call closed the MCP socket (ECONNRESET), a retry
   was refused as "Blocked unsafe Python code". Right: `bel = unreal.BlueprintEditorLibrary`;
   `bel.add_member_variable(bp, "SpinSpeed", bel.get_basic_type_by_name("real"))` (float/double) and
   `bel.get_basic_type_by_name("int")`; both return True.

4. **Class defaults go on the Blueprint, per-instance values on the actor.** Right: `bs.set_variable_default_value(P,
   "SpinSpeed", "90.0")` (value as a string), compile, read
   `unreal.get_default_object(bp.generated_class()).get_editor_property("SpinSpeed")`. Setting 180 on the CDO
   instead of the instance is the plausible-wrong answer the round-3 checker fails. Spawn with
   `unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(bp.generated_class(), loc, rot)`.

5. **Python after `compile_blueprint` does not crash in 5.8** - the old "Silent Execution: no code after
   compile" rule was not reproduced in any probe or run. Compile and read back `bp.status` in the same call;
   never skip the read-back.
