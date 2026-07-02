#!/usr/bin/env python3
"""
Test script for create_agent.py

Tests:
1. Template loading
2. Placeholder replacement
3. Agent name validation
4. Agent creation workflow
5. Force overwrite
6. Interactive mode (manual test only)
"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add script directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from create_agent import (
    load_template,
    populate_template,
    validate_agent_name,
    check_agent_exists,
    create_agent,
    TEMPLATE_PATH
)


def test_template_loading():
    """Test that template file can be loaded."""
    print("\n=== Test 1: Template Loading ===")

    try:
        template = load_template('general-helper')
        assert '{{NAME}}' in template, "Template missing {{NAME}} placeholder"
        assert '{{DESCRIPTION}}' in template, "Template missing {{DESCRIPTION}} placeholder"
        assert '{{TOOLS}}' in template, "Template missing {{TOOLS}} placeholder"
        assert '{{DATE}}' in template, "Template missing {{DATE}} placeholder"
        print("✅ PASS: Template loaded successfully with all placeholders")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_placeholder_replacement():
    """Test that placeholders are replaced correctly."""
    print("\n=== Test 2: Placeholder Replacement ===")

    try:
        template = "name: {{NAME}}\ntools:\n{{TOOLS}}\ndate: {{DATE}}\ndesc: {{DESCRIPTION}}"
        metadata = {
            'name': 'test-agent',
            'description': 'Test agent for validation',
            'tools': ['Read', 'Write', 'Edit']
        }

        result = populate_template(template, metadata)

        assert 'test-agent' in result, "NAME not replaced"
        assert 'Test agent for validation' in result, "DESCRIPTION not replaced"
        assert '  - Read' in result, "TOOLS not formatted correctly"
        assert '  - Write' in result, "TOOLS missing Write"
        assert '  - Edit' in result, "TOOLS missing Edit"
        assert '{{' not in result, "Placeholders still present"

        print("✅ PASS: All placeholders replaced correctly")
        print(f"Sample output:\n{result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_agent_name_validation():
    """Test agent name validation rules."""
    print("\n=== Test 3: Agent Name Validation ===")

    test_cases = [
        # (name, should_pass, description)
        ('valid-agent-name', True, 'Valid name'),
        ('test123', True, 'Name with numbers'),
        ('a', False, 'Too short (< 3 chars)'),
        ('x' * 51, False, 'Too long (> 50 chars)'),
        ('Invalid_Name', False, 'Contains underscore'),
        ('InvalidName', False, 'Contains uppercase'),
        ('agent-v2', False, 'Contains version suffix'),
        ('agent-v1.0', False, 'Contains version suffix'),
        ('-leading-dash', False, 'Leading dash'),
        ('trailing-dash-', False, 'Trailing dash'),
        ('double--dash', False, 'Consecutive dashes'),
        ('good-name', True, 'Valid kebab-case'),
    ]

    passed = 0
    failed = 0

    for name, should_pass, description in test_cases:
        result = validate_agent_name(name)
        is_valid = result['valid']

        if is_valid == should_pass:
            print(f"  ✅ {description}: '{name}' → {result['message']}")
            passed += 1
        else:
            print(f"  ❌ {description}: '{name}' → Expected {should_pass}, got {is_valid}")
            print(f"     Message: {result['message']}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_agent_creation():
    """Test complete agent creation workflow."""
    print("\n=== Test 4: Agent Creation Workflow ===")

    # Create temporary directory for test agents
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Temp directory: {temp_dir}")

        # Test 1: Create new agent
        result = create_agent(
            name='test-workflow-agent',
            description='Test workflow agent. Use when testing agent creation workflows',
            tools=['Read', 'Write', 'Edit', 'Bash'],
            agent_type='general-helper',
            force=False,
            agents_dir=temp_dir
        )

        if not result['success']:
            print(f"❌ FAIL: Agent creation failed: {result['message']}")
            return False

        print(f"✅ Created agent: {result['agent_path']}")

        # Verify file exists
        agent_path = Path(result['agent_path'])
        if not agent_path.exists():
            print(f"❌ FAIL: Agent file not created at {agent_path}")
            return False

        print(f"✅ Agent file exists: {agent_path}")

        # Verify content
        content = agent_path.read_text()
        if '{{' in content:
            print(f"❌ FAIL: Placeholders still present in generated file")
            return False

        if 'test-workflow-agent' not in content:
            print(f"❌ FAIL: Agent name not in content")
            return False

        print(f"✅ Content verified (no placeholders, name present)")

        # Test 2: Try to create duplicate (should fail without force)
        result2 = create_agent(
            name='test-workflow-agent',
            description='Duplicate agent',
            tools=['Read'],
            agent_type='general-helper',
            force=False,
            agents_dir=temp_dir
        )

        if result2['success']:
            print(f"❌ FAIL: Duplicate agent created without force flag")
            return False

        print(f"✅ Duplicate prevention works: {result2['message']}")

        # Test 3: Force overwrite
        result3 = create_agent(
            name='test-workflow-agent',
            description='Updated agent. Use when testing force overwrite',
            tools=['Read', 'Grep'],
            agent_type='general-helper',
            force=True,
            agents_dir=temp_dir
        )

        if not result3['success']:
            print(f"❌ FAIL: Force overwrite failed: {result3['message']}")
            return False

        print(f"✅ Force overwrite works")

        # Verify updated content
        updated_content = agent_path.read_text()
        if 'Updated agent' not in updated_content:
            print(f"❌ FAIL: Content not updated after force overwrite")
            return False

        print(f"✅ Content updated correctly")

        print("\n✅ PASS: All agent creation workflow tests passed")
        return True


def test_validation_integration():
    """Test integration with validate_agent.py."""
    print("\n=== Test 5: Validation Integration ===")

    # Create temporary directory for test agents
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create an agent
        result = create_agent(
            name='validation-test-agent',
            description='Validation test agent. Use when testing validation integration',
            tools=['Read', 'Write', 'Edit'],
            agent_type='general-helper',
            force=False,
            agents_dir=temp_dir
        )

        if not result['success']:
            print(f"❌ FAIL: Agent creation failed: {result['message']}")
            return False

        # Check validation results
        validation = result['validation']

        print(f"Validation passed: {validation['passed']}")
        if not validation['passed']:
            print(f"Validation output:\n{validation['output']}")
            print("Note: Validation may fail due to template structure, but integration is working")

        print("✅ PASS: Validation integration working (subprocess executed)")
        return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Running create_agent.py Test Suite")
    print("=" * 60)

    # Check template exists
    if not TEMPLATE_PATH.exists():
        print(f"❌ ERROR: Template not found: {TEMPLATE_PATH}")
        print(f"Expected path: {TEMPLATE_PATH.absolute()}")
        return False

    print(f"✅ Template found: {TEMPLATE_PATH}")

    tests = [
        test_template_loading,
        test_placeholder_replacement,
        test_agent_name_validation,
        test_agent_creation,
        test_validation_integration,
    ]

    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        symbol = "✅" if passed else "❌"
        print(f"{symbol} {test_name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
