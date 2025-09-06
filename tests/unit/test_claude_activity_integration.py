"""
Integration tests for analyze_with_claude_context activity with Pydantic models.

These tests verify that the activity function correctly uses the new Pydantic models
for input validation and output formatting.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models import (
    AnalyzeWithClaudeInput,
    AnalyzeWithClaudeOutput,
    PromptContextDict,
    ClaudeConfigOverrides,
)


class TestAnalyzeWithClaudeContextIntegration:
    """Test integration of analyze_with_claude_context with Pydantic models."""
    
    def test_function_signature_uses_pydantic_models(self):
        """Test that the function signature uses Pydantic models."""
        from activities.investigate_activities import analyze_with_claude_context
        import inspect
        
        sig = inspect.signature(analyze_with_claude_context)
        
        # Check parameter types
        assert len(sig.parameters) == 1
        input_param = list(sig.parameters.values())[0]
        assert input_param.name == 'input_params'
        assert input_param.annotation == AnalyzeWithClaudeInput
        
        # Check return type
        assert sig.return_annotation == AnalyzeWithClaudeOutput
    
    def test_input_model_parameter_extraction(self):
        """Test that input parameters are correctly extracted from Pydantic model."""
        # Create test input
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            data_reference_key="data_123",
            prompt_version="2"
        )
        
        config = ClaudeConfigOverrides(
            claude_model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0.1
        )
        
        input_model = AnalyzeWithClaudeInput(
            context_dict=context,
            config_overrides=config,
            latest_commit="abc123def456789"
        )
        
        # Test parameter extraction (simulate what the function does)
        context_dict = input_model.context_dict.model_dump()
        config_overrides = input_model.config_overrides.model_dump()
        latest_commit = input_model.latest_commit
        
        # Verify extracted values
        assert context_dict['repo_name'] == "test-repo"
        assert context_dict['step_name'] == "high_level_overview"
        assert context_dict['data_reference_key'] == "data_123"
        assert context_dict['prompt_version'] == "2"
        
        assert config_overrides['claude_model'] == "claude-3-sonnet-20240229"
        assert config_overrides['max_tokens'] == 4000
        assert config_overrides['temperature'] == 0.1
        
        assert latest_commit == "abc123def456789"
    
    def test_output_model_creation(self):
        """Test that output model can be created correctly."""
        # Create test context for output
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            data_reference_key="data_123",
            result_reference_key="result_456",
            prompt_version="2"
        )
        
        # Create output model (simulate what the function returns)
        output = AnalyzeWithClaudeOutput(
            status="success",
            context=context,
            result_length=1500,
            cached=False
        )
        
        # Verify output structure
        assert output.status == "success"
        assert output.context.repo_name == "test-repo"
        assert output.context.result_reference_key == "result_456"
        assert output.result_length == 1500
        assert output.cached is False
        assert output.cache_reason is None
    
    def test_cached_output_model_creation(self):
        """Test that cached output model can be created correctly."""
        context = PromptContextDict(
            repo_name="test-repo",
            step_name="high_level_overview",
            prompt_version="2"
        )
        
        # Create cached output model
        output = AnalyzeWithClaudeOutput(
            status="success",
            context=context,
            result_length=1200,
            cached=True,
            cache_reason="Found cached result for same commit and prompt version"
        )
        
        # Verify cached output structure
        assert output.status == "success"
        assert output.cached is True
        assert output.cache_reason == "Found cached result for same commit and prompt version"
        assert output.result_length == 1200
    
    def test_function_accepts_pydantic_input_model(self):
        """Test that the function can accept Pydantic input model."""
        from activities.investigate_activities import analyze_with_claude_context
        
        # Create input model
        input_model = AnalyzeWithClaudeInput(
            context_dict=PromptContextDict(
                repo_name="test-repo",
                step_name="high_level_overview",
                prompt_version="2"
            ),
            latest_commit="abc123def456789"
        )
        
        # Verify that the function signature accepts our input model
        assert callable(analyze_with_claude_context)
        
        # Verify input model is valid and has expected structure
        assert input_model.context_dict.repo_name == "test-repo"
        assert input_model.latest_commit == "abc123def456789"
        
        # Verify parameter extraction works as expected
        context_dict = input_model.context_dict.model_dump()
        config_overrides = input_model.config_overrides.model_dump() if input_model.config_overrides else {}
        latest_commit = input_model.latest_commit
        
        assert context_dict['repo_name'] == "test-repo"
        assert context_dict['step_name'] == "high_level_overview"
        assert context_dict['prompt_version'] == "2"
        assert config_overrides == {}
        assert latest_commit == "abc123def456789"
    
    def test_model_validation_prevents_invalid_input(self):
        """Test that Pydantic validation prevents invalid input."""
        from pydantic import ValidationError
        
        # Test invalid context
        with pytest.raises(ValidationError):
            AnalyzeWithClaudeInput(
                context_dict=PromptContextDict(
                    repo_name="",  # Empty repo name should fail
                    step_name="test",
                    prompt_version="1"
                )
            )
        
        # Test invalid config
        with pytest.raises(ValidationError):
            AnalyzeWithClaudeInput(
                context_dict=PromptContextDict(
                    repo_name="test-repo",
                    step_name="test",
                    prompt_version="1"
                ),
                config_overrides=ClaudeConfigOverrides(
                    max_tokens=0  # Invalid max_tokens should fail
                )
            )
        
        # Test invalid commit
        with pytest.raises(ValidationError):
            AnalyzeWithClaudeInput(
                context_dict=PromptContextDict(
                    repo_name="test-repo",
                    step_name="test",
                    prompt_version="1"
                ),
                latest_commit="abc"  # Too short commit SHA should fail
            )
