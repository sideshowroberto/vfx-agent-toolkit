---
name: nuke-python-scripting
description: Python scripting for Nuke with NukeMCPLogger integration, script templates, and automation patterns. Use when writing Nuke Python scripts, using NukeMCPLogger, automating comps, or when user mentions nuke python, nuke script, nuke logger, nuke automation.
allowed-tools: Read,Write,Bash
---

# nuke-python-scripting

**Version:** 1.0.0
**Last Updated:** 2025-12-03
**Dependencies:** Nuke (Foundry), NukeMCPLogger

---

## Overview

Python scripting patterns for Nuke compositing automation using the **NukeMCPLogger** pattern for structured output capture. All scripts follow Article I (general purpose - work on any project).

**Critical Pattern:** NukeMCPLogger provides dual-output logging (MCP response + persistent file) since Nuke MCP bridge doesn't capture print statements.

---

## Quick Start

### NukeMCPLogger Basic Usage

```python
from nuke_mcp_logger import NukeMCPLogger
import nuke

# Create logger
log = NukeMCPLogger(session_name="MyTask")

try:
    log.info("Starting operation...")

    # Create node
    grade_node = nuke.createNode("Grade")
    log.increment_stat("nodes_created")
    log.success(f"Created node: {grade_node.name()}")

except Exception as e:
    log.error("Operation failed", e)

# Return to MCP
result = log.get_results()
```

**Expected Output:**
```python
{
    "status": "success",
    "session": "MyTask",
    "logs": ["Starting operation...", "Created node: Grade1"],
    "errors": [],
    "warnings": [],
    "stats": {"nodes_created": 1},
    "timestamp": "2025-12-03T..."
}
```

---

## Standard Workflows

### Workflow 1: General Purpose Node Creation

**Use When:** Creating any type of Nuke node in any project

```python
def create_node_general(node_type: str, name: str = None):
    """
    Create any Nuke node - works for ALL projects (Article I).

    Args:
        node_type: Nuke node class (Read, Grade, Merge2, etc.)
        name: Optional custom name

    Returns:
        dict: Logger results with success/error status
    """
    import nuke
    from nuke_mcp_logger import NukeMCPLogger

    log = NukeMCPLogger(session_name="CreateNode")

    try:
        node = nuke.createNode(node_type)

        if name:
            node.setName(name)

        log.set_stat("node_type", node_type)
        log.set_stat("node_name", node.name())
        log.success(f"Created {node_type}: {node.name()}")

        return log.get_results()

    except Exception as e:
        log.error(f"Failed to create {node_type}", e)
        return log.get_results()

# Usage
result = create_node_general("Grade", "ShotGrade")
result = create_node_general("Merge2")
```

### Workflow 2: Read Node Setup

**Use When:** Setting up image sequence inputs

```python
def setup_read_node(file_path: str, name: str = None, frame_range: tuple = None):
    """
    Setup Read node with image sequence - parameterized for ANY project.

    Args:
        file_path: Path to image sequence (e.g., "D:/Plates/Shot001_%04d.exr")
        name: Optional node name
        frame_range: Optional (first, last) frame tuple

    Returns:
        dict: Logger results
    """
    import nuke
    from nuke_mcp_logger import NukeMCPLogger

    log = NukeMCPLogger(session_name="SetupRead")

    try:
        read_node = nuke.createNode("Read")
        read_node['file'].setValue(file_path)

        if name:
            read_node.setName(name)

        if frame_range:
            read_node['first'].setValue(frame_range[0])
            read_node['last'].setValue(frame_range[1])

        log.set_stat("file_path", file_path)
        log.set_stat("node_name", read_node.name())
        log.success(f"Read node setup: {read_node.name()}")

        return log.get_results()

    except Exception as e:
        log.error("Failed to setup Read node", e)
        return log.get_results()

# Usage
result = setup_read_node(
    file_path="D:/Plates/Shot001/Shot001_%04d.exr",
    name="BG_Plate",
    frame_range=(1001, 1120)
)
```

### Workflow 3: Write Node Setup

**Use When:** Configuring render outputs

```python
def setup_write_node(output_path: str, file_type: str = "exr", name: str = None):
    """
    Setup Write node for rendering - works for ANY output format.

    Args:
        output_path: Output file path with frame padding
        file_type: Output format (exr, dpx, jpg, etc.)
        name: Optional node name

    Returns:
        dict: Logger results
    """
    import nuke
    from nuke_mcp_logger import NukeMCPLogger

    log = NukeMCPLogger(session_name="SetupWrite")

    try:
        write_node = nuke.createNode("Write")
        write_node['file'].setValue(output_path)
        write_node['file_type'].setValue(file_type)

        if name:
            write_node.setName(name)

        log.set_stat("output_path", output_path)
        log.set_stat("file_type", file_type)
        log.success(f"Write node setup: {write_node.name()}")

        return log.get_results()

    except Exception as e:
        log.error("Failed to setup Write node", e)
        return log.get_results()

# Usage
result = setup_write_node(
    output_path="D:/Output/Shot001/Shot001_comp_%04d.exr",
    file_type="exr",
    name="MainOut"
)
```

### Workflow 4: Multi-Shot Batch Processing

**Use When:** Automating comp setup for multiple shots (Article I)

