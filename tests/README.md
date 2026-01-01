# Repo-Swarm Test Suite

Comprehensive test suite for environment variable inheritance, security validation, error handling, and script consistency.

## Test Structure

```
tests/
├── unit/                           # Unit tests for Python code
├── integration/                    # Integration tests for workflows
│   ├── test_env_var_inheritance.py  # Environment variable propagation
│   ├── test_error_handling.py       # Error handling and cleanup
│   └── test_script_consistency.py   # Script consistency checks
├── security/                       # Security validation tests
│   └── test_security_validation.py  # Security checks for scripts
├── helpers/                        # Test helper utilities
│   ├── script_runner.py            # Bash script execution helpers
│   └── security_validators.py      # Security validation functions
└── fixtures/                       # Test fixtures
    └── test_env_files/             # Sample .env files for testing
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories

**Environment Variable Inheritance:**
```bash
pytest tests/integration/test_env_var_inheritance.py -v
```

**Security Validation:**
```bash
pytest tests/security/test_security_validation.py -v
```

**Error Handling:**
```bash
pytest tests/integration/test_error_handling.py -v
```

**Script Consistency:**
```bash
pytest tests/integration/test_script_consistency.py -v
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

## Test Categories

### Part 1: Environment Variable Inheritance (`test_env_var_inheritance.py`)

Tests verifying environment variables are properly passed from parent scripts to worker subprocesses.

**Test Cases:**
- `test_claude_model_inherited_from_env_file` - CLAUDE_MODEL from .env.local reaches worker
- `test_claude_model_override_via_cli` - CLI override takes precedence
- `test_all_anthropic_vars_inherited` - All Anthropic vars exported to worker
- `test_local_testing_vars_inherited` - LOCAL_TESTING vars available
- `test_missing_env_file_uses_defaults` - Defaults when .env.local missing
- `test_env_vars_available_in_activities` - Variables accessible in Python activities
- `test_env_var_export_ordering` - Correct order: load, override, export
- `test_env_var_propagation_to_client` - Client subprocess receives vars

**Critical Verification:**
- ✅ CLAUDE_MODEL exported before worker starts (P0 fix)
- ✅ CLI overrides work correctly
- ✅ All Anthropic configuration inherited
- ✅ Local testing flags available

### Part 2: Security Validation (`test_security_validation.py`)

Tests ensuring sensitive information is protected and malicious input is sanitized.

**Test Cases:**
- `test_api_keys_not_in_logs` - No API keys in output
- `test_api_key_masking_in_output` - Keys masked as "********** (present)"
- `test_command_injection_prevention` - Shell metacharacters removed
- `test_env_file_permission_warning` - Warns on world-readable files
- `test_env_file_ownership_validation` - Validates file ownership
- `test_malicious_input_sanitization` - Various injection attempts sanitized
- `test_no_secrets_in_error_messages` - Error messages don't leak secrets
- `test_no_eval_or_exec` - No dangerous eval usage
- `test_github_token_not_logged` - GitHub tokens masked
- `test_no_hardcoded_secrets` - No hardcoded API keys
- `test_secure_env_file_loading` - Uses 'set -a' pattern

**Security Features Verified:**
- ✅ API key masking (never logged in plaintext)
- ✅ Input sanitization (prevents command injection)
- ✅ File permission validation (600 recommended)
- ✅ File ownership checks (current user)
- ✅ No eval with user input

### Part 3: Error Handling (`test_error_handling.py`)

Tests verifying proper cleanup and error handling in all exit scenarios.

**Test Cases:**
- `test_cleanup_function_exists` - Cleanup function defined
- `test_trap_registered_for_all_signals` - Trap for EXIT, ERR, INT, TERM
- `test_cleanup_on_ctrl_c` - SIGINT triggers cleanup
- `test_cleanup_on_error` - ERR trap triggers cleanup
- `test_missing_api_key_fails_gracefully` - Clear error when API key missing
- `test_temporal_startup_failure_cleanup` - Cleanup if Temporal fails
- `test_worker_startup_failure_cleanup` - Cleanup if worker fails
- `test_orphaned_process_prevention` - No background processes left
- `test_cleanup_handles_already_stopped_processes` - Graceful handling
- `test_cleanup_order` - Worker killed before server
- `test_exit_code_preservation` - Original exit code preserved

**Error Handling Verified:**
- ✅ Trap-based cleanup for all exit paths
- ✅ Background processes properly tracked
- ✅ PIDs captured and killed on exit
- ✅ Clear error messages
- ✅ No orphaned processes

### Part 4: Script Consistency (`test_script_consistency.py`)

Tests ensuring all scripts follow the same patterns for security and error handling.

