"""
Repository type detection based on provided type parameter.
"""

import os
from typing import Optional, Tuple
from pathlib import Path


class RepositoryTypeDetector:
    """Determines repository type from provided parameter."""
    
    def __init__(self, logger):
        """
        Initialize the repository type detector.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
    
    def get_prompts_directory(self, repo_path: str, repo_type: Optional[str] = None, repo_url: Optional[str] = None) -> str:
        """
        Get the appropriate prompts directory for a repository.
        
        Args:
            repo_path: Path to the repository (used for logging)
            repo_type: Repository type (defaults to "generic" if not provided)
            repo_url: Repository URL (not used anymore, kept for backward compatibility)
            
        Returns:
            Path to the prompts directory to use
        """
        # Use the provided type or default to generic
        prompt_dir = repo_type if repo_type else "generic"
        
        if repo_type:
            self.logger.info(f"Using repository type: {repo_type}")
        else:
            self.logger.info("No repository type specified, defaulting to generic")
        
        # Build the full path to the prompts directory
        src_root = Path(__file__).parent.parent.parent.parent
        prompts_path = src_root / "prompts" / prompt_dir
        
        # Validate the directory exists
        if not prompts_path.exists():
            self.logger.warning(f"Prompts directory not found: {prompts_path}, falling back to generic")
            prompts_path = src_root / "prompts" / "generic"
            prompt_dir = "generic"
        
        self.logger.info(f"Using prompts directory: {prompts_path}")
        return str(prompts_path)