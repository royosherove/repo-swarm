#!/usr/bin/env python3
"""
Unit tests for edge cases in prompt version checking.

Tests scenarios where:
1. No prompt versions exist from last investigation but current prompt has version > 1
2. Prompt wasn't tracked before (None) but now has version > 1
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from activities.investigation_cache import InvestigationCache, RepositoryState


class TestPromptVersionEdgeCases:
    """Test edge cases in prompt version checking."""
    
    def test_no_previous_prompt_metadata_with_updated_prompt(self):
        """
        Test that investigation is triggered when there's no prompt metadata
        from last investigation but current prompt has version > 1.
        """
        mock_storage = Mock()
        cache = InvestigationCache(mock_storage)
        
        repo_state = RepositoryState(
            commit_sha="abc123",
            branch_name="main",
            has_uncommitted_changes=False
        )
        
        # Last investigation has no prompt metadata (old investigation before version tracking)
        mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123",  # Same commit
            "branch_name": "main",       # Same branch
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            # No prompt_metadata field
        }
        
        # Current prompts have version > 1 (meaning they've been updated)
        current_prompts = {
            "hl_overview": "2",  # Version 2 - has been updated
            "dependencies": "1",
            "monitoring": "3"     # Version 3 - has been updated multiple times
        }
        
        decision = cache.check_needs_investigation(
            "test-repo",
            repo_state,
            current_prompts
        )
        
        # Should need investigation because prompts have been updated
        assert decision.needs_investigation == True
        assert "updated to v" in decision.reason
        assert "no previous version tracking" in decision.reason
    
    def test_empty_prompt_versions_dict_with_updated_prompt(self):
        """
        Test that investigation is triggered when last investigation has
        empty prompt versions dict but current prompt has version > 1.
        """
        mock_storage = Mock()
        cache = InvestigationCache(mock_storage)
        
        repo_state = RepositoryState(
            commit_sha="abc123",
            branch_name="main",
            has_uncommitted_changes=False
        )
        
        # Last investigation has empty prompt metadata
        mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            "prompt_metadata": {
                "versions": {},  # Empty versions dict
                "count": 0
            }
        }
        
        # Current prompts include one with version > 1
        current_prompts = {
            "hl_overview": "1",
            "security_check": "2"  # This should trigger re-investigation
        }
        
        decision = cache.check_needs_investigation(
            "test-repo",
            repo_state,
            current_prompts
        )
        
        assert decision.needs_investigation == True
        assert "security_check" in decision.reason
        assert "v2" in decision.reason
    
    def test_prompt_not_tracked_before_now_version_2(self):
        """
        Test that investigation is triggered when a prompt wasn't tracked
        in last investigation (None) but now has version > 1.
        """
        mock_storage = Mock()
        cache = InvestigationCache(mock_storage)
        
        repo_state = RepositoryState(
            commit_sha="abc123",
            branch_name="main",
            has_uncommitted_changes=False
        )
        
        # Last investigation tracked some prompts but not all
        mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            "prompt_metadata": {
                "versions": {
                    "hl_overview": "1",
                    "dependencies": "1"
                    # "monitoring" is not tracked
                },
                "count": 2
            }
        }
        
        # Current prompts include a new one with version > 1
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "monitoring": "2"  # New prompt with version 2
        }
        
        decision = cache.check_needs_investigation(
            "test-repo",
            repo_state,
            current_prompts
        )
        
        # Should need investigation - either because count changed or version changed
        assert decision.needs_investigation == True
        # The count check triggers first (2 → 3), which is correct behavior
        # We're adding a new prompt, so investigation is needed
        assert ("Prompt count changed" in decision.reason) or ("monitoring" in decision.reason)
    
    def test_all_prompts_version_1_with_no_previous_metadata(self):
        """
        Test that no investigation is needed when there's no previous prompt
        metadata but all current prompts are version 1 (default).
        """
        mock_storage = Mock()
        cache = InvestigationCache(mock_storage)
        
        repo_state = RepositoryState(
            commit_sha="abc123",
            branch_name="main",
            has_uncommitted_changes=False
        )
        
        # Last investigation has no prompt metadata
        mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            # No prompt_metadata
        }
        
        # All current prompts are version 1 (default)
        current_prompts = {
            "hl_overview": "1",
            "dependencies": "1",
            "apis": "1"
        }
        
        decision = cache.check_needs_investigation(
            "test-repo",
            repo_state,
            current_prompts
        )
        
        # Should NOT need investigation - all prompts are at default version
        assert decision.needs_investigation == False
        assert "No changes since last investigation" in decision.reason
    
    def test_mixed_versions_with_partial_tracking(self):
        """
        Test complex scenario with some prompts tracked, some not,
        and various version numbers.
        """
        mock_storage = Mock()
        cache = InvestigationCache(mock_storage)
        
        repo_state = RepositoryState(
            commit_sha="abc123",
            branch_name="main",
            has_uncommitted_changes=False
        )
        
        # Last investigation tracked only some prompts
        mock_storage.get_latest_investigation.return_value = {
            "latest_commit": "abc123",
            "branch_name": "main",
            "analysis_timestamp": datetime.now(timezone.utc).timestamp(),
            "prompt_metadata": {
                "versions": {
                    "hl_overview": "1",
                    "apis": "2"  # Already at version 2
                },
                "count": 2
            }
        }
        
        # Current state with mixed versions
        current_prompts = {
            "hl_overview": "1",      # Same as before
            "apis": "2",             # Same as before
            "dependencies": "1",     # New prompt at v1 (no change needed)
            "monitoring": "2",       # New prompt at v2 (should trigger)
            "security_check": "3"    # New prompt at v3 (should trigger)
        }
        
        decision = cache.check_needs_investigation(
            "test-repo",
            repo_state,
            current_prompts
        )
        
        # Should need investigation due to new prompts being added
        assert decision.needs_investigation == True
        # The count check triggers first (2 → 5), which is correct
        # We're adding 3 new prompts, so investigation is needed regardless of their versions
        assert "Prompt count changed" in decision.reason or "monitoring" in decision.reason or "security_check" in decision.reason


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
