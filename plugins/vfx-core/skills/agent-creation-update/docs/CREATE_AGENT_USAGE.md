# create_agent.py - Usage Guide

## Overview

The `create_agent.py` script creates new Claude agent files from templates with automatic validation.

**Location:** `<workspace>\.claude\skills\agent-creation-update\scripts\create_agent.py`

**Purpose:** Streamline agent creation with consistent structure, proper naming, and automatic validation.

---

## Quick Start

### Interactive Mode (Recommended for First-Time Users)

```bash
cd <workspace>\.claude\skills\agent-creation-update\scripts
python create_agent.py
```

The script will prompt you for:
1. Agent name (lowercase-with-dashes)
2. Description (What + When + Triggers)
3. Agent type (tool-specialist, cross-tool, general-helper)
4. Tools (comma-separated list)

### CLI Mode (For Automation)

```bash
python create_agent.py unreal-blueprint-specialist \
  --description "Unreal Blueprint automation. Use when working with Blueprints" \
  --tools "Read,Write,Edit,Bash" \
  --type tool-specialist
```

---

## Command-Line Options

### Required Arguments (CLI Mode Only)

```bash
python create_agent.py <agent-name> --description "..." --tools "..."
```

- `<agent-name>` - Agent name (lowercase-with-dashes, 3-50 chars)
- `--description` - Agent description (What + When + Triggers, 10-300 chars)
- `--tools` - Comma-separated tool list (e.g., "Read,Write,Edit")

### Optional Arguments

- `--type` - Agent type (default: `general-helper`)
  - `tool-specialist` - Unreal, Blender, Houdini, Nuke specialists
  - `cross-tool` - Export/import pipeline coordination
  - `general-helper` - Python, testing, documentation helpers

- `--force` - Overwrite if agent already exists

- `--agents-dir` - Agents directory (default: `.claude/agents`)

---

## Usage Examples

### Example 1: Create Tool Specialist Agent

```bash
python create_agent.py nuke-compositing-specialist \
  --description "Nuke compositing automation. Use when working with comp scripts and node graphs" \
  --tools "Read,Write,Edit,Bash,Glob" \
  --type tool-specialist
```

**Output:**
```
✅ Created: <workspace>\.claude\agents\nuke-compositing-specialist.md
Validation: PASS
```

### Example 2: Create Cross-Tool Pipeline Agent

```bash
python create_agent.py blender-to-unreal-pipeline \
  --description "Blender to Unreal asset pipeline. Use when exporting FBX or validating imports" \
  --tools "Read,Write,Bash,Task" \
  --type cross-tool
```

### Example 3: Create General Helper Agent

```bash
python create_agent.py markdown-documentation-helper \
  --description "Markdown documentation generator. Use when creating docs or formatting markdown" \
  --tools "Read,Write,Edit,Grep,Glob" \
  --type general-helper
```

### Example 4: Force Overwrite Existing Agent

```bash
python create_agent.py my-agent \
  --description "Updated agent description. Use when testing updates" \
  --tools "Read,Write" \
  --type general-helper \
  --force
```

### Example 5: Custom Agents Directory

```bash
python create_agent.py test-agent \
  --description "Test agent for validation. Use when testing agent creation" \
  --tools "Read,Write" \
  --type general-helper \
  --agents-dir "./test_agents"
```

---

## Agent Naming Rules

### Valid Names

- Pattern: `^[a-z0-9-]+$` (lowercase, numbers, dashes only)
- Length: 3-50 characters
- No leading/trailing dashes
- No consecutive dashes (`--`)
- No version suffix (`-v2`, `-v1.0`)

### Examples

**✅ Valid:**
- `unreal-blueprint-specialist`
- `blender-geometry-nodes`
- `python-refactoring-helper`
- `test123`

**❌ Invalid:**
- `Agent_Name` (uppercase, underscore)
- `agent-v2` (version suffix)
- `a` (too short)
- `-agent` (leading dash)
- `agent--name` (consecutive dashes)

---

## Description Guidelines

Follow the **What + When + Triggers** formula:

### Good Descriptions

```
✅ "Unreal Blueprint automation. Use when working with Blueprints, actors, or components"
✅ "Houdini to Unreal pipeline. Use when exporting HDAs or validating FBX files"
✅ "Python refactoring specialist. Use when applying templates or adding type hints"
```

### Bad Descriptions

```
❌ "Helps with stuff" (vague)
❌ "Agent" (too short)
❌ "This is a very long description that exceeds the 300 character limit..." (too long)
```

---

## Tools Reference

### Common Tools

**Infrastructure:**
- `Read` - Read files from filesystem
- `Write` - Create new files
- `Edit` - Modify existing files
- `Bash` - Execute shell commands

**Discovery:**
- `Glob` - Find files by pattern
- `Grep` - Search file contents

**Advanced:**
- `Task` - Launch parallel workflows
- `WebFetch` - Fetch web content
- `WebSearch` - Search the web

### Tool Selection Guidelines

**Tool Specialist Agents:**
```bash
--tools "Read,Write,Edit,Bash,Glob,Grep"
```

**Cross-Tool Pipeline Agents:**
```bash
--tools "Read,Write,Bash,Task"
```

**General Helper Agents:**
```bash
--tools "Read,Write,Edit,Grep,Glob"
```

---

## Validation

### Automatic Validation

The script automatically validates created agents against Article IX requirements:

1. **Filename Format** - No version suffix, lowercase-with-dashes
2. **Metadata Present** - All required YAML frontmatter fields
3. **Name Matches Filename** - Internal name == filename
4. **Version Format** - Semantic versioning (X.Y.Z)
5. **Changelog Exists** - Version history for v1.1.0+ (skipped for v1.0.0)
6. **Description Quality** - What + When + Triggers formula

