# Metadata-Based Repository Type Selection

## Overview

The investigator uses a **metadata-based approach** to select appropriate specialized prompts for each repository. Repository types are pre-configured in `repos.json` and passed as parameters rather than loaded from the filesystem.

## How It Works

1. **Repository Configuration**: Each repository in `repos.json` includes a `type` field
2. **Type Extraction**: The workflow reads `repos.json` and extracts the type for each repository
3. **Direct Passing**: The type is passed directly through the workflow chain as a parameter
4. **Prompt Selection**: The appropriate prompts directory is selected based on the type
5. **Fallback**: Repositories without a type default to `generic` prompts

## Architecture

The simplified type selection flow:

```
InvestigateReposWorkflow
    ↓ (reads repos.json once via activity)
    ↓ (extracts type for each repository)
    ↓ (passes repo_type to child workflow)
InvestigateSingleRepoWorkflow
    ↓ (passes repo_type to activity)
investigate_single_repository_activity
    ↓ (passes repo_type to investigator)
ClaudeInvestigator
    ↓ (uses repo_type directly)
RepositoryTypeDetector
    (selects prompts based on type parameter)
```

## Configuration Format

In `prompts/repos.json`:

```json
{
  "repositories": {
    "repo-name": {
      "url": "https://github.com/org/repo",
      "description": "Repository description",
      "type": "backend"  // <-- Repository type
    }
  }
}
```

## Available Repository Types

- **`generic`** - Default type for general repositories
- **`backend`** - Python/Rails backend services and APIs
- **`frontend`** - React, Vue, Angular applications
- **`mobile`** - iOS, Android, React Native, Flutter applications
- **`infra-as-code`** - Terraform, Ansible, Helm, CloudFormation
- **`libraries`** - NPM packages, Python libraries, SDKs

## Adding a New Repository

1. Add the repository to `repos.json`:
```json
"new-repo": {
  "url": "https://github.com/org/new-repo",
  "description": "New repository",
  "type": "backend"  // Choose appropriate type
}
```

2. The system will automatically use backend-specific prompts when investigating this repository.

## Manual Override

You can override the repository type when calling the investigator:

```python
# Use a specific type directly
investigate_repo("https://github.com/org/repo", repo_type="frontend")

# If no type is provided, defaults to "generic"
investigate_repo("https://github.com/org/repo")
```

## Workflow Integration

The Temporal workflows use a simplified data flow:

1. `InvestigateReposWorkflow` reads `repos.json` once
2. Extracts the `type` field for each repository
3. Creates a minimal request object with name, URL, and type
4. Passes the request object to `InvestigateSingleRepoWorkflow`
5. The activity uses the pre-selected type directly

### Request Object Structure

```json
{
  "repo_name": "repository-name",
  "repo_url": "https://github.com/org/repo",
  "repo_type": "backend"
}
```

The simplified request only contains essential fields:
- `repo_name` - Repository identifier
- `repo_url` - Repository location for cloning
- `repo_type` - Pre-selected type from repos.json

## Benefits

- **Predictable**: Repository types are explicitly configured
- **Fast**: No need to scan files for pattern detection
- **Simple**: Type is passed directly as a parameter
- **Maintainable**: Easy to see and update repository types in one place
- **Flexible**: Supports manual overrides when needed
- **Efficient**: Minimal data passed through the system
- **Clean**: No complex metadata passing or lookups
- **Scalable**: Works well in distributed/containerized environments

## Prompt Organization

Each repository type has its own prompts directory:

```
prompts/
├── generic/         # Default prompts
├── backend/         # Backend-specific prompts
├── frontend/        # Frontend-specific prompts
├── mobile/          # Mobile app prompts
├── infra-as-code/  # Infrastructure prompts
└── libraries/       # Library/SDK prompts
```

## Example

When investigating the "is-odd" repository:

1. System reads `repos.json` and finds `"type": "libraries"`
2. Selects `/prompts/libraries/` directory
3. Uses libraries specific prompts on top of the base ones, based on `src/prompts/libraries/prompts.json`

This ensures the analysis asks relevant questions for the repository type!
