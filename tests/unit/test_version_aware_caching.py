"""
Unit tests for version-aware caching functionality.

These tests verify that the caching system correctly handles prompt versions,
intelligently combines cached and new results, and triggers re-investigation
when prompts change.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from src.activities.investigation_cache import InvestigationCache
from src.models.investigation import RepositoryState
from src.investigator.core.analysis_results_collector import AnalysisResultsCollector


class AnalysisResultsCollectorTests(unittest.TestCase):
    """Tests for AnalysisResultsCollector prompt version extraction functionality."""
    
    def test_extract_prompt_version_with_version_header_returns_correct_version(self):
        """Given a prompt with version=2 header, when extracting version, then returns "2"."""
        # Arrange
        prompt_content = """version=2
## Repository Structure and Files

{repo_structure}
---"""
        
        # Act
        version = AnalysisResultsCollector.extract_prompt_version(prompt_content)
        
        # Assert
        self.assertEqual(version, "2")
    
    def test_extract_prompt_version_without_version_header_raises_error(self):
        """Given a prompt without version header, when extracting version, then raises ValueError."""
        # Arrange
        prompt_content = """## Repository Structure and Files

{repo_structure}
---"""
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            AnalysisResultsCollector.extract_prompt_version(prompt_content)
        
        self.assertIn("No version found in prompt", str(context.exception))
    
    def test_extract_prompt_version_with_empty_prompt_raises_error(self):
        """Given an empty prompt, when extracting version, then raises ValueError."""
        # Arrange
        prompt_content = ""
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            AnalysisResultsCollector.extract_prompt_version(prompt_content)
        
        self.assertIn("Prompt content is empty", str(context.exception))
    
    def test_extract_prompt_version_with_invalid_format_returns_raw_value(self):
        """Given a prompt with invalid version format, when extracting version, then returns the raw value."""
        # Arrange
        prompt_content = """version=invalid
## Repository Structure"""
        
        # Act
        version = AnalysisResultsCollector.extract_prompt_version(prompt_content)
        
        # Assert
        self.assertEqual(version, "invalid")


class InvestigationCachePromptVersionTests(unittest.TestCase):
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
    
    def test_individual_version_change_detected(self):
        """Test detection when an individual prompt version changes."""
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
            "dependencies": "3",  # Version changed from 2 to 3
            "apis": "1"
        }
        
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("dependencies", decision.reason)
        self.assertIn("v2 → v3", decision.reason)
    
    def test_new_prompt_assumes_version_1_if_not_tracked(self):
        """Test that untracked prompts assume version 1 for comparison."""
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 3,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1"
                    # apis not tracked before
                }
            }
        }
        
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "2"  # New prompt with version 2
        }
        
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        self.assertIn("apis", decision.reason)
        self.assertIn("v1 → v2", decision.reason)  # Assumes v1 as default
    
    def test_removed_prompt_detected(self):
        """Test detection when a prompt is removed."""
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 3,
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1",
                    "apis": "1",
                    "removed_prompt": "2"  # This will be removed
                }
            }
        }
        
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "1"
            # removed_prompt is gone
        }
        
        # Note: Count change is detected first in current implementation
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        # Either count change or removal will be detected
        self.assertTrue(
            "Prompt count changed" in decision.reason or 
            "removed_prompt" in decision.reason
        )
    
    def test_no_changes_returns_none(self):
        """Test that None is returned when no changes are detected."""
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
        
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        self.assertIsNone(decision)
    
    def test_empty_versions_dict_but_has_metadata(self):
        """Test handling of metadata with empty versions dict."""
        last_investigation = {
            **self.base_last_investigation,
            "prompt_metadata": {
                "count": 0,
                "versions": {}  # Empty but exists
            }
        }
        
        current_prompts = {
            "hl_overview": "2"  # Version > 1
        }
        
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        # Should detect the version > 1 with no tracking
        self.assertIn("hl_overview", decision.reason)
        self.assertIn("v2", decision.reason)
    
    def test_checks_skip_when_no_previous_metadata(self):
        """Test that version checks are skipped when no previous metadata exists and all versions are 1."""
        last_investigation = {
            **self.base_last_investigation
            # No prompt_metadata key at all
        }
        
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "1"
        }
        
        # Should not trigger investigation since all are v1 and no baseline exists
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        self.assertIsNone(decision)
    
    def test_order_of_checks_count_before_version(self):
        """Test that count changes are detected before version changes."""
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
            "hl_overview": "2",  # Version changed
            "dependencies": "1",
            "apis": "1"  # New prompt
        }
        
        decision = self.cache._check_prompt_version_changes(
            self.repo_state,
            current_prompts,
            last_investigation
        )
        
        self.assertIsNotNone(decision)
        self.assertTrue(decision.needs_investigation)
        # Count change should be detected first
        self.assertIn("Prompt count changed", decision.reason)
        self.assertNotIn("version changed", decision.reason)


