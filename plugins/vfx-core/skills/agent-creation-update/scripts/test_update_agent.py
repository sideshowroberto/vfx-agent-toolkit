#!/usr/bin/env python3
"""
Purpose: Test suite for update_agent.py
Usage: python test_update_agent.py

Tests:
1. Version increment logic (major, minor, patch)
2. YAML frontmatter parsing and updating
3. Changelog formatting and insertion
4. Full update workflow with validation
5. Error handling (missing files, invalid versions, etc.)
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from update_agent import (
    increment_version,
    parse_frontmatter,
    update_frontmatter,
    parse_changelog_title,
    format_changelog_entry,
    insert_changelog_entry,
    update_agent
)


# ============================================================================
# Test Data
# ============================================================================

SAMPLE_AGENT_V1 = """---
name: test-agent
description: Test agent for update validation. Use when testing agent updates.
version: 1.2.3
last_updated: 2025-10-20
status: active
tools: Read, Write
---

# Test Agent

This is a test agent for update validation.

## Core Features

- Feature 1
- Feature 2

## Version History

**v1.2.3** (2025-10-20) - Bug fixes
- Fixed critical bug
- Improved performance

**v1.2.0** (2025-10-15) - Minor update
- Added new feature
- Updated documentation

**v1.0.0** (2025-10-01) - Initial release
- Basic functionality
"""

SAMPLE_AGENT_NO_HISTORY = """---
name: test-agent-simple
description: Simple test agent without version history.
version: 1.0.0
last_updated: 2025-10-20
status: active
---

# Test Agent Simple

This is a simple test agent.

## Core Features

