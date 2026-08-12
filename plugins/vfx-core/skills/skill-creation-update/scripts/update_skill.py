#!/usr/bin/env python3
"""
Update VFX Agent Skill version and changelog with semantic versioning.

Purpose: Automate skill version management and documentation updates
Article VIII: Maintains semantic versioning (X.Y.Z)
Updates: SKILL.md version, Last Updated date, Version History

Usage:
    # Minor update
    python update_skill.py SKILL_NAME --version 1.1.0 --changes "Added feature X"

    # Major update (breaking)
    python update_skill.py SKILL_NAME --version 2.0.0 \\
        --changes "BREAKING: Removed UE 4.27 support" --breaking

Author: VFX Skill System
Version: 1.0.0
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


def parse_version(version: str) -> Optional[Tuple[int, int, int]]:
    """
    Parse semantic version string.

    Args:
        version: Version string (e.g., "1.2.3")

    Returns:
        Tuple of (major, minor, patch) or None if invalid
    """
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
    if not match:
        return None

    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def compare_versions(old: Tuple[int, int, int], new: Tuple[int, int, int]) -> str:
    """
    Compare two semantic versions.

    Args:
        old: Old version tuple (major, minor, patch)
        new: New version tuple (major, minor, patch)

    Returns:
        "major", "minor", "patch", "same", or "downgrade"
    """
    if new < old:
        return "downgrade"
    if new == old:
        return "same"

    old_major, old_minor, old_patch = old
    new_major, new_minor, new_patch = new

    if new_major > old_major:
        return "major"
    if new_minor > old_minor:
        return "minor"
    if new_patch > old_patch:
        return "patch"

    return "unknown"


def extract_current_version(content: str) -> Optional[str]:
    """
    Extract current version from SKILL.md.

    Searches:
    1. YAML frontmatter: version: X.Y.Z
    2. Version section: **Version:** X.Y.Z
    3. Version History: **vX.Y.Z**

    Args:
        content: SKILL.md content

    Returns:
        Version string or None if not found
    """
    # Try YAML frontmatter
    frontmatter_match = re.search(r'version:\s*["\']?(\d+\.\d+\.\d+)["\']?', content, re.IGNORECASE)
    if frontmatter_match:
        return frontmatter_match.group(1)

    # Try Version section
    version_match = re.search(r'\*\*(?:Skill )?Version:\*\*\s*(\d+\.\d+\.\d+)', content, re.IGNORECASE)
    if version_match:
        return version_match.group(1)

    # Try Version History (first entry)
    history_match = re.search(r'\*\*v(\d+\.\d+\.\d+)\*\*', content)
    if history_match:
        return history_match.group(1)

    return None


def update_version_in_content(content: str, new_version: str) -> str:
    """
    Update version in SKILL.md content.

    Updates:
    1. YAML frontmatter
    2. Version section
    3. Preserves Version History (updated separately)

    Args:
        content: Original SKILL.md content
        new_version: New version string

    Returns:
        Updated content
    """
    # Update YAML frontmatter (if present)
    content = re.sub(
        r'(version:\s*)["\']?\d+\.\d+\.\d+["\']?',
        f'version: {new_version}',
        content,
        flags=re.IGNORECASE
    )

    # Update Version section
    content = re.sub(
        r'(\*\*(?:Skill )?Version:\*\*\s*)\d+\.\d+\.\d+',
        f'\\1{new_version}',
        content,
        flags=re.IGNORECASE
    )

    return content


def update_last_updated(content: str) -> str:
    """
    Update "Last Updated" date to current date.

    Args:
        content: SKILL.md content

    Returns:
        Updated content
    """
    current_date = datetime.now().strftime("%Y-%m-%d")

    content = re.sub(
        r'(\*\*Last Updated:\*\*\s*)\d{4}-\d{2}-\d{2}',
        f'\\1{current_date}',
        content,
        flags=re.IGNORECASE
    )

    return content


def add_changelog_entry(
    content: str,
    version: str,
    changes: str,
    is_breaking: bool = False
) -> str:
    """
    Add changelog entry to Version History section.

    Format:
        **vX.Y.Z** (YYYY-MM-DD) - Title
        - Change 1
        - Change 2

    Args:
        content: SKILL.md content
        version: Version string
        changes: Change description (can be multiline)
        is_breaking: Whether this is a breaking change

    Returns:
        Updated content
    """
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Parse changes (split by newline, filter empty)
    change_lines = [line.strip() for line in changes.split('\n') if line.strip()]

    # Generate title from first change
    title = change_lines[0] if change_lines else "Update"
    if is_breaking and not title.startswith("BREAKING"):
        title = f"BREAKING: {title}"

    # Build changelog entry
    entry_lines = [f"**v{version}** ({current_date}) - {title}"]
    for change in change_lines:
        if not change.startswith("-"):
            entry_lines.append(f"- {change}")
        else:
            entry_lines.append(change)

    entry = "\n".join(entry_lines)

    # Find Version History section
    version_history_pattern = r'(## Version History\s*\n)'

    if re.search(version_history_pattern, content, re.IGNORECASE):
        # Add entry after section header
        content = re.sub(
            version_history_pattern,
            f'\\1\n{entry}\n',
            content,
            flags=re.IGNORECASE
        )
    else:
        # No Version History section - add at end
        if not content.endswith('\n'):
            content += '\n'
        content += f"\n## Version History\n\n{entry}\n"

    return content


class SkillUpdater:
    """Updates VFX Agent Skill version and documentation."""

    def __init__(self, skill_name: str, skill_path: Optional[Path] = None):
        """
        Initialize updater.

        Args:
            skill_name: Name of skill to update
            skill_path: Path to .claude/skills/ (auto-detect if None)
        """
        self.skill_name = skill_name

        if skill_path is None:
            # Auto-detect from script location
            script_dir = Path(__file__).parent.absolute()
            skill_path = script_dir.parent.parent

        self.skill_dir = skill_path / skill_name
        self.skill_md = self.skill_dir / "SKILL.md"

    def update(
        self,
        new_version: str,
        changes: str,
        is_breaking: bool = False,
        dry_run: bool = False
    ) -> bool:
        """
        Update skill version and changelog.

        Args:
            new_version: New version string (X.Y.Z)
            changes: Change description
            is_breaking: Whether this is a breaking change
            dry_run: Preview changes without writing

        Returns:
            True if update successful, False otherwise
        """
        # Verify skill exists
        if not self.skill_md.exists():
            print(f"[FAIL] SKILL.md not found: {self.skill_md}")
            return False

        # Validate new version format
        new_ver_tuple = parse_version(new_version)
        if not new_ver_tuple:
            print(f"[FAIL] Invalid version format: {new_version}")
            print("   Must be semantic version (X.Y.Z)")
            print("   Examples: 1.0.0, 1.1.0, 2.0.0")
            return False

        # Read current content
        with open(self.skill_md, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Extract current version
        current_version = extract_current_version(original_content)
        if not current_version:
            print("[WARN] Warning: Could not detect current version")
            print("   Proceeding with version update...")
        else:
            current_ver_tuple = parse_version(current_version)
            if current_ver_tuple:
                change_type = compare_versions(current_ver_tuple, new_ver_tuple)

                if change_type == "downgrade":
                    print(f"[FAIL] Version downgrade not allowed")
                    print(f"   Current: {current_version} -> New: {new_version}")
                    return False
                elif change_type == "same":
                    print(f"[WARN] Warning: Version unchanged ({new_version})")
                    print("   Continuing with changelog update...")

        # Update content
        updated_content = original_content
        updated_content = update_version_in_content(updated_content, new_version)
        updated_content = update_last_updated(updated_content)
        updated_content = add_changelog_entry(
            updated_content,
            new_version,
            changes,
            is_breaking
        )

        # Dry run - show diff
        if dry_run:
            print(f"Dry Run: {self.skill_name}\n")
            print(f"Previous version: {current_version or 'unknown'}")
            print(f"New version: {new_version}")
            print(f"Change type: {change_type if current_version else 'initial'}")
            print("\nChanges to be applied:")
            print("  [OK] Update version in SKILL.md")
            print("  [OK] Update 'Last Updated' date")
            print("  [OK] Add changelog entry")
            print("\nChangelog entry:")
            current_date = datetime.now().strftime("%Y-%m-%d")
            change_lines = [line.strip() for line in changes.split('\n') if line.strip()]
            title = change_lines[0] if change_lines else "Update"
            if is_breaking and not title.startswith("BREAKING"):
                title = f"BREAKING: {title}"
            print(f"  **v{new_version}** ({current_date}) - {title}")
            for change in change_lines:
                if not change.startswith("-"):
                    print(f"  - {change}")
                else:
                    print(f"  {change}")
            return True

        # Write updated content
        with open(self.skill_md, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        # Print summary
        print(f"Updating {self.skill_name}\n")
        print(f"Previous version: {current_version or 'unknown'}")
        print(f"New version: {new_version}")

        if current_version:
            change_type = compare_versions(
                parse_version(current_version),
                parse_version(new_version)
            )
            change_type_desc = {
                "major": "Major (breaking changes expected)",
                "minor": "Minor (backward compatible)",
                "patch": "Patch (bug fixes)"
            }.get(change_type, "Unknown")
            print(f"Change type: {change_type_desc}")

        print()
        print("[OK] Updated version in SKILL.md")
        print(f"[OK] Updated 'Last Updated' to {datetime.now().strftime('%Y-%m-%d')}")
        print("[OK] Added changelog entry")

        # Re-validate compliance
        print("\nRe-validating constitutional compliance...")
        script_dir = Path(__file__).parent
        validate_script = script_dir / "validate_skill.py"

        if validate_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(validate_script), self.skill_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("[OK] Re-validated constitutional compliance")
                else:
                    print("[WARN] Compliance validation warnings (see output above)")
            except Exception as e:
                print(f"[WARN] Could not run validation: {e}")
        else:
            print("[WARN] Validation script not found - skipping")

        # Show changelog entry
        print("\nChangelog entry added:")
        current_date = datetime.now().strftime("%Y-%m-%d")
        change_lines = [line.strip() for line in changes.split('\n') if line.strip()]
        title = change_lines[0] if change_lines else "Update"
        if is_breaking and not title.startswith("BREAKING"):
            title = f"BREAKING: {title}"
        print(f"**v{new_version}** ({current_date}) - {title}")
        for change in change_lines:
            if not change.startswith("-"):
                print(f"- {change}")
            else:
                print(change)

        print(f"\n-> Next: Test with production workflow")
        return True


def main() -> int:
    """
    Main entry point for skill updating.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    parser = argparse.ArgumentParser(
        description="Update VFX Agent Skill version and changelog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Minor update (new feature, backward compatible)
    python update_skill.py unreal-vfx-automation \\
        --version 1.1.0 \\
        --changes "Added Sequencer integration support"

    # Patch update (bug fix)
    python update_skill.py houdini-hda-export \\
        --version 1.0.1 \\
        --changes "Fixed: Material export for Unreal 5.5"

    # Major update (breaking change)
    python update_skill.py blender-fbx-workflow \\
        --version 2.0.0 \\
        --changes "BREAKING: Removed Blender 3.x support\\nNow requires Blender 4.2+" \\
        --breaking

    # Dry run (preview changes)
    python update_skill.py my-skill \\
        --version 1.1.0 \\
        --changes "Test update" \\
        --dry-run
        """
    )

    parser.add_argument("name", help="Skill name to update")
    parser.add_argument("--version", required=True,
                        help="New version (semantic: X.Y.Z)")
    parser.add_argument("--changes", required=True,
                        help="Change description (can include \\n for multiple lines)")
    parser.add_argument("--breaking", action="store_true",
                        help="Mark as breaking change (major version)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing")
    parser.add_argument("--skills-path", type=Path,
                        help="Path to .claude/skills directory (auto-detect if not provided)")

    args = parser.parse_args()

    # Create updater
    updater = SkillUpdater(args.name, args.skills_path)

    # Run update
    success = updater.update(
        args.version,
        args.changes,
        args.breaking,
        args.dry_run
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
