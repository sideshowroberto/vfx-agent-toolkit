# Two-Layer Routing: Bridge + Handler Pattern

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Part of:** unreal-mcp-development skill

---

## 🚨 CRITICAL: THIS IS THE MOST FORGOTTEN STEP!

```
WITHOUT BRIDGE REGISTRATION:
❌ "Unknown command: your_tool_name"
(Even though your Python AND C++ code is perfect!)

WITH BRIDGE REGISTRATION:
✅ Tool executes successfully
```

**This document exists because developers forget Bridge routing registration 90% of the time.**

---

## Table of Contents

1. [Overview](#overview)
2. [Bridge Layer: Command Dispatcher](#bridge-layer-command-dispatcher)
3. [Handler Layer: Command Implementation](#handler-layer-command-implementation)
4. [Registration Requirements](#registration-requirements)
5. [Command Naming Conventions](#command-naming-conventions)
6. [Response Format Standards](#response-format-standards)
7. [Multiple Registration Examples](#multiple-registration-examples)
8. [What Happens Without Registration](#what-happens-without-registration)
9. [Testing Registration](#testing-registration)

---

## Overview

The Unreal MCP C++ plugin uses a **two-layer routing pattern** to separate command dispatching from implementation:

```
Layer 1: Bridge (Dispatcher)
    ├─ Receives command name from TCP
    ├─ Routes to appropriate handler
    └─ Returns handler's response

Layer 2: Handler (Implementation)
    ├─ Extracts parameters from JSON
    ├─ Executes Unreal Engine API calls
    └─ Builds JSON response
```

**Why Two Layers?**

- **Separation of Concerns:** Routing logic separate from business logic
- **Maintainability:** Easy to add/remove commands (one line in Bridge)
- **Testability:** Handlers can be tested independently
- **Discoverability:** All available commands visible in one place (RouteCommand function)

---

## Bridge Layer: Command Dispatcher

### Location

**File:** `Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp`
**Function:** `FUnrealMCPEditorCommands::RouteCommand()`

### Responsibilities

1. Accept command name (string) and request (JSON object)
2. Match command name to handler function
3. Call appropriate handler with request
4. Return handler's JSON response
5. **Return error if command not recognized**

---

### Bridge Implementation

```cpp
// File: UnrealMCPEditorCommands.cpp

FString FUnrealMCPEditorCommands::RouteCommand(const FString& Command,
                                                const TSharedPtr<FJsonObject>& Request)
{
    FString Response;

    // ═══════════════════════════════════════════════════════════
    // THIS IS THE BRIDGE - ALL COMMANDS MUST BE REGISTERED HERE!
    // ═══════════════════════════════════════════════════════════

    // Actor Commands
    if (Command == "spawn_actor")
    {
        Response = HandleSpawnActor(Request);
    }
    else if (Command == "spawn_static_mesh_actor")
    {
        Response = HandleSpawnStaticMeshActor(Request);
    }
    else if (Command == "set_actor_transform")
    {
        Response = HandleSetActorTransform(Request);
    }
    else if (Command == "set_actor_component_property")
    {
        Response = HandleSetActorComponentProperty(Request);
    }

    // Material Commands
    else if (Command == "create_material_instance")
    {
        Response = HandleCreateMaterialInstance(Request);
    }

    // Editor Commands
    else if (Command == "execute_python")
    {
        Response = HandleExecutePython(Request);
    }

    // ⚠️ ADD YOUR NEW COMMAND HERE! ⚠️
    // else if (Command == "your_new_command")
    // {
    //     Response = HandleYourNewCommand(Request);
    // }

    // Unknown Command (CRITICAL ERROR HANDLER)
    else
    {
        Response = CreateErrorResponse(FString::Printf(
            TEXT("Unknown command: %s"), *Command));
    }

    return Response;
}
```

---

### Critical Understanding

**The Bridge is a GIANT if-else chain** (or switch statement in other implementations):

```
Command received: "spawn_actor"
    ↓
if (Command == "spawn_actor")         ← Match found!
    ↓
Response = HandleSpawnActor(Request)  ← Call handler
    ↓
Return response to TCP client
```

**If command not registered:**

```
Command received: "your_new_command"
    ↓
if (Command == "spawn_actor")           ← No match
else if (Command == "set_actor_transform") ← No match
else if (Command == "execute_python")     ← No match
    ↓
else                                    ← Falls through to error!
    ↓
Response = CreateErrorResponse("Unknown command: your_new_command")
    ↓
Return error to TCP client
    ↓
Python receives: {"status": "error", "message": "Unknown command: your_new_command"}
    ↓
Claude Code shows error to user
```

---

### How to Add Command to Bridge

**Step 1: Locate RouteCommand Function**

```bash
# File location
MCPGameProject/Plugins/UnrealMCP/Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp

# Search for function
FString FUnrealMCPEditorCommands::RouteCommand(
```

**Step 2: Find the End of Command List**

```cpp
// Scroll through existing commands...
else if (Command == "execute_python")
{
    Response = HandleExecutePython(Request);
}

// ⬅️ ADD YOUR COMMAND BEFORE THE "else" BLOCK!

else  // ← This catches unknown commands
{
    Response = CreateErrorResponse(FString::Printf(
        TEXT("Unknown command: %s"), *Command));
}
```

**Step 3: Add Your Command**

```cpp
else if (Command == "execute_python")
{
    Response = HandleExecutePython(Request);
}

// ⬅️ YOUR NEW COMMAND GOES HERE:
else if (Command == "set_actor_label")
{
    Response = HandleSetActorLabel(Request);
}

else  // Unknown command error
{
    Response = CreateErrorResponse(FString::Printf(
        TEXT("Unknown command: %s"), *Command));
}
```

**Step 4: Verify Syntax**

✅ **CORRECT:**
```cpp
else if (Command == "set_actor_label")  // ← Exact match with Python tool name
{
    Response = HandleSetActorLabel(Request);  // ← Call handler function
}
```

❌ **WRONG:**
```cpp
// Missing "else":
if (Command == "set_actor_label")  // ❌ Will break chain!

// Typo in command name:
else if (Command == "set_actor_lable")  // ❌ Won't match!

// Wrong handler name:
else if (Command == "set_actor_label")
{
    Response = SetActorLabel(Request);  // ❌ Handler doesn't exist!
}
```

---

## Handler Layer: Command Implementation

### Location

Handlers are typically organized by category:

```
Source/UnrealMCP/Private/Commands/
├── ActorCommands.cpp        # spawn_actor, set_actor_transform, etc.
├── MaterialCommands.cpp     # create_material_instance, etc.
├── EditorCommands.cpp       # execute_python, etc.
└── ComponentCommands.cpp    # set_actor_component_property, etc.
```

### Responsibilities

1. Extract parameters from JSON request
2. Validate parameters (type, existence, validity)
3. Execute Unreal Engine API calls
4. Handle errors gracefully (return error response, don't crash)
5. Build structured JSON response
6. Return response as FString

---

### Handler Signature

**Standard pattern:**

```cpp
FString HandleCommandName(const TSharedPtr<FJsonObject>& Request)
{
    // 1. Extract parameters
    // 2. Validate
    // 3. Execute Unreal API
    // 4. Build response
    // 5. Return JSON string
}
```

**Example:**

```cpp
FString HandleSetActorLabel(const TSharedPtr<FJsonObject>& Request)
{
    // ─────────────────────────────────────────────────
    // 1. EXTRACT PARAMETERS FROM JSON
    // ─────────────────────────────────────────────────
    FString ActorName = Request->GetStringField("actor_name");
    FString NewLabel = Request->GetStringField("new_label");

    // ─────────────────────────────────────────────────
    // 2. VALIDATE PARAMETERS
    // ─────────────────────────────────────────────────
    if (ActorName.IsEmpty())
    {
        return CreateErrorResponse("Parameter 'actor_name' is required");
    }

    if (NewLabel.IsEmpty())
    {
        return CreateErrorResponse("Parameter 'new_label' is required");
    }

    // ─────────────────────────────────────────────────
    // 3. EXECUTE UNREAL ENGINE API
    // ─────────────────────────────────────────────────

    // Find actor in current level
    UWorld* World = GEditor->GetEditorWorldContext().World();
    AActor* FoundActor = nullptr;

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (Actor->GetName() == ActorName)
        {
            FoundActor = Actor;
            break;
        }
    }

    // Check if actor found
    if (!FoundActor)
    {
        return CreateErrorResponse(FString::Printf(
            TEXT("Actor not found: %s"), *ActorName));
    }

    // Set actor label
    FoundActor->SetActorLabel(NewLabel);

    // ─────────────────────────────────────────────────
    // 4. BUILD SUCCESS RESPONSE
    // ─────────────────────────────────────────────────
    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("message", FString::Printf(
        TEXT("Label set to %s"), *NewLabel));
    ResultJson->SetStringField("actor_name", ActorName);
    ResultJson->SetStringField("new_label", NewLabel);

    // ─────────────────────────────────────────────────
    // 5. RETURN JSON STRING
    // ─────────────────────────────────────────────────
    return CreateSuccessResponse(ResultJson);
}
```

---

### Parameter Extraction Patterns

**String Parameters:**
```cpp
FString StringParam = Request->GetStringField("param_name");
```

**Integer Parameters:**
```cpp
int32 IntParam = Request->GetIntegerField("param_name");
```

**Float Parameters:**
```cpp
double FloatParam = Request->GetNumberField("param_name");
```

**Boolean Parameters:**
```cpp
bool BoolParam = Request->GetBoolField("param_name");
```

**Nested Object (e.g., Vector):**
```cpp
TSharedPtr<FJsonObject> LocationObj = Request->GetObjectField("location");
FVector Location(
    LocationObj->GetNumberField("x"),
    LocationObj->GetNumberField("y"),
    LocationObj->GetNumberField("z")
);
```

**Optional Parameters:**
```cpp
// Check if field exists before accessing
FString OptionalParam;
if (Request->HasField("optional_param"))
{
    OptionalParam = Request->GetStringField("optional_param");
}
else
{
    OptionalParam = "default_value";
}
```

---

### Response Building Patterns

**Success Response (Simple):**
```cpp
return CreateSuccessResponse("Actor spawned successfully");
```

**Success Response (With Data):**
```cpp
TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
ResultJson->SetStringField("actor_name", ActorName);
ResultJson->SetStringField("actor_class", ActorClass);
ResultJson->SetNumberField("location_x", Location.X);

return CreateSuccessResponse(ResultJson);
```

**Error Response:**
```cpp
return CreateErrorResponse("Actor not found");
```

**Error Response (Formatted):**
```cpp
return CreateErrorResponse(FString::Printf(
    TEXT("Actor not found: %s"), *ActorName));
```

---

## Registration Requirements

### Checklist for New Command

When adding a new MCP tool, you MUST complete all steps:

```
[ ] Step 1: Create Python MCP tool (@mcp.tool() in Python/tools/*.py)
[ ] Step 2: Create C++ handler function (Handle* in Commands/*.cpp)
[ ] Step 3: ⚠️ REGISTER IN BRIDGE (else if block in RouteCommand) ⚠️
[ ] Step 4: Add handler declaration to header (if in separate file)
[ ] Step 5: Compile C++ plugin (Build.bat)
[ ] Step 6: Restart MCP Python server
[ ] Step 7: Test tool from Claude Code
[ ] Step 8: Verify response format
```

**Step 3 is the MOST FORGOTTEN!**

---

### Registration Template

**Add this block to RouteCommand():**

```cpp
else if (Command == "your_command_name")  // ← EXACT match with Python tool
{
    Response = HandleYourCommandName(Request);  // ← Call your handler
}
```

**Before the final `else` block:**

```cpp
    // ... existing commands ...

    else if (Command == "execute_python")
    {
        Response = HandleExecutePython(Request);
    }

    // ⬅️ ADD YOUR COMMAND HERE (before final else)
    else if (Command == "your_command_name")
    {
        Response = HandleYourCommandName(Request);
    }

    else  // ← Unknown command handler (MUST be last!)
    {
        Response = CreateErrorResponse(FString::Printf(
            TEXT("Unknown command: %s"), *Command));
    }
```

---

### Handler Declaration

If handler is in a separate file, add forward declaration to header:

**File:** `Source/UnrealMCP/Public/UnrealMCPEditorCommands.h`

```cpp
class UNREALMCP_API FUnrealMCPEditorCommands
{
public:
    static FString RouteCommand(const FString& Command,
                                const TSharedPtr<FJsonObject>& Request);

    // ─────────────────────────────────────────────────
    // HANDLER DECLARATIONS (if in separate files)
    // ─────────────────────────────────────────────────

    // Actor Commands
    static FString HandleSpawnActor(const TSharedPtr<FJsonObject>& Request);
    static FString HandleSetActorTransform(const TSharedPtr<FJsonObject>& Request);

    // ⬅️ ADD YOUR HANDLER DECLARATION HERE
    static FString HandleYourCommandName(const TSharedPtr<FJsonObject>& Request);
};
```

**Alternative:** Keep handler in same file as RouteCommand (no declaration needed)

---

## Command Naming Conventions

### Python to C++ Mapping

**Python MCP tool name MUST EXACTLY match Bridge command string:**

```python
# Python tool name (snake_case)
@mcp.tool()
def set_actor_component_property(...):
    unreal.send_command("set_actor_component_property", {...})
    #                    ↑
    #                    This string...
```

```cpp
// C++ Bridge registration (MUST MATCH EXACTLY!)
else if (Command == "set_actor_component_property")
//                   ↑
//                   ...must match this string!
{
    Response = HandleSetActorComponentProperty(Request);
}
```

---

### Naming Standards

**Recommended Pattern:**
- Python tool: `verb_noun_qualifier` (snake_case)
- C++ handler: `HandleVerbNounQualifier` (PascalCase with Handle prefix)

**Examples:**

| Python Tool Name            | C++ Handler Name                   | Bridge Command String         |
|-----------------------------|-----------------------------------|-------------------------------|
| `spawn_actor`               | `HandleSpawnActor`                | `"spawn_actor"`               |
| `set_actor_transform`       | `HandleSetActorTransform`         | `"set_actor_transform"`       |
| `create_material_instance`  | `HandleCreateMaterialInstance`    | `"create_material_instance"`  |
| `execute_python`            | `HandleExecutePython`             | `"execute_python"`            |
| `set_actor_component_property` | `HandleSetActorComponentProperty` | `"set_actor_component_property"` |

---

### Common Naming Mistakes

❌ **WRONG: Case mismatch**
```python
# Python
unreal.send_command("set_actor_transform", {...})
```
```cpp
// C++ (WRONG - capital T!)
else if (Command == "set_actor_Transform")  // ❌ Won't match!
```

❌ **WRONG: Underscore vs camelCase**
```python
# Python
unreal.send_command("set_actor_transform", {...})
```
```cpp
// C++ (WRONG - camelCase!)
else if (Command == "setActorTransform")  // ❌ Won't match!
```

❌ **WRONG: Typo**
```python
# Python
unreal.send_command("set_actor_transform", {...})
```
```cpp
// C++ (WRONG - typo!)
else if (Command == "set_actor_tranform")  // ❌ Missing 's'!
```

✅ **CORRECT:**
```python
# Python
unreal.send_command("set_actor_transform", {...})
```
```cpp
// C++ (CORRECT - exact match!)
else if (Command == "set_actor_transform")  // ✅ Perfect!
```

---

## Response Format Standards

### Required Response Structure

**All responses MUST be valid JSON with:**

1. **`status` field** - "success" or "error"
2. **Additional fields** - Command-specific data

**DO NOT manually construct JSON strings!** Use helper functions.

---

### CreateSuccessResponse Function

**Signature:**
```cpp
FString CreateSuccessResponse(const FString& Message);
FString CreateSuccessResponse(const TSharedPtr<FJsonObject>& Data);
```

**Simple Success:**
```cpp
return CreateSuccessResponse("Actor spawned successfully");
```

**Produces:**
```json
{
  "status": "success",
  "message": "Actor spawned successfully"
}
```

---

**Success with Data:**
```cpp
TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
ResultJson->SetStringField("actor_name", "StaticMeshActor_42");
ResultJson->SetStringField("mesh_path", "/Engine/BasicShapes/Cube.Cube");
ResultJson->SetNumberField("location_x", 0.0);

return CreateSuccessResponse(ResultJson);
```

**Produces:**
```json
{
  "status": "success",
  "actor_name": "StaticMeshActor_42",
  "mesh_path": "/Engine/BasicShapes/Cube.Cube",
  "location_x": 0.0
}
```

---

### CreateErrorResponse Function

**Signature:**
```cpp
FString CreateErrorResponse(const FString& ErrorMessage);
```

**Usage:**
```cpp
return CreateErrorResponse("Actor not found");
```

**Produces:**
```json
{
  "status": "error",
  "message": "Actor not found"
}
```

**With Formatting:**
```cpp
return CreateErrorResponse(FString::Printf(
    TEXT("Actor not found: %s"), *ActorName));
```

**Produces:**
```json
{
  "status": "error",
  "message": "Actor not found: StaticMeshActor_99"
}
```

---

### Common Mistakes in Response Building

❌ **WRONG: Manual JSON string construction**
```cpp
FString Response = FString::Printf(TEXT("{status: success, actor: %s}"), *ActorName);
return Response;
// Missing quotes around keys!
// Not escaped properly!
// NOT VALID JSON!
```

❌ **WRONG: Returning non-JSON**
```cpp
return "Actor spawned";  // ❌ Not JSON!
```

❌ **WRONG: Missing status field**
```cpp
TSharedPtr<FJsonObject> Json = MakeShared<FJsonObject>();
Json->SetStringField("actor_name", ActorName);
// No status field!

FString Output;
TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Output);
FJsonSerializer::Serialize(Json.ToSharedRef(), Writer);
return Output;  // ❌ Missing "status": "success"!
```

✅ **CORRECT: Use helper functions**
```cpp
TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
ResultJson->SetStringField("actor_name", ActorName);
return CreateSuccessResponse(ResultJson);  // ✅ Adds status automatically!
```

---

## Multiple Registration Examples

### Example 1: Actor Commands

**Python Tool:**
```python
# Python/tools/actor_tools.py
@mcp.tool()
def spawn_static_mesh_actor(ctx: Context, mesh_path: str, location: Dict) -> Dict:
    unreal = get_unreal_connection()
    result = unreal.send_command("spawn_static_mesh_actor", {
        "mesh_path": mesh_path,
        "location": location
    })
    return result
```

**C++ Handler:**
```cpp
// Source/UnrealMCP/Private/Commands/ActorCommands.cpp
FString HandleSpawnStaticMeshActor(const TSharedPtr<FJsonObject>& Request)
{
    FString MeshPath = Request->GetStringField("mesh_path");
    TSharedPtr<FJsonObject> LocationObj = Request->GetObjectField("location");

    // ... implementation ...

    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("actor_name", Actor->GetName());
    return CreateSuccessResponse(ResultJson);
}
```

**⚠️ Bridge Registration:**
```cpp
// Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp
else if (Command == "spawn_static_mesh_actor")  // ⬅️ MUST ADD THIS!
{
    Response = HandleSpawnStaticMeshActor(Request);
}
```

---

### Example 2: Material Commands

**Python Tool:**
```python
# Python/tools/material_tools.py
@mcp.tool()
def create_material_instance(ctx: Context, parent_path: str, instance_name: str) -> Dict:
    unreal = get_unreal_connection()
    result = unreal.send_command("create_material_instance", {
        "parent_path": parent_path,
        "instance_name": instance_name
    })
    return result
```

**C++ Handler:**
```cpp
// Source/UnrealMCP/Private/Commands/MaterialCommands.cpp
FString HandleCreateMaterialInstance(const TSharedPtr<FJsonObject>& Request)
{
    FString ParentPath = Request->GetStringField("parent_path");
    FString InstanceName = Request->GetStringField("instance_name");

    // ... implementation ...

    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("instance_path", InstancePath);
    return CreateSuccessResponse(ResultJson);
}
```

**⚠️ Bridge Registration:**
```cpp
// Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp
else if (Command == "create_material_instance")  // ⬅️ MUST ADD THIS!
{
    Response = HandleCreateMaterialInstance(Request);
}
```

---

### Example 3: Editor Commands

**Python Tool:**
```python
# Python/tools/editor_tools.py
@mcp.tool()
def execute_python(ctx: Context, script: str) -> Dict:
    unreal = get_unreal_connection()
    result = unreal.send_command("execute_python", {
        "script": script
    })
    return result
```

**C++ Handler:**
```cpp
// Source/UnrealMCP/Private/Commands/EditorCommands.cpp
FString HandleExecutePython(const TSharedPtr<FJsonObject>& Request)
{
    FString Script = Request->GetStringField("script");

    // ... implementation ...

    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("output", Output);
    return CreateSuccessResponse(ResultJson);
}
```

**⚠️ Bridge Registration:**
```cpp
// Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp
else if (Command == "execute_python")  // ⬅️ MUST ADD THIS!
{
    Response = HandleExecutePython(Request);
}
```

---

### Complete Bridge Example

Here's what the full RouteCommand function looks like with multiple commands:

```cpp
FString FUnrealMCPEditorCommands::RouteCommand(const FString& Command,
                                                const TSharedPtr<FJsonObject>& Request)
{
    FString Response;

    // ═══════════════════════════════════════════════════════════
    // ACTOR COMMANDS
    // ═══════════════════════════════════════════════════════════
    if (Command == "spawn_actor")
    {
        Response = HandleSpawnActor(Request);
    }
    else if (Command == "spawn_static_mesh_actor")
    {
        Response = HandleSpawnStaticMeshActor(Request);
    }
    else if (Command == "set_actor_transform")
    {
        Response = HandleSetActorTransform(Request);
    }
    else if (Command == "set_actor_label")
    {
        Response = HandleSetActorLabel(Request);
    }
    else if (Command == "delete_actor")
    {
        Response = HandleDeleteActor(Request);
    }

    // ═══════════════════════════════════════════════════════════
    // COMPONENT COMMANDS
    // ═══════════════════════════════════════════════════════════
    else if (Command == "set_actor_component_property")
    {
        Response = HandleSetActorComponentProperty(Request);
    }

    // ═══════════════════════════════════════════════════════════
    // MATERIAL COMMANDS
    // ═══════════════════════════════════════════════════════════
    else if (Command == "create_material_instance")
    {
        Response = HandleCreateMaterialInstance(Request);
    }
    else if (Command == "set_material_parameter")
    {
        Response = HandleSetMaterialParameter(Request);
    }

    // ═══════════════════════════════════════════════════════════
    // EDITOR COMMANDS
    // ═══════════════════════════════════════════════════════════
    else if (Command == "execute_python")
    {
        Response = HandleExecutePython(Request);
    }
    else if (Command == "save_current_level")
    {
        Response = HandleSaveCurrentLevel(Request);
    }

    // ═══════════════════════════════════════════════════════════
    // UNKNOWN COMMAND (MUST BE LAST!)
    // ═══════════════════════════════════════════════════════════
    else
    {
        Response = CreateErrorResponse(FString::Printf(
            TEXT("Unknown command: %s"), *Command));
    }

    return Response;
}
```

**Notice:**
- Organized by category (actor, component, material, editor)
- Each command is an `else if` block
- Final `else` catches unknown commands
- All handlers return FString (JSON)

---

## What Happens Without Registration

### The Error Chain

**Scenario:** You create a new tool but forget Bridge registration

**Python Side (Looks Perfect):**
```python
# Python/tools/actor_tools.py
@mcp.tool()
def set_actor_label(ctx: Context, actor_name: str, new_label: str) -> Dict:
    unreal = get_unreal_connection()
    result = unreal.send_command("set_actor_label", {
        "actor_name": actor_name,
        "new_label": new_label
    })
    return result
```

**C++ Handler (Also Perfect):**
```cpp
// Source/UnrealMCP/Private/Commands/ActorCommands.cpp
FString HandleSetActorLabel(const TSharedPtr<FJsonObject>& Request)
{
    FString ActorName = Request->GetStringField("actor_name");
    FString NewLabel = Request->GetStringField("new_label");

    // Find actor and set label...

    return CreateSuccessResponse("Label set successfully");
}
```

**Bridge (MISSING REGISTRATION!):**
```cpp
// UnrealMCPEditorCommands.cpp
FString FUnrealMCPEditorCommands::RouteCommand(const FString& Command,
                                                const TSharedPtr<FJsonObject>& Request)
{
    if (Command == "spawn_actor") { ... }
    else if (Command == "set_actor_transform") { ... }
    // ... other commands ...

    // ❌ NO "set_actor_label" REGISTRATION!

    else  // Falls through to here!
    {
        Response = CreateErrorResponse(FString::Printf(
            TEXT("Unknown command: %s"), *Command));
    }
}
```

---

### What the User Experiences

**User types in Claude Code:**
```
"Set the label of Cube_42 to 'MyCube'"
```

**Claude Code invokes tool:**
```python
result = mcp__unreal-mcp__set_actor_label(
    actor_name="Cube_42",
    new_label="MyCube"
)
```

**Python sends TCP message:**
```json
{
  "command": "set_actor_label",
  "actor_name": "Cube_42",
  "new_label": "MyCube"
}
```

**C++ Bridge receives, tries to route:**
```cpp
Command = "set_actor_label"

if (Command == "spawn_actor") { ... }        // No match
else if (Command == "set_actor_transform") { ... }  // No match
// ... all registered commands don't match ...
else  // Falls through!
{
    // Returns this error:
    Response = CreateErrorResponse("Unknown command: set_actor_label");
}
```

**Python receives error response:**
```json
{
  "status": "error",
  "message": "Unknown command: set_actor_label"
}
```

**Claude Code shows user:**
```
Error: Unknown command: set_actor_label
```

**User is confused because:**
- The Python tool exists
- The C++ handler exists and looks correct
- Everything seems properly named
- **But it doesn't work!**

---

### Debugging This Issue

**Step 1: Verify Python Tool Exists**
```bash
# Search for tool definition
grep -r "def set_actor_label" Python/tools/
# Found: Python/tools/actor_tools.py
```
✅ Python tool exists

**Step 2: Verify C++ Handler Exists**
```bash
# Search for handler implementation
grep -r "HandleSetActorLabel" Source/
# Found: Source/UnrealMCP/Private/Commands/ActorCommands.cpp
```
✅ C++ handler exists

**Step 3: Check Bridge Registration**
```bash
# Search for Bridge registration
grep "set_actor_label" Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp
# No results found!
```
❌ **Bridge registration MISSING - THIS IS THE PROBLEM!**

**Step 4: Add Registration**
```cpp
// Add to RouteCommand():
else if (Command == "set_actor_label")
{
    Response = HandleSetActorLabel(Request);
}
```

**Step 5: Recompile and Test**
```bash
# Close Unreal, recompile plugin
Build.bat MCPGameProjectEditor Win64 Development Project.uproject

# Restart MCP server
uv --directory Python/ run unreal_mcp_server.py

# Test again
mcp__unreal-mcp__set_actor_label(actor_name="Cube_42", new_label="MyCube")
# ✅ Now works!
```

---

## Testing Registration

### Manual Verification Checklist

Before testing a new tool, verify:

```
[ ] Python tool exists in Python/tools/*.py
[ ] Python tool calls send_command() with correct command name
[ ] C++ handler exists in Source/UnrealMCP/Private/Commands/*.cpp
[ ] C++ handler returns CreateSuccessResponse() or CreateErrorResponse()
[ ] ⚠️ Bridge registration added to RouteCommand() ⚠️
[ ] Command string in Bridge EXACTLY matches Python send_command() string
[ ] Plugin compiled successfully (DLL created)
[ ] MCP server restarted (picks up new tool)
```

---

### Quick Test Script

**Python test (run in MCP server context):**
```python
# Test all registered commands
commands_to_test = [
    "spawn_actor",
    "set_actor_transform",
    "set_actor_component_property",
    "execute_python",
    # Add your new command here:
    "set_actor_label"
]

for cmd in commands_to_test:
    # Send minimal valid request
    result = unreal.send_command(cmd, {})
    if result["status"] == "error" and "Unknown command" in result["message"]:
        print(f"❌ NOT REGISTERED: {cmd}")
    else:
        print(f"✅ Registered: {cmd}")
```

---

### Log Analysis

**Enable verbose logging in C++:**
```cpp
FString FUnrealMCPEditorCommands::RouteCommand(const FString& Command,
                                                const TSharedPtr<FJsonObject>& Request)
{
    // Add logging at start
    UE_LOG(LogTemp, Log, TEXT("Routing command: %s"), *Command);

    // ... routing logic ...
}
```

**Check Unreal Output Log:**
```
LogTemp: Routing command: set_actor_label
LogTemp: Error: Unknown command: set_actor_label
```

If you see "Unknown command" immediately after routing, Bridge registration is missing!

---

## Summary

**Key Takeaways:**

1. **Bridge routing is CRITICAL** - most forgotten step when adding tools
2. **Two-layer pattern separates routing from implementation** - maintainability
3. **Command names must match EXACTLY** - Python, Bridge, and handler aligned
4. **Use helper functions for responses** - CreateSuccessResponse, CreateErrorResponse
5. **Always test registration** - verify before debugging deeper

**The Bridge Registration Golden Rule:**

```
┌─────────────────────────────────────────────────────┐
│  FOR EVERY PYTHON MCP TOOL:                         │
│                                                     │
│  1. Create @mcp.tool() in Python/tools/*.py        │
│  2. Create Handler* in C++ Commands/*.cpp          │
│  3. ⚠️ ADD "else if" IN RouteCommand() ⚠️           │
│                                                     │
│  Skip step 3 → "Unknown command" error!             │
└─────────────────────────────────────────────────────┘
```

**For complete workflows:**
- **adding_tools_workflow.md** - Step-by-step guide with examples
- **debugging_guide.md** - Systematic troubleshooting for routing failures
- **architecture_overview.md** - Three-layer system understanding

---

**Last Updated:** 2025-10-25
**Part of:** unreal-mcp-development skill (v1.0.0)