- Feature 1
"""


# ============================================================================
# Test Functions
# ============================================================================

def test_increment_version():
    """Test version increment logic."""
    print("\n=== Testing Version Increment ===")

    tests = [
        ("1.2.3", "major", "2.0.0"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "patch", "1.2.4"),
        ("0.0.1", "major", "1.0.0"),
        ("5.9.99", "minor", "5.10.0"),
    ]

    passed = 0
    failed = 0

    for current, increment_type, expected in tests:
        try:
            result = increment_version(current, increment_type)
            if result == expected:
                print(f"✅ {current} + {increment_type} = {result}")
                passed += 1
            else:
                print(f"❌ {current} + {increment_type} = {result} (expected {expected})")
                failed += 1
        except Exception as e:
            print(f"❌ {current} + {increment_type} raised {e}")
            failed += 1

    # Test error cases
    error_tests = [
        ("invalid", "major"),
        ("1.2", "minor"),
        ("1.2.3", "invalid"),
    ]

    for current, increment_type in error_tests:
        try:
            result = increment_version(current, increment_type)
            print(f"❌ {current} + {increment_type} should have raised error but got {result}")
            failed += 1
        except ValueError:
            print(f"✅ {current} + {increment_type} correctly raised ValueError")
            passed += 1

    print(f"\nVersion Increment: {passed} passed, {failed} failed")
    return failed == 0


def test_parse_frontmatter():
    """Test YAML frontmatter parsing."""
    print("\n=== Testing Frontmatter Parsing ===")

    try:
        frontmatter_text, metadata, body_content = parse_frontmatter(SAMPLE_AGENT_V1)

        # Check metadata extraction
        assert metadata['name'] == 'test-agent', f"Expected name='test-agent', got '{metadata['name']}'"
        assert metadata['version'] == '1.2.3', f"Expected version='1.2.3', got '{metadata['version']}'"
        assert metadata['status'] == 'active', f"Expected status='active', got '{metadata['status']}'"

        # Check body extraction
        assert '# Test Agent' in body_content, "Body should contain heading"
        assert '## Core Features' in body_content, "Body should contain features section"

        print("✅ Frontmatter parsing works correctly")
        print(f"   - Extracted {len(metadata)} metadata fields")
        print(f"   - Body content: {len(body_content)} chars")
        return True

    except Exception as e:
        print(f"❌ Frontmatter parsing failed: {e}")
        return False


def test_update_frontmatter():
    """Test frontmatter updating."""
    print("\n=== Testing Frontmatter Update ===")

    try:
        frontmatter_text, metadata, _ = parse_frontmatter(SAMPLE_AGENT_V1)

        # Update frontmatter
        updated = update_frontmatter(frontmatter_text, metadata, "2.0.0", "2025-10-25")

        # Verify updates
        assert 'version: 2.0.0' in updated, "Updated version not found"
        assert 'last_updated: 2025-10-25' in updated, "Updated date not found"
        assert 'version: 1.2.3' not in updated, "Old version still present"

        print("✅ Frontmatter update works correctly")
        print(f"   - version: 1.2.3 -> 2.0.0")
        print(f"   - last_updated: 2025-10-20 -> 2025-10-25")
        return True

    except Exception as e:
        print(f"❌ Frontmatter update failed: {e}")
        return False


def test_changelog_formatting():
    """Test changelog formatting."""
    print("\n=== Testing Changelog Formatting ===")

    tests = [
        (
            "Added new feature",
            "**v2.0.0** (2025-10-25) - Added new feature\n- Added new feature\n"
        ),
        (
            "Major update\nAdded feature A\nFixed bug B",
            "**v2.0.0** (2025-10-25) - Major update\n- Major update\n- Added feature A\n- Fixed bug B\n"
        ),
        (
            "- Already has dash\n- Another item",
            "**v2.0.0** (2025-10-25) - Already has dash\n- Already has dash\n- Another item\n"
        ),
    ]

    passed = 0
    failed = 0

    for changelog, expected in tests:
        try:
            result = format_changelog_entry(changelog, "2.0.0", "2025-10-25")
            if result == expected:
                print(f"✅ Changelog formatted correctly")
                passed += 1
            else:
                print(f"❌ Changelog formatting mismatch")
                print(f"   Expected: {repr(expected)}")
                print(f"   Got: {repr(result)}")
                failed += 1
        except Exception as e:
            print(f"❌ Changelog formatting raised {e}")
            failed += 1

    print(f"\nChangelog Formatting: {passed} passed, {failed} failed")
    return failed == 0


def test_changelog_insertion():
    """Test changelog insertion into body."""
    print("\n=== Testing Changelog Insertion ===")

    try:
        _, _, body_content = parse_frontmatter(SAMPLE_AGENT_V1)

        changelog_entry = "**v2.0.0** (2025-10-25) - Major update\n- Breaking changes\n- New features\n"
        updated_body = insert_changelog_entry(body_content, changelog_entry)

        # Verify insertion
        assert "**v2.0.0** (2025-10-25) - Major update" in updated_body, "New entry not found"
        assert "**v1.2.3** (2025-10-20) - Bug fixes" in updated_body, "Old entry not found"

        # Verify order (new entry should come before old entry)
        v2_pos = updated_body.index("**v2.0.0**")
        v1_pos = updated_body.index("**v1.2.3**")
        assert v2_pos < v1_pos, "New entry should come before old entry"

        print("✅ Changelog insertion works correctly")
        print("   - New entry inserted before old entries")
        print("   - Old entries preserved")
        return True

    except Exception as e:
        print(f"❌ Changelog insertion failed: {e}")
        return False


def test_changelog_insertion_no_history():
    """Test changelog insertion when no history section exists."""
    print("\n=== Testing Changelog Insertion (No History Section) ===")

    try:
        _, _, body_content = parse_frontmatter(SAMPLE_AGENT_NO_HISTORY)

        changelog_entry = "**v1.1.0** (2025-10-25) - Minor update\n- Added feature\n"
        updated_body = insert_changelog_entry(body_content, changelog_entry)

        # Verify section created
        assert "## Version History" in updated_body, "Version History section not created"
        assert "**v1.1.0** (2025-10-25) - Minor update" in updated_body, "Changelog entry not found"

        print("✅ Version History section created successfully")
        print("   - Section added to end of body")
        print("   - Changelog entry inserted")
        return True

    except Exception as e:
        print(f"❌ Changelog insertion (no history) failed: {e}")
        return False


def test_full_update_workflow():
    """Test complete update workflow."""
    print("\n=== Testing Full Update Workflow ===")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        agents_dir = os.path.join(temp_dir, "agents")
        os.makedirs(agents_dir)

        # Write test agent
        agent_path = os.path.join(agents_dir, "test-agent.md")
        with open(agent_path, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_AGENT_V1)

        # Perform update (major version)
        result = update_agent(
            agent_name="test-agent",
            increment="major",
            changelog="Major update\nBreaking changes\nNew architecture",
            archive_old=True,
            agents_dir=agents_dir
        )

        if not result['success']:
            print(f"❌ Update failed: {result['message']}")
            return False

        # Verify result
        assert result['old_version'] == '1.2.3', f"Expected old_version='1.2.3', got '{result['old_version']}'"
        assert result['new_version'] == '2.0.0', f"Expected new_version='2.0.0', got '{result['new_version']}'"
        assert result['archive_path'] is not None, "Archive path should be set"

        # Verify updated file
        with open(agent_path, 'r', encoding='utf-8') as f:
            updated_content = f.read()

        assert 'version: 2.0.0' in updated_content, "Version not updated in file"
        assert 'last_updated: 2025-10-25' in updated_content, "Date not updated in file"
        assert '**v2.0.0**' in updated_content, "New version not in changelog"
        assert 'Major update' in updated_content, "Changelog content not found"

        # Verify archive exists
        assert os.path.exists(result['archive_path']), "Archive file not created"

        print("✅ Full update workflow successful")
        print(f"   - Version: {result['old_version']} -> {result['new_version']}")
        print(f"   - Archive: {os.path.basename(result['archive_path'])}")
        print(f"   - Changelog: 3 entries")
        return True


def test_update_minor_and_patch():
    """Test minor and patch updates."""
    print("\n=== Testing Minor and Patch Updates ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        agents_dir = os.path.join(temp_dir, "agents")
        os.makedirs(agents_dir)

        agent_path = os.path.join(agents_dir, "test-agent.md")

        # Test minor update
        with open(agent_path, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_AGENT_V1)

        result = update_agent("test-agent", "minor", "Added new feature", False, agents_dir)

        if not result['success']:
            print(f"❌ Minor update failed: {result['message']}")
            return False

        assert result['new_version'] == '1.3.0', f"Expected 1.3.0, got {result['new_version']}"
        print(f"✅ Minor update: 1.2.3 -> 1.3.0")

        # Test patch update
        result = update_agent("test-agent", "patch", "Fixed bug", False, agents_dir)

        if not result['success']:
            print(f"❌ Patch update failed: {result['message']}")
            return False

        assert result['new_version'] == '1.3.1', f"Expected 1.3.1, got {result['new_version']}"
        print(f"✅ Patch update: 1.3.0 -> 1.3.1")

        return True


def test_error_handling():
    """Test error handling."""
    print("\n=== Testing Error Handling ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        agents_dir = os.path.join(temp_dir, "agents")
        os.makedirs(agents_dir)

        # Test 1: Agent not found
        result = update_agent("nonexistent", "major", "Update", False, agents_dir)
        assert not result['success'], "Should fail for nonexistent agent"
        assert "not found" in result['message'].lower(), "Error message should mention 'not found'"
        print("✅ Handles missing agent correctly")

        # Test 2: Invalid version format
        agent_path = os.path.join(agents_dir, "invalid-version.md")
        with open(agent_path, 'w', encoding='utf-8') as f:
            f.write("""---
