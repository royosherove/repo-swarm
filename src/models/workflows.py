"""
Workflow parameter and result models.

These models define the inputs and outputs for workflows,
ensuring consistent data structures across the workflow system.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, HttpUrl
from datetime import datetime


class ConfigOverrides(BaseModel):
    """Configuration overrides for workflows."""
    claude_model: Optional[str] = Field(None, description="Claude model to use (e.g., claude-3-sonnet-20240229)")
    max_tokens: Optional[int] = Field(None, ge=1, le=200000, description="Maximum tokens for Claude response")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="Temperature for Claude response")
    sleep_hours: Optional[float] = Field(None, ge=0.1, le=168.0, description="Hours to sleep between executions")
    chunk_size: Optional[int] = Field(None, ge=1, le=100, description="Number of repos to process in parallel")
    force_section: Optional[str] = Field(None, description="Force re-execution of specific section (prompt name)")
    
    @validator('claude_model')
    def validate_claude_model(cls, v):
        """Ensure Claude model is valid if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Claude model must not be empty if provided")
        return v.strip() if v else v
    
    @validator('force_section')
    def validate_force_section(cls, v):
        """Ensure force section is valid if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Force section must not be empty if provided")
        return v.strip() if v else v


class InvestigateSingleRepoRequest(BaseModel):
    """Input parameters for single repository investigation workflow."""
    repo_name: str = Field(..., description="Name of the repository")
    repo_url: str = Field(..., description="URL of the repository")
    repo_type: Optional[str] = Field(default="generic", description="Repository type")
    force: bool = Field(default=False, description="Force investigation even if cached")
    config_overrides: Optional[ConfigOverrides] = Field(None, description="Configuration overrides")
    
    @validator('repo_name')
    def validate_repo_name(cls, v):
        """Ensure repo name is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository name must not be empty")
        return v.strip()
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        """Ensure repo URL is valid."""
        if not v or not v.strip():
            raise ValueError("Repository URL must not be empty")
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError("Repository URL must start with http:// or https://")
        return v.strip()


class CloneRepositoryResult(BaseModel):
    """Result from repository cloning operation."""
    repo_path: str = Field(..., description="Path to the cloned repository")
    temp_dir: str = Field(..., description="Temporary directory path")
    status: str = Field(default="success", description="Status of the operation")
    message: Optional[str] = Field(None, description="Optional status message")


class PromptsConfigResult(BaseModel):
    """Result from prompts configuration loading."""
    prompts_dir: str = Field(..., description="Directory containing prompts")
    processing_order: List[Dict[str, Any]] = Field(..., description="Order of prompt processing")
    prompt_versions: Dict[str, str] = Field(default_factory=dict, description="Mapping of prompt names to versions")
    status: str = Field(default="success", description="Status of the operation")


class AnalysisStepResult(BaseModel):
    """Result from a single analysis step."""
    step_name: str = Field(..., description="Name of the analysis step")
    result_key: str = Field(..., description="Reference key for the result")
    cached: bool = Field(..., description="Whether the result was served from cache")
    cache_reason: Optional[str] = Field(None, description="Reason for cache hit/miss")


class ProcessAnalysisResult(BaseModel):
    """Result from processing all analysis steps."""
    step_results: Dict[str, str] = Field(..., description="Mapping of step names to result keys")
    all_results: List[Dict[str, Any]] = Field(..., description="All analysis results")
    total_steps: int = Field(..., ge=0, description="Total number of steps processed")
    cached_steps: int = Field(default=0, ge=0, description="Number of steps served from cache")


class WriteResultsOutput(BaseModel):
    """Result from writing analysis results to file."""
    arch_file_path: str = Field(..., description="Path to the architecture file")
    status: str = Field(default="success", description="Status of the operation")
    message: Optional[str] = Field(None, description="Optional status message")


class SaveToHubResult(BaseModel):
    """Result from saving to architecture hub."""
    status: str = Field(..., description="Status of the save operation")
    message: str = Field(..., description="Description of the result")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid."""
        if v not in ['success', 'failed', 'skipped']:
            raise ValueError("Status must be 'success', 'failed', or 'skipped'")
        return v


class SaveToDynamoResult(BaseModel):
    """Result from saving metadata to DynamoDB."""
    status: str = Field(..., description="Status of the save operation")
    message: str = Field(..., description="Description of the result")
    timestamp: Optional[float] = Field(None, description="Unix timestamp when saved")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid."""
        if v not in ['success', 'failed']:
            raise ValueError("Status must be 'success' or 'failed'")
        return v


