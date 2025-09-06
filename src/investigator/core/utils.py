"""
Utility functions for the Claude Investigator.
"""

import os
import re
from .config import Config


class Utils:
    """Utility functions."""
    
    @staticmethod
    def extract_repo_name(repo_location: str) -> str:
        """
        Extract repository name from URL or path.
        
        Args:
            repo_location: URL or path to the repository
            
        Returns:
            Repository name
        """
        # Handle different URL formats
        if repo_location.startswith(('http://', 'https://', 'git://', 'ssh://')):
            repo_name = repo_location.rstrip('/').split('/')[-1]
        elif repo_location.startswith('git@'):
            repo_name = repo_location.split(':')[-1].rstrip('/')
        else:
            repo_name = os.path.basename(repo_location.rstrip('/'))
        
        # Remove .git extension if present
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        # Clean up the name to be filesystem-safe
        repo_name = re.sub(r'[^\w\-_.]', '_', repo_name)
        
        return repo_name
    
    @staticmethod
    def get_directory_size(path: str) -> str:
        """Get the size of a directory in human-readable format."""
        total_size = 0
        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                    file_count += 1
                except (OSError, IOError):
                    pass
        
        # Convert to human-readable format
        for unit in Config.SIZE_UNITS:
            if total_size < 1024.0:
                return f"{total_size:.1f} {unit} ({file_count} files)"
            total_size /= 1024.0
        
        return f"{total_size:.1f} TB ({file_count} files)" 