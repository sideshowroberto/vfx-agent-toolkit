# Adding MCP Tools: Complete Workflow Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Part of:** unreal-mcp-development skill

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [8-Step Workflow](#8-step-workflow)
4. [Step 1: Create Python MCP Tool](#step-1-create-python-mcp-tool)
5. [Step 2: Create C++ Handler](#step-2-create-c-handler)
6. [Step 3: Register in Bridge](#step-3-register-in-bridge)
7. [Step 4: Compile C++ Plugin](#step-4-compile-c-plugin)
8. [Step 5: Restart MCP Python Server](#step-5-restart-mcp-python-server)
9. [Step 6: Test Tool from Claude Code](#step-6-test-tool-from-claude-code)
10. [Step 7: Verify JSON Response](#step-7-verify-json-response)
11. [Step 8: Document in MCP_Capabilities](#step-8-document-in-mcp_capabilities)
12. [Common Mistakes at Each Step](#common-mistakes-at-each-step)
13. [Testing Procedures](#testing-procedures)
14. [Complete Example: set_actor_label](#complete-example-set_actor_label)

---

## Overview

Adding a new MCP tool requires coordinated changes across three layers:
1. **Python MCP Server** - Define tool interface
2. **C++ Plugin** - Implement handler logic
3. **Bridge Routing** - Connect Python to C++ (MOST FORGOTTEN!)

**Timeline:**
- Simple tool (set property): 20-30 minutes
- Medium tool (spawn actor): 30-45 minutes
- Complex tool (multi-step workflow): 1-2 hours

**Prerequisite Knowledge:**
- Python (basic): Functions, dictionaries, type hints
- C++ (intermediate): Classes, pointers, JSON serialization
- Unreal Engine (intermediate): Actor API, asset loading, editor operations

---

## Prerequisites

### Required Software

```
✅ Unreal Engine 5.5+ installed
✅ Visual Studio 2022 with C++ tools
✅ Python 3.12+
✅ uv package manager
✅ UnrealMCP plugin compiled and working
✅ Claude Code with MCP configuration
```

### Verification Commands

```bash
# Check Unreal Engine
where UnrealEditor.exe
# Expected: C:\Program Files\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor.exe

# Check Visual Studio
where MSBuild.exe
# Expected: C:\Program Files\Microsoft Visual Studio\2022\...\MSBuild.exe

# Check Python
python --version
# Expected: Python 3.12.x or higher

# Check uv
uv --version
# Expected: uv 0.x.x
```

### Environment Setup

```bash
# Navigate to project directory
cd <UNREAL_MCP_DIR>

# Verify directory structure
ls
# Should see: MCPGameProject/, Python/, MCP_Capabilities_UE55.md

# Test MCP server connection
uv --directory Python/ run unreal_mcp_server.py
# Should see: "Connected to Unreal at localhost:55557"
```

---

## 8-Step Workflow

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: Create Python MCP Tool                         │
│  ✓ Define @mcp.tool() function                          │
│  ✓ Add type hints                                       │
│  ✓ Call send_command() with command name               │
│  ✓ File: Python/tools/[category]_tools.py              │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 2: Create C++ Handler                             │
│  ✓ Implement Handler* function                          │
│  ✓ Extract parameters from JSON                         │
│  ✓ Execute Unreal Engine API                            │
│  ✓ Return CreateSuccessResponse() or CreateErrorResponse()│
│  ✓ File: Source/UnrealMCP/Private/Commands/*.cpp       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 3: ⚠️ REGISTER IN BRIDGE ⚠️ (MOST FORGOTTEN!)    │
│  ✓ Add else if (Command == "tool_name") { ... }        │
│  ✓ File: UnrealMCPEditorCommands.cpp                   │
│  ✓ Function: RouteCommand()                            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 4: Compile C++ Plugin                             │
│  ✓ Close Unreal Editor (avoid DLL locking)             │
│  ✓ Run Build.bat                                        │
│  ✓ Verify DLL created with recent timestamp            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 5: Restart MCP Python Server                      │
│  ✓ Stop existing server (Ctrl+C)                        │
│  ✓ Run: uv --directory Python/ run unreal_mcp_server.py│
│  ✓ Verify connection to localhost:55557                │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 6: Test Tool from Claude Code                     │
│  ✓ Invoke: mcp__unreal-mcp__tool_name(...)             │
│  ✓ Verify response received                            │
│  ✓ Check status: "success" or "error"                  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 7: Verify JSON Response                           │
│  ✓ Valid JSON structure                                │
│  ✓ Contains status field                               │
│  ✓ Test error cases                                    │
│  ✓ Check edge cases                                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 8: Document in MCP_Capabilities                   │
│  ✓ Add tool description                                │
│  ✓ Document parameters                                 │
│  ✓ Provide usage example                               │
│  ✓ File: MCP_Capabilities_UE55.md                      │
└─────────────────────────────────────────────────────────┘
```

---

## Step 1: Create Python MCP Tool

### Location

Choose appropriate tool category file:

```
Python/tools/
├── actor_tools.py       # Actor operations (spawn, transform, delete)
├── component_tools.py   # Component property operations
├── material_tools.py    # Material/texture operations
├── editor_tools.py      # Editor operations (execute_python, save)
└── your_new_category_tools.py  # Create new file if needed
```

### Template

```python
from typing import Dict, Any, List, Optional
from mcp import Context
from connection import get_unreal_connection

@mcp.tool()
def your_tool_name(
    ctx: Context,
    param1: str,
    param2: int,
    param3: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Brief one-line description of what this tool does.

    Longer description if needed, explaining use cases, limitations,
    or important details about the tool's behavior.

    Args:
        param1: Description of first parameter (required)
        param2: Description of second parameter (required)
        param3: Description of optional parameter (optional)

    Returns:
        Dictionary with:
        - status (str): "success" or "error"
        - message (str): Result description
        - [additional fields specific to this tool]

    Example:
        result = mcp__unreal-mcp__your_tool_name(
            param1="value",
            param2=42
        )
    """
    # Get TCP connection to C++ plugin
    unreal = get_unreal_connection()

    # Build request parameters
    params = {
        "param1": param1,
        "param2": param2
    }

    # Add optional parameters if provided
    if param3 is not None:
        params["param3"] = param3

    # Send command over TCP (command name MUST match Bridge registration!)
    result = unreal.send_command("your_tool_name", params)

    return result
```

---

### FastMCP Patterns

**Required Imports:**
```python
from typing import Dict, Any, List, Optional  # Type hints
from mcp import Context                        # MCP context
from connection import get_unreal_connection   # TCP connection helper
```

**Tool Decorator:**
```python
@mcp.tool()  # Exposes function as MCP tool
def your_tool_name(ctx: Context, ...):
    pass
```

**Context Parameter:**
```python
# ALWAYS first parameter
ctx: Context  # Provided by MCP framework (don't use directly in most cases)
```

---

### Type Hints

**String Parameter:**
```python
actor_name: str
```

**Integer Parameter:**
```python
count: int
```

**Float Parameter:**
```python
scale: float
```

**Boolean Parameter:**
```python
enabled: bool
```

**Dictionary Parameter (Vector, Rotator, etc.):**
```python
location: Dict[str, float]  # {"x": 0, "y": 100, "z": 50}
```

**List Parameter:**
```python
actor_names: List[str]  # ["Actor1", "Actor2", "Actor3"]
```

**Optional Parameter:**
```python
optional_param: Optional[str] = None
```

---

### Example: Actor Tool

```python
# File: Python/tools/actor_tools.py

@mcp.tool()
def set_actor_label(
    ctx: Context,
    actor_name: str,
    new_label: str
) -> Dict[str, Any]:
    """
    Set the display label of an actor in the Unreal Editor.

    Args:
        actor_name: Name of the actor to modify
        new_label: New display label to set

    Returns:
        Dictionary with status and updated label information
    """
    unreal = get_unreal_connection()

    result = unreal.send_command("set_actor_label", {
        "actor_name": actor_name,
        "new_label": new_label
    })

    return result
```

---

### Example: Component Tool

```python
# File: Python/tools/component_tools.py

@mcp.tool()
def set_actor_component_property(
    ctx: Context,
    actor_name: str,
    component_name: str,
    property_name: str,
    property_value: str,
    property_type: str
) -> Dict[str, Any]:
    """
    Set a property on an actor's component (supports ObjectProperty, FloatProperty, etc.).

    Args:
        actor_name: Name of the actor
        component_name: Name of the component (e.g., "StaticMeshComponent")
        property_name: Property to set (e.g., "StaticMesh")
        property_value: Value to set (asset path for ObjectProperty)
        property_type: Type of property ("ObjectProperty", "FloatProperty", etc.)

    Returns:
        Dictionary with status and property details
    """
    unreal = get_unreal_connection()

    result = unreal.send_command("set_actor_component_property", {
        "actor_name": actor_name,
        "component_name": component_name,
        "property_name": property_name,
        "property_value": property_value,
        "property_type": property_type
    })

    return result
```

---

## Step 2: Create C++ Handler

### Location

Choose appropriate handler file:

```
Source/UnrealMCP/Private/Commands/
├── ActorCommands.cpp       # Actor-related handlers
├── ComponentCommands.cpp   # Component-related handlers
├── MaterialCommands.cpp    # Material-related handlers
├── EditorCommands.cpp      # Editor-related handlers
└── YourNewCommands.cpp     # Create new file if needed
```

### Template

```cpp
#include "UnrealMCPCommonUtils.h"
#include "Editor.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
// Add other necessary includes

FString HandleYourToolName(const TSharedPtr<FJsonObject>& Request)
{
    // ─────────────────────────────────────────────────────────
    // 1. EXTRACT PARAMETERS FROM JSON REQUEST
    // ─────────────────────────────────────────────────────────

    // Required string parameter
    FString Param1 = Request->GetStringField("param1");

    // Required integer parameter
    int32 Param2 = Request->GetIntegerField("param2");

    // Optional parameter (check existence first)
    FString OptionalParam;
    if (Request->HasField("optional_param"))
    {
        OptionalParam = Request->GetStringField("optional_param");
    }

    // ─────────────────────────────────────────────────────────
    // 2. VALIDATE PARAMETERS
    // ─────────────────────────────────────────────────────────

    if (Param1.IsEmpty())
    {
        return CreateErrorResponse("Parameter 'param1' cannot be empty");
    }

    if (Param2 < 0)
    {
        return CreateErrorResponse("Parameter 'param2' must be non-negative");
    }

    // ─────────────────────────────────────────────────────────
    // 3. EXECUTE UNREAL ENGINE API CALLS
    // ─────────────────────────────────────────────────────────

    // Get editor world
    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (!World)
    {
        return CreateErrorResponse("No active world found");
    }

    // Perform your operation...
    // (This is where your Unreal-specific logic goes)

    // ─────────────────────────────────────────────────────────
    // 4. BUILD SUCCESS RESPONSE
    // ─────────────────────────────────────────────────────────

    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("message", "Operation completed successfully");
    ResultJson->SetStringField("param1", Param1);
    ResultJson->SetNumberField("param2", Param2);

    return CreateSuccessResponse(ResultJson);

    // OR: Return simple message
    // return CreateSuccessResponse("Operation completed successfully");

    // OR: Return error if something fails
    // return CreateErrorResponse("Operation failed: reason here");
}
```

---

### Parameter Extraction Patterns

**String:**
```cpp
FString ActorName = Request->GetStringField("actor_name");
```

**Integer:**
```cpp
int32 Count = Request->GetIntegerField("count");
```

**Float/Double:**
```cpp
double Scale = Request->GetNumberField("scale");
```

**Boolean:**
```cpp
bool bEnabled = Request->GetBoolField("enabled");
```

**Vector (Nested Object):**
```cpp
TSharedPtr<FJsonObject> LocationObj = Request->GetObjectField("location");
FVector Location(
    LocationObj->GetNumberField("x"),
    LocationObj->GetNumberField("y"),
    LocationObj->GetNumberField("z")
);
```

**Rotator (Nested Object):**
```cpp
TSharedPtr<FJsonObject> RotationObj = Request->GetObjectField("rotation");
FRotator Rotation(
    RotationObj->GetNumberField("pitch"),
    RotationObj->GetNumberField("yaw"),
    RotationObj->GetNumberField("roll")
);
```

**Optional Parameter:**
```cpp
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

### Common Unreal API Patterns

**Get Editor World:**
```cpp
UWorld* World = GEditor->GetEditorWorldContext().World();
if (!World)
{
    return CreateErrorResponse("No active world found");
}
```

**Find Actor by Name:**
```cpp
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

if (!FoundActor)
{
    return CreateErrorResponse(FString::Printf(
        TEXT("Actor not found: %s"), *ActorName));
}
```

**Load Asset:**
```cpp
UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *MeshPath);
if (!Mesh)
{
    return CreateErrorResponse(FString::Printf(
        TEXT("Failed to load mesh: %s"), *MeshPath));
}
```

**Spawn Actor:**
```cpp
AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(
    Location,  // FVector
    Rotation   // FRotator
);

if (!Actor)
{
    return CreateErrorResponse("Failed to spawn actor");
}
```

**Get Component:**
```cpp
UStaticMeshComponent* MeshComp = Actor->FindComponentByClass<UStaticMeshComponent>();
if (!MeshComp)
{
    return CreateErrorResponse("Actor has no StaticMeshComponent");
}
```

---

### Example: set_actor_label Handler

```cpp
// File: Source/UnrealMCP/Private/Commands/ActorCommands.cpp

FString HandleSetActorLabel(const TSharedPtr<FJsonObject>& Request)
{
    // Extract parameters
    FString ActorName = Request->GetStringField("actor_name");
    FString NewLabel = Request->GetStringField("new_label");

    // Validate
    if (ActorName.IsEmpty())
    {
        return CreateErrorResponse("actor_name is required");
    }

    if (NewLabel.IsEmpty())
    {
        return CreateErrorResponse("new_label is required");
    }

    // Get world
    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (!World)
    {
        return CreateErrorResponse("No active world");
    }

    // Find actor
    AActor* FoundActor = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if ((*It)->GetName() == ActorName)
        {
            FoundActor = *It;
            break;
        }
    }

    if (!FoundActor)
    {
        return CreateErrorResponse(FString::Printf(
            TEXT("Actor not found: %s"), *ActorName));
    }

    // Set label
    FoundActor->SetActorLabel(NewLabel);

    // Build response
    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("message", "Label set successfully");
    ResultJson->SetStringField("actor_name", ActorName);
    ResultJson->SetStringField("old_label", FoundActor->GetActorLabel());
    ResultJson->SetStringField("new_label", NewLabel);

    return CreateSuccessResponse(ResultJson);
}
```

---

## Step 3: Register in Bridge

### ⚠️ MOST FORGOTTEN STEP! ⚠️

**File:** `Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp`
**Function:** `FUnrealMCPEditorCommands::RouteCommand()`

### Procedure

**1. Open Bridge File:**
```cpp
// Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp
```

**2. Find RouteCommand Function:**
```cpp
FString FUnrealMCPEditorCommands::RouteCommand(const FString& Command,
                                                const TSharedPtr<FJsonObject>& Request)
{
    // ... existing commands ...
}
```

**3. Locate End of Command List:**
```cpp
    // ... other commands ...

    else if (Command == "execute_python")
    {
        Response = HandleExecutePython(Request);
    }

    // ⬅️ ADD YOUR COMMAND HERE (before final else)

    else  // Unknown command handler
    {
        Response = CreateErrorResponse(FString::Printf(
            TEXT("Unknown command: %s"), *Command));
    }
```

**4. Add Your Command Registration:**
```cpp
    else if (Command == "execute_python")
    {
        Response = HandleExecutePython(Request);
    }

    // ⬅️ YOUR NEW COMMAND:
    else if (Command == "set_actor_label")
    {
        Response = HandleSetActorLabel(Request);
    }

    else  // Unknown command
    {
        Response = CreateErrorResponse(FString::Printf(
            TEXT("Unknown command: %s"), *Command));
    }
```

---

### Critical Requirements

✅ **CORRECT:**
```cpp
else if (Command == "set_actor_label")  // Exact match with Python
{
    Response = HandleSetActorLabel(Request);  // Call your handler
}
```

❌ **WRONG - Missing "else":**
```cpp
if (Command == "set_actor_label")  // ❌ Breaks chain!
{
    Response = HandleSetActorLabel(Request);
}
```

❌ **WRONG - Typo in command name:**
```cpp
else if (Command == "set_actor_lable")  // ❌ Typo: "lable"
{
    Response = HandleSetActorLabel(Request);
}
```

❌ **WRONG - Case mismatch:**
```cpp
else if (Command == "Set_Actor_Label")  // ❌ Python uses lowercase
{
    Response = HandleSetActorLabel(Request);
}
```

---

### Verification Checklist

```
[ ] Added else if block before final else
[ ] Command string EXACTLY matches Python send_command() string
[ ] Handler function name matches actual function
[ ] else if (not just if)
[ ] Response variable assigned
[ ] Proper C++ syntax (semicolons, braces)
```

---

## Step 4: Compile C++ Plugin

### Pre-Compilation Checklist

```
[ ] All C++ code saved
[ ] Bridge registration added
[ ] Unreal Editor CLOSED (critical!)
[ ] No compilation errors expected
```

---

### Close Unreal Editor (CRITICAL!)

**Why:** DLL locking prevents compilation if Unreal is open

**Verify:**
```bash
tasklist | findstr "UnrealEditor"
```

**If found:**
- Close Unreal Editor normally (File → Exit)
- Wait for process to fully exit
- Verify again

---

### Build Command

```bash
# Navigate to project root
cd <UNREAL_MCP_DIR>

# Run build (PowerShell)
powershell -Command "& 'C:\Program Files\Epic Games\UE_5.5\Engine\Build\BatchFiles\Build.bat' MCPGameProjectEditor Win64 Development 'MCPGameProject\MCPGameProject.uproject' -WaitMutex"
```

**Expected Output:**
```
Building MCPGameProjectEditor...
Parsing headers for MCPGameProjectEditor
  Running UnrealHeaderTool MCPGameProjectEditor...
  ...
Compiling with Visual C++ ...
  ActorCommands.cpp
  UnrealMCPEditorCommands.cpp
  ...
BUILD SUCCESSFUL
Total build time: 15.3s
```

---

### Verify DLL Created

```bash
# Check DLL exists and timestamp is recent
ls MCPGameProject\Plugins\UnrealMCP\Binaries\Win64\UnrealEditor-UnrealMCP.dll

# Expected output shows file with timestamp from just now
```

---

### Common Compilation Errors

**Error: "Handler* is not defined"**
```
Solution: Add forward declaration to header or move handler to same file as RouteCommand
```

**Error: "Cannot access DLL file"**
```
Solution: Unreal Editor still running - close it and try again
```

**Error: "Syntax error in UnrealMCPEditorCommands.cpp"**
```
Solution: Check Bridge registration syntax (missing semicolon, brace, etc.)
```

---

## Step 5: Restart MCP Python Server

### Stop Existing Server

**If running in terminal:**
```
Press Ctrl+C
Wait for "Server stopped" message
```

**If background process:**
```bash
# Windows
tasklist | findstr "python"
taskkill /PID <process_id> /F
```

---

### Start MCP Server

```bash
cd <UNREAL_MCP_DIR>

uv --directory Python/ run unreal_mcp_server.py
```

**Expected Output:**
```
Loading MCP tools...
Connecting to Unreal at localhost:55557...
Connected to Unreal at localhost:55557
MCP server running...
Available tools: spawn_actor, set_actor_transform, execute_python, set_actor_label, ...
```

---

### Verify Connection

**Check TCP connection:**
```bash
netstat -an | findstr "55557"
# Expected: ESTABLISHED connection to 127.0.0.1:55557
```

**Check MCP logs:**
```
Should see your new tool listed in "Available tools"
```

---

## Step 6: Test Tool from Claude Code

### Basic Test

**In Claude Code conversation:**
```python
# Invoke your new tool
result = mcp__unreal-mcp__set_actor_label(
    actor_name="Cube_42",
    new_label="MyCube"
)

print(result)
```

**Expected Success Response:**
```json
{
  "status": "success",
  "message": "Label set successfully",
  "actor_name": "Cube_42",
  "old_label": "Cube_42",
  "new_label": "MyCube"
}
```

---

### Test Error Cases

**Test with invalid actor:**
```python
result = mcp__unreal-mcp__set_actor_label(
    actor_name="NonExistentActor",
    new_label="Test"
)

print(result)
# Expected: {"status": "error", "message": "Actor not found: NonExistentActor"}
```

**Test with empty parameter:**
```python
result = mcp__unreal-mcp__set_actor_label(
    actor_name="",
    new_label="Test"
)

print(result)
# Expected: {"status": "error", "message": "actor_name is required"}
```

---

### Common Test Failures

**Error: "Unknown command: set_actor_label"**
```
Cause: Bridge registration missing or typo
Solution: Go back to Step 3, verify Bridge registration
```

**Error: "Connection to localhost:55557 failed"**
```
Cause: Unreal Editor not running or plugin not enabled
Solution: Start Unreal Editor, enable UnrealMCP plugin
```

**Error: "Failed to parse response"**
```
Cause: C++ handler returns invalid JSON
Solution: Use CreateSuccessResponse() helper, don't manually construct JSON
```

---

## Step 7: Verify JSON Response

### Response Validation Checklist

```
[ ] Response is valid JSON (parseable)
[ ] Contains "status" field ("success" or "error")
[ ] Success responses contain expected data fields
[ ] Error responses contain descriptive "message"
[ ] All data types correct (strings, numbers, booleans)
[ ] No undefined or null where not expected
```

---

### Test Valid JSON

```python
import json

result = mcp__unreal-mcp__set_actor_label(
    actor_name="Cube_42",
    new_label="MyCube"
)

# Verify it's a dictionary (parsed JSON)
print(type(result))  # Should be: <class 'dict'>

# Verify status field exists
assert "status" in result
assert result["status"] in ["success", "error"]

# If success, verify expected fields
if result["status"] == "success":
    assert "actor_name" in result
    assert "new_label" in result
    print("✅ Response is valid JSON with expected fields")
else:
    assert "message" in result
    print(f"❌ Error: {result['message']}")
```

---

### Test Edge Cases

**Empty strings:**
```python
result = mcp__unreal-mcp__set_actor_label(actor_name="", new_label="Test")
# Should return error, not crash
```

**Special characters:**
```python
result = mcp__unreal-mcp__set_actor_label(
    actor_name="Cube_42",
    new_label="My<>Label:With/Special\\Chars"
)
# Should handle safely
```

**Very long strings:**
```python
result = mcp__unreal-mcp__set_actor_label(
    actor_name="Cube_42",
    new_label="A" * 1000
)
# Should work or return reasonable error
```

---

## Step 8: Document in MCP_Capabilities

### Location

**File:** `UnrealEngine/unreal-mcp-main/MCP_Capabilities_UE55.md`

### Find Appropriate Section

```markdown
## Actor Tools

### spawn_actor
...

### set_actor_transform
...

### ⬅️ ADD YOUR TOOL HERE (in alphabetical order)
```

---

### Documentation Template

```markdown
### set_actor_label

**Purpose:** Set the display label of an actor in the Unreal Editor.

**Parameters:**
- `actor_name` (string, required): Name of the actor to modify
- `new_label` (string, required): New display label to assign

**Returns:**
- `status` (string): "success" or "error"
- `message` (string): Result description
- `actor_name` (string): Name of the modified actor
- `old_label` (string): Previous label (on success)
- `new_label` (string): New label (on success)

**Example:**
```python
result = mcp__unreal-mcp__set_actor_label(
    actor_name="StaticMeshActor_42",
    new_label="HeroCube"
)

# Success response:
{
  "status": "success",
  "message": "Label set successfully",
  "actor_name": "StaticMeshActor_42",
  "old_label": "StaticMeshActor_42",
  "new_label": "HeroCube"
}
```

**Error Cases:**
- Actor not found: `{"status": "error", "message": "Actor not found: ActorName"}`
- Empty parameter: `{"status": "error", "message": "actor_name is required"}`

**Added:** 2025-10-25
**Tested:** Yes
```

---

## Common Mistakes at Each Step

### Step 1: Python Tool Mistakes

❌ **Forgot @mcp.tool() decorator:**
```python
def set_actor_label(...):  # ❌ Not exposed as MCP tool
    pass
```

✅ **Correct:**
```python
@mcp.tool()  # ✅ Properly decorated
def set_actor_label(...):
    pass
```

---

❌ **Missing Context parameter:**
```python
@mcp.tool()
def set_actor_label(actor_name: str):  # ❌ No ctx parameter
    pass
```

✅ **Correct:**
```python
@mcp.tool()
def set_actor_label(ctx: Context, actor_name: str):  # ✅ ctx first
    pass
```

---

❌ **Command name mismatch:**
```python
@mcp.tool()
def set_actor_label(ctx: Context, actor_name: str):
    result = unreal.send_command("set_label", {...})  # ❌ Different name
```

✅ **Correct:**
```python
@mcp.tool()
def set_actor_label(ctx: Context, actor_name: str):
    result = unreal.send_command("set_actor_label", {...})  # ✅ Match function name
```

---

### Step 2: C++ Handler Mistakes

❌ **Returning non-JSON:**
```cpp
FString HandleSetActorLabel(...)
{
    return "Success";  // ❌ Not JSON!
}
```

✅ **Correct:**
```cpp
FString HandleSetActorLabel(...)
{
    return CreateSuccessResponse("Success");  // ✅ Valid JSON
}
```

---

❌ **Not handling errors:**
```cpp
AActor* Actor = FindActor(ActorName);
Actor->SetActorLabel(NewLabel);  // ❌ Crashes if Actor is nullptr!
```

✅ **Correct:**
```cpp
AActor* Actor = FindActor(ActorName);
if (!Actor)
{
    return CreateErrorResponse("Actor not found");  // ✅ Graceful error
}
Actor->SetActorLabel(NewLabel);
```

---

### Step 3: Bridge Registration Mistakes

❌ **Completely forgot to register:**
```cpp
// (No registration at all in RouteCommand)
// Result: "Unknown command" error
```

❌ **Typo in command name:**
```cpp
else if (Command == "set_actor_lable")  // ❌ Typo: "lable"
```

❌ **Missing "else":**
```cpp
if (Command == "set_actor_label")  // ❌ Should be "else if"
```

✅ **Correct:**
```cpp
else if (Command == "set_actor_label")  // ✅ Exact match, proper chain
{
    Response = HandleSetActorLabel(Request);
}
```

---

### Step 4: Compilation Mistakes

❌ **Unreal Editor still running:**
```
Error: Cannot access DLL file (locked by Unreal)
```
✅ **Close Unreal first!**

❌ **Wrong build target:**
```bash
Build.bat MCPGameProject ...  # ❌ Should be MCPGameProjectEditor
```

✅ **Correct:**
```bash
Build.bat MCPGameProjectEditor Win64 Development ...
```

---

## Testing Procedures

### Unit Test (Individual Handler)

Test C++ handler independently before integration:

```cpp
// In a test function or console command
void TestSetActorLabel()
{
    // Build test request
    TSharedPtr<FJsonObject> TestRequest = MakeShared<FJsonObject>();
    TestRequest->SetStringField("actor_name", "Cube");
    TestRequest->SetStringField("new_label", "TestCube");

    // Call handler
    FString Response = HandleSetActorLabel(TestRequest);

    // Parse and verify response
    TSharedPtr<FJsonObject> ResponseJson;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response);
    FJsonSerializer::Deserialize(Reader, ResponseJson);

    FString Status = ResponseJson->GetStringField("status");
    UE_LOG(LogTemp, Log, TEXT("Status: %s"), *Status);

    // Verify actor label changed
    // ...
}
```

---

### Integration Test (Full Stack)

Test entire flow from Claude Code to Unreal:

```python
# Test valid input
result = mcp__unreal-mcp__set_actor_label(
    actor_name="Cube",
    new_label="MyCube"
)
assert result["status"] == "success"
assert result["new_label"] == "MyCube"
print("✅ Valid input test passed")

# Test error case
result = mcp__unreal-mcp__set_actor_label(
    actor_name="NonExistent",
    new_label="Test"
)
assert result["status"] == "error"
assert "not found" in result["message"].lower()
print("✅ Error case test passed")

# Test edge case
result = mcp__unreal-mcp__set_actor_label(
    actor_name="Cube",
    new_label=""
)
assert result["status"] == "error"
assert "required" in result["message"].lower()
print("✅ Edge case test passed")
```

---

### Performance Test

```python
import time

# Measure single invocation
start = time.time()
result = mcp__unreal-mcp__set_actor_label(
    actor_name="Cube",
    new_label="Test"
)
duration = time.time() - start

print(f"Duration: {duration:.3f}s")
# Expected: <0.1s for simple operations
# Expected: <1.0s for complex operations
```

---

## Complete Example: set_actor_label

### Python Tool

```python
# File: Python/tools/actor_tools.py

from typing import Dict, Any
from mcp import Context
from connection import get_unreal_connection

@mcp.tool()
def set_actor_label(
    ctx: Context,
    actor_name: str,
    new_label: str
) -> Dict[str, Any]:
    """
    Set the display label of an actor in the Unreal Editor.

    The actor label is what appears in the World Outliner. This does not
    change the actor's internal name, only its display label.

    Args:
        actor_name: Internal name of the actor (e.g., "StaticMeshActor_42")
        new_label: New label to display in World Outliner (e.g., "HeroCube")

    Returns:
        Dictionary with status, message, and label information

    Example:
        result = mcp__unreal-mcp__set_actor_label(
            actor_name="StaticMeshActor_42",
            new_label="HeroCube"
        )
    """
    unreal = get_unreal_connection()

    result = unreal.send_command("set_actor_label", {
        "actor_name": actor_name,
        "new_label": new_label
    })

    return result
```

---

### C++ Handler

```cpp
// File: Source/UnrealMCP/Private/Commands/ActorCommands.cpp

#include "UnrealMCPCommonUtils.h"
#include "Editor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"

FString HandleSetActorLabel(const TSharedPtr<FJsonObject>& Request)
{
    // Extract parameters
    FString ActorName = Request->GetStringField("actor_name");
    FString NewLabel = Request->GetStringField("new_label");

    // Validate parameters
    if (ActorName.IsEmpty())
    {
        return CreateErrorResponse("Parameter 'actor_name' is required and cannot be empty");
    }

    if (NewLabel.IsEmpty())
    {
        return CreateErrorResponse("Parameter 'new_label' is required and cannot be empty");
    }

    // Get editor world
    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (!World)
    {
        return CreateErrorResponse("No active world found in editor");
    }

    // Find actor by name
    AActor* FoundActor = nullptr;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (Actor && Actor->GetName() == ActorName)
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

    // Store old label
    FString OldLabel = FoundActor->GetActorLabel();

    // Set new label
    FoundActor->SetActorLabel(NewLabel);

    // Build success response
    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("message", "Actor label set successfully");
    ResultJson->SetStringField("actor_name", ActorName);
    ResultJson->SetStringField("old_label", OldLabel);
    ResultJson->SetStringField("new_label", NewLabel);

    return CreateSuccessResponse(ResultJson);
}
```

---

### Bridge Registration

```cpp
// File: Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp

FString FUnrealMCPEditorCommands::RouteCommand(const FString& Command,
                                                const TSharedPtr<FJsonObject>& Request)
{
    FString Response;

    // ... existing commands ...

    else if (Command == "set_actor_transform")
    {
        Response = HandleSetActorTransform(Request);
    }
    else if (Command == "set_actor_label")  // ⬅️ NEW REGISTRATION
    {
        Response = HandleSetActorLabel(Request);
    }
    else if (Command == "execute_python")
    {
        Response = HandleExecutePython(Request);
    }

    // ... rest of function ...
}
```

---

### Test Script

```python
# Test set_actor_label tool

# Step 1: Create a test actor
spawn_result = mcp__unreal-mcp__spawn_actor(
    actor_class="/Script/Engine.StaticMeshActor",
    location={"x": 0, "y": 0, "z": 0}
)

actor_name = spawn_result["actor_name"]
print(f"Created test actor: {actor_name}")

# Step 2: Test setting label (valid)
result = mcp__unreal-mcp__set_actor_label(
    actor_name=actor_name,
    new_label="TestCube"
)

print("Test 1 - Valid input:")
print(f"  Status: {result['status']}")
print(f"  Old label: {result['old_label']}")
print(f"  New label: {result['new_label']}")
assert result["status"] == "success"
assert result["new_label"] == "TestCube"
print("  ✅ PASSED")

# Step 3: Test error case (actor not found)
result = mcp__unreal-mcp__set_actor_label(
    actor_name="NonExistentActor",
    new_label="Test"
)

print("\nTest 2 - Actor not found:")
print(f"  Status: {result['status']}")
print(f"  Message: {result['message']}")
assert result["status"] == "error"
assert "not found" in result["message"].lower()
print("  ✅ PASSED")

# Step 4: Test edge case (empty label)
result = mcp__unreal-mcp__set_actor_label(
    actor_name=actor_name,
    new_label=""
)

print("\nTest 3 - Empty label:")
print(f"  Status: {result['status']}")
print(f"  Message: {result['message']}")
assert result["status"] == "error"
assert "required" in result["message"].lower()
print("  ✅ PASSED")

print("\n✅ ALL TESTS PASSED!")
```

---

## Summary

**8-Step Workflow Recap:**

1. ✅ Create Python MCP tool (@mcp.tool(), type hints, send_command)
2. ✅ Create C++ handler (extract params, validate, execute, return JSON)
3. ✅ **Register in Bridge (MOST FORGOTTEN STEP!)**
4. ✅ Compile C++ plugin (close Unreal first, Build.bat)
5. ✅ Restart MCP server (uv run unreal_mcp_server.py)
6. ✅ Test from Claude Code (verify invocation works)
7. ✅ Verify JSON response (valid structure, error cases)
8. ✅ Document in MCP_Capabilities (parameters, examples, errors)

**Critical Reminders:**

- **Step 3 is forgotten 90% of the time** - Always add Bridge registration!
- **Close Unreal before compiling** - Avoid DLL locking errors
- **Command names must match EXACTLY** - Python, Bridge, and handler aligned
- **Use CreateSuccessResponse/CreateErrorResponse** - Never manually construct JSON
- **Test error cases** - Don't just test happy path

**For deeper information:**
- **two_layer_routing.md** - Bridge pattern deep dive
- **debugging_guide.md** - Systematic troubleshooting
- **architecture_overview.md** - Three-layer system understanding

---

**Last Updated:** 2025-10-25
**Part of:** unreal-mcp-development skill (v1.0.0)