class InvestigateSingleRepoResult(BaseModel):
    """Result from single repository investigation workflow."""
    status: str = Field(..., description="Workflow status")
    repo_name: str = Field(..., description="Name of the repository")
    repo_url: str = Field(..., description="URL of the repository")
    repo_type: str = Field(default="generic", description="Repository type")
    arch_file_path: Optional[str] = Field(None, description="Path to architecture file")
    analysis_steps: int = Field(default=0, ge=0, description="Number of analysis steps completed")
    prompt_versions: Dict[str, str] = Field(default_factory=dict, description="Versions of prompts used")
    latest_commit: str = Field(..., description="Commit SHA that was analyzed")
    branch_name: str = Field(..., description="Branch that was analyzed")
    cached: bool = Field(default=False, description="Whether result was from cache")
    reason: Optional[str] = Field(None, description="Reason for the result")
    arch_file_content: Optional[str] = Field(None, description="Content of the architecture file")
    architecture_hub: Optional[Dict[str, Any]] = Field(None, description="Architecture hub save result")
    metadata_saved: Optional[Dict[str, Any]] = Field(None, description="Metadata save result")
    cleanup: Optional[Dict[str, Any]] = Field(None, description="Cleanup operation result")
    last_investigation_timestamp: Optional[str] = Field(None, description="Timestamp of last investigation")
    message: str = Field(..., description="Human-readable message about the result")
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid."""
        valid_statuses = ['success', 'failed', 'skipped', 'partial']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class InvestigationResult(BaseModel):
    """Result from a completed investigation operation."""
    status: str = Field(..., description="Status of the investigation")
    arch_file_path: str = Field(..., description="Path to the architecture file")
    analysis_steps: int = Field(..., ge=0, description="Number of analysis steps completed")
    prompt_versions: Dict[str, str] = Field(..., description="Versions of prompts used")
    repo_name: str = Field(..., description="Name of the repository")
    repo_url: str = Field(..., description="URL of the repository")
    latest_commit: str = Field(..., description="Latest commit SHA")
    branch_name: str = Field(..., description="Branch name")
    arch_file_content: str = Field(..., description="Content of the architecture file")
    architecture_hub: Optional[Dict[str, Any]] = Field(None, description="Architecture hub save result")
    metadata_saved: Optional[Dict[str, Any]] = Field(None, description="Metadata save result")
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid."""
        if v not in ['success', 'failed', 'partial']:
            raise ValueError("Status must be 'success', 'failed', or 'partial'")
        return v
    
    @validator('repo_name')
    def validate_repo_name(cls, v):
        """Ensure repo name is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository name must not be empty")
        return v.strip()
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        """Ensure repo URL is valid."""
        if not v or not v.strip():
            raise ValueError("Repository URL must not be empty")
        return v.strip()
    
    @validator('arch_file_content')
    def validate_arch_file_content(cls, v):
        """Ensure architecture file content is not empty."""
        if not v or not v.strip():
            raise ValueError("Architecture file content must not be empty")
        return v


class InvestigateReposRequest(BaseModel):
    """Input parameters for multi-repository investigation workflow."""
    force: bool = Field(default=False, description="Force investigation of all repos ignoring cache")
    claude_model: Optional[str] = Field(None, description="Override the Claude model to use")
    max_tokens: Optional[int] = Field(None, ge=1, le=200000, description="Override the max tokens")
    sleep_hours: Optional[float] = Field(None, ge=0.1, le=168.0, description="Hours to sleep between executions")
    chunk_size: Optional[int] = Field(None, ge=1, le=100, description="Number of repos to process in parallel")
    iteration_count: int = Field(default=0, ge=0, description="Current iteration number")
    
    @validator('claude_model')
    def validate_claude_model(cls, v):
        """Ensure Claude model is valid if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Claude model must not be empty if provided")
        return v.strip() if v else v


class InvestigateReposResult(BaseModel):
    """Result from multi-repository investigation workflow."""
    status: str = Field(..., description="Workflow status")
    total_repos: int = Field(..., ge=0, description="Total number of repositories processed")
    successful: int = Field(..., ge=0, description="Number of successful investigations")
    failed: int = Field(..., ge=0, description="Number of failed investigations")
    skipped: int = Field(..., ge=0, description="Number of skipped repositories")
    investigated_repos: List[InvestigateSingleRepoResult] = Field(..., description="Results from all repository investigations")
    repository_update: Dict[str, Any] = Field(..., description="Repository list update results")
    architecture_analysis: Optional[Dict[str, Any]] = Field(None, description="Architecture analysis results")
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid."""
        valid_statuses = ['completed', 'failed', 'partial']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    
    @validator('successful')
    def validate_successful(cls, v, values):
        """Ensure successful count doesn't exceed total."""
        if 'total_repos' in values and v > values['total_repos']:
            raise ValueError("Successful count cannot exceed total repositories")
        return v
    
    @validator('failed')
    def validate_failed(cls, v, values):
        """Ensure failed count doesn't exceed total."""
        if 'total_repos' in values and v > values['total_repos']:
            raise ValueError("Failed count cannot exceed total repositories")
        return v
    
    @validator('skipped')
    def validate_skipped(cls, v, values):
        """Ensure skipped count doesn't exceed total."""
        if 'total_repos' in values and v > values['total_repos']:
            raise ValueError("Skipped count cannot exceed total repositories")
        return v


