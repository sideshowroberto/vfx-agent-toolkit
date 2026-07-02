# Skill Template Guide

**Purpose:** Comprehensive guide to using VFX_SKILL_TEMPLATE.md for creating production-ready Agent Skills

**Last Updated:** 2025-10-25
**Template Version:** 1.0.0
**Skill Creation Tool:** skill-creation-update

---

## Table of Contents

1. [Template Overview](#template-overview)
2. [Placeholder Reference](#placeholder-reference)
3. [Section-by-Section Guidelines](#section-by-section-guidelines)
4. [Progressive Disclosure Strategies](#progressive-disclosure-strategies)
5. [Line Count Management](#line-count-management)
6. [Examples from Production Skills](#examples-from-production-skills)
7. [Quick Reference](#quick-reference)

---

## Template Overview

### Purpose

The VFX_SKILL_TEMPLATE.md provides a standardized structure for creating Agent Skills that:
- Follow constitutional principles (all 9 articles)
- Maintain consistency across VFX applications
- Support progressive disclosure (<500 lines)
- Serve both humans and AI agents
- Enable team collaboration

### Template Structure

**Total Template Size:** ~400 lines (leaves 100 lines for customization)

```markdown
YAML Frontmatter (4 lines)
  ↓
Critical First Step (20 lines)
  ↓
Quick Start (80 lines)
  ↓
Standard Workflows (120 lines) - 3 workflows recommended
  ↓
Advanced Techniques (60 lines)
  ↓
Script Reference (60 lines)
  ↓
Troubleshooting (80 lines) - 3-5 issues recommended
  ↓
Reference Documentation (20 lines)
  ↓
Validation Checklist (30 lines)
  ↓
Output Standards (40 lines)
  ↓
Version History (10 lines)
```

### Automated vs Manual Filling

**Automated by create_skill.py:**
- YAML frontmatter (name, description, triggers, model)
- Skill name header
- Version (1.0.0)
- Date (current date)
- Basic structure (sections with headers)

**Manual customization required:**
- Critical first step content
- Quick Start workflow
- Standard Workflows (3-5 patterns)
- Advanced techniques
- Script documentation
- Troubleshooting issues
- Reference doc descriptions
- Validation checklist items

---

## Placeholder Reference

### All Placeholders Explained

**YAML Frontmatter:**
```yaml
{{SKILL_NAME}}           # kebab-case: unreal-vfx-automation, houdini-hda-export
{{DESCRIPTION}}          # What + When + Triggers (see Description Formula)
{{MODEL}}                # sonnet or haiku (default: sonnet)
```

**Header Metadata:**
```markdown
{{DATE}}                           # YYYY-MM-DD (auto-filled)
{{LIST_ALL_REQUIRED_SOFTWARE}}     # UE 5.5+, Houdini 20+, Python 3.12+
{{STATUS}}                         # Development / Testing / Production Ready
```

**Critical First Step:**
```markdown
{{REQUIRED_TOOL}}                  # UnrealEditor, Houdini, Blender
{{REASON_1/2/3}}                   # Why this check is critical
{{EXPLANATION}}                    # Detailed explanation of risk
```

**Quick Start:**
```markdown
{{WHAT_USER_WANTS_TO_ACCOMPLISH}}  # High-level goal
{{CHECK_COMMAND_1/2}}              # Prerequisite validation commands
{{VALIDATION_COMMAND}}             # Verify structure/files
{{MAIN_COMMAND}}                   # Primary operation
{{VERIFICATION_COMMAND}}           # Check success
{{EXAMPLE_SUCCESS_OUTPUT}}         # Expected result
```

**Standard Workflows:**
```markdown
{{COMMON_PATTERN_NAME}}            # Basic Foreground Plate Setup
{{WHEN_TO_USE_THIS_WORKFLOW}}      # Scenario description
{{STEP_N_NAME}}                    # Descriptive step name
{{STEP_N_COMMAND}}                 # Executable command
{{STEP_N_EXPLANATION}}             # Why this step matters
{{CRITERION_N}}                    # Success checklist item
```

**Advanced Techniques:**
```markdown
{{ADVANCED_PATTERN_NAME}}          # Multi-Shot Production Pipeline
{{PARAM_N}}                        # Parameter name
{{DESCRIPTION}}                    # Parameter description
{{HOW_TO_READ_RESULTS}}            # Output interpretation
{{WHAT_TO_LOOK_FOR}}               # Key indicators
{{WHEN_TO_ACT_ON_FINDINGS}}        # Action triggers
```

**Script Reference:**
```markdown
{{SCRIPT_NAME}}                    # export_hda, compile_plugin
{{WHAT_THIS_SCRIPT_DOES}}          # One-sentence purpose
{{REQUIRED_PARAM}}                 # Mandatory argument
{{OPTIONAL_PARAM}}                 # Optional argument
{{DEFAULT_VALUE}}                  # Default if param omitted
{{OUTPUT_FORMAT}}                  # JSON, structured text, etc.
```

**Troubleshooting:**
```markdown
{{COMMON_ERROR_NAME}}              # DLL Locking During Build
{{WHAT_USER_SEES_N}}               # Error message or behavior
{{WHY_IT_HAPPENS}}                 # Root cause explanation
{{FIX_COMMAND}}                    # Solution command/steps
{{HOW_TO_AVOID_THIS_ISSUE}}        # Prevention strategy
```

**Reference Documentation:**
```markdown
{{REFERENCE_N_NAME}}               # API Reference, Build Requirements
{{filename}}                       # api_reference, build_requirements
{{WHAT_IT_CONTAINS_N}}             # Content description
```

**Validation Checklist:**
```markdown
{{OPERATION}}                      # Plugin compilation, HDA export
{{EXAMPLE}}                        # Concrete example
{{WHAT_TO_CHECK}}                  # Specific verification target
```

**Output Standards:**
```markdown
{{KEY_METRIC_N}}                   # Build time, file count
{{VALUE}}                          # Actual value
{{PATH}}                           # Output location
{{WHAT_TO_DO_NEXT}}                # Next steps
{{ERROR_MESSAGE}}                  # Actual error text
{{LIKELY_CAUSE}}                   # Probable reason
{{HOW_TO_FIX}}                     # Solution
{{TROUBLESHOOTING_SECTION}}        # Link to relevant section
```

**Version History:**
```markdown
{{FEATURE_N}}                      # Initial implementation feature
{{YOUR_TEAM}}                      # Team or individual name
{{SOFTWARE_VERSIONS}}              # Tested versions
```

---

## Section-by-Section Guidelines

### YAML Frontmatter

**Purpose:** Enable skill discovery and triggering

**Required Fields:**
```yaml
---
name: skill-name              # MUST match directory name
description: ...              # MUST follow "What + When + Triggers" formula
triggers:                     # Optional: explicit trigger phrases
  - "trigger phrase 1"
  - "trigger phrase 2"
model: sonnet                 # sonnet or haiku
---
```

**Description Formula: What + When + Triggers**

**Components:**
1. **What:** Primary function (1 sentence)
2. **When:** Key scenarios (2-3 examples)
3. **Triggers:** Natural language phrases users say

**Examples:**

**Bad (vague):**
```yaml
description: Helps with Unreal plugins
```

**Good (specific):**
```yaml
description: Compile Unreal Engine C++ plugins using UnrealBuildTool. Use when compiling plugins, fixing build errors, testing plugin compatibility, or when user mentions UE plugins, Visual Studio builds, .uplugin files, or module initialization errors.
```

**Good (multi-app):**
```yaml
description: Automate VFX workflows in Unreal Engine 5.5 including foreground plates, image sequences, and multi-shot production. Use when setting up ImagePlate, creating foreground plates, batch processing shots, or when user mentions "unreal foreground plate", "image sequence", "vfx set extension", "imageplate setup".
```

**Trigger Phrases Best Practices:**
- 3-7 triggers recommended (not exhaustive)
- Mix technical terms ("imageplate") and natural language ("set up foreground plate")
- Include abbreviations/acronyms if common
- Test with actual user language

---

### Critical First Step Section

**Purpose:** Prevent catastrophic failures (DLL locking, data loss, version conflicts)

**When to Include:**
- Build systems (check editor closed)
- File operations (verify backups)
- Version-specific code (check compatibility)
- Multi-step dependencies (validate prerequisites)

**When to Skip:**
- Documentation-only skills
- Read-only operations
- Simple queries

**Template:**
```markdown
## CRITICAL: MANDATORY FIRST STEP

**ALWAYS verify prerequisites before execution:**
```bash
# Example check
tasklist | findstr "UnrealEditor"
```

**Why Critical:**
- Reason 1: Prevents DLL locking (build will fail)
- Reason 2: Avoids data corruption
- Reason 3: Ensures compatible environment
```

**Example (Unreal Plugin Compilation):**
```markdown
## CRITICAL: MANDATORY FIRST STEP

**ALWAYS verify Unreal Editor is CLOSED before compiling:**
```bash
tasklist | findstr "UnrealEditor"
# Expected: No output (editor not running)
```

**Why Critical:**
- DLL Locking: Running editor locks plugin DLLs, build WILL fail
- Wasted Build Time: 2-5 minutes wasted before failure
- False Errors: DLL locking causes misleading error messages
```

**Example (Cross-App Export):**
```markdown
## CRITICAL: MANDATORY FIRST STEP

**ALWAYS verify target application version compatibility:**
```bash
# Check Unreal Engine version
cat MyProject.uproject | grep "EngineAssociation"
# Expected: "5.5" or later

# Check Houdini version
hython --version
# Expected: 20.0 or later
```

**Why Critical:**
- HDAs compiled for UE 5.5 won't work in UE 4.27
- Material nodes differ between Houdini 19.5 and 20.0
- Wasted iteration time (30+ minutes to discover incompatibility)
```

---

### Quick Start Section

**Purpose:** Get users to success in <5 minutes with copy-paste ready commands

**Structure:**
```markdown
## Quick Start

### Most Common Use Case

**Goal:** [What user wants to accomplish]

**Step 1: Validate Environment**
[Prerequisite checks - copy-paste ready]

**Step 2: Prepare Assets/Files**
[Setup commands]

**Step 3: Execute Main Operation**
[Primary command with all required parameters]

**Step 4: Verify Success**
[Validation check]

**Expected Output:**
[Exact output user should see]
```

**Best Practices:**

1. **One workflow only** (most common 80% use case)
2. **Copy-paste ready** (no placeholders like `<YOUR_VALUE>`)
3. **Concrete example** (real file paths, actual values)
4. **Expected output** (show what success looks like)
5. **~80 lines max** (more detail goes to Standard Workflows)

**Example (Unreal VFX Automation):**
```markdown
## Quick Start

### Basic Foreground Plate Setup

```python
# Via Unreal MCP
mcp__unreal-mcp__create_foreground_plate(
    sequence_path="D:/Plates/Shot001/Shot001_0001.exr",
    plate_name="Shot001_FG"
)
```

**Result:** Complete setup in ~500ms:
- ImgMediaSource created
- MediaPlayer + MediaTexture configured
- VFX-optimized material with alpha support
- ImagePlate component attached to camera
- MediaPlayer auto-plays for immediate preview
```

**Example (Documentation Skill):**
```markdown
## Quick Start: 3 Steps

### Step 1: Copy Template
```bash
cp ClaudeCode/templates/DOCUMENTATION_INDEX_TEMPLATE.md \
   YourProject/DEVELOPMENT_DOCUMENTATION_INDEX.md
```

### Step 2: Fill Sections
Edit: YourProject/DEVELOPMENT_DOCUMENTATION_INDEX.md
- Quick Navigation: Add common tasks
- Main Guides: List primary documents
- Session Docs: Link to development/Session_*.md

### Step 3: Validate
```bash
python scripts/validate_index.py YourProject/
# Expected: ✅ All cross-references valid
```
```

**Anti-Pattern:**
```markdown
# ❌ WRONG: Too many placeholders
python script.py <PROJECT_NAME> --path <YOUR_PATH> --option <VALUE>

# ✅ RIGHT: Concrete example
python script.py CharacterRig --path /Projects/MyProject --option auto
```

---

### Standard Workflows Section

**Purpose:** Cover 3-5 common patterns with detailed step-by-step instructions

**Recommended Count:** 3-5 workflows (more → reference docs)

**Structure per Workflow:**
```markdown
### Workflow N: [Pattern Name]

**Use When:** [Specific scenario]

**Steps:**
1. **[Step Name]**
   ```bash
   [Command]
   ```
   **Why:** [Explanation]

2. **[Step Name]**
   [Command]
   **Why:** [Explanation]

[... 3-7 steps total ...]

**Success Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

**Workflow Selection Strategy:**

**Identify patterns by:**
1. Frequency (what users do most often)
2. Complexity (needs more explanation than Quick Start)
3. Variations (different parameters/approaches)

**Example pattern set (Unreal VFX):**
- Workflow 1: Basic Foreground Plate (single shot, unique material)
- Workflow 2: Multi-Shot Production (master material + instances)
- Workflow 3: Proxy Workflow (fast preview for development)
- Workflow 4: Manual Setup Verification (when automation fails)

**Example pattern set (Houdini HDA Export):**
- Workflow 1: Basic HDA Export (single asset for UE)
- Workflow 2: HDA with Collisions (UCX generation)
- Workflow 3: HDA with LODs (multi-resolution)
- Workflow 4: Batch Export (multiple assets)

**Line Budget per Workflow:** ~40 lines (3 workflows = 120 lines total)

**Detail Level:**
- **Quick Start:** "What" (just commands)
- **Standard Workflows:** "What + Why" (commands + explanations)
- **Reference Docs:** "What + Why + How" (commands + explanations + implementation details)

---

### Troubleshooting Section

**Purpose:** Solve common issues with copy-paste ready solutions

**Recommended Count:** 4-5 issues (covers 80% of problems)

**Structure per Issue:**
```markdown
### Issue N: [Error Name]

**Symptom:** [What user sees]

**Cause:** [Why it happens]

**Solution:**
```bash
[Fix command or steps]
```

**Verification:**
```bash
[Check if fixed]
```

**Prevention:** [Optional: how to avoid]
```

**Issue Selection Strategy:**

**Prioritize:**
1. **Blockers** (stop workflow completely)
2. **Frequent** (common mistakes)
3. **Confusing** (unclear error messages)
4. **Preventable** (known workarounds)

**Example (Plugin Compilation):**
```markdown
### Issue 1: "DLL in Use" Error

**Symptom:**
- Build fails with "cannot open file for writing"
- Error: "UnrealEditor-MyPlugin.dll is being used by another process"

**Cause:**
Unreal Editor is running and has loaded the plugin DLL

**Solution:**
```bash
# Close Unreal Editor
tasklist | findstr "UnrealEditor"
taskkill /F /IM UnrealEditor.exe

# Retry build
& 'C:\Program Files\Epic Games\UE_5.5\Engine\Build\BatchFiles\Build.bat' ...
```

**Verification:**
```bash
ls MyPlugin/Binaries/Win64/UnrealEditor-MyPlugin.dll
# Should show updated timestamp
```

**Prevention:**
- Always close Unreal Editor before compiling plugins
- Use build script that checks editor status first
```

**Line Budget:** ~80 lines (4 issues × 20 lines each)

**When to Move to Reference:**
If troubleshooting exceeds 100 lines:
- Keep 4-5 most common issues in SKILL.md
- Move comprehensive error catalog to `reference/troubleshooting_guide.md`
- Link from SKILL.md: "**Complete troubleshooting:** See reference/troubleshooting_guide.md"

---

### Constitutional Compliance Section

**Purpose:** Document how skill follows each applicable article

**Required for:** All skills (Article VIII mandates this section)

**Structure:**
```markdown
## Constitutional Compliance

### Article I: General Purpose Scripts [STATUS]
[How skill complies or why not applicable]

### Article II: MCP vs Direct [STATUS]
[Design decision rationale]

[... all 9 articles ...]
```

**Status Icons:**
- ✅ Compliant
- ❌ Non-compliant (requires fix)
- ⚠️ Partially compliant (improvement needed)
- ⊘ Not applicable

**Detail Level:**
- **Applicable articles:** 2-3 lines explanation + evidence
- **Not applicable:** 1 line why it doesn't apply

**Example (Script-Based Skill):**
```markdown
### Article I: General Purpose Scripts ✅
- export_hda.py works for ALL Houdini assets (tested: CharacterRig, TreeScatter, RockFormation)
- No hard-coded project names (uses --asset parameter)
- Tested with 3+ projects: verified general-purpose design

### Article II: MCP vs Direct ✅
- Complex workflow (HDA export, validation, UE compatibility check)
- Tool-specific logic (Houdini Python API)
- Direct script appropriate for 5+ parameter operations
```

**Example (Documentation Skill):**
```markdown
### Article I: General Purpose Scripts ✅
- Index template works for ALL VFX applications (Unreal, Houdini, Blender, Nuke)
- No application-specific sections hard-coded
- Tested: Unreal MCP, Blender HTTP Bridge, Nuke pipeline docs

### Article III: Progressive Disclosure ✅
- SKILL.md: 475 lines (<500 limit ✅)
- Margin: 25 lines (5% buffer)
- Reference docs: 3 files (loaded on-demand)

### Article VI: Context Efficiency ✅
**Context Reduction:**
```
Before: Manual doc creation (no standard) = ~2,000 lines reference material
After: Metadata (12) + SKILL.md (475) + Reference avg (300) = ~787 lines
Savings: 60% reduction ✅
```
```

**Line Budget:** ~50 lines (covers all 9 articles at summary level)

---

### Version History Section

**Purpose:** Track changes for users and maintainers

**Format:** Semantic versioning (MAJOR.MINOR.PATCH)

**Structure:**
```markdown
## Version History

**vX.Y.Z** (YYYY-MM-DD) - Title
- Added: New feature description
- Fixed: Bug fix description
- Changed: Modification description
- BREAKING: Breaking change (for MAJOR versions)
```

**Example:**
```markdown
## Version History

**v2.0.0** (2025-11-01) - UE 5.6 Support
- Added: Nanite support for foreground plates
- Added: Virtual texture streaming option
- BREAKING: Removed UE 5.4 compatibility (API changes)
- Fixed: Alpha channel clipping in bright areas

**v1.1.0** (2025-10-26) - Sequencer Integration
- Added: Batch shot processing
- Added: Camera piloting automation
- Fixed: MediaPlayer not looping correctly

**v1.0.0** (2025-10-25) - Initial Release
- create_foreground_plate MCP tool
- Master material + instance pattern
- Proxy workflow support
- 23-step manual process automated
```

**Line Budget:** 10-30 lines (grows with skill maturity)

---

## Progressive Disclosure Strategies

### When to Move Content to Reference Docs

**Threshold Indicators:**

1. **SKILL.md approaching 450 lines** (6% buffer warning from validate_skill.py)
2. **Section exceeds recommended size:**
   - Troubleshooting >100 lines
   - Workflows >150 lines
   - Advanced Techniques >80 lines
3. **Content is detail-heavy but infrequently accessed:**
   - API reference
   - Complete error catalog
   - Build system internals
   - Platform-specific edge cases

### Content Distribution Matrix

| Content Type | SKILL.md | Reference Docs |
|--------------|----------|----------------|
| Quick Start (most common workflow) | ✅ Full | Summary only |
| Standard Workflows (3-5 patterns) | ✅ Full | Detailed variations |
| Troubleshooting (4-5 common issues) | ✅ Full | Complete error catalog |
| Advanced Techniques (2-3 patterns) | ✅ Summary | ✅ Full implementation |
| Script Reference (usage) | ✅ Full | Source code analysis |
| API Documentation | Summary + link | ✅ Full reference |
| Build Requirements | Checklist | ✅ Detailed setup |
| Version-Specific Details | Current version | ✅ All versions |

### Refactoring Example

**Before (557 lines - FAIL):**
```markdown
## Troubleshooting (200 lines)

### Issue 1: DLL Locking (40 lines)
[Detailed explanation, multiple solutions, edge cases]

### Issue 2: Module Not Found (50 lines)
[Complete troubleshooting decision tree]

### Issue 3: Build Configuration (30 lines)
[All possible build configurations]

[... 5 more issues ...]
```

**After (470 lines - PASS):**

**SKILL.md:**
```markdown
## Troubleshooting (80 lines)

### Issue 1: DLL Locking

**Symptom:** Build fails with "cannot open file for writing"

**Solution:**
```bash
tasklist | findstr "UnrealEditor"
taskkill /F /IM UnrealEditor.exe
```

**For complete troubleshooting:** See reference/troubleshooting_guide.md
- Edge cases: Hot reload, multiple instances
- Advanced: Process monitoring scripts
- Platform-specific: Linux/macOS alternatives
```

**reference/troubleshooting_guide.md (300 lines):**
```markdown
# Troubleshooting Guide: Plugin Compilation

## DLL Locking

### Complete Decision Tree
[40 lines of detailed troubleshooting]

### Edge Cases
- Hot reload enabled
- Multiple Unreal instances
- Background processes

### Platform-Specific Solutions
#### Windows
[Detailed solution]

#### Linux
[Detailed solution]

#### macOS
[Detailed solution]

[... complete catalog ...]
```

**Savings:** 557 lines → 470 lines (SKILL.md) + 300 lines (on-demand reference) = 87 lines saved in always-loaded content

---

## Line Count Management

### Measuring Line Count

**Validation Script Method (Official):**
```python
# From validate_skill.py
with open(self.skill_md, 'r', encoding='utf-8') as f:
    lines = f.readlines()
line_count = len(lines)  # Counts ALL lines including blank lines
```

**Matches Bash `wc -l`:**
```bash
wc -l .claude/skills/SKILL_NAME/SKILL.md
```

**What Counts:**
- Content lines: YES
- Blank lines: YES
- Comment lines: YES (if present in Markdown)
- YAML frontmatter: YES

### Thresholds

| Line Count | Status | Action Required |
|------------|--------|-----------------|
| <450 lines | ✅ PASS | Healthy margin (10%+ buffer) |
| 450-500 lines | ⚠️ WARN | Approaching limit, monitor additions |
| >500 lines | ❌ FAIL | MUST refactor to reference docs |

### Refactoring Strategies

**Strategy 1: Move Verbose Troubleshooting**

**Identify:**
```bash
grep -n "^### Issue" SKILL.md | wc -l
# If >5 issues, likely candidate for refactoring
```

**Action:**
- Keep 4-5 most common issues in SKILL.md (~80 lines)
- Move complete catalog to `reference/troubleshooting_guide.md`

**Savings:** ~100-150 lines

---

**Strategy 2: Extract Advanced Techniques**

**Pattern:**
- SKILL.md: High-level description + use case (30 lines)
- Reference: Complete implementation + edge cases (200 lines)

**Example:**

**SKILL.md (30 lines):**
```markdown
## Advanced Techniques

### Multi-Shot Master Material Pipeline

**Use Case:** 50+ shots with shared material logic

**Pattern:** One master material → Instance per shot

**Benefits:**
- 90% faster shot setup (instance vs full material)
- Consistent look across all shots
- One fix applies to all shots

**Implementation:** See reference/advanced_techniques.md
```

**reference/advanced_techniques.md (200 lines):**
```markdown
# Advanced Techniques: Multi-Shot Production

## Master Material Pipeline

### Complete Implementation
[Detailed setup, node graphs, optimization]

### Edge Cases
[Handling shot-specific variations]

### Performance Optimization
[Material instance constant vs parameter]

[... detailed guide ...]
```

**Savings:** ~170 lines

---

**Strategy 3: Summarize Workflow Variations**

**Pattern:**
- SKILL.md: 3 core workflows (120 lines)
- Reference: 10+ workflow variations (400 lines)

**Example:**

**SKILL.md:**
- Workflow 1: Basic Setup
- Workflow 2: Multi-Shot
- Workflow 3: Proxy Workflow

**reference/workflow_variations.md:**
- Variation 1: Custom aspect ratios
- Variation 2: HDR workflows
- Variation 3: Multi-camera setups
- Variation 4: Interactive playback control
- [... 6 more variations ...]

**Savings:** ~280 lines

---

**Strategy 4: Link to External Official Docs**

**Pattern:** Don't duplicate official documentation

**SKILL.md (WRONG - 100 lines):**
```markdown
## Unreal Build System Deep Dive

[Copied from Epic Games documentation - 100 lines]
```

**SKILL.md (RIGHT - 10 lines):**
```markdown
## Build System Reference

**Official Documentation:**
- Unreal Build Tool: https://docs.unrealengine.com/5.5/en-US/unreal-build-tool-in-unreal-engine/
- Plugin Development: https://docs.unrealengine.com/5.5/en-US/plugins-in-unreal-engine/

**Quick Reference:** See reference/build_requirements.md for curated essentials
```

**Savings:** ~90 lines

---

## Examples from Production Skills

### Example 1: vfx-documentation (475 lines)

**Line Breakdown:**
- YAML frontmatter: 12 lines
- Header + intro: 20 lines
- Quick Start: 85 lines
- Standard Workflows (3): 140 lines
- Troubleshooting (4 issues): 75 lines
- Constitutional Compliance: 60 lines
- Reference links: 25 lines
- Version History: 18 lines
- **Total:** 475 lines (5% margin) ✅

**Progressive Disclosure Strategy:**
- SKILL.md: Core workflows for creating and using documentation index
- Reference docs: 3 files
  - template_customization.md (detailed template usage)
  - cross_reference_validation.md (validation logic)
  - multi_app_patterns.md (application-specific tips)

**Context Efficiency:**
- Before: 1,800 lines scattered docs
- After: 475 + ~300 avg reference = 775 lines typical usage
- Savings: 57% reduction

---

### Example 2: unreal-vfx-automation (470 lines)

**Line Breakdown:**
- YAML frontmatter: 13 lines
- Header + intro: 18 lines
- Quick Start: 75 lines
- Standard Workflows (4): 160 lines
- Troubleshooting (5 issues): 90 lines
- Constitutional Compliance: 55 lines
- Reference links: 20 lines
- Output standards: 25 lines
- Version History: 14 lines
- **Total:** 470 lines (6% margin) ✅

**Progressive Disclosure Strategy:**
- SKILL.md: Production workflows for foreground plates
- Reference docs: 2 files
  - imageplate_internals.md (UE architecture)
  - manual_setup_guide.md (fallback procedures)

**Context Efficiency:**
- Before: 1,530 lines manual + troubleshooting docs
- After: 470 + ~250 avg reference = 720 lines typical usage
- Savings: 70% reduction

---

### Example 3: skill-creation-update (364 lines)

**Line Breakdown:**
- YAML frontmatter: 13 lines
- Header + intro: 20 lines
- Quick Start (4 examples): 55 lines
- Standard Workflows (4): 135 lines
- Troubleshooting (4 issues): 60 lines
- Reference links: 10 lines
- Constitutional Compliance: 55 lines
- Version History: 16 lines
- **Total:** 364 lines (27% margin - very healthy) ✅

**Progressive Disclosure Strategy:**
- SKILL.md: CLI usage for skill management scripts
- Reference docs: 2 files
  - skill_template_guide.md (this file - detailed template usage)
  - constitutional_validation.md (validation logic deep dive)

**Why So Compact:**
- Scripts do most of the work (complexity in Python, not Markdown)
- Reference docs handle detailed explanations
- Quick Start is very focused (4 one-liners)

**Context Efficiency:**
- Before: 1,712 lines (constitution + template + guide)
- After: 364 + ~600 avg reference = 964 lines typical usage
- Savings: 43% reduction (even with comprehensive reference docs)

---

## Quick Reference

### Template Checklist

**Before filling template:**
- [ ] Read VFX_SKILL_CONSTITUTION.md (understand principles)
- [ ] Identify 3+ test targets (Article I validation)
- [ ] Plan reference doc structure (if skill complex)

**While filling template:**
- [ ] Replace all {{PLACEHOLDERS}} with real content
- [ ] Follow description formula (What + When + Triggers)
- [ ] Use concrete examples (no `<YOUR_VALUE>` placeholders)
- [ ] Keep Quick Start to single workflow
- [ ] Document 3-5 Standard Workflows (not 10+)
- [ ] Include 4-5 Troubleshooting issues (most common)
- [ ] Link to reference docs (don't inline everything)

**After filling template:**
- [ ] Run validate_skill.py (check compliance)
- [ ] Verify line count <500 (preferably <450)
- [ ] Test Quick Start with copy-paste (no errors)
- [ ] Test scripts with 3+ targets (Article I)
- [ ] Review Constitutional Compliance section (all articles addressed)

### Common Mistakes

**Mistake 1: Too many placeholders in Quick Start**
```markdown
# ❌ WRONG
python script.py <PROJECT> --path <PATH> --option <VALUE>

# ✅ RIGHT
python script.py CharacterRig --path /Projects/Demo --option auto
```

**Mistake 2: Exceeding workflow count**
```markdown
# ❌ WRONG: 8 workflows (>180 lines)
### Workflow 1-8: [Each 25 lines]

# ✅ RIGHT: 3 core workflows + reference link
### Workflow 1-3: [Core patterns]
**More workflows:** See reference/workflow_variations.md
```

**Mistake 3: Duplicating official documentation**
```markdown
# ❌ WRONG: Copy-paste from Unreal docs (150 lines)
## Plugin Architecture
[Complete Unreal documentation]

# ✅ RIGHT: Link + summary (15 lines)
## Plugin Architecture
**Official Guide:** https://docs.unrealengine.com/...
**Quick summary:** 3 required files, module registration, build config
```

**Mistake 4: Verbose troubleshooting**
```markdown
# ❌ WRONG: 10 issues × 20 lines = 200 lines
### Issue 1-10: [Comprehensive guide]

# ✅ RIGHT: 4-5 issues + reference link
### Issue 1-5: [Most common]
**Complete catalog:** See reference/troubleshooting_guide.md
```

### Line Budget Quick Reference

| Section | Recommended Lines | Max Lines |
|---------|-------------------|-----------|
| YAML Frontmatter | 10-15 | 20 |
| Critical First Step | 15-25 | 40 |
| Quick Start | 60-100 | 120 |
| Standard Workflows | 100-150 | 180 |
| Advanced Techniques | 30-60 | 80 |
| Troubleshooting | 60-100 | 120 |
| Constitutional Compliance | 40-60 | 80 |
| Reference Links | 15-25 | 40 |
| Version History | 10-30 | 50 |
| **TOTAL** | **340-565** | **500** |

**Target:** 400-470 lines (leaves margin for future additions)

---

**Last Updated:** 2025-10-25
**Applies To:** VFX_SKILL_TEMPLATE.md v1.0.0+
**Related:** constitutional_validation.md (validation logic), VFX_SKILL_CONSTITUTION.md (core principles)
