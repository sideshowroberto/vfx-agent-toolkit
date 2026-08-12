---
name: development-management
description: Specification-Driven Development (SDD) workflows for VFX pipeline using spec-kit methodology. Covers agent creation, constitutional governance, roadmaps, specs, and validation. Use when user requests development work, agent audits, skill creation, constitutional compliance checks, or mentions 'how do I create agent', 'audit agents', 'spec-kit', 'development process', 'validate this', 'create constitution', 'governance rules'.
allowed-tools: Read,Write,Edit
---

# Development Management

**Version:** 1.0.0
**Last Updated:** 2025-12-03
**Status:** Production-ready
**Dependencies:** VFX_SKILL_CONSTITUTION.md v2.0.0, spec-kit templates

**Purpose:** Specification-Driven Development workflows using spec-kit methodology adapted for VFX pipeline

**Framework:** Spec-kit SDD (Specification -> Plan -> Tasks -> Implementation)

**For VFX Tools:** Unreal Engine, Blender, Houdini, Nuke, ComfyUI, Python

---

## Quick Start - Most Common Workflows

### "How do I create a new agent?"

**Use spec-kit SDD workflow:**

1. **Specify** - Define what agent does
   - Template: `ClaudeCode/templates/agent-skill-template/`
   - Constitution check: Does it follow VFX_SKILL_CONSTITUTION.md?
   - Save spec: `ClaudeCode/development/specs/agents/AGENT_NAME_SPEC.md`

2. **Plan** - Create implementation plan
   - Template: `ClaudeCode/templates/spec-kit/plan-template.md`
   - Constitutional gates: Articles I-VIII compliance
   - Save plan: `ClaudeCode/development/roadmaps/AGENT_NAME_PLAN.md`

3. **Tasks** - Generate executable tasks
   - Break down into parallelizable steps
   - Use helper agents (python-specialist, testing-specialist, documentation-specialist)
   - Track: Use TodoWrite tool

4. **Implement** - Execute with agent orchestration
   - Parallel: Independent agent creation (5 max per batch)
   - Sequential: Testing after creation, documentation after testing
   - Validate: Constitutional compliance at each phase

### "Audit agents for skill creation"

**Workflow:**
1. **List agent files** -> `.claude/agents/*.md`
2. **Read all agent files** -> Analyze tool usage, dependencies
3. **Analyze against criteria** -> Skill readiness, constitutional compliance
4. **Generate documents:**
   - Spec: `ClaudeCode/development/specs/SKILL_CREATION_SPEC.md`
   - Plan: `ClaudeCode/development/roadmaps/SKILL_CREATION_PLAN.md`
   - Checklist: `ClaudeCode/development/checklists/SKILL_CREATION_CHECKLIST.md`
   - Report: `ClaudeCode/development/reports/AGENT_AUDIT_REPORT.md`

### "Validate constitutional compliance"

**Run validation scripts:**
```bash
python3 ClaudeCode/development/scripts/validate_skill.py .claude/skills/SKILL_NAME/
python3 ClaudeCode/development/scripts/check_constitutional_compliance.py
```

**Manual checks:**
- [ ] SKILL.md <500 lines (Article III: Progressive Disclosure)
- [ ] General purpose scripts (Article I: One Script All Assets/Projects)
- [ ] Test independently (Article IV: Test Before Agent Integration)
- [ ] Follow official patterns (Article V: Official Tool/Engine Patterns)
- [ ] Context efficient (Article VI: Context Efficiency)
- [ ] Cross-app integration (Article VII: Cross-Application Protocol)
- [ ] Documentation standards (Article VIII: Documentation)

---

## Spec-Kit SDD Framework

**Philosophy:** Specifications generate code, not the other way around

**Three-Phase Workflow:**

### Phase 1: Specify (What + Why)
- **Purpose:** Define WHAT users need and WHY
- **Focus:** Business requirements, user stories, acceptance criteria
- **Avoid:** HOW to implement (no tech stack, APIs, code structure)
- **Output:** Specification document

