# Agent Validation Rules Reference

**Purpose:** Detailed explanation of validation logic for Article IX compliance
**Constitutional Authority:** VFX_SKILL_CONSTITUTION.md Article IX (Agent Versioning and Naming Conventions)
**Validation Implementation:** `scripts/validate_agent.py`
**Version:** 1.0.0
**Last Updated:** 2025-10-25

---

## Table of Contents

1. [Article IX Compliance Matrix](#article-ix-compliance-matrix)
2. [Detailed Check Explanations](#detailed-check-explanations)
3. [Error Messages Guide](#error-messages-guide)
4. [Edge Cases](#edge-cases)
5. [Manual Override](#manual-override)
6. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Article IX Compliance Matrix

| Validation Check | Constitutional Reference | Purpose | Pass Example | Fail Example |
|-----------------|-------------------------|---------|-------------|--------------|
| **Filename Format** | Article IX, Section 9.1 | Ensure static names without version suffixes | `documentation-specialist.md` | `documentation-specialist-v2.md` |
| **Metadata Present** | Article IX, Section 9.3 | Verify required header fields exist | All 5 required fields present | Missing `version` field |
| **Name Matches Filename** | Article IX, Section 9.1 | Prevent agent name conflicts | filename: `blender-specialist.md`<br>name: `blender-specialist` | filename: `blender-specialist.md`<br>name: `blender_specialist` |
| **Version Format** | Article IX, Section 9.4 | Enforce semantic versioning | `2.0.0`, `1.5.3` | `v2.0`, `1.0`, `2.0.0-beta` |
| **Changelog Exists** | Article IX, Section 9.5 | Document version history for updates | Version 1.1.0+ with history section | Version 2.0.0 with no changelog |
| **Description Quality** | Article VIII, Section 8.2 | Ensure discoverable, specific descriptions | What + When + Triggers (50-200 chars) | "Helps with things" (vague) |

---

## Detailed Check Explanations

### 1. Filename Format Check

**Function:** `check_filename_format(filename: str)`

**What It Does:**
- Validates filename follows kebab-case pattern: `^[a-z0-9-]+\.md$`
- Detects version suffixes like `-v2`, `-v1.0`, `-v2.0.0`
- Rejects snake_case (`_`) and CamelCase patterns
- Ensures `.md` extension

**Why It's Required (Constitutional Reference):**
> **Article IX, Section 9.1:** "Agent filenames and internal names MUST match and remain static across versions."

Version information belongs in the YAML header metadata, NOT the filename. Multiple files with version suffixes (e.g., `agent-v1.md`, `agent-v2.md`) create confusion:
- Claude Code sees multiple agents with potentially the same internal name
- Unclear which is the active/current version
- Skills/workflows reference agents by name, not version
- Archiving protocol manages version history properly

**How to Fix Failures:**

**Problem:** Filename has version suffix
```bash
# WRONG:
.claude/agents/documentation-specialist-v2.md

# FIX:
# Step 1: Archive old version
cp .claude/agents/documentation-specialist.md \
   .claude/agents/archive/documentation-specialist-v1.0.md

# Step 2: Rename new version to static name
mv .claude/agents/documentation-specialist-v2.md \
   .claude/agents/documentation-specialist.md

# Step 3: Update version in header metadata
# Edit: .claude/agents/documentation-specialist.md
# Set: version: 2.0.0
```

**Problem:** Filename uses snake_case
```bash
# WRONG:
documentation_specialist.md

# FIX:
mv documentation_specialist.md documentation-specialist.md
# Also update internal name field to match
```

**Problem:** Filename uses CamelCase
```bash
# WRONG:
DocumentationSpecialist.md

# FIX:
mv DocumentationSpecialist.md documentation-specialist.md
# Also update internal name field to match
```

**Code Examples:**

```python
# GOOD (passes validation):
filename = "documentation-specialist.md"
# Pattern: lowercase letters, numbers, hyphens only
# No version suffix

# BAD (fails validation):
filename = "documentation-specialist-v2.md"  # Version suffix
filename = "documentation_specialist.md"    # Snake_case
filename = "DocumentationSpecialist.md"     # CamelCase
filename = "docs-specialist-1.0.md"         # Version suffix variant
```

---

### 2. Metadata Present Check

**Function:** `check_metadata_present(agent_content: str)`

**What It Does:**
- Extracts YAML frontmatter from agent file (between `---` delimiters)
- Validates presence of 5 required fields:
  - `name`: Agent identifier (must match filename)
  - `description`: What + When + Triggers
  - `version`: Semantic version (X.Y.Z)
  - `last_updated`: YYYY-MM-DD format
  - `status`: active | deprecated | experimental
- Validates `status` field contains only valid values

**Why It's Required (Constitutional Reference):**
> **Article IX, Section 9.3:** "Every agent MUST include required YAML frontmatter fields for discovery, lifecycle management, and integration."

Metadata enables:
- Agent discovery by Claude Code
- Version tracking and change management
- Lifecycle state management (active vs deprecated)
- Documentation currency validation

**How to Fix Failures:**

**Problem:** No YAML frontmatter found
```markdown
<!-- WRONG: No frontmatter -->
# My Agent

This is an agent...

<!-- FIX: Add frontmatter at start of file -->
---
name: my-agent
description: Does X when Y happens. Use for Z scenarios.
version: 1.0.0
last_updated: 2025-10-25
status: active
---

# My Agent

This is an agent...
```

**Problem:** Missing required fields
```yaml
# WRONG: Missing version and status
---
name: my-agent
description: Does stuff
last_updated: 2025-10-25
---

# FIX: Add all required fields
---
name: my-agent
description: Does stuff
version: 1.0.0          # ADD THIS
last_updated: 2025-10-25
status: active          # ADD THIS
---
```

**Problem:** Invalid status value
```yaml
# WRONG: Invalid status
---
name: my-agent
status: production  # Not a valid status
---

# FIX: Use valid status values
status: active       # For production-ready agents
status: experimental # For beta/testing agents
status: deprecated   # For superseded agents
```

**Code Examples:**

```yaml
# GOOD (passes validation):
---
name: documentation-specialist
description: Index-driven documentation updates for VFX projects. Use when updating session logs, maintaining indices, or syncing cross-references.
version: 2.0.0
last_updated: 2025-10-25
status: active
breaking_changes: true  # Optional field
---

# BAD (fails validation):
---
name: documentation-specialist
# Missing: description, version, last_updated, status
---
```

---

### 3. Name Matches Filename Check

**Function:** `check_name_matches_filename(filename: str, metadata_name: str)`

**What It Does:**
- Extracts base name from filename: `agent-name.md` → `agent-name`
- Compares with `name` field from YAML frontmatter
- Requires exact case-sensitive match

**Why It's Required (Constitutional Reference):**
> **Article IX, Section 9.1:** "Agent filenames and internal names MUST match and remain static across versions."

Mismatched names cause:
- Agent discovery failures (Claude Code searches by filename)
- Reference errors (Skills reference by metadata name)
- Confusion about which agent is which
- Integration breakage (workflow systems rely on name consistency)

**How to Fix Failures:**

**Problem:** Name mismatch
```yaml
# Filename: blender-specialist.md
# WRONG metadata:
---
name: blender_specialist  # Uses underscore instead of hyphen
---

# FIX: Match filename exactly
---
name: blender-specialist  # Matches filename (kebab-case)
---
```

**Problem:** Case mismatch
```yaml
# Filename: documentation-specialist.md
# WRONG metadata:
---
name: Documentation-Specialist  # Capitalized
---

# FIX: Use lowercase to match filename
---
name: documentation-specialist  # All lowercase
---
```

**Code Examples:**

```python
# GOOD (passes validation):
filename = "documentation-specialist.md"
metadata = {"name": "documentation-specialist"}
# Extracted: "documentation-specialist" == "documentation-specialist" ✅

# BAD (fails validation):
filename = "documentation-specialist.md"
metadata = {"name": "documentation_specialist"}
# Extracted: "documentation-specialist" != "documentation_specialist" ❌

filename = "blender-specialist.md"
metadata = {"name": "blender-specialist-v2"}
# Extracted: "blender-specialist" != "blender-specialist-v2" ❌
```

---

### 4. Version Format Check

**Function:** `check_version_format(version_string: str)`

**What It Does:**
- Validates version follows semantic versioning: `^\d+\.\d+\.\d+$`
- Requires exactly 3 numeric components separated by dots
- Rejects prefixes (`v1.0.0`), suffixes (`1.0.0-beta`), or 4-part versions (`1.0.0.0`)
- Parses version into major, minor, patch components

**Why It's Required (Constitutional Reference):**
> **Article IX, Section 9.4:** "Version numbering MUST follow semantic versioning format: MAJOR.MINOR.PATCH"

Semantic versioning enables:
- Clear communication of change impact (breaking vs features vs fixes)
- Automated dependency management
- Predictable upgrade paths
- Standardized version comparison

**Semantic Versioning Rules:**
- **MAJOR (X.0.0):** Breaking changes (incompatible changes)
- **MINOR (x.Y.0):** New features (backward compatible)
- **PATCH (x.y.Z):** Bug fixes (backward compatible)

**How to Fix Failures:**

**Problem:** Version has prefix
```yaml
# WRONG:
version: v2.0.0

# FIX:
version: 2.0.0  # Remove 'v' prefix
```

**Problem:** Version missing patch number
```yaml
# WRONG:
version: 1.0

# FIX:
version: 1.0.0  # Add patch number
```

**Problem:** Version has suffix
```yaml
# WRONG:
version: 1.0.0-beta
version: 1.0.0.rc1

# FIX:
version: 1.0.0  # Remove suffix (use status: experimental for beta)
```

**Problem:** Four-part version
```yaml
# WRONG:
version: 1.0.0.0

# FIX:
version: 1.0.0  # Use three parts only
```

**Code Examples:**

```python
# GOOD (passes validation):
"1.0.0"   # Initial release
"2.0.0"   # Major version (breaking changes)
"1.5.0"   # Minor version (new features)
"1.0.3"   # Patch version (bug fix)
"10.20.30"  # Large version numbers OK

# BAD (fails validation):
"v1.0.0"    # Has 'v' prefix
"1.0"       # Missing patch number
"1.0.0-beta"  # Has suffix
"1.0.0.0"   # Four parts
"1.0.0rc1"  # Release candidate suffix
```

**Version Increment Examples:**

```yaml
# Scenario 1: Bug fix (no API changes)
version: 1.0.0  # Current
version: 1.0.1  # Next (patch increment)

# Scenario 2: New feature (backward compatible)
version: 1.0.1  # Current
version: 1.1.0  # Next (minor increment, reset patch to 0)

# Scenario 3: Breaking change (incompatible API)
version: 1.5.3  # Current
version: 2.0.0  # Next (major increment, reset minor and patch to 0)
```

---

### 5. Changelog Exists Check

**Function:** `check_changelog_exists(agent_content: str, version_string: str)`

**What It Does:**
- Checks if version > 1.0.0 (v1.0.0 is exempt as initial release)
- Searches for `## Version History` section (case-insensitive)
- Extracts all version entries (format: `**v2.0.0**` or `**2.0.0**`)
- Validates at least 2 versions documented (current + previous)
- Verifies current version appears in changelog

**Why It's Required (Constitutional Reference):**
> **Article IX, Section 9.5:** "Every agent version > 1.0.0 MUST include version history documenting changes."

Changelogs enable:
- Understanding what changed between versions
- Migration planning for breaking changes
- Historical context for design decisions
- Team communication about updates

**How to Fix Failures:**

**Problem:** No changelog section (version > 1.0.0)
```markdown
<!-- WRONG: Version 1.1.0 with no changelog -->
---
version: 1.1.0
---

# My Agent

Content here...

<!-- FIX: Add Version History section -->
---
version: 1.1.0
---

# My Agent

Content here...

## Version History

**v1.1.0** (2025-10-25) - Enhanced Features
- Added: New capability for X
- Fixed: Bug in Y validation
- Improved: Performance in Z scenario

**v1.0.0** (2025-10-24) - Initial Release
- Initial agent implementation
- Core functionality for A, B, C
```

**Problem:** Changelog exists but missing current version
```markdown
<!-- WRONG: Current version 1.2.0 not in changelog -->
## Version History

**v1.1.0** (2025-10-20)
- Feature update

**v1.0.0** (2025-10-15)
- Initial release

<!-- FIX: Add current version entry -->
## Version History

**v1.2.0** (2025-10-25) - Bug Fix Release
- Fixed: Critical issue in X
- Updated: Documentation for Y

**v1.1.0** (2025-10-20)
- Feature update

**v1.0.0** (2025-10-15)
- Initial release
```

**Problem:** Only one version documented
```markdown
<!-- WRONG: Only current version listed -->
## Version History

**v1.1.0** (2025-10-25)
- Added new features

<!-- FIX: Include previous versions -->
## Version History

**v1.1.0** (2025-10-25) - Feature Addition
- Added: New feature X
- Improved: Y performance

**v1.0.0** (2025-10-24) - Initial Release
- Basic functionality
- Core features A, B, C
```

**Code Examples:**

```markdown
# GOOD (passes validation for v1.1.0+):
## Version History

**v2.0.0** (2025-10-25) - Major Rewrite
- BREAKING: Changed API from X to Y
- Added: Z functionality
- Removed: Deprecated feature W

**v1.1.0** (2025-10-20) - Feature Addition
- Added: New capability A
- Fixed: Bug in B

**v1.0.0** (2025-10-15) - Initial Release
- Initial implementation

# BAD (fails validation):
## Changelog  <!-- Wrong header name -->

v1.1.0 - Updates  <!-- Missing ** formatting -->
v1.0.0 - Initial

# GOOD (version 1.0.0 exempt from changelog requirement):
---
version: 1.0.0
---
# No Version History section needed for v1.0.0
```

---

### 6. Description Quality Check

**Function:** `check_description_quality(description: str)`

**What It Does:**
- Validates length: 10-300 characters (meaningful but concise)
- Detects vague phrases: "helps with", "does stuff", "manages things", "handles", "works with"
- Checks for trigger indicators: "use when", "use with", "triggers:", "for", "when"
- Ensures description is discoverable and actionable

**Why It's Required (Constitutional Reference):**
> **Article VIII, Section 8.2:** "Description MUST follow formula: What + When + Key Triggers"

Quality descriptions enable:
- Agent discovery (users find right agent for task)
- Automated agent selection (AI systems match intent to capability)
- Clear scope understanding (prevents misuse)
- Integration documentation (other systems understand purpose)

**Formula Breakdown:**
- **What:** Primary function/capability
- **When:** Usage scenarios/conditions
- **Triggers:** Keywords that indicate this agent should be used

**How to Fix Failures:**

**Problem:** Description too vague
```yaml
# BAD (vague, no triggers):
description: Helps with documentation

# GOOD (specific, clear triggers):
description: Index-driven documentation updates for VFX projects. Use when updating session logs, maintaining indices, or syncing cross-references.
```

**Problem:** Description too short
```yaml
# BAD (too short):
description: Docs

# GOOD (meets minimum length):
description: Documentation specialist for VFX pipeline projects. Use for session logs and index updates.
```

**Problem:** Description too long
```yaml
# BAD (350+ characters):
description: This agent is a comprehensive documentation management system that handles all aspects of documentation including creation, updating, maintenance, archiving, and cross-referencing across multiple applications in the VFX pipeline including Unreal Engine, Blender, Houdini, and Nuke while maintaining consistency...

# GOOD (concise, focused):
description: Index-driven documentation updates for VFX projects. Use when updating session logs, maintaining indices, or syncing cross-references across Unreal, Blender, Houdini, Nuke.
```

**Problem:** Missing trigger indicators
```yaml
# BAD (no "when" or "use" indicators):
description: Creates and updates documentation files for VFX projects.

# GOOD (includes trigger indicators):
description: Creates and updates documentation files for VFX projects. Use when creating session logs, updating indices, or maintaining cross-application references.
```

**Code Examples:**

```yaml
# EXCELLENT (passes all checks):
description: Compile Unreal Engine C++ plugins using UnrealBuildTool. Use when compiling plugins, fixing build errors, testing plugin compatibility, or when user mentions UE plugins, Visual Studio builds, .uplugin files, or module initialization errors.
# What: Compile UE C++ plugins
# When: compiling, fixing builds, testing compatibility
# Triggers: UE plugins, Visual Studio, .uplugin, module errors

# GOOD (clear and specific):
description: Procedural modeling with Blender Geometry Nodes. Use for asset scattering, terrain generation, or automated mesh variations. Triggers on node trees, procedural, scattering keywords.
# What: Geometry Nodes procedural modeling
# When: scattering, terrain, mesh variations
# Triggers: node trees, procedural, scattering

# BAD (vague language):
description: Helps with plugin stuff and handles compilation things
# Vague: "helps with", "handles"
# No clear triggers

# BAD (no triggers):
description: This agent compiles Unreal Engine plugins using UnrealBuildTool
# Missing: When to use, trigger keywords

# BAD (too technical, no usage context):
description: UnrealBuildTool wrapper with MSVC compiler integration
# Missing: When to use, user-facing scenarios
```

**Description Formula Template:**

```yaml
description: [Primary Function]. Use when [Scenario 1], [Scenario 2], or [Scenario 3]. Triggers: [keyword1], [keyword2], [keyword3].

# Example:
description: Blender MCP integration for Blender automation. Use when executing Python code, batch processing assets, or coordinating multi-application workflows. Triggers: blender mcp, execute blender code, bpy API.
```

---

## Error Messages Guide

### Filename Format Errors

**Error:** `Filename contains version suffix (use metadata instead)`
```
Cause: Filename like "agent-v2.md" or "agent-v1.0.0.md"
Fix: Remove version suffix from filename
     Archive old version to archive/ directory
     Use version field in metadata instead
```

**Error:** `Filename uses snake_case (use kebab-case instead)`
```
Cause: Filename like "my_agent.md"
Fix: Rename file to use hyphens: "my-agent.md"
     Update internal name field to match
```

**Error:** `Filename uses uppercase (use lowercase only)`
```
Cause: Filename like "MyAgent.md" or "My-Agent.md"
Fix: Rename file to all lowercase: "my-agent.md"
     Update internal name field to match
```

---

### Metadata Errors

**Error:** `No YAML frontmatter found (must start with ---)`
```
Cause: File doesn't start with YAML frontmatter
Fix: Add frontmatter at start of file:
     ---
     name: agent-name
     description: What it does
     version: 1.0.0
     last_updated: 2025-10-25
     status: active
     ---
```

**Error:** `Missing required fields: name, version`
```
Cause: YAML frontmatter missing required fields
Fix: Add all 5 required fields:
     - name
     - description
     - version
     - last_updated
     - status
```

**Error:** `Invalid status 'production' (must be: active, deprecated, experimental)`
```
Cause: Status field has invalid value
Fix: Use one of three valid statuses:
     status: active        # Production-ready
     status: experimental  # Beta/testing
     status: deprecated    # Superseded
```

---

### Name Matching Errors

**Error:** `Mismatch: filename=documentation-specialist, metadata=documentation_specialist`
```
Cause: Filename and internal name don't match
Fix: Make metadata name exactly match filename:
     Filename: documentation-specialist.md
     Metadata: name: documentation-specialist
```

---

### Version Format Errors

**Error:** `Version 'v2.0.0' must match X.Y.Z format (e.g., 2.0.0)`
```
Cause: Version has 'v' prefix
Fix: Remove prefix: version: 2.0.0
```

**Error:** `Version '1.0' must match X.Y.Z format (e.g., 2.0.0)`
```
Cause: Version missing patch number
Fix: Add patch number: version: 1.0.0
```

**Error:** `Version '1.0.0-beta' must match X.Y.Z format (e.g., 2.0.0)`
```
Cause: Version has suffix
Fix: Remove suffix: version: 1.0.0
     Use status: experimental for beta versions
```

---

### Changelog Errors

**Error:** `Version 1.1.0 requires '## Version History' section`
```
Cause: Version > 1.0.0 without changelog section
Fix: Add Version History section:
     ## Version History

     **v1.1.0** (2025-10-25)
     - Changes made

     **v1.0.0** (2025-10-24)
     - Initial release
```

**Error:** `Found 1 version(s), need at least 2 (current + previous)`
```
Cause: Changelog only lists current version
Fix: Add previous versions:
     **v1.1.0** (2025-10-25) - Current
     **v1.0.0** (2025-10-24) - Previous
```

**Error:** `Current version 1.1.0 not found in changelog`
```
Cause: Metadata version doesn't appear in changelog
Fix: Add current version entry to changelog:
     **v1.1.0** (2025-10-25)
     - Document changes
```

---

### Description Errors

**Error:** `Description too short (8 chars, need 10-300)`
```
Cause: Description less than 10 characters
Fix: Write meaningful description:
     What + When + Triggers formula
     Minimum 10 characters
```

**Error:** `Description too long (350 chars, need 10-300)`
```
Cause: Description exceeds 300 characters
Fix: Condense to essential information:
     Focus on primary function, key scenarios, main triggers
```

**Error:** `Description contains vague language: helps with, handles`
```
Cause: Using vague phrases instead of specific actions
Fix: Replace vague language:
     "helps with" → "compiles", "creates", "updates"
     "handles" → "manages", "processes", "executes"
     Be specific about what the agent does
```

**Error:** `Description should include trigger indicators (e.g., 'Use when', 'for')`
```
Cause: Missing usage scenarios or keywords
Fix: Add "when to use" information:
     "Use when [scenario1], [scenario2]"
     "Triggers: [keyword1], [keyword2]"
```

---

## Edge Cases

### Pre-1.0 Versions (0.x.x)

**Handling:** Experimental agents can use pre-1.0 versions

```yaml
# ALLOWED (experimental agent):
---
name: new-feature-agent
version: 0.1.0
status: experimental
---

# Validation behavior:
# - Changelog NOT required for 0.x.x versions
# - All other checks still apply
# - status: experimental recommended for 0.x.x
```

**Use Cases:**
- Prototype agents in development
- Beta features not yet production-ready
- Agents undergoing active testing

**Graduation to 1.0.0:**
```yaml
# When ready for production:
1. Test with 3+ real-world scenarios
2. Document all known limitations
3. Create validation checklist
4. Bump to 1.0.0
5. Change status: experimental → active
6. Add initial changelog entry
```

---

### Experimental Agents (status: experimental)

**Validation Differences:**
- All checks still apply (no exemptions)
- Version can be 0.x.x or 1.x.x
- Changelog required if version > 1.0.0 (even for experimental)
- Recommended to include `stability: unstable` optional field

```yaml
# GOOD (experimental agent):
---
name: experimental-feature
version: 0.5.0
status: experimental
stability: unstable
---

# Validation expectations:
# - Same filename, metadata, name checks
# - Same version format requirements
# - Changelog NOT required for 0.x.x
# - Description quality still enforced
```

**Documentation Requirements:**
```markdown
# Experimental Agent Name

**Status:** Experimental (Not Production Ready)

**Known Limitations:**
- Limitation 1
- Limitation 2
- Limitation 3

**Testing Status:** Tested with [X] scenarios
```

---

### Deprecated Agents (status: deprecated)

**Special Requirements:**
- Must include `deprecated_date` field
- Must include `replacement` field (if applicable)
- Should move to archive/ directory after deprecation notice period

```yaml
# GOOD (deprecated agent):
---
name: old-agent-name
version: 1.5.0  # Last active version
status: deprecated
deprecated_date: 2025-10-25
replacement: new-agent-name
---

# Old Agent Name (DEPRECATED)

**DEPRECATED:** Use `new-agent-name` instead.

**Reason:** [Why it was deprecated]
**Migration:** [How to switch to replacement]
**Archive Date:** 2025-11-25 (30 days after deprecation)
```

**Deprecation Workflow:**
```bash
# Step 1: Update agent with deprecation notice
# - Set status: deprecated
# - Add deprecated_date
# - Add replacement field
# - Update content with migration instructions

# Step 2: Wait deprecation notice period (30 days recommended)

# Step 3: Archive deprecated agent
mv .claude/agents/old-agent.md \
   .claude/agents/archive/old-agent-deprecated.md
```

**Validation Behavior:**
- All checks still apply
- No special exemptions for deprecated agents
- Changelog required if version > 1.0.0

---

### Breaking Changes (breaking_changes: true)

**When to Use:**
- Major version bumps (2.0.0, 3.0.0, etc.)
- Incompatible API changes
- Removed features
- Changed tool dependencies

```yaml
# GOOD (breaking change documentation):
---
name: agent-name
version: 2.0.0
status: active
breaking_changes: true  # Optional but recommended
---

## Version History

**v2.0.0** (2025-10-25) - Major Rewrite
- BREAKING: Changed from single-file to index-driven approach
- BREAKING: Removed support for deprecated format
- Added: Multi-application support
- Migration: See MIGRATION.md

**v1.5.0** (2025-10-20)
- Last version with old approach
```

**Documentation Requirements:**
```markdown
## Migration Guide (v1.x → v2.0)

**Breaking Changes:**
1. **Change 1:** What changed and why
   - **Old behavior:** Description
   - **New behavior:** Description
   - **Action required:** Migration steps

2. **Change 2:** What changed and why
   - **Old behavior:** Description
   - **New behavior:** Description
   - **Action required:** Migration steps

**Compatibility:**
- v2.0 NOT compatible with v1.x workflows
- Must update all references to new API
- Test thoroughly before deploying
```

---

## Manual Override (--force Flag)

**Usage:** `python validate_agent.py agent-name --force`

### When to Use --force

**Acceptable Scenarios:**

1. **Emergency Hotfix**
```bash
# Scenario: Critical bug in production agent
# Action: Fix bug, skip changelog for hotfix
python validate_agent.py agent-name --force
# Note: Update changelog in next regular release
```

2. **Migration in Progress**
```bash
# Scenario: Renaming agent during migration
# Action: Temporarily bypass name check while updating references
python validate_agent.py agent-name --force
# Note: Complete migration immediately
```

3. **Template/Example Files**
```bash
# Scenario: Creating documentation examples
# Action: Bypass validation for example files
python validate_agent.py example-agent --force
# Note: Mark clearly as example, not production agent
```

---

### When NOT to Use --force

**Dangerous Scenarios:**

1. **Production Agent Deployment**
```bash
# DON'T: Skip validation for production agents
python validate_agent.py production-agent --force  # WRONG

# DO: Fix validation errors properly
# - Update metadata to meet requirements
# - Add missing changelog entries
# - Fix description quality issues
```

2. **Avoiding Description Work**
```bash
# DON'T: Bypass description quality check
# Description: "Does stuff" + --force  # WRONG

# DO: Write meaningful description
# Description: "What + When + Triggers" formula
```

3. **Version Number Convenience**
```bash
# DON'T: Skip semantic versioning
version: v2.0 --force  # WRONG

# DO: Use proper semantic versioning
version: 2.0.0  # Correct format
```

---

### Risks of Bypassing Validation

**System-Level Risks:**
- Agent discovery failures (Claude Code can't find agent)
- Integration breakage (workflows reference wrong name/version)
- Team confusion (unclear which version is active)
- Documentation debt (missing changelogs accumulate)

**Production Risks:**
- Silent failures (vague descriptions prevent proper agent selection)
- Version conflicts (multiple agents with same name)
- Migration issues (breaking changes undocumented)
- Maintenance burden (validation debt compounds over time)

**Best Practice:**
```bash
# Step 1: Run validation WITHOUT --force
python validate_agent.py agent-name

# Step 2: Fix all reported violations
# - Update filename
# - Add missing metadata
# - Write quality description
# - Add changelog for v1.1.0+

# Step 3: Re-validate (should pass)
python validate_agent.py agent-name  # No --force needed

# Step 4: Deploy with confidence
# All constitutional requirements met
```

---

## Troubleshooting Common Issues

### Issue 1: "My agent has documentation-specialist-v2.md filename"

**Problem:** Version suffix in filename violates Article IX, Section 9.1

**Solution:**
```bash
# Step 1: Archive current version (if exists)
cp .claude/agents/documentation-specialist.md \
   .claude/agents/archive/documentation-specialist-v1.0.md

# Step 2: Rename new version to static name
mv .claude/agents/documentation-specialist-v2.md \
   .claude/agents/documentation-specialist.md

# Step 3: Verify metadata
# Open: .claude/agents/documentation-specialist.md
# Check: name: documentation-specialist (no version)
# Check: version: 2.0.0 (in metadata)

# Step 4: Validate
python validate_agent.py documentation-specialist
# Should pass: ✅ Filename Format
```

---

### Issue 2: "Version format error with 1.0"

**Problem:** Version missing patch number (must be X.Y.Z)

**Solution:**
```yaml
# WRONG:
version: 1.0

# CORRECT:
version: 1.0.0  # Add .0 for patch number

# Other examples:
version: 2.1      # WRONG
version: 2.1.0    # CORRECT

version: v1.0.0   # WRONG (has 'v' prefix)
version: 1.0.0    # CORRECT (no prefix)
```

---

### Issue 3: "Changelog required but I just created this"

**Problem:** Version 1.1.0+ requires changelog, but this is a new agent

**Solution:**

**Scenario A:** Truly new agent (first time creating)
```yaml
# Use version 1.0.0 for initial release
# Changelog NOT required for v1.0.0

---
version: 1.0.0  # Initial release
status: active
---

# No Version History section needed yet
```

**Scenario B:** Updated existing agent to 1.1.0+
```yaml
# Must add Version History section

---
version: 1.1.0
---

## Version History

**v1.1.0** (2025-10-25) - Feature Addition
- Added: New capability X
- Fixed: Bug in Y

**v1.0.0** (2025-10-24) - Initial Release
- Initial implementation
- Core features A, B, C
```

---

### Issue 4: "Description too vague"

**Problem:** Description fails quality check (vague language, no triggers)

**Solution:**

**Bad Description Analysis:**
```yaml
description: Helps with plugin compilation stuff
# Issues:
# - "Helps with" (vague)
# - "stuff" (vague)
# - No "when" scenarios
# - No trigger keywords
```

**Good Description Rewrite:**
```yaml
description: Compile Unreal Engine C++ plugins using UnrealBuildTool. Use when compiling plugins, fixing build errors, or testing plugin compatibility. Triggers: .uplugin files, module errors, Visual Studio builds.

# Formula breakdown:
# What: Compile UE C++ plugins using UnrealBuildTool
# When: compiling plugins, fixing build errors, testing compatibility
# Triggers: .uplugin, module errors, VS builds
```

**Template to Fix Vague Descriptions:**
```yaml
# Step 1: Identify primary function (WHAT)
What: [Primary action + target]

# Step 2: List 2-3 usage scenarios (WHEN)
When: [Scenario 1], [Scenario 2], [Scenario 3]

# Step 3: List trigger keywords (TRIGGERS)
Triggers: [keyword1], [keyword2], [keyword3]

# Step 4: Combine into description
description: [What]. Use when [When]. Triggers: [Triggers].
```

---

### Issue 5: "Name mismatch error"

**Problem:** Filename and internal name don't match exactly

**Solution:**

**Common Mismatch Patterns:**
```bash
# Pattern 1: Underscore vs Hyphen
Filename: blender-specialist.md
Metadata: name: blender_specialist
FIX: Change metadata to: name: blender-specialist

# Pattern 2: Capitalization
Filename: documentation-specialist.md
Metadata: name: Documentation-Specialist
FIX: Change metadata to: name: documentation-specialist

# Pattern 3: Version in name
Filename: agent-name.md
Metadata: name: agent-name-v2
FIX: Change metadata to: name: agent-name

# Pattern 4: Extra words
Filename: python-specialist.md
Metadata: name: python-specialist-agent
FIX: Change metadata to: name: python-specialist
OR rename file to: python-specialist-agent.md
```

**Validation Command:**
```bash
# Test name matching
python validate_agent.py agent-name

# Should see:
# ✅ Name Matches Filename: agent-name == agent-name
```

---

### Issue 6: "Multiple versions in changelog but current not found"

**Problem:** Changelog exists but current version not documented

**Solution:**
```markdown
# Current metadata:
version: 1.2.0

# WRONG changelog:
## Version History

**v1.1.0** (2025-10-20)
- Previous changes

**v1.0.0** (2025-10-15)
- Initial release

# FIX: Add current version entry
## Version History

**v1.2.0** (2025-10-25) - Current Version
- Added: Feature X
- Fixed: Bug in Y
- Updated: Documentation

**v1.1.0** (2025-10-20)
- Previous changes

**v1.0.0** (2025-10-15)
- Initial release
```

---

## Reference Implementation

**Validation Script:** `scripts/validate_agent.py`

**Key Functions:**
- `check_filename_format()` - Lines 31-86
- `check_metadata_present()` - Lines 88-162
- `check_name_matches_filename()` - Lines 164-197
- `check_version_format()` - Lines 199-236
- `check_changelog_exists()` - Lines 238-307
- `check_description_quality()` - Lines 309-371

**Constitutional Authority:**
- VFX_SKILL_CONSTITUTION.md
- Article IX: Agent Versioning and Naming Conventions
- Article VIII, Section 8.2: Description Writing Guidelines

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-25
**Validation Script Version:** Matches validate_agent.py implementation
**Constitutional Version:** VFX_SKILL_CONSTITUTION.md v1.1.0
