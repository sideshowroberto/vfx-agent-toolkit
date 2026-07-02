# MCP Debugging Guide: Systematic Troubleshooting

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Part of:** unreal-mcp-development skill

---

## Table of Contents

1. [Overview](#overview)
2. [Diagnostic Workflow](#diagnostic-workflow)
3. [Issue 1: Connection Failed](#issue-1-connection-failed)
4. [Issue 2: Unknown Command](#issue-2-unknown-command)
5. [Issue 3: Failed to Parse Response](#issue-3-failed-to-parse-response)
6. [Issue 4: Command Timeout](#issue-4-command-timeout)
7. [Log Analysis Techniques](#log-analysis-techniques)
8. [Diagnostic Commands](#diagnostic-commands)
9. [Common Error Messages](#common-error-messages)
10. [Prevention Checklist](#prevention-checklist)

---

## Overview

MCP debugging follows a **systematic layer-by-layer approach**. Errors can occur at any of the three layers:

```
Layer 3: Claude Code    → User interface errors, MCP protocol issues
Layer 2: Python MCP     → TCP connection, JSON formatting
Layer 1: C++ Plugin     → Routing failures, execution errors
```

**Debugging Philosophy:**
- Start at the lowest layer (connection)
- Work upward (routing → execution → response)
- Eliminate possibilities systematically
- Use logs to narrow down the issue

---

## Diagnostic Workflow

### Quick Triage

**Step 1: Classify the Error**

```
Error Message                        → Issue Category
────────────────────────────────────────────────────────
"Connection to localhost:55557..."   → Connection Failed
"Unknown command: tool_name"         → Routing Failure
"Failed to parse response"           → JSON Error
"Command timeout"                    → Timeout Issue
"Actor not found"                    → Execution Error (not MCP issue)
```

**Step 2: Check Layer Health**

```bash
# Layer 1: C++ Plugin (Unreal Editor)
tasklist | findstr "UnrealEditor"
# Expected: Process running

# Layer 2: Python MCP Server
# Check terminal: Should show "Connected to Unreal at localhost:55557"

# Layer 3: Claude Code
# Check if MCP tools are listed in Claude Code interface
```

**Step 3: Apply Specific Fix**

Jump to appropriate section based on error category:
- [Connection Failed](#issue-1-connection-failed)
- [Unknown Command](#issue-2-unknown-command)
- [Parse Error](#issue-3-failed-to-parse-response)
- [Timeout](#issue-4-command-timeout)

---

## Issue 1: Connection Failed

### Symptoms

```
Error: Connection to localhost:55557 failed
Error: Connection refused
Error: Cannot connect to Unreal
All MCP tools fail immediately
No response from Unreal
```

### Root Causes

1. Unreal Editor not running
2. UnrealMCP plugin not enabled
3. Port 55557 blocked or already in use
4. Firewall blocking localhost connection
5. Plugin failed to start TCP server

---

### Diagnostic Steps

**Step 1: Verify Unreal Editor Running**

```bash
# Windows
tasklist | findstr "UnrealEditor"

# Expected output:
UnrealEditor.exe      12345 Console    1    2,500,000 K

# If NO output: Unreal Editor is not running
```

**Fix if not running:**
```
1. Launch Unreal Editor
2. Open MCPGameProject.uproject
3. Wait for editor to fully load (Project browser closes)
4. Check Output Log for "UnrealMCP server listening on port 55557"
```

---

**Step 2: Verify Plugin Enabled**

```
1. In Unreal Editor: Edit → Plugins
2. Search for "UnrealMCP"
3. Check: Enabled checkbox is checked
4. If not enabled:
   - Click checkbox
   - Click "Restart Now" button
   - Wait for editor to restart
```

**Alternative check (Output Log):**
```
Window → Developer Tools → Output Log
Search for: "UnrealMCP"

Expected:
LogModuleManager: Loading module 'UnrealMCP'
LogTemp: UnrealMCP server listening on port 55557
```

---

**Step 3: Verify TCP Port Listening**

```bash
# Windows
netstat -an | findstr "55557"

# Expected output:
TCP    0.0.0.0:55557         0.0.0.0:0              LISTENING

# Breakdown:
# 0.0.0.0:55557  = Server listening on all interfaces, port 55557
# LISTENING      = Accepting connections
```

**If NO output (not listening):**
```
Cause: Plugin not starting TCP server

Fixes:
1. Check Unreal Output Log for errors:
   - Search for "UnrealMCP" or "TCP" or "55557"
   - Look for error messages (red text)

2. Plugin may have failed to load:
   - Edit → Plugins → Search "UnrealMCP"
   - Check for errors (red X icon)
   - Try: Disable → Restart → Enable → Restart

3. Recompile plugin:
   - Close Unreal
   - Run Build.bat (see Step 4 in adding_tools_workflow.md)
   - Reopen Unreal
```

**If output shows ESTABLISHED (already connected):**
```
TCP    127.0.0.1:55557       127.0.0.1:54321        ESTABLISHED

This is GOOD - Python MCP server is already connected!
```

**If output shows port in use by different process:**
```bash
netstat -ano | findstr "55557"
# Note the PID (last column)

tasklist | findstr "<PID>"
# Identify the process

# If it's not UnrealEditor.exe:
# Kill the conflicting process or change port in plugin settings
```

---

**Step 4: Test Manual TCP Connection**

```python
# Quick Python test (run in separate terminal)
import socket

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 55557))
    print("✅ Connection successful!")
    sock.close()
except ConnectionRefusedError:
    print("❌ Connection refused - server not listening")
except Exception as e:
    print(f"❌ Error: {e}")
```

**If connection successful:**
```
TCP layer is working!
Problem is likely in Python MCP server or tool invocation.
```

**If connection refused:**
```
Go back to Steps 1-3 (Unreal not running or plugin not enabled)
```

---

**Step 5: Check Firewall**

```bash
# Windows Firewall (rare issue on localhost, but possible)

# Allow UnrealEditor through firewall:
1. Windows Security → Firewall & network protection
2. Allow an app through firewall
3. Find "UnrealEditor.exe"
4. Check both "Private" and "Public" networks
5. OK

# Or disable firewall temporarily to test (re-enable after!)
```

---

### Complete Fix Workflow

```
┌─────────────────────────────────────────┐
│ 1. Start Unreal Editor                  │
│    - Open MCPGameProject.uproject       │
│    - Wait for full load                 │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 2. Enable UnrealMCP Plugin              │
│    - Edit → Plugins → UnrealMCP         │
│    - Enable → Restart                   │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 3. Verify TCP Listening                 │
│    - netstat -an | findstr "55557"      │
│    - Should show LISTENING              │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 4. Start/Restart MCP Server             │
│    - uv --directory Python/ run ...     │
│    - Should see "Connected to Unreal"   │
└─────────────────┬───────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 5. Test Connection                      │
│    - mcp__unreal-mcp__execute_python    │
│    - Should get response                │
└─────────────────────────────────────────┘
```

---

## Issue 2: Unknown Command

### Symptoms

```
Error: Unknown command: set_actor_label
Error: Unknown command: your_new_tool
Status: "error"
Message: "Unknown command: ..."
```

**Critical Understanding:**
```
┌──────────────────────────────────────────────┐
│  THIS IS THE #1 MOST COMMON ERROR!          │
│                                              │
│  Cause: Bridge routing not registered        │
│  Location: UnrealMCPEditorCommands.cpp       │
│  Fix: Add else if block in RouteCommand()   │
└──────────────────────────────────────────────┘
```

---

### Root Causes

1. **Bridge routing not registered (90% of cases!)**
2. Command name typo (Python vs Bridge mismatch)
3. Plugin not recompiled after adding registration
4. MCP server not restarted after recompiling

---

### Diagnostic Steps

**Step 1: Verify Python Tool Exists**

```bash
# Search for tool definition
cd <UNREAL_MCP_DIR>

grep -r "def set_actor_label" Python/tools/
# Or use text editor search

# Expected: Find tool in Python/tools/actor_tools.py or similar
```

**If NOT found:**
```
Problem: Tool doesn't exist in Python
Solution: Create Python tool (see Step 1 in adding_tools_workflow.md)
```

**If found:**
```
✅ Python tool exists
Continue to Step 2
```

---

**Step 2: Verify C++ Handler Exists**

```bash
# Search for handler implementation
grep -r "HandleSetActorLabel" Source/

# Expected: Find handler in Source/UnrealMCP/Private/Commands/*.cpp
```

**If NOT found:**
```
Problem: Handler doesn't exist in C++
Solution: Create C++ handler (see Step 2 in adding_tools_workflow.md)
```

**If found:**
```
✅ C++ handler exists
Continue to Step 3
```

---

**Step 3: Check Bridge Registration (CRITICAL!)**

```bash
# Search for Bridge registration
grep "set_actor_label" Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp

# Expected output (if registered):
else if (Command == "set_actor_label")
    Response = HandleSetActorLabel(Request);
```

**If NO results found:**
```
❌ PROBLEM IDENTIFIED: Bridge registration MISSING!

This is the issue! Handler exists but is not registered in Bridge.
```

**Fix:**
```cpp
// Open: Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp
// Find: FString FUnrealMCPEditorCommands::RouteCommand(...)

// Locate the end of the command list (before final else)
else if (Command == "execute_python")
{
    Response = HandleExecutePython(Request);
}

// ⬅️ ADD THIS BLOCK:
else if (Command == "set_actor_label")
{
    Response = HandleSetActorLabel(Request);
}

else  // Unknown command handler (keep at end!)
{
    Response = CreateErrorResponse(FString::Printf(
        TEXT("Unknown command: %s"), *Command));
}
```

**After adding registration:**
```
1. Save file
2. Close Unreal Editor
3. Recompile plugin (Build.bat)
4. Restart MCP server
5. Test again
```

---

**Step 4: Verify Command Name Match**

**Python side:**
```python
# In Python/tools/actor_tools.py
@mcp.tool()
def set_actor_label(...):
    result = unreal.send_command("set_actor_label", {...})
    #                             ↑ This string
```

**C++ Bridge:**
```cpp
// In UnrealMCPEditorCommands.cpp
else if (Command == "set_actor_label")  // ← Must match EXACTLY!
```

**Common mismatches:**

❌ **Case difference:**
```python
unreal.send_command("set_actor_label", ...)  # Python
```
```cpp
else if (Command == "Set_Actor_Label")  // ❌ Capital letters!
```

❌ **Underscore vs camelCase:**
```python
unreal.send_command("set_actor_label", ...)  # Python
```
```cpp
else if (Command == "setActorLabel")  // ❌ camelCase!
```

❌ **Typo:**
```python
unreal.send_command("set_actor_label", ...)  # Python
```
```cpp
else if (Command == "set_actor_lable")  // ❌ Typo: "lable"
```

✅ **Correct:**
```python
unreal.send_command("set_actor_label", ...)  # Python
```
```cpp
else if (Command == "set_actor_label")  // ✅ Exact match!
```

---

**Step 5: Verify Plugin Recompiled**

```bash
# Check DLL timestamp
ls MCPGameProject\Plugins\UnrealMCP\Binaries\Win64\UnrealEditor-UnrealMCP.dll

# Timestamp should be AFTER you added Bridge registration
```

**If timestamp is OLD (before registration):**
```
Problem: Plugin not recompiled with new registration

Solution:
1. Close Unreal Editor
2. Run Build.bat
3. Verify DLL timestamp updated
4. Reopen Unreal
```

---

**Step 6: Verify MCP Server Restarted**

```bash
# MCP server caches tool connections
# Must restart after C++ changes

# In MCP server terminal:
Ctrl+C  # Stop server

uv --directory Python/ run unreal_mcp_server.py  # Restart

# Should see:
# Connected to Unreal at localhost:55557
```

---

### Complete Fix Workflow

```
Issue: "Unknown command: set_actor_label"

┌─────────────────────────────────────────┐
│ 1. Check Python tool exists             │
│    grep "def set_actor_label" Python/   │
└────┬────────────────────────────────────┘
     │ ✅ Found
     ↓
┌─────────────────────────────────────────┐
│ 2. Check C++ handler exists             │
│    grep "HandleSetActorLabel" Source/   │
└────┬────────────────────────────────────┘
     │ ✅ Found
     ↓
┌─────────────────────────────────────────┐
│ 3. Check Bridge registration            │
│    grep "set_actor_label" ...Commands.cpp│
└────┬────────────────────────────────────┘
     │ ❌ NOT FOUND → ROOT CAUSE!
     ↓
┌─────────────────────────────────────────┐
│ 4. Add Bridge registration              │
│    else if (Command == "set_actor_label")│
│    { Response = Handle...; }            │
└────┬────────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────────────┐
│ 5. Close Unreal Editor                  │
└────┬────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ 6. Recompile plugin (Build.bat)         │
└────┬────────────────────────────────────┘
     │ ✅ BUILD SUCCESSFUL
     ↓
┌─────────────────────────────────────────┐
│ 7. Restart MCP server                   │
│    uv run unreal_mcp_server.py          │
└────┬────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ 8. Test tool again                      │
│    mcp__unreal-mcp__set_actor_label()   │
└────┬────────────────────────────────────┘
     │ ✅ WORKS!
     ↓
   FIXED
```

---

## Issue 3: Failed to Parse Response

### Symptoms

```
Error: Failed to parse response
Error: Invalid JSON
Error: Unexpected token in JSON
Python exception: json.decoder.JSONDecodeError
```

### Root Causes

1. C++ handler returns invalid JSON (manual string construction)
2. Missing quotes around JSON keys or values
3. Unescaped special characters in strings
4. Not using CreateSuccessResponse/CreateErrorResponse helpers

---

### Diagnostic Steps

**Step 1: Capture Raw Response**

**Modify Python tool temporarily:**
```python
@mcp.tool()
def set_actor_label(ctx: Context, actor_name: str, new_label: str):
    unreal = get_unreal_connection()

    # Send command
    raw_response = unreal.socket.recv(4096)  # Get raw bytes
    print(f"RAW RESPONSE: {raw_response.decode('utf-8')}")  # Print before parsing

    # Normal parsing
    result = unreal.send_command("set_actor_label", {...})
    return result
```

**Look for invalid JSON patterns:**
```
❌ BAD: {result: success}               (no quotes around keys)
❌ BAD: {"result": success}              (no quotes around value)
❌ BAD: {"message": "He said "hello""}  (unescaped quotes)
❌ BAD: {"message": "Path: C:\folder"}  (unescaped backslash)
✅ GOOD: {"result": "success"}
✅ GOOD: {"message": "He said \"hello\""}
```

---

**Step 2: Locate Handler Responsible**

```bash
# Find which handler is being called
# Check Unreal Output Log or MCP server logs

# Example: If testing set_actor_label
# Handler: HandleSetActorLabel in ActorCommands.cpp
```

---

**Step 3: Examine Handler's Return Statement**

**Open handler file and find return statements:**

❌ **WRONG: Manual JSON construction**
```cpp
FString HandleSetActorLabel(const TSharedPtr<FJsonObject>& Request)
{
    FString ActorName = Request->GetStringField("actor_name");

    // Manual JSON construction (BAD!)
    FString Response = FString::Printf(
        TEXT("{status: success, actor: %s}"), *ActorName);
    //     ↑ Missing quotes around keys!
    //     ↑ Missing quotes around values!
    return Response;
}
```

❌ **WRONG: Concatenation**
```cpp
FString Response = "{";
Response += "\"status\": \"success\",";
Response += "\"actor\": \"" + ActorName + "\"";  // ❌ If ActorName has quotes, breaks!
Response += "}";
return Response;
```

✅ **CORRECT: Use helper functions**
```cpp
FString HandleSetActorLabel(const TSharedPtr<FJsonObject>& Request)
{
    FString ActorName = Request->GetStringField("actor_name");

    // Build JSON object
    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("actor_name", ActorName);

    // Use helper (automatically handles escaping, quotes, etc.)
    return CreateSuccessResponse(ResultJson);
}
```

---

**Step 4: Fix Invalid JSON Construction**

**Replace manual construction with helper:**

**Before:**
```cpp
FString Response = FString::Printf(TEXT("{status: success}"));
return Response;
```

**After:**
```cpp
return CreateSuccessResponse("Operation successful");
```

---

**Before (complex):**
```cpp
FString Response = "{";
Response += "\"status\": \"success\",";
Response += "\"actor_name\": \"" + ActorName + "\",";
Response += "\"count\": " + FString::FromInt(Count);
Response += "}";
return Response;
```

**After:**
```cpp
TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
ResultJson->SetStringField("actor_name", ActorName);
ResultJson->SetNumberField("count", Count);

return CreateSuccessResponse(ResultJson);
```

---

**Step 5: Test JSON Validity**

**Use online JSON validator:**
```
1. Copy raw response from Step 1
2. Go to: https://jsonlint.com
3. Paste and click "Validate JSON"
4. If errors, see line/column of issue
```

**Or test in Python:**
```python
import json

response_str = '{"status": "success", "actor_name": "Cube"}'  # Your response

try:
    data = json.loads(response_str)
    print("✅ Valid JSON:", data)
except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON: {e}")
```

---

### Common JSON Errors

**Missing Quotes:**
```json
❌ {status: success}
✅ {"status": "success"}
```

**Trailing Comma:**
```json
❌ {"status": "success",}
✅ {"status": "success"}
```

**Unescaped Backslash:**
```json
❌ {"path": "C:\Folder"}
✅ {"path": "C:\\Folder"}
```

**Unescaped Quote:**
```json
❌ {"message": "He said "hi""}
✅ {"message": "He said \"hi\""}
```

**Single Quotes (not valid in JSON):**
```json
❌ {'status': 'success'}
✅ {"status": "success"}
```

---

### Complete Fix Workflow

```
Issue: "Failed to parse response"

┌─────────────────────────────────────────┐
│ 1. Capture raw response (add logging)   │
└────┬────────────────────────────────────┘
     │ Raw: {status: success}
     ↓
┌─────────────────────────────────────────┐
│ 2. Validate JSON (jsonlint.com)         │
└────┬────────────────────────────────────┘
     │ Error: Keys must be quoted!
     ↓
┌─────────────────────────────────────────┐
│ 3. Find handler in C++                  │
│    HandleSetActorLabel in Commands/     │
└────┬────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ 4. Examine return statement             │
│    FString::Printf manual JSON ❌        │
└────┬────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ 5. Replace with CreateSuccessResponse   │
│    return CreateSuccessResponse(...);   │
└────┬────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ 6. Recompile plugin                     │
└────┬────────────────────────────────────┘
     │ ✅ BUILD SUCCESSFUL
     ↓
┌─────────────────────────────────────────┐
│ 7. Restart MCP server                   │
└────┬────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ 8. Test again                           │
└────┬────────────────────────────────────┘
     │ ✅ Valid JSON received!
     ↓
   FIXED
```

---

## Issue 4: Command Timeout

### Symptoms

```
Error: Command timeout after 30 seconds
Error: Operation timed out
No response received from Unreal
MCP server appears frozen
```

### Root Causes

1. Long-running operation (>30 seconds)
2. Infinite loop in C++ handler
3. Blocking operation without progress updates
4. Large dataset processing

---

### Diagnostic Steps

**Step 1: Identify Timeout Threshold**

```python
# Default MCP timeout (varies by implementation)
# Typical: 30 seconds

# Check MCP server logs:
# "Command timeout after 30s"
```

---

**Step 2: Measure Operation Time**

**Add timing to C++ handler:**

```cpp
FString HandleLongOperation(const TSharedPtr<FJsonObject>& Request)
{
    // Start timer
    double StartTime = FPlatformTime::Seconds();

    // Your operation
    for (int i = 0; i < 10000; i++)
    {
        // Heavy processing...

        // Log progress every 1000 iterations
        if (i % 1000 == 0)
        {
            double Elapsed = FPlatformTime::Seconds() - StartTime;
            UE_LOG(LogTemp, Log, TEXT("Progress: %d/10000 (%.2fs elapsed)"), i, Elapsed);
        }
    }

    double TotalTime = FPlatformTime::Seconds() - StartTime;
    UE_LOG(LogTemp, Log, TEXT("Operation completed in %.2fs"), TotalTime);

    return CreateSuccessResponse("Done");
}
```

**Check Unreal Output Log for timing:**
```
LogTemp: Progress: 0/10000 (0.00s elapsed)
LogTemp: Progress: 1000/10000 (5.23s elapsed)
LogTemp: Progress: 2000/10000 (10.51s elapsed)
...
LogTemp: Operation completed in 52.34s  ← OVER 30s TIMEOUT!
```

---

**Step 3: Determine if Operation Can Be Optimized**

**Check for inefficiencies:**

❌ **Inefficient: Linear search for every actor**
```cpp
// Called 1000 times
for (int i = 0; i < 1000; i++)
{
    // Linear search O(n) inside loop = O(n²)!
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if ((*It)->GetName() == ActorNames[i])
        {
            // Process actor
        }
    }
}
```

✅ **Optimized: Build lookup map once**
```cpp
// Build map once O(n)
TMap<FString, AActor*> ActorMap;
for (TActorIterator<AActor> It(World); It; ++It)
{
    ActorMap.Add((*It)->GetName(), *It);
}

// Lookup O(1) per iteration = O(n) total
for (int i = 0; i < 1000; i++)
{
    if (AActor** FoundActor = ActorMap.Find(ActorNames[i]))
    {
        // Process actor
    }
}
```

---

### Workarounds

**Option 1: Break into Smaller Operations**

Instead of one large operation:
```python
# ❌ Times out
process_all_actors(10000)  # Takes 60 seconds
```

Break into batches:
```python
# ✅ Each batch completes quickly
for batch in range(0, 10000, 1000):
    process_actor_batch(batch, batch + 1000)  # Takes 6 seconds each
    print(f"Processed batch {batch}-{batch+1000}")
```

---

**Option 2: Use execute_python with Progress Logging**

```python
script = '''
import unreal

total = 1000
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for i, actor in enumerate(actors[:total]):
    # Process actor
    actor.set_actor_label(f"Actor_{i}")

    # Log progress every 100 actors
    if i % 100 == 0:
        print(f"Progress: {i}/{total}")

print(f"COMPLETE: Processed {total} actors")
'''

result = mcp__unreal-mcp__execute_python(script=script)

# Can see progress in output
print(result["output"])
# Progress: 0/1000
# Progress: 100/1000
# ...
# COMPLETE: Processed 1000 actors
```

---

**Option 3: Asynchronous Pattern (Future Enhancement)**

**Not currently supported, but roadmap includes:**

```python
# Start long operation (returns job ID)
job = mcp__unreal-mcp__start_long_operation(params)
job_id = job["job_id"]

# Poll for completion
import time
while True:
    status = mcp__unreal-mcp__check_job_status(job_id=job_id)
    if status["state"] == "complete":
        result = mcp__unreal-mcp__get_job_result(job_id=job_id)
        break
    time.sleep(1)
```

**To implement this:**
1. Handler starts operation in background thread
2. Returns job ID immediately
3. Separate handler checks job status
4. Separate handler retrieves result when complete

---

**Option 4: Increase Timeout (Not Recommended)**

**If operation genuinely needs >30s and can't be broken up:**

Modify MCP server timeout (implementation-specific):
```python
# In connection.py or similar
socket.settimeout(120)  # 2 minutes instead of 30 seconds
```

**Downside:**
- Masks underlying performance issues
- Poor user experience (long waits)
- Can't cancel operation if it hangs

**Only use for:**
- Asset imports (legitimately slow)
- Large-scale level generation
- Heavy compilation operations

---

### Complete Fix Workflow

```
Issue: "Command timeout after 30 seconds"

┌─────────────────────────────────────────┐
│ 1. Add timing logs to C++ handler       │
└────┬────────────────────────────────────┘
     │ Logs show: 52.34s total time
     ↓
┌─────────────────────────────────────────┐
│ 2. Identify bottleneck                  │
│    - Linear search in loop (O(n²))      │
└────┬────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ 3. Optimize algorithm                   │
│    - Build map once (O(n))              │
└────┬────────────────────────────────────┘
     │ ✅ Reduced to 8.2s
     ↓
┌─────────────────────────────────────────┐
│ 4. If still >30s, break into batches    │
│    - Process 1000 actors at a time      │
└────┬────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────┐
│ 5. Recompile and test                   │
└────┬────────────────────────────────────┘
     │ ✅ Each batch <10s
     ↓
   FIXED
```

---

## Log Analysis Techniques

### Unreal Output Log

**Location:** Window → Developer Tools → Output Log

**Useful Filters:**

**Search for "MCP":**
```
Filter: MCP

Shows:
- Plugin initialization
- TCP server startup
- Command routing
- Handler execution
```

**Search for "Error":**
```
Filter: Error

Shows:
- C++ exceptions
- Unreal API errors
- Handler failures
```

**Search for specific command:**
```
Filter: set_actor_label

Shows:
- All log messages related to that command
```

---

**Enable Verbose Logging:**

```cpp
// Add to handlers for debugging
UE_LOG(LogTemp, Log, TEXT("HandleSetActorLabel called"));
UE_LOG(LogTemp, Log, TEXT("  actor_name: %s"), *ActorName);
UE_LOG(LogTemp, Log, TEXT("  new_label: %s"), *NewLabel);
```

**Then in Output Log:**
```
LogTemp: HandleSetActorLabel called
LogTemp:   actor_name: Cube_42
LogTemp:   new_label: MyCube
```

---

### Python MCP Server Logs

**Location:** Terminal where server is running

**Typical Output:**
```
Loading MCP tools...
Connected to Unreal at localhost:55557
MCP server running...

[2025-10-25 14:30:15] Tool invoked: set_actor_label
[2025-10-25 14:30:15]   actor_name: Cube_42
[2025-10-25 14:30:15]   new_label: MyCube
[2025-10-25 14:30:15] Response received: {"status": "success", ...}
```

**Add Custom Logging:**

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@mcp.tool()
def set_actor_label(ctx: Context, actor_name: str, new_label: str):
    logger.debug(f"Tool called: actor_name={actor_name}, new_label={new_label}")

    unreal = get_unreal_connection()
    result = unreal.send_command("set_actor_label", {
        "actor_name": actor_name,
        "new_label": new_label
    })

    logger.debug(f"Result: {result}")
    return result
```

---

### TCP Traffic Analysis (Advanced)

**Use Wireshark to capture TCP traffic on port 55557:**

```
1. Install Wireshark
2. Start capture on Loopback interface
3. Filter: tcp.port == 55557
4. Invoke MCP tool
5. Stop capture
6. Analyze TCP stream:
   - Request JSON sent from Python
   - Response JSON sent from C++
```

**Useful for:**
- Verifying exact JSON sent/received
- Detecting truncated responses
- Identifying connection drops

---

## Diagnostic Commands

### Test Basic Connectivity

**Python:**
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 55557))
print("✅ Connected")
sock.close()
```

---

### Test MCP Tool Availability

**Claude Code:**
```python
# List all available MCP tools
# (implementation varies by MCP client)

# In Claude Code conversation:
print(dir(mcp__unreal_mcp))
# Should show: spawn_actor, set_actor_transform, execute_python, etc.
```

---

### Test Simple MCP Tool

**execute_python (simplest tool):**
```python
result = mcp__unreal-mcp__execute_python(script="print('Hello from Unreal')")

print(result)
# Expected: {"status": "success", "output": "Hello from Unreal\n"}
```

**If this works:**
- ✅ TCP connection working
- ✅ Bridge routing working (execute_python registered)
- ✅ Basic JSON response working

**If this fails:**
- Check connection (Issue 1)
- Check plugin enabled
- Check MCP server running

---

### Test Bridge Registration

**Send minimal command:**
```python
# Directly test if command is registered
result = mcp__unreal-mcp__set_actor_label(
    actor_name="anything",
    new_label="anything"
)

# If "Unknown command": Bridge not registered
# If different error (e.g., "Actor not found"): Bridge IS registered!
```

---

## Common Error Messages

### "Connection to localhost:55557 failed"

**Meaning:** TCP connection cannot be established

**Fixes:**
- Start Unreal Editor
- Enable UnrealMCP plugin
- Check port not blocked

**See:** [Issue 1: Connection Failed](#issue-1-connection-failed)

---

### "Unknown command: tool_name"

**Meaning:** Command not registered in Bridge

**Fixes:**
- Add else if block in RouteCommand()
- Verify command name matches exactly
- Recompile plugin
- Restart MCP server

**See:** [Issue 2: Unknown Command](#issue-2-unknown-command)

---

### "Failed to parse response"

**Meaning:** C++ returned invalid JSON

**Fixes:**
- Use CreateSuccessResponse/CreateErrorResponse
- Don't manually construct JSON
- Validate JSON with jsonlint.com

**See:** [Issue 3: Failed to Parse Response](#issue-3-failed-to-parse-response)

---

### "Actor not found: ActorName"

**Meaning:** Execution error (not MCP issue)

**Fixes:**
- Verify actor exists in Unreal (World Outliner)
- Check actor name is correct (case-sensitive)
- Create actor first if needed

**Not covered in this guide** (Unreal-specific, not MCP debugging)

---

### "Property 'PropertyName' not found on component"

**Meaning:** Execution error (not MCP issue)

**Fixes:**
- Verify property name spelling
- Check component type has that property
- Use correct property type (ObjectProperty, FloatProperty, etc.)

**Not covered in this guide** (Unreal-specific, not MCP debugging)

---

## Prevention Checklist

### Before Creating New Tool

```
[ ] Read adding_tools_workflow.md completely
[ ] Understand Bridge routing requirement
[ ] Have test actor/asset ready in Unreal
[ ] MCP server running and connected
```

---

### After Creating Tool (Before Testing)

```
[ ] Python tool has @mcp.tool() decorator
[ ] Python tool calls send_command() with correct name
[ ] C++ handler uses CreateSuccessResponse/CreateErrorResponse
[ ] ⚠️ Bridge registration added to RouteCommand() ⚠️
[ ] Command name matches EXACTLY across Python and C++
[ ] Plugin compiled successfully (DLL created)
[ ] MCP server restarted
```

---

### During Testing

```
[ ] Test with valid inputs first
[ ] Test error cases (actor not found, empty params, etc.)
[ ] Verify JSON structure in responses
[ ] Check Unreal Output Log for errors
[ ] Test edge cases (special characters, very long strings, etc.)
```

---

### After Testing

```
[ ] Document in MCP_Capabilities_UE55.md
[ ] Add usage examples
[ ] Document error cases
[ ] Clean up debug logging (or leave for future debugging)
```

---

## Summary

**The Four Most Common Issues:**

1. **Connection Failed** (20% of errors)
   - Fix: Start Unreal, enable plugin, check port 55557

2. **Unknown Command** (60% of errors!)
   - Fix: Add Bridge registration in RouteCommand()

3. **Failed to Parse Response** (15% of errors)
   - Fix: Use CreateSuccessResponse helper

4. **Command Timeout** (5% of errors)
   - Fix: Break into smaller operations or optimize

**Golden Rules:**
- ✅ Always check Bridge registration FIRST for "Unknown command"
- ✅ Always use CreateSuccessResponse/CreateErrorResponse (never manual JSON)
- ✅ Always restart MCP server after C++ changes
- ✅ Always check Unreal Output Log when debugging

**For complete workflows:**
- **adding_tools_workflow.md** - Step-by-step tool creation
- **two_layer_routing.md** - Bridge routing deep dive
- **architecture_overview.md** - System understanding

---

**Last Updated:** 2025-10-25
**Part of:** unreal-mcp-development skill (v1.0.0)
