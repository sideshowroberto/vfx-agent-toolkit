"""
Automated Image Tiling Tool for Nuke ML Processing

This script automatically tiles large images for processing through ML nodes (like ViTMatte)
that work best with smaller image sizes. It creates a node tree that:
1. Divides the input image into overlapping tiles
2. Processes each tile through an ML node
3. Seamlessly blends the tiles back together using gradient masks

Author: Claude Code
Created: 2026-01-21
Version: 1.0.0
"""

import math
import nuke


# ============================================================================
# CONFIGURATION
# ============================================================================

TILE_SIZES = {
    '1K': 1024,
    '2K': 2048,
}

DEFAULT_OVERLAP = 128  # pixels
DEFAULT_TILE_SIZE = '2K'

# Node layout spacing (Nuke-standard horizontal tile layout)
TILE_SPACING = 292  # Horizontal spacing between tile branches
NODE_SPACING_SMALL = 43  # Vertical spacing between most nodes
NODE_SPACING_LARGE = 97  # Larger gap before Expression mask
START_X = 0
START_Y = 0


# ============================================================================
# GRID CALCULATION
# ============================================================================

def calculate_grid_dimensions(image_width, image_height, tile_size, overlap):
    """
    Calculate optimal grid dimensions for tiling.

    Args:
        image_width (int): Width of input image
        image_height (int): Height of input image
        tile_size (int): Size of square tiles (e.g., 1024, 2048)
        overlap (int): Overlap between tiles in pixels

    Returns:
        tuple: (grid_x, grid_y) - number of tiles in each dimension

    Examples:
        - 5760x5760 image, 2048 tile, 128 overlap:
          Effective step = 2048 - 128 = 1920
          Grid = (3, 3)

        - 8192x8192 image, 2048 tile, 128 overlap:
          Grid = (5, 5)
    """
    effective_step = tile_size - overlap
    grid_x = math.ceil(image_width / effective_step)
    grid_y = math.ceil(image_height / effective_step)
    return grid_x, grid_y


# ============================================================================
# TILE TRANSFORM CALCULATION
# ============================================================================

def calculate_tile_transform(tile_x, tile_y, tile_size, overlap, image_width, image_height):
    """
    Calculate transform translate values for a tile.

    Args:
        tile_x (int): Tile column index (0-indexed)
        tile_y (int): Tile row index (0-indexed)
        tile_size (int): Size of square tile
        overlap (int): Overlap between tiles in pixels
        image_width (int): Width of input image
        image_height (int): Height of input image

    Returns:
        tuple: (translate_x, translate_y) for Transform node
    """
    effective_step = tile_size - overlap
    image_center_x = image_width / 2.0
    image_center_y = image_height / 2.0

    # Calculate top-left corner of tile in original image space
    tile_offset_x = tile_x * effective_step
    tile_offset_y = tile_y * effective_step

    # Convert to transform translate values (relative to image center)
    # Transform node translates relative to center, so we need to:
    # 1. Find tile center in image space
    # 2. Subtract image center to get relative offset
    tile_center_x = tile_offset_x + tile_size / 2.0
    tile_center_y = tile_offset_y + tile_size / 2.0

    translate_x = tile_center_x - image_center_x
    translate_y = tile_center_y - image_center_y

    return translate_x, translate_y


# ============================================================================
# EXPRESSION-BASED BLEND MASK CREATION
# ============================================================================

