# No file system operations in workflows - they must be done in activities

from temporalio import workflow
from temporalio.common import RetryPolicy
from activities.investigate_activities import read_repos_config, update_repos_list
from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
from workflow_config import WorkflowConfig
from models import (
    InvestigateReposRequest,
    InvestigateReposResult,
    InvestigateSingleRepoRequest,
    InvestigateSingleRepoResult,
    ConfigOverrides
)
import logging
from datetime import timedelta
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

@workflow.defn
class InvestigateReposWorkflow:
    """Workflow that investigates multiple repositories from repos.json."""

    @workflow.query
    async def get_status(self) -> str:
        """Query method to get the current status of the workflow."""
        return "YOLO"
    
    @workflow.run
    async def run(self, request: Optional[InvestigateReposRequest] = None, iteration_count: int = 0) -> InvestigateReposResult:
        """Main workflow execution method. Runs one cycle then continues as new.
        
        Args:
            request: Optional InvestigateReposRequest with configuration overrides
            iteration_count: The current iteration number (used internally for Continue-As-New)
        """
        logger.info(f"Starting InvestigateReposWorkflow - Iteration {iteration_count}")
        
        # Extract configuration from initial request
        force_first_run = False
        config_overrides = ConfigOverrides()
        
        if request:
            # Handle dict to Pydantic model conversion if needed
            if isinstance(request, dict):
                logger.info("⚠️  Converting dict to InvestigateReposRequest Pydantic model")
                try:
                    request = InvestigateReposRequest(**request)
                    logger.info("✅ Successfully converted dict to InvestigateReposRequest")
                except Exception as e:
                    logger.error(f"❌ Failed to convert dict to InvestigateReposRequest: {e}")
                    raise
            
            force_first_run = request.force
            
            # Extract and validate config overrides
            if request.claude_model:
                try:
                    config_overrides.claude_model = WorkflowConfig.validate_claude_model(request.claude_model)
                    logger.info(f"🔧 Claude model override: {config_overrides.claude_model}")
                except ValueError as e:
                    logger.error(f"Invalid claude_model in request: {e}")
                    raise
            
            if request.max_tokens:
                try:
                    config_overrides.max_tokens = WorkflowConfig.validate_max_tokens(request.max_tokens)
                    logger.info(f"🔧 Max tokens override: {config_overrides.max_tokens}")
                except ValueError as e:
                    logger.error(f"Invalid max_tokens in request: {e}")
                    raise
            
            if request.sleep_hours:
                try:
                    config_overrides.sleep_hours = WorkflowConfig.validate_sleep_hours(request.sleep_hours)
                    logger.info(f"🔧 Sleep hours override: {config_overrides.sleep_hours} hours")
                except ValueError as e:
                    logger.error(f"Invalid sleep_hours in request: {e}")
                    raise
            
            if request.chunk_size:
                try:
                    config_overrides.chunk_size = WorkflowConfig.validate_chunk_size(request.chunk_size)
                    logger.info(f"🔧 Chunk size override: {config_overrides.chunk_size} repos")
                except ValueError as e:
                    logger.error(f"Invalid chunk_size in request: {e}")
                    raise
            
            if force_first_run and iteration_count == 0:
                logger.info("🚀 Force flag detected - will force investigation of all repositories on first run")
            else:
                logger.info(f"Running in normal mode (respects cache) - Iteration {iteration_count}")
        else:
            logger.info(f"No request provided, running in normal mode (respects cache) - Iteration {iteration_count}")
        
        # Determine if we should force (only on first iteration when force flag is set)
        force_current = force_first_run and iteration_count == 0
        if force_current:
            logger.info("⚡ Running with force flag - ignoring cache for this iteration")
        
        # Run the investigation for this cycle
        result = await self._run_investigation(force=force_current, config_overrides=config_overrides)
        
        # Check if we should continue as new (Temporal's recommendation or after each cycle)
        should_continue = workflow.info().is_continue_as_new_suggested()
        if should_continue:
            logger.info("📊 Temporal suggests Continue-As-New due to event history size")
        
        # Wait before next run (using override or default)
        sleep_hours = config_overrides.sleep_hours or WorkflowConfig.WORKFLOW_SLEEP_HOURS
        logger.info(f"Investigation complete. Waiting {sleep_hours} hours before next run...")
        await workflow.sleep(timedelta(hours=sleep_hours))
        logger.info(f"{sleep_hours} hours elapsed. Continuing as new for next investigation cycle...")
        
        # Continue as new with updated state
        # Prepare the request for the next iteration
        next_request = InvestigateReposRequest(
            force=False,  # Never force after the first iteration
            claude_model=config_overrides.claude_model,
            max_tokens=config_overrides.max_tokens,
            sleep_hours=config_overrides.sleep_hours,
            chunk_size=config_overrides.chunk_size,
            iteration_count=iteration_count + 1
        )
        
        # Continue the workflow as a new execution
        workflow.continue_as_new(
            args=[next_request, iteration_count + 1]
        )
        
        # This line should never be reached due to continue_as_new
        return result
    
    async def _run_investigation(self, force: bool = False, config_overrides: ConfigOverrides = None) -> InvestigateReposResult:
        """Execute a single investigation cycle.
        
        Args:
            force: If True, forces investigation of all repos ignoring cache
            config_overrides: ConfigOverrides containing config overrides
        """
        if config_overrides is None:
            config_overrides = ConfigOverrides()
            
        # First, update the repository list to get the latest repos
        logger.info("Updating repository list with latest repositories...")
        update_result = await workflow.execute_activity(
            update_repos_list,
            start_to_close_timeout=timedelta(minutes=10),  # Allow up to 10 minutes for update
            retry_policy=RetryPolicy(
                maximum_attempts=2,  # Retry once if it fails
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(seconds=30),
                backoff_coefficient=2.0
            )
        )
        
        # Check if update was successful
        if update_result.get("status") == "failed":
            logger.warning(f"Failed to update repository list: {update_result.get('error', 'Unknown error')}")
            logger.info("Continuing with existing repos.json...")
        else:
            logger.info(f"Repository list updated: {update_result.get('message', 'Success')}")
            if "total_repos" in update_result:
                logger.info(f"Update summary: {update_result['total_repos']}")
            if "new_repos" in update_result:
                logger.info(f"New repositories: {update_result['new_repos']}")
        
        # Read repos.json using activity (file operations not allowed in workflows)
        repos_data = await workflow.execute_activity(
            read_repos_config,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2.0
            )
        )
        
        # Check for errors in reading repos.json
        if "error" in repos_data:
            logger.error(f"Failed to read repos.json: {repos_data['error']}")
            return InvestigateReposResult(
                status="failed",
                total_repos=0,
                successful=0,
                failed=1,
                skipped=0,
                investigated_repos=[],
                repository_update=update_result,
                architecture_analysis={
                    "status": "skipped",
                    "message": f"Failed to read repos.json: {repos_data['error']}"
                }
            )
        
        # Get all repositories (excluding "default")
        repositories = repos_data.get("repositories", {})
        
        if not repositories:
            logger.warning("No repositories found in repos.json")
            return InvestigateReposResult(
                status="completed",
                total_repos=0,
                successful=0,
                failed=0,
                skipped=0,
                investigated_repos=[],
                repository_update=update_result,
                architecture_analysis={
                    "status": "skipped",
                    "message": "No repositories to investigate"
                }
            )
        
        logger.info(f"Found {len(repositories)} repositories to investigate")
        
        if force:
            logger.info("⚡ Force mode enabled - all repositories will be investigated regardless of cache")
        
        # Process repositories in chunks - only specified number run in parallel at a time
        window_size = config_overrides.chunk_size or WorkflowConfig.WORKFLOW_CHUNK_SIZE  # Maximum concurrent workflows
        repo_items = list(repositories.items())
        
        # Filter out repos without URLs
        valid_repos = []
        for repo_name, repo_info in repo_items:
            repo_url = repo_info.get("url")
            if not repo_url:
                logger.warning(f"No URL found for repository: {repo_name}")
                continue
            valid_repos.append((repo_name, repo_info))
        
        logger.info(f"Processing {len(valid_repos)} repositories in chunks of {window_size} (max {window_size} parallel)")
        
        # Track all results as we go
        all_results = []
        failed_count = 0
        success_count = 0
        
        # Process repositories in chunks - wait for each chunk to complete before starting next
        for chunk_idx in range(0, len(valid_repos), window_size):
            chunk = valid_repos[chunk_idx:chunk_idx + window_size]
            chunk_num = chunk_idx // window_size + 1
            total_chunks = (len(valid_repos) + window_size - 1) // window_size
            
            logger.info(f"Starting chunk {chunk_num}/{total_chunks} with {len(chunk)} repositories")
            
            # Start all workflows in this chunk
            chunk_handles = []
            chunk_info_map = {}
            
            for repo_name, repo_info in chunk:
                repo_url = repo_info.get("url")
                repo_type = repo_info.get("type", "generic")
                
                logger.info(f"Starting investigation for repository: {repo_name} (type: {repo_type})")
                
                # Create Pydantic request model
                request = InvestigateSingleRepoRequest(
                    repo_name=repo_name,
                    repo_url=repo_url,
                    repo_type=repo_type,
                    force=force,
                    config_overrides=config_overrides
                )
                
                # Start the child workflow (non-blocking)
                handle = await workflow.start_child_workflow(
                    InvestigateSingleRepoWorkflow.run,
                    args=[request],
                    id=f"investigate-single-repo-{repo_name}",
                    task_queue="investigate-task-queue",
                    retry_policy=RetryPolicy(maximum_attempts=3),
                    execution_timeout=timedelta(hours=20),
                    run_timeout=timedelta(hours=1),
                    task_timeout=timedelta(minutes=10),
                )
                
                chunk_handles.append(handle)
                chunk_info_map[handle] = {
                    "repo_name": repo_name,
                    "repo_url": repo_url
                }
                
                # Yield control after starting each workflow to prevent timeout
                await workflow.sleep(0)
            
            logger.info(f"Chunk {chunk_num}: Started {len(chunk_handles)} workflows, waiting for them to complete...")
            
            # Wait for all workflows in this chunk to complete before starting next chunk
            for handle in chunk_handles:
                repo_info = chunk_info_map[handle]
                
                try:
                    # Wait for this workflow to complete
                    result: InvestigateSingleRepoResult = await handle
                    all_results.append(result)
                    
                    if result.status == "success":
                        success_count += 1
                        logger.info(f"Chunk {chunk_num}: ✓ Completed {repo_info['repo_name']}")
                    elif result.status == "skipped":
                        # Don't count skipped as failed - it's a separate category
                        logger.info(f"Chunk {chunk_num}: ⊘ Skipped {repo_info['repo_name']} (cached): {result.reason or 'Unknown reason'}")
                    else:
                        failed_count += 1
                        logger.warning(f"Chunk {chunk_num}: ✗ Failed {repo_info['repo_name']}: {result.message or 'Unknown error'}")
                        
                except Exception as e:
                    # Handle exceptions from child workflows
                    logger.error(f"Chunk {chunk_num}: ✗ Exception for {repo_info['repo_name']}: {str(e)}")
                    error_result = InvestigateSingleRepoResult(
                        status="failed",
                        repo_name=repo_info["repo_name"],
                        repo_url=repo_info["repo_url"],
                        repo_type="generic",
                        latest_commit="unknown",
                        branch_name="unknown",
                        reason=f"Failed to execute investigation: {str(e)}",
                        message=f"Failed to execute investigation for {repo_info['repo_name']}: {str(e)}"
                    )
                    all_results.append(error_result)
                    failed_count += 1
            
            logger.info(f"Chunk {chunk_num}/{total_chunks} completed. Progress: {len(all_results)}/{len(valid_repos)} repos")
            
            # Yield control between chunks
            if chunk_idx + window_size < len(valid_repos):
                logger.info("Yielding control before starting next chunk...")
                await workflow.sleep(1)
        
        # All results have been collected during chunk processing
        logger.info(f"All {len(all_results)} investigations completed!")
        results = all_results
        
        # Count how many were skipped
        skipped_count = sum(1 for result in results if result.status == "skipped")
        
        # Prepare summary
        summary = InvestigateReposResult(
            status="completed",
            total_repos=len(results),
            successful=success_count,
            failed=failed_count,
            skipped=skipped_count,
            investigated_repos=results,
            repository_update=update_result
        )
        
        logger.info(f"Workflow completed. Investigated {len(results)} repositories in parallel. "
                   f"Success: {success_count}, Failed: {failed_count}, Skipped: {skipped_count}")
        
        # Only run architecture hub analysis if we have successful investigations (not skipped)
        if success_count > 0:
            logger.info(f"Starting architecture hub analysis child workflow ({len(results) - skipped_count} new investigations)")
            
            try:
                # Start the architecture hub analysis child workflow
                # analysis_result = await workflow.execute_child_workflow(
                #     AnalyzeArchitectureHubWorkflow.run,
                #     id=f"analyze-arch-hub-{workflow.info().workflow_id}",
                #     task_queue="investigate-task-queue",
                #     retry_policy=RetryPolicy(maximum_attempts=2),
                #     execution_timeout=timedelta(hours=1),
                #     run_timeout=timedelta(minutes=45),
                #     task_timeout=timedelta(minutes=25),
                # )
                
                # summary.architecture_analysis = analysis_result
                logger.info(f"Skipping architecture analysis - not implemented yet")
                summary.architecture_analysis = {
                    "status": "skipped",
                    "message": "Architecture analysis not implemented yet"
                }
                
            except Exception as e:
                from investigator.core.config import Config
                logger.error(f"Failed to analyze {Config.ARCH_HUB_REPO_NAME}: {str(e)}")
                summary.architecture_analysis = {
                    "status": "failed",
                    "error": str(e),
                    "message": f"Failed to analyze {Config.ARCH_HUB_REPO_NAME}: {str(e)}"
                }
        else:
            if skipped_count == len(results):
                logger.info(f"Skipping architecture analysis - all {skipped_count} repositories were skipped (cached)")
                summary.architecture_analysis = {
                    "status": "skipped", 
                    "message": f"Architecture analysis skipped - all {skipped_count} repositories were cached/skipped"
                }
            else:
                from investigator.core.config import Config
                logger.info(f"Skipping architecture analysis - no successful saves to {Config.ARCH_HUB_REPO_NAME}")
                summary.architecture_analysis = {
                    "status": "skipped", 
                    "message": "Architecture analysis skipped - no successful saves to hub"
                }
        
        return summary 