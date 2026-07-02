---
name: unreal-mcp-development
description: Develop and extend Unreal MCP server including adding tools, debugging, architecture understanding, and C++/Python integration. Use when creating MCP tools, debugging MCP errors, extending UnrealMCP, or when user mentions "mcp tool", "unreal mcp", "bridge routing", "execute_python".
allowed-tools: Read,Write,Bash
---

# Unreal MCP Development

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Dependencies:** Unreal Engine 5.5+, Python 3.12+, FastMCP, Visual Studio 2022, UnrealMCP Plugin

---

## 🚨 CRITICAL: BRIDGE ROUTING REGISTRATION

**⚠️ MOST FORGOTTEN STEP WHEN ADDING MCP TOOLS ⚠️**

```
WITHOUT BRIDGE REGISTRATION:
❌ "Unknown command: your_tool_name"

WITH BRIDGE REGISTRATION:
✅ Tool executes successfully
```

**Where to register:**
```cpp
// File: UnrealMCPEditorCommands.cpp
// Function: RouteCommand()

else if (Command == "your_tool_name")  // ⬅️ ADD THIS!
{
    Response = HandleYourToolName(Request);
}
```

**Why critical:** The Bridge routes commands to handlers. Without registration, Unreal doesn't know which handler to call, resulting in "Unknown command" errors even when your Python and C++ code is perfect.

---

## Quick Start

### Example 1: Add Simple MCP Tool

**Python Side** (`Python/tools/actor_tools.py`):
```python
@mcp.tool()
def set_actor_label(ctx: Context, actor_name: str, new_label: str) -> Dict[str, Any]:
    """Set actor's display label in Unreal"""
    unreal = get_unreal_connection()
    result = unreal.send_command("set_actor_label", {
        "actor_name": actor_name,
        "new_label": new_label
    })
    return result
```

**C++ Handler** (`Commands/ActorCommands.cpp`):
```cpp
FString HandleSetActorLabel(const TSharedPtr<FJsonObject>& Request)
{
    FString ActorName = Request->GetStringField("actor_name");
    FString NewLabel = Request->GetStringField("new_label");

    AActor* Actor = FindActorByName(ActorName);
    if (Actor)
    {
        Actor->SetActorLabel(NewLabel);
        return CreateSuccessResponse(FString::Printf(TEXT("Label set to %s"), *NewLabel));
    }
    return CreateErrorResponse("Actor not found");
}
```

**⚠️ CRITICAL: Bridge Registration** (`UnrealMCPEditorCommands.cpp`):
```cpp
// In RouteCommand() function:
else if (Command == "set_actor_label")  // ⬅️ MUST ADD THIS!
{
    Response = HandleSetActorLabel(Request);
}
```

---

### Example 2: Debug Connection Failure

```bash
# 1. Check Unreal Editor running
tasklist | findstr "UnrealEditor"

# 2. Check plugin enabled
# In Unreal: Edit → Plugins → "UnrealMCP" → Enabled?

# 3. Check TCP port
netstat -an | findstr "55557"
# Should show: LISTENING

# 4. Check MCP server running
uv --directory Python/ run unreal_mcp_server.py
```

---

### Example 3: execute_python Pattern

**JSON Output:**
```python
script = '''
import unreal
import json

actors = unreal.EditorLevelLibrary.get_all_level_actors()
result = {"count": len(actors), "names": [a.get_name() for a in actors[:5]]}
print(json.dumps(result))
'''

result = mcp__unreal-mcp__execute_python(script=script)
data = json.loads(result["output"])
print(f"Found {data['count']} actors")
```

---

## Standard Workflows

### Workflow 1: Add New MCP Tool (8-Step Checklist)

```
⚠️ CRITICAL CHECKLIST:
[ ] Step 1: Create Python MCP tool (@mcp.tool())
[ ] Step 2: Create C++ handler function
[ ] Step 3: ⚠️ REGISTER IN BRIDGE (UnrealMCPEditorCommands.cpp) ⚠️
[ ] Step 4: Compile C++ plugin
[ ] Step 5: Restart MCP Python server
[ ] Step 6: Test tool from Claude Code
[ ] Step 7: Verify JSON response
[ ] Step 8: Document in MCP_Capabilities_UE55.md
```

---

**Step 1: Python Tool** (`Python/tools/your_category.py`):
```python
@mcp.tool()
def your_tool_name(ctx: Context, param1: str, param2: int) -> Dict[str, Any]:
    """Tool description"""
    unreal = get_unreal_connection()
    return unreal.send_command("your_tool_name", {"param1": param1, "param2": param2})
```

