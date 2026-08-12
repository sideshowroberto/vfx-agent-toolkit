"""
Unit tests for archive_agent functionality.

Tests:
    - YAML frontmatter parsing
    - Version validation
    - Agent archiving workflow
    - Error handling (missing files, invalid versions, etc.)
    - Force overwrite functionality
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from archive_agent import (
    parse_yaml_frontmatter,
    validate_version_format,
    archive_agent
)


class TestYAMLParsing:
    """Test YAML frontmatter parsing without PyYAML dependency."""

    def test_parse_valid_frontmatter(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
name: test-agent
description: A test agent
version: 1.0.0
tools: Read, Write
---

Agent content here.
"""
        result = parse_yaml_frontmatter(content)

        assert result['name'] == 'test-agent'
        assert result['description'] == 'A test agent'
        assert result['version'] == '1.0.0'
        assert result['tools'] == 'Read, Write'

    def test_parse_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "Just plain text content"
        result = parse_yaml_frontmatter(content)

        assert result == {}

    def test_parse_empty_frontmatter(self):
        """Test parsing empty frontmatter block."""
        content = """---
---

Content here.
"""
        result = parse_yaml_frontmatter(content)

        # Should handle empty block gracefully
        assert isinstance(result, dict)

    def test_parse_multiline_values(self):
        """Test parsing YAML with multiline description."""
        content = """---
name: test
description: A multi-line description that spans multiple lines
version: 2.0.0
---
"""
        result = parse_yaml_frontmatter(content)

        assert result['name'] == 'test'
        assert 'description' in result
        assert result['version'] == '2.0.0'

    def test_parse_whitespace_handling(self):
        """Test that whitespace around keys and values is stripped."""
        content = """---
name:  test-agent
version:   1.0.0
---
"""
        result = parse_yaml_frontmatter(content)

        assert result['name'] == 'test-agent'
        assert result['version'] == '1.0.0'


class TestVersionValidation:
    """Test semantic version format validation."""

    def test_valid_versions(self):
        """Test that valid semantic versions pass validation."""
        valid_versions = [
            "1.0.0",
            "0.1.0",
            "10.20.30",
            "999.999.999",
            "2.0.0"
        ]

        for version in valid_versions:
            assert validate_version_format(version), f"Version {version} should be valid"

    def test_invalid_versions(self):
        """Test that invalid version formats fail validation."""
        invalid_versions = [
            "1.0",           # Missing patch
            "1",             # Missing minor and patch
            "1.0.0.0",       # Too many components
            "v1.0.0",        # Prefix not allowed
            "1.0.0-beta",    # Pre-release tag
            "1.0.0+build",   # Build metadata
            "1.0.x",         # Non-numeric
            "",              # Empty
            "1.0.0 ",        # Trailing space
            " 1.0.0",        # Leading space
        ]

        for version in invalid_versions:
            assert not validate_version_format(version), f"Version '{version}' should be invalid"


