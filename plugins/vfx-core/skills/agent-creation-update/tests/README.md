# Agent-Creation-Update Test Suite

Comprehensive testing for the agent-creation-update skill, covering all 4 scripts and their integration.

---

## Overview

**Test Types:**
- **Unit Tests** - Individual script functionality (create, update, validate, archive)
- **Integration Tests** - Complete workflows combining multiple scripts
- **Coverage** - All scripts working together in realistic scenarios

**Test Files:**
- `test_create.py` - Unit tests for create_agent.py
- `test_update.py` - Unit tests for update_agent.py
- `test_validate.py` - Unit tests for validate_agent.py
- `test_archive.py` - Unit tests for archive_agent.py
- `test_integration.py` - Integration tests (6 comprehensive scenarios)
- `run_all_tests.py` - Test runner for all tests

---

## Quick Start

### Run All Tests

```bash
cd <workspace>\.claude\skills\agent-creation-update\tests
python run_all_tests.py
```

**Expected Output:**
```
======================================================================
RUNNING UNIT TESTS (pytest)
======================================================================
...

======================================================================
RUNNING INTEGRATION TESTS
======================================================================
...

======================================================================
COMBINED TEST REPORT
======================================================================
Unit Tests:
  Tests Run: 15
  Failures: 0
  Status: [OK] PASS

Integration Tests:
  Tests Run: 6
  Failures: 0
  Status: [OK] PASS

----------------------------------------------------------------------
Total Tests: 21
Total Failures: 0
Overall Status: [OK] PASS

 All tests passed!
======================================================================
```

### Run Integration Tests Only

```bash
python test_integration.py
```

**Expected Output:**
```
======================================================================
AGENT-CREATION-UPDATE INTEGRATION TEST SUITE
======================================================================

Test 1: Complete Agent Lifecycle
  [OK] Create agent (v1.0.0)
  [OK] Validate agent (PASS)
  [OK] Update agent to v1.1.0
  [OK] Validate updated agent (PASS)
  [OK] Archive created (v1.0.0)
  [OK] Cleanup successful

Test 2: Create From All Templates
  [OK] tool-specialist created
  [OK] tool-specialist validated (PASS)
  [OK] cross-tool created
  [OK] cross-tool validated (PASS)
  [OK] general-helper created
  [OK] general-helper validated (PASS)

... [4 more tests]

======================================================================
TEST SUMMARY
======================================================================
Total Tests: 6
Passed: 6
Failed: 0

 All integration tests passed!
======================================================================
```

### Run Unit Tests Only

```bash
python run_all_tests.py --unit-only
```

### Run With Verbose Output

```bash
python run_all_tests.py --verbose
```

---

## Integration Test Scenarios

### Test 1: Complete Agent Lifecycle

**What it tests:**
- Create new agent
- Validate agent (should PASS)
- Update agent (minor version)
- Validate updated agent (should PASS)
- Archive agent
- Verify archive exists
- Delete agent
- Verify cleanup

**Why it matters:**
- Most common workflow
- Tests all 4 scripts working together
- Validates end-to-end process

**Checks:**
- [OK] Create agent (v1.0.0)
- [OK] Validate agent (PASS)
- [OK] Update agent to v1.1.0
- [OK] Validate updated agent (PASS)
- [OK] Archive created (v1.0.0)
- [OK] Cleanup successful

---

### Test 2: Create From All Templates

**What it tests:**
- Create agent from tool-specialist template
- Create agent from cross-tool template
- Create agent from general-helper template
- Validate all 3 agents (should PASS)
- Verify all have correct structure

**Why it matters:**
- Tests template application system
- Validates all template types work
- Ensures template placeholders replaced correctly

**Checks:**
- [OK] tool-specialist created
- [OK] tool-specialist validated (PASS)
- [OK] cross-tool created
- [OK] cross-tool validated (PASS)
- [OK] general-helper created
- [OK] general-helper validated (PASS)

---

### Test 3: Version Increments

**What it tests:**
- Create agent (v1.0.0)
- Update major (v1.0.0 -> v2.0.0)
- Update minor (v2.0.0 -> v2.1.0)
- Update patch (v2.1.0 -> v2.1.1)
- Verify 3 archives created (v1.0.0, v2.0.0, v2.1.0)
- Validate final agent (should PASS)

**Why it matters:**
- Tests semantic versioning logic
- Validates archive creation on updates
- Ensures version metadata stays consistent

