# archive_agent.py

Archive Claude agents to preserve history before major updates or consolidation.

## Purpose

When updating or consolidating agents (e.g., Blender agent consolidation), preserve the original version in an archive directory. This maintains historical documentation and allows rollback if needed.

## Requirements

- Python 3.8+ (stdlib only, no external dependencies)
- Agent file must have valid YAML frontmatter with `version: X.Y.Z`

## Usage

### Basic Usage

```bash
# Archive an agent (reads from .claude/agents/ by default)
python archive_agent.py documentation-specialist

# Output:
# ✅ Archived: <workspace>\.claude\agents\archive\documentation-specialist-v2.0.0.md
# Version: 2.0.0
```

### Custom Agents Directory

```bash
# Specify custom agents directory
python archive_agent.py my-agent --agents-dir C:\custom\path\.claude\agents
```

### Force Overwrite

```bash
# Overwrite existing archive file
python archive_agent.py documentation-specialist --force
```

## Workflow

The script follows a systematic 10-step process:

1. **Read agent file** from `agents_dir/<agent_name>.md`
2. **Parse version** from YAML frontmatter
3. **Create archive directory** if needed (`agents_dir/archive/`)
4. **Build archive filename**: `archive/<agent_name>-v<X.Y.Z>.md`
5. **Check if archive exists** (fail if exists and not `--force`)
6. **Copy file** to archive using `shutil.copy2()` (preserves metadata)
7. **Verify** archive file was created
8. **Return success** with archive path and version

## YAML Frontmatter Requirements

Agent files must have valid YAML frontmatter with a semantic version:

```markdown
---
name: my-agent
description: Agent description
version: 2.0.0
tools: Read, Write
---

Agent content...
```

### Version Format

**Valid:** Semantic versioning (X.Y.Z)
- `1.0.0`
- `2.0.0`
- `10.20.30`

**Invalid:**
- `1.0` (missing patch)
- `v1.0.0` (prefix not allowed)
- `1.0.0-beta` (pre-release tag not supported)

## Error Handling

### Agent Not Found

```bash
python archive_agent.py nonexistent-agent

# Output:
# ❌ Error: Agent file not found: C:\...\nonexistent-agent.md
# Exit code: 1
```

### No Version in Frontmatter

```bash
# Agent file missing version field
# ❌ Error: No version found in agent metadata. Agent must have 'version: X.Y.Z' in YAML frontmatter.
```

### Invalid Version Format

```bash
# Agent has version: 1.0 (invalid)
# ❌ Error: Invalid version format: '1.0'. Expected semantic version (X.Y.Z, e.g., 1.0.0).
```

### Archive Already Exists

```bash
python archive_agent.py documentation-specialist

# First time: ✅ Success
# Second time: ❌ Error: Archive already exists: C:\...\archive\documentation-specialist-v2.0.0.md
#              Use --force to overwrite.
```

### Force Overwrite

```bash
python archive_agent.py documentation-specialist --force

# ✅ Archived: C:\...\archive\documentation-specialist-v2.0.0.md (overwrites existing)
```

## Directory Structure

```
.claude/
└── agents/
    ├── documentation-specialist.md      (active agent)
    ├── blender-specialist.md            (active agent)
    └── archive/                         (created automatically)
        ├── documentation-specialist-v1.0.0.md
        ├── documentation-specialist-v2.0.0.md
        ├── blender-geometry-nodes-v1.0.0.md
        └── blender-materials-v2.1.0.md
```

## Use Cases

### 1. Agent Consolidation (Blender Example)

When consolidating 10 specialist agents into 1 unified agent:

```bash
# Archive all 10 agents before consolidation
python archive_agent.py blender-geometry-nodes
python archive_agent.py blender-materials-shaders
python archive_agent.py blender-animation
# ... (7 more)

# Result: 10 archives in .claude/agents/archive/
# - blender-geometry-nodes-v1.0.0.md
# - blender-materials-shaders-v1.0.0.md
# - etc.
```

**Reference:** `ClaudeCode/development/specs/BLENDER_AGENT_CONSOLIDATION_SPEC.md`

### 2. Major Version Update

Before updating agent to v3.0.0 with breaking changes:

```bash
# Archive current v2.0.0
python archive_agent.py documentation-specialist

# Update agent file to v3.0.0
# (manually edit documentation-specialist.md)

# Archive new version for history
python archive_agent.py documentation-specialist --force
```

### 3. Batch Archiving Script

Create a batch script to archive multiple agents:

```bash
# archive_all.sh
agents=("documentation-specialist" "blender-specialist" "unreal-specialist")

for agent in "${agents[@]}"; do
    python archive_agent.py "$agent"
done
```

## Testing

### Unit Tests

```bash
# Run comprehensive pytest suite
cd tests/
pytest test_archive.py -v

# Output shows:
# - YAML parsing tests
# - Version validation tests
# - Archive workflow tests
# - Error handling tests
# - Edge case tests
```

### Manual Integration Tests

