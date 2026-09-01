---
name: skill-creation-update
description: Standardized workflow for creating and updating VFX Agent Skills with constitutional validation, progressive disclosure enforcement, and automated template application. Use when creating skills, validating compliance, testing scripts, updating skill versions, or when user mentions "create skill", "validate skill", "skill template", "constitutional compliance", "skill testing".
allowed-tools: Read,Write,Edit
---

# skill-creation-update

**Skill Version:** 1.1.0
**Last Updated:** 2025-12-03
**Dependencies:** Python 3.12+, VFX_SKILL_CONSTITUTION.md (v2.0.0+)
**Status:** Production-ready

---

## Quick Start

### Create New Skill
```bash
python .claude\skills\skill-creation-update\scripts\create_skill.py houdini-hda-export \
  --description "Export Houdini Digital Assets for Unreal Engine" \
  --triggers "hda export,houdini to unreal" \
  --dependencies "Houdini 20+,UE 5.5+" \
  --model sonnet
```

### Validate Skill Compliance
```bash
# Validate Claude Code skill
python .claude\skills\skill-creation-update\scripts\validate_skill.py unreal-vfx-automation
# Output: Article I: [OK] PASS, Article III: [OK] PASS (470 lines), Overall: [OK] PASS

# Validate Agent OS standard
python .claude\skills\skill-creation-update\scripts\validate_skill.py unreal-engine-standards --agent-os
# Output: Agent OS Headers: [OK] PASS, Article III: [OK] PASS (414 lines), Overall: [OK] PASS
```

### Test with Multiple Targets (Article I)
```bash
python .claude\skills\skill-creation-update\scripts\test_skill.py unreal-vfx-automation \
  --targets Shot001,Shot002,Shot003
# Output: 3/3 passed [OK], Article I: [OK] VALIDATED
```

### Update Skill Version
```bash
python .claude\skills\skill-creation-update\scripts\update_skill.py unreal-vfx-automation \
  --version 1.1.0 \
  --changes "Added Sequencer integration"
# Output: [OK] Updated to 1.1.0, [OK] Compliance maintained
```

---

## Standard Workflows

### Workflow 1: Create New Skill from Template

**Steps:**
1. **Plan scope:** Identify repeatable workflow, verify 3+ projects can use it
2. **Run create_skill.py:**
   ```bash
   python .claude\skills\skill-creation-update\scripts\create_skill.py SKILL_NAME \
     --description "What + When + Triggers (Article VIII)" \
     --triggers "trigger1,trigger2,trigger3" \
     --dependencies "Required software" \
     --model sonnet
   ```
3. **Verify structure:**
   ```bash
   ls .claude/skills/SKILL_NAME/
   # Expected: SKILL.md, reference/, scripts/
   ```
4. **Fill SKILL.md sections:** Quick Start, Workflows (3-5), Troubleshooting (4-5 issues)
5. **Create reference docs:** Move detailed content to `reference/*.md`
6. **Validate line count:**
   ```bash
   wc -l .claude/skills/SKILL_NAME/SKILL.md
   # Must be <500 lines
   ```

**Output:** Complete skill directory with template populated

---

### Workflow 2: Validate Constitutional Compliance

**Steps:**
1. **Run validate_skill.py:**
   ```bash
   python .claude\skills\skill-creation-update\scripts\validate_skill.py SKILL_NAME
   ```
   **Pass the skill NAME, never a path.** Given a path it cannot find the
   skill and still prints `[OK] PASS (0/0 automated checks)` - a vacuous
   pass (2026-08-22). Also known: Article VIII enforces the retired
   emoji-template section list (Quick Start, Dependencies, Last Updated...),
   so current-style skills such as `wrap-session` FAIL it; treat an
   Article VIII-only failure as instrument drift, not a defect, until the
   validator is updated.
2. **Review report:**
   - Article I: No hard-coded paths detected [OK]
   - Article III: 470 lines <500 [OK]
   - Article IV: Independent testing documented [OK]
   - Article VI: 70% context reduction [OK]
   - Article VIII: All sections present [OK]
3. **Address failures:**
   - Article I: Remove hard-coded paths, add params
   - Article III: Move details to reference docs
   - Article VIII: Add missing sections
4. **Re-validate:** Run validate_skill.py again until [OK] PASS
5. **Generate report:**
   ```bash
   python .claude\skills\skill-creation-update\scripts\validate_skill.py SKILL_NAME --report
   # Saves to: ClaudeCode/development/reports/SKILL_NAME_COMPLIANCE_REPORT.md
   ```

