#!/bin/bash

# Get Started Wizard for Repo Swarm
# This script helps you set up your .env.local file for local development

set -e

echo "🚀 Welcome to Repo Swarm Setup Wizard!"
echo "======================================"
echo ""
echo "This wizard will help you configure your local development environment."
echo "It will create a .env.local file based on env.example with your custom settings."
echo ""

# Check if .env.local already exists
if [ -f ".env.local" ]; then
    echo "⚠️  .env.local already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Your existing .env.local file is unchanged."
        exit 0
    fi
fi

echo "📋 Let's configure your environment step by step..."
echo ""

# Copy env.example to .env.local
cp env.example .env.local

# Function to update env variable in .env.local
update_env_var() {
    local var_name="$1"
    local var_value="$2"
    # Escape special characters for sed
    escaped_value=$(printf '%s\n' "$var_value" | sed 's/[[\.*^$()+?{|]/\\&/g')
    sed -i'' "s|^$var_name=.*|$var_name=$escaped_value|" .env.local
}

echo "🤖 Claude API Configuration"
echo "---------------------------"
echo "You need an Anthropic API key to use Claude for repository analysis."
echo "Get one from: https://console.anthropic.com/"
echo ""
read -p "Enter your Anthropic API key: " anthropic_key
if [ -z "$anthropic_key" ]; then
    echo "❌ Anthropic API key is required. Setup cancelled."
    rm .env.local
    exit 1
fi
update_env_var "ANTHROPIC_API_KEY" "$anthropic_key"
echo "✅ Claude API key configured"
echo ""

echo "🐙 GitHub Configuration"
echo "-----------------------"
echo "A GitHub token is recommended for higher rate limits when analyzing repositories."
echo "Create one at: https://github.com/settings/tokens (with 'repo' scope)"
echo ""
read -p "Enter your GitHub token (optional, press Enter to skip): " github_token
if [ -n "$github_token" ]; then
    update_env_var "GITHUB_TOKEN" "$github_token"
    echo "✅ GitHub token configured"
else
    echo "ℹ️  GitHub token skipped - you can add it later if needed"
fi
echo ""

echo "🏗️  Architecture Hub Configuration"
echo "----------------------------------"
echo "The Architecture Hub is where analysis results are stored."
echo ""
read -p "Enter your GitHub username/organization for the Architecture Hub: " arch_username
if [ -z "$arch_username" ]; then
    echo "❌ Architecture Hub username is required. Setup cancelled."
    rm .env.local
    exit 1
fi

read -p "Enter Architecture Hub repository name [my-architecture-hub]: " arch_repo_name
arch_repo_name=${arch_repo_name:-my-architecture-hub}

update_env_var "ARCH_HUB_BASE_URL" "https://github.com/$arch_username"
update_env_var "ARCH_HUB_REPO_NAME" "$arch_repo_name"
echo "✅ Architecture Hub configured: https://github.com/$arch_username/$arch_repo_name"
echo ""

echo "📂 Repository Configuration"
echo "---------------------------"
echo "Configure a test organization and repository for development."
echo ""
read -p "Enter default organization name for testing [$arch_username]: " default_org
default_org=${default_org:-$arch_username}

read -p "Enter default repository URL for testing [https://github.com/sindresorhus/is]: " default_repo_url
default_repo_url=${default_repo_url:-https://github.com/sindresorhus/is}

update_env_var "DEFAULT_ORG_NAME" "$default_org"
update_env_var "DEFAULT_REPO_URL" "$default_repo_url"
echo "✅ Repository configuration set"
echo ""

echo "👤 Git Configuration"
echo "--------------------"
echo "Configure git user details for commits (used when creating Architecture Hub)."
echo ""

# Get current git config or ask user
current_name=$(git config --global user.name 2>/dev/null || echo "")
current_email=$(git config --global user.email 2>/dev/null || echo "")

read -p "Enter git user name${current_name:+ [$current_name]}: " git_name
git_name=${git_name:-$current_name}
if [ -z "$git_name" ]; then
    echo "❌ Git user name is required. Setup cancelled."
    rm .env.local
    exit 1
fi

read -p "Enter git user email${current_email:+ [$current_email]}: " git_email
git_email=${git_email:-$current_email}
if [ -z "$git_email" ]; then
    echo "❌ Git user email is required. Setup cancelled."
    rm .env.local
    exit 1
fi

update_env_var "GIT_USER_NAME" "\"$git_name\""
update_env_var "GIT_USER_EMAIL" "$git_email"
echo "✅ Git configuration set"
echo ""

echo "🔧 Optional AWS/DynamoDB Configuration"
echo "--------------------------------------"
echo "If you want to test with real AWS DynamoDB instead of local file storage."
echo ""
read -p "Configure AWS settings? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Enter your AWS credentials:"
    read -p "AWS Access Key ID: " aws_key_id
    read -p "AWS Secret Access Key: " aws_secret_key
    read -p "AWS Region [us-east-1]: " aws_region
    aws_region=${aws_region:-us-east-1}
    read -p "DynamoDB Endpoint URL (leave empty for production): " dynamodb_endpoint

    if [ -n "$aws_key_id" ] && [ -n "$aws_secret_key" ]; then
        # Uncomment and set AWS settings
        sed -i'' "s|^# AWS_ACCESS_KEY_ID=.*|AWS_ACCESS_KEY_ID=$aws_key_id|" .env.local
        sed -i'' "s|^# AWS_SECRET_ACCESS_KEY=.*|AWS_SECRET_ACCESS_KEY=$aws_secret_key|" .env.local
        sed -i'' "s|^# AWS_REGION=.*|AWS_REGION=$aws_region|" .env.local
        if [ -n "$dynamodb_endpoint" ]; then
            sed -i'' "s|^# DYNAMODB_ENDPOINT_URL=.*|DYNAMODB_ENDPOINT_URL=$dynamodb_endpoint|" .env.local
        fi
        echo "✅ AWS configuration set"
    else
        echo "ℹ️  AWS configuration skipped - missing required credentials"
    fi
else
    echo "ℹ️  AWS configuration skipped"
fi
echo ""

echo "🎯 Setup Complete!"
echo "=================="
echo ""
echo "Your .env.local file has been created with the following configuration:"
echo ""
echo "🤖 Claude API: ✅ Configured"
echo "🐙 GitHub Token: $([ -n "$github_token" ] && echo "✅ Configured" || echo "⚠️  Not configured")"
echo "🏗️  Architecture Hub: https://github.com/$arch_username/$arch_repo_name"
echo "📂 Default Organization: $default_org"
echo "📂 Default Repository: $default_repo_url"
echo "👤 Git User: $git_name <$git_email>"
echo ""
echo "📚 Next Steps:"
echo "1. Run 'mise dev-dependencies' to install Python dependencies"
echo "2. Run 'mise verify-config' to validate your configuration"
echo "3. Run 'mise dev-server' to start the Temporal server"
echo "4. Run 'mise investigate-one' to test with a single repository"
echo ""
echo "For more information, see the README.md file."
echo ""
echo "Happy coding! 🎉"
