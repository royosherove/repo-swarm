# Repository Type Detection System

## Overview

The investigator now automatically detects repository types and selects appropriate specialized prompts for analysis. This provides more targeted and relevant insights for different types of projects.

## How It Works

1. **Automatic Detection**: When analyzing a repository, the system examines:
   - File patterns (e.g., `requirements.txt`, `package.json`, `*.tf`)
   - Directory structure (e.g., `/terraform`, `/components`, `/controllers`)
   - Dependencies in package files
   - Keywords in source code

2. **Scoring Algorithm**: Each repository type gets a confidence score based on:
   - 50% weight on file patterns
   - 30% weight on directory structure
   - 15% weight on dependencies
   - 5% weight on keywords
   - Boosting for significant indicators (e.g., framework-specific files)

3. **Type Selection**: The system follows a priority order:
   1. Infrastructure as Code
   2. Libraries
   3. Frontend
   4. Backend
   5. Generic (fallback)

## Repository Types

### 1. Backend (Python/Rails)
- **Detection**: `requirements.txt`, `Gemfile`, `*.py`, `*.rb`, `/api`, `/models`
- **Prompts**: Service overview, APIs, data layer, events/messaging, dependencies

### 2. Frontend
- **Detection**: `package.json` with UI frameworks, `/components`, `/pages`, `*.jsx`, `*.tsx`
- **Prompts**: UI architecture, components, state management, build configuration

### 3. Infrastructure as Code
- **Detection**: `*.tf`, `ansible.cfg`, `Chart.yaml`, `/terraform`, `/helm`
- **Prompts**: Infrastructure overview, resources, environments, provider dependencies

### 4. Libraries
- **Detection**: `setup.py`, build configs, `/lib`, `/dist`, package exports
- **Prompts**: API surface, internals, usage patterns, integration guides

### 5. Generic
- **Default fallback**: Comprehensive analysis for mixed/unknown projects
- **Prompts**: All aspects covered (modules, entities, databases, APIs, events)

## Usage

### Automatic Detection (Default)
```python
from investigator import investigate_repo

# Automatically detects repository type
result = investigate_repo("https://github.com/user/repo")
```

### Manual Override
```python
# Force a specific repository type
result = investigate_repo(
    "https://github.com/user/repo",
    repo_type="frontend"  # Options: backend, frontend, infra-as-code, libraries, generic
)
```

### In Temporal Workflows
The detection works seamlessly in Temporal activities:
```python
class InvestigateActivities:
    async def investigate_single_repo(self, repo_url: str) -> str:
        # Automatic detection happens internally
        return investigate_repo(repo_url)
```

## Configuration

The detection patterns are defined in `prompt_selector.json`. You can:
- Adjust detection patterns for better accuracy
- Modify scoring weights
- Add new repository types
- Change the confidence threshold (default: 0.15)

## Debugging

When running the investigator, you'll see log messages indicating:
- Which repository type was detected
- The confidence score
- Which prompts directory is being used

Example:
```
INFO - Detecting repository type for: /path/to/repo
INFO - Detected repository type: backend (confidence: 0.60)
INFO - Using prompts from: /path/to/prompts/backend
```

## Adding Custom Repository Types

1. Create a new directory under `prompts/your-type/`
2. Add specialized prompt files
3. Create a `prompts.json` defining the processing order
4. Update `prompt_selector.json` with detection patterns

## Benefits

- **More Relevant Analysis**: Specialized prompts ask the right questions for each project type
- **Better Structure Understanding**: Type-specific patterns are recognized
- **Improved Insights**: Focus on what matters for each repository type
- **Extensible**: Easy to add new types and customize detection