def create_expression_blend_mask(tile_x, tile_y, grid_x, grid_y, tile_size, overlap):
    """
    Creates an Expression node that generates a gradient mask for seamless tile blending.

    The mask is:
    - 1.0 in the tile center (full contribution)
    - Fades to 0.0 at edges over the overlap distance (smoothstep falloff)
    - Handles edge/corner tiles (no fade where there's no neighboring tile)

    Args:
        tile_x (int): Tile column index
        tile_y (int): Tile row index
        grid_x (int): Total columns in grid
        grid_y (int): Total rows in grid
        tile_size (int): Size of square tile
        overlap (int): Overlap distance in pixels

    Returns:
        nuke.Node: Expression node generating the blend mask
    """
    # Deselect all to prevent auto-connection
    for node in nuke.allNodes():
        node.setSelected(False)

    expr_node = nuke.nodes.Expression()
    expr_node.setName(f'TileMask_{tile_x}_{tile_y}')

    # Build expression based on grid position
    # Pattern:
    # - Leftmost column (x=0): only left fade
    # - Middle columns: both left AND right fade
    # - Rightmost column: only right fade
    # Same for Y direction
    expr_parts = []

    # X direction (horizontal fades)
    if tile_x == 0:
        # Leftmost column: fade in from left edge
        expr_parts.append(f'smoothstep(0, {overlap}, x)')
    elif tile_x == grid_x - 1:
        # Rightmost column: fade out to right edge
        expr_parts.append(f'smoothstep({tile_size}, {tile_size - overlap}, x)')
    else:
        # Middle columns: fade both edges
        expr_parts.append(f'smoothstep(0, {overlap}, x)')
        expr_parts.append(f'smoothstep({tile_size}, {tile_size - overlap}, x)')

    # Y direction (vertical fades)
    if tile_y == 0:
        # Top row: fade in from top edge
        expr_parts.append(f'smoothstep(0, {overlap}, y)')
    elif tile_y == grid_y - 1:
        # Bottom row: fade out to bottom edge
        expr_parts.append(f'smoothstep({tile_size}, {tile_size - overlap}, y)')
    else:
        # Middle rows: fade both edges
        expr_parts.append(f'smoothstep(0, {overlap}, y)')
        expr_parts.append(f'smoothstep({tile_size}, {tile_size - overlap}, y)')

    # Multiply all factors together
    expression = ' * '.join(expr_parts) if expr_parts else '1.0'

    # Set expression to output to mask channel
    expr_node['expr3'].setValue(expression)
    expr_node['channel3'].setValue('mask')  # Output to mask channel

    # Disable RGB channels (pass through)
    expr_node['channel0'].setValue('none')  # Red
    expr_node['channel1'].setValue('none')  # Green
    expr_node['channel2'].setValue('none')  # Blue

    return expr_node


# ============================================================================
# TILE BRANCH CREATION
# ============================================================================

