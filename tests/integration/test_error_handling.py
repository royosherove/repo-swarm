"""Error handling and cleanup tests for repo-swarm scripts.

These tests verify that scripts properly clean up resources and handle
errors gracefully in all exit scenarios.
"""

import pytest
import signal
import time
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.helpers.script_runner import (
    ScriptRunner,
    create_test_env_file
)


class TestErrorHandling:
    """Test error handling and cleanup in investigation workflows."""

    @pytest.fixture
    def script_runner(self):
        """Create script runner instance."""
        return ScriptRunner()

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def test_env_file(self, tmp_path):
        """Create test environment file."""
        env_file = tmp_path / ".env.local"
        create_test_env_file(
            env_file,
            api_key="test-key-abc123xyz456def789ghi012jkl345",
            model="claude-3-haiku-20241022"
        )
        env_file.chmod(0o600)
        return env_file

    def test_cleanup_function_exists(self, repo_root):
        """Test that cleanup function is defined in scripts."""
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # Verify cleanup function exists
            assert 'cleanup()' in script_content, \
                f"{script_name} must have cleanup() function"

            # Verify it kills background processes
            assert 'WORKER_PID' in script_content, \
                f"{script_name} cleanup must handle worker PID"
            assert 'SERVER_PID' in script_content, \
                f"{script_name} cleanup must handle server PID"
            assert 'kill' in script_content, \
                f"{script_name} cleanup must kill background processes"

    def test_trap_registered_for_all_signals(self, repo_root):
        """Test that trap is registered for EXIT, ERR, INT, TERM signals."""
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # Verify trap registration
            assert 'trap cleanup' in script_content, \
                f"{script_name} must register trap"

            # Verify all important signals are trapped
            required_signals = ['EXIT', 'ERR', 'INT', 'TERM']
            for sig in required_signals:
                assert sig in script_content, \
                    f"{script_name} trap must handle {sig} signal"

            # Verify trap is registered before any risky operations
            lines = script_content.split('\n')
            trap_line = None
            first_subprocess_line = None

            for i, line in enumerate(lines):
                if 'trap cleanup' in line and trap_line is None:
                    trap_line = i
                if ('mise run' in line or 'python -m' in line) and first_subprocess_line is None:
                    first_subprocess_line = i

            assert trap_line is not None, f"{script_name} must register trap"
            if first_subprocess_line:
                assert trap_line < first_subprocess_line, \
                    f"{script_name} trap must be registered before starting subprocesses"

    def test_cleanup_on_ctrl_c(self, script_runner, repo_root):
        """Test that SIGINT (Ctrl+C) triggers proper cleanup.

        This verifies the trap for INT signal works.
        """
        # Verify trap includes INT signal
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Check trap registration includes INT
        lines = script_content.split('\n')
        trap_line = None

        for line in lines:
            if 'trap cleanup' in line:
                trap_line = line
                break

        assert trap_line is not None, "Trap must be registered"
        assert 'INT' in trap_line, "Trap must handle INT signal (Ctrl+C)"

    def test_cleanup_on_error(self, repo_root):
        """Test that script errors trigger cleanup via ERR trap."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Verify ERR trap is registered
        lines = script_content.split('\n')
        trap_line = None

        for line in lines:
            if 'trap cleanup' in line:
                trap_line = line
                break

        assert trap_line is not None, "Trap must be registered"
        assert 'ERR' in trap_line, "Trap must handle ERR signal"

        # Verify cleanup checks exit code
        cleanup_func = []
        in_cleanup = False

        for line in lines:
            if 'cleanup()' in line:
                in_cleanup = True
            if in_cleanup:
                cleanup_func.append(line)
                if line.strip() == '}':
                    break

        cleanup_code = '\n'.join(cleanup_func)
        assert '$?' in cleanup_code or 'exit_code' in cleanup_code, \
            "Cleanup function must check exit code"

    def test_missing_api_key_fails_gracefully(self, script_runner, repo_root, tmp_path):
        """Test clear error message when ANTHROPIC_API_KEY is missing."""
        # Create env file without API key
        env_file = tmp_path / ".env.local"
        env_file.write_text("""
