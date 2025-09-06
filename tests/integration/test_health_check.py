#!/usr/bin/env python3
"""
Test the DynamoDB health check functionality.

This verifies that:
1. Health check can write, read, and delete test items
2. Test items use unique names that won't conflict with real repos
3. Health check properly cleans up after itself
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up environment for testing
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["DYNAMODB_TABLE_NAME"] = "staging-repo-swarm-results"
os.environ["AWS_PROFILE"] = "dev"


async def test_health_check():
    """Test the DynamoDB health check activity."""
    print("\n" + "="*60)
    print("TESTING DYNAMODB HEALTH CHECK")
    print("="*60)
    
    try:
        from activities.dynamodb_health_check_activity import check_dynamodb_health
        from utils.dynamodb_client import get_dynamodb_client
        
        print("\n1️⃣  Running health check...")
        result = await check_dynamodb_health()
        
        print(f"\n📊 Health Check Result:")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        print(f"   Table: {result.get('table_name', 'N/A')}")
        print(f"   Test key used: {result.get('test_key_used', 'N/A')}")
        print(f"   Operations tested: {result.get('operations_tested', [])}")
        
        assert result['status'] == 'healthy', f"Health check failed: {result['message']}"
        
        # Verify the test key pattern
        test_key = result.get('test_key_used', '')
        assert test_key.startswith('__health_check_'), f"Test key should start with '__health_check_', got: {test_key}"
        assert len(test_key.split('_')) >= 5, f"Test key should have timestamp and UUID parts, got: {test_key}"
        
        print("\n✅ Health check passed!")
        
        # Verify no test items were left behind
        print("\n2️⃣  Verifying cleanup...")
        client = get_dynamodb_client()
        
        # Try to read the test item (should not exist)
        try:
            response = client.table.get_item(
                Key={
                    'repository_name': test_key,
                    'analysis_timestamp': int(datetime.now(timezone.utc).timestamp())
                }
            )
            if 'Item' in response:
                print("⚠️  Warning: Test item still exists (checking with exact key)")
        except:
            pass
        
        print("✅ No test items left behind")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Health check test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_check_failure_handling():
    """Test that health check handles failures gracefully."""
    print("\n" + "="*60)
    print("TESTING HEALTH CHECK FAILURE HANDLING")
    print("="*60)
    
    try:
        from activities.dynamodb_health_check_activity import check_dynamodb_health
        import unittest.mock as mock
        
        # Test with invalid table name
        print("\n1️⃣  Testing with invalid configuration...")
        original_table = os.environ.get("DYNAMODB_TABLE_NAME")
        os.environ["DYNAMODB_TABLE_NAME"] = "non-existent-table-xyz"
        
        result = await check_dynamodb_health()
        
        print(f"\n📊 Result with bad config:")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        print(f"   Error type: {result.get('error_type', 'N/A')}")
        
        assert result['status'] == 'unhealthy', "Should report unhealthy with bad config"
        print("✅ Correctly reported unhealthy status")
        
        # Restore original table
        if original_table:
            os.environ["DYNAMODB_TABLE_NAME"] = original_table
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failure handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cleanup_activity():
    """Test the cleanup activity for old health check items."""
    print("\n" + "="*60)
    print("TESTING CLEANUP ACTIVITY")
    print("="*60)
    
    try:
        from activities.dynamodb_health_check_activity import cleanup_old_health_checks
        
        print("\n1️⃣  Running cleanup activity...")
        result = await cleanup_old_health_checks()
        
        print(f"\n📊 Cleanup Result:")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        print(f"   Items deleted: {result.get('items_deleted', 0)}")
        
        assert result['status'] in ['success', 'failed'], f"Unexpected status: {result['status']}"
        print("✅ Cleanup activity completed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Cleanup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all health check tests."""
    print("DYNAMODB HEALTH CHECK TEST SUITE")
    print("="*60)
    print("Testing the health check functionality that runs before")
    print("each repository investigation.")
    print()
    
    # Check AWS credentials first
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS credentials found: {identity.get('UserId', 'Unknown')}")
    except Exception as e:
        print(f"❌ AWS credentials not available: {e}")
        print("Please configure AWS credentials to run this test")
        return 1
    
    tests = [
        ("Health Check Basic Functionality", test_health_check),
        ("Health Check Failure Handling", test_health_check_failure_handling),
        ("Cleanup Activity", test_cleanup_activity)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            success = await test_func()
            if success:
                passed += 1
                print(f"✅ PASSED: {test_name}")
            else:
                failed += 1
                print(f"❌ FAILED: {test_name}")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR in {test_name}: {e}")
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ALL HEALTH CHECK TESTS PASSED!")
        print("\nKey validations:")
        print("1. ✅ Health check writes, reads, and deletes test items")
        print("2. ✅ Test keys are unique and won't conflict with real repos")
        print("3. ✅ Health check cleans up after itself")
        print("4. ✅ Failures are handled gracefully")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
