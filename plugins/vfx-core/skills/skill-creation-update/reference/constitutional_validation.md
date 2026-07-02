# Constitutional Validation Guide

**Purpose:** Detailed explanation of validation logic for VFX Skill constitutional compliance

**Last Updated:** 2025-10-25
**Validator Version:** 1.0.0 (validate_skill.py)
**Constitution Version:** 1.1.0

---

## Table of Contents

1. [Validation Overview](#validation-overview)
2. [Article-by-Article Validation Logic](#article-by-article-validation-logic)
3. [Validation Report Format](#validation-report-format)
4. [Edge Cases and Special Handling](#edge-cases-and-special-handling)
5. [False Positive Mitigation](#false-positive-mitigation)
6. [Extending Validation Logic](#extending-validation-logic)

---

## Validation Overview

### Philosophy

**Automated vs Manual Validation:**

| Article | Validation Type | Reason |
|---------|----------------|--------|
| I | Automated | Regex patterns detect hard-coded paths |
| II | Manual | Design decision (context-dependent) |
| III | Automated | Line counting is deterministic |
| IV | Automated | Pattern matching for testing evidence |
| V | Manual | Requires understanding of tool patterns |
| VI | Automated | Metrics extraction + structure check |
| VII | Automated | Keyword detection for cross-app workflows |
| VIII | Automated | Required sections + frontmatter check |
| IX | Skip | Not applicable to skills (agents only) |

**Validation Outcomes:**

```python
class ValidationResult:
    article: str      # "Article I", "Article II", etc.
    status: str       # "PASS", "FAIL", "WARN", "SKIP"
    message: str      # Human-readable summary
    details: list     # Detailed findings
```

**Status Meanings:**
- **PASS** (✅): Fully compliant, no issues
- **FAIL** (❌): Constitutional violation, must fix
- **WARN** (⚠️): Potential issue, recommend review
- **SKIP** (⊘): Not applicable to this skill

### Running Validation

**Basic Usage:**
```bash
python scripts/validate_skill.py SKILL_NAME
```

**With Report Generation:**
```bash
python scripts/validate_skill.py SKILL_NAME --report
# Saves to: ClaudeCode/development/reports/SKILL_NAME_COMPLIANCE_REPORT.md
```

**Custom Skills Path:**
```bash
python scripts/validate_skill.py SKILL_NAME --skills-path /path/to/skills
```

---

## Article-by-Article Validation Logic

### Article I: General Purpose Scripts

**Constitutional Requirement:**
> ONE script for ALL projects/assets. NO per-project script generation.

#### Automated Checks

**1. Hard-Coded Path Detection**

**Regex Patterns:**
```python
hard_coded_patterns = [
    (r'[CDE]:\\\\', "Windows absolute path"),           # C:\\, D:\\, E:\\
    (r'/Users/', "macOS user path"),                     # /Users/username/
    (r'/home/', "Linux home path"),                      # /home/username/
    (r'[CDE]:\\', "Windows path (single backslash)"),   # C:\, D:\, E:\
]
```

**Why These Patterns:**
- Windows: `C:\`, `D:\`, `E:\` are drive letters (absolute paths)
- macOS: `/Users/` indicates user-specific path (not portable)
- Linux: `/home/` indicates user-specific path (not portable)
- Double backslash `\\` catches escaped paths in strings

**Example Violations:**
```python
# ❌ FAIL: Windows absolute path
project_path = "C:\\Users\\Me\\UnrealProjects\\MyProject"

# ❌ FAIL: macOS user path
export_dir = "/Users/artist/Desktop/exports"

# ❌ FAIL: Linux home path
output_path = "/home/developer/output"
```

**Example Compliance:**
```python
# ✅ PASS: Parameterized
import argparse
parser.add_argument("--project-path", required=True)
project_path = args.project_path

# ✅ PASS: Relative path
script_dir = os.path.dirname(__file__)
project_path = os.path.join(script_dir, "..", "Projects", "MyProject")

# ✅ PASS: Environment variable
project_path = os.getenv("UNREAL_PROJECT_PATH", "/default/path")
```

---

**2. Hard-Coded Project Name Detection**

**Regex Patterns:**
```python
project_patterns = [
    (r'MyProject', "Generic 'MyProject' name"),
    (r'TestProject', "Generic 'TestProject' name"),
    (r'project_name\s*=\s*["\'][A-Z]', "Hard-coded project_name variable"),
]
```

**Why These Patterns:**
- `MyProject`, `TestProject`: Common placeholder names (likely hard-coded)
- `project_name = "CapitalizedName"`: Variable assignment with capitalized string (likely project name)

**Example Violations:**
```python
# ❌ FAIL: Hard-coded project name
project_name = "MyProject"
uproject_file = "MyProject.uproject"

# ❌ FAIL: Hard-coded in path
build_command = f"Build.bat MyProjectEditor Win64 Development"
```

**Example Compliance:**
```python
# ✅ PASS: Parameterized
project_name = args.project_name
uproject_file = f"{project_name}.uproject"

# ✅ PASS: Derived from path
project_name = Path(args.uproject_path).stem
```

---

**3. Parameterization Verification**

**Detection Logic:**
```python
# Check for parameterization
if 'argparse' in content or 'sys.argv' in content:
    has_argparse = True
```

**Why This Works:**
- `argparse`: Standard Python library for CLI arguments
- `sys.argv`: Direct argument access (lower-level but valid)

**Example Compliance:**
```python
# ✅ PASS: Using argparse
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("asset_name", help="Name of asset to export")
args = parser.parse_args()

# ✅ PASS: Using sys.argv
import sys
if len(sys.argv) < 2:
    print("Usage: export.py <asset_name>")
    sys.exit(1)
asset_name = sys.argv[1]
```

---

**4. Validation Outcomes**

| Condition | Status | Message |
|-----------|--------|---------|
| Hard-coded paths detected | ❌ FAIL | "Hard-coded paths or project names detected" |
| No argparse/sys.argv | ⚠️ WARN | "No argparse/sys.argv found - verify parameterization" |
| No scripts directory | ⊘ SKIP | "No scripts directory (documentation-only skill)" |
| All checks pass | ✅ PASS | "Scripts are general-purpose" |

---

**5. Edge Cases**

**Documentation-Only Skills:**
```python
if not scripts_dir.exists():
    return ValidationResult(status="SKIP", message="No scripts directory")
```
- Reason: No scripts to validate (e.g., vfx-documentation skill)
- Outcome: SKIP (not applicable)

**MCP-Based Skills:**
```python
if not scripts:
    return ValidationResult(status="SKIP", message="No Python scripts found")
```
- Reason: Skill uses MCP tools, not direct scripts
- Outcome: SKIP (validation happens in MCP server layer)

**Test/Validation Scripts:**
```python
# These patterns are ALLOWED (not violations)
# Test scripts often have hard-coded paths for testing
if "test_" in script.name or "_test" in script.name:
    # Skip hard-coded path checks
```
- Note: Current implementation validates ALL scripts
- Future enhancement: Distinguish production vs test scripts

---

### Article II: MCP vs Direct Implementation

**Constitutional Requirement:**
> Choose the right tool for the task - MCP for infrastructure, direct for complex workflows.

#### Validation Approach

**Status:** Manual verification (SKIP in automated validation)

**Why Manual:**
- Decision is context-dependent (no one-size-fits-all rule)
- Requires understanding workflow complexity
- Involves architecture trade-offs

**Validation Logic:**
```python
def validate_article_ii(self) -> None:
    """Article II: Manual decision - no automated check"""
    self.results.append(ValidationResult(
        article="Article II",
        status="SKIP",
        message="Design decision - see Constitutional Compliance section",
        details=["Verify: MCP used for simple operations, direct scripts for complex workflows"]
    ))
```

**Manual Checklist for Skill Authors:**

**Use MCP if:**
- [ ] Operation is 0-2 parameters
- [ ] No complex multi-step logic
- [ ] Reusable across ALL skills
- [ ] Infrastructure operation (files, processes)

**Use Direct Scripts if:**
- [ ] Operation has 3+ parameters
- [ ] Multi-step workflow (validation → processing → output)
- [ ] Tool-specific logic (Houdini API, Blender Python)
- [ ] Build system complexity

**Documentation Requirement:**
Skill MUST document decision in Constitutional Compliance section:

```markdown
### Article II: MCP vs Direct ✅
- Complex workflow (HDA export, validation, UE import)
- Tool-specific logic (Houdini Python API, hou module)
- 5+ parameters (asset, target, version, collisions, LODs)
- Direct script appropriate for complexity level
```

---

### Article III: Progressive Disclosure (<500 Lines)

**Constitutional Requirement:**
> SKILL.md stays focused. Complex details go to reference docs.

#### Automated Checks

**1. Line Counting Methodology**

**Implementation:**
```python
def validate_article_iii(self) -> None:
    with open(self.skill_md, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    line_count = len(lines)
```

**What Gets Counted:**
- Content lines: YES
- Blank lines: YES
- YAML frontmatter: YES
- Code block content: YES
- Comments: YES (if present)

**Matches `wc -l` Behavior:**
```bash
wc -l SKILL.md
# Counts ALL lines including blank lines
```

**Why Count Blank Lines:**
- Constitutional limit is about file size, not content density
- Blank lines improve readability (part of document design)
- Consistent with standard line counting tools

---

**2. Threshold Logic**

| Line Count | Status | Action | Buffer |
|------------|--------|--------|--------|
| <450 lines | ✅ PASS | Healthy margin | >10% |
| 450-500 lines | ⚠️ WARN | Monitor additions | 0-10% |
| >500 lines | ❌ FAIL | MUST refactor | Violation |

**Warning Calculation:**
```python
elif line_count > 450:
    margin = 500 - line_count
    buffer_pct = margin / 500 * 100
    details.append(f"⚠️ {line_count} lines (approaching 500 limit)")
    details.append(f"Margin: {margin} lines ({buffer_pct:.1f}% buffer)")
    return ValidationResult(status="WARN", ...)
```

**Example Output:**
```
⚠️ 475 lines (approaching 500 limit)
Margin: 25 lines (5.0% buffer)
Consider moving content to reference docs before adding more
```

---

**3. Reference Directory Verification**

**Check:**
```python
reference_dir = self.skill_dir / "reference"
if reference_dir.exists():
    ref_files = list(reference_dir.glob("*.md"))
    details.append(f"✅ Reference directory: {len(ref_files)} file(s)")
else:
    details.append("⚠️ No reference/ directory (may not be needed)")
```

**Interpretation:**
- **Has reference dir:** Good progressive disclosure structure
- **No reference dir:** Acceptable if skill is simple (<400 lines)
- **No reference dir + >450 lines:** Warning (consider refactoring)

---

**4. Validation Outcomes**

| Condition | Status | Message |
|-----------|--------|---------|
| >500 lines | ❌ FAIL | "SKILL.md exceeds 500 line limit" |
| 450-500 lines | ⚠️ WARN | "SKILL.md approaching 500 line limit" |
| <450 lines | ✅ PASS | "Progressive disclosure compliant" |

**Failure Details (>500 lines):**
```
❌ 547 lines (>500 limit)
Overage: 47 lines (9.4%)
Fix: Move detailed content to reference/*.md
Example: Troubleshooting (>100 lines) → reference/troubleshooting_guide.md
```

---

**5. Edge Cases**

**Compact Skills (<300 lines):**
- Still PASS (no minimum requirement)
- Skills can be concise if well-designed
- Example: skill-creation-update (364 lines)

**Skills at Exactly 500 Lines:**
- Status: FAIL (limit is <500, not ≤500)
- Must reduce by at least 1 line

**Skills with No Content (Template Only):**
- Line count includes template structure
- Valid if skill is work-in-progress

---

### Article IV: Test Independently Before Agent Integration

**Constitutional Requirement:**
> Scripts must work standalone before agent uses them.

#### Automated Checks

**1. `__main__` Block Detection**

**Pattern Matching:**
```python
for script in scripts:
    with open(script, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'if __name__ == "__main__"' in content:
        has_main_block = True
        details.append(f"✅ {script.name}: Has __main__ block")
```

**Why This Matters:**
- `__main__` block allows script to be run standalone
- Enables independent testing without agent
- Standard Python pattern for executable scripts

**Example:**
```python
# ✅ PASS: Script can be tested independently
def export_hda(asset_name, output_path):
    # ... implementation ...
    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("asset_name")
    parser.add_argument("--output", default="/tmp/")
    args = parser.parse_args()

    export_hda(args.asset_name, args.output)
```

---

**2. Test File Discovery**

**Patterns:**
```python
test_files = (
    list(scripts_dir.glob("test_*.py")) +
    list(scripts_dir.glob("*_test.py"))
)
```

**Why These Patterns:**
- `test_*.py`: Standard pytest naming (e.g., test_export.py)
- `*_test.py`: Alternative naming (e.g., export_test.py)
- Covers 95% of Python test naming conventions

**Example:**
```
scripts/
├── export_hda.py          # Main script
├── test_export_hda.py     # Test file (detected)
└── validate_export.py     # Helper (not a test file)
```

---

**3. Session Documentation Check**

**Discovery Logic:**
```python
parent_dir = self.skill_dir.parent.parent  # Go to project root
if (parent_dir / "development").exists():
    session_docs = list((parent_dir / "development").glob("Session_*.md"))
```

**Why This Helps:**
- Session docs often document testing process
- Evidence of real-world validation
- Provides context for skill development

**Example:**
```
UnrealEngine/unreal-mcp-main/
├── development/
│   ├── Session_2025-10-25_ImagePlate.md   # Documents testing
│   └── Session_2025-10-24_PluginCompile.md
└── .claude/skills/unreal-vfx-automation/
    └── SKILL.md
```

---

**4. Validation Outcomes**

| Condition | Status | Message |
|-----------|--------|---------|
| Has `__main__` blocks OR test files | ✅ PASS | "Independent testing verified" |
| No `__main__` blocks AND no test files | ⚠️ WARN | "No clear testing evidence" |
| No scripts directory | ⊘ SKIP | "No scripts to test" |

**Pass Example:**
```
✅ export_hda.py: Has __main__ block
✅ Independent testing possible (__main__ blocks present)
✅ Test files: test_export_hda.py
✅ Session docs available: 3 file(s)
```

**Warning Example:**
```
⚠️ No __main__ blocks found - add for independent testing
Recommendation: Add if __name__ == '__main__' blocks to scripts
```

---

**5. Edge Cases**

**MCP-Based Skills (No Scripts):**
```python
if not scripts_dir.exists() or not list(scripts_dir.glob("*.py")):
    return ValidationResult(status="SKIP", message="No scripts to test")
```
- Reason: MCP tools tested in MCP server
- Outcome: SKIP

**Library Scripts (Import Only):**
- Script has no `__main__` block (designed to be imported)
- Warning is appropriate (consider adding test stub)

**Documentation-Only Skills:**
- No scripts to test
- Outcome: SKIP

---

### Article V: Follow Official Tool/Engine Patterns

**Constitutional Requirement:**
> Match official examples when available.

#### Validation Approach

**Status:** Manual verification (SKIP in automated validation)

**Why Manual:**
- Requires knowledge of official documentation
- Context-specific (different tools have different patterns)
- Subjective judgment (multiple valid approaches)

**Validation Logic:**
```python
def validate_article_v(self) -> None:
    """Article V: Manual verification - output reminder to user"""
    self.results.append(ValidationResult(
        article="Article V",
        status="SKIP",
        message="Manual verification required",
        details=[
            "⚠️ Verify tool/engine documentation is referenced",
            "Check: Quick Start and Workflows cite official docs",
            "Example: 'See Unreal Engine 5.5 documentation for...'",
            "Example: 'Follows Houdini 20.0 Python API patterns'"
        ]
    ))
```

**Manual Checklist for Skill Authors:**

**For Unreal Engine Skills:**
- [ ] References Epic Games official documentation
- [ ] Uses UBT (UnrealBuildTool) correctly
- [ ] Follows plugin structure conventions
- [ ] Module registration pattern matches samples

**For Houdini Skills:**
- [ ] References SideFX documentation
- [ ] Uses `hython` for automation (not regular Python)
- [ ] HDA parameter interfaces follow UE naming conventions
- [ ] Uses `$HIP` for relative paths

**For Blender Skills:**
- [ ] References Blender Python API docs
- [ ] Uses `bpy` module correctly
- [ ] FBX export settings match UE import expectations
- [ ] Naming conventions: `M_` (materials), `UCX_` (collisions)

**Documentation Requirement:**
```markdown
### Article V: Follow Official Patterns ✅
- Follows Unreal Build Tool conventions (Build.bat usage)
- Plugin structure matches Epic Games samples
- References: https://docs.unrealengine.com/5.5/en-US/plugins-in-unreal-engine/
```

---

### Article VI: Context Efficiency Through Architecture

**Constitutional Requirement:**
> Minimize context consumption at every level.

#### Automated Checks

**1. Context Efficiency Documentation Detection**

**Keyword Search:**
```python
has_context_metrics = False
if "context reduction" in content.lower() or "context efficiency" in content.lower():
    has_context_metrics = True
    details.append("✅ Context efficiency documented in SKILL.md")
```

**Why These Keywords:**
- "context reduction": Direct mention of savings
- "context efficiency": Architectural discussion
- Case-insensitive: Matches variations in writing style

---

**2. Metrics Extraction**

**Regex Pattern:**
```python
metrics_match = re.search(r'(\d+)%\s+(?:context\s+)?(?:reduction|savings)', content, re.IGNORECASE)
if metrics_match:
    pct = int(metrics_match.group(1))
    details.append(f"   Context reduction: {pct}%")
    if pct < 50:
        details.append(f"   ⚠️ <50% reduction - consider more aggressive refactoring")
```

**Pattern Breakdown:**
- `(\d+)%`: Capture percentage value (e.g., "73%")
- `(?:context\s+)?`: Optional "context" word
- `(?:reduction|savings)`: Matches "reduction" or "savings"
- `re.IGNORECASE`: Case-insensitive matching

**Example Matches:**
```markdown
73% context reduction     ✅ Extracts: 73
60% reduction             ✅ Extracts: 60
Context savings: 45%      ✅ Extracts: 45
70% context efficiency    ❌ Doesn't match (needs "reduction" or "savings")
```

**Threshold:**
- **<50% reduction:** Warning (minimal benefit)
- **≥50% reduction:** Good (constitutional goal met)
- **≥70% reduction:** Excellent (well-designed skill)

---

**3. Progressive Disclosure Structure Check**

**Reference Directory Verification:**
```python
reference_dir = self.skill_dir / "reference"
if reference_dir.exists():
    ref_files = list(reference_dir.glob("*.md"))
    details.append(f"✅ Progressive disclosure: {len(ref_files)} reference file(s)")
else:
    details.append("⚠️ No reference/ directory - consider for future content")
```

**YAML Frontmatter Check:**
```python
has_frontmatter = content.strip().startswith("---")
if has_frontmatter:
    details.append("✅ YAML frontmatter present (metadata layer)")
```

**Interpretation:**
- **Metadata (YAML) + SKILL.md + Reference docs:** Full progressive disclosure ✅
- **Metadata + SKILL.md only:** Acceptable if skill is simple
- **No metadata:** Failure (Article VIII violation)

---

**4. Validation Outcomes**

| Condition | Status | Message |
|-----------|--------|---------|
| Has context metrics OR reference docs | ✅ PASS | "Context efficiency verified" |
| No metrics AND no reference docs | ⚠️ WARN | "Context efficiency not documented" |

**Pass Example:**
```
✅ Context efficiency documented in SKILL.md
   Context reduction: 73%
✅ Progressive disclosure: 2 reference file(s)
✅ YAML frontmatter present (metadata layer)
```

**Warning Example:**
```
⚠️ No reference/ directory - consider for future content
Recommendation: Document context savings in Constitutional Compliance
```

---

**5. Edge Cases**

**Skills with No Metrics Documented:**
- Status: WARN (not FAIL)
- Recommendation: Add context efficiency calculation
- Formula: `(before_lines - after_lines) / before_lines * 100`

**New Skills (No "Before" State):**
- Compare to manual process (no skill)
- Estimate context of loading all reference materials
- Document in Constitutional Compliance section

**Skills with High Line Count but Good Structure:**
- 480 lines but has 3 reference docs: Still efficient
- Progressive disclosure matters more than absolute size

---

### Article VII: Cross-Application Integration Protocol

**Constitutional Requirement:**
> Ensure workflows across Houdini, Blender, Unreal, Nuke coordinate correctly.

#### Automated Checks

**1. Cross-App Workflow Detection**

**Keyword Search:**
```python
cross_app_keywords = [
    "export", "import", "unreal", "houdini", "blender", "nuke",
    ".fbx", ".hda", ".exr", ".abc", "alembic"
]

has_cross_app = any(keyword in content.lower() for keyword in cross_app_keywords)
```

**Why These Keywords:**
- Application names: "unreal", "houdini", "blender", "nuke"
- File formats: ".fbx", ".hda", ".exr", ".abc"
- Workflow terms: "export", "import", "alembic"

**Example Skill Content:**
```markdown
## Workflow: Export HDA for Unreal Engine

1. Export HDA using Houdini Engine format
2. Import .hda into Unreal Content Browser
3. Configure material assignments

→ Detected: "houdini", "unreal", "export", ".hda" ✅
```

---

**2. File Format Standards Check**

**Pattern Matching:**
```python
file_format_keywords = [".fbx", ".hda", ".exr", ".abc", ".uasset"]
has_file_format = any(fmt in content for fmt in file_format_keywords)
```

**Why These Formats:**
- `.fbx`: Universal 3D format (Blender → Unreal, Houdini → Unreal)
- `.hda`: Houdini Digital Asset (Houdini → Unreal)
- `.exr`: High dynamic range images (Nuke → Unreal)
- `.abc`: Alembic (animation/geometry interchange)
- `.uasset`: Unreal native format

**Compliance Example:**
```markdown
### File Formats

**Supported:**
- FBX 2020 (Blender → Unreal)
- HDA (Houdini Engine 20.0)
- EXR sequences (ACES color space)

→ Detected: ".fbx", ".hda", ".exr" ✅
```

---

**3. Asset Naming Convention Check**

**Pattern Matching:**
```python
naming_keywords = ["SM_", "SK_", "M_", "T_", "naming convention", "asset naming"]
has_naming = any(kw in content for kw in naming_keywords)
```

**Why These Prefixes:**
- `SM_`: Static Mesh (Unreal standard)
- `SK_`: Skeletal Mesh (Unreal standard)
- `M_`: Material (Unreal standard)
- `T_`: Texture (Unreal standard)
- "naming convention": Explicit documentation

**Compliance Example:**
```markdown
### Asset Naming

Follow Unreal Engine conventions:
- Static meshes: SM_AssetName
- Materials: M_AssetName
- Textures: T_AssetName_Type

→ Detected: "SM_", "M_", "T_", "naming convention" ✅
```

---

**4. Validation Outcomes**

| Condition | Status | Message |
|-----------|--------|---------|
| No cross-app keywords | ⊘ SKIP | "Not applicable (no cross-app integration)" |
| Has file formats AND naming conventions | ✅ PASS | "Cross-app integration documented" |
| Missing file formats OR naming conventions | ⚠️ WARN | "Cross-app integration incomplete" |

**Pass Example:**
```
✅ File format standards documented
✅ Asset naming conventions documented
```

**Warning Example:**
```
⚠️ Consider documenting:
   - File format standards (.fbx, .hda, etc.)
   - Asset naming conventions (SM_, M_, etc.)
```

---

**5. Edge Cases**

**Single-Application Skills:**
- Example: unreal-plugin-compiler (Unreal only)
- No cross-app workflows
- Outcome: SKIP (not applicable)

**Documentation Skills:**
- Example: vfx-documentation (meta skill)
- Mentions multiple apps but doesn't export assets
- May trigger detection but SKIP is appropriate

**Internal Workflows:**
- Example: Unreal → Unreal (level streaming)
- Not cross-application in constitutional sense
- Outcome: SKIP or PASS (depending on interpretation)

---

### Article VIII: Documentation Standards

**Constitutional Requirement:**
> Ensure consistent, discoverable, maintainable documentation.

#### Automated Checks

**1. YAML Frontmatter Validation**

**Detection:**
```python
if not content.strip().startswith("---"):
    issues.append("❌ Missing YAML frontmatter")
else:
    parts = content.split("---", 2)
    if len(parts) >= 2:
        frontmatter = parts[1]
        required_fields = ["name:", "description:", "model:"]
        for field in required_fields:
            if field not in frontmatter:
                issues.append(f"❌ Missing frontmatter field: {field}")
```

**Required Fields:**
- `name:` - Skill identifier (matches directory name)
- `description:` - What + When + Triggers formula
- `model:` - sonnet or haiku

**Optional Fields:**
- `triggers:` - Explicit trigger phrases (recommended)
- `version:` - Can be in frontmatter or header

**Example Valid Frontmatter:**
```yaml
---
name: unreal-vfx-automation
description: Automate VFX workflows in Unreal Engine 5.5...
triggers:
  - "foreground plate"
  - "image sequence"
model: sonnet
---
```

---

**2. Required Sections Check**

**Pattern Matching:**
```python
required_sections = [
    ("Version", r"(?:Version|version).*\d+\.\d+\.\d+"),
    ("Last Updated", r"Last Updated"),
    ("Dependencies", r"Dependencies"),
    ("Quick Start", r"##.*Quick Start"),
    ("Standard Workflows", r"##.*(?:Standard )?Workflows?"),
    ("Troubleshooting", r"##.*Troubleshooting"),
    ("Reference Documentation", r"##.*Reference Documentation"),
    ("Constitutional Compliance", r"##.*Constitutional Compliance"),
    ("Version History", r"##.*Version History"),
]

for section_name, pattern in required_sections:
    if re.search(pattern, content, re.IGNORECASE):
        details.append(f"✅ {section_name} section present")
    else:
        issues.append(f"❌ Missing section: {section_name}")
```

**Section Explanations:**

| Section | Pattern | Why Required |
|---------|---------|--------------|
| Version | `Version.*\d+\.\d+\.\d+` | Semantic versioning (Article VIII) |
| Last Updated | `Last Updated` | Track currency of documentation |
| Dependencies | `Dependencies` | Required software/libraries |
| Quick Start | `##.*Quick Start` | Fast onboarding (most common use case) |
| Standard Workflows | `##.*Workflows?` | Common patterns (3-5 workflows) |
| Troubleshooting | `##.*Troubleshooting` | Error resolution |
| Reference Documentation | `##.*Reference Documentation` | Links to detailed guides |
| Constitutional Compliance | `##.*Constitutional Compliance` | Demonstrate adherence to principles |
| Version History | `##.*Version History` | Change tracking |

**Case Insensitive:** Matches "Quick Start", "quick start", "QUICK START"

**Flexible Headers:** Matches "## Quick Start", "### Quick Start", etc.

---

**3. Semantic Versioning Check**

**Regex Pattern:**
```python
version_match = re.search(r'[Vv]ersion.*?(\d+\.\d+\.\d+)', content)
if version_match:
    details.append(f"✅ Semantic versioning: {version_match.group(1)}")
else:
    issues.append("❌ Version not in semantic format (X.Y.Z)")
```

**Pattern Breakdown:**
- `[Vv]ersion`: Matches "Version" or "version"
- `.*?`: Non-greedy match (minimal characters)
- `(\d+\.\d+\.\d+)`: Captures X.Y.Z format

**Example Matches:**
```markdown
**Version:** 1.0.0       ✅ Extracts: 1.0.0
Version: 2.1.3           ✅ Extracts: 2.1.3
Skill Version: 1.2.0     ✅ Extracts: 1.2.0
v1.5                     ❌ Doesn't match (needs PATCH number)
Version 1                ❌ Doesn't match (needs MINOR.PATCH)
```

**SemVer Requirement:**
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

---

**4. Validation Outcomes**

| Condition | Status | Message |
|-----------|--------|---------|
| Any required section missing OR invalid version | ❌ FAIL | "Documentation standards incomplete" |
| All sections present AND valid version | ✅ PASS | "Documentation standards compliant" |

**Failure Example:**
```
❌ Missing frontmatter field: description:
❌ Missing section: Troubleshooting
❌ Version not in semantic format (X.Y.Z)
✅ Quick Start section present
✅ Standard Workflows section present
```

**Pass Example:**
```
✅ name:
✅ description:
✅ model:
✅ Version section present
✅ Last Updated section present
✅ Dependencies section present
✅ Quick Start section present
✅ Standard Workflows section present
✅ Troubleshooting section present
✅ Reference Documentation section present
✅ Constitutional Compliance section present
✅ Version History section present
✅ Semantic versioning: 1.0.0
```

---

**5. Edge Cases**

**Version in Frontmatter vs Header:**
- Pattern searches entire file (finds either location)
- Flexibility allows different styles

**Section Name Variations:**
- "Workflows" vs "Standard Workflows": Both match
- "Troubleshooting" vs "Troubleshooting Guide": First matches

**Missing Optional Sections:**
- "Advanced Techniques" not required (recommended but optional)
- "Critical First Step" not required (only for risky operations)

---

### Article IX: Agent Versioning and Naming Conventions

**Constitutional Requirement:**
> Maintain stable agent names, prevent confusion from multiple versions.

#### Validation Approach

**Status:** Not applicable to skills (SKIP in automated validation)

**Why Not Applicable:**
- Article IX applies to agents (`.claude/agents/*.md`)
- Skills use directory-based structure (`.claude/skills/skill-name/`)
- Skills don't have versioned filenames (version is in SKILL.md header)

**Validation Logic:**
```python
def validate_article_ix(self) -> None:
    """Article IX: Not applicable to skills (agents only)"""
    self.results.append(ValidationResult(
        article="Article IX",
        status="SKIP",
        message="Not applicable (skills use directory structure)",
        details=["Article IX applies to agents, not skills"]
    ))
```

**Skill Versioning (Different from Agent Versioning):**
- Skills: Directory name is static, version in SKILL.md header
- Agents: Filename is static, version in file header
- Both: Version is metadata, not filename identifier

**Example:**
```
# ✅ CORRECT: Skill versioning
.claude/skills/unreal-vfx-automation/SKILL.md
  → Header: **Version:** 1.0.0

# ✅ CORRECT: Agent versioning
.claude/agents/documentation-specialist.md
  → Header: version: 2.0.0

# ❌ WRONG: Versioned skill directory
.claude/skills/unreal-vfx-automation-v2/
```

---

## Validation Report Format

### Console Output

**Summary Format:**
```
📋 Constitutional Compliance Report: skill-name

Article I: ✅ PASS
  Scripts are general-purpose
  ✅ No hard-coded paths detected in 3 script(s)
  ✅ Parameterization verified (argparse/sys.argv)

Article III: ✅ PASS
  Progressive disclosure compliant
  ✅ 470 lines (<500 limit)
  Margin: 30 lines (6.0% buffer)
  ✅ Reference directory: 2 file(s)

[... all articles ...]

Overall: ✅ PASS (7/7 automated checks, 2 manual verifications needed)
```

**Status Icons:**
- ✅ PASS
- ❌ FAIL
- ⚠️ WARN
- ⊘ SKIP

---

### Markdown Report

**Generated with `--report` flag:**

**Structure:**
```markdown
# Constitutional Compliance Report: skill-name

**Generated:** 2025-10-25 14:30:00
**Skill Path:** C:\path\to\.claude\skills\skill-name

---

## Summary

- **PASS:** 7
- **FAIL:** 0
- **WARN:** 2
- **SKIP:** 2

**Overall Status:** ✅ PASS

---

## Detailed Results

### Article I: ✅ PASS

**Result:** Scripts are general-purpose

**Details:**
- ✅ No hard-coded paths detected in 3 script(s)
- ✅ Parameterization verified (argparse/sys.argv)

---

[... all articles ...]
```

**Report Location:**
```
ClaudeCode/development/reports/SKILL_NAME_COMPLIANCE_REPORT.md
```

---

## Edge Cases and Special Handling

### Documentation-Only Skills

**Example:** vfx-documentation

**Characteristics:**
- No scripts directory
- No executable code
- Focuses on processes and standards

**Validation Adjustments:**
- Article I: SKIP (no scripts)
- Article IV: SKIP (no scripts to test)
- Article VII: May PASS (documents cross-app workflows)

---

### MCP-Based Skills

**Example:** Skill that only defines MCP tools

**Characteristics:**
- No direct Python scripts
- MCP tools in separate server
- SKILL.md documents MCP usage

**Validation Adjustments:**
- Article I: SKIP (scripts are in MCP server)
- Article II: Document why MCP chosen
- Article IV: SKIP (testing happens in MCP server)

---

### Compact Skills (<300 Lines)

**Example:** skill-creation-update (364 lines)

**Characteristics:**
- Very focused functionality
- Scripts do heavy lifting
- Minimal reference docs needed

**Validation:**
- Article III: PASS (no minimum requirement)
- Context efficiency still applies (compare to manual process)

---

### Multi-Application Skills

**Example:** Houdini → Unreal pipeline

**Characteristics:**
- Involves 2+ VFX applications
- Cross-app file format handling
- Asset naming conventions critical

**Validation Emphasis:**
- Article VII: Critical (MUST document formats and naming)
- Article V: Verify both tool patterns followed

---

## False Positive Mitigation

### Hard-Coded Path Detection

**Problem:** Comments or documentation contain example paths

**Example:**
```python
# Example usage:
# python export.py CharacterRig --output "C:\Exports\MyAsset"
#                                           ^^^^^^^^^ False positive
```

**Current Behavior:**
- Detects "C:\" in comment
- Reports as potential violation

**Mitigation:**
- Manual review of findings
- Comments/strings are lower priority than code
- Future: Distinguish code vs comments via AST parsing

---

### Project Name Detection

**Problem:** Generic words trigger false positives

**Example:**
```python
# Avoid MyProject naming patterns
project_types = ["MyProject", "TestProject", "DemoProject"]
```

**Current Behavior:**
- Detects "MyProject" string
- Reports as hard-coded name

**Mitigation:**
- Manual review (is this a configuration list or hard-coded value?)
- Future: AST analysis to distinguish variable assignments vs references

---

### Test Files with Hard-Coded Paths

**Problem:** Test files legitimately have test data paths

**Example:**
```python
# test_export.py
def test_export():
    test_asset = "C:\\TestData\\sample_asset.fbx"  # Test fixture
```

**Current Behavior:**
- Detects hard-coded path
- Reports as violation

**Mitigation:**
- Currently: Manual review (test files are expected to have fixtures)
- Future: Skip validation for `test_*.py` and `*_test.py` files

---

## Extending Validation Logic

### Adding New Checks

**Process:**
1. Identify constitutional requirement
2. Determine if automatable (regex, pattern matching)
3. Define validation function
4. Add test cases
5. Update this documentation

**Example: Adding Trigger Phrase Validation**

**Requirement:** Article VIII could require 3-7 trigger phrases

**Implementation:**
```python
def validate_trigger_count(self) -> None:
    """Check if 3-7 trigger phrases defined"""
    with open(self.skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter
    parts = content.split("---", 2)
    if len(parts) < 2:
        return ValidationResult(status="WARN", message="No frontmatter")

    frontmatter = parts[1]

    # Count triggers
    trigger_count = frontmatter.count("  - \"")  # YAML list items

    if trigger_count < 3:
        return ValidationResult(status="WARN",
                                message=f"Only {trigger_count} triggers (recommend 3-7)")
    elif trigger_count > 7:
        return ValidationResult(status="WARN",
                                message=f"{trigger_count} triggers (recommend 3-7, may be too many)")
    else:
        return ValidationResult(status="PASS",
                                message=f"{trigger_count} trigger phrases (optimal)")
```

---

### Future Constitutional Amendments

**When Constitution Updates:**
1. Update validation logic in `validate_skill.py`
2. Update this documentation (constitutional_validation.md)
3. Test against existing skills
4. Document breaking changes

**Example: Article X (Hypothetical Future Addition)**

If constitution adds Article X: "Performance Standards":
1. Add `validate_article_x()` method
2. Define automated checks (script execution time, build duration)
3. Update report format to include Article X
4. Document validation logic in this guide

---

**Last Updated:** 2025-10-25
**Validator Version:** 1.0.0 (validate_skill.py)
**Constitution Version:** 1.1.0 (VFX_SKILL_CONSTITUTION.md)
**Related:** skill_template_guide.md (template usage), VFX_SKILL_UPDATE_CHECKLIST.md (manual checklist)
