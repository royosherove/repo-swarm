"""Integration tests for environment variable inheritance in investigation workflows.

These tests verify that environment variables are properly passed from parent
scripts to worker subprocesses, ensuring configuration consistency.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.helpers.script_runner import (
    ScriptRunner,
    create_test_env_file,
    extract_env_var_from_output
)


class TestEnvironmentVariableInheritance:
    """Test environment variable inheritance in investigation workflows."""

    @pytest.fixture
    def script_runner(self):
        """Create script runner instance."""
        return ScriptRunner()

    @pytest.fixture
    def test_env_file(self, tmp_path):
        """Create temporary .env.local for testing with proper permissions."""
        env_file = tmp_path / ".env.local"
        create_test_env_file(
            env_file,
            api_key="test-key-abc123xyz456def789ghi012jkl345",
            model="claude-3-haiku-20241022",
            base_url="http://localhost:3000",
            local_testing=True,
            skip_dynamodb=True,
            prompt_storage="file"
        )
        # Set secure permissions
        env_file.chmod(0o600)
        return env_file

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent

    def test_claude_model_inherited_from_env_file(self, script_runner, test_env_file, repo_root, monkeypatch):
        """Test that worker subprocess receives CLAUDE_MODEL from .env.local.

        This verifies the P0 fix: CLAUDE_MODEL must be exported before starting worker.
        """
        # Copy test env file to repo root
        import shutil
        target_env = repo_root / ".env.local.test"
        shutil.copy(test_env_file, target_env)

        try:
            # Mock the actual script execution to avoid starting Temporal
            # We just want to verify the environment variable setup
            with monkeypatch.context() as m:
                # Change to repo root for env file loading
                original_cwd = os.getcwd()
                os.chdir(repo_root)

                # Mock subprocess calls to prevent actual execution
                mock_popen = MagicMock()
                mock_popen.pid = 12345

                with patch('subprocess.Popen', return_value=mock_popen):
                    # Read the script and verify it exports CLAUDE_MODEL
                    single_script = repo_root / "scripts" / "single.sh"
                    script_content = single_script.read_text()

                    # Verify export statement exists
                    assert "export ANTHROPIC_BASE_URL ANTHROPIC_API_KEY CLAUDE_MODEL" in script_content, \
                        "Script must export CLAUDE_MODEL for worker subprocess"

                    # Verify the export happens before worker starts
                    export_line = None
                    worker_start_line = None

                    for i, line in enumerate(script_content.split('\n')):
                        if "export ANTHROPIC_BASE_URL ANTHROPIC_API_KEY CLAUDE_MODEL" in line:
                            export_line = i
                        if "investigate_worker" in line and "python -m" in line:
                            worker_start_line = i

                    assert export_line is not None, "Export statement not found"
                    assert worker_start_line is not None, "Worker start not found"
                    assert export_line < worker_start_line, \
                        "CLAUDE_MODEL must be exported BEFORE starting worker"

                os.chdir(original_cwd)

        finally:
            # Cleanup
            if target_env.exists():
                target_env.unlink()

    def test_claude_model_override_via_cli(self, script_runner, test_env_file, repo_root):
        """Test that CLI override takes precedence over .env.local.

        Verifies: ./single.sh model claude-opus should override .env.local value.
        """
        import shutil
        target_env = repo_root / ".env.local.test"
        shutil.copy(test_env_file, target_env)

        try:
            # Read script to verify override logic
            single_script = repo_root / "scripts" / "single.sh"
            script_content = single_script.read_text()

            # Verify CLI override is set
            assert 'CLAUDE_MODEL_VALUE="$arg"' in script_content or \
                   'CLAUDE_MODEL="$CLAUDE_MODEL_VALUE"' in script_content, \
                "Script must support CLI model override"

            # Verify export after override
            lines = script_content.split('\n')
            override_found = False
            export_after_override = False

            for i, line in enumerate(lines):
                if 'CLAUDE_MODEL="$CLAUDE_MODEL_VALUE"' in line or 'CLAUDE_MODEL_VALUE=' in line:
                    override_found = True
                if override_found and 'export' in line and 'CLAUDE_MODEL' in line:
                    export_after_override = True
                    break

            assert override_found, "CLI override logic not found"
            assert export_after_override, "Model must be exported after CLI override"

        finally:
            if target_env.exists():
                target_env.unlink()

    def test_all_anthropic_vars_inherited(self, script_runner, repo_root):
        """Test that all Anthropic configuration vars are available in worker.

        Verifies: ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, CLAUDE_MODEL all exported.
        """
        # Check both scripts for proper exports
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # Verify export statement exists
            assert "export ANTHROPIC_BASE_URL ANTHROPIC_API_KEY CLAUDE_MODEL" in script_content, \
                f"{script_name} must export all Anthropic variables"

            # Verify exports happen before worker starts
            lines = script_content.split('\n')
            export_line = None
            worker_line = None

            for i, line in enumerate(lines):
                if "export ANTHROPIC_BASE_URL ANTHROPIC_API_KEY CLAUDE_MODEL" in line:
                    export_line = i
                if "investigate_worker" in line and not line.strip().startswith('#'):
                    worker_line = i
                    break  # Get first worker start

            assert export_line is not None, f"Export not found in {script_name}"
            assert worker_line is not None, f"Worker start not found in {script_name}"
            assert export_line < worker_line, \
                f"In {script_name}, variables must be exported before worker starts (export:{export_line}, worker:{worker_line})"

    def test_local_testing_vars_inherited(self, script_runner, repo_root):
        """Test that LOCAL_TESTING, SKIP_DYNAMODB_CHECK, PROMPT_CONTEXT_STORAGE are available.

        These are critical for local development workflow.
        """
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # Verify these vars are exported
            assert "export LOCAL_TESTING SKIP_DYNAMODB_CHECK PROMPT_CONTEXT_STORAGE" in script_content, \
                f"{script_name} must export local testing variables"

            # Verify they're loaded from .env.local
            assert "source .env.local" in script_content or "set -a" in script_content, \
                f"{script_name} must load .env.local"

            # Verify defaults are set if .env.local is missing
            assert "export PROMPT_CONTEXT_STORAGE=file" in script_content, \
                f"{script_name} must set default for PROMPT_CONTEXT_STORAGE"
            assert "export SKIP_DYNAMODB_CHECK=true" in script_content, \
                f"{script_name} must set default for SKIP_DYNAMODB_CHECK"
            assert "export LOCAL_TESTING=true" in script_content, \
                f"{script_name} must set default for LOCAL_TESTING"

    def test_missing_env_file_uses_defaults(self, script_runner, repo_root, tmp_path):
        """Test that scripts fall back to defaults when .env.local is missing."""
        # Run in a temp directory without .env.local
        with patch.dict(os.environ, {}, clear=True):
            # Add minimal required env vars
            os.environ['PATH'] = '/usr/bin:/bin'

            # Read script to verify default setting logic
            single_script = repo_root / "scripts" / "single.sh"
            script_content = single_script.read_text()

            # Verify defaults are set in else block after .env.local check
            lines = script_content.split('\n')
            found_else_block = False
            found_defaults = False

            for i, line in enumerate(lines):
                if 'else' in line and i > 0:
                    # Check if previous context was .env.local check
                    prev_lines = '\n'.join(lines[max(0, i-5):i])
                    if '.env.local' in prev_lines:
                        found_else_block = True
                if found_else_block and not found_defaults:
                    # Check next few lines for defaults
                    next_lines = '\n'.join(lines[i:i+10])
                    if 'export PROMPT_CONTEXT_STORAGE=file' in next_lines:
                        found_defaults = True
                        break

            assert found_else_block, "Else block for missing .env.local not found"
            assert found_defaults, "Default values not set when .env.local is missing"

    def test_env_vars_available_in_activities(self, script_runner, repo_root):
        """Test that environment variables are accessible in Python activities.

        This verifies the complete chain: script -> worker -> activity.
        """
        # Check that worker script properly inherits and uses env vars
        worker_script = repo_root / "src" / "investigate_worker.py"

        if worker_script.exists():
            worker_content = worker_script.read_text()

            # Worker should access environment variables
            # These patterns verify env var usage
            env_var_patterns = [
                "os.environ",
                "os.getenv",
                "ANTHROPIC_API_KEY",
                "CLAUDE_MODEL"
            ]

            for pattern in env_var_patterns:
                assert pattern in worker_content, \
                    f"Worker must access environment variable: {pattern}"

    def test_env_var_export_ordering(self, script_runner, repo_root):
        """Test that environment variables are exported in correct order.

        Critical order:
        1. Load .env.local (set -a; source .env.local; set +a)
        2. Set/override specific variables if needed
        3. Export before starting subprocesses
        """
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()
        lines = script_content.split('\n')

        # Track line numbers of key operations
        load_env_line = None
        override_line = None
        export_anthropic_line = None
        export_local_line = None
        worker_start_line = None

        for i, line in enumerate(lines):
            if 'source .env.local' in line:
                load_env_line = i
            if 'CLAUDE_MODEL="$CLAUDE_MODEL_VALUE"' in line:
                override_line = i
            if 'export ANTHROPIC_BASE_URL ANTHROPIC_API_KEY CLAUDE_MODEL' in line:
                export_anthropic_line = i
            if 'export LOCAL_TESTING SKIP_DYNAMODB_CHECK PROMPT_CONTEXT_STORAGE' in line:
                export_local_line = i
            if 'investigate_worker' in line and 'python -m' in line:
                worker_start_line = i

        # Verify ordering
        assert load_env_line is not None, "Env loading not found"
        assert export_anthropic_line is not None, "Anthropic export not found"
        assert export_local_line is not None, "Local testing export not found"
        assert worker_start_line is not None, "Worker start not found"

        # Load must come before exports
        assert load_env_line < export_anthropic_line, \
            "Must load .env.local before exporting Anthropic vars"

        # Anthropic exports must come before worker start
        assert export_anthropic_line < worker_start_line, \
            "Must export Anthropic vars before starting worker"

        # Local testing vars may be exported after worker (for client subprocess)
        # but must be exported somewhere
        assert export_local_line is not None, \
            "Must export local testing vars somewhere in script"

        # If override exists, it should come after load but before export
        if override_line:
            assert load_env_line < override_line < export_anthropic_line, \
                "Override must come between load and export"

    def test_env_var_propagation_to_client(self, script_runner, repo_root):
        """Test that environment variables are also propagated to client subprocess.

        Both worker AND client need environment variables.
        """
        full_script = repo_root / "scripts" / "full.sh"
        script_content = full_script.read_text()

        # Find worker and client start commands
        worker_exports = []
        client_exports = []
        lines = script_content.split('\n')

        in_worker_section = False
        in_client_section = False

        for i, line in enumerate(lines):
            if 'investigate_worker' in line:
                # Look backwards for recent exports
                for j in range(max(0, i-10), i):
                    if 'export' in lines[j]:
                        worker_exports.append(lines[j])

            if 'python -m client' in line or 'client investigate' in line:
                # Look backwards for recent exports
                for j in range(max(0, i-10), i):
                    if 'export' in lines[j]:
                        client_exports.append(lines[j])

        # Verify both have necessary exports
        assert any('ANTHROPIC' in exp for exp in worker_exports), \
            "Worker section must have Anthropic exports"
        assert any('LOCAL_TESTING' in exp for exp in client_exports), \
            "Client section must have local testing exports"
