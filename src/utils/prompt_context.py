"""
PromptContext factory and utilities for managing analysis data references.

This module provides factory functions to create the appropriate PromptContext
implementation based on the environment (DynamoDB for production, file-based for local testing).
"""

import os
import logging
from typing import Dict, Any, Union

from .prompt_context_base import PromptContextBase, PromptContextManagerBase
from .prompt_context_dynamodb import DynamoDBPromptContext, DynamoDBPromptContextManager
from .prompt_context_file import FileBasedPromptContext, FileBasedPromptContextManager

logger = logging.getLogger(__name__)


def get_storage_backend() -> str:
    """
    Determine which storage backend to use based on environment.
    
    Returns:
        'dynamodb' for production or 'file' for local testing
    """
    # Check environment variables
    storage_backend = os.environ.get('PROMPT_CONTEXT_STORAGE', 'auto')
    
    if storage_backend == 'file':
        return 'file'
    elif storage_backend == 'dynamodb':
        return 'dynamodb'
    elif storage_backend == 'auto':
        # Auto-detect based on environment
        # If we're running in ECS or have AWS credentials, use DynamoDB
        # Otherwise, use file-based storage
        
        # Check if we're in ECS
        if os.environ.get('ECS_CONTAINER_METADATA_URI'):
            logger.info("Detected ECS environment, using DynamoDB storage")
            return 'dynamodb'
        
        # Check if we have AWS credentials
        if os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('AWS_PROFILE'):
            logger.info("Detected AWS credentials, using DynamoDB storage")
            return 'dynamodb'
        
        # Check if we're in a Temporal worker environment
        if os.environ.get('TEMPORAL_WORKER') == 'true':
            logger.info("Detected Temporal worker environment, using DynamoDB storage")
            return 'dynamodb'
        
        # Default to file-based for local development
        logger.info("No production environment detected, using file-based storage")
        return 'file'
    else:
        logger.warning(f"Unknown storage backend: {storage_backend}, defaulting to file")
        return 'file'


def create_prompt_context(repo_name: str, step_name: str, prompt_version: str = "1") -> PromptContextBase:
    """
    Factory function to create the appropriate PromptContext implementation.
    
    Args:
        repo_name: Name of the repository being analyzed
        step_name: Name of the analysis step
        prompt_version: Version of the prompt (default "1")
        
    Returns:
        PromptContext instance (either DynamoDB or file-based)
    """
    backend = get_storage_backend()
    
    if backend == 'dynamodb':
        logger.debug(f"Creating DynamoDBPromptContext for {repo_name}/{step_name} v{prompt_version}")
        return DynamoDBPromptContext.create_for_step(repo_name, step_name, prompt_version)
    else:
        logger.debug(f"Creating FileBasedPromptContext for {repo_name}/{step_name} v{prompt_version}")
        return FileBasedPromptContext.create_for_step(repo_name, step_name, prompt_version)


def create_prompt_context_from_dict(data: Dict[str, Any]) -> PromptContextBase:
    """
    Factory function to create PromptContext from dictionary.
    
    Args:
        data: Dictionary containing context data
        
    Returns:
        PromptContext instance (either DynamoDB or file-based)
    """
    backend = get_storage_backend()
    
    if backend == 'dynamodb':
        logger.debug(f"Creating DynamoDBPromptContext from dict")
        return DynamoDBPromptContext.from_dict(data)
    else:
        logger.debug(f"Creating FileBasedPromptContext from dict")
        return FileBasedPromptContext.from_dict(data)


def create_prompt_context_manager(repo_name: str) -> PromptContextManagerBase:
    """
    Factory function to create the appropriate PromptContextManager implementation.
    
    Args:
        repo_name: Name of the repository being analyzed
        
    Returns:
        PromptContextManager instance (either DynamoDB or file-based)
    """
    backend = get_storage_backend()
    
    if backend == 'dynamodb':
        logger.debug(f"Creating DynamoDBPromptContextManager for {repo_name}")
        return DynamoDBPromptContextManager(repo_name)
    else:
        logger.debug(f"Creating FileBasedPromptContextManager for {repo_name}")
        return FileBasedPromptContextManager(repo_name)


# Re-export the base classes for type hints
PromptContext = PromptContextBase
PromptContextManager = PromptContextManagerBase

# For backward compatibility, provide direct access to factory functions
def PromptContext_create_for_step(repo_name: str, step_name: str) -> PromptContextBase:
    """Backward compatibility wrapper for create_prompt_context."""
    return create_prompt_context(repo_name, step_name)

def PromptContext_from_dict(data: Dict[str, Any]) -> PromptContextBase:
    """Backward compatibility wrapper for create_prompt_context_from_dict."""
    return create_prompt_context_from_dict(data)