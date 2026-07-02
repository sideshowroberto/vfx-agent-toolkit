"""
Manual integration test for archive_agent.py.

Usage: python manual_test_archive.py

This script performs real-world testing of the archive_agent functionality:
1. Tests with documentation-specialist.md (real agent)
2. Tests error conditions (missing agent, invalid version)
3. Tests force overwrite
4. Verifies archive directory structure

Run this from the tests/ directory to validate the implementation.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from archive_agent import archive_agent, parse_yaml_frontmatter, validate_version_format


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def test_yaml_parsing():
    """Test YAML frontmatter parsing."""
    print_section("Test 1: YAML Frontmatter Parsing")

    content = """---
name: test-agent
description: A test agent
version: 2.0.0
tools: Read, Write
---

Agent content here.
"""

    result = parse_yaml_frontmatter(content)
    print(f"Parsed metadata: {result}")

    assert result['name'] == 'test-agent'
    assert result['version'] == '2.0.0'
    print("✅ YAML parsing works correctly")


def test_version_validation():
    """Test version format validation."""
    print_section("Test 2: Version Validation")

    valid_versions = ["1.0.0", "2.0.0", "10.20.30"]
    invalid_versions = ["1.0", "v1.0.0", "1.0.0-beta"]

    print("\nValid versions:")
    for v in valid_versions:
        is_valid = validate_version_format(v)
        print(f"  {v}: {'✅ Valid' if is_valid else '❌ Invalid'}")
        assert is_valid

    print("\nInvalid versions:")
    for v in invalid_versions:
        is_valid = validate_version_format(v)
        print(f"  {v}: {'✅ Valid' if is_valid else '❌ Invalid'}")
        assert not is_valid

    print("✅ Version validation works correctly")


def test_with_temp_agent():
    """Test archiving with a temporary test agent."""
    print_section("Test 3: Archive Test Agent")

    # Create temporary directory structure
    temp_dir = tempfile.mkdtemp()
    agents_dir = Path(temp_dir) / ".claude" / "agents"
    agents_dir.mkdir(parents=True)

    try:
        # Create test agent
        agent_content = """---
name: manual-test-agent
description: Agent for manual integration testing
version: 1.5.0
tools: Read, Write
---

You are a test agent.

## Purpose
This is a test agent for manual validation.
"""
        agent_file = agents_dir / "manual-test-agent.md"
        agent_file.write_text(agent_content, encoding='utf-8')

        print(f"\nCreated test agent: {agent_file}")

        # Test 1: Archive the agent
        print("\n--- Test 3a: First Archive ---")
        result = archive_agent(
            "manual-test-agent",
            agents_dir=str(agents_dir)
        )

        print(f"Success: {result['success']}")
        print(f"Version: {result.get('version', 'N/A')}")
        print(f"Archive Path: {result.get('archive_path', 'N/A')}")
        print(f"Message: {result['message']}")

        assert result['success']
        assert result['version'] == '1.5.0'

        archive_path = Path(result['archive_path'])
        assert archive_path.exists()
        print(f"✅ Archive created: {archive_path.name}")

        # Test 2: Try archiving again without force (should fail)
        print("\n--- Test 3b: Archive Without Force (should fail) ---")
        result2 = archive_agent(
            "manual-test-agent",
            agents_dir=str(agents_dir),
            force=False
        )

        print(f"Success: {result2['success']}")
        print(f"Message: {result2['message']}")

        assert not result2['success']
        assert "Archive already exists" in result2['message']
        print("✅ Correctly prevented duplicate archive")

        # Test 3: Archive with force (should succeed)
        print("\n--- Test 3c: Archive With Force (should succeed) ---")
        result3 = archive_agent(
            "manual-test-agent",
            agents_dir=str(agents_dir),
            force=True
        )

        print(f"Success: {result3['success']}")
        print(f"Message: {result3['message']}")

        assert result3['success']
        print("✅ Force overwrite works correctly")

        # Test 4: Archive non-existent agent (should fail)
        print("\n--- Test 3d: Non-Existent Agent (should fail) ---")
        result4 = archive_agent(
            "nonexistent-agent",
            agents_dir=str(agents_dir)
        )

        print(f"Success: {result4['success']}")
        print(f"Message: {result4['message']}")

        assert not result4['success']
        assert "Agent file not found" in result4['message']
        print("✅ Correctly handled missing agent")

        # Verify archive directory structure
        print("\n--- Archive Directory Structure ---")
        archive_dir = agents_dir / "archive"
        print(f"Archive directory: {archive_dir}")
        print("Contents:")
        for item in archive_dir.iterdir():
            print(f"  - {item.name}")

        print("\n✅ All temp agent tests passed!")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temp directory: {temp_dir}")


def test_with_real_agent():
    """Test with real documentation-specialist agent (optional)."""
    print_section("Test 4: Real Agent (Optional)")

    # Look for real agents directory
    real_agents_dir = Path(__file__).parent.parent.parent.parent / ".claude" / "agents"

    if not real_agents_dir.exists():
        print(f"⚠️  Real agents directory not found: {real_agents_dir}")
        print("Skipping real agent test (this is optional)")
        return

    doc_specialist = real_agents_dir / "documentation-specialist.md"
    if not doc_specialist.exists():
        print(f"⚠️  documentation-specialist.md not found: {doc_specialist}")
        print("Skipping real agent test (this is optional)")
        return

    # Read and parse the real agent
    print(f"\nFound real agent: {doc_specialist}")

    content = doc_specialist.read_text(encoding='utf-8')
    metadata = parse_yaml_frontmatter(content)

    print("\nAgent metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")

    version = metadata.get('version', '')
    if version:
        is_valid = validate_version_format(version)
        print(f"\nVersion '{version}' is {'✅ valid' if is_valid else '❌ invalid'}")

        if is_valid:
            print(f"\n📋 To archive this agent, run:")
            print(f"   python archive_agent.py documentation-specialist")
            print(f"   Expected output: documentation-specialist-v{version}.md")
    else:
        print("⚠️  No version found in agent metadata")


def main():
    """Run all manual tests."""
    print("=" * 60)
    print("  archive_agent.py Manual Integration Tests")
    print("=" * 60)

    try:
        test_yaml_parsing()
        test_version_validation()
        test_with_temp_agent()
        test_with_real_agent()

        print_section("All Tests Complete!")
        print("\n✅ archive_agent.py is working correctly")
        print("\nNext steps:")
        print("1. Run pytest: pytest test_archive.py -v")
        print("2. Test with real agent: python ../scripts/archive_agent.py documentation-specialist --agents-dir ../../..")
        print("3. Verify archive created in .claude/agents/archive/")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
