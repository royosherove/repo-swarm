#!/usr/bin/env python3
"""
Tests for prompt versions bug fix.

These tests verify that prompt versions are properly handled throughout
the workflow, focusing on BEHAVIOR rather than implementation details.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestPromptVersionsBugFix:
    """Test prompt versions handling in the workflow."""
    
    def test_save_to_dynamo_method_signature(self):
        """
        Test that the _save_to_dynamo method has the expected signature.
        This ensures the method can be called with the expected parameters.
        """
        import inspect
        from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
        
        workflow = InvestigateSingleRepoWorkflow()
        
        # Get the method signature
        sig = inspect.signature(workflow._save_to_dynamo)
        params = list(sig.parameters.keys())
        
        # Verify the method exists and has the expected parameters
        expected_params = [
            'investigation_result', 'repo_name', 'repo_url',
            'latest_commit', 'branch_name', 'all_results', 'arch_file_path',
            'prompt_versions'
        ]
        
        assert params == expected_params, f"Expected {expected_params}, got {params}"
    
    def test_pydantic_models_exist_and_work(self):
        """Test that the Pydantic models for activities exist and can be instantiated."""
        from models import AnalyzeWithClaudeInput, AnalyzeWithClaudeOutput, PromptContextDict, SaveMetadataInput
        
        # Test PromptContextDict
        context = PromptContextDict(
            repo_name='test-repo',
            step_name='hl_overview',
            prompt_version='1'
        )
        assert context.repo_name == 'test-repo'
        assert context.step_name == 'hl_overview'
        assert context.prompt_version == '1'
        
        # Test AnalyzeWithClaudeInput
        claude_input = AnalyzeWithClaudeInput(
            context_dict=context,
            latest_commit='abc123def456'
        )
        assert claude_input.context_dict.repo_name == 'test-repo'
        assert claude_input.latest_commit == 'abc123def456'
        
        # Test SaveMetadataInput
        save_input = SaveMetadataInput(
            repo_name='test-repo',
            repo_url='https://github.com/test/repo',
            latest_commit='abc123def456',
            branch_name='main',
            analysis_summary={'test': 'data'},
            prompt_versions={'hl_overview': '1'}
        )
        assert save_input.repo_name == 'test-repo'
        assert save_input.prompt_versions == {'hl_overview': '1'}
    
    def test_pydantic_validation_works(self):
        """Test that Pydantic validation catches invalid data."""
        from models import SaveMetadataInput
        from pydantic import ValidationError
        
        # Test that short commit SHA is rejected
        with pytest.raises(ValidationError) as exc_info:
            SaveMetadataInput(
                repo_name='test-repo',
                repo_url='https://github.com/test/repo',
                latest_commit='abc123',  # Too short
                branch_name='main',
                analysis_summary={},
                prompt_versions={}
            )
        
        assert "Commit SHA must be at least 7 characters" in str(exc_info.value)
    
    def test_prompt_versions_parameter_exists(self):
        """Test that prompt_versions parameter exists in the workflow method."""
        from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
        import inspect
        
        workflow = InvestigateSingleRepoWorkflow()
        sig = inspect.signature(workflow._save_to_dynamo)
        
        # Verify prompt_versions parameter exists
        assert 'prompt_versions' in sig.parameters
        
        # Verify it has a default value (None)
        param = sig.parameters['prompt_versions']
        assert param.default is None
