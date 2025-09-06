"""
Workflow-safe configuration constants and validation methods.
This module contains only pure Python code with no external dependencies
to avoid Temporal workflow sandbox restrictions.
"""


class WorkflowConfig:
    """Configuration constants for workflows - no external dependencies."""
    
    # Claude API settings
    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 6000
    
    # Valid Claude model names for validation
    VALID_CLAUDE_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022", 
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-sonnet-4-20250514"  # current default
    ]
    
    # Workflow configuration
    WORKFLOW_CHUNK_SIZE = 8  # Number of sub-workflows to run in parallel 
    WORKFLOW_SLEEP_HOURS = 6  # Hours to sleep between workflow executions
    
    @staticmethod
    def validate_claude_model(model_name: str) -> str:
        """Validate and return claude model name.
        
        Args:
            model_name: The model name to validate
            
        Returns:
            The validated model name
            
        Raises:
            ValueError: If model name is not in valid list
        """
        if not isinstance(model_name, str) or model_name not in WorkflowConfig.VALID_CLAUDE_MODELS:
            valid_models_str = ", ".join(WorkflowConfig.VALID_CLAUDE_MODELS)
            raise ValueError(f"Invalid claude_model '{model_name}'. Must be one of: {valid_models_str}")
        return model_name
    
    @staticmethod
    def validate_max_tokens(tokens: int) -> int:
        """Validate and return max tokens value.
        
        Args:
            tokens: The max tokens value to validate
            
        Returns:
            The validated max tokens value
            
        Raises:
            ValueError: If tokens is not in valid range (100-8000)
        """
        if not isinstance(tokens, int) or tokens < 100 or tokens > 8000:
            raise ValueError(f"Invalid max_tokens '{tokens}'. Must be integer between 100 and 8000")
        return tokens
    
    @staticmethod
    def validate_sleep_hours(hours: float) -> float:
        """Validate and return sleep hours value.
        
        Args:
            hours: The sleep hours value to validate (supports fractional hours)
            
        Returns:
            The validated sleep hours value
            
        Raises:
            ValueError: If hours is not in valid range (0.01-168)
        """
        if not isinstance(hours, (int, float)) or hours < 0.01 or hours > 168:
            raise ValueError(f"Invalid sleep_hours '{hours}'. Must be number between 0.01 and 168 (36 seconds to 1 week)")
        return float(hours)
    
    @staticmethod
    def validate_chunk_size(size: int) -> int:
        """Validate and return chunk size value.
        
        Args:
            size: The chunk size value to validate
            
        Returns:
            The validated chunk size value
            
        Raises:
            ValueError: If size is not in valid range (1-20)
        """
        if not isinstance(size, int) or size < 1 or size > 20:
            raise ValueError(f"Invalid chunk_size '{size}'. Must be integer between 1 and 20")
        return size
