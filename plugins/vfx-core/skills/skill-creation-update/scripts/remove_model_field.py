#!/usr/bin/env python3
"""
Remove incorrect 'model:' field from skill frontmatter.

The model: field is for agents only, not skills.
Correct skill frontmatter is only: name, description, (optional: allowed-tools)
"""

import re
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ALL_SKILLS = [
    "agent-creation-update", "blender-addon-development", "blender-animation",
    "blender-api-compatibility", "blender-compositing", "blender-geometry-nodes",
    "blender-grease-pencil", "blender-materials-shaders", "blender-physics-simulation",
    "blender-rendering", "blender-sculpting", "brave-search", "development-management",
    "nuke-compositing", "nuke-python-scripting", "skill-creation-update",
    "unreal-actor-operations", "unreal-blueprint-automation", "unreal-mcp-development",
    "unreal-pcg-automation", "unreal-python-scripting", "unreal-sequencer-automation",
    "unreal-vfx-automation", "vfx-documentation"
]

def remove_model_field(skill_name):
    """Remove model: field from skill frontmatter."""
    skill_path = Path(__file__).parent.parent.parent / skill_name / "SKILL.md"
    
    if not skill_path.exists():
        print(f"  ERROR: SKILL.md not found")
        return False
    
    content = skill_path.read_text(encoding='utf-8')
    
    # Check if model: field exists
    if not re.search(r'^model:\s*\w+', content, re.MULTILINE):
        return False  # No change needed
    
    # Remove the model: line from frontmatter
    # Pattern: optional whitespace + model: + value + newline
    new_content = re.sub(r'^model:\s*\w+\s*\n', '', content, flags=re.MULTILINE)
    
    # Write back
    skill_path.write_text(new_content, encoding='utf-8')
    return True

def main():
    print("\n" + "=" * 80)
    print("REMOVING INCORRECT 'model:' FIELD FROM SKILLS")
    print("=" * 80)
    print("\nOfficial Anthropic skill frontmatter:")
    print("  - name: (required)")
    print("  - description: (required)")
    print("  - allowed-tools: (optional)")
    print("\nThe 'model:' field is for AGENTS only, not skills.")
    print("\n" + "=" * 80)
    
    fixed_count = 0
    
    for skill_name in ALL_SKILLS:
        print(f"\n[{skill_name}]", end=" ")
        
        if remove_model_field(skill_name):
            print("FIXED - Removed model: field")
            fixed_count += 1
        else:
            print("SKIP - No model: field found")
    
    print("\n" + "=" * 80)
    print(f"COMPLETE: Fixed {fixed_count}/{len(ALL_SKILLS)} skills")
    print("=" * 80)
    print("\nNEXT: Run batch_validate.py to verify")

if __name__ == "__main__":
    main()
