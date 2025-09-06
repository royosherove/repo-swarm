#!/usr/bin/env python3
"""
Example usage of the Claude Investigator.

This script demonstrates how to use the ClaudeInvestigator class to analyze
repository structure and generate architecture documentation.
"""

import os
from investigator import ClaudeInvestigator, investigate_repo


def main():
    """Example usage of the Claude Investigator."""
    
    # Example 1: Using the convenience function with default logging
    print("=== Example 1: Using convenience function (INFO logging) ===")
    try:
        # Replace with an actual repository URL
        repo_url = "https://github.com/example/repo"
        
        # Make sure you have your Claude API key set
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("Please set ANTHROPIC_API_KEY environment variable")
            return
        
        arch_file_path = investigate_repo(repo_url)
        print(f"Analysis completed! Check: {arch_file_path}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Using the class directly with DEBUG logging
    print("=== Example 2: Using ClaudeInvestigator class (DEBUG logging) ===")
    try:
        # You can also pass the API key directly
        api_key = os.getenv('ANTHROPIC_API_KEY')
        investigator = ClaudeInvestigator(api_key=api_key, log_level="DEBUG")
        
        # Replace with an actual repository URL
        repo_url = "https://github.com/example/repo"
        
        arch_file_path = investigator.investigate_repository(repo_url)
        print(f"Analysis completed! Check: {arch_file_path}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Using convenience function with custom log level
    print("=== Example 3: Using convenience function (WARNING logging) ===")
    try:
        # Replace with an actual repository URL
        repo_url = "https://github.com/example/repo"
        
        # Make sure you have your Claude API key set
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("Please set ANTHROPIC_API_KEY environment variable")
            return
        
        # Use WARNING level for minimal logging
        arch_file_path = investigate_repo(repo_url, log_level="WARNING")
        print(f"Analysis completed! Check: {arch_file_path}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 