#!/usr/bin/env python3
"""
Health check script for the Temporal worker.
Used by Docker HEALTHCHECK and ECS to determine if the container is healthy.

This script is invoked by the Docker HEALTHCHECK instruction and the result
is used by ECS to determine the health status of the task.

Exit codes:
  0 - Healthy: Worker is running and responsive
  1 - Unhealthy: Worker is not running or unresponsive
"""

import sys
import os
import logging
from pathlib import Path
import time

# Setup logging to stdout for ECS
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - HEALTHCHECK - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Health check file path - worker will touch this file periodically
HEALTH_FILE = Path("/tmp/worker_health")
HEALTH_TIMEOUT_SECONDS = 60  # Consider unhealthy if file hasn't been updated in 60 seconds


def check_health():
    """
    Check if the worker is healthy by verifying:
    1. The health file exists
    2. The health file was updated recently
    
    Returns:
        bool: True if healthy, False if unhealthy
    """
    try:
        # Check if health file exists
        if not HEALTH_FILE.exists():
            print(f"UNHEALTHY: Health file does not exist: {HEALTH_FILE}", flush=True)
            logger.error(f"Health file does not exist: {HEALTH_FILE}")
            return False
        
        # Check file modification time
        current_time = time.time()
        file_mtime = HEALTH_FILE.stat().st_mtime
        file_age = current_time - file_mtime
        
        if file_age > HEALTH_TIMEOUT_SECONDS:
            print(f"UNHEALTHY: Health file is stale (age: {file_age:.1f}s > {HEALTH_TIMEOUT_SECONDS}s)", flush=True)
            logger.error(f"Health file is stale - last updated {file_age:.1f}s ago (threshold: {HEALTH_TIMEOUT_SECONDS}s)")
            return False
        
        # Worker is healthy
        print(f"HEALTHY: Worker is alive (last update: {file_age:.1f}s ago)", flush=True)
        logger.info(f"Worker is healthy - health file updated {file_age:.1f}s ago")
        return True
        
    except Exception as e:
        print(f"UNHEALTHY: Health check error: {e}", flush=True)
        logger.error(f"Health check failed with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Perform health check
    is_healthy = check_health()
    
    # Exit with appropriate code for Docker/ECS
    if is_healthy:
        sys.exit(0)  # Exit code 0 = Healthy
    else:
        sys.exit(1)  # Exit code 1 = Unhealthy
