"""
Tests for Claude analysis activity Pydantic models.

These tests ensure that the models for analyze_with_claude_context activity
provide proper validation and type safety.
"""

import pytest
from pydantic import ValidationError

from src.models import (
    AnalyzeWithClaudeInput,
    AnalyzeWithClaudeOutput,
    PromptContextDict,
    ClaudeConfigOverrides,
)


class TestPromptContextDict:
    """Test PromptContextDict model validation."""
    
    def test_valid_prompt_context_dict_creation(self):
        """Test creating a valid PromptContextDict."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="2"
        )
        
        assert context.repo_name == "test-repo"
        assert context.step_name == "high_level_overview"
        assert context.prompt_version == "2"
        assert context.data_reference_key is None
        assert context.context_reference_keys == []
        assert context.result_reference_key is None
    
    def test_prompt_context_dict_with_all_fields(self):
        """Test creating PromptContextDict with all fields."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            data_reference_key="data_key_123",
            context_reference_keys=["ctx_key_1", "ctx_key_2"],
            result_reference_key="result_key_456",
            prompt_version="3"
        )
        
        assert context.data_reference_key == "data_key_123"
        assert context.context_reference_keys == ["ctx_key_1", "ctx_key_2"]
        assert context.result_reference_key == "result_key_456"
    
    def test_empty_repo_name_raises_validation_error(self):
        """Test that empty repo_name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PromptContextDict(
                repo_name="",
                step_name="test_step",
                prompt_version="1"
            )
        
        assert "Repository name must not be empty" in str(exc_info.value)
    
    def test_empty_step_name_raises_validation_error(self):
        """Test that empty step_name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PromptContextDict(
                repo_name="test-repo",
                step_name="",
                prompt_version="1"
            )
        
        assert "Step name must not be empty" in str(exc_info.value)
    
    def test_empty_prompt_version_raises_validation_error(self):
        """Test that empty prompt_version raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PromptContextDict(
                repo_name="test-repo",
                step_name="test_step",
                prompt_version=""
            )
        
        assert "Prompt version must not be empty" in str(exc_info.value)


class TestClaudeConfigOverrides:
    """Test ClaudeConfigOverrides model validation."""
    
    def test_valid_config_overrides_creation(self):
        """Test creating valid ClaudeConfigOverrides."""
        config = ClaudeConfigOverrides(
            claude_model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0.1
        )
        
        assert config.claude_model == "claude-3-sonnet-20240229"
        assert config.max_tokens == 4000
        assert config.temperature == 0.1
    
    def test_empty_config_overrides_creation(self):
        """Test creating empty ClaudeConfigOverrides."""
        config = ClaudeConfigOverrides()
        
        assert config.claude_model is None
        assert config.max_tokens is None
        assert config.temperature is None
    
    def test_invalid_max_tokens_raises_validation_error(self):
        """Test that invalid max_tokens raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeConfigOverrides(max_tokens=0)
        
        assert "Input should be greater than or equal to 1" in str(exc_info.value)
    
    def test_invalid_temperature_raises_validation_error(self):
        """Test that invalid temperature raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeConfigOverrides(temperature=1.5)
        
        assert "Input should be less than or equal to 1" in str(exc_info.value)
    
    def test_empty_claude_model_raises_validation_error(self):
        """Test that empty claude_model raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ClaudeConfigOverrides(claude_model="")
        
        assert "Claude model must not be empty if provided" in str(exc_info.value)


