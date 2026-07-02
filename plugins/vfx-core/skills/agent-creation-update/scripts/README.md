# Agent Creation & Update Scripts

This directory contains Python scripts for managing Claude agents according to Article IX of the VFX_SKILL_CONSTITUTION.md.

## Scripts Overview

### 1. create_agent.py
**Status:** Placeholder (not yet implemented)

Creates new agent files from templates.

```bash
python create_agent.py --name <agent_name> --type <specialist|pipeline|helper>
```

---

### 2. update_agent.py ✅
**Status:** Fully implemented

Updates existing agents with version increments and changelog entries.

**Features:**
- Semantic versioning (major/minor/patch)
- Automatic YAML metadata updates
- Changelog management
- Version history insertion
- Archive integration
- Validation integration with rollback

**Usage:**
```bash
# Major version update with changelog
python update_agent.py documentation-specialist major --changelog "Index-driven approach"

# Minor version with interactive changelog
python update_agent.py blender-specialist minor

# Patch version without archiving
python update_agent.py test-agent patch --changelog "Fixed bug" --no-archive

# Custom agents directory
python update_agent.py my-agent minor --agents-dir ../agents --changelog "New feature"
```

**Arguments:**
- `agent_name` - Agent name (without .md extension)
- `increment` - Version increment type: `major`, `minor`, or `patch`
- `--changelog` - Changelog text (interactive prompt if not provided)
- `--no-archive` - Skip archiving old version
- `--agents-dir` - Agents directory (default: `.claude/agents`)

**Version Increment Rules:**
- **major**: Breaking changes (1.2.3 → 2.0.0)
- **minor**: New features (1.2.3 → 1.3.0)
- **patch**: Bug fixes (1.2.3 → 1.2.4)

**Workflow:**
1. Archive current version (if `--no-archive` not set)
2. Read agent file and parse YAML frontmatter
3. Increment version based on type
4. Update metadata (version, last_updated)
5. Format and insert changelog entry into Version History
6. Validate updated agent
7. Save if validation passes, rollback if fails

**Exit Codes:**
- `0` - Update successful
- `1` - Update failed

---

### 3. archive_agent.py
**Status:** Placeholder (stub implementation in update_agent.py)

Archives deprecated agents while preserving documentation.

```bash
python archive_agent.py --agent <path> --reason <consolidation|deprecated|obsolete>
```

**Note:** Currently, archiving is implemented inline in `update_agent.py` with basic version-based naming.

---

### 4. validate_agent.py ✅
**Status:** Fully implemented

Validates agents against Article IX requirements.

**Validation Checks:**
1. Filename format (no version suffix, kebab-case)
2. Metadata present (required YAML fields)
3. Name matches filename
4. Version format (semantic versioning X.Y.Z)
5. Changelog exists (for versions > 1.0.0)
6. Description quality (What + When + Triggers)

**Usage:**
```bash
python validate_agent.py <agent_name> [--agents-dir <path>]
```

**Exit Codes:**
- `0` - All checks passed
- `1` - One or more checks failed
- `2` - File not found or error

---

### 5. test_validation.py ✅
**Status:** Fully implemented

Test suite for `validate_agent.py`.

```bash
python test_validation.py
```

---

### 6. test_update_agent.py ✅
**Status:** Fully implemented

Comprehensive test suite for `update_agent.py`.

**Tests:**
1. Version increment logic (major, minor, patch)
2. YAML frontmatter parsing and updating
3. Changelog formatting and insertion
4. Full update workflow with validation
5. Error handling (missing files, invalid versions)

**Usage:**
```bash
python test_update_agent.py
```

**Expected Output:**
```
======================================================================
UPDATE_AGENT.PY TEST SUITE
======================================================================

=== Testing Version Increment ===
✅ 1.2.3 + major = 2.0.0
✅ 1.2.3 + minor = 1.3.0
✅ 1.2.3 + patch = 1.2.4
...

======================================================================
TEST SUMMARY
======================================================================
✅ PASS - Version Increment
✅ PASS - Parse Frontmatter
✅ PASS - Update Frontmatter
...

Total: 9 passed, 0 failed

🎉 All tests passed!
```

---

## Implementation Details

### Version Increment Logic

```python
def increment_version(current: str, increment_type: str) -> str:
    """
    Examples:
        increment_version("1.2.3", "major") -> "2.0.0"
        increment_version("1.2.3", "minor") -> "1.3.0"
        increment_version("1.2.3", "patch") -> "1.2.4"
    """
    major, minor, patch = map(int, current.split('.'))

    if increment_type == 'major':
        return f"{major + 1}.0.0"
    elif increment_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif increment_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
```

### Changelog Format

Changelog entries follow this format:

```markdown
**vX.Y.Z** (YYYY-MM-DD) - Title from first line
- First changelog item
- Second changelog item
- Third changelog item
```

**Example:**
```
Input changelog:
  "Major update\nBreaking changes\nNew architecture"

Generated entry:
  **v2.0.0** (2025-10-25) - Major update
  - Major update
  - Breaking changes
  - New architecture
```

