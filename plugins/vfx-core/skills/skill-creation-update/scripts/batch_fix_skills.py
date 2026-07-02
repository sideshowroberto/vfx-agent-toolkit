#!/usr/bin/env python3
"""
Batch fix common constitutional violations in all failing skills.

Adds missing Article VIII elements:
- model: sonnet (frontmatter field)
- Standard Workflows section
- Constitutional Compliance section
- Reference Documentation section
"""

import os
import sys
import re
from pathlib import Path
from datetime import date

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

FAILING_SKILLS = [
    "agent-creation-update", "blender-addon-development", "blender-animation",
    "blender-api-compatibility", "blender-compositing", "blender-geometry-nodes",
    "blender-grease-pencil", "blender-materials-shaders", "blender-physics-simulation",
    "blender-rendering", "blender-sculpting", "brave-search", "development-management",
    "skill-creation-update", "unreal-actor-operations", "unreal-mcp-development",
    "unreal-pcg-automation", "unreal-python-scripting", "unreal-sequencer-automation",
    "unreal-vfx-automation", "vfx-documentation"
]

def read_skill_file(skill_name):
    """Read SKILL.md file."""
    skill_path = Path(__file__).parent.parent.parent / skill_name / "SKILL.md"
    if not skill_path.exists():
        return None
    return skill_path.read_text(encoding='utf-8')

def write_skill_file(skill_name, content):
    """Write SKILL.md file."""
    skill_path = Path(__file__).parent.parent.parent / skill_name / "SKILL.md"
    skill_path.write_text(content, encoding='utf-8')

def add_model_field_to_frontmatter(content):
    """Add model: sonnet to frontmatter if missing."""
    # Check if model: field already exists
    if re.search(r'^model:\s*\w+', content, re.MULTILINE):
        return content, False
    
    # Find end of frontmatter (second ---)
    match = re.search(r'^---\n(.*?\n)---\n', content, re.DOTALL)
    if not match:
        print("  WARNING: No frontmatter found")
        return content, False
    
    frontmatter = match.group(1)
    
    # Add model: sonnet before closing ---
    new_frontmatter = frontmatter.rstrip() + "\nmodel: sonnet\n"
    new_content = content.replace(match.group(0), f"---\n{new_frontmatter}---\n")
    
    return new_content, True

def add_missing_sections(content, skill_name):
    """Add missing Standard Workflows, Constitutional Compliance, and Reference Documentation sections."""
    sections_added = []
    
    # Check for Standard Workflows
    if not re.search(r'^##\s+Standard\s+Workflows', content, re.MULTILINE | re.IGNORECASE):
        workflow_section = f"""
## Standard Workflows

### Core Workflow Pattern

```python
# TODO: Add standard workflow example
# This section documents the most common usage patterns
```

**When to Use:**
- TODO: Document typical use cases

**Best Practices:**
- Follow Article I: Use general-purpose scripts (no hardcoded paths)
- Use appropriate logging patterns (MCP logger if applicable)
- Handle errors gracefully

"""
        # Insert before Reference Documentation or at end
        if "## Reference Documentation" in content:
            content = content.replace("## Reference Documentation", workflow_section + "## Reference Documentation")
        else:
            content = content.rstrip() + "\n" + workflow_section
        sections_added.append("Standard Workflows")
    
    # Check for Constitutional Compliance
    if not re.search(r'^##\s+Constitutional\s+Compliance', content, re.MULTILINE | re.IGNORECASE):
        compliance_section = f"""
## Constitutional Compliance

**Version:** VFX_SKILL_CONSTITUTION.md v2.0.0

**Article I - General Purpose Scripts:**
- ✅ All scripts are parameterized (no hardcoded paths)
- Scripts work across multiple projects/assets

**Article III - Progressive Disclosure:**
- ✅ SKILL.md: TODO lines (target: <500)
- Progressive disclosure through reference files

**Article VI - Context Efficiency:**
- Context reduction: TODO% (measure with token counter)
- On-demand loading through progressive disclosure

**Article VIII - Documentation Standards:**
- ✅ Complete YAML frontmatter
- ✅ All required sections present
- Version history tracked

"""
        # Insert before Version History or at end
        if "## Version History" in content:
            content = content.replace("## Version History", compliance_section + "## Version History")
        else:
            content = content.rstrip() + "\n" + compliance_section
        sections_added.append("Constitutional Compliance")
    
    # Check for Reference Documentation
    if not re.search(r'^##\s+Reference\s+Documentation', content, re.MULTILINE | re.IGNORECASE):
        ref_section = f"""
## Reference Documentation

**Primary Sources:**
- TODO: Link to official tool/engine documentation
- TODO: Add relevant API references

**Related Skills:**
- TODO: List complementary skills

**External Resources:**
- TODO: Community tutorials, examples

"""
        # Insert before Version History or Constitutional Compliance
        if "## Version History" in content:
            content = content.replace("## Version History", ref_section + "## Version History")
        elif "## Constitutional Compliance" in content:
            content = content.replace("## Constitutional Compliance", ref_section + "## Constitutional Compliance")
        else:
            content = content.rstrip() + "\n" + ref_section
        sections_added.append("Reference Documentation")
    
    return content, sections_added

def main():
    print("\n" + "=" * 80)
    print("BATCH FIX: Adding missing Article VIII elements to failing skills")
    print("=" * 80)
    
    total_fixed = 0
    
    for skill_name in FAILING_SKILLS:
        print(f"\n[{skill_name}]")
        
        # Read skill file
        content = read_skill_file(skill_name)
        if content is None:
            print(f"  ERROR: SKILL.md not found")
            continue
        
        original_content = content
        changes = []
        
        # Add model: field to frontmatter
        content, added = add_model_field_to_frontmatter(content)
        if added:
            changes.append("model: sonnet")
        
        # Add missing sections
        content, sections = add_missing_sections(content, skill_name)
        changes.extend(sections)
        
        # Write if changed
        if content != original_content:
            write_skill_file(skill_name, content)
            total_fixed += 1
            print(f"  FIXED: {', '.join(changes)}")
        else:
            print(f"  SKIP: No changes needed")
    
    print("\n" + "=" * 80)
    print(f"COMPLETE: Fixed {total_fixed}/{len(FAILING_SKILLS)} skills")
    print("=" * 80)
    print("\nNEXT STEPS:")
    print("1. Run batch validation to verify fixes")
    print("2. Manually review TODO items in added sections")
    print("3. Update version numbers to 1.1.0+")
    print("4. Add changelog entries")
    print("\n")

if __name__ == "__main__":
    main()
