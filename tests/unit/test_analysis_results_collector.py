#!/usr/bin/env python3
"""
Unit tests for AnalysisResultsCollector class.

Tests that all base prompt sections are properly collected, validated,
and included in the final analysis output.
"""

import sys
import json
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, mock_open

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from investigator.core.analysis_results_collector import (
    AnalysisResultsCollector,
    StepResult
)
from investigator.core.constants import EXPECTED_BASE_PROMPT_COUNT


class TestAnalysisResultsCollector:
    """Test suite for the AnalysisResultsCollector class."""
    
    @classmethod
    def setup_class(cls):
        """Load the actual base_prompts.json for testing."""
        base_prompts_path = Path(__file__).parent.parent.parent / "prompts" / "base_prompts.json"
        with open(base_prompts_path, 'r') as f:
            cls.base_config = json.load(f)
        cls.base_sections = [s["name"] for s in cls.base_config["processing_order"]]
        cls.processing_order = cls.base_config["processing_order"]
    
    def setup_method(self):
        """Create a fresh collector for each test."""
        self.collector = AnalysisResultsCollector("test-repo", self.base_config)
    
    def test_collector_loads_base_prompts_config(self):
        """Test that collector receives and processes base prompts config."""
        assert len(self.collector.base_sections) >= EXPECTED_BASE_PROMPT_COUNT
        assert "monitoring" in self.collector.base_sections
        assert "hl_overview" in self.collector.base_sections
        assert self.collector.base_sections == self.base_sections
    
    def test_track_step_stores_result_info(self):
        """Test that tracking a step stores the correct information."""
        self.collector.track_step(
            step_name="monitoring",
            description="Monitoring and observability analysis",
            result_key="result_123",
            required=True,
            context_dependencies=[]
        )
        
        assert "monitoring" in self.collector.step_results
        step = self.collector.step_results["monitoring"]
        assert step.name == "monitoring"
        assert step.description == "Monitoring and observability analysis"
        assert step.result_key == "result_123"
        assert step.required is True
    
    def test_validate_all_base_sections_present(self):
        """Test validation when all base sections are tracked."""
        # Track all base sections
        for section in self.base_sections:
            self.collector.track_step(
                step_name=section,
                description=f"Description for {section}",
                result_key=f"key_{section}"
            )
        
        is_valid, missing = self.collector.validate_base_sections_present()
        assert is_valid is True
        assert len(missing) == 0
    
    def test_validate_missing_base_sections_detected(self):
        """Test that missing base sections are properly detected."""
        # Track only some sections (missing monitoring and others)
        tracked_sections = self.base_sections[:10]  # Only track first 10
        for section in tracked_sections:
            self.collector.track_step(
                step_name=section,
                description=f"Description for {section}",
                result_key=f"key_{section}"
            )
        
        is_valid, missing = self.collector.validate_base_sections_present()
        assert is_valid is False
        assert len(missing) >= 7  # Should be missing at least 7 sections
        assert "monitoring" in missing  # Monitoring is in position 14
    
    def test_monitoring_section_specifically_validated(self):
        """Test that monitoring section is specifically checked."""
        # Track all sections except monitoring
        for section in self.base_sections:
            if section != "monitoring":
                self.collector.track_step(
                    step_name=section,
                    description=f"Description for {section}",
                    result_key=f"key_{section}"
                )
        
        is_valid, missing = self.collector.validate_base_sections_present()
        assert is_valid is False
        assert "monitoring" in missing
        
        # The logger should have logged an error about missing monitoring
        with patch('investigator.core.analysis_results_collector.logger') as mock_logger:
            self.collector.validate_base_sections_present()
            mock_logger.error.assert_called_with("CRITICAL: Monitoring section is missing from results!")
    
    def test_combine_results_maintains_order(self):
        """Test that results are combined in the order specified by processing_order."""
        # Create a results map with all sections
        results_map = {
            section: f"Content for {section}" 
            for section in self.base_sections
        }
        
        # Track all sections
        for section in self.base_sections:
            self.collector.track_step(
                step_name=section,
                description=f"Description for {section}",
                result_key=f"key_{section}"
            )
        
        combined = self.collector.combine_results(results_map, self.processing_order)
        
        # Verify order matches processing_order
        assert len(combined) >= EXPECTED_BASE_PROMPT_COUNT
        for i, result in enumerate(combined):
            expected_name = self.processing_order[i]["name"]
            assert result["name"] == expected_name
    
    def test_combine_results_includes_all_base_sections(self):
        """Test that all base sections from base_prompts.json appear in combined results."""
        # Create results for all base sections
        results_map = {
            section: f"# Analysis for {section}\n\nDetailed content here..."
            for section in self.base_sections
        }
        
        # Track all sections
        for section in self.base_sections:
            self.collector.track_step(
                step_name=section,
                description=f"Description for {section}",
                result_key=f"key_{section}"
            )
        
        combined = self.collector.combine_results(results_map, self.processing_order)
        
        # Verify all base sections are present
        combined_names = {r["name"] for r in combined}
        assert len(combined_names) >= EXPECTED_BASE_PROMPT_COUNT
        for section in self.base_sections:
            assert section in combined_names
        
        # Specifically verify monitoring is included
        monitoring_result = next((r for r in combined if r["name"] == "monitoring"), None)
        assert monitoring_result is not None
        assert "Analysis for monitoring" in monitoring_result["content"]
    
    def test_combine_results_raises_error_if_monitoring_missing(self):
        """Test that missing monitoring section raises an error."""
        # Create results without monitoring
        results_map = {
            section: f"Content for {section}"
            for section in self.base_sections
            if section != "monitoring"
        }
        
        # Track sections without monitoring
        for section in self.base_sections:
            if section != "monitoring":
                self.collector.track_step(
                    step_name=section,
                    description=f"Description for {section}",
                    result_key=f"key_{section}"
                )
        
        with pytest.raises(ValueError, match="Critical: Monitoring section missing"):
            self.collector.combine_results(results_map, self.processing_order)
    
    def test_generate_final_analysis_includes_all_sections(self):
        """Test that final analysis includes all sections with proper formatting."""
        # Create combined results for all base sections
        results = [
            {
                "name": section,
                "description": next((s["description"] for s in self.processing_order if s["name"] == section), ""),
                "content": f"Detailed analysis content for {section}\nWith multiple lines\nOf important information"
            }
            for section in self.base_sections
        ]
        
        final_analysis = self.collector.generate_final_analysis(results)
        
        # Verify all sections appear in the final output
        for section in self.base_sections:
            assert f"# {section}" in final_analysis
        
        # Verify monitoring section specifically
        assert "# monitoring" in final_analysis
        assert "Monitoring, logging, metrics, and observability analysis" in final_analysis
        assert "Detailed analysis content for monitoring" in final_analysis
        
        # Verify structure
        sections = final_analysis.split("\n\n# ")
        # First section won't have # prefix in split, so we expect 17 total parts
        assert len(sections) >= EXPECTED_BASE_PROMPT_COUNT
    
    def test_generate_final_analysis_correct_markdown_format(self):
        """Test that final analysis has correct markdown formatting."""
        results = [
            {
                "name": "monitoring",
                "description": "Monitoring, logging, metrics, and observability analysis",
                "content": "## Observability Platforms\n\nDataDog, New Relic, etc."
            },
            {
                "name": "security_check",
                "description": "Security vulnerabilities assessment",
                "content": "## Security Issues\n\nNo major vulnerabilities found."
            }
        ]
        
        final_analysis = self.collector.generate_final_analysis(results)
        
        # Check markdown structure
        assert final_analysis.startswith("# monitoring\n\n")
        assert "Monitoring, logging, metrics, and observability analysis\n\n" in final_analysis
        assert "\n\n# security_check\n\n" in final_analysis
        assert final_analysis.count("# monitoring") == 1
        assert final_analysis.count("# security_check") == 1
    
    def test_get_statistics_includes_monitoring_flag(self):
        """Test that statistics include monitoring presence flag."""
        # Track some sections including monitoring
        self.collector.track_step("monitoring", "Monitoring analysis", "key_mon")
        self.collector.track_step("security_check", "Security analysis", "key_sec")
        
        stats = self.collector.get_statistics()
        
        assert stats["has_monitoring"] is True
        assert stats["base_sections_expected"] >= EXPECTED_BASE_PROMPT_COUNT
        assert stats["total_steps_tracked"] == 2
        assert "monitoring" in stats["tracked_sections"]
    
    def test_empty_content_excluded_from_results(self):
        """Test that empty content is excluded from combined results."""
        results_map = {
            "monitoring": "Valid monitoring content",
            "security_check": "",  # Empty content
            "authentication": None,  # None content
            "authorization": "Valid auth content"
        }
        
        for section in ["monitoring", "security_check", "authentication", "authorization"]:
            self.collector.track_step(section, f"Desc for {section}", f"key_{section}")
        
        # Use a subset of processing order for this test
        test_order = [
            {"name": "monitoring", "description": "Monitoring"},
            {"name": "security_check", "description": "Security"},
            {"name": "authentication", "description": "Auth"},
            {"name": "authorization", "description": "Authz"}
        ]
        
        combined = self.collector.combine_results(results_map, test_order)
        
        # Only non-empty content should be included
        assert len(combined) == 2
        assert combined[0]["name"] == "monitoring"
        assert combined[1]["name"] == "authorization"
    
    def test_validate_required_sections(self):
        """Test validation of required vs optional sections."""
        # Create a custom processing order with mix of required and optional
        custom_order = [
            {"name": "required1", "required": True},
            {"name": "optional1", "required": False},
            {"name": "required2", "required": True},
            {"name": "optional2", "required": False}
        ]
        
        # Track only required sections
        self.collector.track_step("required1", "Desc1", "key1")
        self.collector.track_step("required2", "Desc2", "key2")
        
        is_valid, missing = self.collector.validate_required_sections(custom_order)
        
        assert is_valid is True
        assert len(missing) == 0
        
        # Now test with missing required section
        self.collector.step_results.pop("required2")
        is_valid, missing = self.collector.validate_required_sections(custom_order)
        
        assert is_valid is False
        assert "required2" in missing
        assert "optional1" not in missing  # Optional sections shouldn't be in missing
    
    def test_integration_with_actual_base_prompts(self):
        """Integration test using actual base_prompts.json configuration."""
        # This test verifies the complete flow with real configuration
        
        # Simulate the workflow creating results for all base sections
        results_map = {}
        for step in self.processing_order:
            step_name = step["name"]
            # Track the step
            self.collector.track_step(
                step_name=step_name,
                description=step["description"],
                result_key=f"dynamo_key_{step_name}",
                context_dependencies=[
                    ctx["val"] for ctx in step.get("context", [])
                    if isinstance(ctx, dict) and "val" in ctx
                ]
            )
            # Add result content
            results_map[step_name] = f"# {step['description']}\n\nAnalysis results for {step_name}..."
        
        # Validate all base sections are tracked
        is_valid, missing = self.collector.validate_base_sections_present()
        assert is_valid is True
        assert len(missing) == 0
        
        # Combine results
        combined = self.collector.combine_results(results_map, self.processing_order)
        assert len(combined) >= EXPECTED_BASE_PROMPT_COUNT
        
        # Generate final analysis
        final_analysis = self.collector.generate_final_analysis(combined)
        
        # Verify all expected sections are in the final output
        for step in self.processing_order:
            assert f"# {step['name']}" in final_analysis
            assert step["description"] in final_analysis
        
        # Specific check for monitoring section
        assert "# monitoring" in final_analysis
        assert "Monitoring, logging, metrics, and observability analysis" in final_analysis
        
        # Verify the order is maintained
        section_positions = []
        for step in self.processing_order:
            pos = final_analysis.index(f"# {step['name']}")
            section_positions.append(pos)
        
        # Positions should be in increasing order
        assert section_positions == sorted(section_positions)


class TestStepResult:
    """Test the StepResult dataclass."""
    
    def test_step_result_creation(self):
        """Test creating a StepResult."""
        step = StepResult(
            name="monitoring",
            description="Monitoring analysis",
            result_key="key_123",
            content="Analysis content",
            required=True,
            context_dependencies=["hl_overview"]
        )
        
        assert step.name == "monitoring"
        assert step.description == "Monitoring analysis"
        assert step.result_key == "key_123"
        assert step.content == "Analysis content"
        assert step.required is True
        assert step.context_dependencies == ["hl_overview"]
    
    def test_step_result_defaults(self):
        """Test StepResult default values."""
        step = StepResult(
            name="test",
            description="Test step",
            result_key="key"
        )
        
        assert step.content is None
        assert step.required is True
        assert step.context_dependencies == []


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short'])
