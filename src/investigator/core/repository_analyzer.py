"""
Repository structure analysis for the Claude Investigator.
"""

import os
from .config import Config


class RepositoryAnalyzer:
    """Handles repository structure analysis."""
    
    # Maximum depth for directory traversal (0 = root level)
    MAX_DEPTH = 3
    
    # Directories to always skip
    SKIP_DIRS = {
        '.git',
        'node_modules',
        '__pycache__',
        '.venv',
        'venv',
        '.env',
        'dist',
        'build',
        '.next',
        '.nuxt',
        'coverage',
        '.pytest_cache',
        '.mypy_cache',
        '.tox',
        'egg-info',
        '.eggs',
    }
    
    def __init__(self, logger):
        self.logger = logger
    
    def get_structure(self, repo_path: str, max_depth: int = None) -> str:
        """
        Get the file and directory structure of the repository.
        
        Args:
            repo_path: Path to the repository
            max_depth: Maximum depth to traverse (default: MAX_DEPTH)
            
        Returns:
            String representation of the repository structure with repository name
        """
        if max_depth is None:
            max_depth = self.MAX_DEPTH
            
        self.logger.debug(f"Scanning repository structure in: {repo_path} (max depth: {max_depth})")
        
        # Extract repository name from the path
        repo_name = os.path.basename(repo_path.rstrip(os.sep))
        
        structure = []
        # Add repository name as header
        structure.append(f"Repository: {repo_name}")
        structure.append("=" * (len(f"Repository: {repo_name}")))
        structure.append("")  # Empty line for better formatting
        
        stats = {'files': 0, 'dirs': 0, 'nested': 0}
        
        for root, dirs, files in os.walk(repo_path):
            # Calculate depth relative to repo_path
            rel_path = os.path.relpath(root, repo_path)
            if rel_path == '.':
                level = 0
            else:
                level = rel_path.count(os.sep) + 1
            
            indent = '  ' * level
            
            # Filter out directories we should skip
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS and not d.endswith('.egg-info')]
            
            # Add directory (except for root)
            if level > 0:
                dir_name = os.path.basename(root)
                structure.append(f"{indent}{Config.DIR_ICON} {dir_name}/")
                stats['dirs'] += 1
            
            # If we're at max depth, don't descend further
            if level >= max_depth:
                # Show [NESTED] marker for directories we won't explore
                if dirs:
                    for dir_name in sorted(dirs):
                        structure.append(f"{indent}  {Config.DIR_ICON} {dir_name}/ [NESTED]")
                        stats['nested'] += 1
                dirs[:] = []  # Stop os.walk from descending
                
                # At max depth, indicate files exist but don't list them
                if files:
                    file_count = len(files)
                    structure.append(f"{indent}  [{file_count} files]")
            else:
                # Add files (only if within depth limit)
                file_indent = '  ' * (level + 1) if level > 0 else '  '
                for file in sorted(files):
                    structure.append(f"{file_indent}{Config.FILE_ICON} {file}")
                    stats['files'] += 1
        
        self.logger.debug(
            f"Repository structure scan complete for '{repo_name}': "
            f"{stats['dirs']} directories, {stats['files']} files, {stats['nested']} nested (not expanded)"
        )
        return '\n'.join(structure) 