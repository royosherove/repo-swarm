"""
Unit tests for the InvestigationCache class.

These tests verify the caching logic for determining when a repository
needs investigation and managing investigation metadata storage.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from src.activities.investigation_cache import (
    InvestigationCache,
    RepositoryState,
    InvestigationDecision
)


class TestInvestigationCache(unittest.TestCase):
    """Test suite for InvestigationCache class following Art of Unit Testing principles."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage_client = Mock()
        self.cache = InvestigationCache(self.mock_storage_client)
        
        # Common test data
        self.repo_name = "test-repo"
        self.repo_url = "https://github.com/test/test-repo"
        self.current_commit = "abc123def456789012345678901234567890abcd"
        self.current_branch = "main"
        
        self.current_state = RepositoryState(
            commit_sha=self.current_commit,
            branch_name=self.current_branch,
            has_uncommitted_changes=False
        )
        
        # Sample last investigation data
        self.last_investigation = {
            'latest_commit': self.current_commit,
            'branch_name': self.current_branch,
            'analysis_timestamp': datetime.now(timezone.utc).timestamp(),
            'repository_name': self.repo_name,
            'repository_url': self.repo_url
        }
    
    def test_check_needs_investigation_when_no_previous_investigation_should_return_needs_investigation(self):
        """Test that repos with no previous investigation need investigation."""
        # Arrange
        self.mock_storage_client.get_latest_investigation.return_value = None
        
        # Act
        decision = self.cache.check_needs_investigation(self.repo_name, self.current_state)
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertEqual(decision.reason, "No previous investigation found")
        self.assertEqual(decision.latest_commit, self.current_commit)
        self.assertEqual(decision.branch_name, self.current_branch)
        self.assertIsNone(decision.last_investigation)
        self.mock_storage_client.get_latest_investigation.assert_called_once_with(self.repo_name)
    
    def test_check_needs_investigation_when_storage_error_should_return_needs_investigation_with_error_reason(self):
        """Test that storage errors result in investigation with appropriate error message."""
        # Arrange
        error_message = "Connection timeout"
        self.mock_storage_client.get_latest_investigation.side_effect = Exception(error_message)
        
        # Act
        decision = self.cache.check_needs_investigation(self.repo_name, self.current_state)
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertIn("storage error", decision.reason)
        self.assertIn(error_message, decision.reason)
        self.assertEqual(decision.latest_commit, self.current_commit)
        self.assertEqual(decision.branch_name, self.current_branch)
        self.assertIsNone(decision.last_investigation)
    
    def test_check_needs_investigation_when_uncommitted_changes_should_return_needs_investigation(self):
        """Test that uncommitted changes do NOT trigger investigation (feature disabled)."""
        # Arrange
        self.mock_storage_client.get_latest_investigation.return_value = self.last_investigation
        state_with_changes = RepositoryState(
            commit_sha=self.current_commit,
            branch_name=self.current_branch,
            has_uncommitted_changes=True
        )
        
        # Act
        decision = self.cache.check_needs_investigation(self.repo_name, state_with_changes)
        
        # Assert - uncommitted changes should NOT trigger investigation
        self.assertFalse(decision.needs_investigation)
        self.assertIn("No changes since last investigation", decision.reason)
        self.assertEqual(decision.last_investigation, self.last_investigation)
    
    def test_check_needs_investigation_when_new_commit_should_return_needs_investigation(self):
        """Test that new commits trigger investigation."""
        # Arrange
        old_commit = "def456789012345678901234567890abcdef123456"
        self.last_investigation['latest_commit'] = old_commit
        self.mock_storage_client.get_latest_investigation.return_value = self.last_investigation
        
        # Act
        decision = self.cache.check_needs_investigation(self.repo_name, self.current_state)
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertIn("New commits detected", decision.reason)
        self.assertIn(self.current_commit[:8], decision.reason)
        self.assertIn(old_commit[:8], decision.reason)
        self.assertEqual(decision.last_investigation, self.last_investigation)
    
    def test_check_needs_investigation_when_branch_changed_should_return_needs_investigation(self):
        """Test that branch changes trigger investigation."""
        # Arrange
        old_branch = "develop"
        self.last_investigation['branch_name'] = old_branch
        self.mock_storage_client.get_latest_investigation.return_value = self.last_investigation
        
        # Act
        decision = self.cache.check_needs_investigation(self.repo_name, self.current_state)
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertIn("Branch changed", decision.reason)
        self.assertIn(self.current_branch, decision.reason)
        self.assertIn(old_branch, decision.reason)
        self.assertEqual(decision.last_investigation, self.last_investigation)
    
    def test_check_needs_investigation_when_no_changes_should_return_no_investigation_needed(self):
        """Test that unchanged repos don't need investigation."""
        # Arrange
        self.mock_storage_client.get_latest_investigation.return_value = self.last_investigation
        
        # Act
        decision = self.cache.check_needs_investigation(self.repo_name, self.current_state)
        
        # Assert
        self.assertFalse(decision.needs_investigation)
        self.assertIn("No changes since last investigation", decision.reason)
        self.assertEqual(decision.latest_commit, self.current_commit)
        self.assertEqual(decision.branch_name, self.current_branch)
        self.assertEqual(decision.last_investigation, self.last_investigation)
    
    def test_check_needs_investigation_when_missing_commit_in_last_investigation_should_return_needs_investigation(self):
        """Test handling of incomplete last investigation data."""
        # Arrange
        incomplete_investigation = {
            'branch_name': self.current_branch,
            'analysis_timestamp': datetime.now(timezone.utc).timestamp()
        }
        self.mock_storage_client.get_latest_investigation.return_value = incomplete_investigation
        
        # Act
        decision = self.cache.check_needs_investigation(self.repo_name, self.current_state)
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertIn("New commits detected", decision.reason)
        self.assertIn("unknown", decision.reason)
    
    def test_save_investigation_metadata_when_successful_should_return_success_status(self):
        """Test successful saving of investigation metadata."""
        # Arrange
        timestamp = datetime.now(timezone.utc).timestamp()
        saved_item = {'analysis_timestamp': timestamp}
        self.mock_storage_client.save_investigation_metadata.return_value = saved_item
        analysis_summary = {"files_analyzed": 10, "issues_found": 2}
        
        # Act
        result = self.cache.save_investigation_metadata(
            repo_name=self.repo_name,
            repo_url=self.repo_url,
            commit_sha=self.current_commit,
            branch_name=self.current_branch,
            analysis_summary=analysis_summary,
            ttl_days=90
        )
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertIn(self.repo_name, result["message"])
        self.assertEqual(result["timestamp"], timestamp)
        
        self.mock_storage_client.save_investigation_metadata.assert_called_once_with(
            repository_name=self.repo_name,
            repository_url=self.repo_url,
            latest_commit=self.current_commit,
            branch_name=self.current_branch,
            analysis_type="investigation",
            analysis_data=analysis_summary,
            ttl_days=90
        )
    
    def test_save_investigation_metadata_when_storage_error_should_return_error_status(self):
        """Test error handling when saving metadata fails."""
        # Arrange
        error_message = "DynamoDB write throttled"
        self.mock_storage_client.save_investigation_metadata.side_effect = Exception(error_message)
        
        # Act
        result = self.cache.save_investigation_metadata(
            repo_name=self.repo_name,
            repo_url=self.repo_url,
            commit_sha=self.current_commit,
            branch_name=self.current_branch
        )
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertIn(error_message, result["message"])
        self.assertIsNone(result["timestamp"])
    
    def test_save_investigation_metadata_with_no_analysis_summary_should_save_successfully(self):
        """Test saving metadata without analysis summary."""
        # Arrange
        timestamp = datetime.now(timezone.utc).timestamp()
        saved_item = {'analysis_timestamp': timestamp}
        self.mock_storage_client.save_investigation_metadata.return_value = saved_item
        
        # Act
        result = self.cache.save_investigation_metadata(
            repo_name=self.repo_name,
            repo_url=self.repo_url,
            commit_sha=self.current_commit,
            branch_name=self.current_branch,
            analysis_summary=None
        )
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.mock_storage_client.save_investigation_metadata.assert_called_once()
        call_args = self.mock_storage_client.save_investigation_metadata.call_args
        # Now creates an empty dict when None is passed
        self.assertEqual(call_args.kwargs['analysis_data'], {})
    
    def test_save_investigation_metadata_with_custom_ttl_should_use_provided_ttl(self):
        """Test that custom TTL is properly passed to storage."""
        # Arrange
        custom_ttl = 30
        saved_item = {'analysis_timestamp': datetime.now(timezone.utc).timestamp()}
        self.mock_storage_client.save_investigation_metadata.return_value = saved_item
        
        # Act
        result = self.cache.save_investigation_metadata(
            repo_name=self.repo_name,
            repo_url=self.repo_url,
            commit_sha=self.current_commit,
            branch_name=self.current_branch,
            ttl_days=custom_ttl
        )
        
        # Assert
        self.assertEqual(result["status"], "success")
        call_args = self.mock_storage_client.save_investigation_metadata.call_args
        self.assertEqual(call_args.kwargs['ttl_days'], custom_ttl)
    
    def test_check_needs_investigation_should_log_appropriate_messages(self):
        """Test that appropriate log messages are generated during checks."""
        # Arrange
        self.mock_storage_client.get_latest_investigation.return_value = self.last_investigation
        
        # Patch the logger for this specific cache instance
        with patch.object(self.cache, 'logger') as mock_logger:
            # Act
            decision = self.cache.check_needs_investigation(self.repo_name, self.current_state)
            
            # Assert
            # Check that info logs were called with expected content
            info_calls = mock_logger.info.call_args_list
            self.assertTrue(any("🔍 CACHE CHECK: Starting investigation check for test-repo" in str(call) for call in info_calls))
            self.assertTrue(any("🎯 FINAL DECISION: Repository test-repo hasn't changed since last investigation - SKIPPING INVESTIGATION" in str(call) for call in info_calls))
    
    def test_investigation_decision_dataclass_should_have_correct_defaults(self):
        """Test that InvestigationDecision has proper default values."""
        # Act
        decision = InvestigationDecision(
            needs_investigation=True,
            reason="Test reason"
        )
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertEqual(decision.reason, "Test reason")
        self.assertIsNone(decision.latest_commit)
        self.assertIsNone(decision.branch_name)
        self.assertIsNone(decision.last_investigation)
    
    def test_repository_state_dataclass_should_store_all_fields(self):
        """Test that RepositoryState properly stores all fields."""
        # Act
        state = RepositoryState(
            commit_sha="test_sha",
            branch_name="test_branch",
            has_uncommitted_changes=True
        )
        
        # Assert
        self.assertEqual(state.commit_sha, "test_sha")
        self.assertEqual(state.branch_name, "test_branch")
        self.assertTrue(state.has_uncommitted_changes)


