#!/usr/bin/env python3
"""
Query Temporal workflow status
Usage: python query_workflow_status.py <workflow_id> [query_type] [repo_name]
"""

import sys
import os
import asyncio
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def query_workflow_status(workflow_id: str, query_type: str = None, repo_name: str = None):
    """Query workflow status using Temporal client"""

    try:
        # Connect to Temporal server
        client = await Client.connect(
            os.getenv("TEMPORAL_SERVER_URL", "localhost:7233"),
            namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
            data_converter=pydantic_data_converter
        )

        async with client:
            # Get workflow handle
            handle = client.get_workflow_handle(workflow_id)

            try:
                # Try to get basic workflow info
                desc = await handle.describe()

                print(f"Workflow ID: {workflow_id}")
                print(f"Status: {desc.status}")
                print(f"Start Time: {desc.start_time}")
                if desc.close_time:
                    print(f"Close Time: {desc.close_time}")

                # If workflow has a get_status query method, use it
                if query_type:
                    try:
                        result = await handle.query("get_status", query_type, repo_name)
                        print(f"Query Result ({query_type}): {result}")
                    except Exception as e:
                        print(f"Query failed: {e}")
                else:
                    # Basic status info
                    print(f"Workflow Type: {desc.workflow_type}")
                    print(f"Task Queue: {desc.task_queue}")

            except Exception as e:
                print(f"Failed to get workflow status: {e}")
                return False

        return True

    except Exception as e:
        logger.error(f"Failed to connect to Temporal: {e}")
        return False

async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python query_workflow_status.py <workflow_id> [query_type] [repo_name]")
        print("Examples:")
        print("  python query_workflow_status.py investigate-repos-workflow")
        print("  python query_workflow_status.py investigate-repos-workflow all_repo_statuses")
        print("  python query_workflow_status.py investigate-repos-workflow repo_status is-odd")
        sys.exit(1)

    workflow_id = sys.argv[1]
    query_type = sys.argv[2] if len(sys.argv) > 2 else None
    repo_name = sys.argv[3] if len(sys.argv) > 3 else None

    success = await query_workflow_status(workflow_id, query_type, repo_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