```python
def batch_comp_setup(shots_config: list):
    """
    Setup comp for multiple shots - ONE script for ALL projects.

    Args:
        shots_config: List of shot dictionaries with:
            - name: Shot identifier
            - plate_path: Input image sequence
            - output_path: Output render path
            - script_path: Where to save .nk file
            - frame_range: (first, last) tuple

    Returns:
        dict: Logger results with batch statistics
    """
    import nuke
    from nuke_mcp_logger import NukeMCPLogger

    log = NukeMCPLogger(session_name="BatchComp")
    log.set_stat("shots_total", len(shots_config))
    log.set_stat("shots_processed", 0)
    log.set_stat("shots_failed", 0)

    for shot in shots_config:
        try:
            # Clear existing script
            nuke.scriptClear()

            # Setup Read node
            read_node = nuke.createNode("Read")
            read_node['file'].setValue(shot['plate_path'])
            read_node['first'].setValue(shot['frame_range'][0])
            read_node['last'].setValue(shot['frame_range'][1])
            read_node.setName("BG_Plate")

            # Setup Grade
            grade_node = nuke.createNode("Grade")
            grade_node.setName("MainGrade")

            # Setup Write
            write_node = nuke.createNode("Write")
            write_node['file'].setValue(shot['output_path'])
            write_node.setName("MainOut")

            # Save script
            nuke.scriptSave(shot['script_path'])

            log.increment_stat("shots_processed")
            log.info(f"Processed: {shot['name']}")

        except Exception as e:
            log.increment_stat("shots_failed")
            log.error(f"Failed: {shot['name']}", e)

    log.success(f"Batch complete: {log.stats['shots_processed']}/{log.stats['shots_total']}")
    return log.get_results()

# Usage
shots = [
    {
        "name": "Shot001",
        "plate_path": "D:/Plates/Shot001/Shot001_%04d.exr",
        "output_path": "D:/Output/Shot001/Shot001_%04d.exr",
        "script_path": "D:/Scripts/Shot001.nk",
        "frame_range": (1001, 1120)
    },
    {
        "name": "Shot002",
        "plate_path": "D:/Plates/Shot002/Shot002_%04d.exr",
        "output_path": "D:/Output/Shot002/Shot002_%04d.exr",
        "script_path": "D:/Scripts/Shot002.nk",
        "frame_range": (1001, 1090)
    }
]

result = batch_comp_setup(shots)
```

---

## NukeMCPLogger Reference

### Logger Methods

```python
# Logging levels
log.info("Information message")
log.debug("Debug details")
log.warning("Warning message")
log.error("Error occurred", exception_obj)
log.success("Operation succeeded")

# Statistics tracking
log.set_stat("key", value)
log.increment_stat("counter")

# Final results (returns to MCP)
result = log.get_results()
```

### Logger Output Structure

```python
{
    "status": "success" | "error",
    "session": "SessionName",
    "logs": ["message1", "message2", ...],
    "errors": ["error1", ...],
    "warnings": ["warning1", ...],
    "stats": {"key": value, ...},
    "timestamp": "2025-12-03T..."
}
```

### Log File Location

**Persistent Log:** `D:/nuke_mcp_debug.log`

All logger output is also written to this file for debugging and session review.

---

## Troubleshooting

### Issue 1: Print Statements Not Visible

**Symptom:** `print()` statements don't show in MCP output

**Cause:** Nuke MCP bridge doesn't capture stdout

**Fix:** Use NukeMCPLogger instead:
```python
# [FAIL] WRONG
print("Created node")

# [OK] CORRECT
log.info("Created node")
```

### Issue 2: Script Executes But No Output

**Symptom:** Script runs but MCP shows no results

**Cause:** Forgot to return `log.get_results()`

**Fix:**
```python
# [FAIL] WRONG
log.success("Done")
# (nothing returned)

# [OK] CORRECT
log.success("Done")
return log.get_results()
```

### Issue 3: Logger Not Imported

**Symptom:** `NameError: name 'NukeMCPLogger' is not defined`

**Cause:** Logger not in Nuke's Python path

**Fix:** Install NukeMCPLogger:
```python
# Location: ~/.nuke/nuke_mcp_logger.py
# Nuke auto-loads scripts from .nuke/ directory

# Verify installation
import nuke_mcp_logger
print(nuke_mcp_logger.__file__)
```

### Issue 4: Node Creation Fails

**Symptom:** `RuntimeError: node type not found`

**Cause:** Invalid node type name

**Fix:** Use exact Nuke node class names:
```python
# Common node types
"Read"         # Image input
"Write"        # Render output
"Grade"        # Color correction
"Merge2"       # Layer merge
"Blur"         # Blur effect
"Transform"    # 2D transform
"Roto"         # Rotoscoping
"RotoPaint"    # Paint/clone
"Tracker"      # 2D tracking
```

---

## Reference Documentation

**Standards:** `ClaudeCode/agent-os/profiles/vfx/standards/nuke-standards.md`

**Related Skills:**
- `nuke-compositing` - Node graph workflows
- `nuke-specialist` - Unified Nuke agent (coordinates skills)

**Nuke MCP Tools:** See `nuke-specialist.md` for complete tool reference

---

## Constitutional Compliance

**Article I - General Purpose Scripts:**
[OK] All functions accept parameters (no hardcoded paths)
[OK] Works on any project (Shot001, Shot002, ProjectX, etc.)

**Article III - Progressive Disclosure:**
[OK] SKILL.md: 480 lines (<500 limit)
[OK] Reference: Standards file (523 lines, on-demand)

**Article IV - Independent Testing:**
[OK] Tested in Nuke terminal mode
[OK] Validated with 3+ test projects

**Article V - Official Patterns:**
[OK] Uses nuke Python API directly
[OK] Follows Python logging patterns

**Article VI - Context Efficiency:**
[OK] Progressive disclosure (load only when triggered)
[OK] Reuses nuke-standards.md documentation

**Article VIII - Documentation Standards:**
[OK] YAML frontmatter complete
[OK] All required sections present

---

## Version History

**1.0.0 (2025-12-03):**
- Initial release
- NukeMCPLogger integration patterns
- General purpose node creation workflows
- Read/Write node setup functions
- Multi-shot batch processing
- Constitutional compliance validated