**Checks:**
- [OK] Create agent (v1.0.0)
- [OK] Major increment (1.0.0 -> 2.0.0)
- [OK] Minor increment (2.0.0 -> 2.1.0)
- [OK] Patch increment (2.1.0 -> 2.1.1)
- [OK] All archives created
- [OK] Validate final agent (PASS)

---

### Test 4: Validation Prevents Invalid Agents

**What it tests:**
- Create agent with invalid name (version suffix) - should fail
- Manually create invalid agent file
- Validation should FAIL
- Update should refuse to proceed on invalid agent

**Why it matters:**
- Tests validation safeguards
- Ensures invalid agents rejected
- Prevents corruption of agent directory

**Checks:**
- [OK] Invalid name rejected
- [OK] Invalid agent validation fails
- [OK] Update blocked on invalid agent

---

### Test 5: Archive Restoration Workflow

**What it tests:**
- Create agent (v1.0.0)
- Update to v2.0.0
- Archive v1.0.0 created
- Delete v2.0.0 (rollback scenario)
- Copy archive back to active location
- Validate restored v1.0.0 (should PASS)

**Why it matters:**
- Tests rollback scenario
- Validates archive integrity
- Ensures archives are usable for restoration

**Checks:**
- [OK] Original created and updated
- [OK] Archive v1.0.0 exists
- [OK] Restoration successful
- [OK] Restored agent validates

---

### Test 6: Force Overwrite Workflow

**What it tests:**
- Create agent (v1.0.0)
- Create same agent without --force (should fail)
- Create same agent with --force (should succeed)
- Update agent (v2.0.0)
- Archive already exists for v1.0.0
- Archive with --force (should overwrite)

**Why it matters:**
- Tests force overwrite behavior
- Validates duplicate detection
- Ensures --force flag works correctly

**Checks:**
- [OK] Duplicate creation blocked
- [OK] Force overwrite succeeds
- [OK] Archive force overwrite succeeds

---

## Test Infrastructure

### Temporary Directories

All integration tests use temporary directories for isolation:

```python
suite.setup()  # Creates temp_dir with agents/ and archive/ subdirs
suite.teardown()  # Cleans up temp_dir after tests
```

**Benefits:**
- No interference between tests
- No impact on actual agent directory
- Automatic cleanup even if tests fail

### Script Execution

Tests execute actual scripts via subprocess:

```python
result = suite.run_script('create_agent.py', [
    'agent-name',
    '--description', 'Test agent',
    '--tools', 'Read,Write,Edit',
    '--type', 'general-helper',
    '--agents-dir', str(suite.agents_dir)
])
```

**Validation:**
- Exit codes (0 = success, 1 = failure)
- File existence
- File content (version numbers, metadata)
- Output messages

---

## Troubleshooting Test Failures

### Integration Test Fails

**Symptom:** Test shows [FAIL] FAIL

**Steps:**
1. Run integration test with verbose output:
   ```bash
   python test_integration.py
   ```

2. Check which specific check failed:
   ```
   Test 1: Complete Agent Lifecycle - [FAIL] FAIL
     [OK] Create agent (v1.0.0)
     [FAIL] Validate agent (PASS)  <-- This check failed
     ...
   ```

3. Run the failing script manually:
   ```bash
   cd tests
   python ../scripts/validate_agent.py test-agent --agents-dir /tmp/test_agents
   ```

4. Check script output for errors

### Unit Test Fails

**Symptom:** pytest shows failed tests

**Steps:**
1. Run pytest with verbose output:
   ```bash
   python run_all_tests.py --unit-only --verbose
   ```

2. Identify failing test:
   ```
   tests/test_create.py::test_template_application FAILED
   ```

3. Run individual test:
   ```bash
   pytest tests/test_create.py::test_template_application -v
   ```

4. Check assertion errors in output

### All Tests Fail

**Symptom:** Both unit and integration tests fail

**Possible Causes:**
1. **Missing scripts** - Check scripts/ directory exists and contains all 4 scripts
2. **Missing templates** - Check reference/ directory contains agent_template.md
3. **Python path issues** - Run from tests/ directory
4. **Permissions** - Ensure write access to temp directories

**Verification:**
```bash
# Check scripts exist
ls ../scripts/*.py

# Check template exists
ls ../reference/agent_template.md

# Check Python version
python --version  # Should be 3.8+

# Run from correct directory
cd tests/
python test_integration.py
```

