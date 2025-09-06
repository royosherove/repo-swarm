#!/bin/bash

# Test script for get-started.sh
# This provides automated input to test the wizard

echo "Testing get-started wizard with automated input..."

# Provide test input to the wizard
echo -e "y\ntest-anthropic-key\ntest-github-token\ntestuser\ntest-arch-repo\n\ntest-org\n\nTest User\ntest@example.com\nn" | bash scripts/get-started.sh

echo "Test completed. Checking results..."

# Check if .env.local was created/updated
if [ -f ".env.local" ]; then
    echo "✅ .env.local exists"
    echo "🔍 Checking key configurations:"
    grep "ANTHROPIC_API_KEY=" .env.local
    grep "GITHUB_TOKEN=" .env.local
    grep "ARCH_HUB_BASE_URL=" .env.local
    grep "GIT_USER_NAME=" .env.local
else
    echo "❌ .env.local was not created"
fi
