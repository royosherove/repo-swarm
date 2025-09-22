import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate all required environment variables and configuration before starting worker."""
    logger.info("🔍 Starting environment validation...")

    errors = []
    warnings = []

    # Import config to access its validation methods
    try:
        from investigator.core.config import Config
    except ImportError as e:
        errors.append(f"Cannot import Config: {e}")
        return errors, warnings

    # Validate Claude configuration
    try:
        claude_model = os.getenv('CLAUDE_MODEL', Config.CLAUDE_MODEL)
        Config.validate_claude_model(claude_model)
        logger.info(f"  ✓ Claude model: {claude_model}")
    except ValueError as e:
        errors.append(f"Invalid Claude model: {e}")

    try:
        max_tokens = int(os.getenv('MAX_TOKENS', Config.MAX_TOKENS))
        Config.validate_max_tokens(max_tokens)
        logger.info(f"  ✓ Max tokens: {max_tokens}")
    except ValueError as e:
        errors.append(f"Invalid max tokens: {e}")

    # Required API keys
    if not os.getenv('ANTHROPIC_API_KEY'):
        errors.append("ANTHROPIC_API_KEY environment variable is required for Claude API access")
    else:
        logger.info("  ✓ Anthropic API key present")

    if not os.getenv('GITHUB_TOKEN'):
        errors.append("GITHUB_TOKEN environment variable is required for GitHub API access")
    else:
        logger.info("  ✓ GitHub token present")

    # AWS configuration for DynamoDB
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        errors.append("AWS_ACCESS_KEY_ID environment variable is required for DynamoDB access")
    else:
        logger.info("  ✓ AWS access key present")

    if not os.getenv('AWS_SECRET_ACCESS_KEY'):
        errors.append("AWS_SECRET_ACCESS_KEY environment variable is required for DynamoDB access")
    else:
        logger.info("  ✓ AWS secret key present")

    if not os.getenv('AWS_DEFAULT_REGION'):
        warnings.append("AWS_DEFAULT_REGION not set, using default 'us-east-1'")
        logger.info("  ⚠ AWS region not set, will use 'us-east-1'")
    else:
        logger.info(f"  ✓ AWS region: {os.getenv('AWS_DEFAULT_REGION')}")

    # Temporal configuration
    temporal_url = os.getenv('TEMPORAL_SERVER_URL', 'localhost:7233')
    logger.info(f"  ✓ Temporal server URL: {temporal_url}")

    temporal_namespace = os.getenv('TEMPORAL_NAMESPACE', 'default')
    logger.info(f"  ✓ Temporal namespace: {temporal_namespace}")

    temporal_queue = os.getenv('TEMPORAL_TASK_QUEUE', 'investigate-task-queue')
    logger.info(f"  ✓ Temporal task queue: {temporal_queue}")

    temporal_identity = os.getenv('TEMPORAL_IDENTITY', 'investigate-worker')
    logger.info(f"  ✓ Temporal identity: {temporal_identity}")

    if os.getenv('TEMPORAL_API_KEY'):
        logger.info("  ✓ Temporal API key present (for Temporal Cloud)")
    else:
        logger.info("  ⚠ No Temporal API key - assuming local Temporal server")

    # Prompt context storage configuration
    prompt_storage = os.getenv('PROMPT_CONTEXT_STORAGE', 'auto')
    logger.info(f"  ✓ Prompt context storage: {prompt_storage}")

    # Architecture hub configuration
    arch_hub_url = Config.get_arch_hub_repo_url()
    logger.info(f"  ✓ Architecture hub URL: {arch_hub_url}")

    arch_hub_web_url = Config.get_arch_hub_web_url()
    logger.info(f"  ✓ Architecture hub web URL: {arch_hub_web_url}")

    # Git configuration
    git_user = os.getenv('GIT_USER_NAME', 'Architecture Bot')
    git_email = os.getenv('GIT_USER_EMAIL', 'architecture-bot@your-org.com')
    logger.info(f"  ✓ Git user: {git_user} <{git_email}>")

    # Check for any missing DynamoDB table name (might be needed)
    dynamodb_table = os.getenv('DYNAMODB_TABLE_NAME')
    if not dynamodb_table:
        warnings.append("DYNAMODB_TABLE_NAME not set - some features may not work properly")
        logger.info("  ⚠ DynamoDB table name not set")

    # Configuration validation
    try:
        chunk_size = int(os.getenv('WORKFLOW_CHUNK_SIZE', Config.WORKFLOW_CHUNK_SIZE))
        Config.validate_chunk_size(chunk_size)
        logger.info(f"  ✓ Workflow chunk size: {chunk_size}")
    except ValueError as e:
        errors.append(f"Invalid workflow chunk size: {e}")

    try:
        sleep_hours = float(os.getenv('WORKFLOW_SLEEP_HOURS', Config.WORKFLOW_SLEEP_HOURS))
        Config.validate_sleep_hours(sleep_hours)
        logger.info(f"  ✓ Workflow sleep hours: {sleep_hours}")
    except ValueError as e:
        errors.append(f"Invalid workflow sleep hours: {e}")

    # Check directory existence
    temp_dir = os.path.join(os.getcwd(), Config.TEMP_DIR)
    if not os.path.exists(temp_dir):
        warnings.append(f"Temp directory does not exist: {temp_dir}")
        logger.info(f"  ⚠ Temp directory does not exist: {temp_dir}")
    else:
        logger.info(f"  ✓ Temp directory exists: {temp_dir}")

    prompts_dir = os.path.join(os.getcwd(), Config.PROMPTS_DIR)
    if not os.path.exists(prompts_dir):
        errors.append(f"Prompts directory does not exist: {prompts_dir}")
    else:
        logger.info(f"  ✓ Prompts directory exists: {prompts_dir}")

    # Summary
    logger.info("🔍 Environment validation complete")
    logger.info(f"  Found {len(errors)} errors and {len(warnings)} warnings")

    if warnings:
        logger.info("⚠ Warnings:")
        for warning in warnings:
            logger.info(f"    - {warning}")

    return errors, warnings

def print_error_and_exit(errors, warnings):
    """Print validation errors and exit with appropriate status."""
    if errors:
        print("=" * 60, flush=True)
        print("❌ ENVIRONMENT VALIDATION FAILED", flush=True)
        print("=" * 60, flush=True)
        print("The following critical issues must be resolved:", flush=True)
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}", flush=True)

        if warnings:
            print("\n⚠ Additional warnings:", flush=True)
            for warning in warnings:
                print(f"    - {warning}", flush=True)

        print("\n💡 Please set the required environment variables and try again.", flush=True)
        print("=" * 60, flush=True)
        sys.exit(1)
    elif warnings:
        print("=" * 60, flush=True)
        print("⚠ ENVIRONMENT VALIDATION PASSED WITH WARNINGS", flush=True)
        print("=" * 60, flush=True)
        print("The worker can start, but consider addressing these warnings:", flush=True)
        for warning in warnings:
            print(f"  - {warning}", flush=True)
        print("Continuing in 3 seconds...", flush=True)
        print("=" * 60, flush=True)

async def main():
    """
    Validate environment and delegate to the investigate worker main entrypoint.

    Required environment variables:
    - ANTHROPIC_API_KEY: Your Anthropic API key for Claude access
    - GITHUB_TOKEN: GitHub personal access token for repository access
    - AWS_ACCESS_KEY_ID: AWS access key for DynamoDB
    - AWS_SECRET_ACCESS_KEY: AWS secret key for DynamoDB
    - AWS_DEFAULT_REGION: AWS region (e.g., us-east-1, eu-west-1)

    Optional environment variables:
    - TEMPORAL_SERVER_URL: Temporal server URL (default: localhost:7233)
    - TEMPORAL_NAMESPACE: Temporal namespace (default: default)
    - TEMPORAL_TASK_QUEUE: Task queue name (default: investigate-task-queue)
    - TEMPORAL_IDENTITY: Worker identity (default: investigate-worker)
    - TEMPORAL_API_KEY: Temporal Cloud API key (optional, for cloud deployment)
    - PROMPT_CONTEXT_STORAGE: Storage backend (default: auto)
    - DYNAMODB_TABLE_NAME: DynamoDB table name (recommended for production)
    - CLAUDE_MODEL: Claude model to use (default: claude-sonnet-4-20250514)
    - MAX_TOKENS: Maximum tokens per request (default: 6000)
    """
    # Validate environment before starting
    errors, warnings = validate_environment()

    # Print results and exit if there are errors
    print_error_and_exit(errors, warnings)

    # If we get here, validation passed (possibly with warnings)
    # Import the investigate worker and run it
    try:
        from investigate_worker import main as investigate_main
        await investigate_main()
    except ImportError as e:
        logger.error(f"Failed to import investigate_worker: {e}")
        print("=" * 60, flush=True)
        print("❌ CRITICAL ERROR: Cannot import required dependencies", flush=True)
        print("=" * 60, flush=True)
        print(f"Import error: {e}", flush=True)
        print("Please ensure all required packages are installed:", flush=True)
        print("  - temporalio", flush=True)
        print("  - boto3", flush=True)
        print("  - anthropic", flush=True)
        print("Run 'pip install -r requirements.txt' or use your package manager", flush=True)
        print("=" * 60, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())