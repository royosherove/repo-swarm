#!/usr/bin/env python3
"""
Tests for the AnalysisResultsCollector integration with real base prompts data.

These tests verify that the collector correctly handles all sections from
base_prompts.json and ensures they appear in the final output.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from investigator.core.analysis_results_collector import AnalysisResultsCollector
from investigator.core.constants import EXPECTED_BASE_PROMPT_COUNT


class TestAnalysisResultsCollectorIntegration:
    """Integration tests for AnalysisResultsCollector with real data."""
    
    def test_collector_with_real_base_prompts(self):
        """Test the collector with actual base_prompts.json data."""
        # Load actual base prompts config
        base_prompts_path = Path(__file__).parent.parent.parent / "prompts" / "base_prompts.json"
        with open(base_prompts_path, 'r') as f:
            base_config = json.load(f)
        
        collector = AnalysisResultsCollector("test-repo", base_config)
        
        processing_order = base_config["processing_order"]
        
        # Simulate tracking all steps
        for step in processing_order:
            collector.track_step(
                step_name=step["name"],
                description=step["description"],
                result_key=f"key_{step['name']}",
                required=step.get("required", True)
            )
        
        # Create mock results
        results_map = {
            step["name"]: f"Content for {step['name']}"
            for step in processing_order
        }
        
        # Combine results
        combined = collector.combine_results(results_map, processing_order)
        
        # Generate final analysis
        final = collector.generate_final_analysis(combined)
        
        # Verify all sections present
        assert len(combined) >= EXPECTED_BASE_PROMPT_COUNT
        assert "# monitoring" in final
        assert all(f"# {s['name']}" in final for s in processing_order)
    
    def test_collector_validates_monitoring_section(self):
        """Test that the collector specifically validates the monitoring section."""
        # Load actual base prompts config
        base_prompts_path = Path(__file__).parent.parent.parent / "prompts" / "base_prompts.json"
        with open(base_prompts_path, 'r') as f:
            base_config = json.load(f)
        
        collector = AnalysisResultsCollector("test-repo", base_config)
        processing_order = base_config["processing_order"]
        
        # Track all sections except monitoring
        for step in processing_order:
            if step["name"] != "monitoring":
                collector.track_step(
                    step_name=step["name"],
                    description=step["description"],
                    result_key=f"key_{step['name']}"
                )
        
        # Verify monitoring is detected as missing
        is_valid, missing = collector.validate_base_sections_present()
        assert not is_valid
        assert "monitoring" in missing
    
    def test_collector_handles_domain_specific_sections(self):
        """Test that domain-specific sections are properly handled."""
        # Load base config
        base_prompts_path = Path(__file__).parent.parent.parent / "prompts" / "base_prompts.json"
        with open(base_prompts_path, 'r') as f:
            base_config = json.load(f)
        
        # Load backend config which has additional sections
        backend_prompts_path = Path(__file__).parent.parent.parent / "prompts" / "backend" / "prompts.json"
        with open(backend_prompts_path, 'r') as f:
            backend_config = json.load(f)
        
        collector = AnalysisResultsCollector("backend-repo", base_config)
        
        # Create combined processing order (base + backend-specific)
        processing_order = base_config["processing_order"].copy()
        if "additional_prompts" in backend_config:
            processing_order.extend(backend_config["additional_prompts"])
        
        # Track all sections including backend-specific ones
        all_sections = ["data_layer", "events_and_messaging"]  # Backend-specific
        for step in processing_order:
            collector.track_step(
                step_name=step["name"],
                description=step.get("description", ""),
                result_key=f"key_{step['name']}"
            )
        
        # Create results for all sections
        results_map = {
            step["name"]: f"Content for {step['name']}"
            for step in processing_order
        }
        
        # Combine results
        combined = collector.combine_results(results_map, processing_order)
        
        # Verify base sections are validated
        is_valid, missing = collector.validate_base_sections_present()
        assert is_valid  # All base sections should be present
        
        # Verify total count includes domain-specific sections
        assert len(combined) >= EXPECTED_BASE_PROMPT_COUNT + 2  # base + 2 backend-specific
    
    def test_collector_maintains_section_order(self):
        """Test that sections are maintained in the correct order."""
        # Load actual base prompts config
        base_prompts_path = Path(__file__).parent.parent.parent / "prompts" / "base_prompts.json"
        with open(base_prompts_path, 'r') as f:
            base_config = json.load(f)
        
        collector = AnalysisResultsCollector("test-repo", base_config)
        processing_order = base_config["processing_order"]
        
        # Track all steps
        for step in processing_order:
            collector.track_step(
                step_name=step["name"],
                description=step["description"],
                result_key=f"key_{step['name']}"
            )
        
        # Create results
        results_map = {
            step["name"]: f"Content for {step['name']}"
            for step in processing_order
        }
        
        # Combine and generate final
        combined = collector.combine_results(results_map, processing_order)
        final = collector.generate_final_analysis(combined)
        
        # Verify order is maintained
        expected_order = [step["name"] for step in processing_order]
        actual_order = [result["name"] for result in combined]
        assert actual_order == expected_order
        
        # Verify in final markdown, sections appear in order
        positions = []
        for step_name in expected_order:
            pos = final.index(f"# {step_name}")
            positions.append(pos)
        
        # Positions should be strictly increasing
        assert positions == sorted(positions)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])