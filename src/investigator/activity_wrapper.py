"""
ActivityWrapper for executing Temporal activities without direct Temporal dependency.
"""

import asyncio
from typing import Optional, Any, Callable
from datetime import timedelta


class ActivityWrapper:
    """
    Wrapper class to execute Temporal activities without requiring direct Temporal imports.
    This allows the investigator module to remain decoupled from Temporal while still
    being able to execute activities when running within a Temporal workflow context.
    """
    
    def __init__(self, workflow_context: Optional[Any] = None):
        """
        Initialize the ActivityWrapper.
        
        Args:
            workflow_context: The Temporal workflow context (workflow module) if available
        """
        self.workflow_context = workflow_context
        self._is_temporal_context = workflow_context is not None
    
    async def execute_activity(self, activity_func: Callable, *args, 
                              start_to_close_timeout: Optional[timedelta] = None,
                              retry_policy: Optional[Any] = None,
                              **kwargs) -> Any:
        """
        Execute an activity function.
        
        If running in a Temporal workflow context, this will execute the activity
        via Temporal's workflow.execute_activity. Otherwise, it will execute the
        function directly (for testing or non-Temporal environments).
        
        Args:
            activity_func: The activity function to execute
            *args: Positional arguments for the activity function
            start_to_close_timeout: Timeout for the activity execution
            retry_policy: Retry policy for the activity
            **kwargs: Keyword arguments for the activity function
            
        Returns:
            Result from the activity execution
        """
        if self._is_temporal_context and hasattr(self.workflow_context, 'execute_activity'):
            # Running in Temporal workflow context
            return await self.workflow_context.execute_activity(
                activity_func,
                *args,
                start_to_close_timeout=start_to_close_timeout or timedelta(minutes=10),
                retry_policy=retry_policy,
                **kwargs
            )
        else:
            # Running outside Temporal context (testing or direct execution)
            # Execute the activity function directly
            if asyncio.iscoroutinefunction(activity_func):
                return await activity_func(*args, **kwargs)
            else:
                return activity_func(*args, **kwargs)
    
    def is_temporal_context(self) -> bool:
        """
        Check if running in a Temporal workflow context.
        
        Returns:
            True if running in Temporal workflow context, False otherwise
        """
        return self._is_temporal_context