# Legacy models for backward compatibility
class WorkflowParams(BaseModel):
    """Input parameters for investigation workflows."""
    repo_name: str = Field(..., description="Name of the repository")
    repo_url: str = Field(..., description="URL of the repository")
    repo_path: Optional[str] = Field(None, description="Local path to repository if already cloned")
    force_investigation: bool = Field(default=False, description="Force investigation even if cached")
    prompt_versions: Optional[Dict[str, str]] = Field(None, description="Mapping of prompt names to versions")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum number of retries for activities")
    timeout_minutes: int = Field(default=30, ge=5, le=120, description="Overall workflow timeout in minutes")
    
    @validator('repo_name')
    def validate_repo_name(cls, v):
        """Ensure repo name is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository name must not be empty")
        return v.strip()


class AnalysisSummary(BaseModel):
    """Summary of repository analysis results."""
    total_prompts: int = Field(..., ge=0, description="Total number of prompts executed")
    successful_prompts: int = Field(..., ge=0, description="Number of successful prompts")
    failed_prompts: int = Field(default=0, ge=0, description="Number of failed prompts")
    cached_prompts: int = Field(default=0, ge=0, description="Number of prompts served from cache")
    execution_time_seconds: float = Field(..., ge=0, description="Total execution time in seconds")
    sections_analyzed: List[str] = Field(default_factory=list, description="List of sections analyzed")
    
    @validator('successful_prompts')
    def validate_successful_prompts(cls, v, values):
        """Ensure successful prompts doesn't exceed total."""
        if 'total_prompts' in values and v > values['total_prompts']:
            raise ValueError("Successful prompts cannot exceed total prompts")
        return v
    
    @validator('failed_prompts')
    def validate_failed_prompts(cls, v, values):
        """Ensure failed prompts doesn't exceed total."""
        if 'total_prompts' in values and v > values['total_prompts']:
            raise ValueError("Failed prompts cannot exceed total prompts")
        return v


class RepositoryAnalysis(BaseModel):
    """Complete repository analysis result."""
    repo_name: str = Field(..., description="Name of the repository")
    repo_url: str = Field(..., description="URL of the repository")
    repo_type: str = Field(..., description="Detected repository type")
    latest_commit: str = Field(..., description="Commit SHA that was analyzed")
    branch_name: str = Field(..., description="Branch that was analyzed")
    analysis_timestamp: datetime = Field(..., description="When the analysis was performed")
    analysis_content: str = Field(..., description="The complete analysis content")
    summary: AnalysisSummary = Field(..., description="Summary of the analysis")
    prompt_versions: Optional[Dict[str, str]] = Field(None, description="Versions of prompts used")
    
    @validator('analysis_content')
    def validate_content(cls, v):
        """Ensure analysis content is not empty."""
        if not v or not v.strip():
            raise ValueError("Analysis content must not be empty")
        return v


class WorkflowResult(BaseModel):
    """Final result from an investigation workflow."""
    status: str = Field(..., description="Workflow status (success/failed/skipped)")
    repo_name: str = Field(..., description="Name of the repository")
    repo_url: str = Field(..., description="URL of the repository")
    investigation_needed: bool = Field(..., description="Whether investigation was needed")
    investigation_reason: str = Field(..., description="Reason for investigation decision")
    analysis: Optional[RepositoryAnalysis] = Field(None, description="Analysis results if investigation was performed")
    error: Optional[str] = Field(None, description="Error message if workflow failed")
    execution_time_seconds: float = Field(..., ge=0, description="Total workflow execution time")
    metadata_saved: bool = Field(default=False, description="Whether metadata was saved to cache")
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid."""
        valid_statuses = ['success', 'failed', 'skipped', 'partial']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    
    @validator('error')
    def validate_error(cls, v, values):
        """Ensure error is present when status is failed."""
        if values.get('status') == 'failed' and not v:
            raise ValueError("Error message must be provided when status is 'failed'")
        return v
