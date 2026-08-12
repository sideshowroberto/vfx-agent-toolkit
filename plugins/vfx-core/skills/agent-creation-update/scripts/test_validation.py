#!/usr/bin/env python3
"""
Test script for validate_agent.py
Verifies all 6 validation checks work correctly
"""

import os
import sys
from validate_agent import (
    check_filename_format,
    check_metadata_present,
    check_name_matches_filename,
    check_version_format,
    check_changelog_exists,
    check_description_quality,
    validate_agent
)


def test_check_filename_format():
    """Test filename format validation."""
    print("Testing check_filename_format()...")

    # PASS cases
    assert check_filename_format("documentation-specialist.md")['passed']
    assert check_filename_format("unreal-mcp-developer.md")['passed']
    assert check_filename_format("test-agent-123.md")['passed']

    # FAIL cases
    assert not check_filename_format("documentation-specialist-v2.md")['passed']
    assert not check_filename_format("agentName.md")['passed']
    assert not check_filename_format("Agent_Name.md")['passed']
    assert not check_filename_format("agent-v1.0.0.md")['passed']

    print("  [OK] All filename format tests passed")


def test_check_version_format():
    """Test version format validation."""
    print("Testing check_version_format()...")

    # PASS cases
    assert check_version_format("1.0.0")['passed']
    assert check_version_format("2.1.3")['passed']
    assert check_version_format("10.20.30")['passed']

    # FAIL cases
    assert not check_version_format("v1.0.0")['passed']
    assert not check_version_format("1.0")['passed']
    assert not check_version_format("1.0.0-beta")['passed']
    assert not check_version_format("1.0.0.0")['passed']

    print("  [OK] All version format tests passed")


def test_check_description_quality():
    """Test description quality validation."""
    print("Testing check_description_quality()...")

    # PASS case
    good_desc = "Index-driven documentation updates for VFX projects. Use when updating documentation or creating session summaries."
    assert check_description_quality(good_desc)['passed']

    # FAIL cases - too short
    assert not check_description_quality("Short")['passed']

    # FAIL cases - vague language
    assert not check_description_quality("This agent helps with documentation tasks")['passed']
    assert not check_description_quality("Does stuff with files and manages things")['passed']

    # FAIL cases - no triggers
    assert not check_description_quality("This is a documentation agent that updates files and creates summaries.")['passed']

    print("  [OK] All description quality tests passed")


def test_check_name_matches_filename():
    """Test name matching validation."""
    print("Testing check_name_matches_filename()...")

    # PASS case
    assert check_name_matches_filename("test-agent.md", "test-agent")['passed']

    # FAIL case
    assert not check_name_matches_filename("test-agent.md", "different-name")['passed']

    print("  [OK] All name matching tests passed")


def test_check_metadata_present():
    """Test metadata parsing."""
    print("Testing check_metadata_present()...")

    # PASS case
    good_content = """---
name: test-agent
description: Test agent for validation
version: 1.0.0
last_updated: 2025-10-25
status: active
---

# Test Agent
"""
    result = check_metadata_present(good_content)
    assert result['passed']
    assert result['metadata']['name'] == 'test-agent'

    # FAIL case - no frontmatter
    bad_content = """# Test Agent
No frontmatter here
"""
    assert not check_metadata_present(bad_content)['passed']

    # FAIL case - missing fields
    incomplete_content = """---
name: test-agent
description: Test
---
"""
    assert not check_metadata_present(incomplete_content)['passed']

    # FAIL case - invalid status
    invalid_status_content = """---
name: test-agent
description: Test agent
version: 1.0.0
last_updated: 2025-10-25
status: invalid-status
---
"""
    assert not check_metadata_present(invalid_status_content)['passed']

    print("  [OK] All metadata tests passed")


def test_check_changelog_exists():
    """Test changelog validation."""
    print("Testing check_changelog_exists()...")

    # PASS case - v1.0.0 doesn't require changelog
    content_v1 = "# Test Agent\nNo changelog needed"
    assert check_changelog_exists(content_v1, "1.0.0")['passed']

    # PASS case - v2.0.0 with proper changelog
    content_v2 = """# Test Agent

## Version History

**v2.0.0** (2025-10-25) - Major Update
- New features

**v1.0.0** (2025-10-24) - Initial Release
- Basic functionality
"""
    assert check_changelog_exists(content_v2, "2.0.0")['passed']

    # FAIL case - v2.0.0 without changelog
    content_no_changelog = "# Test Agent\nNo changelog"
    assert not check_changelog_exists(content_no_changelog, "2.0.0")['passed']

    # FAIL case - only one version documented
    content_one_version = """## Version History
**v2.0.0** - Current
"""
    assert not check_changelog_exists(content_one_version, "2.0.0")['passed']

    print("  [OK] All changelog tests passed")


def test_full_validation():
    """Test full validation workflow."""
    print("\nTesting full validation workflow...")

    agents_dir = "<workspace>\\.claude\\agents"

    # Test valid agent
    valid_path = os.path.join(agents_dir, "test-agent-valid.md")
    if os.path.exists(valid_path):
        result = validate_agent(valid_path)
        if result['passed']:
            print("  [OK] Valid agent test passed")
        else:
            print(f"  [FAIL] Valid agent test failed: {result['violations']}")

    # Test invalid agent with version suffix
    invalid_path = os.path.join(agents_dir, "test-agent-invalid-v2.md")
    if os.path.exists(invalid_path):
        result = validate_agent(invalid_path)
        if not result['passed'] and 'Filename Format' in str(result['violations']):
            print("  [OK] Invalid agent test passed (correctly detected version suffix)")
        else:
            print(f"  [FAIL] Invalid agent test failed")

    # Test non-existent file
    nonexistent_path = os.path.join(agents_dir, "nonexistent-agent.md")
    result = validate_agent(nonexistent_path)
    if not result['passed'] and 'File not found' in str(result['violations']):
        print("  [OK] Non-existent file test passed")
    else:
        print("  [FAIL] Non-existent file test failed")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Testing validate_agent.py Implementation")
    print("="*60 + "\n")

    try:
        test_check_filename_format()
        test_check_version_format()
        test_check_description_quality()
        test_check_name_matches_filename()
        test_check_metadata_present()
        test_check_changelog_exists()
        test_full_validation()

        print("\n" + "="*60)
        print("All tests passed! [OK]")
        print("="*60 + "\n")
        return 0

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
