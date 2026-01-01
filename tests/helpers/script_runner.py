"""Helper utilities for running bash scripts and capturing output in tests."""

import subprocess
import os
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ScriptResult:
    """Result of a script execution."""
    returncode: int
    stdout: str
    stderr: str
    duration: float
    env_vars: Dict[str, str]


class ScriptRunner:
    """Helper class for running bash scripts in tests."""

    def __init__(self, scripts_dir: Path = None):
        """Initialize script runner.

        Args:
            scripts_dir: Directory containing scripts (defaults to repo root/scripts)
        """
        if scripts_dir is None:
            # Default to scripts directory in repo root
            repo_root = Path(__file__).parent.parent.parent
            scripts_dir = repo_root / "scripts"
        self.scripts_dir = scripts_dir

    def run_script(
        self,
        script_name: str,
        args: List[str] = None,
        env_vars: Dict[str, str] = None,
        timeout: int = 30,
        input_text: str = None,
        cwd: Path = None
    ) -> ScriptResult:
        """Run a bash script and capture output.

        Args:
            script_name: Name of the script file (e.g., "single.sh")
            args: List of arguments to pass to script
            env_vars: Environment variables to set (merged with current env)
            timeout: Timeout in seconds
            input_text: Text to send to stdin
            cwd: Working directory (defaults to repo root)

        Returns:
            ScriptResult with execution details
        """
        if args is None:
            args = []

        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Default working directory to repo root
        if cwd is None:
            cwd = self.scripts_dir.parent

        # Build command
        cmd = ["bash", str(script_path)] + args

        # Run script
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                input=input_text
            )
            duration = time.time() - start_time

            return ScriptResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
                env_vars=env_vars or {}
            )
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return ScriptResult(
                returncode=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                duration=duration,
                env_vars=env_vars or {}
            )

    def run_script_background(
        self,
        script_name: str,
        args: List[str] = None,
        env_vars: Dict[str, str] = None,
        cwd: Path = None
    ) -> subprocess.Popen:
        """Run a bash script in background.

        Args:
            script_name: Name of the script file
            args: List of arguments to pass to script
            env_vars: Environment variables to set
            cwd: Working directory

        Returns:
            Popen process object
        """
        if args is None:
            args = []

        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Default working directory to repo root
        if cwd is None:
            cwd = self.scripts_dir.parent

        # Build command
        cmd = ["bash", str(script_path)] + args

        # Run in background
        process = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return process

    def send_signal(self, process: subprocess.Popen, sig: signal.Signals) -> None:
        """Send signal to a running process.

        Args:
            process: Popen process object
            sig: Signal to send (e.g., signal.SIGINT, signal.SIGTERM)
        """
        process.send_signal(sig)

    def wait_for_output(
        self,
        process: subprocess.Popen,
        pattern: str,
        timeout: int = 10
    ) -> bool:
        """Wait for specific pattern in process output.

        Args:
            process: Popen process object
            pattern: String pattern to search for
            timeout: Timeout in seconds

        Returns:
            True if pattern found, False if timeout
        """
        start_time = time.time()
        output_buffer = ""

        while time.time() - start_time < timeout:
            # Read available output
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    output_buffer += line
                    if pattern in output_buffer:
                        return True

            # Check if process has exited
            if process.poll() is not None:
                return pattern in output_buffer

            time.sleep(0.1)

        return False

    def get_process_output(self, process: subprocess.Popen, timeout: int = 5) -> Tuple[str, str]:
        """Get stdout and stderr from a process.

        Args:
            process: Popen process object
            timeout: Timeout in seconds

        Returns:
            Tuple of (stdout, stderr)
        """
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return stdout, stderr
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return stdout, stderr


def create_test_env_file(
    path: Path,
    api_key: str = "test-api-key-12345",
    model: str = "claude-3-haiku-20241022",
    base_url: str = "http://localhost:3000",
    local_testing: bool = True,
    skip_dynamodb: bool = True,
    prompt_storage: str = "file",
    extra_vars: Dict[str, str] = None
) -> Path:
    """Create a test .env.local file with specified configuration.

    Args:
        path: Path where to create the file
        api_key: Anthropic API key value
        model: Claude model name
        base_url: Anthropic base URL
        local_testing: LOCAL_TESTING flag
        skip_dynamodb: SKIP_DYNAMODB_CHECK flag
        prompt_storage: PROMPT_CONTEXT_STORAGE value
        extra_vars: Additional environment variables

    Returns:
        Path to created file
    """
    content = f"""# Test environment configuration
LOCAL_TESTING={str(local_testing).lower()}
SKIP_DYNAMODB_CHECK={str(skip_dynamodb).lower()}
PROMPT_CONTEXT_STORAGE={prompt_storage}

# Temporal configuration
TEMPORAL_SERVER_URL=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=investigate-task-queue

# Claude API configuration
ANTHROPIC_API_KEY={api_key}
ANTHROPIC_BASE_URL={base_url}
CLAUDE_MODEL={model}
"""

    if extra_vars:
        content += "\n# Extra variables\n"
        for key, value in extra_vars.items():
            content += f"{key}={value}\n"

    path.write_text(content)
    return path


def extract_env_var_from_output(output: str, var_name: str) -> Optional[str]:
    """Extract environment variable value from script output.

    Args:
        output: Script stdout/stderr
        var_name: Name of environment variable

    Returns:
        Variable value if found, None otherwise
    """
    # Look for patterns like "VAR_NAME=value" or "VAR_NAME: value"
    import re
    patterns = [
        rf"{var_name}=([^\s]+)",
        rf"{var_name}:\s*([^\s]+)",
        rf"{var_name}\s*=\s*([^\s]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)

    return None


def check_process_cleanup(initial_pids: set, timeout: int = 5) -> bool:
    """Check if background processes were properly cleaned up.

    Args:
        initial_pids: Set of PIDs that existed before test
        timeout: How long to wait for cleanup

    Returns:
        True if all new processes were cleaned up
    """
    import psutil

    start_time = time.time()
    while time.time() - start_time < timeout:
        current_pids = {p.pid for p in psutil.process_iter(['pid', 'name'])}
        new_pids = current_pids - initial_pids

        # Filter out test-related processes
        orphaned = False
        for pid in new_pids:
            try:
                proc = psutil.Process(pid)
                cmdline = ' '.join(proc.cmdline())
                # Check if it's a Temporal or worker process
                if 'temporal' in cmdline.lower() or 'investigate_worker' in cmdline:
                    orphaned = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not orphaned:
            return True

        time.sleep(0.5)

    return False
