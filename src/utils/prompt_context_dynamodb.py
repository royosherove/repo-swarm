"""
DynamoDB implementation of PromptContext and PromptContextManager.

This implementation stores all data in DynamoDB with automatic TTL for cleanup.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .prompt_context_base import PromptContextBase, PromptContextManagerBase
from .dynamodb_client import get_dynamodb_client

logger = logging.getLogger(__name__)


@dataclass
class DynamoDBPromptContext(PromptContextBase):
    """
    DynamoDB implementation of PromptContext.
    
    Stores all data in DynamoDB with reference keys.
    """
    
    _dynamodb_client: Any = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Initialize DynamoDB client after dataclass initialization."""
        if self._dynamodb_client is None:
            self._dynamodb_client = get_dynamodb_client()
    
    def save_prompt_data(self, prompt_content: str, repo_structure: str, ttl_minutes: int = 60) -> str:
        """
        Save prompt and repository structure to DynamoDB.
        
        Args:
            prompt_content: The prompt template content
            repo_structure: Repository structure string
            ttl_minutes: TTL for the data in minutes
            
        Returns:
            Reference key for the saved data
        """
        # Generate unique reference key
        self.data_reference_key = f"{self.repo_name}_{self.step_name}_{str(uuid.uuid4())[:8]}"
        
        logger.info(f"Saving prompt data to DynamoDB with key: {self.data_reference_key}")
        
        # Save to DynamoDB
        result = self._dynamodb_client.save_temporary_analysis_data(
            reference_key=self.data_reference_key,
            prompt_content=prompt_content,
            repo_structure=repo_structure,
            context=None,  # Context is handled separately through reference keys
            ttl_minutes=ttl_minutes
        )
        
        if result["status"] != "success":
            raise Exception(f"Failed to save prompt data for step {self.step_name}")
        
        return self.data_reference_key
    
    def get_prompt_and_context(self) -> Dict[str, Any]:
        """
        Retrieve prompt data and context from DynamoDB.
        
        Returns:
            Dictionary containing prompt_content, repo_structure, and context
        """
        if not self.data_reference_key:
            raise ValueError("No data reference key set. Call save_prompt_data first.")
        
        logger.info(f"Retrieving prompt data from DynamoDB with key: {self.data_reference_key}")
        
        # Get main prompt data
        temp_data = self._dynamodb_client.get_temporary_analysis_data(self.data_reference_key)
        if not temp_data:
            raise Exception(f"No temporary analysis data found for key: {self.data_reference_key}")
        
        prompt_content = temp_data.get('prompt_content')
        repo_structure = temp_data.get('repo_structure')
        
        # Build context from reference keys
        context = None
        if self.context_reference_keys:
            logger.info(f"Building context from {len(self.context_reference_keys)} references")
            context_parts = []
            
            for context_key in self.context_reference_keys:
                result = self._dynamodb_client.get_analysis_result(context_key)
                if result:
                    # Extract step name from key for better formatting
                    parts = context_key.split('_')
                    step_name = parts[1] if len(parts) > 1 else context_key
                    context_parts.append(f"## {step_name}\n\n{result}")
                else:
                    logger.warning(f"No result found for context key: {context_key}")
            
            if context_parts:
                context = "\n\n".join(context_parts)
        
        return {
            "prompt_content": prompt_content,
            "repo_structure": repo_structure,
            "context": context
        }
    
    def save_result(self, result_content: str, ttl_minutes: int = 60) -> str:
        """
        Save analysis result to DynamoDB.
        
        Args:
            result_content: The analysis result content
            ttl_minutes: TTL for the result in minutes
            
        Returns:
            Reference key for the saved result
        """
        # Generate unique result key
        self.result_reference_key = f"{self.repo_name}_{self.step_name}_result_{str(uuid.uuid4())[:8]}"
        
        logger.info(f"Saving result to DynamoDB with key: {self.result_reference_key}")
        
        # Save to DynamoDB
        save_result = self._dynamodb_client.save_analysis_result(
            reference_key=self.result_reference_key,
            result_content=result_content,
            step_name=self.step_name,
            ttl_minutes=ttl_minutes
        )
        
        if save_result["status"] != "success":
            raise Exception(f"Failed to save analysis result for step {self.step_name}")
        
        return self.result_reference_key
    
    def get_result(self) -> Optional[str]:
        """
        Retrieve the analysis result from DynamoDB.
        
        Returns:
            The result content or None if not found
        """
        if not self.result_reference_key:
            logger.warning("No result reference key set")
            return None
        
        return self._dynamodb_client.get_analysis_result(self.result_reference_key)
    
    def cleanup(self):
        """
        Clean up all temporary data associated with this context from DynamoDB.
        """
        keys_to_cleanup = []
        
        if self.data_reference_key:
            keys_to_cleanup.append(self.data_reference_key)
        
        if self.result_reference_key:
            keys_to_cleanup.append(self.result_reference_key)
        
        for key in keys_to_cleanup:
            try:
                self._dynamodb_client.delete_temporary_analysis_data(key)
                logger.info(f"Cleaned up from DynamoDB: {key}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {key} from DynamoDB: {str(e)}")


class DynamoDBPromptContextManager(PromptContextManagerBase):
    """
    DynamoDB implementation of PromptContextManager.
    """
    
    def create_context_for_step(self, step_name: str, context_config: List = None) -> DynamoDBPromptContext:
        """
        Create a new DynamoDB context for an analysis step with proper context references.
        
        Args:
            step_name: Name of the analysis step
            context_config: Configuration for which previous steps to include as context
            
        Returns:
            New DynamoDBPromptContext instance
        """
        context = DynamoDBPromptContext.create_for_step(self.repo_name, step_name)
        
        # Add context references based on configuration
        if context_config:
            for context_step in context_config:
                # Handle both string and dict formats
                if isinstance(context_step, dict):
                    step_ref = context_step.get("val")
                else:
                    step_ref = context_step
                
                if step_ref and step_ref in self.step_results:
                    context.add_context_reference(self.step_results[step_ref])
        
        self.contexts[step_name] = context
        return context
    
    def retrieve_all_results(self) -> Dict[str, str]:
        """
        Retrieve all results from DynamoDB.
        
        Returns:
            Dictionary mapping step names to their result content
        """
        dynamodb_client = get_dynamodb_client()
        results = {}
        
        for step_name, result_key in self.step_results.items():
            content = dynamodb_client.get_analysis_result(result_key)
            if content:
                results[step_name] = content
            else:
                logger.warning(f"No content found in DynamoDB for step {step_name}")
        
        return results