class InvestigationCacheVersionAwareTests(unittest.TestCase):
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
    
    def test_needs_investigation_when_prompt_count_changes(self):
        """Test that investigation is triggered when prompt count changes."""
        # Mock last investigation with different prompt count
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
        
        decision = self.cache.check_needs_investigation(
            "test-repo",
            self.repo_state,
            self.current_prompts
        )
        
        self.assertTrue(decision.needs_investigation)
        self.assertIn("Prompt count changed", decision.reason)
    
    def test_needs_investigation_when_prompt_removed(self):
        """Test that investigation is triggered when a prompt is removed."""
        # Mock last investigation with an extra prompt
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
                    "removed_prompt": "1"  # This prompt no longer exists
                }
            }
        }
        
        decision = self.cache.check_needs_investigation(
            "test-repo",
            self.repo_state,
            self.current_prompts
        )
        
        self.assertTrue(decision.needs_investigation)
        # The count change is detected first, which is correct behavior
        self.assertIn("Prompt count changed", decision.reason)
    
    def test_no_investigation_needed_when_nothing_changed(self):
        """Test that no investigation is needed when nothing changed."""
        # Mock last investigation with same prompts and versions
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
        
        decision = self.cache.check_needs_investigation(
            "test-repo",
            self.repo_state,
            self.current_prompts
        )
        
        self.assertFalse(decision.needs_investigation)
        self.assertIn("No changes", decision.reason)


