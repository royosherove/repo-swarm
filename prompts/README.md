# Repository Analysis Prompts

This directory contains specialized prompt sets for analyzing different types of repositories. The system automatically selects the appropriate prompt set based on repository characteristics.

## Structure

```
prompts/
├── prompt_selector.json    # Configuration for automatic prompt selection
├── generic/                # Default prompts for all-in-one repositories
├── infra-as-code/         # Prompts for infrastructure projects (Terraform, Ansible, Helm)
├── frontend/              # Prompts for frontend applications
├── backend/               # Prompts for backend services
├── mobile/                # Prompts for mobile applications
└── libraries/             # Prompts for libraries, SDKs, and packages
```

## Prompt Sets

### 1. Generic (`generic/`)
- **Use Case**: All-in-one repositories, monorepos, or projects that don't fit other categories
- **Focus**: Comprehensive analysis covering all aspects
- **Prompts**: 
  - High-level overview
  - Module deep dive
  - Dependencies
  - Core entities
  - Databases
  - APIs
  - Events
  - Service dependencies

### 2. Infrastructure as Code (`infra-as-code/`)
- **Use Case**: Terraform, CloudFormation, Ansible, Helm, Kubernetes manifests
- **Focus**: Infrastructure patterns, cloud resources, deployment strategies
- **Prompts**:
  - Infrastructure overview
  - Resource analysis
  - Environment management
  - Provider dependencies

### 3. Frontend (`frontend/`)
- **Use Case**: React, Vue, Angular, and other UI applications
- **Focus**: Component architecture, state management, UI patterns
- **Prompts**:
  - Frontend architecture overview
  - Component structure
  - State and data flow
  - Build dependencies

### 4. Backend (`backend/`)
- **Use Case**: Python (Django, Flask, FastAPI) and Ruby on Rails backends
- **Focus**: API design, data layer, messaging, service architecture
- **Prompts**:
  - Service overview (with Python/Rails specific frameworks)
  - API endpoints
  - Data layer analysis (Django ORM, SQLAlchemy, ActiveRecord)
  - Events and messaging (Celery, Sidekiq)
  - Service dependencies (Python/Rails ecosystem)

### 5. Mobile (`mobile/`)
- **Use Case**: iOS, Android, React Native, Flutter, and other mobile applications
- **Focus**: Mobile UI patterns, device features, API integration, platform-specific concerns
- **Prompts**:
  - Mobile app overview (platforms, frameworks, architecture)
  - UI and navigation patterns
  - API and network communication
  - Device features and native capabilities
  - Data persistence and state management
  - Mobile-specific dependencies and SDKs

### 6. Libraries (`libraries/`)
- **Use Case**: NPM packages, Python libraries, SDKs, utility libraries
- **Focus**: API design, usage patterns, integration guides
- **Prompts**:
  - Library overview
  - API surface analysis
  - Internal architecture
  - Usage and integration

## Automatic Selection

The `prompt_selector.json` file contains detection patterns for automatically selecting the appropriate prompt set:

- **File patterns**: Looks for specific file types and names
- **Directory structure**: Analyzes folder organization
- **Dependencies**: Checks package dependencies
- **Keywords**: Scans for domain-specific terms

### Selection Priority
1. Infrastructure as Code
2. Libraries
3. Mobile
4. Frontend
5. Backend
6. Generic (fallback)

## Adding New Prompt Sets

To add a new specialized prompt set:

1. Create a new directory under `prompts/`
2. Add your prompt markdown files
3. Create a `prompts.json` file defining the processing order
4. Update `prompt_selector.json` with detection patterns

### Example prompts.json Structure

```json
{
  "processing_order": [
    {
      "name": "overview",
      "file": "overview.md",
      "description": "High level overview",
      "required": true,
      "order": 1
    },
    {
      "name": "analysis",
      "file": "analysis.md",
      "description": "Detailed analysis",
      "required": true,
      "order": 2,
      "context": [
        {"type": "step", "val": "overview"}
      ]
    }
  ],
  "config": {
    "type": "your-type"
  }
}
```

## Prompt Context

Prompts can reference previous analysis results using the `context` field:
- `{"type": "step", "val": "step_name"}`: Include results from a previous step

## Shared Prompts

Shared prompts in the `shared/` directory are used across multiple repository types:

1. **authentication.md**: Analyzes authentication mechanisms, identity management, and access control
2. **authorization.md**: Examines authorization patterns, roles, permissions, and access control policies
3. **core_entities.md**: Identifies core data models, entities, and their relationships
4. **data_mapping.md**: Maps data flows, personal information handling, and compliance requirements
5. **dependencies.md**: Documents external libraries, frameworks, and internal modules
6. **security_check.md**: Performs comprehensive security vulnerability assessment

## Variables

All prompts support the following variables:
- `{repo_structure}`: Complete repository file structure
- `{previous_context}`: Results from previous analysis steps (if configured)

## Manual Override

To force a specific prompt set, you can:
1. Set an environment variable: `PROMPT_TYPE=frontend`
2. Pass a parameter to the analyzer
3. Modify the detection logic in your implementation

## Best Practices

1. **Keep prompts focused**: Each prompt should have a single, clear objective
2. **Use appropriate context**: Only include previous results when needed
3. **Order matters**: Arrange prompts from general to specific
4. **Test detection**: Verify that repositories are correctly identified
5. **Document special instructions**: Use clear markers like "**Special Instruction:**"
