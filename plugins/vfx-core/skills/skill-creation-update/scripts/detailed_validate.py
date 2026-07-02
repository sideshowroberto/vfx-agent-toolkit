#!/usr/bin/env python3
"""Generate detailed validation report for all failing skills."""

import os
import sys
import subprocess
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    if len(sys.argv) < 2:
        print("Usage: python detailed_validate.py <skill_name>")
        print("   or: python detailed_validate.py all")
        sys.exit(1)
    
    skill_name = sys.argv[1]
    
    if skill_name == "all":
        # Get list of all failing skills
        failing_skills = [
            "agent-creation-update", "blender-addon-development", "blender-animation",
            "blender-api-compatibility", "blender-compositing", "blender-geometry-nodes",
            "blender-grease-pencil", "blender-materials-shaders", "blender-physics-simulation",
            "blender-rendering", "blender-sculpting", "brave-search", "development-management",
            "skill-creation-update", "unreal-actor-operations", "unreal-mcp-development",
            "unreal-pcg-automation", "unreal-python-scripting", "unreal-sequencer-automation",
            "unreal-vfx-automation", "vfx-documentation"
        ]
        
        print("\n" + "=" * 80)
        print("DETAILED VALIDATION REPORT - ALL FAILING SKILLS")
        print("=" * 80)
        
        for skill in failing_skills:
            print(f"\n{'=' * 80}")
            print(f"SKILL: {skill}")
            print("=" * 80)
            run_validation(skill)
    else:
        run_validation(skill_name)

def run_validation(skill_name):
    """Run validation and print full output."""
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "validate_skill.py"), skill_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
    except Exception as e:
        print(f"ERROR running validation: {e}")

if __name__ == "__main__":
    main()
