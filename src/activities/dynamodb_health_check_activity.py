"""
DynamoDB health check activity to verify table access at workflow start.

This activity ensures we can read/write to DynamoDB before processing repositories,
preventing wasted computation if the database is unavailable.
"""

import os
import logging
from typing import Dict
from datetime import datetime, timezone
from temporalio import activity
import uuid

activity_logger = logging.getLogger(__name__)


@activity.defn
async def check_dynamodb_health() -> Dict:
    """
    Perform a health check on DynamoDB by writing, reading, and deleting a test item.
    
    This ensures:
    1. DynamoDB table exists and is accessible
    2. We have write permissions (PutItem)
    3. We have read permissions (GetItem)
    4. We have delete permissions (DeleteItem)
    
    Returns:
        Dict with health check results including status and any error messages
    """
    activity.logger.info("Starting DynamoDB health check")
    
    # Check if we're running locally and should skip DynamoDB health check
    is_local = any([
        os.environ.get('PROMPT_CONTEXT_STORAGE') == 'file',
        os.environ.get('SKIP_DYNAMODB_CHECK') == 'true',
        os.environ.get('LOCAL_TESTING') == 'true',
        # Check if we're NOT in AWS/production environment
        not os.environ.get('ECS_CONTAINER_METADATA_URI'),
        not os.environ.get('AWS_EXECUTION_ENV'),
    ])
    
    # Also check if we're in localhost environment
    temporal_server = os.environ.get('TEMPORAL_SERVER_URL', 'localhost:7233')
    is_localhost = 'localhost' in temporal_server or '127.0.0.1' in temporal_server
    
    if is_local or is_localhost:
        activity.logger.info("Local environment detected - skipping DynamoDB health check")
        activity.logger.info(f"  PROMPT_CONTEXT_STORAGE: {os.environ.get('PROMPT_CONTEXT_STORAGE')}")
        activity.logger.info(f"  SKIP_DYNAMODB_CHECK: {os.environ.get('SKIP_DYNAMODB_CHECK')}")
        activity.logger.info(f"  LOCAL_TESTING: {os.environ.get('LOCAL_TESTING')}")
        activity.logger.info(f"  TEMPORAL_SERVER_URL: {temporal_server}")
        activity.logger.info(f"  Running in local mode - DynamoDB operations will use file storage")
        
        return {
            "status": "healthy",
            "message": "DynamoDB health check skipped - running in local mode",
            "mode": "local",
            "storage_backend": os.environ.get('PROMPT_CONTEXT_STORAGE', 'file'),
            "operations_tested": ["skipped"],
            "test_key_used": "none"
        }
    
    try:
        from utils.dynamodb_client import get_dynamodb_client
        
        # Get the DynamoDB client
        dynamodb_client = get_dynamodb_client()
        
        # Generate a unique test key to avoid conflicts with real repos
        # Use double underscore prefix, timestamp, and UUID to ensure uniqueness
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        unique_id = uuid.uuid4().hex[:12]
        test_repo_name = f"__health_check_{current_timestamp}_{unique_id}"
        test_timestamp = current_timestamp
        
        activity.logger.info(f"Health check using test key: {test_repo_name}")
        
        # Step 1: Write test item
        activity.logger.info("Testing DynamoDB write operation...")
        test_item = {
            'repository_name': test_repo_name,
            'repository_url': 'https://health.check/test',
            'analysis_timestamp': test_timestamp,
            'analysis_type': 'health_check',
            'latest_commit': 'test_commit_123',
            'branch_name': 'health_check_branch',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'health_check': True,  # Flag to identify health check items
            'ttl_timestamp': test_timestamp + 60  # Expire in 1 minute if not deleted
        }
        
        # Convert floats to Decimal for DynamoDB
        test_item = dynamodb_client._convert_floats_to_decimal(test_item)
        dynamodb_client.table.put_item(Item=test_item)
        activity.logger.info("✓ Write operation successful")
        
        # Step 2: Read test item back
        activity.logger.info("Testing DynamoDB read operation...")
        response = dynamodb_client.table.get_item(
            Key={
                'repository_name': test_repo_name,
                'analysis_timestamp': test_timestamp
            }
        )
        
        if 'Item' not in response:
            raise Exception("Failed to read back test item - item not found")
        
        read_item = response['Item']
        if read_item.get('repository_name') != test_repo_name:
            raise Exception(f"Read verification failed - expected {test_repo_name}, got {read_item.get('repository_name')}")
        
        activity.logger.info("✓ Read operation successful")
        
        # Step 3: Delete test item
        activity.logger.info("Testing DynamoDB delete operation...")
        dynamodb_client.table.delete_item(
            Key={
                'repository_name': test_repo_name,
                'analysis_timestamp': test_timestamp
            }
        )
        activity.logger.info("✓ Delete operation successful")
        
        # Step 4: Verify deletion
        activity.logger.info("Verifying test item was deleted...")
        verify_response = dynamodb_client.table.get_item(
            Key={
                'repository_name': test_repo_name,
                'analysis_timestamp': test_timestamp
            }
        )
        
        if 'Item' in verify_response:
            activity.logger.warning("Test item still exists after deletion (may be eventual consistency)")
        else:
            activity.logger.info("✓ Deletion verified")
        
        activity.logger.info("DynamoDB health check completed successfully")
        
        return {
            "status": "healthy",
            "message": "DynamoDB is accessible and all operations work correctly",
            "table_name": dynamodb_client.table_name,
            "operations_tested": ["write", "read", "delete"],
            "test_key_used": test_repo_name
        }
        
    except ImportError as e:
        activity.logger.error(f"Failed to import DynamoDB client: {e}")
        return {
            "status": "unhealthy",
            "message": f"DynamoDB client import failed: {str(e)}",
            "error_type": "import_error"
        }
        
    except Exception as e:
        activity.logger.error(f"DynamoDB health check failed: {e}")
        
        # Try to clean up test item if it exists
        try:
            if 'test_repo_name' in locals() and 'test_timestamp' in locals():
                activity.logger.info("Attempting to clean up test item after failure...")
                dynamodb_client.table.delete_item(
                    Key={
                        'repository_name': test_repo_name,
                        'analysis_timestamp': test_timestamp
                    },
                    ConditionExpression='attribute_exists(repository_name)'  # Only delete if exists
                )
                activity.logger.info("Test item cleaned up")
        except:
            pass  # Ignore cleanup errors
        
        return {
            "status": "unhealthy",
            "message": f"DynamoDB health check failed: {str(e)}",
            "error_type": type(e).__name__
        }