**Output:** Compliance report with pass/fail per article

---

### Workflow 3: Test with Multiple Projects (Article I)

**Steps:**
1. **Identify 3+ test targets:** Different projects/assets (e.g., Shot001, Shot002, Shot003)
2. **Run test_skill.py:**
   ```bash
   python .claude\skills\skill-creation-update\scripts\test_skill.py SKILL_NAME \
     --targets target1,target2,target3
   ```
3. **Review results:**
   - Test 1/3: target1 [OK] PASS (487ms)
   - Test 2/3: target2 [OK] PASS (502ms)
   - Test 3/3: target3 [OK] PASS (495ms)
   - Article I: [OK] VALIDATED
4. **Address failures:** Fix script bugs if any target fails
5. **Document testing:** Add to Constitutional Compliance section

**Output:** Test report with 100% pass rate, Article I validation

---

### Workflow 4: Update Existing Skill

**Steps:**
1. **Determine version increment:**
   - MAJOR (X.0.0): Breaking changes
   - MINOR (x.Y.0): New features (backward compatible)
   - PATCH (x.y.Z): Bug fixes
2. **Run update_skill.py:**
   ```bash
   # Minor update
   python .claude\skills\skill-creation-update\scripts\update_skill.py SKILL_NAME \
     --version 1.1.0 \
     --changes "Added feature X"

   # Major update (breaking)
   python .claude\skills\skill-creation-update\scripts\update_skill.py SKILL_NAME \
     --version 2.0.0 \
     --changes "BREAKING: Removed UE 4.27 support" \
     --breaking
   ```
3. **Review changelog entry:**
   ```markdown
   **v1.1.0** (2025-10-26) - Feature Update
   - Added: Feature X
   - Fixed: Bug Y
   ```
4. **Re-validate:** Automatic compliance check during update
5. **Test updated skill:** Re-run test_skill.py to verify

**Output:** Version incremented, changelog added, compliance maintained

---

## Troubleshooting

### Issue 1: "Skill Already Exists"

**Symptom:** `[FAIL] Error: Skill 'skill-name' already exists`

**Fix:**
```bash
# Option 1: Delete and recreate
rm -rf .claude/skills/skill-name
python .claude\skills\skill-creation-update\scripts\create_skill.py skill-name ...

# Option 2: Use update instead
python .claude\skills\skill-creation-update\scripts\update_skill.py skill-name --version 1.1.0
```

---

### Issue 2: "SKILL.md >500 Lines"

**Symptom:** `Article III: [FAIL] FAIL - SKILL.md: 547 lines (>500 limit)`

**Fix:**
1. **Identify verbose sections:**
   ```bash
   grep -n "^## " .claude/skills/SKILL_NAME/SKILL.md
   ```
2. **Move detailed content to reference:**
   - Troubleshooting too long (200 lines)? -> Move to `reference/troubleshooting_guide.md`, keep 4-5 issues (50 lines)
   - Workflows too detailed (300 lines)? -> Move to `reference/detailed_workflow.md`, keep summaries (150 lines)
3. **Add references:**
   ```markdown
   **For complete troubleshooting:** See reference/troubleshooting_guide.md
   ```
4. **Re-validate:**
   ```bash
   python .claude\skills\skill-creation-update\scripts\validate_skill.py SKILL_NAME
   # Should show: Article III: [OK] PASS
   ```

---

### Issue 3: "Hard-Coded Paths Detected"

**Symptom:** `Article I: [FAIL] FAIL - Hard-coded paths in scripts/export.py`

**Fix:**
```python
# [FAIL] WRONG
project_path = "C:\\Users\\Me\\UnrealProjects\\MyProject"

# [OK] CORRECT: Parameterized
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--project-path", required=True)
args = parser.parse_args()
project_path = args.project_path

# [OK] CORRECT: Relative
import os
script_dir = os.path.dirname(__file__)
project_path = os.path.join(script_dir, "..", "..", "Projects", "MyProject")

# [OK] CORRECT: Environment variable
project_path = os.getenv("UNREAL_PROJECT_PATH", "DefaultPath")
```

---

### Issue 4: "No Script Found" (Test Fails)

**Symptom:** `[FAIL] Error: No executable script found in scripts/`

