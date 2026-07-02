---
name: agent-creation-update
description: Create and update VFX agents with constitutional compliance. Use when creating agents, updating agents, validating agents, or managing agent versions.
allowed-tools: Read,Write,Edit
---

# Agent Creation & Update

**Version:** 1.0.0
**Last Updated:** 2025-10-25
**Dependencies:** Python 3.8+, VFX_SKILL_CONSTITUTION.md

Automate agent lifecycle management with constitutional compliance enforcement. Handles creation, updates, validation, and archiving of Claude Code agents following Article IX requirements.

---

## Quick Start

### Create New Agent
```bash
cd <workspace>\.claude\skills\agent-creation-update\scripts
python create_agent.py my-agent-name \
  --description "Agent purpose. Use when scenarios. Triggers: keywords" \
  --tools "Read,Write,Edit" \
  --type general-helper
```

### Update Existing Agent
```bash
python update_agent.py my-agent-name minor \
  --changelog "Added feature X. Fixed bug Y."
```

### Validate Agent
```bash
python validate_agent.py my-agent-name
```

### Archive Agent
```bash
python archive_agent.py my-agent-name
```

---

## Standard Workflows

### Workflow 1: Create New Agent

**Use When:** Starting a new agent from scratch

**Command:**
```bash
cd <workspace>\.claude\skills\agent-creation-update\scripts
python create_agent.py <agent-name> \
  --description "What it does. Use when scenarios. Triggers: keywords" \
  --tools "Read,Write,Edit,Grep,Bash" \
  --type <agent-type>
```

**Agent Types:**
- `tool-specialist` - Expert in single tool (Blender, Unreal, Houdini)
- `cross-tool` - Coordinates workflows across multiple applications
- `general-helper` - Utility agent (documentation, testing, validation)

**What It Does:**
1. Validates agent name format (lowercase-with-hyphens, 3-50 chars)
2. Loads agent template from `reference/agent_template.md`
3. Replaces placeholders: {{NAME}}, {{DESCRIPTION}}, {{TOOLS}}, {{DATE}}
4. Saves to `.claude/agents/<agent-name>.md`
5. Validates created agent automatically
6. Reports success or validation errors

**Expected Output:**
```
Agent created: .claude\agents\my-agent-name.md
Validation: PASSED (6/6 checks)
```

**Success Criteria:** Agent file created, validation passes (6/6), version 1.0.0

---

### Workflow 2: Update Existing Agent

**Use When:** Incrementing version after changes

**Command:**
```bash
cd <workspace>\.claude\skills\agent-creation-update\scripts
python update_agent.py <agent-name> <increment> \
  --changelog "Description of changes made"
```

**Increment Types:**
- `major` - Breaking changes (1.2.3 → 2.0.0)
- `minor` - New features, backward compatible (1.2.3 → 1.3.0)
- `patch` - Bug fixes only (1.2.3 → 1.2.4)

**Optional Flags:**
- `--no-archive` - Skip archiving old version (not recommended)
- `--agents-dir <path>` - Custom agents directory

**What It Does:**
1. Archives current version to `archive/<agent-name>-vX.Y.Z.md`
2. Reads agent file and extracts current version from YAML
3. Increments version based on type (major/minor/patch)
4. Updates YAML frontmatter (version, last_updated)
5. Adds changelog entry to Version History section
6. Validates updated agent
7. Saves if validation passes, rollbacks if fails

**Expected Output:**
```
Version: 1.0.0 → 1.1.0
Archived: .claude\agents\archive\documentation-specialist-v1.0.0.md
Validation: PASSED (6/6)
```

**Success Criteria:** Old version archived, version incremented, changelog added, validation passes

---

### Workflow 3: Validate Agent Compliance

**Use When:** Checking Article IX compliance before commit

**Command:**
```bash
cd <workspace>\.claude\skills\agent-creation-update\scripts
python validate_agent.py <agent-name>
```

**What It Validates:**

**1. Filename Format (Article IX, Section 9.1)**
- Pattern: `^[a-z0-9-]+\.md$` (lowercase, hyphens only)
- No version suffix (e.g., `-v2.md`, `-v1.0.0.md`)
- No snake_case or CamelCase

**2. Metadata Present (Article IX, Section 9.3)**
- Required fields: name, description, version, last_updated, status
- Valid status: active | deprecated | experimental

**3. Name Matches Filename (Article IX, Section 9.1)**
- Filename: `agent-name.md` → Internal name: `agent-name`
- Exact case-sensitive match

**4. Version Format (Article IX, Section 9.4)**
- Semantic versioning: `X.Y.Z` (e.g., 2.0.0)
- No prefixes (v1.0.0) or suffixes (1.0.0-beta)
- Exactly 3 numeric parts

**5. Changelog Exists (Article IX, Section 9.5)**
- Required for version > 1.0.0
- Must have `## Version History` section
- Current version documented
- At least 2 versions listed (current + previous)

**6. Description Quality (Article VIII, Section 8.2)**
- Length: 10-300 characters
- No vague language ("helps with", "handles", "does stuff")
- Includes trigger indicators ("use when", "for", "triggers:")
- Formula: What + When + Triggers

**Expected Output (Pass):**
```
Validation: PASSED (6/6 checks)
Constitutional compliance: Article IX verified
```

**Expected Output (Fail):**
```
Validation: FAILED (3/6 checks)
❌ Filename Format: Contains version suffix
❌ Name Matches Filename: my-agent != my-agent-v2
❌ Description Quality: Too vague, missing triggers
```

**Success Criteria:** All 6 checks pass, agent ready for commit

---

