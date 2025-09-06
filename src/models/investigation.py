"""
Core investigation models for repository analysis.

These models define the fundamental data structures used throughout
the investigation system for tracking repository state, decisions,
and metadata.
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, validator


class PromptMetadata(BaseModel):
    """Metadata about prompts used in an investigation."""
    count: int = Field(..., ge=0, description="Number of prompts used")
    versions: Dict[str, str] = Field(default_factory=dict, description="Mapping of prompt names to versions")
    
    @validator('versions')
    def validate_versions(cls, v):
        """Ensure all version values are non-empty strings."""
        for prompt_name, version in v.items():
            if not isinstance(version, str) or not version.strip():
                raise ValueError(f"Version for prompt '{prompt_name}' must be a non-empty string")
        return v


class InvestigationMetadata(BaseModel):
    """Complete investigation metadata stored in the cache."""
    latest_commit: Optional[str] = Field(None, description="SHA of the latest commit investigated")
    branch_name: str = Field(..., description="Name of the branch investigated")
    analysis_timestamp: float = Field(..., description="Unix timestamp of when the analysis was performed")
    repository_name: Optional[str] = Field(None, description="Name of the repository")
    repository_url: Optional[str] = Field(None, description="URL of the repository")
    analysis_type: str = Field(default="investigation", description="Type of analysis performed")
    prompt_metadata: Optional[PromptMetadata] = Field(None, description="Metadata about prompts used")
    analysis_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional analysis data")
    
    @validator('latest_commit')
    def validate_commit_sha(cls, v):
        """Ensure commit SHA is a non-empty string if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Commit SHA must be a non-empty string if provided")
        return v.strip() if v else v
    
    @validator('branch_name')
    def validate_branch_name(cls, v):
        """Ensure branch name is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Branch name must be a non-empty string")
        return v.strip()
    
    @validator('analysis_timestamp')
    def validate_timestamp(cls, v):
        """Ensure timestamp is non-negative (allow zero for edge cases)."""
        if v < 0:
            raise ValueError("Analysis timestamp must be non-negative")
        return v


class InvestigationDecision(BaseModel):
    """Result of checking if a repository needs investigation."""
    needs_investigation: bool = Field(..., description="Whether investigation is needed")
    reason: str = Field(..., description="Reason for the decision")
    latest_commit: Optional[str] = Field(None, description="Latest commit SHA")
    branch_name: Optional[str] = Field(None, description="Branch name")
    last_investigation: Optional[Any] = Field(None, description="Previous investigation metadata")
    
    @validator('reason')
    def validate_reason(cls, v):
        """Ensure reason is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Reason must be a non-empty string")
        return v.strip()


class RepositoryState(BaseModel):
    """Current state of a repository."""
    commit_sha: str = Field(..., description="Current commit SHA")
    branch_name: str = Field(..., description="Current branch name")
    has_uncommitted_changes: bool = Field(..., description="Whether there are uncommitted changes")
    
    @validator('commit_sha')
    def validate_commit_sha(cls, v):
        """Ensure commit SHA is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Commit SHA must be a non-empty string")
        return v.strip()
    
    @validator('branch_name')
    def validate_branch_name(cls, v):
        """Ensure branch name is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Branch name must be a non-empty string")
        return v.strip()