class TestPromptLevelCaching(unittest.TestCase):
    """Test suite for prompt-level caching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage_client = Mock()
        self.cache = InvestigationCache(self.mock_storage_client)
        
        self.repo_name = "test-repo"
        self.step_name = "architecture_overview"
        self.commit_sha = "abc123def456789012345678901234567890abcd"
        self.result_content = "This is the analysis result for the architecture overview."
    
    def test_check_prompt_needs_analysis_when_no_cached_result_should_return_needs_analysis(self):
        """Test that prompts with no cached result need analysis."""
        # Arrange
        self.mock_storage_client.get_analysis_result.return_value = None
        
        # Act
        result = self.cache.check_prompt_needs_analysis(
            self.repo_name, self.step_name, self.commit_sha
        )
        
        # Assert
        self.assertTrue(result["needs_analysis"])
        self.assertIsNone(result["cached_result_key"])
        self.assertIsNone(result["cached_result"])
        self.assertIn("No cached result", result["reason"])
        
        # Verify the correct cache key was used
        expected_key = f"{self.repo_name}_{self.step_name}_{self.commit_sha}_v1"
        self.mock_storage_client.get_analysis_result.assert_called_once_with(expected_key)
    
    def test_check_prompt_needs_analysis_when_cached_result_exists_should_return_cached(self):
        """Test that prompts with cached results don't need re-analysis."""
        # Arrange
        cached_content = "Previously cached analysis result"
        self.mock_storage_client.get_analysis_result.return_value = cached_content
        
        # Act
        result = self.cache.check_prompt_needs_analysis(
            self.repo_name, self.step_name, self.commit_sha
        )
        
        # Assert
        self.assertFalse(result["needs_analysis"])
        self.assertEqual(result["cached_result"], cached_content)
        self.assertEqual(
            result["cached_result_key"],
            f"{self.repo_name}_{self.step_name}_{self.commit_sha}_v1"
        )
        self.assertIn("Using cached result", result["reason"])
    
    def test_check_prompt_needs_analysis_when_storage_error_should_return_needs_analysis(self):
        """Test that storage errors result in re-analysis for safety."""
        # Arrange
        self.mock_storage_client.get_analysis_result.side_effect = Exception("DynamoDB error")
        
        # Act
        result = self.cache.check_prompt_needs_analysis(
            self.repo_name, self.step_name, self.commit_sha
        )
        
        # Assert
        self.assertTrue(result["needs_analysis"])
        self.assertIsNone(result["cached_result_key"])
        self.assertIsNone(result["cached_result"])
        self.assertIn("Cache check failed", result["reason"])
    
    def test_save_prompt_result_when_successful_should_return_success(self):
        """Test successful saving of prompt results."""
        # Arrange
        timestamp = datetime.now(timezone.utc).timestamp()
        self.mock_storage_client.save_analysis_result.return_value = {
            'timestamp': timestamp
        }
        
        # Act
        result = self.cache.save_prompt_result(
            repo_name=self.repo_name,
            step_name=self.step_name,
            commit_sha=self.commit_sha,
            result_content=self.result_content,
            ttl_days=90
        )
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertIn(self.step_name, result["message"])
        self.assertEqual(
            result["cache_key"],
            f"{self.repo_name}_{self.step_name}_{self.commit_sha}_v1"
        )
        self.assertEqual(result["timestamp"], timestamp)
        
        # Verify correct call to storage
        self.mock_storage_client.save_analysis_result.assert_called_once_with(
            reference_key=f"{self.repo_name}_{self.step_name}_{self.commit_sha}_v1",
            result_content=self.result_content,
            step_name=self.step_name,
            ttl_minutes=90 * 24 * 60  # 90 days in minutes
        )
    
    def test_save_prompt_result_when_storage_error_should_return_error_status(self):
        """Test error handling when saving prompt results fails."""
        # Arrange
        error_msg = "DynamoDB write error"
        self.mock_storage_client.save_analysis_result.side_effect = Exception(error_msg)
        
        # Act
        result = self.cache.save_prompt_result(
            repo_name=self.repo_name,
            step_name=self.step_name,
            commit_sha=self.commit_sha,
            result_content=self.result_content
        )
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertIn(error_msg, result["message"])
        self.assertIsNone(result["cache_key"])
        self.assertIsNone(result["timestamp"])
    
    def test_prompt_cache_key_format_should_be_consistent(self):
        """Test that cache keys are formatted consistently."""
        # Arrange
        repo = "my-repo"
        step = "security_analysis"
        commit = "def456"
        
        # Act - Check for analysis
        self.mock_storage_client.get_analysis_result.return_value = None
        check_result = self.cache.check_prompt_needs_analysis(repo, step, commit)
        
        # Act - Save result
        self.mock_storage_client.save_analysis_result.return_value = {'timestamp': 123}
        save_result = self.cache.save_prompt_result(repo, step, commit, "content")
        
        # Assert - Both operations use the same key format
        expected_key = f"{repo}_{step}_{commit}_v1"
        self.mock_storage_client.get_analysis_result.assert_called_with(expected_key)
        self.mock_storage_client.save_analysis_result.assert_called_with(
            reference_key=expected_key,
            result_content="content",
            step_name=step,
            ttl_minutes=90 * 24 * 60
        )
        self.assertEqual(save_result["cache_key"], expected_key)
    
    def test_save_prompt_result_with_custom_ttl_should_convert_to_minutes(self):
        """Test that custom TTL is properly converted from days to minutes."""
        # Arrange
        custom_ttl_days = 30
        self.mock_storage_client.save_analysis_result.return_value = {'timestamp': 123}
        
        # Act
        result = self.cache.save_prompt_result(
            repo_name=self.repo_name,
            step_name=self.step_name,
            commit_sha=self.commit_sha,
            result_content=self.result_content,
            ttl_days=custom_ttl_days
        )
        
        # Assert
        self.assertEqual(result["status"], "success")
        
        # Verify TTL was converted correctly
        expected_ttl_minutes = custom_ttl_days * 24 * 60
        call_args = self.mock_storage_client.save_analysis_result.call_args
        self.assertEqual(call_args.kwargs['ttl_minutes'], expected_ttl_minutes)
    
    def test_check_prompt_with_different_commits_should_be_independent(self):
        """Test that same prompt with different commits are cached independently."""
        # Arrange
        commit1 = "abc123"
        commit2 = "def456"
        
        # Setup different results for different commits
        def get_result_side_effect(key):
            if commit1 in key:
                return "Result for commit 1"
            elif commit2 in key:
                return None
            return None
        
        self.mock_storage_client.get_analysis_result.side_effect = get_result_side_effect
        
        # Act
        result1 = self.cache.check_prompt_needs_analysis(
            self.repo_name, self.step_name, commit1
        )
        result2 = self.cache.check_prompt_needs_analysis(
            self.repo_name, self.step_name, commit2
        )
        
        # Assert
        self.assertFalse(result1["needs_analysis"])  # Has cached result
        self.assertEqual(result1["cached_result"], "Result for commit 1")
        
        self.assertTrue(result2["needs_analysis"])  # No cached result
        self.assertIsNone(result2["cached_result"])


class TestInvestigationCacheEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for InvestigationCache."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage_client = Mock()
        self.cache = InvestigationCache(self.mock_storage_client)
    
    def test_check_needs_investigation_with_detached_head_should_handle_correctly(self):
        """Test handling of detached HEAD state."""
        # Arrange
        detached_branch = "detached-abc12345"
        state = RepositoryState(
            commit_sha="abc123def456",
            branch_name=detached_branch,
            has_uncommitted_changes=False
        )
        
        last_investigation = {
            'latest_commit': "abc123def456",
            'branch_name': "main",  # Different from detached state
            'analysis_timestamp': datetime.now(timezone.utc).timestamp()
        }
        self.mock_storage_client.get_latest_investigation.return_value = last_investigation
        
        # Act
        decision = self.cache.check_needs_investigation("repo", state)
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertIn("Branch changed", decision.reason)
    
    def test_save_investigation_metadata_with_very_long_commit_sha_should_truncate_in_logs(self):
        """Test that long commit SHAs are properly handled in logging."""
        # Arrange
        long_commit = "a" * 100  # Unusually long SHA
        saved_item = {'analysis_timestamp': datetime.now(timezone.utc).timestamp()}
        self.mock_storage_client.save_investigation_metadata.return_value = saved_item
        
        # Act
        result = self.cache.save_investigation_metadata(
            repo_name="test",
            repo_url="http://test",
            commit_sha=long_commit,
            branch_name="main"
        )
        
        # Assert
        self.assertEqual(result["status"], "success")
        # The storage should receive the full SHA
        call_args = self.mock_storage_client.save_investigation_metadata.call_args
        self.assertEqual(call_args.kwargs['latest_commit'], long_commit)
    
    def test_check_needs_investigation_with_zero_timestamp_should_handle_correctly(self):
        """Test handling of invalid timestamp in last investigation."""
        # Arrange
        last_investigation = {
            'latest_commit': "abc123",
            'branch_name': "main",
            'analysis_timestamp': 0  # Invalid timestamp
        }
        self.mock_storage_client.get_latest_investigation.return_value = last_investigation
        
        state = RepositoryState(
            commit_sha="def456",
            branch_name="main",
            has_uncommitted_changes=False
        )
        
        # Act
        decision = self.cache.check_needs_investigation("repo", state)
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        # Should still work despite invalid timestamp
        self.assertIn("New commits detected", decision.reason)


if __name__ == '__main__':
    unittest.main()
