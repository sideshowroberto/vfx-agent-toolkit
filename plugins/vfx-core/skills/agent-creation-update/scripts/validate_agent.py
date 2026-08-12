#!/usr/bin/env python3
r"""
Purpose: Validate agent files against VFX_SKILL_CONSTITUTION.md Article IX
Usage: python validate_agent.py <agent_name> [--agents-dir <path>]

Validation Checks (Article IX):
1. Filename format: No version suffix in filename
2. Metadata present: Required YAML frontmatter fields
3. Name matches filename: Internal name == filename (without .md)
4. Version format: Semantic versioning (X.Y.Z)
5. Changelog exists: Version history for v1.1.0+
6. Description quality: What + When + Triggers formula

Constitutional Reference:
- ClaudeCode\development\VFX_SKILL_CONSTITUTION.md
- Article IX: Agent Versioning and Naming Conventions (sections 9.1-9.5)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


# ============================================================================
# Validation Check Functions
# ============================================================================

def check_filename_format(filename: str) -> Dict[str, Any]:
    """
    Check if filename follows naming conventions.

    Requirements:
    - Pattern: ^[a-z0-9-]+\.md$
    - No version suffix (e.g., -v2, -v1.0)
    - No CamelCase or snake_case

    Args:
        filename: The agent filename (e.g., "documentation-specialist.md")

    Returns:
        dict: {"name": str, "passed": bool, "message": str}
    """
    check_name = "Filename Format"

    # Check basic pattern
    pattern = r'^[a-z0-9-]+\.md$'
    if not re.match(pattern, filename):
        return {
            "name": check_name,
            "passed": False,
            "message": f"Filename '{filename}' must match pattern: [a-z0-9-].md"
        }

    # Check for version suffix
    version_pattern = r'-v\d+(\.\d+)?(\.\d+)?\.md$'
    if re.search(version_pattern, filename):
        return {
            "name": check_name,
            "passed": False,
            "message": f"Filename '{filename}' contains version suffix (use metadata instead)"
        }

    # Check for invalid naming conventions
    if '_' in filename:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Filename '{filename}' uses snake_case (use kebab-case instead)"
        }

    if re.search(r'[A-Z]', filename):
        return {
            "name": check_name,
            "passed": False,
            "message": f"Filename '{filename}' uses uppercase (use lowercase only)"
        }

    return {
        "name": check_name,
        "passed": True,
        "message": "No version suffix found, follows naming conventions"
    }


def check_metadata_present(agent_content: str) -> Dict[str, Any]:
    """
    Check if required YAML frontmatter fields are present.

    Required fields:
    - name: Agent identifier (must match filename)
    - description: What + When + Triggers
    - version: Semantic version (X.Y.Z)
    - last_updated: YYYY-MM-DD
    - status: active | deprecated | experimental

    Optional fields:
    - model: LLM model to use
    - tools: List of tools available
    - breaking_changes: Boolean for v2.0+ compatibility
    - deprecated_date: Date if status=deprecated

    Args:
        agent_content: Full text content of agent file

    Returns:
        dict: {"name": str, "passed": bool, "message": str, "metadata": dict}
    """
    check_name = "Metadata Present"

    # Extract YAML frontmatter
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.search(frontmatter_pattern, agent_content, re.DOTALL)

    if not match:
        return {
            "name": check_name,
            "passed": False,
            "message": "No YAML frontmatter found (must start with ---)",
            "metadata": {}
        }

    frontmatter_text = match.group(1)

    # Parse YAML manually (simple key: value parsing)
    metadata = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    # Check required fields
    required_fields = ['name', 'description', 'version', 'last_updated', 'status']
    missing_fields = [field for field in required_fields if field not in metadata]

    if missing_fields:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Missing required fields: {', '.join(missing_fields)}",
            "metadata": metadata
        }

    # Validate status field
    valid_statuses = ['active', 'deprecated', 'experimental']
    if metadata['status'] not in valid_statuses:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Invalid status '{metadata['status']}' (must be: {', '.join(valid_statuses)})",
            "metadata": metadata
        }

    return {
        "name": check_name,
        "passed": True,
        "message": "All required fields found",
        "metadata": metadata
    }


def check_name_matches_filename(filename: str, metadata_name: str) -> Dict[str, Any]:
    """
    Check if metadata name field matches filename.

    Requirements:
    - Extract name from filename: "agent-name.md" -> "agent-name"
    - Compare with metadata name field
    - Must match exactly (case-sensitive)

    Args:
        filename: Agent filename (e.g., "documentation-specialist.md")
        metadata_name: Name from YAML frontmatter

    Returns:
        dict: {"name": str, "passed": bool, "message": str}
    """
    check_name = "Name Matches Filename"

    # Extract name from filename (remove .md extension)
    filename_base = filename.replace('.md', '')

    if filename_base == metadata_name:
        return {
            "name": check_name,
            "passed": True,
            "message": f"{filename_base} == {metadata_name}"
        }
    else:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Mismatch: filename={filename_base}, metadata={metadata_name}"
        }


def check_version_format(version_string: str) -> Dict[str, Any]:
    """
    Check if version follows semantic versioning.

    Requirements:
    - Pattern: ^\d+\.\d+\.\d+$ (three numbers with dots)
    - PASS: "1.0.0", "2.1.3", "10.20.30"
    - FAIL: "v1.0.0", "1.0", "1.0.0-beta", "1.0.0.0"

    Args:
        version_string: Version from metadata (e.g., "2.0.0")

    Returns:
        dict: {"name": str, "passed": bool, "message": str, "version_parts": tuple}
    """
    check_name = "Version Format"

    # Check semantic versioning pattern
    pattern = r'^\d+\.\d+\.\d+$'
    if not re.match(pattern, version_string):
        return {
            "name": check_name,
            "passed": False,
            "message": f"Version '{version_string}' must match X.Y.Z format (e.g., 2.0.0)",
            "version_parts": None
        }

    # Parse version parts
    parts = version_string.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    return {
        "name": check_name,
        "passed": True,
        "message": f"{version_string} is valid semantic version",
        "version_parts": (major, minor, patch)
    }


def check_changelog_exists(agent_content: str, version_string: str) -> Dict[str, Any]:
    """
    Check if changelog/version history exists for versions > 1.0.0.

    Requirements:
    - If version > 1.0.0, must have "## Version History" section
    - Must document at least 2 versions (current + previous)
    - Parse version from header (1.0.0 -> major=1, minor=0, patch=0)

    Args:
        agent_content: Full text content of agent file
        version_string: Current version from metadata (e.g., "2.0.0")

    Returns:
        dict: {"name": str, "passed": bool, "message": str, "versions_found": list}
    """
    check_name = "Changelog Exists"

    # Parse version
    parts = version_string.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    # If version is 1.0.0, changelog is optional
    if major == 1 and minor == 0 and patch == 0:
        return {
            "name": check_name,
            "passed": True,
            "message": "Version 1.0.0 - changelog not required",
            "versions_found": []
        }

    # Check for version history section
    version_history_pattern = r'##\s+Version\s+History'
    if not re.search(version_history_pattern, agent_content, re.IGNORECASE):
        return {
            "name": check_name,
            "passed": False,
            "message": f"Version {version_string} requires '## Version History' section",
            "versions_found": []
        }

    # Find all version entries
    version_entry_pattern = r'\*\*v?(\d+\.\d+\.\d+)\*\*'
    versions_found = re.findall(version_entry_pattern, agent_content)

    if len(versions_found) < 2:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Found {len(versions_found)} version(s), need at least 2 (current + previous)",
            "versions_found": versions_found
        }

    # Check if current version is documented
    if version_string not in versions_found:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Current version {version_string} not found in changelog",
            "versions_found": versions_found
        }

    versions_list = ", ".join([f"v{v}" for v in versions_found])
    return {
        "name": check_name,
        "passed": True,
        "message": f"Version history section found ({versions_list})",
        "versions_found": versions_found
    }


def check_description_quality(description: str) -> Dict[str, Any]:
    """
    Check if description follows quality guidelines.

    Requirements:
    - Formula: What + When + Triggers
    - Length: 10-300 characters
    - Not vague (avoid: "helps with", "does stuff", "manages things")
    - Should contain "Use when" or specific trigger words

    Args:
        description: Description from metadata

    Returns:
        dict: {"name": str, "passed": bool, "message": str}
    """
    check_name = "Description Quality"

    # Check length
    desc_length = len(description)
    if desc_length < 10:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Description too short ({desc_length} chars, need 10-300)"
        }

    if desc_length > 300:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Description too long ({desc_length} chars, need 10-300)"
        }

    # Check for vague language
    vague_phrases = ["helps with", "does stuff", "manages things", "handles", "works with"]
    desc_lower = description.lower()
    vague_found = [phrase for phrase in vague_phrases if phrase in desc_lower]

    if vague_found:
        return {
            "name": check_name,
            "passed": False,
            "message": f"Description contains vague language: {', '.join(vague_found)}"
        }

    # Check for trigger indicators
    trigger_indicators = ["use when", "use with", "triggers:", "for", "when"]
    has_triggers = any(indicator in desc_lower for indicator in trigger_indicators)

    if not has_triggers:
        return {
            "name": check_name,
            "passed": False,
            "message": "Description should include trigger indicators (e.g., 'Use when', 'for')"
        }

    return {
        "name": check_name,
        "passed": True,
        "message": "Clear description with triggers"
    }


# ============================================================================
# Main Validation Function
# ============================================================================

def validate_agent(agent_path: str) -> Dict[str, Any]:
    """
    Validate an agent file against Article IX requirements.

    Args:
        agent_path: Full path to agent file

    Returns:
        dict: {
            "passed": bool,
            "violations": list,
            "checks": dict,
            "agent_name": str,
            "agent_path": str
        }
    """
    # Check if file exists
    if not os.path.exists(agent_path):
        return {
            "passed": False,
            "violations": [f"File not found: {agent_path}"],
            "checks": {},
            "agent_name": "unknown",
            "agent_path": agent_path
        }

    # Read file
    try:
        with open(agent_path, 'r', encoding='utf-8') as f:
            agent_content = f.read()
    except Exception as e:
        return {
            "passed": False,
            "violations": [f"Error reading file: {e}"],
            "checks": {},
            "agent_name": "unknown",
            "agent_path": agent_path
        }

    # Extract filename
    filename = os.path.basename(agent_path)
    agent_name = filename.replace('.md', '')

    # Run all checks
    checks = {}

    # Check 1: Filename format
    checks['filename_format'] = check_filename_format(filename)

    # Check 2: Metadata present
    metadata_check = check_metadata_present(agent_content)
    checks['metadata_present'] = metadata_check
    metadata = metadata_check.get('metadata', {})

    # Check 3: Name matches filename (only if metadata exists)
    if metadata and 'name' in metadata:
        checks['name_matches_filename'] = check_name_matches_filename(
            filename, metadata['name']
        )
    else:
        checks['name_matches_filename'] = {
            "name": "Name Matches Filename",
            "passed": False,
            "message": "Cannot check: metadata not present"
        }

    # Check 4: Version format (only if metadata exists)
    if metadata and 'version' in metadata:
        version_check = check_version_format(metadata['version'])
        checks['version_format'] = version_check

        # Check 5: Changelog exists (only if version is valid)
        if version_check['passed']:
            checks['changelog_exists'] = check_changelog_exists(
                agent_content, metadata['version']
            )
        else:
            checks['changelog_exists'] = {
                "name": "Changelog Exists",
                "passed": False,
                "message": "Cannot check: version format invalid"
            }
    else:
        checks['version_format'] = {
            "name": "Version Format",
            "passed": False,
            "message": "Cannot check: metadata not present"
        }
        checks['changelog_exists'] = {
            "name": "Changelog Exists",
            "passed": False,
            "message": "Cannot check: version not present"
        }

    # Check 6: Description quality (only if metadata exists)
    if metadata and 'description' in metadata:
        checks['description_quality'] = check_description_quality(
            metadata['description']
        )
    else:
        checks['description_quality'] = {
            "name": "Description Quality",
            "passed": False,
            "message": "Cannot check: metadata not present"
        }

    # Determine overall pass/fail
    passed = all(check['passed'] for check in checks.values())
    violations = [
        f"{check['name']}: {check['message']}"
        for check in checks.values()
        if not check['passed']
    ]

    return {
        "passed": passed,
        "violations": violations,
        "checks": checks,
        "agent_name": agent_name,
        "agent_path": agent_path
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate agent against Article IX of VFX_SKILL_CONSTITUTION.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_agent.py documentation-specialist
  python validate_agent.py blender-specialist --agents-dir .claude/agents
  python validate_agent.py my-agent --agents-dir ../agents

Exit Codes:
  0 - All checks passed
  1 - One or more checks failed
  2 - File not found or error
        """
    )

    parser.add_argument(
        "agent_name",
        help="Agent name (without .md extension)"
    )

    parser.add_argument(
        "--agents-dir",
        default=".claude/agents",
        help="Agents directory (default: .claude/agents)"
    )

    args = parser.parse_args()

    # Build full path
    agent_path = os.path.join(args.agents_dir, f"{args.agent_name}.md")

    # Validate
    result = validate_agent(agent_path)

    # Print results
    print(f"\nValidating: {result['agent_name']}")
    print(f"Path: {result['agent_path']}\n")

    # Print each check
    for check_name, check_result in result['checks'].items():
        symbol = "[PASS]" if check_result['passed'] else "[FAIL]"
        print(f"{symbol} {check_result['name']}: {check_result['message']}")

    # Print summary
    passed_count = sum(1 for c in result['checks'].values() if c['passed'])
    total_count = len(result['checks'])

    print(f"\nRESULT: {'PASS' if result['passed'] else 'FAIL'} ({passed_count}/{total_count} checks)")

    # Print violations if any
    if result['violations']:
        print("\nViolations:")
        for violation in result['violations']:
            print(f"  - {violation}")

    # Exit with appropriate code
    if not os.path.exists(result['agent_path']):
        sys.exit(2)

    sys.exit(0 if result['passed'] else 1)


if __name__ == "__main__":
    main()