**Template:** Use existing specs as examples:
- Agent specs: `live-data/development/specs/agents/`
- Feature specs: `live-data/development/specs/WEEK*_*.md`
- Command specs: `live-data/development/specs/commands/`

**Key Sections:**
```markdown
# [Feature/Agent Name] Specification

**Date:** YYYY-MM-DD
**Scope:** Brief description
**Constitutional Compliance:** List articles

## Purpose
[What and why]

## Requirements
[Functional requirements]

## User Stories
[As a... I want... So that...]

## Acceptance Criteria
[Testable success criteria]

## Non-Functional Requirements
[Performance, security, scalability]

## Success Metrics
[How do we know it worked?]
```

### Phase 2: Plan (How)
- **Purpose:** Define HOW to implement
- **Focus:** Technical architecture, implementation details, phases
- **Include:** Technology choices with rationale, constitutional gates
- **Output:** Implementation plan

**Template:** `live-data/development/spec-kit_files/templates/plan-template.md`

**Key Sections:**
```markdown
# [Feature/Agent Name] Implementation Plan

## Quick Reference
[Links to spec, constitution, checklist]

## Constitutional Gates (Pre-Implementation)
[Article-by-article compliance checks]

## Technical Approach
[Architecture, patterns, technologies]

## Implementation Phases
[Phase 0, 1, 2... with deliverables]

## Agent Orchestration
[Parallel vs sequential execution]

## Testing Strategy
[Unit, integration, validation]

## Validation
[Success criteria, rollback plan]
```

### Phase 3: Tasks (Executable Breakdown)
- **Purpose:** Break plan into parallelizable tasks
- **Focus:** Concrete steps, dependencies, agent assignments
- **Output:** Task list with [P] parallel markers

**Template:** `live-data/development/spec-kit_files/templates/tasks-template.md`

**Agent Orchestration Principles:**
- Max 5 agents per parallel batch
- Sequential for dependent tasks
- Use TodoWrite to track progress
- Wait for batch completion before next phase

---

## Constitutional Governance

### Primary Constitution
**Location:** `ClaudeCode/development/VFX_SKILL_CONSTITUTION.md`

**8 Core Articles:**
1. **General Purpose Scripts** - ONE script for ALL projects/assets
2. **MCP vs Direct Implementation** - Choose right tool for task
3. **Progressive Disclosure** - SKILL.md <500 lines
4. **Test Independently** - Before agent integration
5. **Follow Official Patterns** - Match tool/engine examples
6. **Context Efficiency** - Minimize context at every level
7. **Cross-Application Integration** - Standard formats, naming, validation
8. **Documentation Standards** - Consistent, discoverable, maintainable

### Secondary Constitutions
**Location:** `ClaudeCode/development/constitutions/` (if needed)

**Creating project-specific constitutions:**
- For Unreal-specific workflows
- For Blender addon development
- For Houdini HDA pipelines

**Creating New Constitution:**

1. **Use template:** `ClaudeCode/templates/spec-kit/constitution_template.md`
2. **Adapt for domain:** Replace placeholders with specific rules
3. **Define articles:** Core principles (I-VIII typically)
4. **Add governance:** Amendment process, version tracking
5. **Create checklist:** Update `ClaudeCode/development/checklists/`
6. **Save:** `ClaudeCode/development/constitutions/[SCOPE]_CONSTITUTION.md`

**Structure:**
```markdown
# [Scope] Constitution

## Core Principles

### Article I: [Principle Name]
[Description, requirements, violations]

### Article II: [Principle Name]
[Description, requirements, violations]

...

## Enforcement
[Pre-commit checklist, violation consequences]

## Governance
[Amendment process, version tracking]

**Version:** X.Y.Z | **Ratified:** YYYY-MM-DD
```

### Constitutional Update Checklist
**Reference:** `ClaudeCode/development/VFX_SKILL_UPDATE_CHECKLIST.md`

**When amending constitution:**
- [ ] Update all templates referencing changed articles
- [ ] Update CLAUDE.md if runtime guidance affected
- [ ] Update checklists for new requirements
- [ ] Increment version number
- [ ] Document amendment rationale
- [ ] Test sample implementation for compliance

