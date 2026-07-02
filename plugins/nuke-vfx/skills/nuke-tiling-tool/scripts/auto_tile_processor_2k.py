"""
Automated Image Tiling Tool for Nuke ML Processing - 2K Tiles

Creates a tiling setup with 2048x2048 tiles for processing large images
through ML nodes (like ViTMatte) with seamless gradient blending.

Usage:
    - Select a Read node (or any image node)
    - Run this script
    - Replace NoOp placeholders with your ML nodes
    - Connect viewer to Reformat_Final

Author: Claude Code
Version: 1.0.0
Created: 2026-01-21
"""

import sys
import os

# Add the scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from auto_tile_processor import create_tiling_setup

# Run with 2K tile size
result = create_tiling_setup(tile_size='2K', overlap=128)

if result['status'] == 'success':
    print("\n" + "="*60)
    print("2K TILING SETUP COMPLETE")
    print("="*60)
    print(result['message'])
    print(f"\nCreated {result['tile_count']} tiles (2048x2048 each)")
    print(f"Grid: {result['grid'][0]}x{result['grid'][1]}")
    print("\nNext steps:")
    print("  1. Replace orange NoOp nodes with your ML nodes")
    print("  2. Connect viewer to Reformat_Final node")
else:
    print("\n" + "="*60)
    print("ERROR")
    print("="*60)
    print(result['message'])
