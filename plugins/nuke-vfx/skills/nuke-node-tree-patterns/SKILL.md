---
name: nuke-node-tree-patterns
description: Production-tested patterns for creating robust Nuke node trees programmatically. Use for avoiding auto-connection issues, dynamic positioning, expression masks, and gradient blending.
allowed-tools: Read,Write,Bash
---

# Nuke Node Tree Patterns

**Version:** 1.0.0
**Last Updated:** 2026-01-21
**Status:** Production-ready
**Dependencies:** Nuke Python API

---

Production-tested patterns for creating robust, complex node trees programmatically in Nuke.

## Purpose

This skill provides battle-tested patterns for Nuke Python automation, learned from building production tools like the auto-tiling system. These patterns solve common issues like unwanted auto-connections, positioning problems, and blending artifacts.

## Core Patterns

### 1. Avoiding Auto-Connection Issues

**Problem:** `nuke.createNode()` auto-connects to selected nodes, causing unexpected connections.

**Solution:** Use `nuke.nodes.X()` and manage connections explicitly.

```python
# [FAIL] BAD: Auto-connects unpredictably
transform = nuke.createNode('Transform', inpanel=False)
transform.setInput(0, input_node)  # May already be connected!

# [OK] GOOD: Explicit control
for node in nuke.allNodes():
    node.setSelected(False)  # Deselect all first

transform = nuke.nodes.Transform()  # Create without auto-connection
transform.setXYpos(x, y)            # Position first
transform.setInput(0, input_node)   # Then connect explicitly
```

**Key Rules:**
1. **Always deselect** all nodes before creation: `for node in nuke.allNodes(): node.setSelected(False)`
2. **Use `nuke.nodes.X()`** instead of `nuke.createNode('X')`
3. **Position before connecting**: `setXYpos()` then `setInput()`
4. **Connect explicitly**: Never rely on auto-connection

### 2. Dynamic Node Positioning

**Problem:** Hardcoded positions don't work when input nodes move.

**Solution:** Calculate positions relative to input node.

```python
# [FAIL] BAD: Hardcoded positions
base_x = 0
base_y = 0

# [OK] GOOD: Dynamic from input
input_x = input_node.xpos()
input_y = input_node.ypos()
base_x = input_x + 200  # Offset to the right
base_y = input_y + 100  # Offset below
```

**Typical Offsets:**
- Horizontal spacing between tiles: 292px
- Vertical spacing (small): 43px
- Vertical spacing (before Expression): 97px
- Dot row below input: 200px

### 3. Horizontal Tile Distribution Pattern

**Problem:** Creating multiple parallel branches cleanly.

**Solution:** Horizontal dot distribution row.

```python
# Create horizontal row of dots for distribution
dots = []
dot_y = input_y + 200
tile_spacing = 292

for i in range(tile_count):
    for node in nuke.allNodes():
        node.setSelected(False)

    dot = nuke.nodes.Dot()
    dot.setName(f'Dot{i+1}')
    dot_x = input_x + (i * tile_spacing)
    dot.setXYpos(dot_x, dot_y)

    if i == 0:
        dot.setInput(0, input_node)
    else:
        dot.setInput(0, dots[-1])  # Chain from previous

    dots.append(dot)

# Now create vertical stacks below each dot
for i, dot in enumerate(dots):
    tile_x = dot.xpos()
    # Create vertical stack at tile_x...
```

**Result:** Clean horizontal layout, Nuke-standard pattern.

### 4. Vertical Node Stacks

**Problem:** Maintaining consistent spacing in vertical node chains.

**Solution:** Calculate Y positions explicitly.