name: invalid-version
description: Test
version: invalid
last_updated: 2025-10-25
status: active
---

# Test
""")

        result = update_agent("invalid-version", "major", "Update", False, agents_dir)
        assert not result['success'], "Should fail for invalid version"
        print("✅ Handles invalid version format correctly")

        # Test 3: Empty changelog
        agent_path = os.path.join(agents_dir, "test-agent.md")
        with open(agent_path, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_AGENT_V1)

        result = update_agent("test-agent", "major", "", False, agents_dir)
        assert not result['success'], "Should fail for empty changelog"
        print("✅ Handles empty changelog correctly")

        return True


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run all tests."""
    print("=" * 70)
    print("UPDATE_AGENT.PY TEST SUITE")
    print("=" * 70)

    tests = [
        ("Version Increment", test_increment_version),
        ("Parse Frontmatter", test_parse_frontmatter),
        ("Update Frontmatter", test_update_frontmatter),
        ("Changelog Formatting", test_changelog_formatting),
        ("Changelog Insertion", test_changelog_insertion),
        ("Changelog Insertion (No History)", test_changelog_insertion_no_history),
        ("Full Update Workflow", test_full_update_workflow),
        ("Minor and Patch Updates", test_update_minor_and_patch),
        ("Error Handling", test_error_handling),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} raised unexpected error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    failed_count = len(results) - passed_count

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed_count} passed, {failed_count} failed")

    if failed_count == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