```bash
# Run manual integration test
cd tests/
python manual_test_archive.py

# Tests:
# 1. YAML frontmatter parsing
# 2. Version validation
# 3. Archive with temp agent (create, force, errors)
# 4. Real agent detection (optional)
```

### Test Coverage

The test suite validates:

- ✅ YAML frontmatter parsing (with/without frontmatter, multiline, whitespace)
- ✅ Version validation (valid/invalid formats)
- ✅ Successful archiving
- ✅ Error conditions (missing agent, no version, invalid version)
- ✅ Force overwrite functionality
- ✅ Directory creation
- ✅ Content preservation (byte-for-byte identical)
- ✅ Multiple version archiving
- ✅ Absolute path handling

## API Usage

### Python API

```python
from archive_agent import archive_agent

# Archive an agent programmatically
result = archive_agent(
    agent_name="documentation-specialist",
    force=False,
    agents_dir=".claude/agents"
)

if result['success']:
    print(f"Archived: {result['archive_path']}")
    print(f"Version: {result['version']}")
else:
    print(f"Error: {result['message']}")
```

### Return Value

```python
{
    "success": bool,           # True if archived successfully
    "archive_path": str,       # Absolute path to archive file (if success)
    "version": str,            # Version number (if success)
    "message": str             # Success or error message
}
```

## Implementation Details

### YAML Parsing (stdlib only)

No PyYAML dependency - uses regex to extract frontmatter:

```python
def parse_yaml_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter without PyYAML."""
    match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    yaml_block = match.group(1)
    metadata = {}
    for line in yaml_block.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    return metadata
```

### Version Validation

Semantic versioning pattern (MAJOR.MINOR.PATCH):

```python
def validate_version_format(version: str) -> bool:
    """Validate semantic version format (X.Y.Z)."""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))
```

### File Operations

Uses `shutil.copy2()` to preserve metadata (timestamps, permissions):

```python
shutil.copy2(agent_file, archive_path)
```

## Troubleshooting

### Issue: "Agent file not found"

**Cause:** Agent name doesn't match filename or wrong agents_dir

**Solution:**
```bash
# Check filename matches agent name
ls .claude/agents/

# Use correct agent name (without .md)
python archive_agent.py documentation-specialist  # ✅ Correct
python archive_agent.py documentation-specialist.md  # ❌ Wrong
```

### Issue: "No version found"

**Cause:** Missing `version:` field in YAML frontmatter

**Solution:**
```markdown
# Add version to agent file
---
name: my-agent
version: 1.0.0  # Add this line
---
```

### Issue: "Invalid version format"

**Cause:** Version doesn't follow semantic versioning (X.Y.Z)

**Solution:**
```markdown
# Update version to semantic format
---
version: 1.0.0  # ✅ Valid
---

# Invalid formats:
version: 1.0    # ❌ Missing patch
version: v1.0.0 # ❌ Prefix not allowed
```

### Issue: "Archive already exists"

**Cause:** Archive file with same version already exists

**Solution:**
```bash
# Option 1: Use --force to overwrite
python archive_agent.py my-agent --force

# Option 2: Update version in agent file first
# (edit agent.md, change version to 2.1.0)
python archive_agent.py my-agent
```

## Integration with Agent Creation Workflow

This script is part of the **agent-creation-update** skill:

```
.claude/skills/agent-creation-update/
├── scripts/
│   ├── create_agent.py      # Create new agents
│   ├── update_agent.py      # Update existing agents
│   ├── archive_agent.py     # Archive agents (this script)
│   └── validate_agent.py    # Validate agent structure
└── tests/
    ├── test_create.py
    ├── test_update.py
    ├── test_archive.py      # Tests for this script
    └── manual_test_archive.py
```

**Typical workflow:**
1. `validate_agent.py` - Validate agent before archiving
2. `archive_agent.py` - Archive current version
3. `update_agent.py` - Update agent to new version
4. `validate_agent.py` - Validate updated agent

## Related Documentation

- **Agent Creation Guide:** `.claude/skills/agent-creation-update/SKILL.md`
- **Blender Consolidation Spec:** `ClaudeCode/development/specs/BLENDER_AGENT_CONSOLIDATION_SPEC.md`
- **VFX Agent Skills Guide:** `ClaudeCode/development/VFX_AGENT_SKILLS_GUIDE.md`

## Exit Codes

- `0` - Success
- `1` - Error (see stderr for details)

## Performance

- **Fast:** Processes agents in < 1 second
- **Memory efficient:** Streams file content, no large buffers
- **Safe:** Uses `shutil.copy2()` to preserve metadata

## Compatibility

- **OS:** Windows, Linux, macOS (uses pathlib for cross-platform paths)
- **Python:** 3.8+ (type hints, pathlib)
- **Dependencies:** stdlib only (argparse, pathlib, shutil, re, sys)

---

**Last Updated:** 2025-10-25
**Version:** 1.0.0
**Author:** Python Specialist Agent
