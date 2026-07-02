#!/usr/bin/env python3
"""
Purpose: Update existing agent files with version increment and changelog
Usage: python update_agent.py <agent_name> <increment> [--changelog <text>] [--no-archive] [--agents-dir <path>]

Version Increment Types:
- major: 1.2.3 -> 2.0.0 (breaking changes)
- minor: 1.2.3 -> 1.3.0 (new features)
- patch: 1.2.3 -> 1.2.4 (bug fixes)

Workflow:
1. Archive current version (optional)
2. Read agent file and parse current version
3. Increment version based on type
4. Update YAML metadata (version, last_updated)
5. Add changelog entry to Version History section
6. Validate updated agent
7. Save if validation passes, rollback if fails

Constitutional Reference:
- <workspace>\ClaudeCode\development\VFX_SKILL_CONSTITUTION.md
- Article IX: Agent Versioning and Naming Conventions
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


# ============================================================================
# Version Increment Logic
# ============================================================================

def increment_version(current: str, increment_type: str) -> str:
    """
    Increment semantic version.

    Args:
        current: Current version (e.g., "1.2.3")
        increment_type: "major", "minor", or "patch"

    Returns:
        New version string

    Examples:
        increment_version("1.2.3", "major") -> "2.0.0"
        increment_version("1.2.3", "minor") -> "1.3.0"
        increment_version("1.2.3", "patch") -> "1.2.4"

    Raises:
        ValueError: If version format is invalid or increment_type is not recognized
    """
    try:
        major, minor, patch = map(int, current.split('.'))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid version format: {current}. Expected X.Y.Z format (e.g., 1.2.3)")

    if increment_type == 'major':
        return f"{major + 1}.0.0"
    elif increment_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif increment_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid increment type: {increment_type}. Must be major, minor, or patch")


# ============================================================================
# YAML Frontmatter Parsing and Updating
# ============================================================================

def parse_frontmatter(agent_content: str) -> Tuple[str, Dict[str, str], str]:
    """
    Parse YAML frontmatter from agent content.

    Args:
        agent_content: Full text content of agent file

    Returns:
        Tuple of (frontmatter_text, metadata_dict, body_content)

    Raises:
        ValueError: If frontmatter is not found or invalid
    """
    # Extract YAML frontmatter
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.search(frontmatter_pattern, agent_content, re.DOTALL)

    if not match:
        raise ValueError("No YAML frontmatter found (must start with ---)")

    frontmatter_text = match.group(1)
    body_content = match.group(2)

    # Parse YAML manually (simple key: value parsing)
    metadata = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    return frontmatter_text, metadata, body_content


def update_frontmatter(frontmatter_text: str, metadata: Dict[str, str],
                       new_version: str, today: str) -> str:
    """
    Update YAML frontmatter with new version and date.

    Args:
        frontmatter_text: Original frontmatter text
        metadata: Parsed metadata dict
        new_version: New version string (e.g., "2.0.0")
        today: Today's date in YYYY-MM-DD format

    Returns:
        Updated frontmatter text
    """
    # Update version line
    frontmatter_text = re.sub(
        r'version:\s*[\d\.]+',
        f'version: {new_version}',
        frontmatter_text
    )

    # Update last_updated line
    frontmatter_text = re.sub(
        r'last_updated:\s*[\d\-]+',
        f'last_updated: {today}',
        frontmatter_text
    )

    return frontmatter_text


# ============================================================================
# Changelog Management
# ============================================================================

def parse_changelog_title(changelog: str) -> str:
    """
    Extract title from first line of changelog.

    Args:
        changelog: Changelog text (may be multi-line)

    Returns:
        First line as title (truncated to 80 chars if needed)
    """
    lines = [line.strip() for line in changelog.split('\n') if line.strip()]
    if not lines:
        return "Update"

    title = lines[0]
    # Remove leading dash if present
    if title.startswith('- '):
        title = title[2:]

    # Truncate if too long
    if len(title) > 80:
        title = title[:77] + "..."

    return title


def format_changelog_entry(changelog: str, version: str, today: str) -> str:
    """
    Format changelog text into version history entry.

    Args:
        changelog: Raw changelog text (lines separated by newlines)
        version: Version string (e.g., "2.0.0")
        today: Date string (YYYY-MM-DD)

    Returns:
        Formatted changelog entry

    Example:
        Input: "Added new feature\nFixed bug\nImproved performance"
        Output:
        **v2.0.0** (2025-10-25) - Added new feature
        - Added new feature
        - Fixed bug
        - Improved performance
    """
    lines = [line.strip() for line in changelog.split('\n') if line.strip()]

    if not lines:
        raise ValueError("Changelog cannot be empty")

    # Extract title from first line
    title = parse_changelog_title(changelog)

    # Format entry header
    entry = f"**v{version}** ({today}) - {title}\n"

    # Add changelog items as bullets
    for line in lines:
        # Ensure each line starts with a dash
        if not line.startswith('- '):
            line = f"- {line}"
        entry += f"{line}\n"

    return entry


def insert_changelog_entry(body_content: str, changelog_entry: str) -> str:
    """
    Insert changelog entry into Version History section.

    Args:
        body_content: Agent body content (everything after frontmatter)
        changelog_entry: Formatted changelog entry to insert

    Returns:
        Updated body content with new changelog entry

    Raises:
        ValueError: If Version History section not found
    """
    # Find Version History section
    version_history_pattern = r'(##\s+Version\s+History\s*\n\s*\n)'
    match = re.search(version_history_pattern, body_content, re.IGNORECASE)

    if not match:
        # If no Version History section exists, create it at the end
        body_content += "\n## Version History\n\n"
        body_content += changelog_entry + "\n"
        return body_content

    # Insert new entry after the header
    insert_pos = match.end()
    updated_body = (
        body_content[:insert_pos] +
        changelog_entry + "\n" +
        body_content[insert_pos:]
    )

    return updated_body


# ============================================================================
# Archive Integration
# ============================================================================

def archive_current_version(agent_name: str, agents_dir: str, script_dir: str) -> Optional[str]:
    """
    Archive current version of agent using archive_agent.py.

    Args:
        agent_name: Agent name (without .md)
        agents_dir: Agents directory path
        script_dir: Directory containing scripts

    Returns:
        Archive file path if successful, None if failed
    """
    agent_path = os.path.join(agents_dir, f"{agent_name}.md")
    archive_script = os.path.join(script_dir, "archive_agent.py")

    # Check if archive script exists
    if not os.path.exists(archive_script):
        print(f"Warning: Archive script not found at {archive_script}")
        print("Skipping archiving (continuing with update)")
        return None

    # Run archive script
    try:
        # For now, we'll implement basic archiving inline since archive_agent.py
        # might not be fully implemented. We'll create a simple version backup.
        archive_dir = os.path.join(agents_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        # Read current agent to get version
        with open(agent_path, 'r', encoding='utf-8') as f:
            content = f.read()

        _, metadata, _ = parse_frontmatter(content)
        current_version = metadata.get('version', '0.0.0')

        # Create archive filename
        archive_filename = f"{agent_name}-v{current_version}.md"
        archive_path = os.path.join(archive_dir, archive_filename)

        # Copy to archive
        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return archive_path

    except Exception as e:
        print(f"Warning: Failed to archive agent: {e}")
        print("Continuing with update")
        return None


# ============================================================================
# Validation Integration
# ============================================================================

def validate_updated_agent(agent_name: str, agents_dir: str, script_dir: str) -> bool:
    """
    Validate updated agent using validate_agent.py.

    Args:
        agent_name: Agent name (without .md)
        agents_dir: Agents directory path
        script_dir: Directory containing scripts

    Returns:
        True if validation passed, False otherwise
    """
    validate_script = os.path.join(script_dir, "validate_agent.py")

    if not os.path.exists(validate_script):
        print(f"Warning: Validation script not found at {validate_script}")
        print("Skipping validation (continuing anyway)")
        return True

    try:
        # Run validation script
        result = subprocess.run(
            [sys.executable, validate_script, agent_name, "--agents-dir", agents_dir],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True
        else:
            print("\nValidation failed:")
            print(result.stdout)
            return False

    except Exception as e:
        print(f"Warning: Validation check failed: {e}")
        print("Continuing anyway")
        return True


# ============================================================================
# Main Update Function
# ============================================================================

def update_agent(agent_name: str, increment: str, changelog: str,
                archive_old: bool = True, agents_dir: str = ".claude/agents") -> Dict[str, Any]:
    """
    Update agent with version increment and changelog.

    Args:
        agent_name: Agent name (without .md extension)
        increment: Version increment type ("major", "minor", or "patch")
        changelog: Changelog text (newline-separated items)
        archive_old: Whether to archive old version before updating
        agents_dir: Path to agents directory

    Returns:
        dict: {
            "success": bool,
            "old_version": str,
            "new_version": str,
            "archive_path": str or None,
            "message": str
        }
    """
    # Resolve paths
    agents_dir = os.path.abspath(agents_dir)
    agent_path = os.path.join(agents_dir, f"{agent_name}.md")
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if agent exists
    if not os.path.exists(agent_path):
        return {
            "success": False,
            "old_version": "unknown",
            "new_version": "unknown",
            "archive_path": None,
            "message": f"Agent not found: {agent_path}"
        }

    # Read agent file
    try:
        with open(agent_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        return {
            "success": False,
            "old_version": "unknown",
            "new_version": "unknown",
            "archive_path": None,
            "message": f"Error reading agent file: {e}"
        }

    # Archive current version (if requested)
    archive_path = None
    if archive_old:
        archive_path = archive_current_version(agent_name, agents_dir, script_dir)

    # Parse frontmatter and body
    try:
        frontmatter_text, metadata, body_content = parse_frontmatter(original_content)
    except ValueError as e:
        return {
            "success": False,
            "old_version": "unknown",
            "new_version": "unknown",
            "archive_path": archive_path,
            "message": f"Error parsing agent file: {e}"
        }

    # Get current version
    if 'version' not in metadata:
        return {
            "success": False,
            "old_version": "unknown",
            "new_version": "unknown",
            "archive_path": archive_path,
            "message": "No version field found in metadata"
        }

    old_version = metadata['version']

    # Increment version
    try:
        new_version = increment_version(old_version, increment)
    except ValueError as e:
        return {
            "success": False,
            "old_version": old_version,
            "new_version": "unknown",
            "archive_path": archive_path,
            "message": str(e)
        }

    # Update frontmatter
    today = date.today().strftime('%Y-%m-%d')
    updated_frontmatter = update_frontmatter(frontmatter_text, metadata, new_version, today)

    # Format and insert changelog entry
    try:
        changelog_entry = format_changelog_entry(changelog, new_version, today)
        updated_body = insert_changelog_entry(body_content, changelog_entry)
    except ValueError as e:
        return {
            "success": False,
            "old_version": old_version,
            "new_version": new_version,
            "archive_path": archive_path,
            "message": f"Error formatting changelog: {e}"
        }

    # Construct updated content
    updated_content = f"---\n{updated_frontmatter}\n---\n{updated_body}"

    # Write updated content to file
    try:
        with open(agent_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    except Exception as e:
        return {
            "success": False,
            "old_version": old_version,
            "new_version": new_version,
            "archive_path": archive_path,
            "message": f"Error writing updated file: {e}"
        }

    # Validate updated agent
    validation_passed = validate_updated_agent(agent_name, agents_dir, script_dir)

    if not validation_passed:
        # Rollback to original content
        try:
            with open(agent_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        except Exception as e:
            return {
                "success": False,
                "old_version": old_version,
                "new_version": new_version,
                "archive_path": archive_path,
                "message": f"Validation failed and rollback also failed: {e}"
            }

        return {
            "success": False,
            "old_version": old_version,
            "new_version": new_version,
            "archive_path": archive_path,
            "message": "Validation failed, changes rolled back"
        }

    # Success
    return {
        "success": True,
        "old_version": old_version,
        "new_version": new_version,
        "archive_path": archive_path,
        "message": f"Successfully updated {agent_name} from v{old_version} to v{new_version}"
    }


# ============================================================================
# Interactive Changelog Input
# ============================================================================

def get_changelog_interactive() -> str:
    """
    Prompt user for changelog items interactively.

    Returns:
        Changelog text (newline-separated items)

    Raises:
        ValueError: If changelog is empty
    """
    print("\nWhat changed in this version?")
    print("Enter changelog items, one per line.")
    print("Enter an empty line when finished.\n")

    items = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        items.append(line)

    if not items:
        raise ValueError("Changelog cannot be empty")

    return '\n'.join(items)


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Update agent with version increment and changelog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Major version update with changelog
  python update_agent.py documentation-specialist major --changelog "Index-driven approach"

  # Minor version update with interactive changelog
  python update_agent.py blender-specialist minor

  # Patch version without archiving
  python update_agent.py test-agent patch --changelog "Fixed bug" --no-archive

  # Custom agents directory
  python update_agent.py my-agent minor --agents-dir ../agents --changelog "New feature"

Version Increment Types:
  major  - Breaking changes (1.2.3 -> 2.0.0)
  minor  - New features (1.2.3 -> 1.3.0)
  patch  - Bug fixes (1.2.3 -> 1.2.4)

Exit Codes:
  0 - Update successful
  1 - Update failed
        """
    )

    parser.add_argument(
        "agent_name",
        help="Agent name (without .md extension)"
    )

    parser.add_argument(
        "increment",
        choices=['major', 'minor', 'patch'],
        help="Version increment type"
    )

    parser.add_argument(
        "--changelog",
        help="Changelog text (interactive if not provided)"
    )

    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip archiving old version"
    )

    parser.add_argument(
        "--agents-dir",
        default=".claude/agents",
        help="Agents directory (default: .claude/agents)"
    )

    args = parser.parse_args()

    # Get changelog (interactive or from argument)
    try:
        if args.changelog:
            changelog = args.changelog
        else:
            changelog = get_changelog_interactive()
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user")
        sys.exit(1)

    # Perform update
    result = update_agent(
        args.agent_name,
        args.increment,
        changelog,
        archive_old=not args.no_archive,
        agents_dir=args.agents_dir
    )

    # Print results
    if result['success']:
        print(f"\n[SUCCESS] Updated: {args.agent_name}")
        print(f"Version: {result['old_version']} -> {result['new_version']}")
        if result.get('archive_path'):
            print(f"Archived: {result['archive_path']}")
        print()
    else:
        print(f"\n[ERROR] {result['message']}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