@activity.defn
async def cleanup_old_health_checks() -> Dict:
    """
    Clean up any old health check items that might have been left behind.
    This is a maintenance activity that can be run periodically.
    
    Returns:
        Dict with cleanup results
    """
    activity.logger.info("Cleaning up old health check items")
    
    try:
        from utils.dynamodb_client import get_dynamodb_client
        from boto3.dynamodb.conditions import Attr
        
        dynamodb_client = get_dynamodb_client()
        
        # Scan for health check items (this should be very few items)
        response = dynamodb_client.table.scan(
            FilterExpression=Attr('health_check').eq(True),
            Limit=100  # Limit to prevent runaway scans
        )
        
        items_deleted = 0
        for item in response.get('Items', []):
            try:
                dynamodb_client.table.delete_item(
                    Key={
                        'repository_name': item['repository_name'],
                        'analysis_timestamp': item['analysis_timestamp']
                    }
                )
                items_deleted += 1
                activity.logger.info(f"Deleted old health check item: {item['repository_name']}")
            except Exception as e:
                activity.logger.warning(f"Failed to delete health check item: {e}")
        
        activity.logger.info(f"Cleanup completed - deleted {items_deleted} old health check items")
        
        return {
            "status": "success",
            "items_deleted": items_deleted,
            "message": f"Cleaned up {items_deleted} old health check items"
        }
        
    except Exception as e:
        activity.logger.error(f"Health check cleanup failed: {e}")
        return {
            "status": "failed",
            "message": f"Cleanup failed: {str(e)}",
            "items_deleted": 0
        }