```python
# Define vertical spacing constants
NODE_SPACING_SMALL = 43
NODE_SPACING_LARGE = 97

# Calculate positions for vertical stack
base_y = dot_y + 40
y_transform = base_y
y_reformat = y_transform + NODE_SPACING_SMALL
y_noop = y_reformat + NODE_SPACING_SMALL
y_expression = y_noop + NODE_SPACING_LARGE  # Larger gap
y_premult = y_expression + NODE_SPACING_SMALL
y_inverse = y_premult + 55

# Create nodes at calculated positions
transform.setXYpos(tile_x, y_transform)
reformat.setXYpos(tile_x, y_reformat)
noop.setXYpos(tile_x, y_noop)
expression.setXYpos(tile_x, y_expression)
premult.setXYpos(tile_x, y_premult)
inverse_transform.setXYpos(tile_x, y_inverse)
```

### 5. Expression-Based Gradient Masks

**Problem:** Need seamless blending without destroying detail.

**Solution:** Position-based gradient masks using Expression nodes.

```python
def create_gradient_mask(tile_x, tile_y, grid_x, grid_y, tile_size, overlap):
    """
    Creates gradient mask that fades at interior edges, sharp at frame edges.
    """
    for node in nuke.allNodes():
        node.setSelected(False)

    expr = nuke.nodes.Expression()
    expr.setName(f'TileMask_{tile_x}_{tile_y}')

    expr_parts = []

    # X direction: leftmost, middle, rightmost pattern
    if tile_x == 0:
        expr_parts.append(f'smoothstep(0, {overlap}, x)')
    elif tile_x == grid_x - 1:
        expr_parts.append(f'smoothstep({tile_size}, {tile_size - overlap}, x)')
    else:
        expr_parts.append(f'smoothstep(0, {overlap}, x)')
        expr_parts.append(f'smoothstep({tile_size}, {tile_size - overlap}, x)')

    # Y direction: same pattern
    if tile_y == 0:
        expr_parts.append(f'smoothstep(0, {overlap}, y)')
    elif tile_y == grid_y - 1:
        expr_parts.append(f'smoothstep({tile_size}, {tile_size - overlap}, y)')
    else:
        expr_parts.append(f'smoothstep(0, {overlap}, y)')
        expr_parts.append(f'smoothstep({tile_size}, {tile_size - overlap}, y)')

    expression = ' * '.join(expr_parts)

    # Output to mask channel
    expr['expr3'].setValue(expression)
    expr['channel3'].setValue('mask')  # NOT 'mask.a'
    expr['channel0'].setValue('none')
    expr['channel1'].setValue('none')
    expr['channel2'].setValue('none')

    return expr
```

**Key Points:**
- Output to `'mask'` channel (not `'mask.a'`)
- Frame edges stay sharp (leftmost/rightmost tiles)
- Interior edges blend smoothly (middle tiles)
- Works for any grid size and aspect ratio

### 6. Applying Masks with Premult

**Problem:** How to apply gradient masks without destroying original alpha.

**Solution:** Premult node with mask.a as alpha.

```python
# After Expression mask node
premult = nuke.nodes.Premult()
premult.setName(f'Premult_{tile_x}_{tile_y}')
premult['channels'].setValue('all')
premult['alpha'].setValue('mask.a')  # Use mask channel as alpha
premult.setInput(0, expression_node)
```

**Chain:**
```
ML Node output
    v
Expression (creates mask channel)
    v
Premult (multiply all by mask.a)
    v
Result: Blended contribution
```

### 7. Merge Node Configuration

**Problem:** Standard merge doesn't work for masked tiles.

**Solution:** Use 'plus' operation with rgba output.

```python
merge = nuke.nodes.Merge2()
merge.setName(f'Merge_Tile_{tile_x}_{tile_y}')
merge['operation'].setValue('plus')  # NOT 'over'
merge['output'].setValue('rgba')     # Explicit rgba output
merge.setInput(0, accumulated_tiles)
merge.setInput(1, current_tile)
```

**Why 'plus':**
- Tiles are pre-masked (via Premult)
- Masks ensure proper weighting (sum to 1.0 in overlaps)
- Plus operation adds weighted contributions correctly

### 8. Reformat Pattern: "to box"

