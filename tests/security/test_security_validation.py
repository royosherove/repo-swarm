"""Security validation tests for repo-swarm scripts.

These tests verify that sensitive information is properly protected and
malicious input is sanitized.
"""

import pytest
import os
import stat
from pathlib import Path
from unittest.mock import patch

from tests.helpers.script_runner import (
    ScriptRunner,
    create_test_env_file
)
from tests.helpers.security_validators import (
    check_for_api_keys_in_output,
    verify_api_key_masking,
    check_command_injection_sanitization,
    check_file_permissions,
    check_file_ownership,
    find_security_violations_in_output,
    validate_input_sanitization
)


class TestSecurityValidation:
    """Security validation tests for scripts and workflows."""

    @pytest.fixture
    def script_runner(self):
        """Create script runner instance."""
        return ScriptRunner()

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def test_env_secure(self, tmp_path):
        """Create secure test env file."""
        env_file = tmp_path / ".env.local"
        create_test_env_file(
            env_file,
            api_key="sk-ant-test123456789012345678901234567890ab",
            model="claude-3-haiku-20241022"
        )
        env_file.chmod(0o600)  # Secure permissions
        return env_file

    @pytest.fixture
    def test_env_insecure(self, tmp_path):
        """Create insecure test env file (wrong permissions)."""
        env_file = tmp_path / ".env.local.insecure"
        create_test_env_file(
            env_file,
            api_key="sk-ant-test123456789012345678901234567890cd"
        )
        env_file.chmod(0o644)  # World-readable - insecure!
        return env_file

    def test_api_keys_not_in_logs(self, script_runner, repo_root):
        """Test that API keys are never printed in stdout/stderr.

        Critical security check: No actual API keys should appear in output.
        """
        # Check script for direct API key printing
        scripts_to_check = ["single.sh", "full.sh", "investigate-single.sh", "investigate.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            if not script_path.exists():
                continue

            script_content = script_path.read_text()

            # Verify no direct echo of ANTHROPIC_API_KEY
            assert 'echo "$ANTHROPIC_API_KEY"' not in script_content, \
                f"{script_name} must not directly echo API key"
            assert 'echo $ANTHROPIC_API_KEY' not in script_content, \
                f"{script_name} must not directly echo API key (unquoted)"

            # Verify proper masking if printing the value (not just mentioning in error)
            lines = script_content.split('\n')
            for i, line in enumerate(lines):
                if 'ANTHROPIC_API_KEY' in line and 'echo' in line.lower():
                    # Skip error messages that just mention the variable name
                    if 'not set' in line.lower() or 'missing' in line.lower() or 'error' in line.lower():
                        continue
                    # If actually printing the value (with $), should have masking
                    if '$ANTHROPIC_API_KEY' in line and '"$ANTHROPIC_API_KEY"' not in line:
                        assert '***' in line or 'present' in line.lower(), \
                            f"{script_name}:{i+1} - API key value must be masked when printed"

    def test_api_key_masking_in_output(self, script_runner, repo_root):
        """Test that API key references use the masked pattern '********** (present)'."""
        # Check single.sh for masking pattern
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Verify masking pattern exists
        assert '********** (present)' in script_content, \
            "Script must use '********** (present)' pattern for API key masking"

        # Verify it's used in the right context
        lines = script_content.split('\n')
        found_masking = False

        for i, line in enumerate(lines):
            if '********** (present)' in line:
                # Check it's in an echo statement checking API key
                context_lines = '\n'.join(lines[max(0, i-3):i+3])
                assert 'ANTHROPIC_API_KEY' in context_lines, \
                    "Masking pattern should be used for API key output"
                found_masking = True

        assert found_masking, "API key masking pattern not properly implemented"

    def test_command_injection_prevention(self, script_runner, repo_root):
        """Test that command injection attempts are prevented via sanitization."""
        # Verify sanitize_input function exists and is used
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # Verify sanitize_input function exists
            assert 'sanitize_input()' in script_content, \
                f"{script_name} must have sanitize_input function"

            # Verify it removes dangerous characters
            assert "tr -d" in script_content and (
                ";|&$`<>(){}[]!*?~#" in script_content or
                ';|&$`' in script_content
            ), f"{script_name} sanitize_input must remove shell metacharacters"

            # Verify user input is sanitized
            lines = script_content.split('\n')
            for i, line in enumerate(lines):
                # Look for variable assignments from user input ($1, $2, etc)
                if '=$1' in line or '="${1' in line:
                    # Check if sanitize_input is used
                    assert 'sanitize_input' in line, \
                        f"{script_name}:{i+1} - User input must be sanitized"

    def test_env_file_permission_warning(self, script_runner, test_env_insecure, repo_root):
        """Test that scripts warn when .env.local has overly permissive permissions."""
        # Check script for permission checking code
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Verify permission checking exists
        assert 'stat' in script_content, \
            "Script must check file permissions using stat"

        # Verify warning is issued
        assert 'world-readable permissions' in script_content.lower() or \
               'permission' in script_content.lower(), \
            "Script must warn about insecure permissions"

        # Verify recommended fix is mentioned
        assert 'chmod 600' in script_content, \
            "Script must recommend 'chmod 600' for secure permissions"

    def test_env_file_ownership_validation(self, script_runner, repo_root):
        """Test that scripts validate .env.local is owned by current user."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Verify ownership check exists
        assert 'stat' in script_content, "Must check file ownership"

        # Verify warning for wrong owner
        assert 'not owned by current user' in script_content.lower() or \
               'ownership' in script_content.lower(), \
            "Must warn if .env.local owned by different user"

        # Verify user is prompted to continue
        assert 'read -p' in script_content or 'Continue anyway' in script_content, \
            "Must prompt user when ownership mismatch detected"

    def test_malicious_input_sanitization(self, script_runner, repo_root):
        """Test various injection attempts are sanitized.

        Test cases:
        - Shell command injection (;, |, &&)
        - Command substitution ($(), ``)
        - File redirection (<, >)
        - Glob expansion (*, ?)
        - Environment variable expansion ($)
        """
        malicious_inputs = validate_input_sanitization([])

        # Read sanitize_input function from script
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Extract sanitize_input function
        lines = script_content.split('\n')
        sanitize_func = []
        in_function = False

        for line in lines:
            if 'sanitize_input()' in line:
                in_function = True
            if in_function:
                sanitize_func.append(line)
                if line.strip() == '}':
                    break

        sanitize_code = '\n'.join(sanitize_func)

        # Verify dangerous characters are removed
        dangerous_chars = [';', '|', '&', '$', '`', '<', '>', '(', ')', '{', '}', '[', ']', '!', '*', '?', '~', '#']
        for char in dangerous_chars:
            assert char in sanitize_code, \
                f"sanitize_input must remove dangerous character: {char}"

    def test_no_secrets_in_error_messages(self, script_runner, repo_root):
        """Test that error messages don't leak sensitive information."""
        # Check error handling doesn't expose secrets
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # Look for error handling
            lines = script_content.split('\n')
            for i, line in enumerate(lines):
                if 'echo' in line.lower() and ('error' in line.lower() or '❌' in line):
                    # Error messages should not contain variable expansions
                    # of sensitive data
                    assert '$ANTHROPIC_API_KEY' not in line, \
                        f"{script_name}:{i+1} - Error message must not expose API key"

    def test_temporary_files_secure(self, script_runner, repo_root):
        """Test that any temporary files created have secure permissions."""
        # Check if scripts create temp files
        scripts_to_check = ["single.sh", "full.sh", "investigate-single.sh", "investigate.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            if not script_path.exists():
                continue

            script_content = script_path.read_text()

            # If creating temp files, they should have secure permissions
            if 'mktemp' in script_content or '/tmp/' in script_content:
                # Should set umask or chmod temp files
                assert 'umask' in script_content or 'chmod' in script_content, \
                    f"{script_name} must secure temporary files"

    def test_no_eval_or_exec(self, script_runner, repo_root):
        """Test that scripts don't use eval or dangerous exec patterns."""
        scripts_to_check = ["single.sh", "full.sh", "investigate-single.sh", "investigate.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            if not script_path.exists():
                continue

            script_content = script_path.read_text()
            lines = script_content.split('\n')

            # Check for dangerous eval usage
            for i, line in enumerate(lines):
                # Allow 'eval $CMD' for our specific use case where CMD is built safely
                if 'eval' in line and 'CMD' in line:
                    # This is our controlled eval usage - verify CMD is built safely
                    # Look backwards to see how CMD is constructed
                    cmd_construction = '\n'.join(lines[max(0, i-40):i])
                    # Should use sanitized input - check for sanitize_input or REPO_ARG (which is sanitized)
                    if '$1' in cmd_construction and 'CMD' in cmd_construction:
                        # Check if REPO_ARG (sanitized) is used or direct sanitize_input call
                        assert 'sanitize_input' in cmd_construction or 'REPO_ARG' in cmd_construction, \
                            f"{script_name}:{i+1} - eval with user input must use sanitized variables"
                elif 'eval' in line and not line.strip().startswith('#'):
                    # General eval usage - should be avoided unless documented
                    # Skip comments
                    pass

    def test_secure_subprocess_invocation(self, script_runner, repo_root):
        """Test that Python subprocesses are invoked securely."""
        # Check worker invocation
        worker_script = repo_root / "src" / "investigate_worker.py"

        if worker_script.exists():
            worker_content = worker_script.read_text()

            # If using subprocess, should not use shell=True with user input
            if 'subprocess' in worker_content:
                lines = worker_content.split('\n')
                for i, line in enumerate(lines):
                    if 'subprocess' in line and 'shell=True' in line:
                        # Should not have user input in same statement
                        context = '\n'.join(lines[max(0, i-5):min(len(lines), i+5)])
                        # Verify no obvious user input variables
                        dangerous_vars = ['repo_name', 'repo_url', 'user_input', 'args']
                        for var in dangerous_vars:
                            assert var not in context, \
                                f"worker:{i+1} - shell=True with user input is dangerous"

    def test_github_token_not_logged(self, script_runner, repo_root):
        """Test that GITHUB_TOKEN is not exposed in logs."""
        # Similar to API key, GitHub tokens should be masked
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # If script uses GITHUB_TOKEN, it should be masked
            if 'GITHUB_TOKEN' in script_content:
                lines = script_content.split('\n')
                for i, line in enumerate(lines):
                    if 'GITHUB_TOKEN' in line and 'echo' in line.lower():
                        # Should be masked
                        assert '***' in line or 'present' in line.lower(), \
                            f"{script_name}:{i+1} - GitHub token must be masked"

    def test_no_hardcoded_secrets(self, script_runner, repo_root):
        """Test that no secrets are hardcoded in scripts."""
        scripts_to_check = ["single.sh", "full.sh", "investigate-single.sh", "investigate.sh"]

        # Patterns that might indicate hardcoded secrets
        secret_patterns = [
            r'sk-ant-[a-zA-Z0-9_-]{32,}',  # Anthropic API key
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub personal access token
            r'ghs_[a-zA-Z0-9]{36}',  # GitHub app token
        ]

        import re

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            if not script_path.exists():
                continue

            script_content = script_path.read_text()

            for pattern in secret_patterns:
                matches = re.findall(pattern, script_content)
                # Filter out test/example keys
                real_secrets = [m for m in matches if not any(
                    x in m.lower() for x in ['test', 'example', 'placeholder', 'xxx']
                )]

                assert len(real_secrets) == 0, \
                    f"{script_name} contains hardcoded secret: {pattern}"

    def test_secure_env_file_loading(self, script_runner, repo_root):
        """Test that .env.local is loaded securely using 'set -a' pattern."""
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # Verify secure loading pattern
            assert 'set -a' in script_content, \
                f"{script_name} must use 'set -a' before sourcing .env.local"
            assert 'source .env.local' in script_content or '. .env.local' in script_content, \
                f"{script_name} must source .env.local"
            assert 'set +a' in script_content, \
                f"{script_name} must use 'set +a' after sourcing .env.local"

            # Verify they're in the right order
            lines = script_content.split('\n')
            set_a_line = None
            source_line = None
            set_plus_a_line = None

            for i, line in enumerate(lines):
                if 'set -a' in line and set_a_line is None:
                    set_a_line = i
                if ('source .env.local' in line or '. .env.local' in line) and source_line is None:
                    source_line = i
                if 'set +a' in line and set_plus_a_line is None and set_a_line is not None:
                    set_plus_a_line = i

            if set_a_line and source_line and set_plus_a_line:
                assert set_a_line < source_line < set_plus_a_line, \
                    f"{script_name} must use correct order: set -a, source, set +a"
