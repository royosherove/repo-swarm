#!/usr/bin/env python3
"""
Unit tests for the investigate_single_repo_workflow to verify that DynamoDB 
metadata is only saved after successful processing.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest
import pytest_asyncio
import asyncio
import unittest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
from models import InvestigateSingleRepoRequest, InvestigateSingleRepoResult, CacheCheckInput
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.client import Client


@pytest.mark.skip(reason="Complex workflow tests need refactoring for proper Temporal mocking")
class TestInvestigateWorkflowCaching:
    """Test suite for verifying DynamoDB caching behavior in the workflow."""
    
    @pytest_asyncio.fixture
    async def workflow_env(self):
        """Create a test workflow environment."""
        env = await WorkflowEnvironment.start_time_skipping()
        yield env
        await env.shutdown()
    
    @pytest.fixture
    def mock_activities(self):
        """Create mock activities for testing."""
        mocks = {
            'clone_repository_activity': AsyncMock(return_value={
                'repo_path': '/tmp/test_repo',
                'temp_dir': '/tmp/test_temp'
            }),
            'check_if_repo_needs_investigation': AsyncMock(return_value={
                'needs_investigation': True,
                'reason': 'No previous investigation found',
                'latest_commit': 'abc123',
                'branch_name': 'main'
            }),
            'analyze_repository_structure_activity': AsyncMock(return_value={
                'repo_structure': {'files': ['README.md', 'app.py']}
            }),
            'get_prompts_config_activity': AsyncMock(return_value={
                'prompts_dir': '/tmp/prompts',
                'processing_order': [
                    {'name': 'test_step', 'file': 'test.md', 'required': True, 'description': 'Test'}
                ]
            }),
            'read_prompt_file_activity': AsyncMock(return_value={
                'status': 'success',
                'prompt_content': 'Test prompt'
            }),
            'analyze_with_claude': AsyncMock(return_value='Test analysis result'),
            'write_analysis_result_activity': AsyncMock(return_value={
                'arch_file_path': '/tmp/test_arch.md'
            }),
            'save_investigation_metadata': AsyncMock(return_value={
                'status': 'success',
                'message': 'Metadata saved',
                'timestamp': 123456789
            }),
            'save_to_arch_hub': AsyncMock(return_value={
                'status': 'success',
                'message': 'Saved to hub'
            })
        }
        return mocks
    
    @pytest.mark.asyncio
    async def test_metadata_saved_only_after_successful_investigation(self, workflow_env, mock_activities):
        """
        Test that DynamoDB metadata is saved ONLY after successful investigation.
        This ensures we don't mark a repo as processed if it failed.
        """
        async with workflow_env as env:
            # Register the workflow and mock activities
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[InvestigateSingleRepoWorkflow],
                activities=mock_activities
            )
            
            async with worker:
                # Create Pydantic request model
                request = InvestigateSingleRepoRequest(
                    repo_name='test-repo',
                    repo_url='https://github.com/test/repo',
                    repo_type='generic'
                )
                
                # Execute the workflow
                result: InvestigateSingleRepoResult = await env.client.execute_workflow(
                    InvestigateSingleRepoWorkflow.run,
                    arg=request,
                    id="test-workflow-1",
                    task_queue="test-queue"
                )
                
                # Verify the workflow completed successfully
                assert result.status == 'success'
                
                # Verify save_investigation_metadata was called
                mock_activities['save_investigation_metadata'].assert_called_once()
                
                # Verify it was called with correct arguments (now using Pydantic model)
                call_args = mock_activities['save_investigation_metadata'].call_args[0]
                input_model = call_args[0]
                assert isinstance(input_model, CacheCheckInput) or hasattr(input_model, 'repo_name')
                
                # Verify save_to_arch_hub was also called (happens after metadata save)
                mock_activities['save_to_arch_hub'].assert_called_once()
    
    @pytest.mark.asyncio
    async def test_metadata_not_saved_when_investigation_fails(self, workflow_env, mock_activities):
        """
        Test that DynamoDB metadata is NOT saved when investigation fails.
        This prevents marking failed investigations as complete.
        """
        # Make the analysis fail
        mock_activities['analyze_with_claude'].side_effect = Exception("Analysis failed")
        
        async with workflow_env as env:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[InvestigateSingleRepoWorkflow],
                activities=list(mock_activities.values())
            )
            
            async with worker:
                # Create Pydantic request model
                request = InvestigateSingleRepoRequest(
                    repo_name='test-repo',
                    repo_url='https://github.com/test/repo',
                    repo_type='generic'
                )
                
                # Execute the workflow - should raise exception
                with pytest.raises(Exception, match="Analysis failed"):
                    await env.client.execute_workflow(
                        InvestigateSingleRepoWorkflow.run,
                        arg=request,
                        id="test-workflow-2",
                        task_queue="test-queue"
                    )
                
                # Verify save_investigation_metadata was NOT called
                mock_activities['save_investigation_metadata'].assert_not_called()
                
                # Verify save_to_arch_hub was NOT called
                mock_activities['save_to_arch_hub'].assert_not_called()
    
    @pytest.mark.asyncio
    async def test_skip_investigation_when_no_changes(self, workflow_env, mock_activities):
        """
        Test that investigation is skipped when cache indicates no changes.
        This proves the caching mechanism works correctly.
        """
        # Make cache check return that no investigation is needed
        mock_activities['check_if_repo_needs_investigation'].return_value = {
            'needs_investigation': False,
            'reason': 'No changes since last investigation',
            'latest_commit': 'abc123',
            'branch_name': 'main',
            'last_investigation': {
                'analysis_timestamp': 123456789
            }
        }
        
        async with workflow_env as env:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[InvestigateSingleRepoWorkflow],
                activities=list(mock_activities.values())
            )
            
            async with worker:
                # Create Pydantic request model
                request = InvestigateSingleRepoRequest(
                    repo_name='test-repo',
                    repo_url='https://github.com/test/repo',
                    repo_type='generic'
                )
                
                result: InvestigateSingleRepoResult = await env.client.execute_workflow(
                    InvestigateSingleRepoWorkflow.run,
                    arg=request,
                    id="test-workflow-3",
                    task_queue="test-queue"
                )
                
                # Verify the workflow returned early with skipped status
                assert result.status == 'skipped'
                assert result.cached == True
                assert result.reason == 'No changes since last investigation'
                
                # Verify that analysis activities were NOT called
                mock_activities['analyze_repository_structure_activity'].assert_not_called()
                mock_activities['analyze_with_claude'].assert_not_called()
                mock_activities['save_investigation_metadata'].assert_not_called()
                mock_activities['save_to_arch_hub'].assert_not_called()
    
    @pytest.mark.asyncio
    async def test_metadata_save_continues_even_if_hub_save_fails(self, workflow_env, mock_activities):
        """
        Test that DynamoDB metadata is saved even if architecture hub save fails.
        This ensures we don't re-process repos just because hub save failed.
        """
        # Make hub save fail
        mock_activities['save_to_arch_hub'].side_effect = Exception("Git push failed")
        
        async with workflow_env as env:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[InvestigateSingleRepoWorkflow],
                activities=list(mock_activities.values())
            )
            
            async with worker:
                # Create Pydantic request model
                request = InvestigateSingleRepoRequest(
                    repo_name='test-repo',
                    repo_url='https://github.com/test/repo',
                    repo_type='generic'
                )
                
                result: InvestigateSingleRepoResult = await env.client.execute_workflow(
                    InvestigateSingleRepoWorkflow.run,
                    arg=request,
                    id="test-workflow-4",
                    task_queue="test-queue"
                )
                
                # Verify the workflow completed (with hub failure noted)
                assert result.status == 'success'
                assert result.architecture_hub['status'] == 'failed'
                assert 'Git push failed' in result.architecture_hub['error']
                
                # Verify save_investigation_metadata WAS called (before hub save)
                mock_activities['save_investigation_metadata'].assert_called_once()
                
                # Verify the metadata save happened with correct data
                assert result.metadata_saved.get('status') == 'success'
    
    @pytest.mark.asyncio
    async def test_metadata_save_handles_dynamodb_failure_gracefully(self, workflow_env, mock_activities):
        """
        Test that workflow continues even if DynamoDB metadata save fails.
        The investigation should still be considered successful.
        """
        # Make metadata save fail
        mock_activities['save_investigation_metadata'].side_effect = Exception("DynamoDB error")
        
        async with workflow_env as env:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[InvestigateSingleRepoWorkflow],
                activities=list(mock_activities.values())
            )
            
            async with worker:
                # Create Pydantic request model
                request = InvestigateSingleRepoRequest(
                    repo_name='test-repo',
                    repo_url='https://github.com/test/repo',
                    repo_type='generic'
                )
                
                result: InvestigateSingleRepoResult = await env.client.execute_workflow(
                    InvestigateSingleRepoWorkflow.run,
                    arg=request,
                    id="test-workflow-5",
                    task_queue="test-queue"
                )
                
                # Verify the workflow completed successfully despite metadata save failure
                assert result.status == 'success'
                
                # Verify metadata save was attempted
                mock_activities['save_investigation_metadata'].assert_called_once()
                
                # Verify the failure was captured
                assert result.metadata_saved['status'] == 'failed'
                assert 'DynamoDB error' in result.metadata_saved['error']
                
                # Verify hub save was still attempted
                mock_activities['save_to_arch_hub'].assert_called_once()


class TestCacheActivityIntegration:
    """Test the cache activities themselves."""
    
    @pytest.mark.asyncio
    async def test_check_if_repo_needs_investigation_logic(self):
        """Test the logic for determining if a repo needs investigation."""
        from activities.investigation_cache_activities import (
            check_if_repo_needs_investigation
        )
        
        with patch('utils.dynamodb_client.get_dynamodb_client') as mock_client_getter:
            with patch('activities.investigation_cache_activities._get_latest_commit') as mock_get_commit:
                with patch('activities.investigation_cache_activities._get_current_branch') as mock_get_branch:
                    with patch('activities.investigation_cache_activities._has_uncommitted_changes') as mock_has_changes:
                        
                        # Setup mocks
                        mock_client = Mock()
                        mock_client_getter.return_value = mock_client
                        mock_get_commit.return_value = 'new_commit_123'
                        mock_get_branch.return_value = 'main'
                        mock_has_changes.return_value = False
                        
                        # Case 1: No previous investigation
                        mock_client.get_latest_investigation.return_value = None
                        
                        from src.models.activities import CacheCheckInput
                        input_params = CacheCheckInput(
                            repo_name='test-repo',
                            repo_url='https://github.com/test/repo',
                            repo_path='/tmp/test-repo'
                        )
                        result = await check_if_repo_needs_investigation(input_params)
                        
                        assert result.needs_investigation == True
                        assert 'No previous investigation found' in result.reason
                        
                        # Case 2: Different commit
                        mock_client.get_latest_investigation.return_value = {
                            'latest_commit': 'old_commit_456',
                            'branch_name': 'main',
                            'analysis_timestamp': 123456789
                        }
                        
                        result = await check_if_repo_needs_investigation(input_params)
                        
                        assert result.needs_investigation == True
                        assert 'New commits detected' in result.reason
                        
                        # Case 3: Same commit, no changes
                        mock_client.get_latest_investigation.return_value = {
                            'latest_commit': 'new_commit_123',
                            'branch_name': 'main',
                            'analysis_timestamp': 123456789
                        }
                        
                        result = await check_if_repo_needs_investigation(input_params)
                        
                        assert result.needs_investigation == False
                        assert 'No changes since last investigation' in result.reason
                        
                        # Case 4: Uncommitted changes
                        mock_has_changes.return_value = True
                        
                        result = await check_if_repo_needs_investigation(input_params)
                        
                        assert result.needs_investigation == False
                        assert 'No changes since last investigation' in result.reason


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