**Test Cases:**
- `test_all_scripts_have_sanitize_input` - Same sanitize_input function
- `test_all_scripts_have_cleanup_function` - Consistent cleanup
- `test_all_scripts_register_trap` - All use trap
- `test_all_scripts_check_api_key` - API key validation
- `test_all_scripts_mask_api_key` - Consistent masking
- `test_all_scripts_load_env_file` - Same .env.local loading
- `test_all_scripts_export_anthropic_vars` - Export before worker
- `test_all_scripts_export_local_testing_vars` - Local testing vars
- `test_all_scripts_set_defaults_for_missing_env` - Consistent defaults
- `test_all_scripts_sanitize_user_input` - All sanitize input
- `test_security_features_consistent` - All security features present

**Consistency Verified:**
- ✅ Same security measures in all scripts
- ✅ Same error handling patterns
- ✅ Same environment loading
- ✅ Same cleanup mechanisms

## Test Helpers

### `script_runner.py`

Utilities for running bash scripts and capturing output:

```python
from tests.helpers.script_runner import ScriptRunner, create_test_env_file

# Run a script
runner = ScriptRunner()
result = runner.run_script("single.sh", args=["is-odd", "force"])

# Check output
assert result.returncode == 0
assert "Starting investigation" in result.stdout

# Create test env file
env_file = create_test_env_file(
    tmp_path / ".env.local",
    api_key="test-key",
    model="claude-3-haiku-20241022"
)
```

### `security_validators.py`

Security validation functions:

```python
from tests.helpers.security_validators import (
    check_for_api_keys_in_output,
    verify_api_key_masking,
    check_command_injection_sanitization
)

# Check for leaked API keys
violations = check_for_api_keys_in_output(script_output)
assert len(violations) == 0

# Verify proper masking
assert verify_api_key_masking(script_output)

# Verify input sanitization
assert check_command_injection_sanitization(output, malicious_input)
```

## Test Fixtures

### Test Environment Files

Located in `tests/fixtures/test_env_files/`:

- `valid_secure.env` - Properly configured .env with secure permissions
- `valid_with_overrides.env` - Environment with custom overrides
- `missing_api_key.env` - Missing API key for error testing

## Writing New Tests

### Test Naming Convention

- Test files: `test_<feature>.py`
- Test classes: `Test<Feature>`
- Test methods: `test_<specific_behavior>`

### Example Test

```python
import pytest
from tests.helpers.script_runner import ScriptRunner

class TestNewFeature:
    @pytest.fixture
    def script_runner(self):
        return ScriptRunner()

    def test_specific_behavior(self, script_runner):
        """Test that specific behavior works correctly."""
        result = script_runner.run_script(
            "single.sh",
            args=["is-odd"],
            env_vars={"LOCAL_TESTING": "true"}
        )

        assert result.returncode == 0
        assert "expected output" in result.stdout
```

## Coverage Requirements

### Target Coverage

- **Environment variable tests**: 100% of export paths
- **Security tests**: All identified vulnerabilities covered
- **Error handling**: All trap conditions tested
- **Script consistency**: All scripts validated

### Running Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html --cov-report=term

# View report
open htmlcov/index.html
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```bash
# Quick validation (unit + integration)
pytest tests/integration tests/security -v --tb=short

# Full test suite with coverage
pytest --cov=src --cov-report=term --cov-report=xml -v
```

## Troubleshooting

### Tests Fail Due to Missing Dependencies

```bash
# Install test dependencies
pip install -r requirements-test.txt
# or
uv sync --dev
```

### Tests Hang on Script Execution

- Check if Temporal server is already running
- Increase timeout values in `script_runner.py`
- Run with `-v` flag to see detailed output

### Permission Errors

```bash
# Ensure test env files have correct permissions
chmod 600 tests/fixtures/test_env_files/*.env
```

## Test Philosophy

### What We Test

1. **Behavior over Implementation**: Test what the code does, not how it does it
2. **User Scenarios**: Test real-world usage patterns
3. **Error Paths**: Test failure scenarios as thoroughly as success paths
4. **Security**: Every security measure must be tested

### What We Don't Test

- Internal implementation details that might change
- Third-party libraries (assume they work)
- UI/visual aspects (these are CLI scripts)

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests cover security implications
3. Add integration tests for end-to-end workflows
4. Update this README with new test categories

## Test Execution Time

Expected execution times:

- Unit tests: < 5 seconds
- Integration tests: 30-60 seconds
- Security tests: 10-20 seconds
- Full suite: ~2 minutes

## Related Documentation

- [Main README](../README.md) - Project overview
- [WORKLOG.md](../WORKLOG.md) - Implementation details
- [Scripts README](../scripts/README.md) - Script documentation