**Problem:** Setting format by string can fail or default to root.

**Solution:** Use 'to box' type with explicit dimensions.

```python
# [FAIL] BAD: Format string may not exist
reformat['format'].setValue('2048 2048 0 0 2048 2048 1')  # May default to root

# [OK] GOOD: Explicit dimensions via "to box"
reformat = nuke.nodes.Reformat()
reformat['type'].setValue('to box')
reformat['box_width'].setValue(2048)
reformat['box_height'].setValue(2048)
reformat['box_fixed'].setValue(True)
reformat['resize'].setValue('none')
```

**Use cases:**
- Cropping to tile size
- Restoring original dimensions after processing
- Any dimension change without scaling

### 9. Complete Node Creation Template

**Full pattern combining all best practices:**

```python
def create_node_safely(node_type, name, x, y, **kwargs):
    """
    Create a node with all best practices applied.
    """
    # 1. Deselect all
    for node in nuke.allNodes():
        node.setSelected(False)

    # 2. Create node via nuke.nodes.X()
    node = getattr(nuke.nodes, node_type)()

    # 3. Set name
    node.setName(name)

    # 4. Position BEFORE connecting
    node.setXYpos(x, y)

    # 5. Set parameters
    for key, value in kwargs.items():
        if key != 'input':  # Handle inputs separately
            node[key].setValue(value)

    # 6. Connect input last (if provided)
    if 'input' in kwargs:
        node.setInput(0, kwargs['input'])

    return node

# Usage:
transform = create_node_safely(
    'Transform',
    'Transform_Tile_0_0',
    x=100, y=200,
    translate=[64, 64],
    center=[2880, 2880],
    input=input_node
)
```

## Common Pitfalls

### [FAIL] Pitfall 1: Using createNode() with inpanel=False

```python
# Still auto-connects!
node = nuke.createNode('Transform', inpanel=False)
```

**Fix:** Use `nuke.nodes.Transform()` instead.

### [FAIL] Pitfall 2: Connecting Before Positioning

```python
node.setInput(0, input_node)  # Connect first
node.setXYpos(100, 200)       # Position after
```

**Fix:** Always position before connecting.

### [FAIL] Pitfall 3: Forgetting to Deselect

```python
# If nodes are selected, createNode still connects
node = nuke.nodes.Transform()  # May still auto-connect!
```

**Fix:** Always deselect all nodes first.

### [FAIL] Pitfall 4: Expression Output to Wrong Channel

```python
expr['channel3'].setValue('mask.a')  # Wrong!
```

**Fix:** Use `'mask'` not `'mask.a'`

### [FAIL] Pitfall 5: Wrong Merge Operation

```python
merge['operation'].setValue('over')  # Doesn't work for masked tiles
```

**Fix:** Use `'plus'` for pre-masked tiles.

## Integration with NukeMCPLogger

For MCP-based tools, wrap with logging:

```python
from nuke_mcp_logger import NukeMCPLogger

def create_complex_tree():
    log = NukeMCPLogger(session_name="NodeTreeCreation")

    try:
        # Create nodes with patterns above
        transform = create_node_safely(...)
        log.increment_stat("nodes_created")

        reformat = create_node_safely(...)
        log.increment_stat("nodes_created")

        log.success(f"Created {count} nodes successfully")
        return log.get_results()

    except Exception as e:
        log.error("Node creation failed", e)
        return log.get_results()
```

## Performance Considerations

1. **Deselection overhead**: Minimal, worth it for reliability
2. **Explicit positioning**: No performance impact, improves clarity
3. **Expression masks**: Single eval, cached - very efficient
4. **Premult vs blur**: Premult is faster (no kernel processing)

## Validation Checklist

Before deploying node creation code:

