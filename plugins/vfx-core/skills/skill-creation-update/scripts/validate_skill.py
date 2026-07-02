#!/usr/bin/env python3
"""
Validate VFX Agent Skill constitutional compliance across all 9 articles.
Now supports Agent OS standards validation.

Purpose: Automated constitutional validation for skill quality assurance
Article I: Detects hard-coded paths/project names in scripts
Article III: Enforces <500 line limit for SKILL.md (Skills) or standards files (Agent OS)
Article IV: Verifies independent testing evidence
Article VI: Validates context efficiency through progressive disclosure
Article VIII: Checks documentation standards compliance

Usage:
    # Validate Claude Code skill
    python validate_skill.py SKILL_NAME [--report]

    # Validate Agent OS standard
    python validate_skill.py STANDARD_NAME --agent-os [--report]

    --agent-os: Validate Agent OS standard instead of Claude Code skill
    --report: Generate detailed markdown compliance report

Author: VFX Skill System
Version: 1.1.0
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    article: str
    status: str  # "PASS", "FAIL", "WARN", "SKIP"
    message: str
    details: list[str]


class SkillValidator:
    """Validates VFX Agent Skills and Agent OS standards against constitutional requirements."""

    def __init__(self, skill_name: str, skill_path: Optional[Path] = None, is_agent_os: bool = False):
        """
        Initialize validator.

        Args:
            skill_name: Name of skill or standard to validate
            skill_path: Path to .claude/skills/ or agent-os/profiles/vfx/standards/ (auto-detect if None)
            is_agent_os: True if validating Agent OS standard, False for Claude Code skill
        """
        self.skill_name = skill_name
        self.is_agent_os = is_agent_os

        if skill_path is None:
            script_dir = Path(__file__).parent.absolute()
            if is_agent_os:
                # Navigate to agent-os/profiles/vfx/standards/
                skill_path = script_dir.parent.parent.parent.parent / "ClaudeCode" / "agent-os" / "profiles" / "vfx" / "standards"
            else:
                # Auto-detect .claude/skills/
                skill_path = script_dir.parent.parent

        if is_agent_os:
            # Agent OS standards are single .md files
            self.skill_dir = skill_path
            self.skill_md = skill_path / f"{skill_name}.md"
        else:
            # Claude Code skills are directories with SKILL.md
            self.skill_dir = skill_path / skill_name
            self.skill_md = self.skill_dir / "SKILL.md"
        
        self.results: list[ValidationResult] = []

    def validate_all(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if all applicable checks pass, False otherwise
        """
        # Check file exists
        if not self.skill_md.exists():
            entity_type = "Agent OS standard" if self.is_agent_os else "Skill"
            print(f"❌ {entity_type} not found: {self.skill_name}")
            print(f"   Expected path: {self.skill_md}")
            return False

        # Check constitutional headers for Agent OS standards
        if self.is_agent_os:
            self.validate_agent_os_headers()

        # Run validations
        self.validate_article_i()
        self.validate_article_iii()
        self.validate_article_iv()
        self.validate_article_v()
        self.validate_article_vi()
        self.validate_article_vii()
        self.validate_article_viii()
        self.validate_article_ix()

        # Calculate overall pass/fail
        failures = [r for r in self.results if r.status == "FAIL"]
        return len(failures) == 0

    def validate_agent_os_headers(self) -> None:
        """
        Validate Agent OS standard constitutional headers (YAML frontmatter).

        Required fields:
        - validated_by: VFX_SKILL_CONSTITUTION.md vX.X.X
        - last_validation: YYYY-MM-DD
        - articles_compliant: [I, II, III, ...]
        - tool_version: Tool name + version
        """
        with open(self.skill_md, 'r', encoding='utf-8') as f:
            content = f.read()

        details = []
        issues = []

        if not content.strip().startswith("---"):
            issues.append("❌ Missing YAML frontmatter with constitutional headers")
            self.results.append(ValidationResult(
                article="Agent OS Headers",
                status="FAIL",
                message="Constitutional headers missing",
                details=issues
            ))
            return

        # Extract frontmatter
        parts = content.split("---", 2)
        if len(parts) < 2:
            issues.append("❌ Malformed YAML frontmatter")
            self.results.append(ValidationResult(
                article="Agent OS Headers",
                status="FAIL",
                message="Constitutional headers malformed",
                details=issues
            ))
            return

        frontmatter = parts[1]

        # Check required fields
        required_fields = {
            "validated_by": r"validated_by:\s*VFX_SKILL_CONSTITUTION\.md\s+v\d+\.\d+\.\d+",
            "last_validation": r"last_validation:\s*\d{4}-\d{2}-\d{2}",
            "articles_compliant": r"articles_compliant:\s*\[.*\]",
            "tool_version": r"tool_version:"
        }

        for field_name, pattern in required_fields.items():
            if re.search(pattern, frontmatter):
                details.append(f"✅ {field_name}")
            else:
                issues.append(f"❌ Missing or malformed: {field_name}")

        # Extract articles_compliant list
        articles_match = re.search(r"articles_compliant:\s*\[(.*?)\]", frontmatter)
        if articles_match:
            articles_str = articles_match.group(1)
            articles = [a.strip() for a in articles_str.split(",")]
            details.append(f"   Compliant articles: {', '.join(articles)}")

        if issues:
            self.results.append(ValidationResult(
                article="Agent OS Headers",
                status="FAIL",
                message="Constitutional headers incomplete",
                details=issues + details
            ))
        else:
            self.results.append(ValidationResult(
                article="Agent OS Headers",
                status="PASS",
                message="Constitutional headers valid",
                details=details
            ))

    def validate_article_i(self) -> None:
        """
        Article I: General Purpose Scripts

        Checks:
        - No hard-coded paths (C:\\, D:\\, /Users/, /home/)
        - No hard-coded project names (common patterns)
        - Parameterization (argparse, sys.argv)
        - Relative paths preferred
        """
        scripts_dir = self.skill_dir / "scripts"
        details = []

        if not scripts_dir.exists():
            self.results.append(ValidationResult(
                article="Article I",
                status="SKIP",
                message="No scripts directory (documentation-only skill)",
                details=["Scripts directory not found - skill may be doc-only or MCP-based"]
            ))
            return

        # Find Python scripts
        scripts = list(scripts_dir.glob("*.py"))
        if not scripts:
            self.results.append(ValidationResult(
                article="Article I",
                status="SKIP",
                message="No Python scripts found",
                details=["No .py files in scripts/ - may use MCP tools instead"]
            ))
            return

        # Check for hard-coded paths
        hard_coded_patterns = [
            (r'[CDE]:\\\\', "Windows absolute path"),
            (r'/Users/', "macOS user path"),
            (r'/home/', "Linux home path"),
            (r'[CDE]:\\', "Windows path (single backslash)"),
        ]

        # Check for hard-coded project names (common patterns)
        project_patterns = [
            (r'MyProject', "Generic 'MyProject' name"),
            (r'TestProject', "Generic 'TestProject' name"),
            (r'project_name\s*=\s*["\'][A-Z]', "Hard-coded project_name variable"),
        ]

        has_hard_coded = False
        has_argparse = False

        for script in scripts:
            with open(script, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check hard-coded paths
            for pattern, desc in hard_coded_patterns:
                if re.search(pattern, content):
                    details.append(f"❌ {script.name}: {desc} detected")
                    has_hard_coded = True

            # Check hard-coded project names
            for pattern, desc in project_patterns:
                if re.search(pattern, content):
                    details.append(f"❌ {script.name}: {desc}")
                    has_hard_coded = True

            # Check for parameterization
            if 'argparse' in content or 'sys.argv' in content:
                has_argparse = True

        if has_hard_coded:
            details.append("Fix: Replace hard-coded values with CLI parameters or environment variables")
            self.results.append(ValidationResult(
                article="Article I",
                status="FAIL",
                message="Hard-coded paths or project names detected",
                details=details
            ))
        elif not has_argparse and len(scripts) > 0:
            self.results.append(ValidationResult(
                article="Article I",
                status="WARN",
                message="No argparse/sys.argv found - verify parameterization",
                details=[f"Scripts: {', '.join(s.name for s in scripts)}"]
            ))
        else:
            details.append(f"✅ No hard-coded paths detected in {len(scripts)} script(s)")
            details.append(f"✅ Parameterization verified (argparse/sys.argv)")
            self.results.append(ValidationResult(
                article="Article I",
                status="PASS",
                message="Scripts are general-purpose",
                details=details
            ))

    def validate_article_iii(self) -> None:
        """
        Article III: Progressive Disclosure (<500 Lines)

        Checks:
        - SKILL.md line count <500 (Skills)
        - Agent OS standards can exceed 500 but track context efficiency
        - Warn if >450 (approaching limit)
        - Reference directory exists
        - Reference docs mentioned in SKILL.md
        """
        # Count lines
        with open(self.skill_md, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        line_count = len(lines)

        details = []
        
        if self.is_agent_os:
            # Agent OS standards: Track but don't enforce <500 line limit
            details.append(f"📊 {line_count} lines (Agent OS standard)")
            
            # Calculate context efficiency
            # Typical before: Complete tool docs (1000-2000 lines)
            # After: Focused standard (300-600 lines)
            if line_count < 400:
                details.append(f"✅ Excellent context efficiency (<400 lines)")
            elif line_count < 550:
                details.append(f"✅ Good context efficiency (400-550 lines)")
            else:
                details.append(f"⚠️  Consider refactoring (>550 lines)")
                details.append("   Complex topics acceptable, but aim for <550")
            
            self.results.append(ValidationResult(
                article="Article III",
                status="PASS",
                message="Progressive disclosure (Agent OS mode)",
                details=details
            ))
            return

        # Claude Code Skills: Enforce strict <500 line limit
        reference_dir = self.skill_dir / "reference"

        if line_count > 500:
            margin = line_count - 500
            self.results.append(ValidationResult(
                article="Article III",
                status="FAIL",
                message=f"SKILL.md exceeds 500 line limit ({line_count} lines)",
                details=[
                    f"❌ {line_count} lines (>{500} limit)",
                    f"Overage: {margin} lines ({margin / 500 * 100:.1f}%)",
                    "Fix: Move detailed content to reference/*.md",
                    "Example: Troubleshooting (>100 lines) → reference/troubleshooting_guide.md"
                ]
            ))
        elif line_count > 450:
            margin = 500 - line_count
            buffer_pct = margin / 500 * 100
            details.append(f"⚠️  {line_count} lines (approaching 500 limit)")
            details.append(f"Margin: {margin} lines ({buffer_pct:.1f}% buffer)")
            details.append("Consider moving content to reference docs before adding more")
            self.results.append(ValidationResult(
                article="Article III",
                status="WARN",
                message="SKILL.md approaching 500 line limit",
                details=details
            ))
        else:
            margin = 500 - line_count
            buffer_pct = margin / 500 * 100
            details.append(f"✅ {line_count} lines (<500 limit)")
            details.append(f"Margin: {margin} lines ({buffer_pct:.1f}% buffer)")

            # Check reference directory
            if reference_dir.exists():
                ref_files = list(reference_dir.glob("*.md"))
                details.append(f"✅ Reference directory: {len(ref_files)} file(s)")
            else:
                details.append("⚠️  No reference/ directory (may not be needed)")

            self.results.append(ValidationResult(
                article="Article III",
                status="PASS",
                message="Progressive disclosure compliant",
                details=details
            ))

    def validate_article_iv(self) -> None:
        """
        Article IV: Test Independently Before Agent Integration

        Checks:
        - Scripts have if __name__ == "__main__" blocks
        - Test files exist (test_*.py, *_test.py)
        - Session documentation mentions testing
        """
        scripts_dir = self.skill_dir / "scripts"
        details = []

        if not scripts_dir.exists() or not list(scripts_dir.glob("*.py")):
            self.results.append(ValidationResult(
                article="Article IV",
                status="SKIP",
                message="No scripts to test",
                details=["Skill may be documentation-only or MCP-based"]
            ))
            return

        # Check for __main__ blocks
        scripts = list(scripts_dir.glob("*.py"))
        has_main_block = False

        for script in scripts:
            with open(script, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'if __name__ == "__main__"' in content:
                has_main_block = True
                details.append(f"✅ {script.name}: Has __main__ block")

        # Check for test files
        test_files = (
            list(scripts_dir.glob("test_*.py")) +
            list(scripts_dir.glob("*_test.py"))
        )

        # Check session documentation
        session_docs = []
        parent_dir = self.skill_dir.parent.parent  # Go up to project root
        if (parent_dir / "development").exists():
            session_docs = list((parent_dir / "development").glob("Session_*.md"))

        if has_main_block:
            details.append(f"✅ Independent testing possible (__main__ blocks present)")
        else:
            details.append("⚠️  No __main__ blocks found - add for independent testing")

        if test_files:
            details.append(f"✅ Test files: {', '.join(f.name for f in test_files)}")

        if session_docs:
            details.append(f"✅ Session docs available: {len(session_docs)} file(s)")

        # Determine status
        if has_main_block or test_files:
            self.results.append(ValidationResult(
                article="Article IV",
                status="PASS",
                message="Independent testing verified",
                details=details
            ))
        else:
            details.append("Recommendation: Add if __name__ == '__main__' blocks to scripts")
            self.results.append(ValidationResult(
                article="Article IV",
                status="WARN",
                message="No clear testing evidence",
                details=details
            ))

    def validate_article_v(self) -> None:
        """
        Article V: Follow Official Tool/Engine Patterns

        Manual verification - output reminder to user
        """
        self.results.append(ValidationResult(
            article="Article V",
            status="SKIP",
            message="Manual verification required",
            details=[
                "⚠️  Verify tool/engine documentation is referenced",
                "Check: Quick Start and Workflows cite official docs",
                "Example: 'See Unreal Engine 5.5 documentation for...'",
                "Example: 'Follows Houdini 20.0 Python API patterns'"
            ]
        ))

    def validate_article_vi(self) -> None:
        """
        Article VI: Context Efficiency Through Architecture

        Checks:
        - Context savings metrics in Constitutional Compliance
        - Progressive disclosure structure
        - Metadata → SKILL.md → reference pattern
        """
        details = []

        # Read SKILL.md
        with open(self.skill_md, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for context efficiency documentation
        has_context_metrics = False
        if "context reduction" in content.lower() or "context efficiency" in content.lower():
            has_context_metrics = True
            details.append("✅ Context efficiency documented in SKILL.md")

            # Extract metrics if present
            metrics_match = re.search(r'(\d+)%\s+(?:context\s+)?(?:reduction|savings)', content, re.IGNORECASE)
            if metrics_match:
                pct = int(metrics_match.group(1))
                details.append(f"   Context reduction: {pct}%")
                if pct < 50:
                    details.append(f"   ⚠️  <50% reduction - consider more aggressive refactoring")

        # Check progressive disclosure structure
        reference_dir = self.skill_dir / "reference"
        if reference_dir.exists():
            ref_files = list(reference_dir.glob("*.md"))
            details.append(f"✅ Progressive disclosure: {len(ref_files)} reference file(s)")
        else:
            details.append("⚠️  No reference/ directory - consider for future content")

        # Check metadata (YAML frontmatter)
        has_frontmatter = content.strip().startswith("---")
        if has_frontmatter:
            details.append("✅ YAML frontmatter present (metadata layer)")

        if has_context_metrics or (reference_dir.exists() and len(list(reference_dir.glob("*.md"))) > 0):
            self.results.append(ValidationResult(
                article="Article VI",
                status="PASS",
                message="Context efficiency verified",
                details=details
            ))
        else:
            details.append("Recommendation: Document context savings in Constitutional Compliance")
            self.results.append(ValidationResult(
                article="Article VI",
                status="WARN",
                message="Context efficiency not documented",
                details=details
            ))

    def validate_article_vii(self) -> None:
        """
        Article VII: Cross-Application Integration Protocol

        Optional check - only applicable if skill involves cross-app workflows
        """
        # Read SKILL.md
        with open(self.skill_md, 'r', encoding='utf-8') as f:
            content = f.read()

        # Keywords suggesting cross-app integration
        cross_app_keywords = [
            "export", "import", "unreal", "houdini", "blender", "nuke",
            ".fbx", ".hda", ".exr", ".abc", "alembic"
        ]

        has_cross_app = any(keyword in content.lower() for keyword in cross_app_keywords)

        if not has_cross_app:
            self.results.append(ValidationResult(
                article="Article VII",
                status="SKIP",
                message="Not applicable (no cross-app integration)",
                details=["Skill does not involve cross-application workflows"]
            ))
        else:
            details = []
            # Check for file format documentation
            file_format_keywords = [".fbx", ".hda", ".exr", ".abc", ".uasset"]
            has_file_format = any(fmt in content for fmt in file_format_keywords)

            # Check for asset naming conventions
            naming_keywords = ["SM_", "SK_", "M_", "T_", "naming convention", "asset naming"]
            has_naming = any(kw in content for kw in naming_keywords)

            if has_file_format:
                details.append("✅ File format standards documented")

            if has_naming:
                details.append("✅ Asset naming conventions documented")

            if has_file_format and has_naming:
                self.results.append(ValidationResult(
                    article="Article VII",
                    status="PASS",
                    message="Cross-app integration documented",
                    details=details
                ))
            else:
                details.append("⚠️  Consider documenting:")
                if not has_file_format:
                    details.append("   - File format standards (.fbx, .hda, etc.)")
                if not has_naming:
                    details.append("   - Asset naming conventions (SM_, M_, etc.)")
                self.results.append(ValidationResult(
                    article="Article VII",
                    status="WARN",
                    message="Cross-app integration incomplete",
                    details=details
                ))

    def validate_article_viii(self) -> None:
        """
        Article VIII: Documentation Standards

        Checks:
        - YAML frontmatter with required fields
        - Required sections present (Skills)
        - Agent OS standards have different requirements
        - Description follows "What + When + Triggers" formula (Skills)
        - Semantic versioning (X.Y.Z) (Skills)
        """
        with open(self.skill_md, 'r', encoding='utf-8') as f:
            content = f.read()

        details = []
        issues = []

        # Check YAML frontmatter
        if not content.strip().startswith("---"):
            issues.append("❌ Missing YAML frontmatter")
        else:
            parts = content.split("---", 2)
            if len(parts) >= 2:
                frontmatter = parts[1]
                
                if self.is_agent_os:
                    # Agent OS standards: Different required fields
                    required_fields = [
                        "validated_by:",
                        "last_validation:",
                        "articles_compliant:",
                        "tool_version:"
                    ]
                else:
                    # Claude Code skills: Official Anthropic format
                    # Reference: https://code.claude.com/docs/en/skills
                    required_fields = ["name:", "description:"]
                    # Optional: allowed-tools:
                
                for field in required_fields:
                    if field not in frontmatter:
                        issues.append(f"❌ Missing frontmatter field: {field}")
                    else:
                        details.append(f"✅ {field.rstrip(':')}")

        if self.is_agent_os:
            # Agent OS standards: Check for standard sections
            required_sections = [
                ("Overview", r"##.*Overview"),
                ("Core Patterns", r"##.*(?:Core )?Patterns?"),
                ("Article I Examples", r"##.*Article I"),
                ("MCP Integration", r"##.*MCP"),
            ]
        else:
            # Claude Code skills: Original required sections
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
                # Only warn for Agent OS (some sections optional)
                if self.is_agent_os:
                    details.append(f"⚠️  {section_name} section recommended")
                else:
                    issues.append(f"❌ Missing section: {section_name}")

        # Check semantic versioning (Skills only)
        if not self.is_agent_os:
            version_match = re.search(r'[Vv]ersion.*?(\d+\.\d+\.\d+)', content)
            if version_match:
                details.append(f"✅ Semantic versioning: {version_match.group(1)}")
            else:
                issues.append("❌ Version not in semantic format (X.Y.Z)")

        # Determine status
        if issues:
            self.results.append(ValidationResult(
                article="Article VIII",
                status="FAIL",
                message="Documentation standards incomplete",
                details=issues + details
            ))
        else:
            self.results.append(ValidationResult(
                article="Article VIII",
                status="PASS",
                message="Documentation standards compliant",
                details=details
            ))

    def validate_article_ix(self) -> None:
        """
        Article IX: Agent Versioning and Naming Conventions

        Not applicable to skills (agents only)
        """
        self.results.append(ValidationResult(
            article="Article IX",
            status="SKIP",
            message="Not applicable (skills use directory structure)",
            details=["Article IX applies to agents, not skills"]
        ))

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generate detailed compliance report in markdown format.

        Args:
            output_path: Path to save report (optional)

        Returns:
            Report content as string
        """
        report = []
        report.append(f"# Constitutional Compliance Report: {self.skill_name}\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Skill Path:** {self.skill_dir.absolute()}\n")
        report.append("\n---\n\n")

        # Summary
        passed = [r for r in self.results if r.status == "PASS"]
        failed = [r for r in self.results if r.status == "FAIL"]
        warned = [r for r in self.results if r.status == "WARN"]
        skipped = [r for r in self.results if r.status == "SKIP"]

        report.append("## Summary\n\n")
        report.append(f"- **PASS:** {len(passed)}\n")
        report.append(f"- **FAIL:** {len(failed)}\n")
        report.append(f"- **WARN:** {len(warned)}\n")
        report.append(f"- **SKIP:** {len(skipped)}\n")
        report.append(f"\n**Overall Status:** {'✅ PASS' if len(failed) == 0 else '❌ FAIL'}\n\n")
        report.append("---\n\n")

        # Detailed results
        report.append("## Detailed Results\n\n")
        for result in self.results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "WARN": "⚠️",
                "SKIP": "⊘"
            }.get(result.status, "?")

            report.append(f"### {result.article}: {status_icon} {result.status}\n\n")
            report.append(f"**Result:** {result.message}\n\n")
            if result.details:
                report.append("**Details:**\n")
                for detail in result.details:
                    report.append(f"- {detail}\n")
            report.append("\n---\n\n")

        report_content = "".join(report)

        # Save to file if requested
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

        return report_content

    def print_summary(self) -> None:
        """Print human-readable summary to console."""
        import sys
        # Fix Windows console encoding for emojis
        if sys.platform == 'win32':
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except:
                pass
        
        entity_type = "Agent OS Standard" if self.is_agent_os else "Skill"
        print(f"\n[Constitutional Compliance Report: {self.skill_name} ({entity_type})]\n")

        for result in self.results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "WARN": "⚠️",
                "SKIP": "⊘"
            }.get(result.status, "?")

            print(f"{result.article}: {status_icon} {result.status}")
            print(f"  {result.message}")

            # Print first 3 details
            for detail in result.details[:3]:
                print(f"  {detail}")
            if len(result.details) > 3:
                print(f"  ... and {len(result.details) - 3} more")
            print()

        # Overall summary
        passed = [r for r in self.results if r.status == "PASS"]
        failed = [r for r in self.results if r.status == "FAIL"]
        warned = [r for r in self.results if r.status == "WARN"]
        automated = len([r for r in self.results if r.status != "SKIP"])
        manual = len([r for r in self.results if r.status == "SKIP" and "Manual" in r.message])

        overall = "✅ PASS" if len(failed) == 0 else "❌ FAIL"
        print(f"Overall: {overall} ({len(passed)}/{automated} automated checks")
        if manual > 0:
            print(f"         {manual} manual verification(s) needed)")
        else:
            print(")")


def main() -> int:
    """
    Main entry point for skill and Agent OS standard validation.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    parser = argparse.ArgumentParser(
        description="Validate VFX Agent Skill or Agent OS standard constitutional compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate Claude Code skill
    python validate_skill.py unreal-vfx-automation

    # Validate Agent OS standard
    python validate_skill.py unreal-engine-standards --agent-os

    # Generate detailed report
    python validate_skill.py unreal-vfx-automation --report

    # Validate all Agent OS standards
    python validate_skill.py blender-standards --agent-os --report
        """
    )

    parser.add_argument("name", help="Skill or standard name to validate")
    parser.add_argument("--report", action="store_true",
                        help="Generate detailed markdown report")
    parser.add_argument("--agent-os", action="store_true",
                        help="Validate Agent OS standard instead of Claude Code skill")
    parser.add_argument("--skills-path", type=Path,
                        help="Path to .claude/skills or agent-os standards directory (auto-detect if not provided)")

    args = parser.parse_args()

    # Create validator
    validator = SkillValidator(args.name, args.skills_path, is_agent_os=args.agent_os)

    # Run validation
    success = validator.validate_all()

    # Print summary
    validator.print_summary()

    # Generate report if requested
    if args.report:
        # Determine report path
        script_dir = Path(__file__).parent.absolute()
        reports_dir = script_dir.parent.parent.parent.parent / "ClaudeCode" / "development" / "reports"
        
        if args.agent_os:
            report_path = reports_dir / f"AGENT_OS_{args.name}_COMPLIANCE_REPORT.md"
        else:
            report_path = reports_dir / f"{args.name}_COMPLIANCE_REPORT.md"

        validator.generate_report(report_path)
        print(f"\n📄 Detailed report saved to: {report_path.absolute()}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
