#!/usr/bin/env python3
"""
Create new VFX Agent Skill from template with constitutional compliance.

Purpose: Automate skill scaffolding from VFX_SKILL_TEMPLATE.md
Article I: Works for ALL skill types (parameterized, no hard-coded names)
Article III: Generates compliant structure (<500 lines)
Article VIII: Applies documentation standards

Usage:
    python create_skill.py SKILL_NAME \
        --description "What + When + Triggers" \
        --triggers "trigger1,trigger2,trigger3" \
        --dependencies "Software 1,Software 2" \
        --model sonnet

Author: VFX Skill System
Version: 1.0.0
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def validate_skill_name(name: str) -> bool:
    """
    Validate skill name follows naming conventions.

    Requirements:
    - Lowercase only
    - Hyphens allowed (word separators)
    - No spaces, underscores, or special characters
    - Length: 3-50 characters

    Args:
        name: Skill name to validate

    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False

    # Check length
    if len(name) < 3 or len(name) > 50:
        return False

    # Check characters (lowercase, hyphens only)
    allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if not all(c in allowed_chars for c in name):
        return False

    # Must not start or end with hyphen
    if name.startswith("-") or name.endswith("-"):
        return False

    return True


def find_template_path() -> Optional[Path]:
    """
    Locate VFX_SKILL_TEMPLATE.md in ClaudeCode/templates/.

    Searches relative to script location and common locations.

    Returns:
        Path to template if found, None otherwise
    """
    # Get script directory
    script_dir = Path(__file__).parent.absolute()

    # Search paths (relative to script location)
    search_paths = [
        # From .claude/skills/skill-creation-update/scripts/ -> ClaudeCode/templates/
        script_dir.parent.parent.parent.parent / "ClaudeCode" / "templates" / "VFX_SKILL_TEMPLATE.md",
        # Fallback: assume ClaudeCode is sibling to .claude
        script_dir.parent.parent.parent / "ClaudeCode" / "templates" / "VFX_SKILL_TEMPLATE.md",
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def create_skill_directory(skill_name: str, base_path: Optional[Path] = None) -> Path:
    """
    Create skill directory structure.

    Structure:
        .claude/skills/{skill_name}/
        |-- SKILL.md
        |-- reference/
        `-- scripts/

    Args:
        skill_name: Name of skill to create
        base_path: Base path for .claude/skills/ (default: auto-detect)

    Returns:
        Path to created skill directory

    Raises:
        FileExistsError: If skill directory already exists
    """
    if base_path is None:
        # Auto-detect: script is in .claude/skills/skill-creation-update/scripts/
        script_dir = Path(__file__).parent.absolute()
        base_path = script_dir.parent.parent

    skill_dir = base_path / skill_name

    # Check if already exists
    if skill_dir.exists():
        raise FileExistsError(f"Skill '{skill_name}' already exists at {skill_dir}")

    # Create directories
    skill_dir.mkdir(parents=True, exist_ok=False)
    (skill_dir / "reference").mkdir(exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)

    return skill_dir


def apply_template(
    template_path: Path,
    output_path: Path,
    skill_name: str,
    description: str,
    triggers: list[str],
    dependencies: str,
    model: str
) -> None:
    """
    Apply template with placeholder replacement.

    Placeholders:
        {{SKILL_NAME}} -> skill_name
        {{DESCRIPTION}} -> description
        {{DATE}} -> current date (YYYY-MM-DD)
        {{LIST_ALL_REQUIRED_SOFTWARE}} -> dependencies

    Args:
        template_path: Path to VFX_SKILL_TEMPLATE.md
        output_path: Path to output SKILL.md
        skill_name: Name of skill
        description: Skill description
        triggers: List of trigger phrases
        dependencies: Comma-separated dependencies
        model: Model preference (sonnet/haiku)
    """
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Prepare replacements
    current_date = datetime.now().strftime("%Y-%m-%d")
    triggers_yaml = "\n".join(f'  - "{trigger.strip()}"' for trigger in triggers)

    # Replace placeholders
    replacements = {
        "{{SKILL_NAME}}": skill_name,
        "{{DESCRIPTION}}": description,
        "{{DATE}}": current_date,
        "{{LIST_ALL_REQUIRED_SOFTWARE}}": dependencies,
    }

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    # Handle YAML frontmatter (first 4 lines)
    lines = content.split('\n')
    if lines[0] == '---' and '{{SKILL_NAME}}' not in lines[1]:
        # Already replaced, now update triggers
        # Find description line and add triggers after it
        for i, line in enumerate(lines):
            if line.startswith('description:'):
                # Insert triggers after description
                lines.insert(i + 1, f"triggers:\n{triggers_yaml}")
                lines.insert(i + 2, f"model: {model}")
                break
        content = '\n'.join(lines)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def create_placeholder_references(skill_dir: Path, skill_name: str) -> None:
    """
    Create placeholder reference documentation files.

    Args:
        skill_dir: Skill directory path
        skill_name: Name of skill
    """
    reference_dir = skill_dir / "reference"

    # Template guide placeholder
    template_guide = reference_dir / "detailed_workflow.md"
    with open(template_guide, 'w', encoding='utf-8') as f:
        f.write(f"# {skill_name.replace('-', ' ').title()} - Detailed Workflows\n\n")
        f.write("**Purpose:** Comprehensive workflow documentation for complex scenarios.\n\n")
        f.write("## Advanced Workflows\n\n")
        f.write("(To be filled in with detailed step-by-step instructions)\n\n")
        f.write("## Edge Cases\n\n")
        f.write("(Document unusual scenarios and solutions)\n\n")
        f.write("## Performance Optimization\n\n")
        f.write("(Best practices for large-scale operations)\n")

    # Troubleshooting guide placeholder
    troubleshooting = reference_dir / "troubleshooting_guide.md"
    with open(troubleshooting, 'w', encoding='utf-8') as f:
        f.write(f"# {skill_name.replace('-', ' ').title()} - Troubleshooting Guide\n\n")
        f.write("**Purpose:** Comprehensive error catalog and solutions.\n\n")
        f.write("## Common Errors\n\n")
        f.write("(Catalog of errors with solutions)\n\n")
        f.write("## Debugging Strategies\n\n")
        f.write("(How to diagnose issues)\n\n")
        f.write("## Known Limitations\n\n")
        f.write("(Document tool/version-specific issues)\n")


def main() -> int:
    """
    Main entry point for skill creation.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    parser = argparse.ArgumentParser(
        description="Create new VFX Agent Skill from template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Create Houdini HDA export skill
    python create_skill.py houdini-hda-export \\
        --description "Export Houdini Digital Assets for Unreal Engine" \\
        --triggers "hda export,houdini to unreal,digital asset" \\
        --dependencies "Houdini 20+,Unreal Engine 5.5+" \\
        --model sonnet

    # Create Blender FBX workflow skill
    python create_skill.py blender-fbx-workflow \\
        --description "Batch export Blender models to FBX for game engines" \\
        --triggers "blender export,fbx batch,game export" \\
        --dependencies "Blender 4.2+,Python 3.12+" \\
        --model haiku
        """
    )

    parser.add_argument("name", help="Skill name (lowercase, hyphens only)")
    parser.add_argument("--description", required=True,
                        help="Skill description (What + When + Triggers)")
    parser.add_argument("--triggers", required=True,
                        help="Comma-separated trigger phrases")
    parser.add_argument("--dependencies", default="None",
                        help="Comma-separated dependencies (default: None)")
    parser.add_argument("--model", choices=["sonnet", "haiku"], default="sonnet",
                        help="Model preference (default: sonnet)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate inputs without creating files")

    args = parser.parse_args()

    # Validate skill name
    if not validate_skill_name(args.name):
        print(f"[FAIL] Invalid skill name: '{args.name}'")
        print("\nRequirements:")
        print("  - Lowercase only")
        print("  - Hyphens allowed (word separators)")
        print("  - No spaces, underscores, or special characters")
        print("  - Length: 3-50 characters")
        print("\nExamples:")
        print("  [OK] houdini-hda-export")
        print("  [OK] unreal-vfx-automation")
        print("  [FAIL] Houdini_Export (uppercase, underscore)")
        print("  [FAIL] hda export (space)")
        return 1

    # Parse triggers
    triggers = [t.strip() for t in args.triggers.split(',') if t.strip()]
    if len(triggers) < 2:
        print("[FAIL] At least 2 trigger phrases required")
        print(f"   Provided: {len(triggers)} trigger(s)")
        return 1

    # Dry run exit
    if args.dry_run:
        print(f"[OK] Dry run successful for skill: {args.name}")
        print(f"   Description: {args.description}")
        print(f"   Triggers: {', '.join(triggers)}")
        print(f"   Dependencies: {args.dependencies}")
        print(f"   Model: {args.model}")
        return 0

    # Find template
    template_path = find_template_path()
    if not template_path:
        print("[FAIL] Template not found: VFX_SKILL_TEMPLATE.md")
        print("\nSearched paths:")
        script_dir = Path(__file__).parent.absolute()
        print(f"  - {script_dir.parent.parent.parent.parent / 'ClaudeCode' / 'templates' / 'VFX_SKILL_TEMPLATE.md'}")
        print("\nPlease ensure ClaudeCode/templates/VFX_SKILL_TEMPLATE.md exists")
        return 1

    try:
        # Create skill directory
        skill_dir = create_skill_directory(args.name)
        print(f"[OK] Created {skill_dir}/")

        # Apply template
        skill_md = skill_dir / "SKILL.md"
        apply_template(
            template_path,
            skill_md,
            args.name,
            args.description,
            triggers,
            args.dependencies,
            args.model
        )

        # Count lines in generated SKILL.md
        with open(skill_md, 'r', encoding='utf-8') as f:
            line_count = len(f.readlines())

        print(f"[OK] Created SKILL.md ({line_count} lines from template)")

        # Create reference placeholders
        create_placeholder_references(skill_dir, args.name)
        print("[OK] Created reference/ directory with placeholders")

        print("[OK] Created scripts/ directory")

        # Success summary
        print(f"\nSkill '{args.name}' created successfully!")
        print(f"\n-> Next Steps:")
        print(f"   1. Fill in Quick Start section in SKILL.md")
        print(f"   2. Add 3-5 Standard Workflows")
        print(f"   3. Document 4-5 common issues in Troubleshooting")
        print(f"   4. Move detailed content to reference/*.md if needed")
        print(f"   5. Validate compliance: python validate_skill.py {args.name}")
        print(f"\nLocation: {skill_dir.absolute()}")

        return 0

    except FileExistsError as e:
        print(f"[FAIL] {e}")
        print(f"\nOptions:")
        print(f"   1. Delete existing skill: rm -rf .claude/skills/{args.name}")
        print(f"   2. Update existing skill: python update_skill.py {args.name} --version X.Y.Z")
        return 1

    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
