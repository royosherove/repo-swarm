"""
Activity input and output models.

These models define the parameters and return types for all activities
in the investigation system, providing type safety and validation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, HttpUrl


class CacheCheckInput(BaseModel):
    """Input parameters for check_if_repo_needs_investigation activity."""
    repo_name: str = Field(..., description="Name of the repository")
    repo_url: str = Field(..., description="URL of the repository")
    repo_path: str = Field(..., description="Local path to the cloned repository")
    prompt_versions: Optional[Dict[str, str]] = Field(None, description="Mapping of prompt names to versions")
    
    @validator('repo_name')
    def validate_repo_name(cls, v):
        """Ensure repo name is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository name must not be empty")
        return v.strip()
    
    @validator('repo_path')
    def validate_repo_path(cls, v):
        """Ensure repo path is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository path must not be empty")
        return v.strip()


class CacheCheckOutput(BaseModel):
    """Output from check_if_repo_needs_investigation activity."""
    needs_investigation: bool = Field(..., description="Whether investigation is needed")
    reason: str = Field(..., description="Reason for the decision")
    latest_commit: Optional[str] = Field(None, description="Current commit SHA")
    branch_name: Optional[str] = Field(None, description="Current branch name")
    last_investigation: Optional[Dict[str, Any]] = Field(None, description="Previous investigation metadata")


class SaveMetadataInput(BaseModel):
    """Input parameters for save_investigation_metadata activity."""
    repo_name: str = Field(..., description="Name of the repository")
    repo_url: str = Field(..., description="URL of the repository")
    latest_commit: str = Field(..., description="SHA of the commit that was investigated")
    branch_name: str = Field(..., description="Name of the branch that was investigated")
    analysis_summary: Optional[Dict[str, Any]] = Field(None, description="Summary of the analysis results")
    prompt_versions: Optional[Dict[str, str]] = Field(None, description="Mapping of prompt names to versions")
    ttl_days: int = Field(default=90, ge=1, le=365, description="Time-to-live in days")
    
    @validator('repo_name')
    def validate_repo_name(cls, v):
        """Ensure repo name is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository name must not be empty")
        return v.strip()
    
    @validator('latest_commit')
    def validate_commit(cls, v):
        """Ensure commit SHA is valid."""
        if not v or not v.strip():
            raise ValueError("Commit SHA must not be empty")
        # Basic validation for commit SHA format
        if len(v.strip()) < 7:
            raise ValueError("Commit SHA must be at least 7 characters")
        return v.strip()
    
    @validator('branch_name')
    def validate_branch(cls, v):
        """Ensure branch name is not empty."""
        if not v or not v.strip():
            raise ValueError("Branch name must not be empty")
        return v.strip()


class SaveMetadataOutput(BaseModel):
    """Output from save_investigation_metadata activity."""
    status: str = Field(..., description="Status of the save operation (success/error)")
    message: str = Field(..., description="Description of the result")
    timestamp: Optional[float] = Field(None, description="Unix timestamp when saved")
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid."""
        if v not in ['success', 'error']:
            raise ValueError("Status must be 'success' or 'error'")
        return v


class AnalyzeStructureInput(BaseModel):
    """Input parameters for analyze_repository_structure activity."""
    repo_path: str = Field(..., description="Local path to the repository")
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum depth to analyze")
    include_hidden: bool = Field(default=False, description="Whether to include hidden files/directories")
    
    @validator('repo_path')
    def validate_repo_path(cls, v):
        """Ensure repo path is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository path must not be empty")
        return v.strip()


