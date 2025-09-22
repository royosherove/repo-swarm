#!/usr/bin/env python3
"""
Configuration verification script for RepoSwarm.

This script validates all configuration values from config.py and tests
repository access using git_manager.py when possible.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Any
import requests

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from investigator.core.config import Config
from investigator.core.git_manager import GitRepositoryManager

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

class ConfigVerifier:
    """Verifies RepoSwarm configuration and tests repository access."""

    def __init__(self):
        self.config = Config
        self.git_manager = None
        self.console = Console() if RICH_AVAILABLE else None
        self.errors = []
        self.warnings = []
        self.successes = []

    def verify(self):
        """Run all verification checks."""
        self._print_header()

        # Initialize git manager if we have a token
        self._initialize_git_manager()

        # Run all verification checks
        self._run_verification_checks()

        # Test repository access if possible
        self._test_repository_access()

        # Test architecture hub specifically
        self._test_architecture_hub_access()

        # Print summary
        self._print_summary()

        return len(self.errors) == 0

    def _print_header(self):
        """Print the verification header."""
        if self.console:
            self.console.print(Panel.fit("🔍 REPOSWARM CONFIGURATION VERIFICATION",
                                       style="bold blue"))
        else:
            print("🔍 REPOSWARM CONFIGURATION VERIFICATION")
            print("=" * 50)

    def _initialize_git_manager(self):
        """Initialize Git manager if GitHub token is available."""
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            # Create a simple logger for the git manager
            import logging
            logger = logging.getLogger('verify-config-git')
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
                logger.addHandler(handler)

            self.git_manager = GitRepositoryManager(logger)
            self._add_success("GitHub token found and GitRepositoryManager initialized")
        else:
            self._add_warning("No GitHub token found - repository access testing will be limited")

    def _run_verification_checks(self):
        """Run all verification checks."""
        check_functions = [
            self._check_claude_config,
            self._check_file_config,
            self._check_directory_config,
            self._check_repository_config,
            self._check_git_config,
            self._check_workflow_config,
        ]

        for check_func in check_functions:
            check_func()

    # Check functions for different configuration areas
    def _check_claude_config(self):
        """Check Claude API configuration."""
        checks = [
            self._check_claude_model,
            self._check_claude_tokens,
            self._check_claude_api_key,
        ]
        self._run_checks_with_table("🤖 CLAUDE CONFIGURATION", checks)

    def _check_file_config(self):
        """Check file-related configuration."""
        checks = [self._check_analysis_file]
        self._run_checks_with_table("📁 FILE CONFIGURATION", checks)

    def _check_directory_config(self):
        """Check directory-related configuration."""
        checks = [
            self._check_temp_directory,
            self._check_prompts_directory,
        ]
        self._run_checks_with_table("📂 DIRECTORY CONFIGURATION", checks)

    def _check_repository_config(self):
        """Check repository-related configuration."""
        checks = [
            self._check_architecture_hub_url,
            self._check_architecture_hub_web_url,
            self._check_default_org,
            self._check_default_repo,
        ]
        self._run_checks_with_table("🔗 REPOSITORY CONFIGURATION", checks)

    def _check_git_config(self):
        """Check Git configuration."""
        checks = [self._check_git_user_config]
        self._run_checks_with_table("🔧 GIT CONFIGURATION", checks)

    def _check_workflow_config(self):
        """Check workflow configuration."""
        checks = [
            self._check_workflow_chunk_size,
            self._check_workflow_sleep_hours,
        ]
        self._run_checks_with_table("⚙️  WORKFLOW CONFIGURATION", checks)

    def _run_checks_with_table(self, title: str, checks: List):
        """Run a list of checks and display results in a table."""
        results = []
        for check in checks:
            result = check()
            results.append(result)

        self._display_table(title, results)

    def _test_architecture_hub_access(self):
        """Test architecture hub access specifically."""
        if not self.git_manager:
            print("\n🔍 ARCHITECTURE HUB DEBUG")
            print("-" * 30)
            print("⚠️  Cannot test architecture hub access (no GitHub token)")
            return

        print("\n🔍 ARCHITECTURE HUB DEBUG")
        print("-" * 30)

        # Import Config to check the actual values being used
        from investigator.core.config import Config

        # Show what values are being used
        arch_hub_name = os.getenv('ARCH_HUB_REPO_NAME', Config.ARCH_HUB_REPO_NAME)
        arch_hub_base = os.getenv('ARCH_HUB_BASE_URL', Config.ARCH_HUB_BASE_URL)
        arch_hub_files_dir = os.getenv('ARCH_HUB_FILES_DIR', Config.ARCH_HUB_FILES_DIR)

        print(f"Architecture Hub Name: {arch_hub_name}")
        print(f"Architecture Hub Base URL: {arch_hub_base}")
        print(f"Architecture Hub Files Dir: {arch_hub_files_dir}")

        # Show the constructed URL
        constructed_url = Config.get_arch_hub_repo_url()
        print(f"Constructed Repository URL: {constructed_url}")

        web_url = Config.get_arch_hub_web_url()
        print(f"Web URL: {web_url}")

        # Test if the repository exists and is accessible
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            print("❌ No GitHub token available for testing")
            return

        # Check token format
        print(f"GitHub token format check: {github_token[:10]}... (length: {len(github_token)})")
        print(f"Token starts with 'ghp_': {github_token.startswith('ghp_')}")

        try:
            import requests

            # Test API URL instead of web URL
            api_url = f"https://api.github.com/repos{web_url.replace('https://github.com', '')}"
            print(f"API URL: {api_url}")

            # Test API access first
            api_headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'RepoSwarm/1.0'
            }

            print("Testing GitHub API access...")
            api_response = requests.get(api_url, headers=api_headers, timeout=10)

            if api_response.status_code == 200:
                print("✅ GitHub API is accessible")
                try:
                    repo_data = api_response.json()
                    print(f"Repository name: {repo_data.get('name', 'Unknown')}")
                    print(f"Repository owner: {repo_data.get('owner', {}).get('login', 'Unknown')}")
                    print(f"Private: {repo_data.get('private', 'Unknown')}")
                    print(f"Permissions: {repo_data.get('permissions', {})}")
                except Exception as json_e:
                    print(f"❌ Failed to parse API JSON response: {json_e}")
                    print(f"API Response: {api_response.text[:500]}...")
            else:
                print(f"❌ GitHub API not accessible (HTTP {api_response.status_code})")
                print(f"API Response: {api_response.text[:200]}...")

                # Try without token to see if it's a public repo
                print("Testing API access without token (for public repos)...")
                api_response_no_auth = requests.get(api_url, timeout=10)
                if api_response_no_auth.status_code == 200:
                    print("✅ Repository is public and accessible without authentication")
                    try:
                        repo_data = api_response_no_auth.json()
                        print(f"Repository name: {repo_data.get('name', 'Unknown')}")
                        print(f"Repository owner: {repo_data.get('owner', {}).get('login', 'Unknown')}")
                        print(f"Private: {repo_data.get('private', 'Unknown')}")
                    except Exception as json_e:
                        print(f"❌ Failed to parse public API response: {json_e}")
                else:
                    print(f"❌ Repository not accessible even without auth (HTTP {api_response_no_auth.status_code})")

        except Exception as e:
            print(f"❌ Failed to test API: {e}")

        # Test the git URL format
        try:
            print("\nTesting git URL format...")
            git_url = constructed_url
            if not git_url.endswith('.git'):
                git_url += '.git'

            print(f"Git URL to test: {git_url}")

            # Try to access the git repository via HTTP (without auth for basic connectivity)
            test_url = git_url.replace('.git', '') + '/info/refs?service=git-upload-pack'
            print(f"Testing git service: {test_url}")

            # Test without auth first to see if repo is public
            git_response = requests.get(test_url, timeout=10)
            if git_response.status_code == 200:
                print("✅ Git repository is accessible (public repository)")
            elif git_response.status_code == 401:
                print("ℹ️ Repository requires authentication")
                # Test with auth
                git_response = requests.get(test_url, headers=headers, timeout=10)
                if git_response.status_code == 200:
                    print("✅ Git repository is accessible with authentication")
                else:
                    print(f"❌ Git repository not accessible with authentication (HTTP {git_response.status_code})")
                    print(f"Response: {git_response.text[:200]}...")
            else:
                print(f"❌ Git repository not accessible (HTTP {git_response.status_code})")
                print(f"Response: {git_response.text[:200]}...")

        except Exception as e:
            print(f"❌ Failed to test git URL: {e}")

    # Individual check methods - each returns a tuple (status, setting_name, value, details)
    def _check_claude_model(self) -> Tuple[str, str, str, str]:
        """Check Claude model configuration."""
        try:
            claude_model = os.getenv('CLAUDE_MODEL', self.config.CLAUDE_MODEL)
            Config.validate_claude_model(claude_model)
            self._add_success(f"Claude model: {claude_model}")
            return "✅", "Model", claude_model, "Valid"
        except ValueError as e:
            self._add_error(f"Invalid Claude model: {e}")
            return "❌", "Model", str(e), "Invalid"

    def _check_claude_tokens(self) -> Tuple[str, str, str, str]:
        """Check Claude max tokens configuration."""
        try:
            max_tokens = int(os.getenv('MAX_TOKENS', self.config.MAX_TOKENS))
            Config.validate_max_tokens(max_tokens)
            self._add_success(f"Max tokens: {max_tokens}")
            return "✅", "Max Tokens", str(max_tokens), "Valid"
        except ValueError as e:
            self._add_error(f"Invalid max tokens: {e}")
            return "❌", "Max Tokens", str(e), "Invalid"

    def _check_claude_api_key(self) -> Tuple[str, str, str, str]:
        """Check Claude API key presence."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            self._add_success("Anthropic API key found")
            return "✅", "API Key", "***HIDDEN***", "Present"
        else:
            self._add_error("ANTHROPIC_API_KEY not found")
            return "❌", "API Key", "MISSING", "Not set"

    def _check_analysis_file(self) -> Tuple[str, str, str, str]:
        """Check analysis file configuration."""
        analysis_file = self.config.ANALYSIS_FILE
        self._add_success(f"Analysis file: {analysis_file}")
        return "✅", "Analysis File", analysis_file, "Configured"

    def _check_temp_directory(self) -> Tuple[str, str, str, str]:
        """Check temp directory existence."""
        temp_dir = os.path.join(os.getcwd(), self.config.TEMP_DIR)
        if os.path.exists(temp_dir):
            self._add_success(f"Temp directory exists: {temp_dir}")
            return "✅", "Temp Directory", temp_dir, "Exists"
        else:
            self._add_warning(f"Temp directory does not exist: {temp_dir}")
            return "⚠️", "Temp Directory", temp_dir, "Missing"

    def _check_prompts_directory(self) -> Tuple[str, str, str, str]:
        """Check prompts directory existence."""
        prompts_dir = os.path.join(os.getcwd(), self.config.PROMPTS_DIR)
        if os.path.exists(prompts_dir):
            self._add_success(f"Prompts directory exists: {prompts_dir}")
            return "✅", "Prompts Directory", prompts_dir, "Exists"
        else:
            self._add_error(f"Prompts directory does not exist: {prompts_dir}")
            return "❌", "Prompts Directory", prompts_dir, "Missing"

    def _check_architecture_hub_url(self) -> Tuple[str, str, str, str]:
        """Check architecture hub repository URL."""
        arch_hub_url = self.config.get_arch_hub_repo_url()
        self._add_success(f"Architecture Hub URL: {arch_hub_url}")
        return "✅", "Architecture Hub", arch_hub_url, "Configured"

    def _check_architecture_hub_web_url(self) -> Tuple[str, str, str, str]:
        """Check architecture hub web URL."""
        arch_hub_web = self.config.get_arch_hub_web_url()
        self._add_success(f"Architecture Hub Web URL: {arch_hub_web}")
        return "✅", "Architecture Hub Web", arch_hub_web, "Configured"

    def _check_default_org(self) -> Tuple[str, str, str, str]:
        """Check default organization."""
        default_org = os.getenv('DEFAULT_ORG_NAME', self.config.DEFAULT_ORG_NAME)
        self._add_success(f"Default organization: {default_org}")
        return "✅", "Default Organization", default_org, "Configured"

    def _check_default_repo(self) -> Tuple[str, str, str, str]:
        """Check default repository."""
        default_repo = os.getenv('DEFAULT_REPO_URL', self.config.DEFAULT_REPO_URL)
        self._add_success(f"Default repository: {default_repo}")
        return "✅", "Default Repository", default_repo, "Configured"

    def _check_git_user_config(self) -> Tuple[str, str, str, str]:
        """Check Git user configuration."""
        git_user = os.getenv('GIT_USER_NAME', 'Architecture Bot')
        git_email = os.getenv('GIT_USER_EMAIL', 'architecture-bot@your-org.com')
        self._add_success(f"Git user: {git_user} <{git_email}>")
        return "✅", "Git User", f"{git_user} <{git_email}>", "Configured"

    def _check_workflow_chunk_size(self) -> Tuple[str, str, str, str]:
        """Check workflow chunk size configuration."""
        try:
            chunk_size = int(os.getenv('WORKFLOW_CHUNK_SIZE', self.config.WORKFLOW_CHUNK_SIZE))
            Config.validate_chunk_size(chunk_size)
            self._add_success(f"Workflow chunk size: {chunk_size}")
            return "✅", "Chunk Size", str(chunk_size), "Valid"
        except ValueError as e:
            self._add_error(f"Invalid chunk size: {e}")
            return "❌", "Chunk Size", str(e), "Invalid"

    def _check_workflow_sleep_hours(self) -> Tuple[str, str, str, str]:
        """Check workflow sleep hours configuration."""
        try:
            sleep_hours = float(os.getenv('WORKFLOW_SLEEP_HOURS', self.config.WORKFLOW_SLEEP_HOURS))
            Config.validate_sleep_hours(sleep_hours)
            self._add_success(f"Workflow sleep hours: {sleep_hours}")
            return "✅", "Sleep Hours", str(sleep_hours), "Valid"
        except ValueError as e:
            self._add_error(f"Invalid sleep hours: {e}")
            return "❌", "Sleep Hours", str(e), "Invalid"

    def _test_repository_access(self):
        """Test repository access using git_manager."""
        if not self.git_manager:
            results = [("⚠️", "Repository Tests", "SKIPPED", "No GitHub token")]
            self._display_table("🔐 REPOSITORY ACCESS TEST", results)
            return

        # Test GitHub token
        token_result = self.git_manager.validate_github_token()
        if token_result['status'] == 'valid':
            self._add_success(f"GitHub token valid for user: {token_result['user']}")
            token_status = "✅"
            token_value = f"{token_result['user']}"
            token_details = "Valid"
        else:
            self._add_error(f"GitHub token invalid: {token_result['message']}")
            token_status = "❌"
            token_value = "INVALID"
            token_details = token_result['message']

        # Test repository access
        repo_checks = [
            (self._test_github_token_access, "GitHub Token", token_status, token_value, token_details),
        ]

        # Test architecture hub access
        arch_hub_url = self.config.get_arch_hub_repo_url()
        if 'github.com' in arch_hub_url:
            repo_checks.append((self._test_arch_hub_access, "Architecture Hub", "", "", ""))

        # Test default repo access
        default_repo = os.getenv('DEFAULT_REPO_URL', self.config.DEFAULT_REPO_URL)
        if 'github.com' in default_repo:
            repo_checks.append((self._test_default_repo_access, "Default Repository", "", "", ""))

        # Run repository tests
        results = []
        for check_func, repo_name, status, value, details in repo_checks:
            if check_func == self._test_github_token_access:
                results.append((status, repo_name, value, details))
            else:
                result = check_func()
                results.append(result)

        self._display_table("🔐 REPOSITORY ACCESS TEST", results)

    def _test_github_token_access(self) -> Tuple[str, str, str, str]:
        """Test GitHub token access (placeholder for table structure)."""
        return "", "", "", ""

    def _test_arch_hub_access(self) -> Tuple[str, str, str, str]:
        """Test architecture hub repository access."""
        arch_hub_url = self.config.get_arch_hub_repo_url()
        # Extract repo name from URL for display
        repo_display = '/'.join(arch_hub_url.split('/')[-2:]) if '/' in arch_hub_url else arch_hub_url
        try:
            perm_result = self.git_manager.check_repository_permissions(arch_hub_url)
            if perm_result['status'] == 'allowed':
                self._add_success(f"Architecture Hub ({arch_hub_url}) access: Allowed")
                return "✅", f"Arch Hub ({repo_display})", "PUSH ACCESS", "Granted"
            elif perm_result['status'] == 'denied':
                self._add_warning(f"Architecture Hub ({arch_hub_url}) access: Push denied (read-only access)")
                return "⚠️", f"Arch Hub ({repo_display})", "READ ONLY", "Push denied"
            elif perm_result['status'] == 'not_found':
                self._add_warning(f"Architecture Hub ({arch_hub_url}) access: Repository not found")
                return "⚠️", f"Arch Hub ({repo_display})", "NOT FOUND", "Repository not found"
            else:
                self._add_warning(f"Architecture Hub ({arch_hub_url}) access: {perm_result['message']}")
                return "⚠️", f"Arch Hub ({repo_display})", "UNKNOWN", perm_result['message']
        except Exception as e:
            self._add_warning(f"Architecture Hub access test failed: {str(e)}")
            return "⚠️", f"Arch Hub ({repo_display})", "TEST FAILED", str(e)

    def _test_default_repo_access(self) -> Tuple[str, str, str, str]:
        """Test default repository access."""
        default_repo = os.getenv('DEFAULT_REPO_URL', self.config.DEFAULT_REPO_URL)
        # Extract repo name from URL for display
        repo_display = default_repo.split('/')[-1] if '/' in default_repo else default_repo
        try:
            perm_result = self.git_manager.check_repository_permissions(default_repo)
            if perm_result['status'] == 'allowed':
                self._add_success(f"Default Repository ({default_repo}) access: Allowed")
                return "✅", f"Default Repo ({repo_display})", "PUSH ACCESS", "Granted"
            elif perm_result['status'] == 'denied':
                self._add_warning(f"Default Repository ({default_repo}) access: Push denied (read-only access)")
                return "⚠️", f"Default Repo ({repo_display})", "READ ONLY", "Push denied"
            elif perm_result['status'] == 'not_found':
                self._add_warning(f"Default Repository ({default_repo}) access: Repository not found")
                return "⚠️", f"Default Repo ({repo_display})", "NOT FOUND", "Repository not found"
            else:
                self._add_warning(f"Default Repository ({default_repo}) access: {perm_result['message']}")
                return "⚠️", f"Default Repo ({repo_display})", "UNKNOWN", perm_result['message']
        except Exception as e:
            self._add_warning(f"Default Repository access test failed: {str(e)}")
            return "⚠️", "Default Repository", "TEST FAILED", str(e)

    def _display_table(self, title: str, results: List[Tuple[str, str, str, str]]):
        """Display results in a table format."""
        if self.console and RICH_AVAILABLE:
            self._display_rich_table(title, results)
        else:
            self._display_plain_table(title, results)

    def _display_rich_table(self, title: str, results: List[Tuple[str, str, str, str]]):
        """Display table using Rich library."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Status", style="white", width=4)
        table.add_column("Setting", style="yellow", width=20)
        table.add_column("Value", style="white", width=40)
        table.add_column("Details", style="blue", width=15)

        for status, setting, value, details in results:
            table.add_row(status, setting, value, details)

        self.console.print(table)

    def _display_plain_table(self, title: str, results: List[Tuple[str, str, str, str]]):
        """Display table in plain text format."""
        print(f"\n{title}")
        print("-" * 80)
        print(f"{'Status':<4} {'Setting':<20} {'Value':<40} {'Details':<15}")
        print("-" * 80)
        for status, setting, value, details in results:
            print(f"{status:<4} {setting:<20} {value:<40} {details:<15}")
        print("-" * 80)

    def _add_success(self, message: str):
        """Add a success message."""
        self.successes.append(message)

    def _add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)

    def _add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)

    def _print_summary(self):
        """Print verification summary."""
        if self.console and RICH_AVAILABLE:
            self._print_rich_summary()
        else:
            self._print_plain_summary()

    def _print_rich_summary(self):
        """Print summary using Rich formatting."""
        self.console.print("\n📊 VERIFICATION SUMMARY", style="bold magenta")
        self.console.print("=" * 50)

        # Successes
        if self.successes:
            self.console.print(Panel.fit("\n".join(f"✅ {success}" for success in self.successes),
                                       title="SUCCESSFUL CONFIGURATION",
                                       style="green"))

        # Warnings
        if self.warnings:
            self.console.print(Panel.fit("\n".join(f"⚠️  {warning}" for warning in self.warnings),
                                       title="WARNINGS",
                                       style="yellow"))

        # Errors
        if self.errors:
            self.console.print(Panel.fit("\n".join(f"❌ {error}" for error in self.errors),
                                       title="ERRORS",
                                       style="red"))

        # Results summary
        result_text = f"📈 RESULTS: {len(self.successes)} successes, {len(self.warnings)} warnings, {len(self.errors)} errors"
        if self.errors:
            self.console.print(f"\n💡 Please fix the errors above before running the worker.", style="red")
        elif self.warnings:
            self.console.print(f"\n💡 Consider addressing the warnings for optimal performance.", style="yellow")
        else:
            self.console.print(f"\n🎉 Configuration looks good! Ready to run the worker.", style="green")

    def _print_plain_summary(self):
        """Print summary in plain text format."""
        print("\n📊 VERIFICATION SUMMARY")
        print("=" * 50)

        if self.successes:
            print("✅ SUCCESSFUL CONFIGURATION:")
            for success in self.successes:
                print(f"   • {success}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"   • {error}")

        print(f"\n📈 RESULTS: {len(self.successes)} successes, {len(self.warnings)} warnings, {len(self.errors)} errors")

        if self.errors:
            print("\n💡 Please fix the errors above before running the worker.")
        elif self.warnings:
            print("\n💡 Consider addressing the warnings for optimal performance.")
        else:
            print("\n🎉 Configuration looks good! Ready to run the worker.")


def main():
    """Main entry point."""
    verifier = ConfigVerifier()
    success = verifier.verify()

    if not success:
        print("\n❌ Configuration verification failed!")
        sys.exit(1)
    else:
        print("\n✅ Configuration verification completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