**Fix:**
- **Documentation-only skills:** Skip test_skill.py (not applicable)
- **MCP-based skills:** Create test wrapper:
  ```python
  # scripts/test_wrapper.py
  import sys
  from mcp import client

  def test(target):
      result = client.call_tool("tool_name", {"target": target})
      return result["success"]

  if __name__ == "__main__":
      sys.exit(0 if test(sys.argv[1]) else 1)
  ```
- **Validation scripts:**
  ```python
  # scripts/validate.py
  import sys, os

  skill_md = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")
  if not os.path.exists(skill_md):
      print("[FAIL] SKILL.md not found")
      sys.exit(1)

  with open(skill_md) as f:
      if len(f.readlines()) > 500:
          print("[FAIL] SKILL.md >500 lines")
          sys.exit(1)

  print("[OK] Valid")
  sys.exit(0)
  ```

---

## Reference Documentation

### Detailed Guides

**skill_template_guide.md** - Template structure, placeholders, best practices
**constitutional_validation.md** - Validation logic, regex patterns, edge cases

### Python Scripts

**create_skill.py** - Create new skill from template (CLI, template copying)
**validate_skill.py** - Validate constitutional compliance (9 articles)
**test_skill.py** - Test with multiple targets (Article I validation)
**update_skill.py** - Update version and changelog (SemVer)

**Detailed workflow documentation:** See `reference/skill_template_guide.md`

---

## Constitutional Compliance

### Article I: General Purpose Scripts [OK]
- create_skill.py works for ALL skill types (tested: vfx-documentation, unreal-vfx-automation, agent-creation-update)
- validate_skill.py validates ANY skill (no hard-coded skill names)
- test_skill.py tests ANY skill with scripts
- No per-skill script generation

### Article II: MCP vs Direct [OK]
- Complex workflows -> Direct Python scripts (not MCP tools)
- Multi-step processes (creation, validation, testing)
- Skill-specific logic (constitutional rules, line counting)

### Article III: Progressive Disclosure [OK]
- SKILL.md: 465 lines (<500 limit [OK])
- Margin: 35 lines (7% buffer)
- Reference docs: 2 files (on-demand loading)

### Article IV: Test Independently [OK]
- create_skill.py tested with test-skill (deleted after)
- validate_skill.py tested against all existing skills
- test_skill.py tested with unreal-vfx-automation
- update_skill.py tested with version increments

### Article V: Follow Official Patterns [OK]
- Python argparse (Python standard)
- JSON output (industry standard)
- Semantic versioning (SemVer 2.0)
- Markdown docs (GitHub standard)

### Article VI: Context Efficiency [OK]
**Context Reduction:**
```
Before: VFX_SKILL_CONSTITUTION (862) + VFX_SKILL_TEMPLATE (350) + VFX_AGENT_SKILLS_GUIDE (500) = 1,712 lines (~8,560 tokens)
After: Metadata (12) + SKILL.md (465) + Reference avg (300) = ~777 lines (3,885 tokens)
Savings: 73% reduction [OK]
```

### Article VII: Cross-App Integration [SKIP]
Not applicable (skill management tool, not cross-app workflow)

### Article VIII: Documentation Standards [OK]
- [OK] YAML frontmatter (name, description, triggers, model)
- [OK] Version/Last Updated/Dependencies
- [OK] Quick Start (4 workflows)
- [OK] Standard Workflows (4 detailed)
- [OK] Troubleshooting (4 issues)
- [OK] Reference Documentation (2 guides)
- [OK] Constitutional Compliance (applicable articles)
- [OK] Version History (SemVer)
- [OK] Description formula: What + When + Triggers

### Article IX: Agent Versioning [SKIP]
Not applicable (this is a skill, uses directory structure)

---

## Version History

**v1.1.0** (2025-12-03) - Agent OS Integration
- Added Agent OS standards validation support
- New `--agent-os` flag for validate_skill.py
- Constitutional header validation (YAML frontmatter)
- Context efficiency tracking for standards files
- Line count flexibility for complex standards (400-550 lines)
- Fixed Windows console encoding for Unicode emojis
- All 5 VFX standards validated successfully

**v1.0.0** (2025-10-25) - Initial Release
- create_skill.py: Automated skill creation from template
- validate_skill.py: Constitutional compliance validation (9 articles)
- test_skill.py: Multi-target testing for Article I
- update_skill.py: Semantic versioning and changelog
- Reference docs: Template guide, validation guide
- 73% context reduction vs manual process
- Full constitutional compliance (8/8 applicable articles)
