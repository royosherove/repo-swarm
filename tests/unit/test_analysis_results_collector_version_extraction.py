"""
Unit tests for AnalysisResultsCollector prompt version extraction functionality.

These tests verify that the system correctly extracts version information
from prompt content headers.
"""

import unittest
from src.investigator.core.analysis_results_collector import AnalysisResultsCollector


class AnalysisResultsCollectorVersionExtractionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