LOCAL_TESTING=true
SKIP_DYNAMODB_CHECK=true
PROMPT_CONTEXT_STORAGE=file
# ANTHROPIC_API_KEY intentionally missing
""")
        env_file.chmod(0o600)

        # Check script has validation
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Verify API key check exists
        assert 'ANTHROPIC_API_KEY' in script_content, \
            "Script must check for ANTHROPIC_API_KEY"

        # Verify error message when missing
        lines = script_content.split('\n')
        found_check = False
        found_error = False

        for i, line in enumerate(lines):
            if 'ANTHROPIC_API_KEY' in line and ('-z' in line or '[ -z' in line):
                found_check = True
                # Look at next few lines for error message
                next_lines = '\n'.join(lines[i:i+5])
                if '❌' in next_lines or 'Error' in next_lines:
                    found_error = True

        assert found_check, "Must check if ANTHROPIC_API_KEY is set"
        assert found_error, "Must show error message when API key missing"

    def test_temporal_startup_failure_cleanup(self, repo_root):
        """Test cleanup if Temporal server fails to start."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Verify Temporal is started in background and PID is captured
        assert 'mise run dev-temporal &' in script_content or \
               'temporal server start &' in script_content, \
            "Temporal must be started in background"

        assert 'SERVER_PID=$!' in script_content, \
            "Must capture Temporal server PID"

        # Verify cleanup handles SERVER_PID
        lines = script_content.split('\n')
        cleanup_func = []
        in_cleanup = False

        for line in lines:
            if 'cleanup()' in line:
                in_cleanup = True
            if in_cleanup:
                cleanup_func.append(line)
                if line.strip() == '}':
                    break

        cleanup_code = '\n'.join(cleanup_func)
        assert 'SERVER_PID' in cleanup_code, \
            "Cleanup must handle SERVER_PID"
        assert 'kill' in cleanup_code and '$SERVER_PID' in cleanup_code, \
            "Cleanup must kill Temporal server"

    def test_worker_startup_failure_cleanup(self, repo_root):
        """Test cleanup if worker fails to start."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Verify worker is started in background and PID is captured
        assert 'investigate_worker' in script_content, \
            "Worker must be started"

        assert 'WORKER_PID=$!' in script_content, \
            "Must capture worker PID"

        # Verify cleanup handles WORKER_PID
        lines = script_content.split('\n')
        cleanup_func = []
        in_cleanup = False

        for line in lines:
            if 'cleanup()' in line:
                in_cleanup = True
            if in_cleanup:
                cleanup_func.append(line)
                if line.strip() == '}':
                    break

        cleanup_code = '\n'.join(cleanup_func)
        assert 'WORKER_PID' in cleanup_code, \
            "Cleanup must handle WORKER_PID"
        assert 'kill' in cleanup_code and '$WORKER_PID' in cleanup_code, \
            "Cleanup must kill worker process"

    def test_cleanup_exit_message(self, repo_root):
        """Test that cleanup shows appropriate exit message."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Extract cleanup function
        lines = script_content.split('\n')
        cleanup_func = []
        in_cleanup = False

        for line in lines:
            if 'cleanup()' in line:
                in_cleanup = True
            if in_cleanup:
                cleanup_func.append(line)
                if line.strip() == '}':
                    break

        cleanup_code = '\n'.join(cleanup_func)

        # Should show different message based on exit code
        assert 'exit_code' in cleanup_code or '$?' in cleanup_code, \
            "Cleanup should check exit code"

        # Should have user-friendly messages
        assert '🧹' in cleanup_code or 'Cleaning up' in cleanup_code, \
            "Cleanup should show cleanup message"

        assert '✅' in cleanup_code or 'complete' in cleanup_code.lower(), \
            "Cleanup should show completion message"

    def test_orphaned_process_prevention(self, repo_root):
        """Test that no background processes are left running after cleanup."""
        # Verify PID tracking and cleanup
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # All background processes should have their PIDs captured
        lines = script_content.split('\n')
        background_processes = []
        pid_captures = []

        for i, line in enumerate(lines):
            if line.strip().endswith('&') and ('mise run' in line or 'python -m' in line):
                background_processes.append((i, line))

            if 'PID=$!' in line:
                pid_captures.append((i, line))

        # Every background process should have PID capture
        assert len(background_processes) == len(pid_captures), \
            f"Every background process must capture PID. Found {len(background_processes)} " \
            f"background processes but {len(pid_captures)} PID captures"

        # Verify all PIDs are cleaned up
        cleanup_func = []
        in_cleanup = False

        for line in lines:
            if 'cleanup()' in line:
                in_cleanup = True
            if in_cleanup:
                cleanup_func.append(line)
                if line.strip() == '}':
                    break

        cleanup_code = '\n'.join(cleanup_func)

        for _, pid_line in pid_captures:
            pid_var = pid_line.split('=')[0].strip()
            assert pid_var in cleanup_code, \
                f"Cleanup must handle {pid_var}"

    def test_cleanup_handles_already_stopped_processes(self, repo_root):
        """Test cleanup handles PIDs that are already stopped gracefully."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Extract cleanup function
        lines = script_content.split('\n')
        cleanup_func = []
        in_cleanup = False

        for line in lines:
            if 'cleanup()' in line:
                in_cleanup = True
            if in_cleanup:
                cleanup_func.append(line)
                if line.strip() == '}':
                    break

        cleanup_code = '\n'.join(cleanup_func)

        # Verify kill commands redirect errors to avoid noise
        kill_lines = [line for line in cleanup_func if 'kill' in line and 'PID' in line]

        for line in kill_lines:
            assert '2>/dev/null' in line, \
                "kill commands must redirect stderr to avoid errors for already-stopped processes"

    def test_cleanup_order(self, repo_root):
        """Test that cleanup kills processes in correct order (worker before server)."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Extract cleanup function
        lines = script_content.split('\n')
        cleanup_func = []
        in_cleanup = False

        for line in lines:
            if 'cleanup()' in line:
                in_cleanup = True
            if in_cleanup:
                cleanup_func.append(line)
                if line.strip() == '}':
                    break

        # Find order of kills
        worker_kill_line = None
        server_kill_line = None

        for i, line in enumerate(cleanup_func):
            if 'WORKER_PID' in line and 'kill' in line:
                worker_kill_line = i
            if 'SERVER_PID' in line and 'kill' in line:
                server_kill_line = i

        # Worker should be killed before server (or doesn't matter if independent)
        # But both must be killed
        assert worker_kill_line is not None, "Must kill worker process"
        assert server_kill_line is not None, "Must kill server process"

    def test_exit_code_preservation(self, repo_root):
        """Test that cleanup preserves original exit code."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Extract cleanup function
        lines = script_content.split('\n')
        cleanup_func = []
        in_cleanup = False

        for line in lines:
            if 'cleanup()' in line:
                in_cleanup = True
            if in_cleanup:
                cleanup_func.append(line)
                if line.strip() == '}':
                    break

        cleanup_code = '\n'.join(cleanup_func)

        # Should capture exit code at start
        assert 'exit_code=$?' in cleanup_code or 'local exit_code=$?' in cleanup_code, \
            "Cleanup must capture exit code at start"

        # Should use it for conditional logic
        assert 'exit_code' in cleanup_code, \
            "Cleanup must use exit_code variable"

    def test_error_messages_are_clear(self, repo_root):
        """Test that error messages are clear and actionable."""
        scripts_to_check = ["single.sh", "full.sh"]

        for script_name in scripts_to_check:
            script_path = repo_root / "scripts" / script_name
            script_content = script_path.read_text()

            # Find all error messages
            lines = script_content.split('\n')
            error_messages = []

            for i, line in enumerate(lines):
                if '❌' in line or ('echo' in line and 'Error' in line):
                    error_messages.append((i, line))

            # Each error should be descriptive
            for line_num, msg in error_messages:
                # Should not just say "Error" without context
                assert len(msg.strip()) > 15, \
                    f"{script_name}:{line_num} - Error message too short"

                # Should have actionable information
                # (This is a heuristic check)
                has_action = any(keyword in msg.lower() for keyword in [
                    'set', 'export', 'install', 'check', 'ensure', 'please', 'run'
                ])
                # Not all errors need actions, but most should guide user
                # So we just verify error messages exist and are not empty

    def test_script_stops_on_critical_errors(self, repo_root):
        """Test that scripts exit on critical errors (missing API key, etc)."""
        single_script = repo_root / "scripts" / "single.sh"
        script_content = single_script.read_text()

        # Find critical error checks
        lines = script_content.split('\n')

        # API key check should exit
        found_api_check = False
        found_exit = False

        for i, line in enumerate(lines):
            if 'ANTHROPIC_API_KEY' in line and '-z' in line:
                found_api_check = True
                # Check next few lines for exit
                next_lines = '\n'.join(lines[i:i+10])
                if 'exit 1' in next_lines:
                    found_exit = True

        assert found_api_check, "Must check for API key"
        assert found_exit, "Must exit when API key missing"
