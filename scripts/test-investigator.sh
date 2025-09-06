#!/bin/bash

# Test script for Claude Investigator
# This script validates that the Claude Investigator is working correctly

# Set environment variables for local testing
export PROMPT_CONTEXT_STORAGE=file
export SKIP_DYNAMODB_CHECK=true
export LOCAL_TESTING=true

set -e  # Exit on any error

# Function to get repository URL from repos.json
get_repo_url() {
    local repo_name=$1
    local repos_file="prompts/repos.json"
    
    if [ ! -f "$repos_file" ]; then
        echo "❌ Error: repos.json file not found at $repos_file"
        exit 1
    fi
    
    # If no repo name provided, use default
    if [ -z "$repo_name" ]; then
        repo_url=$(python3 -c "import json; print(json.load(open('$repos_file'))['default'])")
        echo "Using default repository: $repo_url" >&2
    else
        # Check if it's a direct URL
        if [[ "$repo_name" == http* ]]; then
            repo_url="$repo_name"
            echo "Using provided URL: $repo_url" >&2
        else
            # Try to get from repos.json
            repo_url=$(python3 -c "
import json
try:
    data = json.load(open('$repos_file'))
    if '$repo_name' in data['repositories']:
        print(data['repositories']['$repo_name']['url'])
    else:
        print('NOT_FOUND')
except:
    print('ERROR')
")
            
            if [ "$repo_url" = "NOT_FOUND" ]; then
                echo "❌ Error: Repository '$repo_name' not found in repos.json"
                echo "Available repositories:"
                python3 -c "import json; data = json.load(open('$repos_file')); [print(f'  - {k}: {v[\"description\"]}') for k, v in data['repositories'].items()]"
                exit 1
            elif [ "$repo_url" = "ERROR" ]; then
                echo "❌ Error: Failed to read repos.json file"
                exit 1
            else
                echo "Using repository '$repo_name': $repo_url" >&2
            fi
        fi
    fi
    
    echo "$repo_url"
}

echo "🧪 Testing Claude Investigator with validation..."

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable is not set"
    echo "Please set your Claude API key:"
    echo "export ANTHROPIC_API_KEY='your-api-key-here'"
    exit 1
fi

# Get repository URL (optional parameter)
REPO_NAME=$1
REPO_URL=$(get_repo_url "$REPO_NAME")

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Clean up any existing temp folder
echo "🧹 Cleaning up any existing temp folder..."
rm -rf src/investigator/temp

# Run the investigation
echo "🔍 Running Claude Investigator test..."
cd src/investigator
python investigator.py "$REPO_URL"

# Check if the investigation was successful
if [ $? -ne 0 ]; then
    echo "❌ Test failed: Investigation did not complete successfully"
    exit 1
fi

echo "✅ Investigation completed successfully!"

# Go back to project root to check the temp directory
cd ../..

# Validate the output file
echo "🔍 Validating generated output file..."

# Check if {repo-name}-arch.md file exists
# The file will be in temp/[repo-name]/arch-docs/{repo-name}-arch.md where repo-name is extracted from the URL
ARCH_FILE=$(find temp -path "*/arch-docs/*-arch.md" -type f 2>/dev/null | head -1)
if [ -z "$ARCH_FILE" ] || [ ! -f "$ARCH_FILE" ]; then
    echo "❌ Test failed: {repo-name}-arch.md file not found in arch-docs folder"
    echo "Available files in temp directory:"
    find temp -name "*.md" -type f 2>/dev/null || echo "No markdown files found in temp directory"
    ls -la temp/ 2>/dev/null || echo "temp directory not found"
    exit 1
fi

echo "✅ {repo-name}-arch.md file found at: $ARCH_FILE"

# Check file size (should not be empty)
FILE_SIZE=$(wc -c < "$ARCH_FILE")
if [ "$FILE_SIZE" -lt 100 ]; then
    echo "❌ Test failed: {repo-name}-arch.md file is too small ($FILE_SIZE bytes), expected at least 100 bytes"
    exit 1
fi

echo "✅ File size is reasonable ($FILE_SIZE bytes)"

# Check if file contains expected content
if ! grep -q "Repository Architecture Analysis" "$ARCH_FILE"; then
    echo "❌ Test failed: {repo-name}-arch.md does not contain expected header"
    exit 1
fi

# Check for expected sections from the new sequential analysis approach
if ! grep -q "Hl Overview\|High Level Overview" "$ARCH_FILE"; then
    echo "❌ Test failed: {repo-name}-arch.md does not contain expected 'Hl Overview' section"
    exit 1
fi

if ! grep -q "Dependencies" "$ARCH_FILE"; then
    echo "❌ Test failed: {repo-name}-arch.md does not contain expected 'Dependencies' section"
    exit 1
fi

if ! grep -q "Core Entities" "$ARCH_FILE"; then
    echo "❌ Test failed: {repo-name}-arch.md does not contain expected 'Core Entities' section"
    exit 1
fi

# Count lines to ensure substantial content
LINE_COUNT=$(wc -l < "$ARCH_FILE")
if [ "$LINE_COUNT" -lt 10 ]; then
    echo "❌ Test failed: {repo-name}-arch.md has too few lines ($LINE_COUNT), expected at least 10 lines"
    exit 1
fi

echo "✅ File contains substantial content ($LINE_COUNT lines)"

# Display a preview of the generated file
echo ""
echo "📄 Generated {repo-name}-arch.md preview (first 20 lines):"
echo "================================================"
head -20 "$ARCH_FILE"
echo "================================================"

echo ""
echo "🎉 All tests passed! Claude Investigator is working correctly."
echo "📁 Full analysis saved to: $(pwd)/$ARCH_FILE" 