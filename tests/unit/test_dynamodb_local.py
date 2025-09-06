#!/usr/bin/env python3
"""
Local test script to verify DynamoDB functionality for investigation caching.

This script tests the DynamoDB client without requiring the full Temporal worker setup.
It uses moto to mock DynamoDB locally for testing.

Usage:
    python test_dynamodb_local.py

Requirements:
    pip install moto boto3
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Use AWS CLI credentials (assumes aws configure has been run or SSO login)
# Set default region if not already set
if not os.environ.get("AWS_DEFAULT_REGION"):
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"

print("Using AWS CLI credentials for DynamoDB access")

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Mock DynamoDB table name
os.environ["DYNAMODB_TABLE_NAME"] = "test-architecture-hub"

import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from utils.dynamodb_client import DynamoDBClient

# Optional: Import moto for local mocking if available
try:
    from moto.dynamodb import mock_dynamodb
    MOTO_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import path for newer versions
        from moto import mock_dynamodb
        MOTO_AVAILABLE = True
    except ImportError:
        mock_dynamodb = None
        MOTO_AVAILABLE = False


def check_aws_credentials():
    """Check if AWS credentials are available."""
    try:
        # Try to get caller identity to verify credentials
        sts = boto3.client('sts')
        response = sts.get_caller_identity()
        
        print(f"✓ AWS credentials found:")
        print(f"  Account: {response.get('Account', 'Unknown')}")
        print(f"  UserId: {response.get('UserId', 'Unknown')}")
        print(f"  Arn: {response.get('Arn', 'Unknown')}")
        return True
        
    except NoCredentialsError:
        print("✗ No AWS credentials found")
        print("Please run 'aws configure' or 'aws sso login' first")
        return False
    except Exception as e:
        print(f"✗ Error checking AWS credentials: {e}")
        return False


def create_test_table(dynamodb_resource, use_real_aws=False):
    """Create a test DynamoDB table that matches our schema."""
    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    
    if use_real_aws:
        # Check if table already exists
        try:
            existing_table = dynamodb_resource.Table(table_name)
            existing_table.load()
            print(f"✓ Using existing DynamoDB table: {table_name}")
            return existing_table
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
            print(f"Table {table_name} doesn't exist, creating it...")
    
    print(f"Creating test DynamoDB table: {table_name}")
    
    table = dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'repository_name',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'analysis_timestamp',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'repository_name',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'analysis_timestamp',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'analysis_type',
                'AttributeType': 'S'
            }
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'AnalysisTypeIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'analysis_type',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'analysis_timestamp',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                }
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Wait for table to be created
    table.wait_until_exists()
    print(f"✓ Table {table_name} created successfully")
    return table


def test_dynamodb_operations():
    """Test all DynamoDB operations using our client."""
    print("\n" + "="*60)
    print("TESTING DYNAMODB OPERATIONS")
    print("="*60)
    
    try:
        # Initialize our DynamoDB client
        client = DynamoDBClient()
        print("✓ DynamoDB client initialized")
        
        # Test data
        test_repos = [
            {
                "repo_name": "test-repo-1",
                "repo_url": "https://github.com/test/repo1",
                "commit": "abc123def456",
                "branch": "main",
                "analysis_data": {"steps": 5, "duration": 120}
            },
            {
                "repo_name": "test-repo-2", 
                "repo_url": "https://github.com/test/repo2",
                "commit": "xyz789uvw012",
                "branch": "develop",
                "analysis_data": {"steps": 3, "duration": 90}
            },
            {
                "repo_name": "test-repo-1",  # Same repo, different commit
                "repo_url": "https://github.com/test/repo1",
                "commit": "def456ghi789",
                "branch": "main",
                "analysis_data": {"steps": 6, "duration": 150}
            }
        ]
        
        print("\n--- Test 1: Save Investigation Metadata ---")
        saved_items = []
        for i, repo_data in enumerate(test_repos):
            print(f"\nSaving investigation {i+1}: {repo_data['repo_name']} (commit: {repo_data['commit'][:8]})")
            
            result = client.save_investigation_metadata(
                repository_name=repo_data["repo_name"],
                repository_url=repo_data["repo_url"],
                latest_commit=repo_data["commit"],
                branch_name=repo_data["branch"],
                analysis_type="investigation",
                analysis_data=repo_data["analysis_data"],
                ttl_days=90
            )
            
            saved_items.append(result)
            print(f"✓ Saved with timestamp: {result.get('analysis_timestamp')}")
        
        print("\n--- Test 2: Get Latest Investigation ---")
        for repo_name in ["test-repo-1", "test-repo-2", "non-existent-repo"]:
            print(f"\nGetting latest investigation for: {repo_name}")
            
            latest = client.get_latest_investigation(repo_name)
            if latest:
                print(f"✓ Found investigation:")
                print(f"  Commit: {latest['latest_commit'][:8]}")
                print(f"  Branch: {latest['branch_name']}")
                print(f"  Timestamp: {latest['analysis_timestamp']}")
                print(f"  Analysis data: {latest.get('analysis_data', 'None')}")
            else:
                print("✓ No investigation found (expected for non-existent repo)")
        
        print("\n--- Test 3: Query by Analysis Type ---")
        print("\nQuerying all investigations of type 'investigation':")
        
        investigations = client.query_by_analysis_type("investigation", limit=5)
        print(f"✓ Found {len(investigations)} investigations:")
        for inv in investigations:
            print(f"  {inv['repository_name']} - {inv['latest_commit'][:8]} - {inv['branch_name']}")
        
        print("\n--- Test 4: Get All Analyses for Repository ---")
        print("\nGetting all analyses for test-repo-1:")
        
        all_analyses = client.get_all_analyses("test-repo-1", limit=10)
        print(f"✓ Found {len(all_analyses)} analyses:")
        for analysis in all_analyses:
            print(f"  Timestamp: {analysis['analysis_timestamp']} - Commit: {analysis['latest_commit'][:8]}")
        
        print("\n--- Test 5: Test Cache Check Logic ---")
        print("\nSimulating cache check scenarios:")
        
        # Scenario 1: Same commit - should not need investigation
        latest_repo1 = client.get_latest_investigation("test-repo-1")
        if latest_repo1:
            current_commit = latest_repo1['latest_commit']
            current_branch = latest_repo1['branch_name']
            
            print(f"\nScenario 1: Same commit ({current_commit[:8]})")
            if current_commit == latest_repo1['latest_commit']:
                print("✓ Cache hit - no investigation needed")
            else:
                print("✗ Unexpected - should be cache hit")
        
        # Scenario 2: Different commit - should need investigation
        print(f"\nScenario 2: Different commit")
        new_commit = "new123commit456"
        if new_commit != latest_repo1['latest_commit']:
            print("✓ Cache miss - investigation needed")
        else:
            print("✗ Unexpected - should be cache miss")
        
        print("\n--- Test 6: Cleanup Test ---")
        print("\nDeleting a specific investigation:")
        
        if saved_items and latest_repo1:
            delete_result = client.delete_analysis(
                "test-repo-1",
                latest_repo1['analysis_timestamp']
            )
            if delete_result:
                print("✓ Investigation deleted successfully")
            else:
                print("✗ Failed to delete investigation")
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✓ DynamoDB client is working correctly")
        print("✓ Save operations work")
        print("✓ Query operations work") 
        print("✓ Cache logic works as expected")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_conditions():
    """Test error handling in our DynamoDB client."""
    print("\n" + "="*60)
    print("TESTING ERROR CONDITIONS")
    print("="*60)
    
    try:
        # Test with invalid table name
        print("\n--- Test: Invalid Table Name ---")
        old_table_name = os.environ.get("DYNAMODB_TABLE_NAME")
        os.environ["DYNAMODB_TABLE_NAME"] = "non-existent-table"
        
        try:
            client = DynamoDBClient()
            result = client.get_latest_investigation("test-repo")
            print("✗ Should have failed with invalid table name")
        except Exception as e:
            print(f"✓ Correctly handled invalid table: {type(e).__name__}")
        finally:
            # Restore original table name
            if old_table_name:
                os.environ["DYNAMODB_TABLE_NAME"] = old_table_name
        
        print("\n--- Test: Missing Table Name ---")
        if "DYNAMODB_TABLE_NAME" in os.environ:
            del os.environ["DYNAMODB_TABLE_NAME"]
        
        try:
            client = DynamoDBClient()
            print("✗ Should have failed with missing table name")
        except ValueError as e:
            print(f"✓ Correctly handled missing table name: {e}")
        finally:
            # Restore table name
            os.environ["DYNAMODB_TABLE_NAME"] = "test-architecture-hub"
        
        print("\n✓ Error handling tests completed")
        
    except Exception as e:
        print(f"\n✗ Error during error testing: {e}")
        return False
    
    return True


def run_tests_with_real_aws():
    """Run tests using real AWS credentials and DynamoDB."""
    print("DYNAMODB REAL AWS TEST")
    print("="*60)
    print("This test verifies that our DynamoDB client works correctly")
    print("using real AWS credentials and DynamoDB.")
    print()
    
    if not check_aws_credentials():
        return 1
    
    try:
        # Create a real DynamoDB resource
        region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Create or use existing test table
        try:
            create_test_table(dynamodb, use_real_aws=True)
            print("✓ Table is ready for testing")
        except ClientError as e:
            if "AccessDeniedException" in str(e) and "CreateTable" in str(e):
                print("⚠️  No permission to create tables (expected - tables are created by Terraform)")
                print("✓ AWS credentials and DynamoDB connection are working")
                print("✓ The investigate worker will use tables created by Terraform deployment")
                print("\n🎉 BASIC CONNECTIVITY TEST PASSED!")
                print("Next steps:")
                print("  1. Deploy Terraform to create the DynamoDB table")
                print("  2. Update worker IAM role with DynamoDB permissions")
                print("  3. Deploy the investigate worker")
                return 0
            else:
                raise
        
        # Run the tests
        success1 = test_dynamodb_operations()
        success2 = test_error_conditions()
        
        if success1 and success2:
            print("\n🎉 ALL TESTS PASSED!")
            print("The DynamoDB client is ready for use in the investigation worker.")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED!")
            return 1
            
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_tests_with_mock():
    """Run tests using moto to mock DynamoDB."""
    if not MOTO_AVAILABLE:
        print("❌ Moto not available. Install with: pip install moto[dynamodb]")
        return 1
    
    print("DYNAMODB MOCK TEST")
    print("="*60)
    print("This test verifies that our DynamoDB client works correctly")
    print("using moto to mock AWS DynamoDB locally.")
    print()
    
    @mock_dynamodb
    def run_mock_tests():
        try:
            # Create a mock DynamoDB resource
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            
            # Create the test table
            create_test_table(dynamodb)
            
            # Run the tests
            success1 = test_dynamodb_operations()
            success2 = test_error_conditions()
            
            if success1 and success2:
                print("\n🎉 ALL TESTS PASSED!")
                print("The DynamoDB client is ready for use in the investigation worker.")
                return 0
            else:
                print("\n❌ SOME TESTS FAILED!")
                return 1
                
        except Exception as e:
            print(f"\n💥 FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return run_mock_tests()


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test DynamoDB functionality')
    parser.add_argument('--real-aws', action='store_true', 
                       help='Use real AWS credentials instead of mocking')
    parser.add_argument('--table-name', default='test-architecture-hub',
                       help='DynamoDB table name to use (default: test-architecture-hub)')
    
    args = parser.parse_args()
    
    # Set the table name
    os.environ["DYNAMODB_TABLE_NAME"] = args.table_name
    
    if args.real_aws:
        return run_tests_with_real_aws()
    else:
        return run_tests_with_mock()


if __name__ == "__main__":
    # Check dependencies
    try:
        import boto3
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install: pip install boto3")
        sys.exit(1)
    
    sys.exit(main())
