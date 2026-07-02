# Pin Discovery Patterns

**Purpose:** Programmatically discover pin names for any PCG node

---

## ⚠️ CRITICAL: Print Output Location

**print() statements execute in Unreal Engine and output to UNREAL OUTPUT LOG, not MCP response!**

### Why This Happens

- Unreal Python executes in-engine (separate process from MCP)
- `print()` writes to Unreal's stdout → captured in log files
- MCP only receives command success/failure, not print output
- **Log file is the ONLY way to see print() results**

### Find Latest Log File

**Method 1: Python (Recommended)**
```python
import os, glob

log_dir = "<workspace>/UnrealEngine/MCPGameProject/Saved/Logs"
logs = glob.glob(f"{log_dir}/*.log")
latest_log = max(logs, key=os.path.getmtime) if logs else None
print(f"Latest log: {latest_log}")
```

**Method 2: Bash**
```bash
ls -t "<workspace>/UnrealEngine/MCPGameProject/Saved/Logs"/*.log | head -1
```

### Read Pin Discovery Output

After running pin discovery scripts:

```python
import os, glob

log_dir = "<workspace>/UnrealEngine/MCPGameProject/Saved/Logs"
logs = glob.glob(f"{log_dir}/*.log")
latest_log = max(logs, key=os.path.getmtime)

# Read last 50 lines
with open(latest_log, 'r', encoding='utf-8') as f:
    lines = f.readlines()[-50:]
    for line in lines:
        if "LogPython:" in line:
            print(line.strip())
```

**Look for:** `LogPython: Input: <pin_name>` or `LogPython: Output: <pin_name>`

---

## Basic Pin Query

### List All Input Pins
```python
import unreal

node = graph.nodes[0]
for pin in node.input_pins:
    print(f"Input: {pin.properties.label}")
```

### List All Output Pins
```python
for pin in node.output_pins:
    print(f"Output: {pin.properties.label}")
```

---

## Find Specific Pin

### By Name
```python
# Find "Spline" input pin
spline_pin = next((p for p in node.input_pins if p.properties.label == "Spline"), None)
if spline_pin:
    print(f"Found Spline pin!")
else:
    print("No Spline pin on this node")
```

### By Index
```python
# Get first output pin
first_output = node.output_pins[0] if node.output_pins else None
```

---

## Pin Properties

### Available Properties
```python
pin = node.output_pins[0]
print(f"Label: {pin.properties.label}")
print(f"Type: {pin.properties.allowed_types}")
print(f"Tooltip: {pin.properties.tooltip}")
```

---

## Complete Node Inspection

### Inspect All Pins
```python
def inspect_node(node):
    print(f"Node: {type(node.get_settings()).__name__}")

    print("\nInput Pins:")
    for i, pin in enumerate(node.input_pins):
        print(f"  [{i}] {pin.properties.label}")

    print("\nOutput Pins:")
    for i, pin in enumerate(node.output_pins):
        print(f"  [{i}] {pin.properties.label}")

    return len(node.input_pins), len(node.output_pins)

# Usage
node = graph.nodes[3]
in_count, out_count = inspect_node(node)
print(f"\nTotal: {in_count} inputs, {out_count} outputs")
```

---

## Verify Connection Compatibility

### Check Pin Before Connecting
```python
def can_connect(from_node, from_pin_name, to_node, to_pin_name):
    # Check from_node has output pin
    from_pin = next((p for p in from_node.output_pins if p.properties.label == from_pin_name), None)
    if not from_pin:
        print(f"ERROR: {from_pin_name} not found on source node")
        return False

    # Check to_node has input pin
    to_pin = next((p for p in to_node.input_pins if p.properties.label == to_pin_name), None)
    if not to_pin:
        print(f"ERROR: {to_pin_name} not found on target node")
        return False

    print(f"OK: Can connect {from_pin_name} → {to_pin_name}")
    return True

# Usage
if can_connect(sampler_node, "Out", projection_node, "In"):
    graph.add_edge(sampler_node, unreal.Name("Out"), projection_node, unreal.Name("In"))
```

---

## Common Pin Naming Patterns

### Standard Patterns
- **"In"** - Primary input (most nodes)
- **"Out"** - Primary output (most nodes)
- **"Spline"** - Spline data input
- **"Surface"** - Surface data input
- **"Projection Target"** - Target for projection
- **"Bounding Shape"** - Bounding volume input
- **"Overrides"** - Settings override input

### Counter-Intuitive Names
- **Input node outputs "In"** (not "Out"!)
- **Output node inputs "Out"** (not "In"!)

---

## Batch Pin Discovery

### Inspect All Nodes in Graph
```python
def inspect_graph(graph):
    print(f"Graph: {graph.get_name()}")
    print(f"Total nodes: {len(graph.nodes)}")

    for i, node in enumerate(graph.nodes):
        print(f"\n--- Node {i}: {type(node.get_settings()).__name__} ---")

        if node.output_pins:
            print("Outputs:", ", ".join([p.properties.label for p in node.output_pins]))

        if node.input_pins:
            # Show first 5 inputs (many nodes have 20+)
            inputs = [p.properties.label for p in node.input_pins[:5]]
            more = f" (+{len(node.input_pins) - 5} more)" if len(node.input_pins) > 5 else ""
            print(f"Inputs: {', '.join(inputs)}{more}")

# Usage
g = unreal.load_asset('/Game/PCG/MyGraph')
inspect_graph(g)
```

---

## Pin Type Discovery

### Check Data Type
```python
pin = node.output_pins[0]
print(f"Allowed types: {pin.properties.allowed_types}")

# Example outputs:
# - EPCGDataType::Spline
# - EPCGDataType::Point
# - EPCGDataType::Surface
# - EPCGDataType::Landscape
```

---

## Best Practices

1. **Always query before connecting unfamiliar nodes**
2. **Cache pin names** if connecting same types multiple times
3. **Check Unreal Output Log** for "does not have the X label" errors
4. **Use unreal.Name()** when connecting (not raw strings)
5. **Inspect once, connect many** - Query in separate script, then connect

---

## Example Workflow

```python
# Step 1: Discovery (separate script)
import unreal
g = unreal.load_asset('/Game/PCG/MyGraph')
node = g.nodes[3]

print("Projection node pins:")
for pin in node.input_pins:
    print(f"  Input: {pin.properties.label}")
# Output: In, Projection Target, Overrides, ...

# Step 2: Connect (separate script, Silent Execution)
g = unreal.load_asset('/Game/PCG/MyGraph')
g.add_edge(g.nodes[2], unreal.Name("Out"), g.nodes[3], unreal.Name("Projection Target"))
# Use discovered pin names with unreal.Name()
```

---

## Quick Reference

**Projection node:**
- Inputs: "In", "Projection Target"
- Outputs: "Out"

**Spline Sampler node:**
- Inputs: "Spline", "Bounding Shape", "Overrides"
- Outputs: "Out"

**Transform Points node:**
- Inputs: "In", "Overrides"
- Outputs: "Out"

**Spawn Actor node:**
- Inputs: "In", "Overrides"
- Outputs: "Out"

---

## Related

**Common Nodes Reference:** `common_nodes.md`
**Full Session:** `Session_2025-10-26_PCG_LandscapeDeformation.md`
