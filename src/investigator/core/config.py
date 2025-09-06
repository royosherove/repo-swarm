"""
Configuration constants for the Claude Investigator.
"""

import os


class Config:
    """Configuration constants for the investigator."""
    
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
    
    # File settings
    ANALYSIS_FILE = "arch.md"
    
    # Logging format
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Directory names
    TEMP_DIR = "temp"
    PROMPTS_DIR = "prompts"
    
    # Repository structure icons
    DIR_ICON = "📁"
    FILE_ICON = "📄"
    
    # Size units for human-readable format
    SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB']
    
    # Architecture Hub configuration
    # These values are read from environment variables with sensible defaults
    ARCH_HUB_REPO_NAME = os.getenv("ARCH_HUB_REPO_NAME", "architecture-hub")
    ARCH_HUB_BASE_URL = os.getenv("ARCH_HUB_BASE_URL", "https://github.com/your-org")
    ARCH_HUB_FILES_DIR = os.getenv("ARCH_HUB_FILES_DIR", "")  # Empty string means root directory
    
    # Repository scanning configuration
    # DEFAULT_ORG_NAME supports both GitHub organizations and individual user accounts
    DEFAULT_ORG_NAME = os.getenv("DEFAULT_ORG_NAME", "your-org")
    DEFAULT_REPO_URL = os.getenv("DEFAULT_REPO_URL", "https://github.com/facebook/react")
    
    # Git configuration for commits
    GIT_USER_NAME = os.getenv("GIT_USER_NAME", "Architecture Bot")
    GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL", "architecture-bot@your-org.com")
    
    @staticmethod
    def get_arch_hub_repo_url() -> str:
        """Get the full repository URL for the architecture hub."""
        return f"{Config.ARCH_HUB_BASE_URL}/{Config.ARCH_HUB_REPO_NAME}.git"
    
    @staticmethod
    def get_arch_hub_web_url() -> str:
        """Get the web URL for the architecture hub (without .git extension)."""
        return f"{Config.ARCH_HUB_BASE_URL}/{Config.ARCH_HUB_REPO_NAME}"
    
    @staticmethod
    def get_default_org_github_url() -> str:
        """Get the GitHub URL for the default organization."""
        return f"https://github.com/{Config.DEFAULT_ORG_NAME}" 
    
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
            ValueError: If model name is not in VALID_CLAUDE_MODELS
        """
        if model_name not in Config.VALID_CLAUDE_MODELS:
            valid_models_str = ", ".join(Config.VALID_CLAUDE_MODELS)
            raise ValueError(f"Invalid Claude model '{model_name}'. Valid models: {valid_models_str}")
        return model_name
    
    @staticmethod
    def validate_max_tokens(tokens: int) -> int:
        """Validate and return max tokens value.
        
        Args:
            tokens: The max tokens value to validate
            
        Returns:
            The validated max tokens value
            
        Raises:
            ValueError: If tokens is not in valid range (100-100000)
        """
        if not isinstance(tokens, int) or tokens < 100 or tokens > 100000:
            raise ValueError(f"Invalid max_tokens '{tokens}'. Must be integer between 100 and 100000")
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