**Step 2: C++ Handler** (`Commands/YourHandler.cpp`):
```cpp
FString HandleYourToolName(const TSharedPtr<FJsonObject>& Request)
{
    FString Param1 = Request->GetStringField("param1");
    int32 Param2 = Request->GetIntegerField("param2");

    // Implementation logic

    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("message", "Success");
    return CreateSuccessResponse(ResultJson);
}
```

**Step 3: Bridge Registration** (`UnrealMCPEditorCommands.cpp`):
```cpp
┌────────────────────────────────────────┐
│  ⚠️ THIS IS THE STEP PEOPLE FORGET ⚠️  │
│                                        │
│  Without this: "Unknown command" ❌    │
│  With this: Tool works ✅              │
└────────────────────────────────────────┘

// In RouteCommand():
else if (Command == "your_tool_name")  // ⬅️ ADD THIS!
{
    Response = HandleYourToolName(Request);
}
```

**Step 4: Compile:**
```bash
# Close Unreal Editor first!
powershell -Command "& 'C:\Program Files\Epic Games\UE_5.5\Engine\Build\BatchFiles\Build.bat' MCPGameProjectEditor Win64 Development 'MCPGameProject\MCPGameProject.uproject'"
```

**Step 5: Restart MCP Server:**
```bash
uv --directory Python/ run unreal_mcp_server.py
```

**Step 6-7: Test:**
```python
result = mcp__unreal-mcp__your_tool_name(param1="test", param2=42)
print(result)  # Verify JSON structure
```

**Step 8: Document** in `MCP_Capabilities_UE55.md`

---

### Workflow 2: Debug "Unknown command" Error

**⚠️ #1 Most Common Error - Bridge Registration Missing**

**Checklist:**
1. Verify Unreal Editor running: `tasklist | findstr "UnrealEditor"`
2. Check plugin enabled: Edit → Plugins → "UnrealMCP"
3. Check TCP connection: `netstat -an | findstr "55557"`
4. **⚠️ CRITICAL: Check Bridge Registration:**
   - Open `UnrealMCPEditorCommands.cpp`
   - Search for `else if (Command == "tool_name")`
   - If NOT found: Add registration block
5. Recompile plugin (close Unreal first!)
6. Restart MCP server
7. Test again

---

### Workflow 3: execute_python Patterns

**Pattern 1: Structured JSON Output**
```python
script = '''
import unreal
import json
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print(json.dumps({"total": len(actors), "names": [a.get_name() for a in actors[:5]]}))
'''
result = mcp__unreal-mcp__execute_python(script=script)
data = json.loads(result["output"])
```

**Pattern 2: Error Handling**
```python
script = '''
import unreal
try:
    # Risky operation
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {str(e)}")
'''
result = mcp__unreal-mcp__execute_python(script=script)
if "ERROR" in result["output"]:
    print("Failed:", result["output"])
```

---

### Workflow 4: Compile and Deploy

**Pre-Build:**
```bash
# 1. Close Unreal Editor (REQUIRED!)
tasklist | findstr "UnrealEditor"  # Must be empty

# 2. Stop MCP server (Ctrl+C)
```

**Build:**
```bash
cd UnrealEngine\unreal-mcp-main
powershell -Command "& 'C:\Program Files\Epic Games\UE_5.5\Engine\Build\BatchFiles\Build.bat' MCPGameProjectEditor Win64 Development 'MCPGameProject\MCPGameProject.uproject'"
```

**Verify:**
```bash
ls MCPGameProject\Plugins\UnrealMCP\Binaries\Win64\UnrealEditor-UnrealMCP.dll
# Check recent timestamp
```

**Deploy:**
```bash
# Restart MCP server
uv --directory Python/ run unreal_mcp_server.py

# Launch Unreal Editor
# Test changes in Claude Code
```

---

## Troubleshooting

### Issue 1: Connection Failed (localhost:55557)

**Symptoms:** All MCP tools fail, "Connection refused"

**Causes:** Unreal not running, plugin not enabled, port blocked

**Fix:**
1. Launch Unreal Editor with MCPGameProject.uproject
2. Edit → Plugins → Enable "UnrealMCP" → Restart
3. Verify TCP: `netstat -an | findstr "55557"` (should show LISTENING)
4. Check Unreal Output Log for "UnrealMCP server listening on port 55557"

---

### Issue 2: "Unknown command: tool_name" (MOST COMMON!)

```
┌─────────────────────────────────────────┐
│ ⚠️  #1 MOST COMMON ERROR  ⚠️            │
│                                         │
│ Cause: Bridge routing not registered    │
│ File: UnrealMCPEditorCommands.cpp       │
│ Function: RouteCommand()                │
└─────────────────────────────────────────┘
```

**Fix:**
1. Open `UnrealMCPEditorCommands.cpp`
2. Search for `else if (Command == "tool_name")`
3. If NOT found, add:
```cpp
else if (Command == "tool_name")
{
    Response = HandleToolName(Request);
}
```
4. Recompile (close Unreal first!)
5. Restart MCP server
6. Test again

