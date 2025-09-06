#!/bin/bash

# Install test dependencies for DynamoDB testing
echo "Installing test dependencies for DynamoDB testing..."

# Install boto3 (required)
pip install boto3

# Install moto for local mocking (optional)
echo "Installing moto for local testing (optional)..."
pip install moto[dynamodb]

echo "Test dependencies installed successfully!"
echo ""
echo "You can now run the DynamoDB test with:"
echo ""
echo "For local mocking (default):"
echo "python test_dynamodb_local.py"
echo ""
echo "For real AWS testing (requires aws configure or sso login):"
echo "python test_dynamodb_local.py --real-aws"
echo ""
echo "To use a specific table name:"
echo "python test_dynamodb_local.py --real-aws --table-name my-test-table"
