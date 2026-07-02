"""
Archive an agent to the archive directory with version suffix.

Purpose: Preserve agent history before major updates or consolidation.
Usage: python archive_agent.py <agent_name> [--force] [--agents-dir <path>]

Examples:
    python archive_agent.py documentation-specialist
    python archive_agent.py blender-specialist --force
    python archive_agent.py my-agent --agents-dir C:\custom\path\.claude\agents
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def parse_yaml_frontmatter(content: str) -> Dict[str, str]:
    """
    Extract YAML frontmatter without PyYAML dependency.

    Args:
        content: File content as string

    Returns:
        Dictionary of metadata key-value pairs

    Example:
        >>> content = "---\\nname: test\\nversion: 1.0.0\\n---\\n"
        >>> parse_yaml_frontmatter(content)
        {'name': 'test', 'version': '1.0.0'}
    """
    match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    yaml_block = match.group(1)
    metadata: Dict[str, str] = {}

    for line in yaml_block.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    return metadata


def validate_version_format(version: str) -> bool:
    """
    Validate semantic version format (X.Y.Z).

    Args:
        version: Version string to validate

    Returns:
        True if valid semantic version, False otherwise

    Example:
        >>> validate_version_format("1.0.0")
        True
        >>> validate_version_format("1.0")
        False
    """
    # Semantic versioning pattern: MAJOR.MINOR.PATCH
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))


def archive_agent(
    agent_name: str,
    force: bool = False,
    agents_dir: str = ".claude/agents"
) -> Dict[str, Any]:
    """
    Archive an agent file to the archive directory with version suffix.

    Workflow:
        1. Read agent file from agents_dir/<agent_name>.md
        2. Parse version from YAML frontmatter
        3. Create archive directory if needed
        4. Build archive filename: archive/<agent_name>-v<X.Y.Z>.md
        5. Copy file to archive using shutil.copy()
        6. Verify archive file was created
        7. Return success with archive path and version

    Args:
        agent_name: Agent name (without .md extension)
        force: Overwrite existing archive file if True
        agents_dir: Path to agents directory (absolute or relative)

    Returns:
        Dictionary with keys:
            - success (bool): Whether operation succeeded
            - archive_path (str): Absolute path to archived file (if success)
            - version (str): Version number archived (if success)
            - message (str): Success or error message

    Example:
        >>> result = archive_agent("documentation-specialist")
        >>> print(result['success'])
        True
        >>> print(result['version'])
        2.0.0
    """
    # Convert to absolute path if needed
    agents_path = Path(agents_dir).resolve()
    agent_file = agents_path / f"{agent_name}.md"

    # Step 1: Check if agent file exists
    if not agent_file.exists():
        return {
            "success": False,
            "message": f"Agent file not found: {agent_file}"
        }

    # Step 2: Read agent file
    try:
        with open(agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to read agent file: {e}"
        }

    # Step 3: Parse version from YAML frontmatter
    metadata = parse_yaml_frontmatter(content)
    version = metadata.get('version', '').strip()

    if not version:
        return {
            "success": False,
            "message": "No version found in agent metadata. Agent must have 'version: X.Y.Z' in YAML frontmatter."
        }

    # Step 4: Validate version format
    if not validate_version_format(version):
        return {
            "success": False,
            "message": f"Invalid version format: '{version}'. Expected semantic version (X.Y.Z, e.g., 1.0.0)."
        }

    # Step 5: Create archive directory if needed
    archive_dir = agents_path / "archive"
    try:
        archive_dir.mkdir(exist_ok=True)
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create archive directory: {e}"
        }

    # Step 6: Build archive filename
    archive_filename = f"{agent_name}-v{version}.md"
    archive_path = archive_dir / archive_filename

    # Step 7: Check if archive already exists
    if archive_path.exists() and not force:
        return {
            "success": False,
            "message": f"Archive already exists: {archive_path}\nUse --force to overwrite."
        }

    # Step 8: Copy file to archive
    try:
        shutil.copy2(agent_file, archive_path)
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to copy file to archive: {e}"
        }

    # Step 9: Verify archive file was created
    if not archive_path.exists():
        return {
            "success": False,
            "message": f"Archive file was not created: {archive_path}"
        }

    # Step 10: Return success
    return {
        "success": True,
        "archive_path": str(archive_path),
        "version": version,
        "message": f"Successfully archived {agent_name} v{version}"
    }


def main() -> None:
    """
    CLI entry point for archive_agent script.

    Exit codes:
        0: Success
        1: Error (agent not found, archive exists without --force, etc.)
    """
    parser = argparse.ArgumentParser(
        description="Archive an agent to archive directory with version suffix",
        epilog="""
Examples:
  python archive_agent.py documentation-specialist
  python archive_agent.py blender-specialist --force
  python archive_agent.py my-agent --agents-dir C:\\custom\\path\\.claude\\agents

Output:
  Success: Prints archive path and version
  Failure: Prints error message and exits with code 1
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "agent_name",
        help="Agent name (without .md extension)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite if archive file already exists"
    )

    parser.add_argument(
        "--agents-dir",
        default=".claude/agents",
        help="Agents directory path (default: .claude/agents)"
    )

    args = parser.parse_args()

    # Execute archive operation
    result = archive_agent(
        args.agent_name,
        force=args.force,
        agents_dir=args.agents_dir
    )

    # Print results
    if result['success']:
        print(f"[SUCCESS] Archived: {result['archive_path']}")
        print(f"Version: {result['version']}")
        sys.exit(0)
    else:
        print(f"[ERROR] {result['message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
