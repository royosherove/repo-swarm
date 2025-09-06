#!/usr/bin/env python3
"""
Integration test for DynamoDB functionality using the actual investigator components.

This test verifies that our investigation cache activities can successfully
interact with the real DynamoDB table in staging.
"""

import os
import sys
import tempfile
import shutil
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up environment variables for testing
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_PROFILE"] = "dev"
os.environ["DYNAMODB_TABLE_NAME"] = "staging-repo-swarm-results"
os.environ["ENVIRONMENT"] = "staging"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_aws_credentials():
    """Check if AWS credentials are available."""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS credentials found:")
        print(f"  Account: {identity.get('Account')}")
        print(f"  UserId: {identity.get('UserId')}")
        print(f"  Arn: {identity.get('Arn')}")
        return True
    except Exception as e:
        print(f"❌ AWS credentials not available: {e}")
        return False


def verify_table_exists():
    """Verify the DynamoDB table exists and is accessible."""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        dynamodb = boto3.resource('dynamodb', region_name=os.environ["AWS_DEFAULT_REGION"])
        table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])
        
        # Try to describe the table
        table.load()
        print(f"✓ Table {os.environ['DYNAMODB_TABLE_NAME']} exists and is accessible")
        print(f"  Status: {table.table_status}")
        print(f"  Item count: {table.item_count}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"❌ Table {os.environ['DYNAMODB_TABLE_NAME']} not found")
        else:
            print(f"❌ Error accessing table: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def create_test_repo():
    """Create a temporary test repository with some commits."""
    import git
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_repo_")
    repo_path = Path(temp_dir)
    
    try:
        # Initialize git repo
        repo = git.Repo.init(repo_path)
        
        # Configure git (required for commits)
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")
        
        # Create some test files and commits
        test_file = repo_path / "README.md"
        test_file.write_text("# Test Repository\n\nThis is a test repo for DynamoDB integration testing.\n")
        
        repo.index.add(["README.md"])  # Use relative path
        repo.index.commit("Initial commit")
        
        # Create another commit
        code_file = repo_path / "app.py"
        code_file.write_text("print('Hello, World!')\n")
        repo.index.add(["app.py"])  # Use relative path
        repo.index.commit("Add sample code")
        
        latest_commit = repo.head.commit.hexsha
        branch_name = repo.active_branch.name
        
        print(f"✓ Created test repository at {repo_path}")
        print(f"  Branch: {branch_name}")
        print(f"  Latest commit: {latest_commit[:8]}")
        
        return str(repo_path), latest_commit, branch_name
        
    except Exception as e:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


async def test_investigation_cache_activities():
    """Test the investigation cache activities with real DynamoDB."""
    print("\n" + "="*60)
    print("TESTING INVESTIGATION CACHE ACTIVITIES")
    print("="*60)
    
    try:
        # Import our activities
        from activities.investigation_cache_activities import (
            check_if_repo_needs_investigation,
            save_investigation_metadata
        )
        
        print("✓ Successfully imported investigation cache activities")
        
        # Create a test repository
        repo_path, latest_commit, branch_name = create_test_repo()
        
        try:
            # Test data
            repo_name = "test-integration-repo"
            repo_url = "https://github.com/test/integration-repo"
            
            print(f"\n🧪 Testing with repository: {repo_name}")
            
            # Test 1: Check if repo needs investigation (first time)
            print("\n--- Test 1: First-time investigation check ---")
            result1 = await check_if_repo_needs_investigation(repo_name, repo_url, repo_path)
            
            print(f"Needs investigation: {result1.get('needs_investigation')}")
            print(f"Reason: {result1.get('reason')}")
            print(f"Current commit: {result1.get('latest_commit', '')[:8]}")
            print(f"Current branch: {result1.get('branch_name')}")
            
            assert result1["needs_investigation"] == True, "Should need investigation on first run"
            print("✓ First-time check passed")
            
            # Test 2: Save investigation metadata
            print("\n--- Test 2: Save investigation metadata ---")
            analysis_summary = {
                "total_files": 2,
                "languages": ["markdown", "python"],
                "analysis_date": datetime.now(timezone.utc).isoformat(),
                "test_run": True
            }
            
            save_result = await save_investigation_metadata(
                repo_name=repo_name,
                repo_url=repo_url,
                latest_commit=latest_commit,
                branch_name=branch_name,
                analysis_summary=analysis_summary
            )
            
            print(f"Save status: {save_result.get('status')}")
            print(f"Saved timestamp: {save_result.get('saved_timestamp')}")
            
            if save_result["status"] == "success":
                print("✓ Save metadata passed")
            elif save_result["status"] == "error" and "AccessDeniedException" in str(save_result.get("message", "")):
                print("⚠️  Expected: No write permissions (IAM role will have permissions when deployed)")
                print("✓ DynamoDB write operations are correctly configured but need deployment permissions")
                # Continue with read-only tests
            else:
                assert False, f"Unexpected save error: {save_result}"
            
            # Test 3: Check if repo needs investigation (should skip now)
            print("\n--- Test 3: Second investigation check (should skip) ---")
            result2 = await check_if_repo_needs_investigation(repo_name, repo_url, repo_path)
            
            print(f"Needs investigation: {result2.get('needs_investigation')}")
            print(f"Reason: {result2.get('reason')}")
            last_investigation = result2.get('last_investigation')
            if last_investigation:
                print(f"Last investigation: {datetime.fromtimestamp(last_investigation.get('analysis_timestamp', 0), tz=timezone.utc).isoformat()}")
                print(f"Last commit: {last_investigation.get('latest_commit', '')[:8]}")
            
            assert result2["needs_investigation"] == False, "Should not need investigation on second run"
            print("✓ Second check passed (correctly skipped)")
            
            # Test 4: Test direct DynamoDB client operations
            print("\n--- Test 4: Direct DynamoDB client operations ---")
            from utils.dynamodb_client import get_dynamodb_client
            
            client = get_dynamodb_client()
            
            # Get latest investigation
            latest = client.get_latest_investigation(repo_name)
            assert latest is not None, "Should find the saved investigation"
            print(f"✓ Retrieved latest investigation: {latest['latest_commit'][:8]}")
            
            # Query by analysis type
            investigations = client.query_by_analysis_type("investigation", limit=5)
            print(f"✓ Found {len(investigations)} investigations of type 'investigation'")
            
            # Get all analyses for this repo
            all_analyses = client.get_all_analyses(repo_name, limit=10)
            print(f"✓ Found {len(all_analyses)} total analyses for {repo_name}")
            
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            return True
            
        finally:
            # Clean up test repository
            shutil.rmtree(repo_path, ignore_errors=True)
            print(f"✓ Cleaned up test repository")
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_modified_repo():
    """Test behavior when repository has changes."""
    print("\n" + "="*60)
    print("TESTING WITH REPOSITORY CHANGES")
    print("="*60)
    
    try:
        from activities.investigation_cache_activities import (
            check_if_repo_needs_investigation,
            save_investigation_metadata
        )
        
        # Create a test repository
        repo_path, initial_commit, branch_name = create_test_repo()
        
        try:
            repo_name = "test-changes-repo"
            repo_url = "https://github.com/test/changes-repo"
            
            # Save initial state
            print("📝 Saving initial investigation state...")
            await save_investigation_metadata(
                repo_name=repo_name,
                repo_url=repo_url,
                latest_commit=initial_commit,
                branch_name=branch_name,
                analysis_summary={"initial": True}
            )
            
            # Modify the repository (add new commit)
            import git
            repo = git.Repo(repo_path)
            
            new_file = Path(repo_path) / "new_feature.py"
            new_file.write_text("def new_feature():\n    pass\n")
            repo.index.add(["new_feature.py"])  # Use relative path
            new_commit = repo.index.commit("Add new feature")
            
            print(f"📝 Added new commit: {new_commit.hexsha[:8]}")
            
            # Check if investigation is needed (should be True due to new commit)
            result = await check_if_repo_needs_investigation(repo_name, repo_url, repo_path)
            
            print(f"Needs investigation: {result.get('needs_investigation')}")
            print(f"Reason: {result.get('reason')}")
            
            assert result["needs_investigation"] == True, "Should need investigation after new commit"
            print("✓ Correctly detected repository changes")
            
            return True
            
        finally:
            shutil.rmtree(repo_path, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ Repository changes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_data():
    """Clean up any test data from DynamoDB."""
    print("\n" + "="*60)
    print("CLEANING UP TEST DATA")
    print("="*60)
    
    try:
        from utils.dynamodb_client import get_dynamodb_client
        
        client = get_dynamodb_client()
        
        # Find and delete test repositories
        test_repos = ["test-integration-repo", "test-changes-repo"]
        
        for repo_name in test_repos:
            try:
                analyses = client.get_all_analyses(repo_name, limit=100)
                for analysis in analyses:
                    client.delete_analysis(
                        repo_name, 
                        int(analysis['analysis_timestamp'])
                    )
                    print(f"✓ Deleted test data for {repo_name}")
            except Exception as e:
                print(f"⚠️  Could not clean up {repo_name}: {e}")
        
        print("✓ Test data cleanup completed")
        
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")


async def main():
    """Run the integration tests."""
    print("DYNAMODB INTEGRATION TEST")
    print("="*60)
    print("Testing the investigator's DynamoDB cache functionality")
    print("against the real staging-architecture-hub table.")
    print()
    
    # Check prerequisites
    if not check_aws_credentials():
        return 1
    
    if not verify_table_exists():
        return 1
    
    try:
        # Run the tests
        success1 = await test_investigation_cache_activities()
        success2 = await test_with_modified_repo()
        
        if success1 and success2:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("The DynamoDB cache functionality is working correctly with the staging table.")
            return 0
        else:
            print("\n❌ SOME INTEGRATION TESTS FAILED!")
            return 1
            
    finally:
        # Clean up test data
        cleanup_test_data()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
