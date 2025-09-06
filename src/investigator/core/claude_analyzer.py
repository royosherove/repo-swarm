"""
Claude API integration for the Claude Investigator.
"""

from anthropic import Anthropic
from typing import Optional
from .config import Config


class ClaudeAnalyzer:
    """Handles Claude API interactions for analysis."""
    
    def __init__(self, api_key: str, logger):
        self.client = Anthropic(api_key=api_key)
        self.logger = logger
    
    def clean_prompt(self, prompt_template: str) -> str:
        """
        Clean the prompt template by removing version lines and other metadata.
        
        Args:
            prompt_template: Raw prompt template that may contain version headers
            
        Returns:
            Cleaned prompt template ready for Claude
        """
        if not prompt_template:
            return prompt_template
        
        lines = prompt_template.split('\n')
        
        # Only clean if version line exists at the beginning
        if lines and lines[0].startswith('version'):
            lines = lines[1:]
            self.logger.debug("Removed version line from prompt")
            
            # Remove any leading empty lines after version removal
            while lines and lines[0].strip() == '':
                lines = lines[1:]
            
            cleaned_prompt = '\n'.join(lines)
            self.logger.debug(f"Cleaned prompt ({len(cleaned_prompt)} characters)")
            
            return cleaned_prompt
        else:
            # No version line found, return as-is
            return prompt_template
    
    def analyze_with_context(self, prompt_template: str, repo_structure: str, 
                           previous_context: Optional[str] = None,
                           config_overrides: Optional[dict] = None) -> str:
        """
        Analyze using Claude with optional context from previous analyses.
        
        Args:
            prompt_template: Prompt template to use
            repo_structure: Repository structure string
            previous_context: Previous analysis results to include as context
            config_overrides: Optional dict with claude_model, max_tokens overrides
            
        Returns:
            Analysis result from Claude
        """
        if config_overrides is None:
            config_overrides = {}
        
        # Clean the prompt template first (remove version lines, etc.)
        cleaned_template = self.clean_prompt(prompt_template)
        
        # Replace placeholders in the cleaned prompt
        prompt = cleaned_template.replace("{repo_structure}", repo_structure)
        
        # Add previous context if available
        if previous_context:
            context_section = f"\n\n## Previous Analysis Context\n\n{previous_context}\n\n"
            prompt = prompt.replace("{previous_context}", context_section)
        else:
            # Remove the placeholder if no context
            prompt = prompt.replace("{previous_context}", "")
        
        self.logger.debug(f"Prompt created ({len(prompt)} characters)")
        self.logger.debug(f"Prompt preview (first 1000 chars): {prompt[:1000]}...")
        
        try:
            # Use config overrides or defaults
            claude_model = config_overrides.get("claude_model") or Config.CLAUDE_MODEL
            max_tokens = config_overrides.get("max_tokens") or Config.MAX_TOKENS
            
            self.logger.info("Sending analysis request to Claude API")
            self.logger.debug(f"Using model: {claude_model}, max_tokens: {max_tokens}")
            
            response = self.client.messages.create(
                model=claude_model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis_text = response.content[0].text
            self.logger.info(f"Received analysis from Claude ({len(analysis_text)} characters)")
            self.logger.debug(f"Analysis preview (first 1000 chars): {analysis_text[:1000]}...")
            
            return analysis_text
            
        except Exception as e:
            self.logger.error(f"Claude API request failed: {str(e)}")
            raise Exception(f"Failed to get analysis from Claude: {str(e)}")
    
    def analyze_structure(self, repo_structure: str, prompt_template: str) -> str:
        """
        Analyze repository structure using Claude.
        
        Args:
            repo_structure: Repository structure string
            prompt_template: Prompt template to use
            
        Returns:
            Analysis result from Claude
        """
        return self.analyze_with_context(prompt_template, repo_structure, None) 