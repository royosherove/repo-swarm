# Claude Investigator

A Python tool that uses Claude Code SDK to analyze repository structure and generate comprehensive architecture documentation.

## Features

- **Repository Cloning**: Automatically clones repositories to analyze
- **Private Repository Support**: Supports GitHub private repositories using personal access tokens
- **Structure Analysis**: Uses Claude AI to analyze repository structure and architecture
- **Documentation Generation**: Outputs detailed architecture analysis to `{repository-name}-arch.md`
- **Clean Up**: Automatically cleans up temporary files after analysis

## Installation

1. Install the required dependencies:
```bash
uv sync
```

2. Set up your Claude API key:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

3. (Optional) For private GitHub repositories, set up your GitHub token:
```bash
export GITHUB_TOKEN="your-github-personal-access-token"
```

## Authentication for Private Repositories

### GitHub Private Repositories

To analyze private GitHub repositories, you need to set the `GITHUB_TOKEN` environment variable with a personal access token that has repository read permissions.

1. Create a GitHub personal access token:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Click "Generate new token" (classic)
   - Select the `repo` scope for full repository access
   - Generate and copy the token

2. Set the environment variable:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

3. Use the investigator normally:
```bash
python investigator.py https://github.com/username/private-repo
```

The tool will automatically detect GitHub URLs and use the token for authentication when available.

## Usage

### Command Line

```bash
python investigator.py <repository_location> [api_key] [log_level]
```

Examples:
```bash
# Basic usage with default INFO logging
python investigator.py https://github.com/username/repo-name

# With custom API key
python investigator.py https://github.com/username/repo-name your-api-key

# With DEBUG logging for detailed output
python investigator.py https://github.com/username/repo-name your-api-key DEBUG

# With WARNING logging for minimal output
python investigator.py https://github.com/username/repo-name your-api-key WARNING

# Private repository (requires GITHUB_TOKEN environment variable)
export GITHUB_TOKEN="ghp_your_token_here"
python investigator.py https://github.com/username/private-repo
```

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General information about progress (default)
- `WARNING`: Only warnings and errors
- `ERROR`: Only error messages

### Python API

#### Using the convenience function:

```python
from investigator import investigate_repo
import os

# For private repositories, set the GitHub token
os.environ['GITHUB_TOKEN'] = 'ghp_your_token_here'

# Analyze a repository with default INFO logging
arch_file_path = investigate_repo("https://github.com/username/repo-name")
print(f"Analysis saved to: {arch_file_path}")

# With custom logging level
arch_file_path = investigate_repo("https://github.com/username/repo-name", log_level="DEBUG")
```

#### Using the class directly:

```python
from investigator import ClaudeInvestigator
import os

# For private repositories, set the GitHub token
os.environ['GITHUB_TOKEN'] = 'ghp_your_token_here'

# Create investigator instance with default logging
investigator = ClaudeInvestigator(api_key="your-api-key")

# Create investigator with custom logging level
investigator = ClaudeInvestigator(api_key="your-api-key", log_level="DEBUG")

# Analyze a repository
arch_file_path = investigator.investigate_repository("https://github.com/username/repo-name")
print(f"Analysis saved to: {arch_file_path}")
```

## Output

The tool generates a `{repository-name}-arch.md` file in the repository with a comprehensive analysis including:

1. **Project Overview**: Type and main purpose of the project
2. **Architecture Pattern**: Overall architectural patterns used
3. **Technology Stack**: Main technologies, frameworks, and tools
4. **Directory Structure**: Explanation of key directories and their purposes
5. **Key Components**: Main components/modules and their responsibilities
6. **Dependencies**: Notable external dependencies or integrations
7. **Build/Deployment**: How the project is likely built and deployed
8. **Code Organization**: How the code is organized and structured

## Example

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# (Optional) Set GitHub token for private repositories
export GITHUB_TOKEN="ghp_your_token_here"

# Run the investigator with default INFO logging
python investigator.py https://github.com/username/example-repo

# Run with DEBUG logging for detailed output
python investigator.py https://github.com/username/example-repo "" DEBUG

