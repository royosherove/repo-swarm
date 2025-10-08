<!--
SYNC IMPACT REPORT
==================
Version change: Initial → 1.0.0
Modified principles: N/A (initial version)
Added sections: All sections are new
Removed sections: None
Templates requiring updates:
  ✅ plan-template.md - Constitution Check section already aligned
  ✅ spec-template.md - User scenarios and requirements structure compatible
  ✅ tasks-template.md - Testing discipline and phase organization compatible
Follow-up TODOs: None
-->

# RepoSwarm Constitution

## Core Principles

### I. Separation of Concerns

Every component has a single, well-defined responsibility. The architecture enforces clean boundaries:

- **Core Components**: Each component in `src/investigator/core/` handles one concern (Git operations, Claude API, file management, repository analysis, type detection)
- **Activities vs Workflows**: Temporal activities perform isolated units of work; workflows orchestrate without business logic
- **Storage Abstraction**: Storage implementations (DynamoDB, file-based) are isolated behind a common interface (`PromptContext`)
- **No Cross-Contamination**: Git logic stays in `git_manager.py`, Claude API calls in `claude_analyzer.py`, file operations in `file_manager.py`

**Rationale**: Single Responsibility Principle enables independent testing, parallel development, and confident refactoring without cascading changes.

### II. Test-First Development (NON-NEGOTIABLE)

All production code MUST follow Test-Driven Development as defined in "The Art of Unit Testing" (3rd edition):

- **Red-Green-Refactor**: Tests are written first and MUST fail before implementation begins
- **Test Organization**: Tests are organized in `tests/unit/` (isolated, fast) and `tests/integration/` (external dependencies, slower)
- **Test Naming**: Test names follow the pattern `test_<unit_under_test>_<scenario>_<expected_behavior>` (e.g., `test_clean_prompt_removes_version_line`)
- **Trustworthy Tests**: Tests must be readable, maintainable, and trustworthy - avoid magic numbers, unclear assertions, or implementation details leaking into tests
- **Test Independence**: Each test can run in isolation without depending on execution order
- **Mock External Dependencies**: Unit tests mock all external dependencies (API calls, file system, Git operations)

**Rationale**: TDD produces better design, catches regressions early, and serves as living documentation. Following Roy Osherove's principles ensures tests remain maintainable long-term.

### III. Configuration and Environment Management

All configuration is externalized and environment-specific:

- **Environment Files**: Use `.env.local` for local development (gitignored), `.env` for defaults, `env.example` for documentation
- **Secrets Management**: API keys and sensitive data NEVER committed to repository; use environment variables or AWS Parameter Store
- **Runtime Configuration**: All configuration centralized in `src/investigator/core/config.py` with sensible defaults
- **Validation**: Configuration validation happens at startup (see `scripts/verify_config.py`)
- **Override Capability**: Allow CLI arguments to override config values (model, max-tokens, sleep-hours, etc.)

**Rationale**: Secure credential handling, environment-specific behavior without code changes, and easy local development setup.

### IV. Workflow Orchestration and Reliability

Temporal workflows ensure reliability and observability:

- **Workflow Activities**: Every external operation (Git clone, Claude API call, file write) is a separate Temporal activity
- **Idempotency**: Activities must be idempotent - safe to retry on failure
- **Heartbeat Monitoring**: Long-running activities send heartbeats to Temporal for health monitoring
- **Activity Wrapper**: Use `ActivityWrapper` to safely execute activities with proper error handling and heartbeat support
- **Workflow State**: Workflows maintain state in Temporal, not in application memory
- **Caching Logic**: Cache decisions happen at workflow level based on repository state (commit SHA, branch, timestamp)

**Rationale**: Temporal provides durable execution, automatic retries, visibility into workflow state, and resilience against infrastructure failures.

### V. Caching and Performance

Intelligent caching avoids redundant analysis:

- **Cache Invalidation**: Cache is invalidated when commit SHA changes, branch changes, or cache TTL expires (30 days default)
- **Version-Aware Caching**: Prompt version changes trigger re-analysis even if repository hasn't changed
- **Storage Abstraction**: Cache implementation can be file-based (local development) or DynamoDB (production) without code changes
- **Metadata Tracking**: Store repository metadata (commit, branch, timestamp, prompt versions) alongside analysis results
- **Force Flag**: Allow explicit cache bypass via `force` parameter for debugging or manual re-analysis

**Rationale**: Reduces Claude API costs, improves performance, respects rate limits, while ensuring analysis remains fresh when inputs change.

### VI. Type Detection and Prompt Selection

Repository type determines analysis approach:

- **Automatic Detection**: System automatically detects repository type (backend, frontend, mobile, library, infra-as-code, generic) based on file patterns
- **Override Capability**: Allow manual type specification via `type` parameter for edge cases
- **Prompt Organization**: Prompts organized by repository type in `prompts/{type}/` with shared cross-cutting prompts in `prompts/shared/`
- **Hierarchical Prompts**: Repository-specific prompts inherit and extend shared prompts
- **Version Tracking**: Each prompt file tracks its version for cache invalidation