### YAML Metadata Updates

The script updates two fields in the YAML frontmatter:

```yaml
version: 2.0.0          # Incremented based on type
last_updated: 2025-10-25  # Set to today's date
```

### Version History Insertion

New changelog entries are inserted **before** existing entries:

```markdown
## Version History

**v2.0.0** (2025-10-25) - Major update    ← NEW ENTRY
- Breaking changes
- New features

**v1.2.3** (2025-10-20) - Bug fixes       ← OLD ENTRY
- Fixed critical bug

**v1.0.0** (2025-10-01) - Initial release
- Basic functionality
```

If no `## Version History` section exists, it's created at the end of the file.

---

## Testing

### Running Tests

```bash
# Test validation script
python test_validation.py

# Test update script
python test_update_agent.py
```

### Creating Test Agents

For testing purposes, you can create test agents in `.claude/agents/`:

```bash
# Create test agent
cat > .claude/agents/test-agent.md << 'EOF'
---
name: test-agent
description: Test agent for validation. Use when testing agent scripts.
version: 1.0.0
last_updated: 2025-10-25
status: active
---

# Test Agent

This is a test agent.

## Version History

**v1.0.0** (2025-10-25) - Initial release
- Basic functionality
EOF

# Test update
python update_agent.py test-agent minor --changelog "Added new feature"

# Verify result
cat .claude/agents/test-agent.md
```

---

## Dependencies

All scripts use only Python standard library:

- `argparse` - CLI argument parsing
- `os` - File system operations
- `re` - Regular expressions (YAML parsing, version matching)
- `subprocess` - Running validation script
- `sys` - Exit codes and paths
- `datetime` - Date formatting
- `pathlib` - Path operations
- `typing` - Type hints

**No external dependencies required.**

---

## Constitutional Compliance

These scripts implement Article IX of `VFX_SKILL_CONSTITUTION.md`:

**Article IX: Agent Versioning and Naming Conventions**

- **9.1** No version suffix in filenames
- **9.2** Version tracked in YAML metadata
- **9.3** Semantic versioning (X.Y.Z)
- **9.4** last_updated field synchronized
- **9.5** Version history for v1.1.0+

**Constitutional Reference:**
```
<workspace>\ClaudeCode\development\VFX_SKILL_CONSTITUTION.md
```

---

## Future Enhancements

### Planned Features

1. **create_agent.py** - Full implementation with templates
2. **archive_agent.py** - Proper archiving with metadata preservation
3. **Multi-line YAML parsing** - Handle multi-line description fields
4. **Batch operations** - Update multiple agents at once
5. **Changelog validation** - Ensure changelog follows style guide
6. **Interactive mode** - TUI for guided updates

### Potential Improvements

- YAML library integration (PyYAML) for more robust parsing
- Git integration (automatic commits on update)
- Diff preview before applying changes
- Changelog generation from git history
- Version compatibility matrix

---

## Troubleshooting

### Common Issues

**Issue:** "Agent not found: .claude/agents/my-agent.md"
- **Solution:** Ensure agent file exists and name matches (without .md extension)

**Issue:** "Invalid version format: X.Y"
- **Solution:** Agent version must be semantic (X.Y.Z format, e.g., 1.0.0)

**Issue:** "Validation failed, changes rolled back"
- **Solution:** Check validation output for specific failures
- Run `python validate_agent.py <agent_name>` to debug

**Issue:** "No YAML frontmatter found"
- **Solution:** Ensure agent file starts with `---` and has proper YAML metadata

**Issue:** "Changelog cannot be empty"
- **Solution:** Provide changelog via `--changelog` or enter items interactively

---

## Examples

### Example 1: Major Version Update

```bash
# Before: v1.5.2 (active agent)
python update_agent.py blender-specialist major --changelog "Consolidated 10 agents into unified system"

# After: v2.0.0 (with changelog entry)
# Archive: .claude/agents/archive/blender-specialist-v1.5.2.md
```

### Example 2: Interactive Changelog

```bash
python update_agent.py documentation-specialist minor

# Output:
# What changed in this version?
# Enter changelog items, one per line.
# Enter an empty line when finished.
#
# > Added multi-application support
# > Enhanced cross-reference validation
# > Improved session documentation format
# >

# ✅ Updated: documentation-specialist
# Version: 1.0.0 -> 1.1.0
# Archived: .claude/agents/archive/documentation-specialist-v1.0.0.md
```

### Example 3: Patch Without Archive

```bash
python update_agent.py test-agent patch --changelog "Fixed typo in description" --no-archive

# ✅ Updated: test-agent
# Version: 1.2.3 -> 1.2.4
```

---

## Related Files

- **Skill Documentation:** `../.SKILL.md`
- **Constitution:** `<workspace>\ClaudeCode\development\VFX_SKILL_CONSTITUTION.md`
- **Agent Templates:** `<workspace>\ClaudeCode\templates\`

---

*Last Updated: 2025-10-25*
*Script Version: 1.0.0*