---

## Agent Architecture Patterns

**For detailed patterns, see:** `reference/detailed-reference.md`

**Three Patterns:**
1. **Tool-Specific Specialists** - Deep expertise (Blender, Unreal specialists)
2. **Cross-Tool Pipeline** - Multi-app coordination (export/import workflows)
3. **General Purpose Helpers** - Domain-agnostic (python-specialist, testing-specialist)

---

## Templates

**For detailed template usage, see:** `reference/detailed-reference.md`

**Available at** `ClaudeCode/templates/`:
- **agent-skill-template/** - Complete skill structure with scripts
- **spec-kit/** - Spec, plan, tasks, agent, constitution templates
- **VFX_SKILL_TEMPLATE.md** - Standard skill structure

---

## Helper Agents (Standardized)

**For detailed capabilities, see:** `reference/detailed-reference.md`

**Available Agents:**
- **python-specialist** - Template application, type safety, async, testing
- **testing-specialist** - Script validation, JSON verification, compliance testing
- **documentation-specialist** - README generation, progress tracking, summaries

---

## Parallel Agent Orchestration

**Principle:** Parallelize independent tasks, sequence dependent tasks

**Patterns:**
- **Parallel (Single Message):** Launch independent agents simultaneously (max 5/batch)
- **Sequential (Wait Between):** Create -> Test -> Document (wait for completion between phases)

**Rules:** Max 5 agents/batch, wait for completion, use TodoWrite, no dependent tasks in parallel

---

## Validation Scripts

**For detailed validation info, see:** `reference/detailed-reference.md`

**Location:** `ClaudeCode/development/scripts/`

**Available Scripts:**
- **validate_skill.py** - SKILL.md constitutional validation
- **check_constitutional_compliance.py** - All agents/skills compliance report
- **validate_cross_app_workflow.py** - Export/import workflow validation

---

## Roadmaps & Progress Tracking

**Location:** `ClaudeCode/development/roadmaps/` and project-specific

### ACTIVE_ROADMAP.md (Master Roadmap)
**Structure:**
```markdown
# Active Roadmap

## [OK] COMPLETED - [Phase Name]
**Scope:** Brief description
**Effort:** Time estimate
**Outcome:** Results achieved
**Next:** Link to next phase

## IN PROGRESS - [Current Phase]
**Scope:** What we're building
**Status:** Current step
**Blockers:** Issues if any
**ETA:** Estimated completion

## PLANNED - [Future Phase]
**Priority:** High/Medium/Low
**Dependencies:** What must complete first
**Effort:** Time estimate
```

### Individual Roadmaps
**Pattern:** `[FEATURE]_PLAN.md` or `[FEATURE]_ROADMAP.md`

**Examples:**
- `UNREAL_MCP_ENHANCEMENT_PLAN.md`
- `BLENDER_PIPELINE_ROADMAP.md`
- `SKILL_CREATION_PLAN.md`

### Progress Tracking
**After completing work:**
1. Update ACTIVE_ROADMAP.md (mark phase completed)
2. Create session summary in project `development/` directory
3. Update relevant specs/plans with final metrics
4. Document key decisions in ADRs (if architectural)

---

## Session Summaries

**Location:** Project-specific `development/` directories
**Pattern:** `Session_YYYY-MM-DD_Description.md`

**Template:**
```markdown
# Session Summary - [Date] - [Topic]

**Duration:** X hours over Y days
**Agents Used:** [List with counts]
**Project:** [Unreal, Blender, etc.]

## What We Built
- [Major deliverables]
- [Key features]

## Key Decisions
- [Architectural choices]
- [Tradeoffs made]
- [Constitutional amendments]

## Metrics
- [Quantitative results]
- [Before/after comparisons]
- [Test pass rates]

## Files Created/Modified
[List with purposes]

## Lessons Learned
- What worked well
- What didn't work
- Gotchas to remember

## Next Steps
[Immediate follow-ups]

## References
[Links to related docs, sessions, skills]
```

---

## Common Workflows

**All follow Spec-Kit SDD:** Specify -> Plan -> Tasks -> Implement -> Validate

**Three Patterns:**
1. **Create New VFX Skill** - Copy template, create scripts, write SKILL.md (<500 lines), test 3+ projects
2. **Enhance Unreal MCP** - Add C++ handler, Python wrapper, test, document in MCP_Capabilities_UE55.md
3. **Create Cross-Tool Pipeline** - Export script, validation, round-trip testing with 3+ asset types

---

## Troubleshooting

**Constitutional violations:** Run validate_skill.py or check_constitutional_compliance.py | **Agent not loading:** Check YAML frontmatter format | **Script failures:** Test independently before agent integration | **Template errors:** Verify placeholders replaced

---

## Natural Language Examples

**These phrases trigger this skill:**

- "How do I create a new agent?"
- "Audit agents for plugin conversion"
- "Validate constitutional compliance"
- "What's the development process?"
- "How do I use spec-kit?"
- "Create a new constitution for [scope]"
- "Update the roadmap"
- "Generate a session summary"
- "Check agent tool usage"
- "What templates are available?"

---

## References

**VFX Constitution & Guides:**
- Primary Constitution: `ClaudeCode/development/VFX_SKILL_CONSTITUTION.md`
- Skills Guide: `ClaudeCode/development/VFX_AGENT_SKILLS_GUIDE.md`
- Skills Overview: `ClaudeCode/development/VFX_SKILLS_SYSTEM_OVERVIEW.md`
- Update Checklist: `ClaudeCode/development/VFX_SKILL_UPDATE_CHECKLIST.md`

**Templates:**
- Skill Template: `ClaudeCode/templates/VFX_SKILL_TEMPLATE.md`
- Agent-Skill Template: `ClaudeCode/templates/agent-skill-template/`
- Spec-Kit Templates: `ClaudeCode/templates/spec-kit/`
- Trading Constitution (reference): `ClaudeCode/templates/SKILL_CONSTITUTION.md`

**Project Documentation:**
- CLAUDE.md: Project instructions and context
- Unreal MCP Capabilities: `UnrealEngine/unreal-mcp-main/MCP_Capabilities_UE55.md`
- Unreal MCP Development: `UnrealEngine/unreal-mcp-main/development/`

**Tool-Specific:**
- Unreal session logs: `UnrealEngine/unreal-mcp-main/development/Session_*.md`
- Houdini workflows: `Houdini/[project]/development/`
- Blender workflows: `Blender/[project]/development/`

---

**Version:** 1.0 (VFX Adapted)
**Last Updated:** October 24, 2025
**Framework:** Spec-Kit SDD adapted for VFX pipeline
**Adapted From:** Trading intelligence development-management skill
**Maintainer:** development-management skill

## Reference Documentation

**For detailed information, see:** `reference/detailed-reference.md`

**Primary Sources:**
- VFX_SKILL_CONSTITUTION.md
- VFX_AGENT_SKILLS_GUIDE.md
- Templates in `ClaudeCode/templates/`

---

## Constitutional Compliance

**Version:** VFX_SKILL_CONSTITUTION.md v2.0.0

**Article I - General Purpose Scripts:**
- [OK] All templates and workflows are project-agnostic
- [OK] Spec-kit SDD works across all VFX tools

**Article III - Progressive Disclosure:**
- [OK] SKILL.md: 490 lines (2% buffer)
- [OK] Reference file: detailed-reference.md for patterns/templates/validation

**Article VI - Context Efficiency:**
- [OK] Context reduction: 31% (713 -> 490 lines)
- [OK] Progressive disclosure through reference files

**Article VII - Cross-App Integration:**
- [OK] Works with all VFX applications (Unreal, Blender, Houdini, Nuke)
- [OK] Cross-tool pipeline patterns documented

**Article VIII - Documentation Standards:**
- [OK] Complete YAML frontmatter
- [OK] Version, Status, Dependencies documented
- [OK] Troubleshooting section present
- [OK] Constitutional compliance section present

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-03 | Initial VFX-adapted version with Article III compliance |

