# Unreal MCP Architecture Overview

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Part of:** unreal-mcp-development skill

---

## Table of Contents

1. [Introduction](#introduction)
2. [Three-Layer System Architecture](#three-layer-system-architecture)
3. [TCP Communication Protocol](#tcp-communication-protocol)
4. [JSON Message Format](#json-message-format)
5. [Connection Lifecycle](#connection-lifecycle)
6. [Error Propagation](#error-propagation)
7. [Command Execution Flow](#command-execution-flow)
8. [System Components](#system-components)

---

## Introduction

The Unreal MCP (Model Context Protocol) system enables AI control of Unreal Engine through natural language via a three-layer architecture. Understanding this architecture is essential for developing new tools, debugging issues, and extending functionality.

**Key Design Principles:**

- **Separation of Concerns:** Each layer has distinct responsibilities
- **Protocol-Based Communication:** Standard JSON over TCP
- **Loose Coupling:** Layers communicate via well-defined interfaces
- **Extensibility:** New tools added without modifying core architecture

**Why Three Layers?**

```
Claude Code     → MCP Protocol expertise (AI interaction)
Python Server   → MCP specification implementation (routing)
C++ Plugin      → Unreal Engine expertise (editor integration)
```

Each layer focuses on what it does best, enabling independent development and testing.

---

## Three-Layer System Architecture

### Overview Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: Claude Code (MCP Client)                          │
│  ─────────────────────────────────────────────────────────  │
│  Purpose: User interface and AI interaction                 │
│  Technology: Claude Code, MCP client libraries              │
│  Location: .cursor/mcp.json or MCP client config            │
│  ─────────────────────────────────────────────────────────  │
│  Responsibilities:                                          │
│  • Accept natural language commands from user               │
│  • Translate to MCP tool invocations                        │
│  • Format parameters as JSON                                │
│  • Display results to user                                  │
│  • Handle MCP protocol specifics                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ MCP Protocol (JSON-RPC over stdio/TCP)
                   │
┌──────────────────▼──────────────────────────────────────────┐
│  LAYER 2: Python MCP Server                                 │
│  ─────────────────────────────────────────────────────────  │
│  Purpose: MCP specification implementation                  │
│  Technology: Python 3.12+, FastMCP library                  │
│  Location: UnrealEngine/unreal-mcp-main/Python/             │
│  ─────────────────────────────────────────────────────────  │
│  Responsibilities:                                          │
│  • Implement MCP server protocol (FastMCP)                  │
│  • Expose tools via @mcp.tool() decorator                   │
│  • Manage TCP client connection to C++ plugin               │
│  • Translate MCP calls to TCP JSON messages                 │
│  • Handle connection lifecycle (connect/disconnect)         │
│  • Return structured responses to Claude Code               │
│  ─────────────────────────────────────────────────────────  │
│  Key Files:                                                 │
│  • unreal_mcp_server.py - Main server implementation        │
│  • connection.py - TCP client to C++ plugin                 │
│  • tools/*.py - MCP tool wrappers                           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ TCP/JSON Protocol (localhost:55557)
                   │
┌──────────────────▼──────────────────────────────────────────┐
│  LAYER 1: C++ Plugin (UnrealMCP)                            │
│  ─────────────────────────────────────────────────────────  │
│  Purpose: Unreal Engine integration                         │
│  Technology: C++, Unreal Engine 5.5 API                     │
│  Location: MCPGameProject/Plugins/UnrealMCP/                │
│  ─────────────────────────────────────────────────────────  │
│  Responsibilities:                                          │
│  • Run TCP server on port 55557                             │
│  • Accept JSON command messages                             │
│  • Route commands to handlers (Bridge pattern)              │
│  • Execute Unreal Engine API calls                          │
│  • Access Editor subsystems (actors, assets, levels)        │
│  • Return JSON responses                                    │
│  ─────────────────────────────────────────────────────────  │
│  Key Files:                                                 │
│  • UnrealMCPModule.cpp - Plugin initialization, TCP server  │
│  • UnrealMCPEditorCommands.cpp - Bridge routing             │
│  • Commands/*.cpp - Command handler implementations         │
└─────────────────────────────────────────────────────────────┘
```

---

### Layer 3: Claude Code (MCP Client)

**Purpose:** Provide user interface for AI-driven Unreal Engine control

**Technology Stack:**
- Claude Code interface
- MCP client protocol implementation
- JSON-RPC communication

**Configuration:**

```json
// .cursor/mcp.json (for Cursor IDE)
{
  "mcpServers": {
    "unreal-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Path/To/UnrealEngine/unreal-mcp-main/Python",
        "run",
        "unreal_mcp_server.py"
      ]
    }
  }
}
```

**Tool Invocation:**

```python
# Claude Code invokes tools like this:
result = mcp__unreal-mcp__spawn_actor(
    actor_class="/Script/Engine.StaticMeshActor",
    location={"x": 0, "y": 0, "z": 0}
)
```

**Responsibilities:**
1. Accept natural language from user ("Create a cube at origin")
2. Determine appropriate MCP tool to call
3. Extract parameters from context
4. Invoke tool with structured JSON parameters
5. Receive and parse JSON response
6. Present results to user in natural language

---

### Layer 2: Python MCP Server

**Purpose:** Implement MCP specification and translate to Unreal-specific TCP protocol

**Technology Stack:**
- Python 3.12+
- FastMCP library (MCP server implementation)
- Socket programming (TCP client)
- JSON serialization

**Entry Point:** `unreal_mcp_server.py`

```python
from fastmcp import FastMCP
from connection import get_unreal_connection

# Initialize FastMCP server
mcp = FastMCP("unreal-mcp")

# Define MCP tool
@mcp.tool()
def spawn_actor(ctx: Context, actor_class: str, location: Dict[str, float]) -> Dict[str, Any]:
    """Spawn an actor in Unreal Engine"""
    # Get TCP connection to C++ plugin
    unreal = get_unreal_connection()

    # Send command over TCP as JSON
    result = unreal.send_command("spawn_actor", {
        "actor_class": actor_class,
        "location": location
    })

    # Return result (already parsed JSON)
    return result

# Run server
mcp.run()
```

**TCP Connection Management:** `connection.py`

```python
import socket
import json

class UnrealConnection:
    def __init__(self, host='localhost', port=55557):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """Establish TCP connection to C++ plugin"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def send_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON command over TCP, receive JSON response"""
        # Build request
        request = {
            "command": command,
            **params
        }

        # Send as JSON string
        message = json.dumps(request) + "\n"
        self.socket.sendall(message.encode('utf-8'))

        # Receive response
        response_data = self.socket.recv(4096)
        response = json.loads(response_data.decode('utf-8'))

        return response
```

**Tool Organization:**

```
Python/tools/
├── actor_tools.py       # spawn_actor, set_actor_transform, etc.
├── material_tools.py    # create_material_instance, etc.
├── editor_tools.py      # execute_python, etc.
└── component_tools.py   # set_actor_component_property, etc.
```

**Responsibilities:**
1. Implement MCP server specification (via FastMCP)
2. Expose tools to Claude Code with proper type hints
3. Maintain TCP connection to C++ plugin (localhost:55557)
4. Translate MCP tool calls to TCP JSON messages
5. Handle connection errors and reconnection
6. Parse JSON responses from C++ plugin
7. Return structured data to Claude Code

---

### Layer 1: C++ Plugin (UnrealMCP)

**Purpose:** Integrate with Unreal Engine Editor and execute commands

**Technology Stack:**
- C++ (UE 5.5 standards)
- Unreal Engine Editor API
- TCP socket server (native sockets)
- JSON parsing (UE Json module)

**Plugin Structure:**

```
MCPGameProject/Plugins/UnrealMCP/
├── Source/UnrealMCP/
│   ├── Public/
│   │   ├── UnrealMCPModule.h
│   │   └── UnrealMCPEditorCommands.h
│   ├── Private/
│   │   ├── UnrealMCPModule.cpp          # Plugin initialization, TCP server
│   │   ├── UnrealMCPEditorCommands.cpp  # Bridge routing
│   │   ├── UnrealMCPCommonUtils.cpp     # JSON helpers
│   │   └── Commands/
│   │       ├── ActorCommands.cpp        # Actor-related handlers
│   │       ├── MaterialCommands.cpp     # Material-related handlers
│   │       └── EditorCommands.cpp       # Editor-related handlers
│   └── UnrealMCP.Build.cs               # Build configuration
├── Binaries/Win64/
│   └── UnrealEditor-UnrealMCP.dll       # Compiled plugin
└── UnrealMCP.uplugin                    # Plugin manifest
```

**TCP Server Initialization:** `UnrealMCPModule.cpp`

```cpp
void FUnrealMCPModule::StartupModule()
{
    // Create TCP server socket
    FIPv4Endpoint Endpoint(FIPv4Address(127, 0, 0, 1), 55557);
    ListenSocket = FTcpSocketBuilder(TEXT("UnrealMCP Server"))
        .AsReusable()
        .BoundToEndpoint(Endpoint)
        .Listening(8);

    if (ListenSocket)
    {
        UE_LOG(LogTemp, Log, TEXT("UnrealMCP server listening on port 55557"));

        // Start accept thread
        ConnectionThread = FRunnableThread::Create(
            new FTCPConnectionRunnable(this),
            TEXT("UnrealMCP Connection Thread")
        );
    }
}
```

**Message Processing:**

```cpp
void FUnrealMCPModule::ProcessMessage(const FString& Message)
{
    // Parse JSON
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Message);

    if (FJsonSerializer::Deserialize(Reader, JsonObject))
    {
        // Extract command
        FString Command = JsonObject->GetStringField("command");

        // Route to handler
        FString Response = FUnrealMCPEditorCommands::RouteCommand(Command, JsonObject);

        // Send response over TCP
        SendResponse(Response);
    }
}
```

**Responsibilities:**
1. Initialize and manage TCP server on port 55557
2. Accept connections from Python MCP server
3. Parse incoming JSON messages
4. Route commands to appropriate handlers (Bridge pattern)
5. Execute Unreal Engine API calls (spawn actors, modify properties, etc.)
6. Build JSON responses (success/error)
7. Send responses back over TCP
8. Handle Unreal Editor lifecycle (module startup/shutdown)

---

## TCP Communication Protocol

### Protocol Specification

**Connection:**
- **Host:** localhost (127.0.0.1)
- **Port:** 55557
- **Type:** TCP stream socket
- **Encoding:** UTF-8
- **Message Format:** Newline-delimited JSON (\n)

**Why TCP?**
- Reliable delivery (guaranteed order, no packet loss)
- Bidirectional communication
- Simple implementation on both Python and C++ sides
- Standard socket APIs available

**Why Port 55557?**
- High port number (>1024, no admin privileges needed)
- Unlikely to conflict with standard services
- Easy to remember (sequential digits)

---

### Connection Flow

```
Python Client                          C++ Server (Plugin)
─────────────                          ───────────────────

1. Unreal Editor starts
                                       Plugin loads
                                       Create TCP socket
                                       Bind to 0.0.0.0:55557
                                       Listen (backlog: 8)
                                       Start accept thread

2. MCP Server starts
   Create socket
   Connect to localhost:55557 ────────▶ Accept connection
                                       Store client socket
                                       Start receive thread

3. Connection established ◀────────────▶ Connection established

4. Send command
   Create JSON request
   Serialize to string
   Append newline
   Send over socket ───────────────────▶ Receive data
                                       Parse JSON
                                       Route command
                                       Execute handler
                                       Build response
   Receive response ◀─────────────────  Send JSON response
   Parse JSON
   Return to MCP tool

5. (Repeat step 4 for each command)

6. Shutdown
   Close socket ──────────────────────▶ Detect disconnect
                                       Close client socket
                                       Continue listening
```

---

### Message Format

**Request Message (Python → C++):**

```json
{
  "command": "spawn_actor",
  "actor_class": "/Script/Engine.StaticMeshActor",
  "location": {"x": 0, "y": 100, "z": 50},
  "rotation": {"pitch": 0, "yaw": 90, "roll": 0},
  "scale": {"x": 1, "y": 1, "z": 1}
}
```

**Fields:**
- `command` (string, required): Command identifier (matches Bridge routing)
- Additional fields: Command-specific parameters (varies by command)

**Message Termination:**
- Each message terminated with newline character (`\n`)
- Allows stream-based parsing (read until newline)

---

**Response Message (C++ → Python):**

**Success Response:**
```json
{
  "status": "success",
  "message": "Actor spawned successfully",
  "actor_name": "StaticMeshActor_42",
  "actor_path": "/Game/Level1.Level1:PersistentLevel.StaticMeshActor_42"
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Actor class not found: /Script/Engine.InvalidClass",
  "error_code": "ACTOR_CLASS_NOT_FOUND"
}
```

**Required Fields:**
- `status` (string): "success" or "error"
- `message` (string): Human-readable description

**Optional Fields:**
- Any command-specific data (actor_name, count, paths, etc.)
- `error_code` (string): Machine-readable error identifier

---

### Error Handling

**TCP-Level Errors:**

1. **Connection Refused**
   - Cause: C++ plugin not running or port not listening
   - Python behavior: Raise exception
   - Recovery: Prompt user to start Unreal Editor

2. **Connection Lost**
   - Cause: Unreal Editor closed or plugin disabled
   - Python behavior: Detect on next send, raise exception
   - Recovery: Reconnect when Unreal restarts

3. **Socket Timeout**
   - Cause: Long-running command (>30 seconds)
   - Python behavior: Timeout exception
   - Recovery: Increase timeout or break into smaller operations

**Protocol-Level Errors:**

1. **Invalid JSON**
   - Cause: Malformed message
   - C++ behavior: Return error response
   - Example: Missing quotes, trailing commas

2. **Missing Command Field**
   - Cause: Request doesn't include "command"
   - C++ behavior: Return error response
   - Example: `{"actor_class": "..."}`  (no command!)

3. **Unknown Command**
   - Cause: Command not registered in Bridge
   - C++ behavior: Return error with "Unknown command"
   - Example: `{"command": "nonexistent_tool"}`

---

## JSON Message Format

### Design Principles

**Simplicity:**
- Flat structure when possible
- Nested objects only when necessary (locations, rotations)
- Consistent naming (snake_case for compatibility)

**Type Safety:**
- Explicit types in documentation
- Validation in C++ handlers
- Python type hints in MCP tools

**Extensibility:**
- Optional fields allowed
- Forward compatibility (ignore unknown fields)
- Backward compatibility (provide defaults)

---

### Common Data Types

**Vector (Location/Scale):**
```json
{
  "x": 0.0,
  "y": 100.0,
  "z": 50.0
}
```
Maps to `FVector` in Unreal

**Rotator:**
```json
{
  "pitch": 0.0,
  "yaw": 90.0,
  "roll": 0.0
}
```
Maps to `FRotator` in Unreal

**Transform:**
```json
{
  "location": {"x": 0, "y": 100, "z": 50},
  "rotation": {"pitch": 0, "yaw": 90, "roll": 0},
  "scale": {"x": 1, "y": 1, "z": 1}
}
```
Maps to `FTransform` in Unreal

**Asset Path:**
```json
{
  "asset_path": "/Game/Meshes/SM_Cube.SM_Cube"
}
```
Unreal object path format

**Color:**
```json
{
  "r": 1.0,
  "g": 0.5,
  "b": 0.0,
  "a": 1.0
}
```
Maps to `FLinearColor` in Unreal (0.0-1.0 range)

---

### Request Examples

**Spawn Actor:**
```json
{
  "command": "spawn_actor",
  "actor_class": "/Script/Engine.StaticMeshActor",
  "location": {"x": 0, "y": 0, "z": 0},
  "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
  "scale": {"x": 1, "y": 1, "z": 1}
}
```

**Set Actor Transform:**
```json
{
  "command": "set_actor_transform",
  "actor_name": "StaticMeshActor_42",
  "location": {"x": 100, "y": 200, "z": 50}
}
```

**Set Component Property:**
```json
{
  "command": "set_actor_component_property",
  "actor_name": "StaticMeshActor_42",
  "component_name": "StaticMeshComponent",
  "property_name": "StaticMesh",
  "property_value": "/Game/Meshes/SM_Cube.SM_Cube",
  "property_type": "ObjectProperty"
}
```

**Execute Python:**
```json
{
  "command": "execute_python",
  "script": "import unreal\nactors = unreal.EditorLevelLibrary.get_all_level_actors()\nprint(len(actors))"
}
```

---

### Response Examples

**Spawn Actor Success:**
```json
{
  "status": "success",
  "message": "Actor spawned successfully",
  "actor_name": "StaticMeshActor_42",
  "actor_class": "/Script/Engine.StaticMeshActor",
  "location": {"x": 0, "y": 0, "z": 0}
}
```

**Set Property Success:**
```json
{
  "status": "success",
  "message": "Property 'StaticMesh' set successfully",
  "actor_name": "StaticMeshActor_42",
  "component_name": "StaticMeshComponent",
  "property_name": "StaticMesh",
  "property_value": "/Game/Meshes/SM_Cube.SM_Cube"
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Actor not found: NonExistentActor",
  "error_code": "ACTOR_NOT_FOUND",
  "requested_actor": "NonExistentActor"
}
```

**Execute Python Success:**
```json
{
  "status": "success",
  "output": "42\n",
  "script_length": 98
}
```

---

## Connection Lifecycle

### Startup Sequence

**Phase 1: Unreal Editor Launch**

```
1. User opens MCPGameProject.uproject
2. Unreal Editor loads
3. Plugin system scans Plugins/ folder
4. UnrealMCP plugin detected (UnrealMCP.uplugin)
5. Plugin module loaded (FUnrealMCPModule)
6. StartupModule() called
   ├─ Create TCP socket
   ├─ Bind to 0.0.0.0:55557
   ├─ Start listening (backlog: 8)
   └─ Spawn accept thread
7. Log message: "UnrealMCP server listening on port 55557"
```

**Verification:**
```bash
# Check port is listening
netstat -an | findstr "55557"
# Expected: TCP 0.0.0.0:55557 LISTENING
```

---

**Phase 2: MCP Server Launch**

```
1. User (or Claude Code) runs:
   uv --directory Python/ run unreal_mcp_server.py

2. Python script starts
   ├─ Import FastMCP
   ├─ Initialize MCP server
   ├─ Load tool modules (tools/*.py)
   ├─ Create UnrealConnection instance
   └─ Attempt TCP connection to localhost:55557

3. If connection succeeds:
   ├─ Store socket in UnrealConnection
   ├─ Log: "Connected to Unreal at localhost:55557"
   └─ Start MCP server (listen for Claude Code requests)

4. If connection fails:
   ├─ Raise exception: "Connection to localhost:55557 failed"
   └─ Exit (prompt user to start Unreal Editor)
```

**Verification:**
```python
# MCP server should print:
# Connected to Unreal at localhost:55557
# MCP server running...
```

---

**Phase 3: Claude Code Connection**

```
1. Claude Code starts (reads .cursor/mcp.json)
2. Spawns MCP server subprocess (if not already running)
3. Establishes MCP protocol connection (stdio or TCP)
4. Queries available tools
5. Receives tool list (spawn_actor, set_actor_transform, etc.)
6. Tools ready for invocation
```

---

### Normal Operation

**Command Execution Flow:**

```
1. User types natural language in Claude Code
   "Create a cube at origin"

2. Claude Code determines MCP tool to invoke
   Tool: spawn_static_mesh_actor
   Parameters: {mesh: SM_Cube, location: {x: 0, y: 0, z: 0}}

3. Claude Code sends MCP request to Python server
   (via MCP protocol)

4. Python MCP tool wrapper receives call
   @mcp.tool() spawn_static_mesh_actor(...)

5. Python builds TCP JSON request
   {
     "command": "spawn_static_mesh_actor",
     "mesh_path": "/Engine/BasicShapes/Cube.Cube",
     "location": {"x": 0, "y": 0, "z": 0}
   }

6. Python sends TCP message to C++ plugin
   (over socket to localhost:55557)

7. C++ plugin receives message
   ├─ Parse JSON
   ├─ Extract command: "spawn_static_mesh_actor"
   ├─ Route to handler: HandleSpawnStaticMeshActor()
   └─ Execute handler

8. C++ handler executes
   ├─ Load mesh asset
   ├─ Spawn StaticMeshActor
   ├─ Set StaticMeshComponent mesh
   ├─ Set actor location
   └─ Build success response JSON

9. C++ sends response over TCP
   {
     "status": "success",
     "actor_name": "StaticMeshActor_42",
     "mesh_path": "/Engine/BasicShapes/Cube.Cube"
   }

10. Python receives response
    ├─ Parse JSON
    ├─ Validate status field
    └─ Return dict to MCP tool

11. MCP tool returns to Claude Code
    (via MCP protocol)

12. Claude Code displays to user
    "Created cube actor at origin: StaticMeshActor_42"
```

---

### Shutdown Sequence

**Graceful Shutdown:**

```
1. User closes Unreal Editor
   ├─ Editor shutdown sequence begins
   ├─ Plugin system notifies plugins
   └─ ShutdownModule() called on UnrealMCP

2. UnrealMCP plugin cleanup
   ├─ Stop accept thread
   ├─ Close all client sockets
   ├─ Close listen socket
   └─ Release resources

3. TCP connection broken
   ├─ Python detects socket error on next send
   └─ Raises exception: "Connection lost"

4. MCP server handles error
   ├─ Log: "Unreal connection lost"
   ├─ Tools return connection errors
   └─ Continue running (can reconnect if Unreal restarts)
```

**Manual MCP Server Stop:**

```
1. User presses Ctrl+C in MCP server terminal
2. Python receives SIGINT
3. MCP server cleanup
   ├─ Close TCP socket to Unreal
   ├─ Shutdown MCP protocol server
   └─ Exit process

4. C++ plugin detects disconnect
   ├─ Close client socket
   └─ Continue listening (ready for next connection)
```

---

## Error Propagation

### Error Flow Across Layers

```
Error Source                 Propagation Path
────────────────────────────────────────────────────────

C++ Execution Error
(Actor not found)
    │
    ├─ Catch in handler      FString HandleSetActorTransform(...)
    ├─ Create error response {
    │                          "status": "error",
    │                          "message": "Actor not found",
    │                          "error_code": "ACTOR_NOT_FOUND"
    ├─ Return JSON           }
    │
    ▼
TCP Layer
(No error, valid JSON)
    │
    ▼
Python MCP Tool
    ├─ Receive response      result = unreal.send_command(...)
    ├─ Check status          if result["status"] == "error":
    ├─ Return error dict         return result  # Contains error details
    │
    ▼
Claude Code
    ├─ Receive tool response
    ├─ Interpret error
    └─ Display to user       "Error: Actor not found"
```

---

### Error Categories

**1. Connection Errors (Python Layer)**

Occur when TCP connection fails or is lost.

**Symptoms:**
- Exception raised in Python
- All tools fail immediately
- No response from Unreal

**Causes:**
- Unreal Editor not running
- Plugin not enabled
- Port 55557 blocked
- Firewall interference

**Handling:**
```python
try:
    unreal = get_unreal_connection()
except ConnectionRefusedError:
    return {
        "status": "error",
        "message": "Cannot connect to Unreal (port 55557). Is Unreal Editor running?",
        "error_code": "CONNECTION_REFUSED"
    }
```

---

**2. Protocol Errors (JSON Layer)**

Occur when message format is invalid.

**Symptoms:**
- Error response from C++
- Message: "Failed to parse request" or similar
- Specific tool fails, others work

**Causes:**
- Invalid JSON syntax
- Missing required fields
- Wrong data types

**Handling (C++ side):**
```cpp
TSharedPtr<FJsonObject> JsonObject;
TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Message);

if (!FJsonSerializer::Deserialize(Reader, JsonObject))
{
    return CreateErrorResponse("Failed to parse JSON request");
}

if (!JsonObject->HasField("command"))
{
    return CreateErrorResponse("Missing 'command' field in request");
}
```

---

**3. Routing Errors (Bridge Layer)**

Occur when command is not registered in Bridge.

**Symptoms:**
- Error message: "Unknown command: tool_name"
- Python MCP tool exists and looks correct
- Other tools work fine

**Cause:**
- **Bridge registration missing** (most common error!)

**Handling (C++ side):**
```cpp
FString FUnrealMCPEditorCommands::RouteCommand(const FString& Command,
                                                const TSharedPtr<FJsonObject>& Request)
{
    if (Command == "known_command")
    {
        return HandleKnownCommand(Request);
    }
    // ... other commands ...
    else
    {
        // CRITICAL: This catches unregistered commands
        return CreateErrorResponse(FString::Printf(
            TEXT("Unknown command: %s"), *Command));
    }
}
```

---

**4. Execution Errors (Handler Layer)**

Occur during Unreal API execution.

**Symptoms:**
- Error response with specific message
- Status: "error"
- Tool-specific error codes

**Causes:**
- Actor not found
- Asset path invalid
- Property type mismatch
- Insufficient permissions

**Handling (C++ side):**
```cpp
FString HandleSetActorTransform(const TSharedPtr<FJsonObject>& Request)
{
    FString ActorName = Request->GetStringField("actor_name");

    AActor* Actor = FindActorByName(ActorName);
    if (!Actor)
    {
        // Graceful error handling
        return CreateErrorResponse(FString::Printf(
            TEXT("Actor not found: %s"), *ActorName));
    }

    // Continue with valid actor...
}
```

---

### Error Response Standards

**All error responses MUST include:**

1. **status** field = "error"
2. **message** field with human-readable description
3. **error_code** field (optional but recommended)

**Example:**
```json
{
  "status": "error",
  "message": "Static mesh not found at path: /Game/Meshes/SM_Missing.SM_Missing",
  "error_code": "ASSET_NOT_FOUND",
  "requested_path": "/Game/Meshes/SM_Missing.SM_Missing"
}
```

**Common Error Codes:**
- `CONNECTION_REFUSED` - TCP connection failed
- `UNKNOWN_COMMAND` - Command not registered in Bridge
- `ACTOR_NOT_FOUND` - Actor name invalid
- `ASSET_NOT_FOUND` - Asset path invalid
- `PROPERTY_NOT_FOUND` - Property name invalid on component
- `TYPE_MISMATCH` - Property type doesn't match expected
- `INVALID_JSON` - JSON parsing failed

---

## Command Execution Flow

### Complete Flow Diagram

```
USER                 CLAUDE CODE          PYTHON MCP           C++ PLUGIN
────                 ───────────          ──────────           ──────────

Natural language
"Create cube" ─────▶ Parse intent
                     Determine tool
                     Extract params

                     MCP request ────────▶ Receive via MCP
                                          Execute tool function
                                          Build TCP JSON

                                          TCP send ───────────▶ Receive TCP
                                                               Parse JSON
                                                               Route command
                                                               Execute handler
                                                               Build response

                                          TCP receive ◀─────── Send JSON
                                          Parse JSON
                                          Return dict

                     MCP response ◀─────── Return via MCP
                     Format result

Display result ◀──── Natural language
"Created: Actor_42"
```

---

### Detailed Step-by-Step

**Step 1: User Input**
```
User types: "Create a red cube at origin"
```

**Step 2: Claude Code Processing**
```
1. Parse natural language
2. Identify intent: spawn mesh actor
3. Extract parameters:
   - mesh: cube (map to /Engine/BasicShapes/Cube.Cube)
   - color: red (set after spawning)
   - location: origin (0, 0, 0)
4. Determine tool: spawn_static_mesh_actor
```

**Step 3: MCP Tool Invocation**
```python
# Claude Code invokes:
result = mcp__unreal-mcp__spawn_static_mesh_actor(
    mesh_path="/Engine/BasicShapes/Cube.Cube",
    location={"x": 0, "y": 0, "z": 0}
)
```

**Step 4: Python MCP Tool Execution**
```python
@mcp.tool()
def spawn_static_mesh_actor(ctx: Context, mesh_path: str, location: Dict) -> Dict:
    # Get TCP connection
    unreal = get_unreal_connection()

    # Build request
    request = {
        "command": "spawn_static_mesh_actor",
        "mesh_path": mesh_path,
        "location": location
    }

    # Send over TCP, receive response
    result = unreal.send_command(request)

    return result  # Pass response to Claude Code
```

**Step 5: TCP Communication (Python → C++)**
```
Python sends (newline-terminated):
{
  "command": "spawn_static_mesh_actor",
  "mesh_path": "/Engine/BasicShapes/Cube.Cube",
  "location": {"x": 0, "y": 0, "z": 0}
}\n
```

**Step 6: C++ Plugin Receives**
```cpp
// TCP thread receives data
FString Message = ReceiveFromSocket();  // Read until \n

// Parse JSON
TSharedPtr<FJsonObject> Request;
FJsonSerializer::Deserialize(Reader, Request);

// Extract command
FString Command = Request->GetStringField("command");
// Command = "spawn_static_mesh_actor"
```

**Step 7: Bridge Routing**
```cpp
FString FUnrealMCPEditorCommands::RouteCommand(const FString& Command,
                                                const TSharedPtr<FJsonObject>& Request)
{
    // Route to correct handler
    if (Command == "spawn_static_mesh_actor")
    {
        return HandleSpawnStaticMeshActor(Request);  // ⬅️ Call handler
    }
    // ... other commands ...
}
```

**Step 8: Handler Execution**
```cpp
FString HandleSpawnStaticMeshActor(const TSharedPtr<FJsonObject>& Request)
{
    // Extract parameters
    FString MeshPath = Request->GetStringField("mesh_path");
    TSharedPtr<FJsonObject> LocationObj = Request->GetObjectField("location");
    FVector Location(
        LocationObj->GetNumberField("x"),
        LocationObj->GetNumberField("y"),
        LocationObj->GetNumberField("z")
    );

    // Load mesh asset
    UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *MeshPath);
    if (!Mesh)
    {
        return CreateErrorResponse("Mesh not found at path: " + MeshPath);
    }

    // Spawn actor
    UWorld* World = GEditor->GetEditorWorldContext().World();
    AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(Location, FRotator::ZeroRotator);

    // Set mesh on component
    UStaticMeshComponent* MeshComp = Actor->GetStaticMeshComponent();
    MeshComp->SetStaticMesh(Mesh);

    // Build success response
    TSharedPtr<FJsonObject> ResultJson = MakeShared<FJsonObject>();
    ResultJson->SetStringField("actor_name", Actor->GetName());
    ResultJson->SetStringField("mesh_path", MeshPath);

    return CreateSuccessResponse(ResultJson);
}
```

**Step 9: Response Construction**
```cpp
FString CreateSuccessResponse(const TSharedPtr<FJsonObject>& Data)
{
    TSharedPtr<FJsonObject> Response = MakeShared<FJsonObject>();
    Response->SetStringField("status", "success");

    // Merge data fields
    for (auto& Pair : Data->Values)
    {
        Response->SetField(Pair.Key, Pair.Value);
    }

    // Serialize to JSON string
    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(Response.ToSharedRef(), Writer);

    return OutputString;
}
```

**Step 10: TCP Response (C++ → Python)**
```
C++ sends (newline-terminated):
{
  "status": "success",
  "actor_name": "StaticMeshActor_42",
  "mesh_path": "/Engine/BasicShapes/Cube.Cube"
}\n
```

**Step 11: Python Receives and Returns**
```python
# Python TCP client receives
response_data = socket.recv(4096)
response = json.loads(response_data.decode('utf-8'))

# Returns to MCP tool:
{
  "status": "success",
  "actor_name": "StaticMeshActor_42",
  "mesh_path": "/Engine/BasicShapes/Cube.Cube"
}
```

**Step 12: Claude Code Processes Result**
```
Claude Code receives MCP response
Formats natural language output
Displays to user: "Created cube actor at origin: StaticMeshActor_42"
```

---

## System Components

### Key Files Reference

**Python Layer:**
- `Python/unreal_mcp_server.py` - Main entry point, FastMCP server
- `Python/connection.py` - TCP client to C++ plugin
- `Python/tools/actor_tools.py` - Actor-related MCP tools
- `Python/tools/material_tools.py` - Material-related MCP tools
- `Python/tools/editor_tools.py` - Editor-related MCP tools (execute_python)

**C++ Layer:**
- `Source/UnrealMCP/Private/UnrealMCPModule.cpp` - Plugin initialization, TCP server
- `Source/UnrealMCP/Private/UnrealMCPEditorCommands.cpp` - **Bridge routing (CRITICAL!)**
- `Source/UnrealMCP/Private/UnrealMCPCommonUtils.cpp` - JSON helpers, response builders
- `Source/UnrealMCP/Private/Commands/ActorCommands.cpp` - Actor handler implementations
- `Source/UnrealMCP/Public/UnrealMCPEditorCommands.h` - Handler declarations

**Configuration:**
- `.cursor/mcp.json` - MCP server configuration (Cursor IDE)
- `MCPGameProject/Plugins/UnrealMCP/UnrealMCP.uplugin` - Plugin manifest

---

## Summary

Understanding the Unreal MCP architecture enables effective tool development, debugging, and extension:

**Key Takeaways:**

1. **Three-layer architecture** separates concerns (AI, MCP protocol, Unreal integration)
2. **TCP/JSON communication** provides reliable, standard protocol
3. **Bridge routing** is CRITICAL - most forgotten step when adding tools
4. **Error propagation** flows upward through all layers with structured responses
5. **Connection lifecycle** must be managed (startup, operation, shutdown)

**For deeper information:**
- **two_layer_routing.md** - Bridge + Handler pattern deep dive
- **adding_tools_workflow.md** - Step-by-step tool creation
- **debugging_guide.md** - Systematic troubleshooting

---

**Last Updated:** 2025-10-25
**Part of:** unreal-mcp-development skill (v1.0.0)
