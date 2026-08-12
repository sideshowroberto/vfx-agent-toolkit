#!/usr/bin/env python3
"""
Purpose: Integration tests for agent-creation-update skill
Tests: All 4 scripts working together in realistic workflows
Coverage: Complete agent lifecycle, version management, validation, archiving

Test Scenarios:
1. Complete agent lifecycle (create -> validate -> update -> archive -> delete)
2. Create from all templates (tool-specialist, cross-tool, general-helper)
3. Version increments (major, minor, patch)
4. Validation prevents invalid agents
5. Archive restoration workflow
6. Force overwrite workflow

Requirements:
- Temporary directories for isolation
- Cleanup after tests
- All scripts in scripts/ directory
- Template files in reference/
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List


# ============================================================================
# Test Infrastructure
# ============================================================================

class IntegrationTestSuite:
    """Test harness for integration testing."""

    def __init__(self):
        """Initialize test suite."""
        self.temp_dir: str = ""
        self.agents_dir: Path = Path()
        self.archive_dir: Path = Path()
        self.scripts_dir: Path = Path(__file__).parent.parent / 'scripts'
        self.reference_dir: Path = Path(__file__).parent.parent / 'reference'
        self.results: List[Dict[str, Any]] = []

    def setup(self) -> None:
        """Create temporary test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix='agent_test_')
        self.agents_dir = Path(self.temp_dir) / 'agents'
        self.archive_dir = self.agents_dir / 'archive'

        # Create directories
        self.agents_dir.mkdir(parents=True)
        self.archive_dir.mkdir(parents=True)

    def teardown(self) -> None:
        """Clean up temporary environment."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def run_script(self, script_name: str, args: List[str]) -> subprocess.CompletedProcess:
        """
        Run a script and return result.

        Args:
            script_name: Script filename (e.g., 'create_agent.py')
            args: Command line arguments

        Returns:
            CompletedProcess with returncode, stdout, stderr
        """
        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        cmd = [sys.executable, str(script_path)] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def verify_file_exists(self, file_path: Path) -> bool:
        """Check if file exists."""
        return file_path.exists()

    def verify_file_content(self, file_path: Path, expected_content: str) -> bool:
        """Check if file contains expected content."""
        if not file_path.exists():
            return False
        try:
            content = file_path.read_text(encoding='utf-8')
            return expected_content in content
        except Exception:
            return False

    def verify_version_in_file(self, file_path: Path, expected_version: str) -> bool:
        """Check if file contains expected version."""
        return self.verify_file_content(file_path, f"version: {expected_version}")

    def add_result(self, test_name: str, checks: List[tuple]) -> bool:
        """
        Add test result.

        Args:
            test_name: Name of test
            checks: List of (description, passed) tuples

        Returns:
            True if all checks passed, False otherwise
        """
        all_passed = all(passed for _, passed in checks)
        self.results.append({
            "name": test_name,
            "passed": all_passed,
            "checks": checks
        })
        return all_passed


# ============================================================================
# Test 1: Complete Agent Lifecycle
# ============================================================================

def test_complete_agent_lifecycle(suite: IntegrationTestSuite) -> bool:
    """
    Test complete agent lifecycle:
    - Create new agent
    - Validate agent (should PASS)
    - Update agent (minor version)
    - Validate updated agent (should PASS)
    - Archive agent
    - Verify archive exists
    - Delete agent
    - Verify cleanup
    """
    print("\nTest 1: Complete Agent Lifecycle")

    agent_name = "test-lifecycle-agent"
    agent_file = suite.agents_dir / f"{agent_name}.md"
    archive_file = suite.archive_dir / f"{agent_name}-v1.0.0.md"

    checks = []

    # Step 1: Create agent
    result = suite.run_script('create_agent.py', [
        agent_name,
        '--description', 'Test lifecycle agent for integration testing',
        '--tools', 'Read,Write,Edit',
        '--type', 'general-helper',
        '--agents-dir', str(suite.agents_dir)
    ])

    create_success = result.returncode == 0 and suite.verify_file_exists(agent_file)
    checks.append(("Create agent (v1.0.0)", create_success))

    if not create_success:
        print(f"  [FAIL] Create failed: {result.stderr}")
        return suite.add_result("Complete Agent Lifecycle", checks)

    # Step 2: Validate agent
    result = suite.run_script('validate_agent.py', [
        agent_name,
        '--agents-dir', str(suite.agents_dir)
    ])

    validate_success = result.returncode == 0
    checks.append(("Validate agent (PASS)", validate_success))

    # Step 3: Update agent to v1.1.0
    result = suite.run_script('update_agent.py', [
        agent_name,
        'minor',
        '--changelog', 'Added new feature for testing',
        '--agents-dir', str(suite.agents_dir)
    ])

    update_success = (result.returncode == 0 and
                     suite.verify_version_in_file(agent_file, "1.1.0"))
    checks.append(("Update agent to v1.1.0", update_success))

    # Step 4: Validate updated agent
    result = suite.run_script('validate_agent.py', [
        agent_name,
        '--agents-dir', str(suite.agents_dir)
    ])

    validate_updated_success = result.returncode == 0
    checks.append(("Validate updated agent (PASS)", validate_updated_success))

    # Step 5: Archive created during update
    archive_created = suite.verify_file_exists(archive_file)
    checks.append(("Archive created (v1.0.0)", archive_created))

    # Step 6: Delete agent file
    if agent_file.exists():
        agent_file.unlink()

    cleanup_success = not suite.verify_file_exists(agent_file)
    checks.append(("Cleanup successful", cleanup_success))

    return suite.add_result("Complete Agent Lifecycle", checks)


# ============================================================================
# Test 2: Create From All Templates
# ============================================================================

def test_create_from_all_templates(suite: IntegrationTestSuite) -> bool:
    """
    Test creating agents from all template types:
    - tool-specialist
    - cross-tool
    - general-helper
    - Validate all 3 agents (should PASS)
    - Verify all have correct structure
    """
    print("\nTest 2: Create From All Templates")

    templates = [
        ('tool-specialist', 'test-tool-specialist'),
        ('cross-tool', 'test-cross-tool'),
        ('general-helper', 'test-general-helper')
    ]

    checks = []

    for template_type, agent_name in templates:
        # Create agent
        result = suite.run_script('create_agent.py', [
            agent_name,
            '--description', f'Test {template_type} agent for integration testing',
            '--tools', 'Read,Write,Edit',
            '--type', template_type,
            '--agents-dir', str(suite.agents_dir)
        ])

        agent_file = suite.agents_dir / f"{agent_name}.md"
        create_success = result.returncode == 0 and suite.verify_file_exists(agent_file)
        checks.append((f"{template_type} created", create_success))

        # Validate agent
        if create_success:
            result = suite.run_script('validate_agent.py', [
                agent_name,
                '--agents-dir', str(suite.agents_dir)
            ])

            validate_success = result.returncode == 0
            checks.append((f"{template_type} validated (PASS)", validate_success))

    return suite.add_result("Create From All Templates", checks)


# ============================================================================
# Test 3: Version Increments
# ============================================================================

def test_version_increments(suite: IntegrationTestSuite) -> bool:
    """
    Test version increment logic:
    - Create agent (v1.0.0)
    - Update major (v1.0.0 -> v2.0.0)
    - Update minor (v2.0.0 -> v2.1.0)
    - Update patch (v2.1.0 -> v2.1.1)
    - Verify 3 archives created (v1.0.0, v2.0.0, v2.1.0)
    - Validate final agent (should PASS)
    """
    print("\nTest 3: Version Increments")

    agent_name = "test-version-agent"
    agent_file = suite.agents_dir / f"{agent_name}.md"

    checks = []

    # Create agent (v1.0.0)
    result = suite.run_script('create_agent.py', [
        agent_name,
        '--description', 'Test version increment agent for integration testing',
        '--tools', 'Read,Write,Edit',
        '--type', 'general-helper',
        '--agents-dir', str(suite.agents_dir)
    ])

    create_success = result.returncode == 0 and suite.verify_version_in_file(agent_file, "1.0.0")
    checks.append(("Create agent (v1.0.0)", create_success))

    if not create_success:
        return suite.add_result("Version Increments", checks)

    # Major increment (1.0.0 -> 2.0.0)
    result = suite.run_script('update_agent.py', [
        agent_name,
        'major',
        '--changelog', 'Breaking change: major refactor',
        '--agents-dir', str(suite.agents_dir)
    ])

    major_success = (result.returncode == 0 and
                    suite.verify_version_in_file(agent_file, "2.0.0") and
                    suite.verify_file_exists(suite.archive_dir / f"{agent_name}-v1.0.0.md"))
    checks.append(("Major increment (1.0.0 -> 2.0.0)", major_success))

    # Minor increment (2.0.0 -> 2.1.0)
    result = suite.run_script('update_agent.py', [
        agent_name,
        'minor',
        '--changelog', 'New feature: added capability',
        '--agents-dir', str(suite.agents_dir)
    ])

    minor_success = (result.returncode == 0 and
                    suite.verify_version_in_file(agent_file, "2.1.0") and
                    suite.verify_file_exists(suite.archive_dir / f"{agent_name}-v2.0.0.md"))
    checks.append(("Minor increment (2.0.0 -> 2.1.0)", minor_success))

    # Patch increment (2.1.0 -> 2.1.1)
    result = suite.run_script('update_agent.py', [
        agent_name,
        'patch',
        '--changelog', 'Bug fix: corrected validation logic',
        '--agents-dir', str(suite.agents_dir)
    ])

    patch_success = (result.returncode == 0 and
                    suite.verify_version_in_file(agent_file, "2.1.1") and
                    suite.verify_file_exists(suite.archive_dir / f"{agent_name}-v2.1.0.md"))
    checks.append(("Patch increment (2.1.0 -> 2.1.1)", patch_success))

    # Verify all 3 archives created
    archives_exist = (
        suite.verify_file_exists(suite.archive_dir / f"{agent_name}-v1.0.0.md") and
        suite.verify_file_exists(suite.archive_dir / f"{agent_name}-v2.0.0.md") and
        suite.verify_file_exists(suite.archive_dir / f"{agent_name}-v2.1.0.md")
    )
    checks.append(("All archives created", archives_exist))

    # Validate final agent
    result = suite.run_script('validate_agent.py', [
        agent_name,
        '--agents-dir', str(suite.agents_dir)
    ])

    validate_success = result.returncode == 0
    checks.append(("Validate final agent (PASS)", validate_success))

    return suite.add_result("Version Increments", checks)


# ============================================================================
# Test 4: Validation Prevents Invalid Agents
# ============================================================================

def test_validation_prevents_invalid_agents(suite: IntegrationTestSuite) -> bool:
    """
    Test that validation prevents invalid agents:
    - Create agent with invalid name (version suffix) - should fail before file creation
    - Manually create invalid agent file
    - Validation should FAIL
    - Update should refuse to proceed on invalid agent
    """
    print("\nTest 4: Validation Prevents Invalid Agents")

    checks = []

    # Test 1: Try to create agent with version suffix in name
    invalid_name = "test-agent-v2"
    result = suite.run_script('create_agent.py', [
        invalid_name,
        '--description', 'This should fail due to invalid name',
        '--tools', 'Read,Write,Edit',
        '--type', 'general-helper',
        '--agents-dir', str(suite.agents_dir)
    ])

    # Should fail and not create file
    invalid_name_rejected = (result.returncode != 0 and
                            not suite.verify_file_exists(suite.agents_dir / f"{invalid_name}.md"))
    checks.append(("Invalid name rejected", invalid_name_rejected))

    # Test 2: Manually create invalid agent file (missing required metadata)
    invalid_agent_name = "test-invalid-agent"
    invalid_agent_file = suite.agents_dir / f"{invalid_agent_name}.md"

    # Create file with invalid content (no YAML frontmatter)
    invalid_agent_file.write_text("# Invalid Agent\n\nThis agent has no metadata.", encoding='utf-8')

    # Validation should fail
    result = suite.run_script('validate_agent.py', [
        invalid_agent_name,
        '--agents-dir', str(suite.agents_dir)
    ])

    validation_fails = result.returncode != 0
    checks.append(("Invalid agent validation fails", validation_fails))

    # Test 3: Update should refuse to proceed on invalid agent
    result = suite.run_script('update_agent.py', [
        invalid_agent_name,
        'minor',
        '--changelog', 'This should fail',
        '--agents-dir', str(suite.agents_dir)
    ])

    update_blocked = result.returncode != 0
    checks.append(("Update blocked on invalid agent", update_blocked))

    return suite.add_result("Validation Prevents Invalid Agents", checks)


# ============================================================================
# Test 5: Archive Restoration Workflow
# ============================================================================

def test_archive_restoration_workflow(suite: IntegrationTestSuite) -> bool:
    """
    Test archive restoration workflow:
    - Create agent (v1.0.0)
    - Update to v2.0.0
    - Archive v1.0.0 created
    - Delete v2.0.0 (rollback scenario)
    - Copy archive back to active location
    - Validate restored v1.0.0 (should PASS)
    """
    print("\nTest 5: Archive Restoration Workflow")

    agent_name = "test-restore-agent"
    agent_file = suite.agents_dir / f"{agent_name}.md"
    archive_file = suite.archive_dir / f"{agent_name}-v1.0.0.md"

    checks = []

    # Create agent (v1.0.0)
    result = suite.run_script('create_agent.py', [
        agent_name,
        '--description', 'Test restore agent for integration testing',
        '--tools', 'Read,Write,Edit',
        '--type', 'general-helper',
        '--agents-dir', str(suite.agents_dir)
    ])

    create_success = result.returncode == 0
    checks.append(("Original created (v1.0.0)", create_success))

    if not create_success:
        return suite.add_result("Archive Restoration Workflow", checks)

    # Update to v2.0.0
    result = suite.run_script('update_agent.py', [
        agent_name,
        'major',
        '--changelog', 'Major update to v2.0.0',
        '--agents-dir', str(suite.agents_dir)
    ])

    update_success = result.returncode == 0 and suite.verify_version_in_file(agent_file, "2.0.0")
    checks.append(("Updated to v2.0.0", update_success))

    # Archive v1.0.0 exists
    archive_exists = suite.verify_file_exists(archive_file)
    checks.append(("Archive v1.0.0 exists", archive_exists))

    if not archive_exists:
        return suite.add_result("Archive Restoration Workflow", checks)

    # Delete v2.0.0 (rollback scenario)
    if agent_file.exists():
        agent_file.unlink()

    deleted = not suite.verify_file_exists(agent_file)
    checks.append(("Deleted v2.0.0", deleted))

    # Copy archive back to active location
    shutil.copy2(archive_file, agent_file)

    restored = suite.verify_file_exists(agent_file)
    checks.append(("Restoration successful", restored))

    # Validate restored v1.0.0
    result = suite.run_script('validate_agent.py', [
        agent_name,
        '--agents-dir', str(suite.agents_dir)
    ])

    validate_success = result.returncode == 0 and suite.verify_version_in_file(agent_file, "1.0.0")
    checks.append(("Restored agent validates", validate_success))

    return suite.add_result("Archive Restoration Workflow", checks)


# ============================================================================
# Test 6: Force Overwrite Workflow
# ============================================================================

def test_force_overwrite_workflow(suite: IntegrationTestSuite) -> bool:
    """
    Test force overwrite workflow:
    - Create agent (v1.0.0)
    - Create same agent without --force (should fail)
    - Create same agent with --force (should succeed)
    - Update agent (v2.0.0)
    - Archive already exists for v1.0.0
    - Archive with --force (should overwrite)
    """
    print("\nTest 6: Force Overwrite Workflow")

    agent_name = "test-force-agent"
    agent_file = suite.agents_dir / f"{agent_name}.md"
    archive_file = suite.archive_dir / f"{agent_name}-v1.0.0.md"

    checks = []

    # Create agent (v1.0.0)
    result = suite.run_script('create_agent.py', [
        agent_name,
        '--description', 'Test force overwrite agent for integration testing',
        '--tools', 'Read,Write,Edit',
        '--type', 'general-helper',
        '--agents-dir', str(suite.agents_dir)
    ])

    create_success = result.returncode == 0
    checks.append(("Created agent (v1.0.0)", create_success))

    if not create_success:
        return suite.add_result("Force Overwrite Workflow", checks)

    # Try to create same agent without --force (should fail)
    result = suite.run_script('create_agent.py', [
        agent_name,
        '--description', 'This should fail',
        '--tools', 'Read,Write',
        '--type', 'general-helper',
        '--agents-dir', str(suite.agents_dir)
    ])

    duplicate_blocked = result.returncode != 0
    checks.append(("Duplicate creation blocked", duplicate_blocked))

    # Create same agent with --force (should succeed)
    result = suite.run_script('create_agent.py', [
        agent_name,
        '--description', 'Force overwrite test agent',
        '--tools', 'Read,Write,Edit,Grep',
        '--type', 'general-helper',
        '--force',
        '--agents-dir', str(suite.agents_dir)
    ])

    force_success = result.returncode == 0
    checks.append(("Force overwrite succeeds", force_success))

    # Update to create archive
    result = suite.run_script('update_agent.py', [
        agent_name,
        'major',
        '--changelog', 'Major update',
        '--agents-dir', str(suite.agents_dir)
    ])

    update_success = result.returncode == 0
    checks.append(("Update creates archive", update_success))

    # Archive v1.0.0 now exists
    archive_exists = suite.verify_file_exists(archive_file)
    checks.append(("Archive exists", archive_exists))

    if not archive_exists:
        return suite.add_result("Force Overwrite Workflow", checks)

    # Try to archive again with same version (using archive script directly)
    # First, rollback agent to v1.0.0 for re-archiving
    if archive_file.exists():
        shutil.copy2(archive_file, agent_file)

    # Try archive without --force (should fail)
    result = suite.run_script('archive_agent.py', [
        agent_name,
        '--agents-dir', str(suite.agents_dir)
    ])

    archive_duplicate_blocked = result.returncode != 0
    checks.append(("Archive duplicate blocked", archive_duplicate_blocked))

    # Archive with --force (should overwrite)
    result = suite.run_script('archive_agent.py', [
        agent_name,
        '--force',
        '--agents-dir', str(suite.agents_dir)
    ])

    archive_force_success = result.returncode == 0
    checks.append(("Archive force overwrite succeeds", archive_force_success))

    return suite.add_result("Force Overwrite Workflow", checks)


# ============================================================================
# Test Runner
# ============================================================================

def print_test_header():
    """Print test suite header."""
    print("=" * 70)
    print("AGENT-CREATION-UPDATE INTEGRATION TEST SUITE")
    print("=" * 70)


def print_test_results(suite: IntegrationTestSuite):
    """Print detailed test results."""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    total_tests = len(suite.results)
    passed_tests = sum(1 for r in suite.results if r['passed'])

    for i, result in enumerate(suite.results, 1):
        status = "[OK] PASS" if result['passed'] else "[FAIL] FAIL"
        print(f"\nTest {i}: {result['name']} - {status}")

        for check_desc, check_passed in result['checks']:
            symbol = "  [OK]" if check_passed else "  [FAIL]"
            print(f"{symbol} {check_desc}")

    print("\n" + "=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")

    if passed_tests == total_tests:
        print("\nAll integration tests passed!")
    else:
        print(f"\n[WARN] {total_tests - passed_tests} test(s) failed")

    print("=" * 70)


def run_all_tests() -> int:
    """
    Run all integration tests.

    Returns:
        Exit code (0 if all pass, 1 if any fail)
    """
    suite = IntegrationTestSuite()

    try:
        # Setup
        suite.setup()

        # Print header
        print_test_header()

        # Run all tests
        test_complete_agent_lifecycle(suite)
        test_create_from_all_templates(suite)
        test_version_increments(suite)
        test_validation_prevents_invalid_agents(suite)
        test_archive_restoration_workflow(suite)
        test_force_overwrite_workflow(suite)

        # Print results
        print_test_results(suite)

        # Determine exit code
        all_passed = all(r['passed'] for r in suite.results)
        return 0 if all_passed else 1

    finally:
        # Always cleanup
        suite.teardown()


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
