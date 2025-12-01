import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
import json
from datetime import timedelta
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from workflows.investigate_repos_workflow import InvestigateReposWorkflow
from workflows.investigate_single_repo_workflow import InvestigateSingleRepoWorkflow
from models import InvestigateReposRequest, InvestigateSingleRepoRequest, ConfigOverrides

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_investigate_repos_workflow(client: Client, force: bool = False, 
                                      claude_model: str = None, max_tokens: int = None, 
                                      sleep_hours: float = None, chunk_size: int = None):
    """Run the InvestigateReposWorkflow. Runs continuously every X hours.
    
    Args:
        client: Temporal client instance
        force: If True, forces investigation of all repos ignoring cache on first iteration
        claude_model: Optional Claude model override
        max_tokens: Optional max tokens override  
        sleep_hours: Optional sleep hours override (supports fractional hours)
        chunk_size: Optional chunk size override (number of repos processed in parallel)
    """
    from datetime import datetime
    
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "investigate-task-queue")
    
    # Generate unique workflow ID with timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    workflow_id = f"investigate-repos-workflow-{timestamp}"
    
    logger.info(f"Starting InvestigateReposWorkflow on task queue: {task_queue}")
    logger.info(f"Using workflow ID: {workflow_id}")
    logger.info("Mode: Continuous (runs every X hours)")
    
    if force:
        logger.info("🚀 Force flag enabled - will force investigation of all repositories on first run")
    
    # Create Pydantic request model instead of dictionary
    request = InvestigateReposRequest(
        force=force,
        claude_model=claude_model,
        max_tokens=max_tokens,
        sleep_hours=sleep_hours,
        chunk_size=chunk_size,
        iteration_count=0
    )
    
    if claude_model:
        logger.info(f"🔧 Claude model override: {claude_model}")
    
    if max_tokens:
        logger.info(f"🔧 Max tokens override: {max_tokens}")
    
    if sleep_hours:
        logger.info(f"🔧 Sleep hours override: {sleep_hours}")
    
    if chunk_size:
        logger.info(f"🔧 Chunk size override: {chunk_size}")
    
    result = await client.execute_workflow(
        InvestigateReposWorkflow.run,
        request,
        id=workflow_id,
        task_queue=task_queue,
        task_timeout=timedelta(minutes=60),  # 60 minutes for workflow task execution
        execution_timeout=timedelta(days=365),  # Long timeout for continuous mode
    )
    logger.info(f"InvestigateReposWorkflow result: {result}")
    return result

