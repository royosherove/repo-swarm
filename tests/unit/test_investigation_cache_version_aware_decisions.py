"""
Unit tests for InvestigationCache version-aware investigation decision functionality.

These tests verify that the investigation cache correctly makes decisions about
whether to investigate based on prompt version changes at the high level.
"""

import unittest
from unittest.mock import Mock
from datetime import datetime, timezone

from src.activities.investigation_cache import InvestigationCache
from src.models.investigation import RepositoryState


class InvestigationCacheVersionAwareDecisionTests(unittest.TestCase):
    """Tests for InvestigationCache version-aware investigation decision functionality."""
    
    def setUp(self):
        """Set up common test fixtures and dependencies."""
        self.mock_storage = Mock()
        self.cache = InvestigationCache(self.mock_storage)
        
        self.repo_state = RepositoryState(
            commit_sha="abc123def456",
            branch_name="main",
            has_uncommitted_changes=False
        )
        
        self.current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "1"
        }
    
    def test_check_needs_investigation_with_changed_prompt_version_triggers_investigation(self):
        """Given a prompt version changed from 1 to 2, when checking investigation need, then triggers investigation."""
        # Arrange
        self.mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123def456",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            "prompt_metadata": {
                "count": 3,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1",
                    "apis": "1"
                }
            }
        }
        current_prompts = {
            "hl_overview": "2",
            "dependencies": "1",
            "apis": "1"
        }
        
        # Act
        decision = self.cache.check_needs_investigation(
            "test-repo", 
            self.repo_state,
            current_prompts
        )
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertIn("version changed", decision.reason)
    
    def test_check_needs_investigation_with_prompt_count_change_triggers_investigation(self):
        """Given prompt count changed from 2 to 3, when checking investigation need, then triggers investigation."""
        # Arrange
        self.mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123def456",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            "prompt_metadata": {
                "count": 2,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1"
                }
            }
        }
        
        # Act
        decision = self.cache.check_needs_investigation(
            "test-repo",
            self.repo_state,
            self.current_prompts
        )
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertIn("Prompt count changed", decision.reason)
    
    def test_check_needs_investigation_with_removed_prompt_triggers_investigation(self):
        """Given a prompt was removed, when checking investigation need, then triggers investigation."""
        # Arrange
        self.mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123def456",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            "prompt_metadata": {
                "count": 4,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1",
                    "apis": "1",
                    "removed_prompt": "1"
                }
            }
        }
        
        # Act
        decision = self.cache.check_needs_investigation(
            "test-repo",
            self.repo_state,
            self.current_prompts
        )
        
        # Assert
        self.assertTrue(decision.needs_investigation)
        self.assertIn("Prompt count changed", decision.reason)
    
    def test_check_needs_investigation_with_no_changes_skips_investigation(self):
        """Given no prompt changes, when checking investigation need, then skips investigation."""
        # Arrange
        self.mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123def456",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            "prompt_metadata": {
                "count": 3,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1",
                    "apis": "1"
                }
            }
        }
        
        # Act
        decision = self.cache.check_needs_investigation(
            "test-repo",
            self.repo_state,
            self.current_prompts
        )
        
        # Assert
        self.assertFalse(decision.needs_investigation)
        self.assertIn("No changes", decision.reason)


if __name__ == "__main__":
    unittest.main()
