"""
Pydantic models for the investigation system.

This package contains all data models used throughout the application
for type safety, validation, and documentation.
"""

# Core investigation models
from .investigation import (
    PromptMetadata,
    InvestigationMetadata,
    InvestigationDecision,
    RepositoryState,
)

# Cache models
from .cache import (
    AnalysisResult,
    CacheCheckResult,
    PromptCacheResult,
)

# Activity models
from .activities import (
    CacheCheckInput,
    CacheCheckOutput,
    SaveMetadataInput,
    SaveMetadataOutput,
    AnalyzeStructureInput,
    AnalyzeStructureOutput,
    PromptContextDict,
    ClaudeConfigOverrides,
    AnalyzeWithClaudeInput,
    AnalyzeWithClaudeOutput,
)

# Workflow models
from .workflows import (
    WorkflowParams,
    WorkflowResult,
    AnalysisSummary,
    RepositoryAnalysis,
    # New workflow models
    ConfigOverrides,
    InvestigateSingleRepoRequest,
    InvestigateSingleRepoResult,
    InvestigateReposRequest,
    InvestigateReposResult,
    CloneRepositoryResult,
    PromptsConfigResult,
    AnalysisStepResult,
    ProcessAnalysisResult,
    WriteResultsOutput,
    SaveToHubResult,
    SaveToDynamoResult,
    InvestigationResult,
)

__all__ = [
    # Investigation
    "PromptMetadata",
    "InvestigationMetadata",
    "InvestigationDecision",
    "RepositoryState",
    # Cache
    "AnalysisResult",
    "CacheCheckResult",
    "PromptCacheResult",
    # Activities
    "CacheCheckInput",
    "CacheCheckOutput",
    "SaveMetadataInput",
    "SaveMetadataOutput",
    "AnalyzeStructureInput",
    "AnalyzeStructureOutput",
    "PromptContextDict",
    "ClaudeConfigOverrides",
    "AnalyzeWithClaudeInput",
    "AnalyzeWithClaudeOutput",
    # Workflows (legacy)
    "WorkflowParams",
    "WorkflowResult",
    "AnalysisSummary",
    "RepositoryAnalysis",
    # Workflows (new)
    "ConfigOverrides",
    "InvestigateSingleRepoRequest",
    "InvestigateSingleRepoResult",
    "InvestigateReposRequest",
    "InvestigateReposResult",
    "CloneRepositoryResult",
    "PromptsConfigResult",
    "AnalysisStepResult",
    "ProcessAnalysisResult",
    "WriteResultsOutput",
    "SaveToHubResult",
    "SaveToDynamoResult",
    "InvestigationResult",
]