async def run_investigate_single_repo_workflow(client: Client, repo_identifier: str, 
                                             force: bool = False, claude_model: str = None, 
                                             max_tokens: int = None, repo_type: str = None,
                                             force_section: str = None):
    """Run the InvestigateSingleRepoWorkflow for a specific repository.
    
    Args:
        client: Temporal client instance
        repo_identifier: Repository name (from repos.json) or direct URL
        force: If True, forces investigation ignoring cache
        claude_model: Optional Claude model override
        max_tokens: Optional max tokens override
        repo_type: Optional repository type override
        force_section: Optional section name to force re-execution
    """
    from datetime import datetime
    import uuid
    
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "investigate-task-queue")
    
    # Determine if repo_identifier is a URL or a name from repos.json
    repo_name = None
    repo_url = None
    detected_repo_type = "generic"
    
    if repo_identifier.startswith("http"):
        # Direct URL provided
        repo_url = repo_identifier
        # Extract repo name from URL (last part after /)
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
    else:
        # Repository name provided - look it up in repos.json
        try:
            from activities.investigate_activities import read_repos_config
            repos_data = await read_repos_config()
            
            if "error" in repos_data:
                logger.error(f"Failed to read repos.json: {repos_data['error']}")
                return {"status": "failed", "error": f"Failed to read repos.json: {repos_data['error']}"}
            
            repositories = repos_data.get("repositories", {})
            
            if repo_identifier not in repositories:
                logger.error(f"Repository '{repo_identifier}' not found in repos.json")
                available_repos = list(repositories.keys())
                return {
                    "status": "failed", 
                    "error": f"Repository '{repo_identifier}' not found in repos.json. Available repositories: {available_repos}"
                }
            
            repo_info = repositories[repo_identifier]
            repo_name = repo_identifier
            repo_url = repo_info.get("url")
            detected_repo_type = repo_info.get("type", "generic")
            
            if not repo_url:
                logger.error(f"No URL found for repository: {repo_identifier}")
                return {"status": "failed", "error": f"No URL found for repository: {repo_identifier}"}
        
        except Exception as e:
            logger.error(f"Error reading repos.json: {str(e)}")
            return {"status": "failed", "error": f"Error reading repos.json: {str(e)}"}
    
    if not repo_url:
        logger.error(f"No URL found for repository: {repo_identifier}")
        return {"status": "failed", "error": f"No URL found for repository: {repo_identifier}"}
    
    # Use provided repo_type or fall back to detected type
    final_repo_type = repo_type or detected_repo_type
    
    # Generate a unique workflow ID for this investigation
    workflow_id = f"investigate-single-repo-{repo_name}-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Starting InvestigateSingleRepoWorkflow on task queue: {task_queue}")
    logger.info(f"Using workflow ID: {workflow_id}")
    logger.info(f"Repository: {repo_name} ({final_repo_type})")
    logger.info(f"URL: {repo_url}")
    
    if force:
        logger.info("🚀 Force flag enabled - will investigate regardless of cache")
    
    # Create config overrides if needed
    config_overrides = None
    if claude_model or max_tokens or force_section:
        config_overrides = ConfigOverrides(
            claude_model=claude_model,
            max_tokens=max_tokens,
            force_section=force_section
        )
        
        if claude_model:
            logger.info(f"🔧 Claude model override: {claude_model}")
        
        if max_tokens:
            logger.info(f"🔧 Max tokens override: {max_tokens}")
        
        if force_section:
            logger.info(f"🚀 Force section override: {force_section}")
    
    # Create Pydantic request model instead of dictionary
    request = InvestigateSingleRepoRequest(
        repo_name=repo_name,
        repo_url=repo_url,
        repo_type=final_repo_type,
        force=force,
        config_overrides=config_overrides
    )
    
    result = await client.execute_workflow(
        InvestigateSingleRepoWorkflow.run,
        request,
        id=workflow_id,
        task_queue=task_queue,
        task_timeout=timedelta(minutes=60),  # 60 minutes for workflow task execution
        execution_timeout=timedelta(hours=2),  # 2 hours max for single repo investigation
    )
    logger.info(f"InvestigateSingleRepoWorkflow result: {result}")
    return result