**Rationale**: Different repository types require different analysis perspectives. Automatic detection reduces manual configuration while allowing override for accuracy.

### VII. Observability and Debugging

System behavior must be transparent and debuggable:

- **Structured Logging**: Consistent log format with timestamp, level, and component name
- **Log Levels**: Use DEBUG for verbose output, INFO for key operations, WARNING for recoverable issues, ERROR for failures
- **Temporal UI**: Workflow execution visible in Temporal UI with complete history and state
- **Query Handlers**: Workflows expose query handlers for status inspection during execution
- **Verification Tools**: Provide `mise verify-config` for configuration validation before deployment
- **Debug Mode**: Support `investigate-debug` task with verbose logging for troubleshooting

**Rationale**: Production issues are inevitable. Comprehensive observability reduces mean time to resolution and enables proactive monitoring.

## Development Workflow

### Task Organization via Mise

All development tasks are defined in `mise.toml` with:

- **Consistent Naming**: Tasks follow `category-action` pattern (e.g., `dev-temporal`, `test-units`, `investigate-all`, `docker-build`)
- **Clear Documentation**: Each task includes "Use when:" guidance and examples
- **Environment Integration**: Tasks automatically load environment from `.env.local` or `.env`
- **Workflow Orchestration**: Complex workflows orchestrated through mise tasks rather than ad-hoc scripts
- **Testing Hierarchy**: Tests organized as `test-all` (comprehensive), `test-units` (fast), `test-integration` (slower)

### Code Review and Quality Gates

Before merging:

- **All Tests Pass**: Both unit and integration tests must pass
- **Linting Clean**: Code must pass linting without warnings
- **Test Coverage**: New code requires corresponding tests
- **Configuration Valid**: Run `mise verify-config` to validate settings
- **No Secrets**: Verify no secrets committed via environment variables or hardcoded values

### Git Workflow

- **Branch Naming**: Use feature branches with descriptive names
- **Commit Messages**: Follow conventional commits format
- **No Force Push**: Never force push to main/master branch
- **Hooks Respected**: Never skip git hooks unless explicitly justified

## Architecture Constraints

### Component Structure

```
src/
├── investigator/       # Core analysis engine
│   ├── core/          # Single-responsibility components
│   └── investigator.py # Main orchestrator
├── workflows/          # Temporal workflow definitions
├── activities/         # Temporal activity implementations
├── models/             # Data models and schemas
└── utils/              # Shared utilities and storage adapters
```

### Dependency Rules

- **Core Independence**: `src/investigator/core/` components have no dependencies on workflows or activities
- **Workflow Abstraction**: Workflows depend on activities, not on implementation details
- **Storage Abstraction**: No direct DynamoDB or file system calls outside storage adapters
- **Activity Isolation**: Activities are pure functions with clear inputs/outputs

### Technology Stack

- **Python 3.12+**: Required language version
- **Temporal**: Workflow orchestration (must support async Python workflows)
- **Claude API**: AI analysis via Anthropic SDK
- **DynamoDB**: Production cache storage (with local file-based fallback)
- **pytest**: Testing framework with async support
- **mise**: Tool version management and task orchestration

## Security Requirements

### Secrets Management

- **Environment Variables**: All secrets loaded from environment, never hardcoded
- **GitHub Tokens**: Stored in environment, support for multiple GitHub accounts (see `git_manager.py`)
- **AWS Credentials**: Use standard AWS credential chain (environment, config files, IAM roles)
- **API Keys**: Claude API key required in `ANTHROPIC_API_KEY` environment variable

### Input Validation

- **URL Sanitization**: Repository URLs sanitized before use (remove auth tokens, validate format)
- **Path Traversal**: Prevent directory traversal in file operations
- **Git Operations**: Use GitPython library for safe Git operations
- **User Input**: Validate and sanitize all user-provided configuration

### Logging Safety

- **No Secrets in Logs**: Never log API keys, tokens, or credentials
- **Sanitize URLs**: Remove authentication tokens from URLs before logging
- **PII Protection**: Avoid logging personally identifiable information

## Governance

### Amendment Process

1. Propose amendment with rationale
2. Update constitution with version bump (MAJOR for breaking changes, MINOR for additions, PATCH for clarifications)
3. Update Sync Impact Report at top of document
4. Validate all dependent templates remain consistent
5. Document in commit message

### Version Semantics

- **MAJOR**: Principle removed or fundamentally redefined; breaking governance changes
- **MINOR**: New principle added or existing principle materially expanded
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance

- **Constitution Supersedes**: This constitution takes precedence over informal practices
- **Complexity Justification**: Any deviation from principles requires documented justification
- **Review Requirement**: All code reviews verify compliance with constitution principles
- **Template Consistency**: Plan, spec, and task templates must align with constitution

### Related Documentation

- **Runtime Guidance**: See `README.md` for development setup and deployment
- **Testing Principles**: Follow "The Art of Unit Testing" (3rd edition) by Roy Osherove
- **Security Guidelines**: See workspace rules for detailed security practices

**Version**: 1.0.0 | **Ratified**: 2025-10-08 | **Last Amended**: 2025-10-08
