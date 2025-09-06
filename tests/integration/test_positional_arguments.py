"""
Integration tests for positional argument parsing in mise scripts.

Tests that the actual shell scripts correctly parse positional arguments and convert them
to the appropriate format for the client using the dry-run flag.
"""

import pytest
import subprocess
import os
import re
from pathlib import Path


class TestPositionalArgumentParsing:
    """Test suite for positional argument parsing in shell scripts."""
    
    @pytest.fixture
    def script_root(self):
        """Get the root directory where scripts are located."""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def full_script(self, script_root):
        """Get path to the actual full.sh script."""
        return script_root / "scripts" / "full.sh"
    
    @pytest.fixture
    def investigate_script(self, script_root):
        """Get path to the actual investigate.sh script."""
        return script_root / "scripts" / "investigate.sh"
    
    def extract_argument_parsing_logic(self, script_path):
        """Extract just the argument parsing logic from the script."""
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Extract the argument parsing section
        start_marker = "# Parse positional arguments"
        end_marker = "# Build arguments for client"
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"Could not find argument parsing section in {script_path}")
        
        parsing_logic = content[start_idx:end_idx]
        
        # Create a minimal test script
        # Replace exit statements with error reporting for testing
        test_parsing_logic = parsing_logic.replace('exit 1', 'echo "ERROR:$arg requires argument" >&2; exit 1')
        
        test_script = f'''#!/bin/bash
{test_parsing_logic}

# Output results in parseable format
echo "FORCE_FLAG:$FORCE_FLAG"
echo "CLAUDE_MODEL:$CLAUDE_MODEL"
echo "MAX_TOKENS:$MAX_TOKENS"
echo "SLEEP_HOURS:$SLEEP_HOURS"
echo "CHUNK_SIZE:$CHUNK_SIZE"
'''
        return test_script

    def run_script(self, script_path, args):
        """Run the script's argument parsing logic in isolation."""
        try:
            # Extract and create minimal test script
            test_script_content = self.extract_argument_parsing_logic(script_path)
            
            # Create temporary script
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(test_script_content)
                temp_script_path = f.name
            
            os.chmod(temp_script_path, 0o755)
            
            try:
                result = subprocess.run(
                    ["bash", temp_script_path] + args,
                    capture_output=True,
                    text=True,
                    timeout=10  # Much shorter timeout for parsing-only test
                )
                
                if result.returncode != 0:
                    return None, result.stderr.strip()
                
                # Parse output
                output = {}
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        output[key] = value
                
                return output, None
                
            finally:
                # Cleanup temp file
                os.unlink(temp_script_path)
            
        except subprocess.TimeoutExpired:
            return None, "Script timed out"
        except Exception as e:
            return None, f"Script execution failed: {str(e)}"
    
    def test_real_scripts_comprehensive(self, full_script, investigate_script):
        """Test both real scripts with comprehensive argument combinations."""
        
        # Test scenarios for both scripts
        test_scenarios = [
            # Basic model override
            (['model', 'claude-3-opus-20240229'], {
                'CLAUDE_MODEL': 'claude-3-opus-20240229',
                'FORCE_FLAG': '',
                'MAX_TOKENS': '',
                'SLEEP_HOURS': ''
            }),
            # Force flag only
            (['force'], {
                'FORCE_FLAG': '--force',
                'CLAUDE_MODEL': '',
                'MAX_TOKENS': '',
                'SLEEP_HOURS': ''
            }),
            # Max tokens only
            (['max-tokens', '8000'], {
                'MAX_TOKENS': '8000',
                'FORCE_FLAG': '',
                'CLAUDE_MODEL': '',
                'SLEEP_HOURS': ''
            }),
            # Sleep hours with fractional value
            (['sleep-hours', '0.5'], {
                'SLEEP_HOURS': '0.5',
                'FORCE_FLAG': '',
                'CLAUDE_MODEL': '',
                'MAX_TOKENS': ''
            }),
            # Combined arguments
            (['force', 'model', 'claude-3-5-sonnet-20241022', 'max-tokens', '6000', 'sleep-hours', '1.5'], {
                'FORCE_FLAG': '--force',
                'CLAUDE_MODEL': 'claude-3-5-sonnet-20241022',
                'MAX_TOKENS': '6000',
                'SLEEP_HOURS': '1.5'
            }),
            # Mixed order arguments
            (['sleep-hours', '2', 'force', 'max-tokens', '4000', 'model', 'claude-3-haiku-20241022'], {
                'FORCE_FLAG': '--force',
                'CLAUDE_MODEL': 'claude-3-haiku-20241022',
                'MAX_TOKENS': '4000',
                'SLEEP_HOURS': '2'
            }),
            # Empty arguments
            ([], {
                'FORCE_FLAG': '',
                'CLAUDE_MODEL': '',
                'MAX_TOKENS': '',
                'SLEEP_HOURS': ''
            })
        ]
        
        # Test both scripts
        for script_name, script_path in [("full.sh", full_script), ("investigate.sh", investigate_script)]:
            for args, expected in test_scenarios:
                output, error = self.run_script(script_path, args)
                assert error is None, f"{script_name} failed with args {args}: {error}"
                
                for key, expected_value in expected.items():
                    actual_value = output.get(key, '')
                    assert actual_value == expected_value, f"{script_name} with args {args}: Expected {key}={expected_value}, got {actual_value}"
    
    def test_fractional_sleep_hours_both_scripts(self, full_script, investigate_script):
        """Test fractional sleep hours values with both scripts."""
        test_cases = ['0.25', '0.1', '2.5', '12.75']
        
        for script_name, script_path in [("full.sh", full_script), ("investigate.sh", investigate_script)]:
            for value in test_cases:
                output, error = self.run_script(script_path, ['sleep-hours', value])
                assert error is None, f"{script_name} failed for sleep-hours {value}: {error}"
                assert output['SLEEP_HOURS'] == value, f"{script_name}: Expected sleep-hours={value}, got {output['SLEEP_HOURS']}"
    
    def test_valid_claude_models_both_scripts(self, full_script, investigate_script):
        """Test with various valid Claude model names on both scripts."""
        valid_models = [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-sonnet-4-20250514'
        ]
        
        for script_name, script_path in [("full.sh", full_script), ("investigate.sh", investigate_script)]:
            for model in valid_models:
                output, error = self.run_script(script_path, ['model', model])
                assert error is None, f"{script_name} failed for model {model}: {error}"
                assert output['CLAUDE_MODEL'] == model, f"{script_name}: Expected model={model}, got {output['CLAUDE_MODEL']}"
    
    def test_chunk_size_values_both_scripts(self, full_script, investigate_script):
        """Test chunk size values with both scripts."""
        test_cases = ['1', '4', '8', '12', '20']
        
        for script_name, script_path in [("full.sh", full_script), ("investigate.sh", investigate_script)]:
            for value in test_cases:
                output, error = self.run_script(script_path, ['chunk-size', value])
                assert error is None, f"{script_name} failed for chunk-size {value}: {error}"
                assert output['CHUNK_SIZE'] == value, f"{script_name}: Expected chunk-size={value}, got {output['CHUNK_SIZE']}"
    
    def test_chunk_size_missing_argument_both_scripts(self, full_script, investigate_script):
        """Test that chunk-size without an argument produces an error."""
        for script_name, script_path in [("full.sh", full_script), ("investigate.sh", investigate_script)]:
            output, error = self.run_script(script_path, ['chunk-size'])
            assert error == "ERROR:chunk-size requires argument", f"{script_name}: Expected error for missing chunk-size argument"
    
    def test_realistic_usage_scenarios_both_scripts(self, full_script, investigate_script):
        """Test realistic usage scenarios with both scripts."""
        scenarios = [
            # Quick testing
            (['force', 'sleep-hours', '0.1'], {
                'FORCE_FLAG': '--force',
                'SLEEP_HOURS': '0.1'
            }),
            # Cheap model for development
            (['model', 'claude-3-haiku-20241022', 'max-tokens', '3000'], {
                'CLAUDE_MODEL': 'claude-3-haiku-20241022',
                'MAX_TOKENS': '3000'
            }),
            # Production settings
            (['model', 'claude-3-opus-20240229', 'max-tokens', '8000', 'sleep-hours', '24'], {
                'CLAUDE_MODEL': 'claude-3-opus-20240229',
                'MAX_TOKENS': '8000',
                'SLEEP_HOURS': '24'
            }),
            # Force with custom model and timing
            (['force', 'model', 'claude-3-5-sonnet-20241022', 'sleep-hours', '2.5'], {
                'FORCE_FLAG': '--force',
                'CLAUDE_MODEL': 'claude-3-5-sonnet-20241022',
                'SLEEP_HOURS': '2.5'
            }),
            # Custom chunk size for parallel processing
            (['chunk-size', '4', 'sleep-hours', '1'], {
                'CHUNK_SIZE': '4',
                'SLEEP_HOURS': '1'
            }),
            # All overrides combined
            (['force', 'model', 'claude-3-opus-20240229', 'max-tokens', '8000', 'sleep-hours', '12', 'chunk-size', '6'], {
                'FORCE_FLAG': '--force',
                'CLAUDE_MODEL': 'claude-3-opus-20240229',
                'MAX_TOKENS': '8000',
                'SLEEP_HOURS': '12',
                'CHUNK_SIZE': '6'
            })
        ]
        
        for script_name, script_path in [("full.sh", full_script), ("investigate.sh", investigate_script)]:
            for args, expected in scenarios:
                output, error = self.run_script(script_path, args)
                assert error is None, f"{script_name} scenario failed with args {args}: {error}"
                
                for key, expected_value in expected.items():
                    actual_value = output.get(key, '')
                    assert actual_value == expected_value, f"{script_name} scenario: Expected {key}={expected_value}, got {actual_value}"
    
    def test_real_script_exists(self, script_root):
        """Test that the actual scripts exist and are executable."""
        full_script = script_root / "scripts" / "full.sh"
        investigate_script = script_root / "scripts" / "investigate.sh"
        
        assert full_script.exists(), "scripts/full.sh should exist"
        assert investigate_script.exists(), "scripts/investigate.sh should exist"
        
        # Check if they're executable
        assert os.access(full_script, os.X_OK), "scripts/full.sh should be executable"
        assert os.access(investigate_script, os.X_OK), "scripts/investigate.sh should be executable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