---

### Issue 3: "Failed to parse response"

**Cause:** C++ handler returns invalid JSON

**Fix:**
```cpp
// ❌ WRONG: Manual JSON
FString Response = FString::Printf(TEXT("{result: %s}"), *Value);

// ✅ CORRECT: Use helpers
TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
ResultJson->SetStringField("result", Value);
return CreateSuccessResponse(ResultJson);
```

---

### Issue 4: Command Timeout

**Cause:** Operation takes >30 seconds

**Workarounds:**
- Break into smaller operations (batch processing)
- Use execute_python with progress prints
- Check reference/debugging_guide.md for async patterns

---

## MCP Architecture

### Three-Layer System

```
┌─────────────────────────────────────────┐
│  Layer 3: Claude Code (MCP Client)      │
│  - Tool invocation                      │
│  - JSON communication                   │
└──────────────┬──────────────────────────┘
               │ MCP Protocol (FastMCP)
┌──────────────▼──────────────────────────┐
│  Layer 2: Python MCP Server             │
│  - FastMCP implementation               │
│  - Tool wrappers (@mcp.tool())          │
│  - TCP client → localhost:55557         │
└──────────────┬──────────────────────────┘
               │ TCP/JSON
┌──────────────▼──────────────────────────┐
│  Layer 1: C++ Plugin (UnrealMCP)        │
│  - TCP server (port 55557)              │
│  - ⚠️ Bridge routing (CRITICAL!) ⚠️     │
│  - Command handlers                     │
│  - Unreal Engine integration            │
└─────────────────────────────────────────┘
```

### Two-Layer Command Routing (CRITICAL)

```
Flow:
1. Python → TCP: {"command": "tool_name", "param": "value"}
2. C++ receives message
3. ⚠️ Bridge routes: if (Command == "tool_name") → Handler
4. Handler executes: HandleToolName(Request)
5. Handler returns: JSON response
6. Python receives response
7. Claude Code gets result
```

**Bridge Registration Example:**
```cpp
// UnrealMCPEditorCommands.cpp - RouteCommand()
if (Command == "spawn_actor")
{
    return HandleSpawnActor(Request);
}
else if (Command == "set_actor_transform")
{
    return HandleSetActorTransform(Request);
}
// ⬅️ YOUR NEW COMMAND GOES HERE!
else if (Command == "your_new_command")
{
    return HandleYourNewCommand(Request);
}
else
{
    return CreateErrorResponse("Unknown command");
}
```

**Critical Understanding:**
- Bridge = Dispatcher (routes commands to handlers)
- Handler = Implementation (does the work)
- Without bridge registration → "Unknown command" error
- Even if handler exists and is perfect!

---

## Reference Documentation

**architecture_overview.md** - Three-layer system deep dive
- TCP communication protocol
- JSON message format
- Connection lifecycle

**two_layer_routing.md** - Bridge + Handler pattern (CRITICAL!)
- Bridge routing requirements (most forgotten step!)
- Handler implementation patterns
- Response format standards

**adding_tools_workflow.md** - Complete 8-step guide with examples
- Python tool creation (FastMCP patterns)
- C++ handler creation (UE patterns)
- Testing procedures

**debugging_guide.md** - Systematic troubleshooting
- Connection issues (TCP, plugin, port)
- Routing failures (Bridge registration)
- JSON errors (parsing, format)

---

## Constitutional Compliance

### Articles I, III, IV, V, VIII ✅ PASS
- General purpose (all MCP tool types)
- Progressive disclosure (SKILL.md <500 lines, reference docs on-demand)
- Tested independently (Session_2025-10-23c_Final.md)
- Follow official patterns (MCP spec, FastMCP, UE plugin guide)
- Documentation standards (semantic versioning, all sections)

### Article VI: Context Efficiency ✅
```
Before: 2,000 lines (~10,000 tokens)
After: SKILL.md (490) + Reference (500 avg) = 990 lines (~4,950 tokens)
Savings: 51% reduction ✅
```

### Article VII ⊘ Not applicable (Unreal-specific)

---

## Version History

**v1.0.0** (2025-10-25) - Initial Release
- 8-step MCP tool creation workflow (⚠️ Bridge routing emphasis!)
- 4 common debugging issues with fixes
- execute_python patterns (JSON output, error handling)
- Three-layer architecture + two-layer routing (Bridge + Handler)
- Tested with set_actor_component_property workflow
- 51% context reduction, constitutional compliance: 6/9 articles

**Tested With:** Unreal Engine 5.5, Python 3.12, FastMCP 0.4.0
**Source:** Session_2025-10-23c_Final.md