### Script Not Found Error

**Symptom:** `FileNotFoundError: Script not found: .../scripts/create_agent.py`

**Solution:**
Ensure you're running from the tests/ directory:
```bash
cd <workspace>\.claude\skills\agent-creation-update\tests
python test_integration.py
```

### Template Not Found Error

**Symptom:** Test fails with "Template not found" message

**Solution:**
Check template file exists:
```bash
ls ../reference/agent_template.md
```

If missing, recreate from VFX_SKILL_TEMPLATE.md

### Cleanup Errors

**Symptom:** Tests pass but temp directories not cleaned up

**Solution:**
Manually clean temp directories:
```bash
# Windows
del /s /q %TEMP%\agent_test_*

# Linux/Mac
rm -rf /tmp/agent_test_*
```

### Validation Always Fails

**Symptom:** Validation check always shows [FAIL] FAIL

**Possible Causes:**
1. **validate_agent.py has bugs** - Test script independently
2. **Agent template invalid** - Check template has all required fields
3. **YAML frontmatter parsing fails** - Check frontmatter format

**Debug Steps:**
1. Create agent manually:
   ```bash
   python ../scripts/create_agent.py test-debug --description "Test" --tools "Read,Write" --type general-helper
   ```

2. Validate manually:
   ```bash
   python ../scripts/validate_agent.py test-debug
   ```

3. Check validation output for specific errors

---

## Exit Codes

**Integration Tests (test_integration.py):**
- `0` - All tests passed
- `1` - One or more tests failed

**Combined Tests (run_all_tests.py):**
- `0` - All tests passed
- `1` - One or more tests failed
- `2` - Error running tests (missing pytest, etc.)

---

## Test Coverage

**Scripts Covered:**
- [OK] create_agent.py - Agent creation, template application
- [OK] update_agent.py - Version increments, changelog
- [OK] validate_agent.py - Article IX validation
- [OK] archive_agent.py - Archive workflow

**Workflows Covered:**
- [OK] Complete agent lifecycle
- [OK] Template application (all 3 types)
- [OK] Semantic versioning (major, minor, patch)
- [OK] Validation safeguards
- [OK] Archive restoration
- [OK] Force overwrite

**Edge Cases Covered:**
- [OK] Invalid agent names
- [OK] Duplicate creation attempts
- [OK] Missing metadata
- [OK] Archive conflicts
- [OK] Rollback scenarios
- [OK] Force overwrite behavior

---

## Adding New Tests

### Add Integration Test

1. Add new test function to `test_integration.py`:
```python
def test_new_scenario(suite: IntegrationTestSuite) -> bool:
    """Test description."""
    print("\nTest N: New Scenario")

    checks = []

    # Test steps
    # ...

    return suite.add_result("New Scenario", checks)
```

2. Call from `run_all_tests()`:
```python
test_new_scenario(suite)
```

3. Run tests to verify:
```bash
python test_integration.py
```

### Add Unit Test

1. Create new test file or add to existing:
```python
# tests/test_new_feature.py
import pytest

def test_new_feature():
    """Test new feature."""
    result = new_feature_function()
    assert result == expected_value
```

2. Run tests:
```bash
python run_all_tests.py --unit-only
```

---

## Requirements

**Python:**
- Python 3.8+
- pytest (for unit tests)

**Installation:**
```bash
pip install pytest
```

**Scripts:**
- create_agent.py
- update_agent.py
- validate_agent.py
- archive_agent.py

**Templates:**
- reference/agent_template.md
- reference/examples/*.md

---

## Continuous Integration

**Pre-Commit Hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

cd .claude/skills/agent-creation-update/tests
python run_all_tests.py

if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

**GitHub Actions:**
```yaml
# .github/workflows/test.yml
name: Test Agent-Creation-Update

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install pytest
      - name: Run tests
        run: |
          cd .claude/skills/agent-creation-update/tests
          python run_all_tests.py
```

---

## Contributing

When adding new functionality:
1. Write tests first (TDD approach)
2. Run all tests before committing
3. Add integration test for workflows
4. Update this README with new test scenarios

---

## Support

**Issues:**
- Test failures -> Check troubleshooting section above
- Missing features -> Add new test scenarios
- Bug reports -> Include test output

**Contact:**
- VFX Pipeline Team
- Reference: VFX_SKILL_CONSTITUTION.md Article IX

---

*Last Updated: 2025-10-25*