class AnalyzeStructureOutput(BaseModel):
    """Output from analyze_repository_structure activity."""
    repo_type: str = Field(..., description="Detected repository type")
    structure: Dict[str, Any] = Field(..., description="Repository structure data")
    file_count: int = Field(..., ge=0, description="Total number of files")
    directory_count: int = Field(..., ge=0, description="Total number of directories")
    languages: List[str] = Field(default_factory=list, description="Detected programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Detected frameworks")
    
    @validator('repo_type')
    def validate_repo_type(cls, v):
        """Ensure repo type is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository type must not be empty")
        return v.strip()


class PromptContextDict(BaseModel):
    """Dictionary representation of PromptContext for activity parameters."""
    repo_name: str = Field(..., description="Name of the repository")
    step_name: str = Field(..., description="Name of the analysis step")
    data_reference_key: Optional[str] = Field(None, description="Reference key for prompt data")
    context_reference_keys: List[str] = Field(default_factory=list, description="Reference keys for context data")
    result_reference_key: Optional[str] = Field(None, description="Reference key for result data")
    prompt_version: str = Field(default="1", description="Version of the prompt being used")
    
    @validator('repo_name')
    def validate_repo_name(cls, v):
        """Ensure repo name is not empty."""
        if not v or not v.strip():
            raise ValueError("Repository name must not be empty")
        return v.strip()
    
    @validator('step_name')
    def validate_step_name(cls, v):
        """Ensure step name is not empty."""
        if not v or not v.strip():
            raise ValueError("Step name must not be empty")
        return v.strip()
    
    @validator('prompt_version')
    def validate_prompt_version(cls, v):
        """Ensure prompt version is not empty."""
        if not v or not v.strip():
            raise ValueError("Prompt version must not be empty")
        return v.strip()
    
    @validator('context_reference_keys')
    def validate_context_reference_keys(cls, v):
        """Ensure context reference keys list doesn't contain None values."""
        if v:
            # Filter out None values and empty strings
            cleaned = [key for key in v if key and isinstance(key, str) and key.strip()]
            if len(cleaned) != len(v):
                # Log warning but don't fail - just clean the list
                import logging
                logging.warning(f"Filtered out {len(v) - len(cleaned)} invalid context reference keys")
            return cleaned
        return v


class ClaudeConfigOverrides(BaseModel):
    """Configuration overrides for Claude API calls."""
    claude_model: Optional[str] = Field(None, description="Claude model to use (e.g., claude-3-sonnet-20240229)")
    max_tokens: Optional[int] = Field(None, ge=1, le=200000, description="Maximum tokens for Claude response")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="Temperature for Claude response")
    
    @validator('claude_model')
    def validate_claude_model(cls, v):
        """Ensure Claude model is valid if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Claude model must not be empty if provided")
        return v.strip() if v else v


class AnalyzeWithClaudeInput(BaseModel):
    """Input parameters for analyze_with_claude_context activity."""
    context_dict: PromptContextDict = Field(..., description="Dictionary representation of PromptContext")
    config_overrides: Optional[ClaudeConfigOverrides] = Field(None, description="Optional configuration overrides for Claude API")
    latest_commit: Optional[str] = Field(None, description="Current commit SHA for cache checking")
    
    @validator('latest_commit')
    def validate_commit(cls, v):
        """Ensure commit SHA is valid if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Commit SHA must not be empty if provided")
        # Basic validation for commit SHA format
        if v is not None and len(v.strip()) < 7:
            raise ValueError("Commit SHA must be at least 7 characters")
        return v.strip() if v else v


class AnalyzeWithClaudeOutput(BaseModel):
    """Output from analyze_with_claude_context activity."""
    status: str = Field(..., description="Status of the analysis (success/error)")
    context: PromptContextDict = Field(..., description="Updated context dictionary with result reference")
    result_length: int = Field(..., ge=0, description="Length of the analysis result in characters")
    cached: bool = Field(..., description="Whether the result was served from cache")
    cache_reason: Optional[str] = Field(None, description="Reason for cache hit/miss if applicable")
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid."""
        if v not in ['success', 'error']:
            raise ValueError("Status must be 'success' or 'error'")
        return v
    
    @validator('cache_reason', always=True)
    def validate_cache_reason(cls, v, values):
        """Ensure cache reason is provided when result is cached."""
        if values.get('cached') is True and (not v or not v.strip() if v else True):
            raise ValueError("Cache reason must be provided when result is cached")
        return v
