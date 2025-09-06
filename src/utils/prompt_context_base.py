"""
Abstract base classes for PromptContext and PromptContextManager.

These base classes define the interface for managing analysis data references,
allowing different implementations (DynamoDB, file-based, etc.) for different environments.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PromptContextBase(ABC):
    """
    Abstract base class for managing prompt, repository structure, context, and results.
    
    Subclasses must implement the storage-specific methods.
    """
    
    repo_name: str
    step_name: str = None
    data_reference_key: str = None
    context_reference_keys: List[str] = field(default_factory=list)
    result_reference_key: str = None
    prompt_version: str = "1"
    
    @classmethod
    def create_for_step(cls, repo_name: str, step_name: str, prompt_version: str = "1") -> 'PromptContextBase':
        """
        Create a new PromptContext for a specific analysis step.
        
        Args:
            repo_name: Name of the repository being analyzed
            step_name: Name of the analysis step
            prompt_version: Version of the prompt (default "1")
            
        Returns:
            New PromptContext instance
        """
        return cls(repo_name=repo_name, step_name=step_name, prompt_version=prompt_version)
    
    @abstractmethod
    def save_prompt_data(self, prompt_content: str, repo_structure: str, ttl_minutes: int = 60) -> str:
        """
        Save prompt and repository structure to storage.
        
        Args:
            prompt_content: The prompt template content
            repo_structure: Repository structure string
            ttl_minutes: TTL for the data in minutes (may be ignored by some implementations)
            
        Returns:
            Reference key for the saved data
        """
        pass
    
    @abstractmethod
    def get_prompt_and_context(self) -> Dict[str, Any]:
        """
        Retrieve prompt data and context from storage.
        
        Returns:
            Dictionary containing prompt_content, repo_structure, and context
        """
        pass
    
    @abstractmethod
    def get_result(self) -> Optional[str]:
        """
        Retrieve the analysis result from storage.
        
        Returns:
            The result content or None if not found
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Clean up all temporary data associated with this context.
        """
        pass
    
    def add_context_reference(self, reference_key: str):
        """
        Add a context reference key from a previous step.
        
        Args:
            reference_key: Reference key of a previous step's result
        """
        if reference_key and reference_key not in self.context_reference_keys:
            self.context_reference_keys.append(reference_key)
            logger.debug(f"Added context reference: {reference_key}")
    
    def add_context_from_steps(self, step_names: List[str], step_results: Dict[str, str]):
        """
        Add context references from specific previous steps.
        
        Args:
            step_names: List of step names to include as context
            step_results: Dictionary mapping step names to their result reference keys
        """
        for step_name in step_names:
            if step_name in step_results:
                self.add_context_reference(step_results[step_name])
            else:
                logger.warning(f"Step {step_name} not found in results for context")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization (e.g., passing between activities).
        
        Returns:
            Dictionary representation of the context
        """
        return {
            "repo_name": self.repo_name,
            "step_name": self.step_name,
            "data_reference_key": self.data_reference_key,
            "context_reference_keys": self.context_reference_keys,
            "result_reference_key": self.result_reference_key,
            "prompt_version": self.prompt_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptContextBase':
        """
        Create PromptContext from dictionary (e.g., from activity parameters).
        
        Args:
            data: Dictionary containing context data
            
        Returns:
            PromptContext instance
        """
        return cls(
            repo_name=data.get("repo_name"),
            step_name=data.get("step_name"),
            data_reference_key=data.get("data_reference_key"),
            context_reference_keys=data.get("context_reference_keys", []),
            result_reference_key=data.get("result_reference_key"),
            prompt_version=data.get("prompt_version", "1")
        )
    
    def to_json(self) -> str:
        """
        Convert to JSON string for serialization.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PromptContextBase':
        """
        Create PromptContext from JSON string.
        
        Args:
            json_str: JSON string containing context data
            
        Returns:
            PromptContext instance
        """
        return cls.from_dict(json.loads(json_str))
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"{self.__class__.__name__}(repo={self.repo_name}, step={self.step_name}, "
                f"data_key={self.data_reference_key[:20] if self.data_reference_key else None}..., "
                f"context_keys={len(self.context_reference_keys)}, "
                f"result_key={self.result_reference_key[:20] if self.result_reference_key else None}...)")


class PromptContextManagerBase(ABC):
    """
    Abstract base class for managing multiple PromptContexts across analysis steps.
    """
    
    def __init__(self, repo_name: str):
        """
        Initialize the manager for a repository.
        
        Args:
            repo_name: Name of the repository being analyzed
        """
        self.repo_name = repo_name
        self.contexts: Dict[str, PromptContextBase] = {}
        self.step_results: Dict[str, str] = {}  # Maps step names to result keys
        logger.info(f"Initialized {self.__class__.__name__} for {repo_name}")
    
    @abstractmethod
    def create_context_for_step(self, step_name: str, context_config: List = None) -> PromptContextBase:
        """
        Create a new context for an analysis step with proper context references.
        
        Args:
            step_name: Name of the analysis step
            context_config: Configuration for which previous steps to include as context
            
        Returns:
            New PromptContext instance
        """
        pass
    
    @abstractmethod
    def retrieve_all_results(self) -> Dict[str, str]:
        """
        Retrieve all results from storage.
        
        Returns:
            Dictionary mapping step names to their result content
        """
        pass
    
    def register_result(self, step_name: str, result_key: str):
        """
        Register a step's result key for use as context in later steps.
        
        Args:
            step_name: Name of the completed step
            result_key: Reference key of the step's result
        """
        self.step_results[step_name] = result_key
        logger.info(f"Registered result for {step_name}: {result_key}")
    
    def get_all_result_keys(self) -> List[str]:
        """
        Get all result reference keys.
        
        Returns:
            List of all result reference keys
        """
        return list(self.step_results.values())
    
    def cleanup_all(self):
        """Clean up all contexts and their associated data."""
        for context in self.contexts.values():
            context.cleanup()
        logger.info(f"Cleaned up {len(self.contexts)} contexts for {self.repo_name}")