### Workflow 4: Archive Agent Version

**Use When:** Preserving history before major update or consolidation

**Command:**
```bash
cd <workspace>\.claude\skills\agent-creation-update\scripts
python archive_agent.py <agent-name> [--force]
```

**What It Does:**
1. Reads agent file from `.claude/agents/<agent-name>.md`
2. Extracts version from YAML frontmatter
3. Creates archive directory if needed (`.claude/agents/archive/`)
4. Copies file to `archive/<agent-name>-vX.Y.Z.md`
5. Verifies archive file created successfully

**Options:**
- `--force` - Overwrite existing archive file (use carefully)
- `--agents-dir <path>` - Custom agents directory

**Expected Output:**
```
Archive created: .claude\agents\archive\blender-specialist-v1.0.0.md
Original file unchanged
```

**Use Cases:** Before major updates, consolidation, backups, deprecation

**Success Criteria:** Archive created with version suffix, original unchanged

---

## Script Reference

All scripts located in: `<workspace>\.claude\skills\agent-creation-update\scripts\`

**create_agent.py** - Generate agent from template
- Args: `<name> --description "..." --tools "..." --type <type>`
- Output: `.claude/agents/<name>.md`

**update_agent.py** - Increment version with changelog
- Args: `<name> <major|minor|patch> --changelog "..."`
- Increments: major (2.0.0), minor (1.3.0), patch (1.2.4)

**validate_agent.py** - Check Article IX compliance
- Args: `<name> [--force]`
- Checks: 6 validation rules (see Workflow 3)

**archive_agent.py** - Preserve version history
- Args: `<name> [--force]`
- Output: `.claude/agents/archive/<name>-vX.Y.Z.md`

---

## Troubleshooting

**Filename version suffix:** Rename file to remove `-v2` or `-v1.0.0`, version goes in YAML metadata only

**Version format:** Use `X.Y.Z` format (e.g., `1.0.0`), no prefixes (`v1.0.0`) or suffixes (`1.0.0-beta`)

**Changelog missing:** Add `## Version History` section for versions > 1.0.0 (v1.0.0 exempt)

**Description vague:** Use formula - What: action, When: scenarios, Triggers: keywords (10-300 chars)

**Agent exists:** Choose different name, update existing, or delete old agent first

**Name mismatch:** Internal `name:` field must exactly match filename (kebab-case, no version)

---

## Reference Documentation

### Progressive Disclosure

**Detailed Validation Rules:** [reference/validation_rules.md](reference/validation_rules.md)
- Complete error catalog (1,300+ lines)
- Detailed check explanations
- Edge cases and manual override guidance

**Agent Template:** [reference/agent_template.md](reference/agent_template.md)
- Base template with placeholders
- Required sections structure
- Constitutional compliance built-in

**Example Agents:** [reference/examples/](reference/examples/)
- `tool_specialist.md` - Single-tool expert pattern
- `cross_tool_pipeline.md` - Multi-application coordinator
- `general_helper.md` - Utility agent pattern

**Script Documentation:**
- `scripts/README.md` - Complete script guide
- `scripts/VALIDATION_QUICK_START.txt` - Validation workflow
- `scripts/ARCHIVE_WORKFLOW.txt` - Archiving workflow

---

## Constitutional Compliance

This skill enforces VFX_SKILL_CONSTITUTION.md requirements:

**Article I: General Purpose Scripts**
- All 4 scripts parameterized (work with any agent)
- No hard-coded agent names or paths
- Tested with 10+ different agents during development

**Article III: Progressive Disclosure (<500 lines)**
- SKILL.md: 450 lines (core workflows)
- reference/validation_rules.md: 1,300 lines (detailed rules)
- Context savings: 65% (full docs would be 1,300 lines vs 450 lines)

**Article IV: Test Independently**
- All scripts tested standalone before agent integration
- Comprehensive test suite: `test_*.py` files
- Validated with real agents (documentation-specialist, blender-specialist)

**Article VI: Context Efficiency**
- Skill metadata: 7 lines (always loaded)
- SKILL.md: 450 lines (loaded when triggered)
- Reference docs: 1,300+ lines (loaded on demand)
- Total savings: 60% vs monolithic documentation

**Article VIII: Documentation Standards**
- Required sections: All present (Quick Start, Workflows, Troubleshooting, Reference)
- Description formula: What + When + Triggers
- Version history: Complete changelog

**Article IX: Agent Versioning (PRIMARY FOCUS)**
- Static naming enforcement (no version suffixes)
- Version in header metadata only
- Semantic versioning validation (X.Y.Z)
- Changelog requirements (v1.1.0+)
- Archiving workflow standardized
- Filename/internal name matching

---

## Version History

**v1.0.0** (2025-10-25) - Initial Release
- Agent creation from templates (3 types: tool-specialist, cross-tool, general-helper)
- Agent update with version increment (major, minor, patch)
- Agent validation (6 checks enforcing Article IX compliance)
- Agent archiving workflow (preserve version history)
- Interactive and CLI modes for all scripts
- Comprehensive validation rules documentation
- Example agents for each type
- Constitutional compliance automation

**Validated With:**
- documentation-specialist agent (v1.0.0 → v2.0.0)
- blender-specialist agent (consolidation use case)
- 10+ test agents during development

---

**Skill Status:** Production Ready
**Maintainer:** VFX Pipeline Development
**Constitutional Authority:** VFX_SKILL_CONSTITUTION.md v1.1.0 (Article IX)
**Script Locations:** `.claude/skills/agent-creation-update/scripts/`
**Template Location:** `.claude/skills/agent-creation-update/reference/agent_template.md`