async def main():
    """Main function to run the workflow client."""
    # Get Temporal configuration from environment variables or use local defaults
    temporal_server_url = os.getenv("TEMPORAL_SERVER_URL", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    
    logger.info(f"Connecting to Temporal server: {temporal_server_url}")
    logger.info(f"Using namespace: {temporal_namespace}")
    logger.info(f"API Key present: {'Yes' if temporal_api_key else 'No'}")
    
    # Configure connection parameters based on environment
    connection_kwargs = {
        "namespace": temporal_namespace
    }
    
    # Only use TLS and API key for non-localhost connections (Temporal Cloud)
    is_localhost = temporal_server_url.startswith('localhost')
    
    if not is_localhost and temporal_api_key:
        from temporalio.service import TLSConfig
        logger.info("Configuring for Temporal Cloud with TLS...")
        connection_kwargs.update({
            "tls": TLSConfig(),
            "api_key": temporal_api_key
        })
    elif is_localhost:
        logger.info("Detected localhost - using insecure connection (no TLS)")
    
    # Create client connected to server
    client = await Client.connect(
        temporal_server_url, 
        data_converter=pydantic_data_converter,
        **connection_kwargs
    )
    
    # Get command line arguments
    if len(sys.argv) > 1:
        workflow_name = sys.argv[1].lower()
        
        if workflow_name == "investigate":
            # Parse configuration overrides from command line
            force = "--force" in sys.argv
            claude_model = None
            max_tokens = None
            sleep_hours = None
            chunk_size = None
            
            for arg in sys.argv[2:]:
                if arg.startswith("--claude-model="):
                    claude_model = arg.split("=", 1)[1]
                elif arg.startswith("--max-tokens="):
                    try:
                        max_tokens = int(arg.split("=", 1)[1])
                    except ValueError:
                        logger.error(f"Invalid max-tokens value: {arg.split('=', 1)[1]}. Must be an integer.")
                        return
                elif arg.startswith("--sleep-hours="):
                    try:
                        sleep_hours = float(arg.split("=", 1)[1])
                    except ValueError:
                        logger.error(f"Invalid sleep-hours value: {arg.split('=', 1)[1]}. Must be a number.")
                        return
                elif arg.startswith("--chunk-size="):
                    try:
                        chunk_size = int(arg.split("=", 1)[1])
                    except ValueError:
                        logger.error(f"Invalid chunk-size value: {arg.split('=', 1)[1]}. Must be an integer.")
                        return
            
            await run_investigate_repos_workflow(client, force=force, claude_model=claude_model, 
                                               max_tokens=max_tokens, sleep_hours=sleep_hours, chunk_size=chunk_size)
        elif workflow_name == "investigate-single":
            # Parse repository identifier and configuration overrides
            if len(sys.argv) < 3:
                logger.error("Repository name or URL is required for investigate-single")
                logger.info("Usage: python client.py investigate-single REPO_NAME_OR_URL [--force] [--claude-model=MODEL] [--max-tokens=NUM] [--repo-type=TYPE]")
                return
            
            repo_identifier = sys.argv[2]
            force = "--force" in sys.argv
            claude_model = None
            max_tokens = None
            repo_type = None
            force_section = None
            
            for arg in sys.argv[3:]:
                if arg.startswith("--claude-model="):
                    claude_model = arg.split("=", 1)[1]
                elif arg.startswith("--max-tokens="):
                    try:
                        max_tokens = int(arg.split("=", 1)[1])
                    except ValueError:
                        logger.error(f"Invalid max-tokens value: {arg.split('=', 1)[1]}. Must be an integer.")
                        return
                elif arg.startswith("--repo-type="):
                    repo_type = arg.split("=", 1)[1]
                elif arg.startswith("--force-section="):
                    force_section = arg.split("=", 1)[1]
            
            await run_investigate_single_repo_workflow(client, repo_identifier, force=force, 
                                                     claude_model=claude_model, max_tokens=max_tokens, 
                                                     repo_type=repo_type, force_section=force_section)
        else:
            logger.error(f"Unknown workflow: {workflow_name}")
            logger.info("Available workflows: investigate, investigate-single")
            logger.info("Usage: python client.py investigate [--force] [--claude-model=MODEL] [--max-tokens=NUM] [--sleep-hours=NUM] [--chunk-size=NUM]")
            logger.info("Usage: python client.py investigate-single REPO_NAME_OR_URL [options]")
    else:
        # Default to investigate workflow
        logger.info("No arguments provided. Running investigate workflow.")
        logger.info("The workflow will run continuously every X hours.")
        logger.info("Use 'python client.py investigate --force' to force investigation of all repos.")
        logger.info("Config overrides: --claude-model=MODEL --max-tokens=NUM --sleep-hours=NUM --chunk-size=NUM")
        logger.info("For single repository investigation: python client.py investigate-single REPO_NAME_OR_URL [options]")
        await run_investigate_repos_workflow(client)

if __name__ == "__main__":
    asyncio.run(main()) 