class TestAnalyzeWithClaudeInput:
    """Test AnalyzeWithClaudeInput model validation."""
    
    def test_valid_input_creation(self):
        """Test creating valid AnalyzeWithClaudeInput."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        
        input_model = AnalyzeWithClaudeInput(
            context_dict=context,
            latest_commit="abc123def456789"
        )
        
        assert input_model.context_dict == context
        assert input_model.config_overrides is None
        assert input_model.latest_commit == "abc123def456789"
    
    def test_input_with_config_overrides(self):
        """Test creating AnalyzeWithClaudeInput with config overrides."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        config = ClaudeConfigOverrides(
            claude_model="claude-3-sonnet-20240229",
            max_tokens=4000
        )
        
        input_model = AnalyzeWithClaudeInput(
            context_dict=context,
            config_overrides=config,
            latest_commit="abc123def456789"
        )
        
        assert input_model.config_overrides == config
    
    def test_short_commit_sha_raises_validation_error(self):
        """Test that short commit SHA raises ValidationError."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeWithClaudeInput(
                context_dict=context,
                latest_commit="abc123"
            )
        
        assert "Commit SHA must be at least 7 characters" in str(exc_info.value)
    
    def test_empty_commit_sha_raises_validation_error(self):
        """Test that empty commit SHA raises ValidationError."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeWithClaudeInput(
                context_dict=context,
                latest_commit=""
            )
        
        assert "Commit SHA must not be empty if provided" in str(exc_info.value)


class TestAnalyzeWithClaudeOutput:
    """Test AnalyzeWithClaudeOutput model validation."""
    
    def test_valid_output_creation(self):
        """Test creating valid AnalyzeWithClaudeOutput."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        
        output_model = AnalyzeWithClaudeOutput(
            status="success",
            context=context,
            result_length=1500,
            cached=False
        )
        
        assert output_model.status == "success"
        assert output_model.context == context
        assert output_model.result_length == 1500
        assert output_model.cached is False
        assert output_model.cache_reason is None
    
    def test_cached_output_with_reason(self):
        """Test creating cached AnalyzeWithClaudeOutput with cache reason."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        
        output_model = AnalyzeWithClaudeOutput(
            status="success",
            context=context,
            result_length=1500,
            cached=True,
            cache_reason="Found cached result for same commit and prompt version"
        )
        
        assert output_model.cached is True
        assert output_model.cache_reason == "Found cached result for same commit and prompt version"
    
    def test_invalid_status_raises_validation_error(self):
        """Test that invalid status raises ValidationError."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeWithClaudeOutput(
                status="invalid_status",
                context=context,
                result_length=1500,
                cached=False
            )
        
        assert "Status must be 'success' or 'error'" in str(exc_info.value)
    
    def test_negative_result_length_raises_validation_error(self):
        """Test that negative result_length raises ValidationError."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeWithClaudeOutput(
                status="success",
                context=context,
                result_length=-100,
                cached=False
            )
        
        assert "Input should be greater than or equal to 0" in str(exc_info.value)
    
    def test_cached_without_reason_raises_validation_error(self):
        """Test that cached=True without cache_reason raises ValidationError."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="1"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeWithClaudeOutput(
                status="success",
                context=context,
                result_length=1500,
                cached=True  # No cache_reason provided
            )
        
        assert "Cache reason must be provided when result is cached" in str(exc_info.value)


class TestModelIntegration:
    """Test integration between models."""
    
    def test_full_workflow_model_creation(self):
        """Test creating models for a complete workflow."""
        # Create context
        context = PromptContextDict(
            repo_name="my-awesome-repo",
            step_name="architecture_analysis",
            data_reference_key="data_abc123",
            context_reference_keys=["ctx_1", "ctx_2"],
            prompt_version="2"
        )
        
        # Create config overrides
        config = ClaudeConfigOverrides(
            claude_model="claude-3-sonnet-20240229",
            max_tokens=8000,
            temperature=0.2
        )
        
        # Create input
        input_model = AnalyzeWithClaudeInput(
            context_dict=context,
            config_overrides=config,
            latest_commit="abc123def456789012345"
        )
        
        # Create successful output
        updated_context = PromptContextDict(
            repo_name="my-awesome-repo",
            step_name="architecture_analysis",
            data_reference_key="data_abc123",
            context_reference_keys=["ctx_1", "ctx_2"],
            result_reference_key="result_xyz789",
            prompt_version="2"
        )
        
        output_model = AnalyzeWithClaudeOutput(
            status="success",
            context=updated_context,
            result_length=2500,
            cached=False
        )
        
        # Verify all models are valid
        assert input_model.context_dict.repo_name == "my-awesome-repo"
        assert input_model.config_overrides.claude_model == "claude-3-sonnet-20240229"
        assert output_model.context.result_reference_key == "result_xyz789"
        assert output_model.result_length == 2500