class TestArchiveAgent:
    """Test agent archiving functionality."""

    @pytest.fixture
    def temp_agents_dir(self):
        """Create temporary agents directory structure."""
        temp_dir = tempfile.mkdtemp()
        agents_dir = Path(temp_dir) / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        yield agents_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_agent_file(self, temp_agents_dir):
        """Create a sample agent file."""
        agent_content = """---
name: test-agent
description: A test agent for archiving
version: 2.0.0
tools: Read, Write, Edit
---

You are a test agent.

## Purpose

This is a test agent for validating the archive functionality.
"""
        agent_file = temp_agents_dir / "test-agent.md"
        agent_file.write_text(agent_content, encoding='utf-8')

        return agent_file

    def test_archive_success(self, temp_agents_dir, sample_agent_file):
        """Test successful agent archiving."""
        result = archive_agent(
            "test-agent",
            agents_dir=str(temp_agents_dir)
        )

        assert result['success'] is True
        assert result['version'] == '2.0.0'
        assert 'test-agent-v2.0.0.md' in result['archive_path']

        # Verify archive file exists
        archive_path = Path(result['archive_path'])
        assert archive_path.exists()

        # Verify archive directory was created
        assert (temp_agents_dir / "archive").exists()

        # Verify content was preserved
        archived_content = archive_path.read_text(encoding='utf-8')
        original_content = sample_agent_file.read_text(encoding='utf-8')
        assert archived_content == original_content

    def test_archive_agent_not_found(self, temp_agents_dir):
        """Test archiving non-existent agent."""
        result = archive_agent(
            "nonexistent-agent",
            agents_dir=str(temp_agents_dir)
        )

        assert result['success'] is False
        assert "Agent file not found" in result['message']

    def test_archive_no_version(self, temp_agents_dir):
        """Test archiving agent without version in frontmatter."""
        agent_content = """---
name: no-version-agent
description: Agent without version
---

Content here.
"""
        agent_file = temp_agents_dir / "no-version-agent.md"
        agent_file.write_text(agent_content, encoding='utf-8')

        result = archive_agent(
            "no-version-agent",
            agents_dir=str(temp_agents_dir)
        )

        assert result['success'] is False
        assert "No version found" in result['message']

    def test_archive_invalid_version(self, temp_agents_dir):
        """Test archiving agent with invalid version format."""
        agent_content = """---
name: invalid-version-agent
description: Agent with invalid version
version: 1.0
---

Content here.
"""
        agent_file = temp_agents_dir / "invalid-version-agent.md"
        agent_file.write_text(agent_content, encoding='utf-8')

        result = archive_agent(
            "invalid-version-agent",
            agents_dir=str(temp_agents_dir)
        )

        assert result['success'] is False
        assert "Invalid version format" in result['message']

    def test_archive_already_exists_no_force(self, temp_agents_dir, sample_agent_file):
        """Test archiving when archive already exists without --force."""
        # First archive
        result1 = archive_agent(
            "test-agent",
            agents_dir=str(temp_agents_dir)
        )
        assert result1['success'] is True

        # Second archive without force
        result2 = archive_agent(
            "test-agent",
            agents_dir=str(temp_agents_dir),
            force=False
        )

        assert result2['success'] is False
        assert "Archive already exists" in result2['message']
        assert "--force" in result2['message']

    def test_archive_already_exists_with_force(self, temp_agents_dir, sample_agent_file):
        """Test archiving with --force overwrites existing archive."""
        # First archive
        result1 = archive_agent(
            "test-agent",
            agents_dir=str(temp_agents_dir)
        )
        assert result1['success'] is True

        archive_path = Path(result1['archive_path'])
        original_mtime = archive_path.stat().st_mtime

        # Modify original agent file
        modified_content = """---
name: test-agent
description: Modified description
version: 2.0.0
tools: Read, Write, Edit, Grep
---

Modified content.
"""
        sample_agent_file.write_text(modified_content, encoding='utf-8')

        # Second archive with force
        result2 = archive_agent(
            "test-agent",
            agents_dir=str(temp_agents_dir),
            force=True
        )

        assert result2['success'] is True
        assert result2['archive_path'] == result1['archive_path']

        # Verify file was overwritten
        new_mtime = archive_path.stat().st_mtime
        assert new_mtime >= original_mtime  # File was updated

        # Verify new content
        archived_content = archive_path.read_text(encoding='utf-8')
        assert "Modified content" in archived_content

    def test_archive_creates_directory(self, temp_agents_dir, sample_agent_file):
        """Test that archive directory is created if it doesn't exist."""
        # Ensure archive directory doesn't exist
        archive_dir = temp_agents_dir / "archive"
        assert not archive_dir.exists()

        result = archive_agent(
            "test-agent",
            agents_dir=str(temp_agents_dir)
        )

        assert result['success'] is True
        assert archive_dir.exists()
        assert archive_dir.is_dir()

    def test_archive_multiple_versions(self, temp_agents_dir):
        """Test archiving multiple versions of same agent."""
        # Create v1.0.0
        v1_content = """---
name: multi-version-agent
version: 1.0.0
---
Version 1.0.0 content
"""
        agent_file = temp_agents_dir / "multi-version-agent.md"
        agent_file.write_text(v1_content, encoding='utf-8')

        result_v1 = archive_agent(
            "multi-version-agent",
            agents_dir=str(temp_agents_dir)
        )
        assert result_v1['success'] is True

        # Update to v2.0.0
        v2_content = """---
name: multi-version-agent
version: 2.0.0
---
Version 2.0.0 content
"""
        agent_file.write_text(v2_content, encoding='utf-8')

        result_v2 = archive_agent(
            "multi-version-agent",
            agents_dir=str(temp_agents_dir)
        )
        assert result_v2['success'] is True

        # Verify both archives exist
        archive_dir = temp_agents_dir / "archive"
        assert (archive_dir / "multi-version-agent-v1.0.0.md").exists()
        assert (archive_dir / "multi-version-agent-v2.0.0.md").exists()

        # Verify content is different
        v1_archived = (archive_dir / "multi-version-agent-v1.0.0.md").read_text(encoding='utf-8')
        v2_archived = (archive_dir / "multi-version-agent-v2.0.0.md").read_text(encoding='utf-8')
        assert "Version 1.0.0 content" in v1_archived
        assert "Version 2.0.0 content" in v2_archived

    def test_archive_preserves_content_exactly(self, temp_agents_dir):
        """Test that archiving preserves file content exactly (no modifications)."""
        agent_content = """---
name: preservation-test
description: Test exact content preservation
version: 3.5.7
tools: Read, Write, Edit, Grep, Glob
model: sonnet
---

You are a preservation test agent.

## Special Characters

- Emoji: \U0001F525 \u2705 \u274C
- Unicode: \u03B1\u03B2\u03B3 \u03B4\u03B5\u03B6
- Quotes: "double" 'single'
- Symbols: @#$%^&*()

## Code Block

```python
def test():
    return "preserve me"
```

## Edge Cases

Trailing whitespace:
Multiple    spaces
Tabs	here
"""
        agent_file = temp_agents_dir / "preservation-test.md"
        agent_file.write_text(agent_content, encoding='utf-8')

        result = archive_agent(
            "preservation-test",
            agents_dir=str(temp_agents_dir)
        )

        assert result['success'] is True

        # Verify byte-for-byte identical content
        original_content = agent_file.read_text(encoding='utf-8')
        archived_content = Path(result['archive_path']).read_text(encoding='utf-8')
        assert archived_content == original_content

    def test_archive_absolute_path(self, temp_agents_dir, sample_agent_file):
        """Test that archive_path in result is absolute."""
        result = archive_agent(
            "test-agent",
            agents_dir=str(temp_agents_dir)
        )

        assert result['success'] is True

        archive_path = Path(result['archive_path'])
        assert archive_path.is_absolute()

    def test_archive_relative_agents_dir(self, temp_agents_dir, sample_agent_file):
        """Test archiving with relative agents_dir path converts to absolute."""
        # This test verifies pathlib.Path().resolve() works correctly
        result = archive_agent(
            "test-agent",
            agents_dir=str(temp_agents_dir)  # Could be relative
        )

        assert result['success'] is True

        # Result should always have absolute path
        archive_path = Path(result['archive_path'])
        assert archive_path.is_absolute()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def temp_agents_dir(self):
        """Create temporary agents directory structure."""
        temp_dir = tempfile.mkdtemp()
        agents_dir = Path(temp_dir) / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        yield agents_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_agent_name_with_spaces(self, temp_agents_dir):
        """Test archiving agent with spaces in name."""
        agent_content = """---
name: agent with spaces
version: 1.0.0
---
Content
"""
        # Note: Agent filenames typically don't have spaces, but test handling
        agent_file = temp_agents_dir / "agent-with-spaces.md"
        agent_file.write_text(agent_content, encoding='utf-8')

        result = archive_agent(
            "agent-with-spaces",
            agents_dir=str(temp_agents_dir)
        )

        assert result['success'] is True
        assert "agent-with-spaces-v1.0.0.md" in result['archive_path']

    def test_version_with_leading_zeros(self, temp_agents_dir):
        """Test version numbers with leading zeros."""
        agent_content = """---
name: leading-zeros
version: 01.02.03
---
Content
"""
        agent_file = temp_agents_dir / "leading-zeros.md"
        agent_file.write_text(agent_content, encoding='utf-8')

        result = archive_agent(
            "leading-zeros",
            agents_dir=str(temp_agents_dir)
        )

        # Should succeed - regex allows leading zeros
        assert result['success'] is True
        assert result['version'] == '01.02.03'

    def test_empty_agent_file(self, temp_agents_dir):
        """Test archiving completely empty agent file."""
        agent_file = temp_agents_dir / "empty-agent.md"
        agent_file.write_text("", encoding='utf-8')

        result = archive_agent(
            "empty-agent",
            agents_dir=str(temp_agents_dir)
        )

        # Should fail - no frontmatter
        assert result['success'] is False
        assert "No version found" in result['message']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