### Validation Output

**Pass:**
```
✅ Created: C:\...\agents\my-agent.md
Validation: PASS
```

**Fail:**
```
✅ Created: C:\...\agents\my-agent.md
Validation: FAIL

Validation Output:
❌ Description Quality: Description too short (5 chars, need 10-300)

Agent created but failed validation. Please review and fix issues.
```

### Manual Validation

```bash
cd <workspace>\.claude\skills\agent-creation-update\scripts
python validate_agent.py my-agent --agents-dir .claude/agents
```

---

## Workflow

### 1. Create Agent

```bash
python create_agent.py my-new-agent \
  --description "My agent description. Use when doing XYZ tasks" \
  --tools "Read,Write,Edit" \
  --type general-helper
```

### 2. Review Generated File

```
.claude/agents/my-new-agent.md
```

The file includes:
- YAML frontmatter with metadata
- Complete agent structure
- Template sections with placeholders
- Version history (v1.0.0 entry)

### 3. Customize Agent

Replace template placeholders:
- `[Capability Category 1]` → Actual capability names
- `[Tool1]` → Actual tool names
- `[Example request]` → Actual example requests
- Remove "Template Usage Notes" section

### 4. Test Agent

```bash
# Test in Claude Code
# Use agent name in conversation to trigger
```

### 5. Validate Final Version

```bash
python validate_agent.py my-new-agent
```

---

## Troubleshooting

### Error: "Invalid agent name"

**Cause:** Name doesn't follow naming conventions

**Solution:** Use lowercase-with-dashes only, 3-50 chars, no version suffix

```bash
# Bad
python create_agent.py My_Agent  # ❌ Uppercase, underscore

# Good
python create_agent.py my-agent  # ✅ Lowercase, dash
```

### Error: "Agent already exists"

**Cause:** Agent file already exists at target path

**Solution:** Use `--force` to overwrite or choose different name

```bash
python create_agent.py existing-agent --force \
  --description "Updated description" \
  --tools "Read,Write"
```

### Error: "Template not found"

**Cause:** Template file missing or incorrect path

**Solution:** Verify template exists at expected location

```bash
# Check template exists
ls <workspace>\.claude\skills\agent-creation-update\reference\agent_template.md
```

### Error: "Description too short"

**Cause:** Description < 10 characters

**Solution:** Provide meaningful description with What + When + Triggers

```bash
# Bad
--description "Helper"  # ❌ Too short

# Good
--description "Python helper. Use when refactoring code or adding type hints"  # ✅
```

### Error: "Validation script not found"

**Cause:** `validate_agent.py` missing from scripts directory

**Solution:** Ensure both scripts are in same directory

```bash
ls scripts/
# Should show:
# - create_agent.py
# - validate_agent.py
```

---

## Testing

### Run Test Suite

```bash
cd <workspace>\.claude\skills\agent-creation-update\scripts
python test_create_agent.py
```

**Tests:**
1. Template loading
2. Placeholder replacement
3. Agent name validation (12 test cases)
4. Agent creation workflow
5. Validation integration

**Expected Output:**
```
============================================================
Running create_agent.py Test Suite
============================================================
✅ Template found: ...

=== Test 1: Template Loading ===
✅ PASS: Template loaded successfully with all placeholders

=== Test 2: Placeholder Replacement ===
✅ PASS: All placeholders replaced correctly

=== Test 3: Agent Name Validation ===
  ✅ Valid name: 'valid-agent-name' → Valid agent name
  ...
Results: 12 passed, 0 failed

...

============================================================
Test Summary
============================================================
✅ test_template_loading
✅ test_placeholder_replacement
✅ test_agent_name_validation
✅ test_agent_creation
✅ test_validation_integration

Total: 5/5 tests passed
```

---

## Advanced Usage

### Batch Agent Creation

```bash
# Create multiple agents
for agent in "agent1" "agent2" "agent3"; do
  python create_agent.py "$agent" \
    --description "$agent description. Use when testing" \
    --tools "Read,Write" \
    --type general-helper
done
```

### Custom Template Workflow

1. Edit base template: `reference/agent_template.md`
2. Add custom sections or modify structure
3. Run `create_agent.py` to use updated template
4. All new agents will use custom template

### Integration with CI/CD

```bash
# In CI pipeline
python create_agent.py test-ci-agent \
  --description "CI test agent. Use when testing automated agent creation" \
  --tools "Read,Write" \
  --type general-helper \
  --agents-dir ./build/agents

# Validate
python validate_agent.py test-ci-agent --agents-dir ./build/agents

# Exit on validation failure
if [ $? -ne 0 ]; then
  echo "Agent validation failed"
  exit 1
fi
```

---

## Files Created

### Agent File Structure

```markdown
---
name: my-agent
description: My agent description. Use when doing XYZ tasks
version: 1.0.0
last_updated: 2025-10-25
status: active
model: sonnet
tools:
  - Read
  - Write
  - Edit
---

# my-agent

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Status:** Active

---

## When to Use

...

## Capabilities

...

## Version History

**v1.0.0** (2025-10-25) - Initial Release
- [Feature/capability 1]
- [Feature/capability 2]
```

### Default Location

```
.claude/agents/
├── my-agent.md
├── another-agent.md
└── yet-another-agent.md
```

---

## See Also

- **validate_agent.py** - Validate existing agents
- **update_agent.py** - Update agent versions
- **archive_agent.py** - Archive old agent versions
- **VFX_SKILL_CONSTITUTION.md** - Agent design principles (Article IX)
- **VFX_AGENT_SKILLS_GUIDE.md** - Complete agent development guide

---

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Script:** `create_agent.py`