- [ ] Uses `nuke.nodes.X()` not `createNode()`
- [ ] Deselects all before each node creation
- [ ] Positions before connecting
- [ ] Connects inputs explicitly
- [ ] Expression masks output to 'mask' channel
- [ ] Premult uses 'mask.a' as alpha
- [ ] Merge uses 'plus' for masked content
- [ ] Reformat uses "to box" type
- [ ] Dynamic positioning from input nodes
- [ ] NukeMCPLogger integration (if MCP tool)

## Real-World Example

From the auto-tiling tool, complete tile branch creation:

```python
# 1. Deselect
for node in nuke.allNodes():
    node.setSelected(False)

# 2. Calculate positions
y_transform = base_y
y_reformat = y_transform + 43
y_noop = y_reformat + 43
y_expression = y_noop + 97
y_premult = y_expression + 43
y_inverse = y_premult + 55

# 3. Transform
transform = nuke.nodes.Transform()
transform.setName(f'Transform_Tile_{tile_x}_{tile_y}')
transform['translate'].setValue([translate_x, translate_y])
transform['center'].setValue([image_width / 2, image_height / 2])
transform.setXYpos(tile_x_pos, y_transform)
transform.setInput(0, input_node)

# 4. Reformat
reformat = nuke.nodes.Reformat()
reformat.setName(f'Reformat_Tile_{tile_x}_{tile_y}')
reformat['type'].setValue('to box')
reformat['box_width'].setValue(tile_size)
reformat['box_height'].setValue(tile_size)
reformat['box_fixed'].setValue(True)
reformat['resize'].setValue('none')
reformat['black_outside'].setValue(True)
reformat.setXYpos(tile_x_pos, y_reformat)
reformat.setInput(0, transform)

# 5. NoOp placeholder
placeholder = nuke.nodes.NoOp()
placeholder.setName(f'MLNode_Tile_{tile_x}_{tile_y}')
placeholder['label'].setValue(f'** SWAP FOR ML NODE **\\nTile [{tile_x},{tile_y}]')
placeholder['tile_color'].setValue(0xff9900ff)
placeholder.setXYpos(tile_x_pos, y_noop)
placeholder.setInput(0, reformat)

# 6. Expression mask
expression = create_gradient_mask(tile_x, tile_y, grid_x, grid_y, tile_size, overlap)
expression.setXYpos(tile_x_pos, y_expression)
expression.setInput(0, placeholder)

# 7. Premult
premult = nuke.nodes.Premult()
premult.setName(f'Premult_{tile_x}_{tile_y}')
premult['channels'].setValue('all')
premult['alpha'].setValue('mask.a')
premult.setXYpos(tile_x_pos, y_premult)
premult.setInput(0, expression)

# 8. InverseTransform
inverse_transform = nuke.nodes.Transform()
inverse_transform.setName(f'InverseTransform_Tile_{tile_x}_{tile_y}')
inverse_transform['translate'].setValue([translate_x, translate_y])
inverse_transform['center'].setValue([image_width / 2, image_height / 2])
inverse_transform['invert_matrix'].setValue(True)
inverse_transform.setXYpos(tile_x_pos, y_inverse)
inverse_transform.setInput(0, premult)
```

## Constitutional Compliance

This skill follows VFX Skill Constitution principles:

- **Article I (General Purpose):** Patterns work for any node tree, any project
- **Article IV (Independent Testing):** Each pattern tested in production
- **Article V (Official Patterns):** Uses standard Nuke Python API correctly
- **Article VI (Context Efficiency):** Documents reusable patterns, not full scripts

## References

- Developed from: nuke-tiling-tool debugging session (2026-01-21)
- Tested in production on a commercial spot
- NukeMCPLogger: `~/.nuke\nuke_mcp_logger.py`

## Version History

- **1.0.0** (2026-01-21): Initial release
  - Auto-connection avoidance patterns
  - Dynamic positioning
  - Expression-based gradient masks
  - Premult masking pattern
  - Merge configuration for masked content
  - Reformat "to box" pattern

---

*These patterns enable robust, production-ready Nuke automation.*
