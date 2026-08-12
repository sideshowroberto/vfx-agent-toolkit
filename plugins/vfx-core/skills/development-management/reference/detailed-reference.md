# Development Management: Detailed Reference

## Agent Architecture Patterns

### Pattern 1: Tool-Specific Specialists
**Examples:** blender-geometry-nodes-specialist, blender-sculpting-specialist, unreal-mcp agents

**Characteristics:**
- Deep expertise in ONE tool/domain
- MCP integration for tool control (Unreal MCP, Blender Python API)
- Skills for common workflows
- Documentation-heavy (API references)

**When to use:**
- Tool-specific operations (Blender, Unreal, Houdini)
- Complex workflows requiring tool knowledge
- API integration needed

### Pattern 2: Cross-Tool Pipeline
**Examples:** houdini-to-unreal-export, blender-fbx-pipeline

**Characteristics:**
- Coordinates multiple applications
- Skills for format conversion
- Validation at each step
- Standard naming conventions

**When to use:**
- Asset export/import workflows
- Multi-tool pipelines
- Format standardization needed
- Team collaboration workflows

### Pattern 3: General Purpose Helpers
**Examples:** python-specialist, testing-specialist, documentation-specialist

**Characteristics:**
- Domain-agnostic
- Works across all VFX tools
- Minimal tool-specific knowledge
- Template-based workflows

**When to use:**
- Code refactoring
- Documentation generation
- Testing and validation
- Template application

---

## Templates

**Location:** `ClaudeCode/templates/`

### Agent-Skill Template (Complete)
**Path:** `ClaudeCode/templates/agent-skill-template/`

**Contents:**
- SKILL.md structure (progressive disclosure)
- Python scripts (process, validate, export)
- Reference docs (API, patterns, troubleshooting)
- Agent file template
- README with usage

**How to use:**
1. Copy entire template to `.claude/skills/[skill-name]/`
2. Search/replace placeholders:
   - `{{SKILL_NAME}}` -> Your skill name
   - `{{TOOL_NAME}}` -> Tool/application (Unreal, Blender, etc.)
   - `{{WORKFLOW_TYPE}}` -> Workflow type (export, compile, validate)
3. Customize scripts for your workflow
4. Test independently before agent integration
5. Verify <500 lines SKILL.md

### Spec-Kit Templates
**Path:** `ClaudeCode/templates/spec-kit/`

**Available:**
- `spec-template.md` - Feature specification
- `plan-template.md` - Implementation plan
- `tasks-template.md` - Executable tasks
- `agent-file-template.md` - Agent definition
- `constitution-template.md` - Constitution structure

### VFX Skill Template
**Reference:** `ClaudeCode/templates/VFX_SKILL_TEMPLATE.md`

**Use for:**
- All new VFX skill creation
- Ensures constitutional compliance
- Standard structure across skills

---

## Helper Agents (Standardized)

### python-specialist
**Path:** `.claude/agents/python-specialist.md`

**Capabilities:**
- Template application (spec-kit templates)
- Type safety (mypy, type hints, protocols)
- Async programming (AsyncIO, concurrent.futures)
- Data science (pandas, numpy, vectorization)
- Testing (pytest, fixtures, parameterized tests)
- Security (input validation, .env loading)

**When to use:**
- Creating SKILL.md from templates
- Applying agent-skill-template
- Refactoring scripts for compliance
- Adding type hints and async

### testing-specialist
**Path:** `.claude/agents/testing-specialist.md`

**Capabilities:**
- Script validation (3+ assets/scenarios)
- JSON output verification
- Constitutional compliance testing
- Test report generation

**When to use:**
- Validating new scripts
- Testing skill discovery
- Integration testing
- Generating test reports

### documentation-specialist
**Path:** `.claude/agents/documentation-specialist.md`

**Capabilities:**
- README generation
- Progress tracking
- Session summaries
- Formatting consistency

**When to use:**
- Updating roadmaps
- Generating session summaries
- Maintaining documentation
- Updating CLAUDE.md

---

## Validation Scripts

**Location:** `ClaudeCode/development/scripts/`

### validate_skill.py
**Purpose:** Validate SKILL.md against VFX constitution

**Checks:**
- Line count <500 lines
- Frontmatter present with name + description
- Progressive disclosure structure
- Reference files for complex details
- Documentation standards

**Usage:**
```bash
python ClaudeCode/development/scripts/validate_skill.py \
  .claude/skills/unreal-plugin-compiler/

# Output: PASS/FAIL with violations
```

### check_constitutional_compliance.py
**Purpose:** Validate all agents/skills against VFX constitution

**Checks:**
- Article I: General purpose scripts (tested with 3+ projects)
- Article II: MCP vs Direct implementation choice
- Article III: Progressive disclosure (<500 lines)
- Article IV: Independent testing
- Article V: Official patterns followed
- Article VI: Context efficiency
- Article VII: Cross-application integration
- Article VIII: Documentation standards

**Usage:**
```bash
python ClaudeCode/development/scripts/check_constitutional_compliance.py

# Output: Compliance report by article
```

### validate_cross_app_workflow.py
**Purpose:** Validate export/import workflows across tools

**Checks:**
- File format compatibility
- Naming convention compliance
- Required validation steps present
- Round-trip testing documented

**Usage:**
```bash
python ClaudeCode/development/scripts/validate_cross_app_workflow.py \
  .claude/skills/houdini-unreal-export/

# Output: Workflow validation report
```