class InvestigationCachePromptLevelTests(unittest.TestCase):
    """Tests for InvestigationCache prompt-level caching with version support."""
    
    def setUp(self):
        """Set up common test fixtures and dependencies."""
        self.mock_storage = Mock()
        self.cache = InvestigationCache(self.mock_storage)
    
    def test_check_prompt_needs_analysis_with_cached_result_returns_cached_content(self):
        """Given a cached result exists for prompt version, when checking analysis need, then returns cached content."""
        # Arrange
        expected_cached_content = "Cached analysis content"
        expected_version = "2"
        self.mock_storage.get_analysis_result.return_value = expected_cached_content
        
        # Act
        result = self.cache.check_prompt_needs_analysis(
            "test-repo",
            "hl_overview",
            "abc123",
            expected_version
        )
        
        # Assert
        self.assertFalse(result["needs_analysis"])
        self.assertEqual(result["cached_result"], expected_cached_content)
        self.assertEqual(result["version"], expected_version)
        
        expected_cache_key = "test-repo_hl_overview_abc123_v2"
        self.mock_storage.get_analysis_result.assert_called_with(expected_cache_key)
    
    def test_check_prompt_with_no_cached_result(self):
        """Test checking prompt cache when no cached result exists."""
        # Mock no cached result
        self.mock_storage.get_analysis_result.return_value = None
        
        result = self.cache.check_prompt_needs_analysis(
            "test-repo",
            "hl_overview",
            "abc123",
            "2"
        )
        
        self.assertTrue(result["needs_analysis"])
        self.assertIsNone(result["cached_result"])
        self.assertEqual(result["version"], "2")
    
    def test_save_prompt_with_version(self):
        """Test saving prompt result with version."""
        # Mock successful save
        self.mock_storage.save_analysis_result.return_value = {
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        result = self.cache.save_prompt_result(
            "test-repo",
            "hl_overview",
            "abc123",
            "Analysis content",
            "2"
        )
        
        self.assertEqual(result["status"], "success")
        
        # Verify correct cache key was used
        expected_key = "test-repo_hl_overview_abc123_v2"
        self.mock_storage.save_analysis_result.assert_called_once()
        call_args = self.mock_storage.save_analysis_result.call_args
        self.assertEqual(call_args[1]["reference_key"], expected_key)


class AnalysisResultsCollectorCombinationTests(unittest.TestCase):
    """Tests for AnalysisResultsCollector combining cached and new results based on versions."""
    
    def setUp(self):
        """Set up common test fixtures and dependencies."""
        self.collector = AnalysisResultsCollector("test-repo")
        
        self.processing_order = [
            {"name": "hl_overview", "description": "High level overview"},
            {"name": "dependencies", "description": "Dependencies analysis"},
            {"name": "apis", "description": "API analysis"}
        ]
        
        self.prompt_versions = {
            "hl_overview": "2",
            "dependencies": "1",
            "apis": "1"
        }
    
    def test_combine_results_with_all_cached_results_returns_cached_content(self):
        """Given all results are cached with matching versions, when combining results, then returns all cached content."""
        # Arrange
        cached_results = {
            "hl_overview": {
                "content": "Cached overview content",
                "version": "2",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "dependencies": {
                "content": "Cached dependencies content",
                "version": "1",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "apis": {
                "content": "Cached API content",
                "version": "1",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        new_results = {}
        
        # Act
        combined = self.collector.combine_results(
            new_results,
            self.processing_order,
            cached_results,
            self.prompt_versions
        )
        
        # Assert
        self.assertEqual(len(combined), 3)
        for result in combined:
            self.assertTrue(result["cached"])
            self.assertIn("Cached", result["content"])
    
    def test_combine_with_mixed_cached_and_new(self):
        """Test combining when some results are cached and some are new."""
        # Some results from cache
        cached_results = {
            "dependencies": {
                "content": "Cached dependencies content",
                "version": "1",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "apis": {
                "content": "Cached API content",
                "version": "1",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        # New result for updated prompt
        new_results = {
            "hl_overview": "New overview content"
        }
        
        combined = self.collector.combine_results(
            new_results,
            self.processing_order,
            cached_results,
            self.prompt_versions
        )
        
        self.assertEqual(len(combined), 3)
        
        # Check first result is new
        self.assertEqual(combined[0]["name"], "hl_overview")
        self.assertFalse(combined[0]["cached"])
        self.assertEqual(combined[0]["content"], "New overview content")
        
        # Check other results are cached
        self.assertTrue(combined[1]["cached"])
        self.assertTrue(combined[2]["cached"])
    
    def test_combine_with_version_mismatch_fallback(self):
        """Test that outdated cached results are used as fallback."""
        # Cached result with old version
        cached_results = {
            "hl_overview": {
                "content": "Old cached overview",
                "version": "1",  # Old version
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        # No new result available
        new_results = {}
        
        # Current version is 2
        prompt_versions = {"hl_overview": "2"}
        
        with patch('src.investigator.core.analysis_results_collector.logger') as mock_logger:
            combined = self.collector.combine_results(
                new_results,
                [{"name": "hl_overview", "description": "Overview"}],
                cached_results,
                prompt_versions
            )
            
            # Should use cached result but warn about version mismatch
            self.assertEqual(len(combined), 1)
            self.assertTrue(combined[0]["cached"])
            self.assertEqual(combined[0]["content"], "Old cached overview")
            
            # Check warning was logged
            mock_logger.warning.assert_called()
            warning_msg = str(mock_logger.warning.call_args)
            self.assertIn("outdated", warning_msg.lower())


class InvestigationCacheMetadataTests(unittest.TestCase):
    """Tests for InvestigationCache saving investigation metadata with prompt versions."""
    
    def setUp(self):
        """Set up common test fixtures and dependencies."""
        self.mock_storage = Mock()
        self.cache = InvestigationCache(self.mock_storage)
    
    def test_save_investigation_metadata_with_prompt_versions_includes_version_data(self):
        """Given prompt versions provided, when saving metadata, then includes prompt version data."""
        # Arrange
        prompt_versions = {
            "hl_overview": "2",
            "dependencies": "1",
            "apis": "1"
        }
        self.mock_storage.save_investigation_metadata.return_value = {
            "analysis_timestamp": datetime.now(timezone.utc).timestamp()
        }
        
        # Act
        result = self.cache.save_investigation_metadata(
            "test-repo",
            "https://github.com/test/repo",
            "abc123",
            "main",
            analysis_summary={"steps": 3},
            prompt_versions=prompt_versions
        )
        
        # Assert
        self.assertEqual(result["status"], "success")
        
        call_args = self.mock_storage.save_investigation_metadata.call_args
        analysis_data = call_args[1]["analysis_data"]
        
        self.assertIn("prompt_metadata", analysis_data)
        self.assertEqual(analysis_data["prompt_metadata"]["count"], 3)
        self.assertEqual(analysis_data["prompt_metadata"]["versions"], prompt_versions)


if __name__ == "__main__":
    unittest.main()
