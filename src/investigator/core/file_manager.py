"""
File operations for the Claude Investigator.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from .config import Config


class FileManager:
    """Handles file operations."""
    
    def __init__(self, logger):
        self.logger = logger
    
    def read_prompts_config(self, prompts_dir: str) -> Dict:
        """Read the prompts configuration from prompts.json with inheritance support."""
        prompts_config_path = os.path.join(prompts_dir, "prompts.json")
        
        try:
            with open(prompts_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Check if this config extends another config
            if "extends" in config:
                # Load the base configuration
                base_config_path = os.path.normpath(os.path.join(prompts_dir, config["extends"]))
                self.logger.debug(f"Loading base config from: {base_config_path}")
                
                with open(base_config_path, 'r', encoding='utf-8') as f:
                    base_config = json.load(f)
                
                # Start with base processing order
                processing_order = base_config.get("processing_order", []).copy()
                
                # Add any additional prompts from the domain config
                if "additional_prompts" in config:
                    # Fix file paths for domain-specific prompts (they're relative to domain dir)
                    for prompt in config["additional_prompts"]:
                        # Ensure file path doesn't start with ../
                        if not prompt["file"].startswith("../"):
                            # It's a domain-specific file, keep as is
                            pass
                        processing_order.append(prompt)
                    self.logger.debug(f"Added {len(config['additional_prompts'])} domain-specific prompts")
                
                return {"processing_order": processing_order}
            else:
                # No inheritance, return config as-is
                return config
                
        except FileNotFoundError:
            self.logger.error(f"Prompts config file not found: {prompts_config_path}")
            raise Exception(f"Prompts config file not found: {prompts_config_path}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in prompts config: {str(e)}")
            raise Exception(f"Invalid JSON in prompts config: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to read prompts config: {str(e)}")
            raise Exception(f"Failed to read prompts config: {str(e)}")
    
    def read_prompt_file(self, prompts_dir: str, filename: str) -> Optional[str]:
        """Read a specific prompt file."""
        # Handle relative paths properly
        if filename.startswith('../'):
            # Resolve relative path from prompts_dir
            prompt_path = os.path.normpath(os.path.join(prompts_dir, filename))
        else:
            prompt_path = os.path.join(prompts_dir, filename)
        
        if not os.path.exists(prompt_path):
            self.logger.warning(f"Prompt file not found: {prompt_path}")
            return None
            
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read prompt file {filename}: {str(e)}")
            return None
    
    
    def cleanup_arch_docs(self, repo_path: str) -> None:
        """
        Remove existing arch-docs folder if it exists to prevent stale output.
        
        Args:
            repo_path: Path to the repository
        """
        arch_docs_path = os.path.join(repo_path, "arch-docs")
        
        if os.path.exists(arch_docs_path):
            try:
                import shutil
                shutil.rmtree(arch_docs_path)
                self.logger.info(f"Cleaned up existing arch-docs folder: {arch_docs_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up existing arch-docs folder: {str(e)}")
        else:
            self.logger.debug(f"No existing arch-docs folder found at: {arch_docs_path}")

    def extract_repository_name_from_analysis(self, analysis: str) -> str:
        """Extract repository name from hl_overview section using [[name]] format."""
        import re
        # Look for [[repository name]] pattern in the analysis
        match = re.search(r'\[\[([^\]]+)\]\]', analysis)
        if match:
            repo_name = match.group(1).strip()
            # Clean up the name for filename use
            repo_name = re.sub(r'[^\w\-_.]', '_', repo_name)
            return repo_name
        return "unknown_repo" 

    def write_analysis(self, repo_path: str, analysis: str) -> str:
        """
        Write analysis to {repo_name}_arch.md file in the arch-docs folder.
        
        Args:
            repo_path: Path to the repository
            analysis: Analysis content to write
            
        Returns:
            Path to the created {repository-name}-arch.md file
        """
        # Extract repository name from analysis
        repo_name = self.extract_repository_name_from_analysis(analysis)
        
        # Create arch-docs folder in the repository
        arch_docs_path = os.path.join(repo_path, "arch-docs")
        os.makedirs(arch_docs_path, exist_ok=True)
        
        # Use repository name in filename
        filename = f"{repo_name}-arch.md"
        arch_file_path = os.path.join(arch_docs_path, filename)
        self.logger.debug(f"Writing analysis to: {arch_file_path}")
        
        header = self._create_analysis_header()
        full_content = header + analysis
        
        try:
            with open(arch_file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            self.logger.info(f"Architecture analysis written to: {arch_file_path}")
            self.logger.debug(f"File size: {len(full_content)} characters")
            return arch_file_path
            
        except Exception as e:
            self.logger.error(f"Failed to write analysis file: {str(e)}")
            raise Exception(f"Failed to write analysis file: {str(e)}")
    
    def write_prompt_file(self, repo_path: str, step_name: str, prompt_content: str) -> str:
        """Write prompt content to a file in the arch-docs folder."""
        # Create arch-docs folder in the repository
        arch_docs_path = os.path.join(repo_path, "arch-docs")
        os.makedirs(arch_docs_path, exist_ok=True)
        
        output_path = os.path.join(arch_docs_path, f"{step_name}_prompt.md")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            
            self.logger.debug(f"Prompt file written to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to write prompt file: {str(e)}")
            raise Exception(f"Failed to write prompt file: {str(e)}")

    def write_intermediate_result(self, repo_path: str, step_name: str, content: str) -> str:
        """Write intermediate analysis result to a file in the arch-docs folder."""
        # Create arch-docs folder in the repository
        arch_docs_path = os.path.join(repo_path, "arch-docs")
        os.makedirs(arch_docs_path, exist_ok=True)
        
        output_path = os.path.join(arch_docs_path, f"{step_name}_result.md")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.debug(f"Intermediate result written to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to write intermediate result: {str(e)}")
            raise Exception(f"Failed to write intermediate result: {str(e)}")
    
    def _create_analysis_header(self) -> str:
        """Create the header for the analysis file."""
        return f"""# Repository Architecture Analysis

This document was automatically generated by Claude Investigator to analyze the repository structure and architecture.

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}

---

""" 
