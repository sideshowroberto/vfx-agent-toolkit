#!/usr/bin/env python3
"""
Test VFX Agent Skill scripts with multiple targets for Article I validation.

Purpose: Validate general-purpose script compliance (Article I)
Tests: Execute skill scripts with 3+ different targets
Output: Test report with pass/fail per target

Usage:
    python test_skill.py SKILL_NAME --targets target1,target2,target3

    --targets: Comma-separated list of test targets (min 3)
    --script: Specific script to test (default: auto-detect)
    --timeout: Timeout per test in seconds (default: 30)

Author: VFX Skill System
Version: 1.0.0
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class TestResult:
    """Result of a single test execution."""
    target: str
    command: str
    status: str  # "PASS", "FAIL"
    duration_ms: int
    exit_code: int
    stdout: str
    stderr: str
    error: Optional[str] = None


class SkillTester:
    """Tests VFX Agent Skill scripts with multiple targets."""

    def __init__(self, skill_name: str, skill_path: Optional[Path] = None):
        """
        Initialize tester.

        Args:
            skill_name: Name of skill to test
            skill_path: Path to .claude/skills/ (auto-detect if None)
        """
        self.skill_name = skill_name

        if skill_path is None:
            # Auto-detect from script location
            script_dir = Path(__file__).parent.absolute()
            skill_path = script_dir.parent.parent

        self.skill_dir = skill_path / skill_name
        self.scripts_dir = self.skill_dir / "scripts"
        self.results: list[TestResult] = []

    def find_main_script(self) -> Optional[Path]:
        """
        Find main executable script in scripts/ directory.

        Priority:
        1. main.py
        2. {skill_name}.py
        3. First .py file with __main__ block

        Returns:
            Path to main script, or None if not found
        """
        if not self.scripts_dir.exists():
            return None

        # Priority 1: main.py
        main_py = self.scripts_dir / "main.py"
        if main_py.exists():
            return main_py

        # Priority 2: {skill_name}.py
        skill_py = self.scripts_dir / f"{self.skill_name}.py"
        if skill_py.exists():
            return skill_py

        # Priority 3: First script with __main__
        for script in self.scripts_dir.glob("*.py"):
            if script.name.startswith("test_") or script.name.startswith("_"):
                continue  # Skip test and private files

            with open(script, 'r', encoding='utf-8') as f:
                if 'if __name__ == "__main__"' in f.read():
                    return script

        return None

    def run_test(
        self,
        script: Path,
        target: str,
        timeout: int = 30
    ) -> TestResult:
        """
        Run script with single target and capture results.

        Args:
            script: Path to script to execute
            target: Target parameter to pass to script
            timeout: Timeout in seconds

        Returns:
            TestResult with execution details
        """
        command = [sys.executable, str(script), target]
        command_str = " ".join(command)

        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=script.parent
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Determine pass/fail
            if result.returncode == 0:
                status = "PASS"
                error = None
            else:
                status = "FAIL"
                error = f"Non-zero exit code: {result.returncode}"

            return TestResult(
                target=target,
                command=command_str,
                status=status,
                duration_ms=duration_ms,
                exit_code=result.returncode,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                error=error
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestResult(
                target=target,
                command=command_str,
                status="FAIL",
                duration_ms=duration_ms,
                exit_code=-1,
                stdout="",
                stderr="",
                error=f"Timeout after {timeout}s"
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return TestResult(
                target=target,
                command=command_str,
                status="FAIL",
                duration_ms=duration_ms,
                exit_code=-1,
                stdout="",
                stderr="",
                error=f"Exception: {str(e)}"
            )

    def test_all_targets(
        self,
        targets: list[str],
        script: Optional[Path] = None,
        timeout: int = 30
    ) -> bool:
        """
        Test script with all targets.

        Args:
            targets: List of targets to test
            script: Script to test (auto-detect if None)
            timeout: Timeout per test in seconds

        Returns:
            True if all tests pass, False otherwise
        """
        # Find script
        if script is None:
            script = self.find_main_script()
            if script is None:
                print(f"❌ No executable script found in {self.scripts_dir}")
                print("\nGuidance:")
                print("  - Documentation-only skills: Skip test_skill.py (not applicable)")
                print("  - MCP-based skills: Create test wrapper script")
                print("  - Add if __name__ == '__main__' block to make script executable")
                return False

        print(f"🧪 Testing {self.skill_name} with {len(targets)} targets\n")
        print(f"Script: {script.name}\n")

        # Run tests
        for i, target in enumerate(targets, 1):
            print(f"Test {i}/{len(targets)}: {target}")
            result = self.run_test(script, target, timeout)
            self.results.append(result)

            status_icon = "✅" if result.status == "PASS" else "❌"
            print(f"  Command: {result.command}")
            print(f"  Status: {status_icon} {result.status}")
            print(f"  Duration: {result.duration_ms}ms")

            if result.stdout:
                # Parse JSON output if present
                try:
                    output_data = json.loads(result.stdout)
                    print(f"  Output: {json.dumps(output_data, indent=2)}")
                except json.JSONDecodeError:
                    # Not JSON, show first line
                    first_line = result.stdout.split('\n')[0]
                    if len(first_line) > 80:
                        first_line = first_line[:77] + "..."
                    print(f"  Output: {first_line}")

            if result.error:
                print(f"  Error: {result.error}")

            if result.stderr:
                stderr_preview = result.stderr.split('\n')[0][:80]
                print(f"  Stderr: {stderr_preview}")

            print()

        # Summary
        passed = [r for r in self.results if r.status == "PASS"]
        failed = [r for r in self.results if r.status == "FAIL"]

        print(f"Summary: {len(passed)}/{len(targets)} targets passed", end=" ")
        if len(failed) == 0:
            print("✅")
        else:
            print("❌")

        # Article I validation
        if len(targets) >= 3 and len(failed) == 0:
            print(f"Article I compliance: ✅ VALIDATED (script is general-purpose)")
        elif len(targets) < 3:
            print(f"Article I compliance: ⚠️  INSUFFICIENT (need 3+ targets, got {len(targets)})")
        else:
            print(f"Article I compliance: ❌ FAILED ({len(failed)} target(s) failed)")

        return len(failed) == 0

    def generate_report(self) -> str:
        """
        Generate test report in markdown format.

        Returns:
            Report content as string
        """
        report = []
        report.append(f"# Test Report: {self.skill_name}\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Skill Path:** {self.skill_dir.absolute()}\n")
        report.append("\n---\n\n")

        # Summary
        passed = [r for r in self.results if r.status == "PASS"]
        failed = [r for r in self.results if r.status == "FAIL"]
        avg_duration = sum(r.duration_ms for r in self.results) / len(self.results) if self.results else 0

        report.append("## Summary\n\n")
        report.append(f"- **Total Tests:** {len(self.results)}\n")
        report.append(f"- **Passed:** {len(passed)}\n")
        report.append(f"- **Failed:** {len(failed)}\n")
        report.append(f"- **Average Duration:** {avg_duration:.0f}ms\n")
        report.append(f"\n**Overall Status:** {'✅ PASS' if len(failed) == 0 else '❌ FAIL'}\n\n")

        # Article I validation
        if len(self.results) >= 3:
            article_i = "✅ VALIDATED" if len(failed) == 0 else "❌ FAILED"
            report.append(f"**Article I Compliance:** {article_i} (script tested with {len(self.results)} targets)\n\n")
        else:
            report.append(f"**Article I Compliance:** ⚠️ INSUFFICIENT (need 3+ targets, got {len(self.results)})\n\n")

        report.append("---\n\n")

        # Detailed results
        report.append("## Test Results\n\n")
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result.status == "PASS" else "❌"
            report.append(f"### Test {i}: {result.target} {status_icon}\n\n")
            report.append(f"**Command:** `{result.command}`\n\n")
            report.append(f"**Status:** {result.status}\n\n")
            report.append(f"**Duration:** {result.duration_ms}ms\n\n")
            report.append(f"**Exit Code:** {result.exit_code}\n\n")

            if result.stdout:
                report.append("**Output:**\n")
                report.append("```\n")
                report.append(result.stdout)
                report.append("\n```\n\n")

            if result.stderr:
                report.append("**Stderr:**\n")
                report.append("```\n")
                report.append(result.stderr)
                report.append("\n```\n\n")

            if result.error:
                report.append(f"**Error:** {result.error}\n\n")

            report.append("---\n\n")

        return "".join(report)

    def save_report(self) -> Path:
        """
        Save test report to skill directory.

        Returns:
            Path to saved report
        """
        report_path = self.skill_dir / "test_report.md"
        report_content = self.generate_report()

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_path


def main() -> int:
    """
    Main entry point for skill testing.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    parser = argparse.ArgumentParser(
        description="Test VFX Agent Skill with multiple targets (Article I validation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Test with 3 different shots
    python test_skill.py unreal-vfx-automation \\
        --targets Shot001,Shot002,Shot003

    # Test with custom script and timeout
    python test_skill.py houdini-hda-export \\
        --targets CharacterRig,EnvironmentProp,Vehicle \\
        --script export_hda.py \\
        --timeout 60

    # Test Blender workflow with different assets
    python test_skill.py blender-fbx-workflow \\
        --targets Character,Prop,Environment
        """
    )

    parser.add_argument("name", help="Skill name to test")
    parser.add_argument("--targets", required=True,
                        help="Comma-separated list of test targets (min 3 for Article I)")
    parser.add_argument("--script",
                        help="Specific script to test (auto-detect if not provided)")
    parser.add_argument("--timeout", type=int, default=30,
                        help="Timeout per test in seconds (default: 30)")
    parser.add_argument("--skills-path", type=Path,
                        help="Path to .claude/skills directory (auto-detect if not provided)")

    args = parser.parse_args()

    # Parse targets
    targets = [t.strip() for t in args.targets.split(',') if t.strip()]
    if len(targets) < 1:
        print("❌ At least 1 target required")
        return 1

    if len(targets) < 3:
        print(f"⚠️  Warning: {len(targets)} target(s) provided")
        print("   Article I requires 3+ targets for validation")
        print("   Continuing with limited testing...\n")

    # Create tester
    tester = SkillTester(args.name, args.skills_path)

    # Verify skill exists
    if not tester.skill_dir.exists():
        print(f"❌ Skill not found: {args.name}")
        print(f"   Expected path: {tester.skill_dir}")
        return 1

    # Find script
    script = None
    if args.script:
        script = tester.scripts_dir / args.script
        if not script.exists():
            print(f"❌ Script not found: {args.script}")
            print(f"   Expected path: {script}")
            return 1

    # Run tests
    success = tester.test_all_targets(targets, script, args.timeout)

    # Save report
    report_path = tester.save_report()
    print(f"\n📄 Report saved to: {report_path.absolute()}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
