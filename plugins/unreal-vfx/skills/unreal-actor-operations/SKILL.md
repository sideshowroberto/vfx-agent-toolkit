---
name: unreal-actor-operations
description: Spawn, manipulate, and query actors in Unreal Engine via Python. Use when spawning actors, setting transforms, getting/setting properties, or when user mentions "actor", "spawn", "transform", "location", "rotation", "static mesh actor", "blueprint actor".
allowed-tools: mcp__ue58-mcp__execute_python_code,mcp__ue58-mcp__call_tool
---

# Unreal Actor Operations

**Version:** 2.0.0
**Last Updated:** 2026-07-06
**Dependencies:** Unreal Engine 5.8+, UE 5.8 native MCP (HTTP, port 8000), VibeUE plugin (optional)
**Context7 Validation:** ACTOR_API_VALIDATION_REPORT.md (18/20 APIs validated)

## CRITICAL: MCP Connection Required

**BEFORE any actor operations:**
1. Verify UE editor is open with project loaded (MCP server runs inside the editor)
2. Native MCP auto-starts on port 8000 when `bAutoStartServer=True` in project config
3. All Python execution happens on game thread (synchronous)

**Connection Test:**
```python
# Via mcp__ue58-mcp__execute_python_code
import unreal
print("Unreal Python API ready")
print(f"Editor world: {unreal.EditorLevelLibrary.get_editor_world()}")
```

---

## QUICK START: Spawn Static Mesh Actor

**Most common use case - copy and execute:**

```python
# Via mcp__ue58-mcp__execute_python_code
import unreal

# Spawn actor at world location
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.StaticMeshActor,
    unreal.Vector(0, 0, 100),  # X, Y, Z
    unreal.Rotator(0, 0, 0)    # Pitch, Yaw, Roll
)

# Validate spawn succeeded
if actor is None:
    print("ERROR: Failed to spawn actor")
else:
    # Set mesh component
    mesh_comp = actor.static_mesh_component
    mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    mesh_comp.set_static_mesh(mesh)

    # Set actor label
    actor.set_actor_label("MyCube")

    # Set scale
    unreal.EditorLevelLibrary.set_actor_scale3d(
        actor,
        unreal.Vector(2.0, 2.0, 2.0)
    )

    print(f"SUCCESS: Spawned {actor.get_actor_label()}")
```

**Expected Output:**
```
SUCCESS: Spawned MyCube
```

---

## STANDARD WORKFLOWS

**For detailed workflow code and step-by-step instructions, see:** `reference/detailed-workflows.md`

**Five Core Workflows:**

1. **Spawn and Configure Multiple Actors** - Batch spawning, CSV import, grid placement patterns
2. **Property Manipulation Patterns** - Transform, visibility, tags, custom properties
3. **Component Operations** - Add/remove components, configure properties, material assignment
4. **Blueprint Actor Workflows** - Spawn from Blueprint, set construction script parameters
5. **Actor Query and Filtering** - Find by name, class, tags, location, complex queries

## VibeUE Toolset Alternative

When VibeUE plugin is installed, actor operations are also available via toolsets:

```
mcp__ue58-mcp__call_tool(
    toolset_name="VibeUE.ActorService",
    tool_name="spawn_actor",
    arguments={...}
)
```

Use `mcp__ue58-mcp__list_toolsets()` to discover available services.
Use `mcp__ue58-mcp__describe_toolset(toolset_name="VibeUE.ActorService")` for tool details.

---

## TROUBLESHOOTING

### Error: spawn_actor_from_class() returns None

**Cause:** Spawn location blocked by collision or invalid class.

**Solution:**
```python
# Check if class is valid
if not unreal.StaticMeshActor:
    print("ERROR: Class not available")

# Try different location (away from blocking geometry)
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.StaticMeshActor,
    unreal.Vector(0, 0, 1000),  # Higher Z
    unreal.Rotator(0, 0, 0)
)

# Always validate return
if actor is None:
    print("ERROR: Spawn failed - check collision at spawn location")
```

---

### Error: set_editor_property() returns False

**Cause:** Property doesn't exist or type mismatch.

**Solution:**
```python
# Check if property exists first
current_value = actor.get_editor_property('property_name')

if current_value is None:
    print("WARNING: Property 'property_name' not found or is None")
else:
    # Property exists, safe to set
    success = actor.set_editor_property('property_name', new_value)
    if not success:
        print("ERROR: Type mismatch or read-only property")
```

---

### Error: get_all_level_actors() is slow

**Cause:** Level has 1000+ actors, returning all is inefficient.

**Solution:**
```python
# Use class-specific query instead
world = unreal.EditorLevelLibrary.get_editor_world()
specific_actors = unreal.GameplayStatics.get_all_actors_of_class(
    world,
    unreal.StaticMeshActor  # Only get what you need
)
```

---

### Error: Actor is invalid after operation

**Cause:** Actor was deleted or became invalid.

**Solution:**
```python
# Always validate before operations
if actor is not None and actor.is_valid():
    # Safe to operate
    unreal.EditorLevelLibrary.set_actor_location(actor, new_location)
else:
    print("ERROR: Actor is invalid or None")
```

---

## REFERENCE DOCUMENTATION

For complete API details, see:
- **[actor_api_reference.md](reference/actor_api_reference.md)** - Complete EditorLevelLibrary API
- **[examples.md](examples/examples.md)** - 20+ actor manipulation examples

---

## VALIDATION CHECKLIST

**After actor operations, verify:**
- [ ] Actor spawned at correct location (check viewport)
- [ ] Actor label set correctly (Outliner panel)
- [ ] Transform applied (Details panel shows correct values)
- [ ] Properties set (Details panel shows changes)
- [ ] No error messages in Python output log
- [ ] Actor is valid (actor.is_valid() returns True)

**Common Success Indicators:**
```python
# Verify spawn
assert actor is not None, "Spawn failed"
assert actor.is_valid(), "Actor invalid"

# Verify transform
actual_loc = actor.get_actor_location()
assert actual_loc.x == expected_x, f"Location X mismatch: {actual_loc.x}"

# Verify property
actual_value = actor.get_editor_property('property_name')
assert actual_value == expected_value, f"Property mismatch: {actual_value}"
```

---

## VERSION HISTORY

**v2.0.0** (2026-07-06) - UE 5.8 Migration
- Migrated from community MCP (localhost:55557) to UE 5.8 native MCP (HTTP, port 8000)
- Updated allowed-tools: mcp__ue58-mcp__execute_python_code + call_tool
- Added VibeUE toolset alternative for actor operations
- Removed all references to old unreal-mcp server and send_command() patterns

**v1.0.0** (2025-11-17) - Initial Release
- EditorLevelLibrary as primary interface (18/20 APIs validated via Context7)
- Spawning, transform, property, and query patterns
- Troubleshooting: Silent failures, validation patterns
