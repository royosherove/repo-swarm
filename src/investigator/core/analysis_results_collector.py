"""
Analysis Results Collector for managing and combining analysis results.

This module provides functionality to track, validate, and combine analysis
results from multiple processing steps, ensuring all required sections are
included in the final output.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from .constants import EXPECTED_BASE_PROMPT_COUNT


logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Represents a single analysis step result."""
    name: str
    description: str
    result_key: str
    content: Optional[str] = None
    required: bool = True
    context_dependencies: List[str] = field(default_factory=list)
    version: Optional[str] = None
    cached: bool = False
    cache_timestamp: Optional[str] = None


class AnalysisResultsCollector:
    """
    Collects and manages analysis results from multiple processing steps.
    
    This class ensures that all required sections from the processing order
    are included in the final analysis output, maintaining correct ordering
    and validating completeness.
    """
    
    def __init__(self, repo_name: str, base_prompts_config: Optional[Dict] = None):
        """
        Initialize the collector.
        
        Args:
            repo_name: Name of the repository being analyzed
            base_prompts_config: Optional base prompts configuration dict with 'processing_order' key
        """
        self.repo_name = repo_name
        self.step_results: Dict[str, StepResult] = {}
        self.processing_order: List[Dict] = []
        self.base_prompts_config = base_prompts_config or {}
        self._extract_base_sections()
    
    def _extract_base_sections(self) -> None:
        """Extract base sections from the provided configuration."""
        if self.base_prompts_config and "processing_order" in self.base_prompts_config:
            self.base_sections = [
                step["name"] for step in self.base_prompts_config.get("processing_order", [])
            ]
            logger.info(f"Extracted {len(self.base_sections)} base sections from config")
        else:
            logger.warning("No base prompts configuration provided")
            self.base_sections = []
    
    def track_step(self, step_name: str, description: str, result_key: str, 
                   required: bool = True, context_dependencies: Optional[List[str]] = None) -> None:
        """
        Track a completed analysis step.
        
        Args:
            step_name: Name of the step
            description: Description of what the step analyzes
            result_key: Key to retrieve the result from storage
            required: Whether this step is required
            context_dependencies: List of step names this step depends on
        """
        self.step_results[step_name] = StepResult(
            name=step_name,
            description=description,
            result_key=result_key,
            required=required,
            context_dependencies=context_dependencies or []
        )
        logger.debug(f"Tracked step: {step_name} with key: {result_key}")
    
    def validate_required_sections(self, processing_order: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate that all required sections are present.
        
        Args:
            processing_order: The processing order configuration
            
        Returns:
            Tuple of (is_valid, missing_sections)
        """
        required_sections = [
            step["name"] for step in processing_order 
            if step.get("required", True)
        ]
        
        tracked_sections = set(self.step_results.keys())
        missing_sections = [
            section for section in required_sections 
            if section not in tracked_sections
        ]
        
        is_valid = len(missing_sections) == 0
        
        if not is_valid:
            logger.warning(f"Missing required sections: {missing_sections}")
        
        return is_valid, missing_sections
    
    def validate_base_sections_present(self) -> Tuple[bool, List[str]]:
        """
        Validate that all base prompt sections are tracked.
        
        Returns:
            Tuple of (all_present, missing_sections)
        """
        if not self.base_sections:
            logger.warning("No base sections loaded for validation")
            return True, []
        
        tracked_sections = set(self.step_results.keys())
        missing_base_sections = [
            section for section in self.base_sections
            if section not in tracked_sections
        ]
        
        all_present = len(missing_base_sections) == 0
        
        if not all_present:
            logger.warning(f"Missing base sections: {missing_base_sections}")
        else:
            logger.info(f"All {len(self.base_sections)} base sections are present")
        
        # Special check for monitoring section
        if "monitoring" in self.base_sections and "monitoring" not in tracked_sections:
            logger.error("CRITICAL: Monitoring section is missing from results!")
        
        return all_present, missing_base_sections
    
    def combine_results(self, results_map: Dict[str, str], processing_order: List[Dict],
                       cached_results_map: Optional[Dict[str, Dict]] = None,
                       prompt_versions: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Combine results in the correct order based on processing_order.
        Intelligently uses cached results when prompt versions match.
        
        Args:
            results_map: Map of step names to their newly executed content
            processing_order: The order in which to combine results
            cached_results_map: Optional map of step names to cached results with version info
            prompt_versions: Optional map of step names to current prompt versions
            
        Returns:
            List of results in the correct order with content (mixed cached and new)
        """
        combined_results = []
        cached_results_map = cached_results_map or {}
        prompt_versions = prompt_versions or {}
        
        # Statistics for logging
        cached_count = 0
        new_count = 0
        
        # Process in the order specified by processing_order
        for step_config in processing_order:
            step_name = step_config.get("name")
            current_version = prompt_versions.get(step_name, "1")
            
            # Check if we have a cached result with matching version
            cached_result = cached_results_map.get(step_name, {})
            cached_version = cached_result.get("version")
            cached_content = cached_result.get("content")
            
            # Decide whether to use cached or new result
            use_cached = False
            content = None
            
            if cached_content and cached_version == current_version and step_name not in results_map:
                # Use cached result if versions match and no new result available
                content = cached_content
                use_cached = True
                cached_count += 1
                logger.info(f"Using cached result for step: {step_name} (v{current_version})")
            elif step_name in results_map:
                # Use new result if available
                content = results_map[step_name]
                new_count += 1
                logger.info(f"Using new result for step: {step_name} (v{current_version})")
            elif cached_content:
                # Fallback to cached even if version mismatch (better than nothing)
                content = cached_content
                use_cached = True
                cached_count += 1
                logger.warning(f"Using outdated cached result for step: {step_name} "
                             f"(cached v{cached_version} != current v{current_version})")
            
            if content:  # Only include if there's actual content
                # Get the tracked step info if available
                step_info = self.step_results.get(step_name)
                
                result_dict = {
                    "name": step_name,
                    "description": step_config.get("description", ""),
                    "content": content,
                    "version": current_version,
                    "cached": use_cached
                }
                
                # Add additional metadata if available
                if step_info:
                    result_dict["result_key"] = step_info.result_key
                    result_dict["required"] = step_info.required
                
                if use_cached and cached_result:
                    result_dict["cache_timestamp"] = cached_result.get("timestamp")
                
                combined_results.append(result_dict)
                logger.debug(f"Added {'cached' if use_cached else 'new'} result for step: {step_name} ({len(content)} chars)")
            else:
                # Check if this was a required step
                if step_config.get("required", True):
                    logger.error(f"Missing required step in results: {step_name}")
                else:
                    logger.info(f"Optional step not in results: {step_name}")
        
        logger.info(f"Combined {len(combined_results)} results from {len(processing_order)} steps "
                   f"(cached: {cached_count}, new: {new_count})")
        
        # Validate all base sections are present
        if self.base_sections:
            result_names = {r["name"] for r in combined_results}
            missing_base = [s for s in self.base_sections if s not in result_names]
            if missing_base:
                logger.error(f"Base sections missing from combined results: {missing_base}")
            
            # Special validation for monitoring section
            if "monitoring" in self.base_sections and "monitoring" not in result_names:
                raise ValueError("Critical: Monitoring section missing from final results!")
        
        return combined_results
    
    def generate_final_analysis(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate the final analysis markdown from combined results.
        
        Args:
            results: List of result dictionaries with name, description, and content
            
        Returns:
            Final analysis as a markdown string
        """
        if not results:
            logger.warning("No results to generate final analysis")
            return ""
        
        sections = []
        for result in results:
            section = f"# {result['name']}\n\n"
            
            if result.get('description'):
                section += f"{result['description']}\n\n"
            
            section += result['content']
            sections.append(section)
        
        final_analysis = "\n\n".join(sections)
        
        logger.info(f"Generated final analysis with {len(sections)} sections, "
                   f"total length: {len(final_analysis)} characters")
        
        # Final validation - ensure monitoring section is in the output
        if self.base_sections and "monitoring" in self.base_sections:
            if "# monitoring\n" not in final_analysis.lower():
                logger.error("WARNING: Monitoring section not found in final analysis output!")
        
        return final_analysis
    
    def get_missing_sections(self, results_map: Dict[str, str]) -> List[str]:
        """
        Get list of sections that are tracked but missing from results.
        
        Args:
            results_map: Map of step names to their content
            
        Returns:
            List of missing section names
        """
        tracked = set(self.step_results.keys())
        available = set(results_map.keys())
        return list(tracked - available)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the collected results.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "repo_name": self.repo_name,
            "total_steps_tracked": len(self.step_results),
            "base_sections_expected": len(self.base_sections),
            "has_monitoring": "monitoring" in self.step_results,
            "tracked_sections": list(self.step_results.keys()),
            "base_sections": self.base_sections
        }
    
    @staticmethod
    def extract_prompt_version(prompt_content: str) -> str:
        """
        Extract version from prompt content.
        
        Args:
            prompt_content: The prompt markdown content
            
        Returns:
            Version string from the first line (format: version=X)
            
        Raises:
            ValueError: If prompt content is empty, has no version header, or has invalid version format
        """
        if not prompt_content:
            raise ValueError("Prompt content is empty")
        
        lines = prompt_content.split('\n')
        if lines and lines[0].startswith('version='):
            try:
                version = lines[0].split('=')[1].strip()
                if not version:
                    raise ValueError(f"Version is empty in prompt: {prompt_content}")
                return version
            except (IndexError, ValueError):
                raise ValueError(f"Invalid version format in prompt (line missing?): {prompt_content}")
        
        raise ValueError(f"No version found in prompt: {prompt_content}")
    
    def track_prompt_versions(self, prompts_content: Dict[str, str]) -> Dict[str, str]:
        """
        Extract versions from all prompt contents.
        
        Args:
            prompts_content: Map of prompt names to their content
            
        Returns:
            Map of prompt names to their versions
        """
        versions = {}
        for name, content in prompts_content.items():
            versions[name] = self.extract_prompt_version(content)
            logger.debug(f"Prompt {name} has version {versions[name]}")
        
        return versions
