#!/usr/bin/env python3
"""
Purpose: Run all tests (unit + integration) for agent-creation-update skill
Usage: python run_all_tests.py [--verbose] [--unit-only] [--integration-only]

Exit Codes:
    0 - All tests passed
    1 - One or more tests failed
    2 - Error running tests

Test Discovery:
    - Unit tests: test_*.py (excluding test_integration.py)
    - Integration tests: test_integration.py

Requirements:
    - pytest for unit tests
    - subprocess for integration tests
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List


# ============================================================================
# Test Runner Configuration
# ============================================================================

TESTS_DIR = Path(__file__).parent
UNIT_TEST_PATTERN = "test_*.py"
INTEGRATION_TEST_FILE = "test_integration.py"


# ============================================================================
# Unit Test Runner (pytest)
# ============================================================================

def run_unit_tests(verbose: bool = False) -> Dict[str, Any]:
    """
    Run unit tests using pytest.

    Args:
        verbose: Enable verbose output

    Returns:
        dict: {
            "success": bool,
            "tests_run": int,
            "failures": int,
            "output": str
        }
    """
    print("\n" + "=" * 70)
    print("RUNNING UNIT TESTS (pytest)")
    print("=" * 70)

    # Find unit test files (exclude test_integration.py)
    unit_test_files = [
        f for f in TESTS_DIR.glob(UNIT_TEST_PATTERN)
        if f.name != INTEGRATION_TEST_FILE
    ]

    if not unit_test_files:
        print("No unit test files found")
        return {
            "success": True,
            "tests_run": 0,
            "failures": 0,
            "output": "No unit tests found"
        }

    print(f"\nFound {len(unit_test_files)} unit test file(s):")
    for test_file in unit_test_files:
        print(f"  - {test_file.name}")

    # Build pytest command
    pytest_args = [
        sys.executable,
        "-m", "pytest",
        str(TESTS_DIR),
        "--ignore", str(TESTS_DIR / INTEGRATION_TEST_FILE),
        "-v" if verbose else "-q"
    ]

    # Run pytest
    try:
        result = subprocess.run(
            pytest_args,
            capture_output=True,
            text=True,
            cwd=str(TESTS_DIR.parent)
        )

        output = result.stdout + result.stderr

        # Print output
        print("\n" + output)

        # Parse pytest output for test counts
        # pytest exit codes: 0 = all passed, 1 = tests failed, 2+ = error
        success = result.returncode == 0

        # Try to extract test counts from output
        tests_run = 0
        failures = 0

        # Look for pytest summary line
        for line in output.split('\n'):
            if 'passed' in line or 'failed' in line:
                # Example: "5 passed in 0.12s" or "3 failed, 2 passed in 0.15s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        try:
                            tests_run += int(parts[i-1])
                        except ValueError:
                            pass
                    if part == 'failed' and i > 0:
                        try:
                            failures += int(parts[i-1])
                            tests_run += failures
                        except ValueError:
                            pass

        return {
            "success": success,
            "tests_run": tests_run,
            "failures": failures,
            "output": output
        }

    except FileNotFoundError:
        error_msg = "pytest not installed. Install with: pip install pytest"
        print(f"\n❌ Error: {error_msg}")
        return {
            "success": False,
            "tests_run": 0,
            "failures": 0,
            "output": error_msg
        }
    except Exception as e:
        error_msg = f"Error running pytest: {e}"
        print(f"\n❌ Error: {error_msg}")
        return {
            "success": False,
            "tests_run": 0,
            "failures": 0,
            "output": error_msg
        }


# ============================================================================
# Integration Test Runner
# ============================================================================

def run_integration_tests(verbose: bool = False) -> Dict[str, Any]:
    """
    Run integration tests.

    Args:
        verbose: Enable verbose output

    Returns:
        dict: {
            "success": bool,
            "tests_run": int,
            "failures": int,
            "output": str
        }
    """
    print("\n" + "=" * 70)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 70)

    integration_test_path = TESTS_DIR / INTEGRATION_TEST_FILE

    if not integration_test_path.exists():
        print(f"Integration test file not found: {integration_test_path}")
        return {
            "success": False,
            "tests_run": 0,
            "failures": 0,
            "output": f"File not found: {integration_test_path}"
        }

    # Run integration tests
    try:
        result = subprocess.run(
            [sys.executable, str(integration_test_path)],
            capture_output=True,
            text=True,
            cwd=str(TESTS_DIR)
        )

        output = result.stdout + result.stderr

        # Print output
        print("\n" + output)

        # Integration tests return 0 if all pass, 1 if any fail
        success = result.returncode == 0

        # Parse output for test counts
        tests_run = 0
        failures = 0

        for line in output.split('\n'):
            if line.startswith("Total Tests:"):
                try:
                    tests_run = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            if line.startswith("Failed:"):
                try:
                    failures = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass

        return {
            "success": success,
            "tests_run": tests_run,
            "failures": failures,
            "output": output
        }

    except Exception as e:
        error_msg = f"Error running integration tests: {e}"
        print(f"\n❌ Error: {error_msg}")
        return {
            "success": False,
            "tests_run": 0,
            "failures": 0,
            "output": error_msg
        }


# ============================================================================
# Combined Test Report
# ============================================================================

def print_combined_report(unit_results: Dict[str, Any], integration_results: Dict[str, Any]):
    """
    Print combined test report.

    Args:
        unit_results: Results from unit tests
        integration_results: Results from integration tests
    """
    print("\n" + "=" * 70)
    print("COMBINED TEST REPORT")
    print("=" * 70)

    # Unit test summary
    print("\nUnit Tests:")
    print(f"  Tests Run: {unit_results['tests_run']}")
    print(f"  Failures: {unit_results['failures']}")
    print(f"  Status: {'✅ PASS' if unit_results['success'] else '❌ FAIL'}")

    # Integration test summary
    print("\nIntegration Tests:")
    print(f"  Tests Run: {integration_results['tests_run']}")
    print(f"  Failures: {integration_results['failures']}")
    print(f"  Status: {'✅ PASS' if integration_results['success'] else '❌ FAIL'}")

    # Overall summary
    total_tests = unit_results['tests_run'] + integration_results['tests_run']
    total_failures = unit_results['failures'] + integration_results['failures']
    all_passed = unit_results['success'] and integration_results['success']

    print("\n" + "-" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Total Failures: {total_failures}")
    print(f"Overall Status: {'✅ PASS' if all_passed else '❌ FAIL'}")

    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_failures} test(s) failed")

    print("=" * 70)


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> int:
    """
    Main entry point for test runner.

    Returns:
        Exit code (0 if all pass, 1 if any fail, 2 if error)
    """
    parser = argparse.ArgumentParser(
        description="Run all tests for agent-creation-update skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_all_tests.py

  # Run with verbose output
  python run_all_tests.py --verbose

  # Run only unit tests
  python run_all_tests.py --unit-only

  # Run only integration tests
  python run_all_tests.py --integration-only

Exit Codes:
  0 - All tests passed
  1 - One or more tests failed
  2 - Error running tests
        """
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="Run only unit tests"
    )

    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Run only integration tests"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.unit_only and args.integration_only:
        print("Error: Cannot specify both --unit-only and --integration-only")
        return 2

    # Run tests based on arguments
    unit_results = {"success": True, "tests_run": 0, "failures": 0, "output": ""}
    integration_results = {"success": True, "tests_run": 0, "failures": 0, "output": ""}

    if not args.integration_only:
        unit_results = run_unit_tests(verbose=args.verbose)

    if not args.unit_only:
        integration_results = run_integration_tests(verbose=args.verbose)

    # Print combined report
    if not args.unit_only and not args.integration_only:
        print_combined_report(unit_results, integration_results)

    # Determine exit code
    all_passed = unit_results['success'] and integration_results['success']
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