# Output: Investigation complete! Analysis saved to: /tmp/claude_investigator_xxx/{repository-name}-arch.md
```

### Sample Log Output (INFO level)

```
2024-01-15 10:30:15 - investigator - INFO - Initializing Claude Investigator
2024-01-15 10:30:15 - investigator - DEBUG - Claude Investigator initialized successfully
2024-01-15 10:30:15 - investigator - INFO - Starting investigation of repository: https://github.com/username/repo-name
2024-01-15 10:30:15 - investigator - INFO - Step 1: Cloning repository
2024-01-15 10:30:15 - investigator - DEBUG - Creating temporary directory for repository cloning
2024-01-15 10:30:15 - investigator - DEBUG - Temporary directory created: /tmp/claude_investigator_abc123
2024-01-15 10:30:15 - investigator - INFO - Cloning repository from: https://github.com/username/repo-name
2024-01-15 10:30:15 - investigator - INFO - Using GitHub token authentication for private repository access
2024-01-15 10:30:20 - investigator - INFO - Repository successfully cloned to: /tmp/claude_investigator_abc123
2024-01-15 10:30:20 - investigator - INFO - Repository size: 2.3 MB (1,247 files)
2024-01-15 10:30:20 - investigator - INFO - Step 2: Analyzing repository structure
2024-01-15 10:30:20 - investigator - DEBUG - Getting repository structure
2024-01-15 10:30:21 - investigator - DEBUG - Repository structure scan complete: 45 directories, 1,247 files
2024-01-15 10:30:21 - investigator - INFO - Repository structure captured (1,292 lines)
2024-01-15 10:30:21 - investigator - DEBUG - Creating analysis prompt for Claude
2024-01-15 10:30:21 - investigator - DEBUG - Prompt created (2,847 characters)
2024-01-15 10:30:21 - investigator - INFO - Sending analysis request to Claude API
2024-01-15 10:30:21 - investigator - DEBUG - Using model: claude-3-5-sonnet-20241022, max_tokens: 4000
2024-01-15 10:30:45 - investigator - INFO - Received analysis from Claude (3,892 characters)
2024-01-15 10:30:45 - investigator - DEBUG - Analysis preview: # Repository Architecture Analysis

This document was automatically generated by Claude Investigator to analyze the repository structure and architecture.

## Project Overview

This appears to be a Python web application...
2024-01-15 10:30:45 - investigator - INFO - Step 3: Writing analysis to arch.md
2024-01-15 10:30:45 - investigator - DEBUG - Writing analysis to: /tmp/claude_investigator_abc123/arch.md
2024-01-15 10:30:45 - investigator - INFO - Architecture analysis written to: /tmp/claude_investigator_abc123/arch.md
2024-01-15 10:30:45 - investigator - DEBUG - File size: 4,156 characters
2024-01-15 10:30:45 - investigator - INFO - Investigation completed successfully. Analysis saved to: /tmp/claude_investigator_abc123/arch.md
2024-01-15 10:30:45 - investigator - INFO - Cleaning up temporary directory: /tmp/claude_investigator_abc123
2024-01-15 10:30:45 - investigator - DEBUG - Temporary directory cleanup completed
```

## Requirements

- Python 3.7+
- Claude API key
- Git (for repository cloning)
- Internet connection (for API calls and repository cloning)
- GitHub personal access token (for private repositories)

## Dependencies

- `anthropic`: Claude Code SDK
- `gitpython`: Git repository operations
- `temporalio`: Temporal workflow framework (existing dependency)

## Error Handling

The tool includes comprehensive error handling for:
- Invalid repository URLs
- Network connectivity issues
- API authentication problems (including GitHub authentication failures)
- File system operations
- Claude API rate limits

## Security Notes

- The GitHub token is never logged or displayed in output for security reasons
- The tool only adds authentication to GitHub URLs when the GITHUB_TOKEN is available
- Existing authentication in URLs is preserved and not overridden
- Error messages are sanitized to prevent token leakage

## Notes

- The tool creates temporary directories for cloning repositories
- Temporary files are automatically cleaned up after analysis
- The analysis is written to `arch.md` in the cloned repository directory
- Make sure you have sufficient API credits for Claude calls
- For private repositories, ensure your GitHub token has appropriate permissions 