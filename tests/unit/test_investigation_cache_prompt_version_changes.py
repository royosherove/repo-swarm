"""
Unit tests for InvestigationCache prompt version change detection functionality.

These tests verify that the caching system correctly detects when prompt versions
change and triggers re-investigation appropriately.
"""

import unittest
from unittest.mock import Mock
from datetime import datetime, timezone

from src.activities.investigation_cache import InvestigationCache
from src.models.investigation import RepositoryState


class InvestigationCachePromptVersionChangeTests(unittest.TestCase):
    """Tests for InvestigationCache prompt version change detection functionality."""
    
    def setUp(self):
        """Set up common test fixtures and dependencies."""
        self.mock_storage = Mock()
        self.cache = InvestigationCache(self.mock_storage)
        
        self.repo_state = RepositoryState(
            commit_sha="abc123def456",
            branch_name="main",
            has_uncommitted_changes=False
        )
        
        self.base_last_investigation = {
            "latest_commit": "abc123def456",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp()
        }
    
    def test_check_prompt_version_changes_with_no_current_versions_returns_none(self):
        """Given no current prompt versions, when checking version changes, then returns None."""
        # Arrange
        current_prompt_versions = None
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompt_versions,
            self.base_last_investigation
        )
        
        # Assert
        self.assertIsNone(decision)
    
    def test_check_prompt_version_changes_with_no_previous_metadata_and_version_greater_than_1_triggers_investigation(self):
        """Given no previous metadata and current version > 1, when checking changes, then triggers investigation."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {}
        }
        current_prompts = {
            "hl_overview": "2",
            "dependencies": "1"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("hl_overview", decision.reason)
        self.assertIn("v2", decision.reason)
        self.assertIn("no previous version tracking", decision.reason)
    
    def test_check_prompt_version_changes_with_no_previous_metadata_and_all_version_1_returns_none(self):
        """Given no previous metadata and all current versions are 1, when checking changes, then returns None."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {}
        }
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "1"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNone(decision)
    
    def test_check_prompt_version_changes_with_increased_prompt_count_triggers_investigation(self):
        """Given prompt count increased from 2 to 3, when checking changes, then triggers investigation."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 2,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1"
                }
            }
        }
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "1"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("Prompt count changed", decision.reason)
        self.assertIn("2 → 3", decision.reason)
    
    def test_check_prompt_version_changes_with_decreased_prompt_count_triggers_investigation(self):
        """Given prompt count decreased from 3 to 2, when checking changes, then triggers investigation."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
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
            "hl_overview": "1",
            "dependencies": "1"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("Prompt count changed", decision.reason)
        self.assertIn("3 → 2", decision.reason)
    
    def test_check_prompt_version_changes_with_individual_version_change_triggers_investigation(self):
        """Given an individual prompt version changed from 2 to 3, when checking changes, then triggers investigation."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 3,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "2",
                    "apis": "1"
                }
            }
        }
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "3",
            "apis": "1"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("dependencies", decision.reason)
        self.assertIn("v2 → v3", decision.reason)
    
    def test_check_prompt_version_changes_with_new_untracked_prompt_assumes_version_1(self):
        """Given a new untracked prompt with version 2, when checking changes, then assumes previous version was 1."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 3,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1"
                }
            }
        }
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "2"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("apis", decision.reason)
        self.assertIn("v1 → v2", decision.reason)
    
    def test_check_prompt_version_changes_with_removed_prompt_triggers_investigation(self):
        """Given a prompt was removed, when checking changes, then triggers investigation."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 3,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1",
                    "apis": "1",
                    "removed_prompt": "2"
                }
            }
        }
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "1"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        # Either count change or removal will be detected
        self.assertTrue(
            "Prompt count changed" in decision.reason or 
            "removed_prompt" in decision.reason
        )
    
    def test_check_prompt_version_changes_with_no_changes_returns_none(self):
        """Given no prompt version changes, when checking changes, then returns None."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 3,
                "versions": {
                    "hl_overview": "2",
                    "dependencies": "1",
                    "apis": "3"
                }
            }
        }
        current_prompts = {
            "hl_overview": "2",
            "dependencies": "1",
            "apis": "3"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNone(decision)
    
    def test_check_prompt_version_changes_with_empty_versions_dict_but_metadata_exists_triggers_investigation(self):
        """Given empty versions dict but metadata exists and current version > 1, when checking changes, then triggers investigation."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 0,
                "versions": {}
            }
        }
        current_prompts = {
            "hl_overview": "2"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("hl_overview", decision.reason)
        self.assertIn("v2", decision.reason)
    
    def test_check_prompt_version_changes_with_no_previous_metadata_and_all_version_1_skips_checks(self):
        """Given no previous metadata and all versions are 1, when checking changes, then skips checks and returns None."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation
        }
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "1"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNone(decision)
    
    def test_check_prompt_version_changes_detects_count_changes_before_version_changes(self):
        """Given both count and version changes, when checking changes, then detects count change first."""
        # Arrange
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 2,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1"
                }
            }
        }
        current_prompts = {
            "hl_overview": "2",
            "dependencies": "1",
            "apis": "1"
        }
        
        # Act
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        # Assert
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("Prompt count changed", decision.reason)
        self.assertNotIn("version changed", decision.reason)


if __name__ == "__main__":
    unittest.main()
