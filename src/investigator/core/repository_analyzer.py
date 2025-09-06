"""
Repository structure analysis for the Claude Investigator.
"""

import os
from .config import Config


class RepositoryAnalyzer:
    """Handles repository structure analysis."""
    
    def __init__(self, logger):
        self.logger = logger
    
    def get_structure(self, repo_path: str) -> str:
        """
        Get the file and directory structure of the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            String representation of the repository structure with repository name
        """
        self.logger.debug(f"Scanning repository structure in: {repo_path}")
        
        # Extract repository name from the path
        repo_name = os.path.basename(repo_path.rstrip(os.sep))
        
        structure = []
        # Add repository name as header
        structure.append(f"Repository: {repo_name}")
        structure.append("=" * (len(f"Repository: {repo_name}")))
        structure.append("")  # Empty line for better formatting
        
        stats = {'files': 0, 'dirs': 0}
        
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            dirs[:] = [d for d in dirs if d != '.git']
            
            level = root.replace(repo_path, '').count(os.sep)
            indent = '  ' * level
            
            # Add directory
            if level > 0:
                dir_name = os.path.basename(root)
                structure.append(f"{indent}{Config.DIR_ICON} {dir_name}/")
                stats['dirs'] += 1
            
            # Add files
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                structure.append(f"{indent}{Config.FILE_ICON} {relative_path}")
                stats['files'] += 1
        
        self.logger.debug(f"Repository structure scan complete for '{repo_name}': {stats['dirs']} directories, {stats['files']} files")
        return '\n'.join(structure) 