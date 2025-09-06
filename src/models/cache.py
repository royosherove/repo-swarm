"""
Cache-specific models for storing and retrieving analysis results.

These models define the structures used for caching analysis results
and prompt outputs at various levels.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class AnalysisResult(BaseModel):
    """Structure for cached analysis results."""
    reference_key: str = Field(..., description="Unique reference key for the result")
    result_content: str = Field(..., description="The analysis result content")
    step_name: Optional[str] = Field(None, description="Name of the analysis step")
    timestamp: float = Field(..., description="Unix timestamp when result was saved")
    ttl_minutes: int = Field(default=60, ge=1, description="Time-to-live in minutes")
    
    @validator('reference_key')
    def validate_reference_key(cls, v):
        """Ensure reference key follows expected format."""
        if not v or not v.strip():
            raise ValueError("Reference key must be a non-empty string")
        # Expected format: repo_name#step_name#commit_sha#version
        parts = v.split('#')
        if len(parts) < 3:
            raise ValueError("Reference key must contain at least repo_name#step_name#commit_sha")
        return v.strip()


class CacheCheckResult(BaseModel):
    """Result of checking if a repository needs investigation."""
    needs_investigation: bool = Field(..., description="Whether investigation is needed")
    reason: str = Field(..., description="Reason for the decision")
    latest_commit: Optional[str] = Field(None, description="Current commit SHA")
    branch_name: Optional[str] = Field(None, description="Current branch name")
    last_investigation: Optional[Dict[str, Any]] = Field(None, description="Previous investigation metadata")
    
    @validator('reason')
    def validate_reason(cls, v):
        """Ensure reason is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Reason must be a non-empty string")
        return v.strip()


class PromptCacheResult(BaseModel):
    """Result of checking prompt-level cache."""
    needs_analysis: bool = Field(..., description="Whether the prompt needs to be analyzed")
    cached_result_key: Optional[str] = Field(None, description="Reference key to cached result if available")
    cached_result: Optional[str] = Field(None, description="The cached content if available")
    reason: str = Field(..., description="Explanation of the decision")
    version: str = Field(default="1", description="Version of the cached result")
    
    @validator('reason')
    def validate_reason(cls, v):
        """Ensure reason is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Reason must be a non-empty string")
        return v.strip()
    
    @validator('version')
    def validate_version(cls, v):
        """Ensure version is a non-empty string."""
        if not v or not v.strip():
            raise ValueError("Version must be a non-empty string")
        return v.strip()
