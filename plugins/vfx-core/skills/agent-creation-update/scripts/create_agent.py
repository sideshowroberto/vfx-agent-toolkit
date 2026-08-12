#!/usr/bin/env python3
"""
Purpose: Create new Claude agent files from templates
Usage:
  Interactive: python create_agent.py
  CLI: python create_agent.py <name> --description "..." --tools "Read,Write" --type tool-specialist

Template Application:
- Loads template based on agent type
- Replaces placeholders ({{NAME}}, {{DESCRIPTION}}, {{TOOLS}}, {{DATE}})
- Validates created agent against Article IX
- Saves to .claude/agents/<agent-name>.md

Requirements:
- Agent name: ^[a-z0-9-]+$ (lowercase with dashes, 3-50 chars)
- Description: What + When + Triggers formula
- Tools: List of available tools (Read, Write, Edit, etc.)
- Agent type: tool-specialist, cross-tool, general-helper
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Any, Optional


# ============================================================================
# Template Path Configuration
# ============================================================================

# Get script directory for relative path resolution
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent

# Template path - single base template with placeholders
TEMPLATE_PATH = SKILL_DIR / 'reference' / 'agent_template.md'

# Example templates for reference (not used directly, but available for guidance)
EXAMPLES = {
    'tool-specialist': SKILL_DIR / 'reference' / 'examples' / 'tool_specialist.md',
    'cross-tool': SKILL_DIR / 'reference' / 'examples' / 'cross_tool_pipeline.md',
    'general-helper': SKILL_DIR / 'reference' / 'examples' / 'general_helper.md'
}


# ============================================================================
# Path Resolution Helpers
# ============================================================================

def find_project_root() -> Path:
    """
    Find project root directory by walking up from script directory.

    Project root is identified by presence of .claude/agents or .claude/skills directory.
    This is more robust than just checking for .claude, which might be an empty directory.
    If not found within reasonable depth (5 levels), uses current working directory.

    Returns:
        Path: Absolute path to project root
    """
    current = SCRIPT_DIR
    max_depth = 5

    for _ in range(max_depth):
        # Check if .claude/agents or .claude/skills exists at this level
        # (more robust than just checking .claude directory)
        claude_dir = current / '.claude'
        if (claude_dir / 'agents').exists() or (claude_dir / 'skills').exists():
            return current

        # Move up one level
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    # Fallback: use current working directory
    return Path.cwd()


def resolve_agents_dir(agents_dir: str) -> Path:
    """
    Resolve agents directory path, handling relative paths correctly.

    If path is relative (e.g., ".claude/agents"), resolves it against project root.
    If path is absolute, uses it directly.

    Args:
        agents_dir: Agent directory path (relative or absolute)

    Returns:
        Path: Absolute path to agents directory
    """
    agents_path = Path(agents_dir)

    # If already absolute, use it
    if agents_path.is_absolute():
        return agents_path

    # If relative, resolve against project root
    project_root = find_project_root()
    return (project_root / agents_path).resolve()


# ============================================================================
# Template Loading and Processing
# ============================================================================

def load_template(agent_type: str) -> str:
    """
    Load template file content.

    Note: Currently uses single base template (agent_template.md) for all types.
    The agent_type parameter is validated but all types use the same template.
    Future enhancement: Could customize template based on type.

    Args:
        agent_type: Type of agent (tool-specialist, cross-tool, general-helper)

    Returns:
        str: Template file content

    Raises:
        FileNotFoundError: If template file doesn't exist
        ValueError: If agent_type is invalid
    """
    # Validate agent_type
    valid_types = ['tool-specialist', 'cross-tool', 'general-helper']
    if agent_type not in valid_types:
        raise ValueError(f"Invalid agent_type '{agent_type}'. Must be: {', '.join(valid_types)}")

    # Use single base template for all types
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Template not found: {TEMPLATE_PATH}\n"
            f"Expected path: {TEMPLATE_PATH.absolute()}"
        )

    try:
        return TEMPLATE_PATH.read_text(encoding='utf-8')
    except Exception as e:
        raise RuntimeError(f"Error reading template: {e}")


def populate_template(template: str, metadata: Dict[str, Any]) -> str:
    """
    Replace all placeholders in template.

    Placeholders:
    - {{NAME}} -> agent name (e.g., "unreal-blueprint-specialist")
    - {{DESCRIPTION}} -> agent description
    - {{TOOLS}} -> tools list as YAML array (e.g., "\n  - Read\n  - Write")
    - {{DATE}} -> today's date (YYYY-MM-DD)

    Args:
        template: Template file content with placeholders
        metadata: Dictionary with keys: name, description, tools

    Returns:
        str: Template with all placeholders replaced
    """
    # Get today's date
    today = date.today().strftime('%Y-%m-%d')

    # Format tools as YAML array (indented list format)
    # Convert ['Read', 'Write'] -> "\n  - Read\n  - Write"
    tools_list = metadata.get('tools', [])
    if tools_list:
        tools_yaml = '\n'.join(f'  - {tool}' for tool in tools_list)
    else:
        tools_yaml = '  - Read\n  - Write\n  - Edit'  # Default tools

    # Replace placeholders
    content = template.replace('{{NAME}}', metadata['name'])
    content = content.replace('{{DESCRIPTION}}', metadata['description'])
    content = content.replace('{{TOOLS}}', tools_yaml)
    content = content.replace('{{DATE}}', today)

    return content


# ============================================================================
# Agent Name Validation
# ============================================================================

def validate_agent_name(name: str) -> Dict[str, Any]:
    """
    Validate agent name format.

    Requirements:
    - Pattern: ^[a-z0-9-]+$ (lowercase, numbers, dashes only)
    - No version suffix (e.g., -v2, -v1.0)
    - Length: 3-50 characters
    - No leading/trailing dashes
    - No consecutive dashes

    Args:
        name: Agent name to validate

    Returns:
        dict: {"valid": bool, "message": str}
    """
    # Check length
    if len(name) < 3:
        return {
            "valid": False,
            "message": f"Name too short ({len(name)} chars, need 3-50)"
        }

    if len(name) > 50:
        return {
            "valid": False,
            "message": f"Name too long ({len(name)} chars, need 3-50)"
        }

    # Check pattern
    pattern = r'^[a-z0-9-]+$'
    if not re.match(pattern, name):
        return {
            "valid": False,
            "message": f"Name '{name}' must match pattern: [a-z0-9-] (lowercase, numbers, dashes only)"
        }

    # Check for version suffix
    version_pattern = r'-v\d+(\.\d+)?(\.\d+)?$'
    if re.search(version_pattern, name):
        return {
            "valid": False,
            "message": f"Name '{name}' contains version suffix (use metadata instead)"
        }

    # Check for leading/trailing dashes
    if name.startswith('-') or name.endswith('-'):
        return {
            "valid": False,
            "message": f"Name '{name}' has leading/trailing dashes"
        }

    # Check for consecutive dashes
    if '--' in name:
        return {
            "valid": False,
            "message": f"Name '{name}' has consecutive dashes"
        }

    return {
        "valid": True,
        "message": "Valid agent name"
    }


# ============================================================================
# Agent Creation and Validation
# ============================================================================

def check_agent_exists(agent_name: str, agents_dir: str) -> bool:
    """
    Check if agent file already exists.

    Args:
        agent_name: Agent name (without .md extension)
        agents_dir: Directory containing agent files

    Returns:
        bool: True if agent file exists, False otherwise
    """
    agent_path = resolve_agents_dir(agents_dir) / f"{agent_name}.md"
    return agent_path.exists()


def validate_created_agent(agent_name: str, agents_dir: str) -> Dict[str, Any]:
    """
    Run validate_agent.py on created agent.

    Args:
        agent_name: Agent name (without .md extension)
        agents_dir: Directory containing agent files

    Returns:
        dict: {"passed": bool, "output": str}
    """
    validate_script = SCRIPT_DIR / 'validate_agent.py'

    if not validate_script.exists():
        return {
            "passed": False,
            "output": f"Validation script not found: {validate_script}"
        }

    # Resolve agents_dir to absolute path for validation
    resolved_agents_dir = str(resolve_agents_dir(agents_dir))

    try:
        result = subprocess.run(
            [sys.executable, str(validate_script), agent_name, '--agents-dir', resolved_agents_dir],
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            "passed": result.returncode == 0,
            "output": result.stdout + result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "output": "Validation timed out (>10s)"
        }
    except Exception as e:
        return {
            "passed": False,
            "output": f"Validation error: {e}"
        }


def create_agent(
    name: str,
    description: str,
    tools: List[str],
    agent_type: str = 'general-helper',
    force: bool = False,
    agents_dir: str = ".claude/agents"
) -> Dict[str, Any]:
    """
    Create new agent from template.

    Main workflow:
    1. Validate agent name
    2. Check if agent exists (unless force=True)
    3. Load template based on agent_type
    4. Populate template placeholders
    5. Save to agents_dir/<name>.md
    6. Validate created agent
    7. Return result

    Args:
        name: Agent name (lowercase-with-dashes)
        description: Agent description (What + When + Triggers)
        tools: List of tool names (e.g., ['Read', 'Write', 'Edit'])
        agent_type: Template type (tool-specialist, cross-tool, general-helper)
        force: Overwrite if agent already exists
        agents_dir: Directory to save agent file

    Returns:
        dict: {
            "success": bool,
            "agent_path": str,
            "validation": dict,
            "message": str
        }
    """
    # Step 1: Validate agent name
    name_validation = validate_agent_name(name)
    if not name_validation['valid']:
        return {
            "success": False,
            "agent_path": "",
            "validation": {},
            "message": f"Invalid agent name: {name_validation['message']}"
        }

    # Step 2: Check if agent exists
    if check_agent_exists(name, agents_dir) and not force:
        agent_path = Path(agents_dir) / f"{name}.md"
        return {
            "success": False,
            "agent_path": str(agent_path.absolute()),
            "validation": {},
            "message": f"Agent already exists: {agent_path} (use --force to overwrite)"
        }

    # Step 3: Load template
    try:
        template = load_template(agent_type)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        return {
            "success": False,
            "agent_path": "",
            "validation": {},
            "message": str(e)
        }

    # Step 4: Populate template
    metadata = {
        "name": name,
        "description": description,
        "tools": tools
    }
    content = populate_template(template, metadata)

    # Step 5: Save to file
    agents_path = resolve_agents_dir(agents_dir)
    agents_path.mkdir(parents=True, exist_ok=True)

    agent_file = agents_path / f"{name}.md"

    try:
        agent_file.write_text(content, encoding='utf-8')
    except Exception as e:
        return {
            "success": False,
            "agent_path": str(agent_file.absolute()),
            "validation": {},
            "message": f"Error writing agent file: {e}"
        }

    # Step 6: Validate created agent
    validation = validate_created_agent(name, agents_dir)

    # Step 7: Return result
    return {
        "success": True,
        "agent_path": str(agent_file.absolute()),
        "validation": validation,
        "message": f"Created agent: {name}"
    }


# ============================================================================
# Interactive Mode
# ============================================================================

def get_agent_metadata_interactive() -> Dict[str, Any]:
    """
    Prompt user for agent metadata.

    Returns:
        dict: {
            "name": str,
            "description": str,
            "tools": List[str],
            "agent_type": str
        }
    """
    print("\n=== Create New Agent ===\n")

    # Agent name
    print("Agent name (lowercase-with-dashes):")
    print("Example: unreal-blueprint-specialist")
    print("Pattern: [a-z0-9-] (3-50 chars)")
    name = input("> ").strip()

    # Description
    print("\nDescription (What + When + Triggers):")
    print("Example: Unreal Blueprint automation. Use when working with Blueprints")
    print("Length: 10-300 chars")
    description = input("> ").strip()

    # Agent type
    print("\nSelect agent type:")
    print("1. Tool Specialist (Unreal, Blender, Houdini, Nuke)")
    print("2. Cross-Tool Pipeline (Export/import workflows)")
    print("3. General Helper (Python, testing, documentation)")
    choice = input("> ").strip()

    agent_type_map = {
        '1': 'tool-specialist',
        '2': 'cross-tool',
        '3': 'general-helper'
    }
    agent_type = agent_type_map.get(choice, 'general-helper')

    # Tools
    print("\nTools (comma-separated):")
    print("Common: Read, Write, Edit, Bash, Glob, Grep")
    print("Advanced: Task, WebFetch, WebSearch")
    tools_input = input("> ").strip()

    if tools_input:
        tools = [t.strip() for t in tools_input.split(',')]
    else:
        tools = ['Read', 'Write', 'Edit']  # Default tools

    return {
        'name': name,
        'description': description,
        'tools': tools,
        'agent_type': agent_type
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Create new agent from template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python create_agent.py

  # CLI mode
  python create_agent.py unreal-blueprint-specialist \\
    --description "Unreal Blueprint automation. Use when working with Blueprints" \\
    --tools "Read,Write,Edit,Bash" \\
    --type tool-specialist

  # Force overwrite
  python create_agent.py my-agent \\
    --description "My custom agent" \\
    --tools "Read,Write" \\
    --type general-helper \\
    --force

Agent Types:
  tool-specialist  - Unreal, Blender, Houdini, Nuke specialists
  cross-tool       - Export/import pipeline coordination
  general-helper   - Python, testing, documentation helpers

Common Tools:
  Read, Write, Edit, Bash, Glob, Grep, Task, WebFetch, WebSearch
        """
    )

    parser.add_argument(
        "name",
        nargs='?',
        help="Agent name (interactive if not provided)"
    )

    parser.add_argument(
        "--description",
        help="Agent description (What + When + Triggers)"
    )

    parser.add_argument(
        "--tools",
        help="Comma-separated tool list (e.g., 'Read,Write,Edit')"
    )

    parser.add_argument(
        "--type",
        choices=['tool-specialist', 'cross-tool', 'general-helper'],
        default='general-helper',
        help="Agent type (default: general-helper)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite if agent already exists"
    )

    parser.add_argument(
        "--agents-dir",
        default=".claude/agents",
        help="Agents directory (default: .claude/agents)"
    )

    args = parser.parse_args()

    # Interactive mode if name not provided
    if not args.name:
        metadata = get_agent_metadata_interactive()
        metadata['force'] = args.force
        metadata['agents_dir'] = args.agents_dir
    else:
        # CLI mode - require description and tools
        if not args.description:
            print("Error: --description required when name provided")
            print("Example: --description 'Unreal automation. Use when working with Blueprints'")
            sys.exit(1)

        if not args.tools:
            print("Error: --tools required when name provided")
            print("Example: --tools 'Read,Write,Edit,Bash'")
            sys.exit(1)

        metadata = {
            'name': args.name,
            'description': args.description,
            'tools': [t.strip() for t in args.tools.split(',')],
            'agent_type': args.type,
            'force': args.force,
            'agents_dir': args.agents_dir
        }

    # Validate empty inputs
    if not metadata['description']:
        print("Error: Description cannot be empty")
        sys.exit(1)

    if not metadata['tools']:
        print("Error: Tools list cannot be empty")
        sys.exit(1)

    # Create agent
    result = create_agent(**metadata)

    # Print results
    if result['success']:
        print(f"\n[SUCCESS] Created: {result['agent_path']}")

        # Print validation results
        if result['validation']['passed']:
            print("Validation: PASS")
        else:
            print("Validation: FAIL")
            print("\nValidation Output:")
            print(result['validation']['output'])
            print("\nAgent created but failed validation. Please review and fix issues.")
            sys.exit(1)
    else:
        print(f"\n[ERROR] {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