def create_tile_branch(input_node, tile_x, tile_y, grid_x, grid_y, tile_size, overlap,
                       image_width, image_height, tile_x_pos, base_y):
    """
    Creates a complete tile processing branch (vertical stack):
    Transform → Reformat → NoOp → Expression (mask) → Premult → InverseTransform

    Args:
        input_node (nuke.Node): Input image node
        tile_x (int): Tile column index
        tile_y (int): Tile row index
        grid_x (int): Total columns in grid
        grid_y (int): Total rows in grid
        tile_size (int): Size of square tile
        overlap (int): Overlap in pixels
        image_width (int): Width of input image
        image_height (int): Height of input image
        tile_x_pos (int): X position for this tile column
        base_y (int): Y position for top of tile branches

    Returns:
        dict: {
            'transform': Transform node,
            'reformat': Reformat node,
            'placeholder': NoOp placeholder node,
            'expression': Expression mask node,
            'premult': Premult node,
            'inverse_transform': InverseTransform node,
            'output': Final output node of branch
        }
    """
    # Calculate transform values
    translate_x, translate_y = calculate_tile_transform(
        tile_x, tile_y, tile_size, overlap, image_width, image_height
    )

    # Deselect all to prevent auto-connection issues
    for node in nuke.allNodes():
        node.setSelected(False)

    # Vertical positions for each node in the branch
    y_transform = base_y
    y_reformat = y_transform + NODE_SPACING_SMALL
    y_noop = y_reformat + NODE_SPACING_SMALL
    y_expression = y_noop + NODE_SPACING_LARGE
    y_premult = y_expression + NODE_SPACING_SMALL
    y_inverse = y_premult + 55  # Slightly larger gap

    # Create Transform node
    transform = nuke.nodes.Transform()
    transform.setName(f'Transform_Tile_{tile_x}_{tile_y}')
    transform['translate'].setValue([translate_x, translate_y])
    transform['center'].setValue([image_width / 2.0, image_height / 2.0])
    transform.setXYpos(tile_x_pos, y_transform)
    transform.setInput(0, input_node)

    # Create Reformat node (crop to tile size)
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

    # Create NoOp placeholder for ML node
    placeholder = nuke.nodes.NoOp()
    placeholder.setName(f'MLNode_Tile_{tile_x}_{tile_y}')
    placeholder['label'].setValue(f'** SWAP FOR ML NODE **\nTile [{tile_x},{tile_y}]')
    placeholder['note_font_size'].setValue(20)
    placeholder['tile_color'].setValue(0xff9900ff)
    placeholder.setXYpos(tile_x_pos, y_noop)
    placeholder.setInput(0, reformat)

    # Create Expression node for gradient mask
    expression = create_expression_blend_mask(tile_x, tile_y, grid_x, grid_y, tile_size, overlap)
    expression.setXYpos(tile_x_pos, y_expression)
    expression.setInput(0, placeholder)

    # Create Premult node to apply mask
    premult = nuke.nodes.Premult()
    premult.setName(f'Premult_{tile_x}_{tile_y}')
    premult['channels'].setValue('all')
    premult['alpha'].setValue('mask.a')
    premult.setXYpos(tile_x_pos, y_premult)
    premult.setInput(0, expression)

    # Create InverseTransform node (restore to original position)
    inverse_transform = nuke.nodes.Transform()
    inverse_transform.setName(f'InverseTransform_Tile_{tile_x}_{tile_y}')
    inverse_transform['translate'].setValue([translate_x, translate_y])
    inverse_transform['center'].setValue([image_width / 2.0, image_height / 2.0])
    inverse_transform['invert_matrix'].setValue(True)
    inverse_transform.setXYpos(tile_x_pos, y_inverse)
    inverse_transform.setInput(0, premult)

    return {
        'transform': transform,
        'reformat': reformat,
        'placeholder': placeholder,
        'expression': expression,
        'premult': premult,
        'inverse_transform': inverse_transform,
        'output': inverse_transform,
        'tile_x': tile_x,
        'tile_y': tile_y,
    }


# ============================================================================
# MERGE TREE WITH MASKED BLENDING
# ============================================================================

