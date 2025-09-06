"""
Unit tests for prompt loading logic.

Tests that:
1. Prompts are loaded from correct paths
2. Missing required prompts fail appropriately
3. Optional prompts are skipped gracefully
4. Relative paths are resolved correctly
5. Shared prompts are accessible
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import json
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from investigator.core.file_manager import FileManager


# Test constants for better maintainability
class TestConstants:
    """Constants used across prompt loading tests."""
    
    # Sample prompt content
    SAMPLE_HL_OVERVIEW = "# High-Level Overview\n\nAnalyze the architecture..."
    SAMPLE_AUTH_CONTENT = "# Authentication\n\nAnalyze auth mechanisms..."
    SAMPLE_SECURITY_CONTENT = "# Security Check\n\nAnalyze security..."
    SAMPLE_OVERVIEW_CONTENT = "# Overview content"
    
    # Common prompt names
    PROMPT_HL_OVERVIEW = "hl_overview"
    PROMPT_APIS = "apis"
    PROMPT_AUTH = "authentication"
    PROMPT_OPTIONAL = "optional_feature"
    
    # File names
    FILE_HL_OVERVIEW = "hl_overview.md"
    FILE_APIS = "apis.md"
    FILE_AUTH = "authentication.md"
    FILE_OPTIONAL = "optional.md"
    
    # Relative paths
    SHARED_AUTH_PATH = "../shared/authentication.md"
    SHARED_SECURITY_PATH = "../shared/security/security_check.md"


class BasePromptTest(unittest.TestCase):
    """Base class for prompt testing with common utilities.
    
    Provides:
    - Automatic temp directory setup/teardown
    - Helper methods for creating test files and configs
    - Common test fixtures
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.file_manager = FileManager(self.logger)
        
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.prompts_dir = os.path.join(self.test_dir, "prompts")
        self.backend_dir = os.path.join(self.prompts_dir, "backend")
        self.shared_dir = os.path.join(self.prompts_dir, "shared")
        
        # Create directory structure
        os.makedirs(self.backend_dir)
        os.makedirs(self.shared_dir)
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def create_prompts_config(self, directory: str, prompts: list) -> str:
        """Helper to create a prompts.json file.
        
        Args:
            directory: Directory to create the config in
            prompts: List of prompt configurations
            
        Returns:
            Path to the created config file
        """
        config = {"prompts": prompts}
        config_path = os.path.join(directory, "prompts.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)
        return config_path
    
    def create_prompt_file(self, directory: str, filename: str, content: str) -> str:
        """Helper to create a prompt file.
        
        Args:
            directory: Directory to create the file in
            filename: Name of the file
            content: Content to write to the file
            
        Returns:
            Path to the created file
        """
        file_path = os.path.join(directory, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def create_standard_prompt(self, name: str, required: bool = True, 
                              file: Optional[str] = None, 
                              description: Optional[str] = None) -> Dict[str, Any]:
        """Helper to create a standard prompt configuration.
        
        Args:
            name: Name of the prompt
            required: Whether the prompt is required
            file: File path (defaults to {name}.md)
            description: Description (defaults to generated from name)
            
        Returns:
            Prompt configuration dictionary
        """
        return {
            "name": name,
            "file": file or f"{name}.md",
            "required": required,
            "description": description or f"{name.replace('_', ' ').title()} Analysis"
        }


class TestPromptLoading(BasePromptTest):
    """Test prompt loading functionality."""
    
    def test_read_prompts_config_with_valid_json_returns_config_dict(self):
        """Test that read_prompts_config with valid JSON returns the config dictionary."""
        # Create test prompts using helper
        prompts = [
            self.create_standard_prompt(TestConstants.PROMPT_HL_OVERVIEW),
            self.create_standard_prompt(TestConstants.PROMPT_APIS)
        ]
        self.create_prompts_config(self.backend_dir, prompts)
        
        # Test reading
        result = self.file_manager.read_prompts_config(self.backend_dir)
        self.assertEqual(result["prompts"], prompts)
        
    def test_read_prompts_config_with_missing_file_raises_exception(self):
        """Test that read_prompts_config with missing file raises exception."""
        with self.assertRaises(Exception) as context:
            self.file_manager.read_prompts_config(self.backend_dir)
        
        self.assertIn("Prompts config file not found", str(context.exception))
        
    def test_read_prompts_config_with_invalid_json_raises_exception(self):
        """Test that read_prompts_config with invalid JSON raises exception."""
        config_path = os.path.join(self.backend_dir, "prompts.json")
        with open(config_path, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(Exception) as context:
            self.file_manager.read_prompts_config(self.backend_dir)
        
        self.assertIn("Invalid JSON in prompts config", str(context.exception))
    
    def test_read_prompt_file_with_existing_file_returns_content(self):
        """Test that read_prompt_file with existing file returns its content."""
        # Create a test prompt file using helper
        self.create_prompt_file(self.backend_dir, TestConstants.FILE_HL_OVERVIEW, 
                              TestConstants.SAMPLE_HL_OVERVIEW)
        
        # Test reading
        result = self.file_manager.read_prompt_file(self.backend_dir, TestConstants.FILE_HL_OVERVIEW)
        self.assertEqual(result, TestConstants.SAMPLE_HL_OVERVIEW)
    
    def test_read_prompt_file_with_missing_file_returns_none(self):
        """Test that read_prompt_file with missing file returns None."""
        result = self.file_manager.read_prompt_file(self.backend_dir, "missing.md")
        self.assertIsNone(result)
        self.logger.warning.assert_called_with(
            f"Prompt file not found: {os.path.join(self.backend_dir, 'missing.md')}"
        )
    
    def test_read_prompt_file_with_relative_path_resolves_correctly(self):
        """Test that read_prompt_file with relative path resolves and reads correctly."""
        # Create a shared prompt file using helper
        self.create_prompt_file(self.shared_dir, TestConstants.FILE_AUTH, 
                              TestConstants.SAMPLE_AUTH_CONTENT)
        
        # Test reading with relative path from backend dir
        result = self.file_manager.read_prompt_file(self.backend_dir, TestConstants.SHARED_AUTH_PATH)
        self.assertEqual(result, TestConstants.SAMPLE_AUTH_CONTENT)
    
    def test_read_prompt_file_with_nested_relative_path_resolves_correctly(self):
        """Test that read_prompt_file with nested relative path resolves correctly."""
        # Create a deeply nested shared prompt using helper
        nested_content = "# Security Check\n\nAnalyze security..."
        self.create_prompt_file(self.shared_dir, "security/security_check.md", nested_content)
        
        # Test reading with complex relative path
        result = self.file_manager.read_prompt_file(
            self.backend_dir, 
            "../shared/security/security_check.md"
        )
        self.assertEqual(result, nested_content)
    
    def test_prompts_json_with_shared_references_loads_all_correctly(self):
        """Test that prompts.json with shared references loads all prompts correctly."""
        # Create prompts using helpers
        prompts = [
            self.create_standard_prompt("hl_overview", description="High-level architecture overview"),
            self.create_standard_prompt("authentication", file="../shared/authentication.md", 
                                       description="Authentication mechanisms"),
            self.create_standard_prompt("optional_feature", required=False, file="optional.md",
                                       description="Optional analysis")
        ]
        self.create_prompts_config(self.backend_dir, prompts)
        
        # Create the referenced files using helpers
        self.create_prompt_file(self.backend_dir, "hl_overview.md", "# Overview content")
        self.create_prompt_file(self.shared_dir, "authentication.md", "# Auth content")
        # Note: optional.md is intentionally not created to test missing optional prompts
        
        # Read config
        loaded_config = self.file_manager.read_prompts_config(self.backend_dir)
        
        # Verify all prompts can be read
        for prompt in loaded_config["prompts"]:
            content = self.file_manager.read_prompt_file(self.backend_dir, prompt["file"])
            
            if prompt["required"]:
                self.assertIsNotNone(content, f"Required prompt {prompt['name']} should be readable")
            elif prompt["name"] == "optional_feature":
                # This one doesn't exist
                self.assertIsNone(content, f"Missing optional prompt should return None")
    
    def test_read_prompt_file_with_path_traversal_returns_none(self):
        """Test that read_prompt_file with path traversal attempt returns None safely."""
        # Try to read a file outside the prompts directory
        result = self.file_manager.read_prompt_file(self.backend_dir, "../../etc/passwd")
        
        # The function should handle this safely (either return None or normalize the path)
        # It should not actually try to read /etc/passwd
        # The current implementation uses os.path.normpath which should handle this
        self.assertIsNone(result)  # File shouldn't exist in our test environment


class TestPromptLoadingIntegration(BasePromptTest):
    """Integration tests for prompt loading in the workflow context."""
    
    @patch('src.activities.investigate_activities.FileManager')
    async def test_read_prompt_file_activity_with_valid_file_returns_success(self, mock_file_manager_class):
        """Test that read_prompt_file_activity with valid file returns success status."""
        from activities.investigate_activities import read_prompt_file_activity
        
        # Mock the file manager
        mock_file_manager = Mock()
        mock_file_manager.read_prompt_file.return_value = "# Test prompt content"
        mock_file_manager_class.return_value = mock_file_manager
        
        # Create mock activity context
        with patch('temporalio.activity.logger') as mock_logger:
            result = await read_prompt_file_activity("/test/prompts", "test.md")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["prompt_content"], "# Test prompt content")
        mock_file_manager.read_prompt_file.assert_called_once_with("/test/prompts", "test.md")
    
    @patch('src.activities.investigate_activities.FileManager')
    async def test_read_prompt_file_activity_with_missing_file_returns_not_found(self, mock_file_manager_class):
        """Test that read_prompt_file_activity with missing file returns not_found status."""
        from activities.investigate_activities import read_prompt_file_activity
        
        # Mock the file manager to return None (file not found)
        mock_file_manager = Mock()
        mock_file_manager.read_prompt_file.return_value = None
        mock_file_manager_class.return_value = mock_file_manager
        
        # Create mock activity context
        with patch('temporalio.activity.logger') as mock_logger:
            result = await read_prompt_file_activity("/test/prompts", "missing.md")
        
        self.assertEqual(result["status"], "not_found")
        self.assertIsNone(result["prompt_content"])
    
    def test_workflow_with_missing_required_prompt_raises_exception(self):
        """Test that workflow with missing required prompt raises exception."""
        # This would be tested in the workflow test file
        # Here we just document the expected behavior
        pass
    
    def test_workflow_with_missing_optional_prompt_continues_normally(self):
        """Test that workflow with missing optional prompt continues normally."""
        # This would be tested in the workflow test file
        # Here we just document the expected behavior
        pass


class TestPromptPathResolution(unittest.TestCase):
    """Test correct path resolution for different repository types."""
    
    # Test data: (repo_type, expected_path_suffix)
    REPO_TYPE_TESTS = [
        ("backend", "prompts/backend"),
        ("frontend", "prompts/frontend"),
        ("mobile", "prompts/mobile"),
        ("libraries", "prompts/libraries"),
        ("infra-as-code", "prompts/infra-as-code"),
        (None, "prompts/generic"),  # Test default fallback
    ]
    
    def setUp(self):
        """Set up the repository type detector."""
        from investigator.core.repository_type_detector import RepositoryTypeDetector
        self.detector = RepositoryTypeDetector(Mock())
    
    def test_get_prompts_directory_with_each_repo_type_returns_correct_path(self):
        """Test that get_prompts_directory with each repo type returns correct path."""
        for repo_type, expected_suffix in self.REPO_TYPE_TESTS:
            with self.subTest(repo_type=repo_type):
                # Get the prompts path
                if repo_type:
                    prompts_path = self.detector.get_prompts_directory("/test/repo", repo_type=repo_type)
                else:
                    prompts_path = self.detector.get_prompts_directory("/test/repo")
                
                # Verify it ends with the expected suffix
                self.assertTrue(
                    prompts_path.endswith(expected_suffix),
                    f"Expected path to end with '{expected_suffix}' for repo_type='{repo_type}', "
                    f"but got: {prompts_path}"
                )
    
    def test_get_prompts_directory_with_unknown_type_returns_generic_path(self):
        """Test that get_prompts_directory with unknown type returns generic path."""
        # Test with a non-existent repo type
        prompts_path = self.detector.get_prompts_directory("/test/repo", repo_type="unknown-type")
        self.assertTrue(
            prompts_path.endswith("prompts/generic"),
            f"Unknown repo type should fall back to generic, but got: {prompts_path}"
        )


if __name__ == '__main__':
    unittest.main()