def merge_tiles(tile_branches, merge_y):
    """
    Creates a merge tree that combines all tiles.
    Tiles already have gradient masks applied via Premult nodes.

    Args:
        tile_branches (list): List of tile branch dicts from create_tile_branch()
        merge_y (int): Y position for merge nodes

    Returns:
        nuke.Node: Final merged output node
    """
    if not tile_branches:
        return None

    if len(tile_branches) == 1:
        # Only one tile, no merging needed
        return tile_branches[0]['output']

    # Deselect all
    for node in nuke.allNodes():
        node.setSelected(False)

    # Build sequential merge tree
    # Start with first tile
    current_output = tile_branches[0]['output']

    # Merge remaining tiles sequentially
    for i, branch in enumerate(tile_branches[1:]):
        tile_x = branch['tile_x']
        tile_y = branch['tile_y']

        # Position merge at the current tile's X position
        current_merge_x = branch['output'].xpos()

        for node in nuke.allNodes():
            node.setSelected(False)

        merge = nuke.nodes.Merge2()
        merge.setName(f'Merge_Tile_{tile_x}_{tile_y}')
        merge['operation'].setValue('plus')  # Plus operation for masked tiles
        merge['output'].setValue('rgba')  # Output RGBA channels
        merge.setXYpos(current_merge_x, merge_y)
        merge.setInput(0, current_output)  # A input (accumulated tiles)
        merge.setInput(1, branch['output'])  # B input (current tile)

        current_output = merge

    return current_output


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def create_tiling_setup(input_node=None, tile_size='2K', overlap=DEFAULT_OVERLAP):
    """
    Main entry point: Creates complete tiling setup for ML processing.

    Args:
        input_node (nuke.Node, optional): Input image node. If None, uses selected node.
        tile_size (str): Tile size ('1K' or '2K'). Default: '2K'
        overlap (int): Overlap between tiles in pixels. Default: 128

    Returns:
        dict: Results with status, tile info, and node references
            {
                'status': 'success' or 'error',
                'message': str,
                'grid': (grid_x, grid_y),
                'tile_count': int,
                'placeholders': [list of Group nodes to insert ML nodes],
                'output': final merged node,
            }

    Usage:
        # Select a Read node, then:
        result = create_tiling_setup(tile_size='2K')
        print(result['message'])
        # Insert your ML nodes into result['placeholders']
    """
    try:
        # Get input node
        if input_node is None:
            selected = nuke.selectedNodes()
            if not selected:
                return {
                    'status': 'error',
                    'message': 'No node selected. Please select an input image node.',
                }
            input_node = selected[0]

        # Get image format
        format_obj = input_node.format()
        if not format_obj:
            return {
                'status': 'error',
                'message': f'Node "{input_node.name()}" has no format information.',
            }

        image_width = format_obj.width()
        image_height = format_obj.height()

        # Resolve tile size
        if tile_size not in TILE_SIZES:
            return {
                'status': 'error',
                'message': f'Invalid tile_size "{tile_size}". Must be "1K" or "2K".',
            }

        tile_size_px = TILE_SIZES[tile_size]

        # Check if image is too small for tiling
        if image_width <= tile_size_px and image_height <= tile_size_px:
            return {
                'status': 'error',
                'message': f'Image ({image_width}x{image_height}) is smaller than tile size ({tile_size_px}x{tile_size_px}). Tiling not needed.',
            }

        # Calculate grid dimensions
        grid_x, grid_y = calculate_grid_dimensions(image_width, image_height, tile_size_px, overlap)
        tile_count = grid_x * grid_y

        print(f"Creating tiling setup:")
        print(f"  Input: {input_node.name()} ({image_width}x{image_height})")
        print(f"  Tile size: {tile_size} ({tile_size_px}x{tile_size_px})")
        print(f"  Overlap: {overlap}px")
        print(f"  Grid: {grid_x}x{grid_y} ({tile_count} tiles)")

        # Get input node position and use as base for layout
        input_x = input_node.xpos()
        input_y = input_node.ypos()

        # Create distribution dots (horizontal row below input)
        dots = []
        dot_y = input_y + 200  # Below input
        first_dot_x = input_x

        for node in nuke.allNodes():
            node.setSelected(False)

        for i in range(tile_count):
            dot = nuke.nodes.Dot()
            dot.setName(f'Dot{i+1}')
            dot_x = first_dot_x + (i * TILE_SPACING)
            dot.setXYpos(dot_x, dot_y)

            if i == 0:
                dot.setInput(0, input_node)
            else:
                dot.setInput(0, dots[-1])

            dots.append(dot)

        # Create all tile branches (vertical stacks, one per tile)
        tile_branches = []
        placeholders = []
        base_y_tiles = dot_y + 40  # Start tiles below the dot row

        tile_index = 0
        for tile_y in range(grid_y):
            for tile_x in range(grid_x):
                # X position for this tile column
                tile_x_pos = first_dot_x + (tile_index * TILE_SPACING)

                branch = create_tile_branch(
                    input_node=dots[tile_index],
                    tile_x=tile_x,
                    tile_y=tile_y,
                    grid_x=grid_x,
                    grid_y=grid_y,
                    tile_size=tile_size_px,
                    overlap=overlap,
                    image_width=image_width,
                    image_height=image_height,
                    tile_x_pos=tile_x_pos,
                    base_y=base_y_tiles,
                )

                tile_branches.append(branch)
                placeholders.append(branch['placeholder'])
                tile_index += 1

        print(f"  Created {len(tile_branches)} tile branches")

        # Create merge tree
        # Calculate merge_y based on actual InverseTransform positions
        # Total branch height from base to InverseTransform = 43 + 43 + 97 + 43 + 55 = 281
        # Add a gap below InverseTransform (gap from example = 109)
        merge_y = base_y_tiles + 281 + 109
        merge_output = merge_tiles(tile_branches, merge_y)

        print(f"  Created merge tree")

        # Add final Reformat to restore original format
        for node in nuke.allNodes():
            node.setSelected(False)

        final_reformat = nuke.nodes.Reformat()
        final_reformat.setName('Reformat_Final')

        # Use "to box" type to set dimensions back to original input size
        final_reformat['type'].setValue('to box')
        final_reformat['box_width'].setValue(image_width)
        final_reformat['box_height'].setValue(image_height)
        final_reformat['box_fixed'].setValue(True)
        final_reformat['resize'].setValue('none')
        final_reformat.setXYpos(merge_output.xpos(), merge_y + 80)
        final_reformat.setInput(0, merge_output)

        print(f"  Added final reformat to {image_width}x{image_height}")

        print(f"\nSuccess! Created {tile_count} tile branches.")
        print(f"Next steps:")
        print(f"  1. Find the NoOp nodes named 'MLNode_Tile_X_Y'")
        print(f"  2. Replace each NoOp with your ML node (e.g., ViTMatte)")
        print(f"  3. Connect your viewer to the Reformat_Final node")

        return {
            'status': 'success',
            'message': f'Successfully created {tile_count} tile branches ({grid_x}x{grid_y} grid)',
            'grid': (grid_x, grid_y),
            'tile_count': tile_count,
            'placeholders': placeholders,
            'output': final_reformat,
            'final_reformat': final_reformat,
        }

    except Exception as e:
        error_msg = f'Error creating tiling setup: {str(e)}'
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': error_msg,
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_tiling_setup_with_logger(input_node=None, tile_size='2K', overlap=DEFAULT_OVERLAP):
    """
    Wrapper around create_tiling_setup() that uses NukeMCPLogger for proper MCP integration.

    This version should be called when invoked via Nuke MCP bridge.

    Returns:
        dict: NukeMCPLogger formatted results
    """
    try:
        from nuke_mcp_logger import NukeMCPLogger
    except ImportError:
        # NukeMCPLogger not available, fall back to regular version
        print("Warning: NukeMCPLogger not found, using standard logging")
        return create_tiling_setup(input_node, tile_size, overlap)

    log = NukeMCPLogger(session_name="AutoTileProcessor")

    try:
        result = create_tiling_setup(input_node, tile_size, overlap)

        if result['status'] == 'success':
            log.info(f"Input format: {input_node.format().width()}x{input_node.format().height()}")
            log.info(f"Tile size: {tile_size}")
            log.info(f"Grid: {result['grid'][0]}x{result['grid'][1]}")
            log.set_stat('grid_size', f"{result['grid'][0]}x{result['grid'][1]}")
            log.set_stat('tile_count', result['tile_count'])
            log.success(result['message'])
        else:
            log.error(result['message'])

        # Return NukeMCPLogger formatted results
        logger_result = log.get_results()
        logger_result.update(result)  # Include original result data
        return logger_result

    except Exception as e:
        log.error("Tiling setup failed", e)
        return log.get_results()


# ============================================================================
# SCRIPT EXECUTION (when run directly in Nuke)
# ============================================================================

if __name__ == '__main__':
    # When executed directly in Nuke Script Editor
    result = create_tiling_setup(tile_size='2K', overlap=128)

    if result['status'] == 'success':
        print("\n" + "="*60)
        print("TILING SETUP COMPLETE")
        print("="*60)
        print(result['message'])
        print(f"\nPlaceholder nodes created: {len(result['placeholders'])}")
        print("\nReplace the Group nodes with your ML processing nodes.")
    else:
        print("\n" + "="*60)
        print("ERROR")
        print("="*60)
        print(result['message'])
