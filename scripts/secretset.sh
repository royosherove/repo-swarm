#!/bin/bash

# Script to set SSM parameters from .env file
# Usage: mise secretset [environment] [ssm_base_path]
# Examples:
#   mise secretset staging /staging/repo_swarm
#   mise secretset production /prod/repo_swarm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists, fallback to env.example
ENV_FILE=".env"
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        print_warning ".env file not found, using env.example instead"
        ENV_FILE="env.example"
    else
        print_error ".env or env.example file not found. Please create one based on env.example"
        exit 1
    fi
fi

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: mise secretset [environment] [ssm_base_path] [aws_profile]"
    echo ""
    echo "Sets SSM parameters from .env file for the specified environment."
    echo ""
    echo "Arguments:"
    echo "  environment    Environment name (default: staging)"
    echo "  ssm_base_path  SSM base path (default: /{environment}/repo_swarm)"
    echo "  aws_profile    AWS profile to use (optional)"
    echo ""
    echo "Examples:"
    echo "  mise secretset staging"
    echo "  mise secretset production"
    echo "  mise secretset staging /staging/repo-swarm"
    echo "  mise secretset staging /staging/repo-swarm aws-profile-name"
    echo ""
    echo "Required:"
    echo "  - .env file with configuration values"
    echo "  - AWS CLI installed and configured"
    echo "  - Appropriate AWS permissions for SSM Parameter Store"
    exit 0
fi

# Parse command line arguments
ENVIRONMENT=${1:-staging}
SSM_BASE_PATH=${2:-"/${ENVIRONMENT}/repo_swarm"}
AWS_PROFILE=${3:-""}  # Optional AWS profile parameter
AWS_REGION=${AWS_REGION:-"us-east-1"}  # Default to eu-west-1 if not set

print_status "Setting SSM parameters for environment: $ENVIRONMENT"
print_status "SSM base path: $SSM_BASE_PATH"
print_status "AWS region: $AWS_REGION"
if [ -n "$AWS_PROFILE" ]; then
    print_status "Using AWS profile: $AWS_PROFILE"
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Build AWS CLI options
AWS_CLI_OPTS="--region $AWS_REGION"
if [ -n "$AWS_PROFILE" ]; then
    AWS_CLI_OPTS="$AWS_CLI_OPTS --profile $AWS_PROFILE"
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity $AWS_CLI_OPTS &> /dev/null; then
    if [ -n "$AWS_PROFILE" ]; then
        print_error "AWS credentials not configured for profile '$AWS_PROFILE'. Please run 'aws sso login --profile $AWS_PROFILE' first."
    else
        print_error "AWS credentials not configured. Please configure AWS CLI or run 'aws sso login' first."
    fi
    exit 1
fi

# Display which account we're using
ACCOUNT_ID=$(aws sts get-caller-identity $AWS_CLI_OPTS --query Account --output text)
print_status "Using AWS account: $ACCOUNT_ID"

# Function to set SSM parameter
set_ssm_parameter() {
    local param_name="$1"
    local param_value="$2"
    local param_type="${3:-String}"
    
    if [ -z "$param_value" ]; then
        print_warning "Skipping $param_name (empty value)"
        return 0
    fi
    
    # Show first 10 characters of the value for debugging
    local value_preview="${param_value:0:10}"
    print_status "Setting $param_name (${value_preview}...)..."
    
    # Capture the error message
    local error_output
    if error_output=$(aws ssm put-parameter \
        $AWS_CLI_OPTS \
        --name "$SSM_BASE_PATH/$param_name" \
        --value "$param_value" \
        --type "$param_type" \
        --overwrite 2>&1); then
        print_success "Set $param_name (${value_preview}...)"
    else
        print_error "Failed to set $param_name: $error_output"
        return 1
    fi
}

# Function to set parameter from environment variable if present
set_param_from_env() {
    local param_name="$1"
    local env_var_name="$2"
    local param_type="${3:-String}"
    local env_value="${!env_var_name}"
    
    if [ -n "$env_value" ]; then
        set_ssm_parameter "$param_name" "$env_value" "$param_type" || true
    fi
}

# Function to set default parameter value with warning if env var not set
set_param_with_default() {
    local param_name="$1"
    local env_var_name="$2"
    local default_value="$3"
    local param_type="${4:-String}"
    local env_value="${!env_var_name}"
    
    if [ -z "$env_value" ]; then
        if [ "$default_value" = "CHANGE_ME" ]; then
            print_warning "$env_var_name not set - you'll need to update this manually in SSM"
        fi
        set_ssm_parameter "$param_name" "$default_value" "$param_type" || true
    fi
}

# Read .env file and set parameters
print_status "Reading .env file and setting SSM parameters..."

# Source the environment file to get variables (only if it exists and is not env.example)
if [ "$ENV_FILE" != "env.example" ]; then
    # Export variables from .env file safely, skipping AWS SSO config lines
    while IFS= read -r line; do
        # Skip comments and empty lines
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
            continue
        fi
        # Skip AWS SSO configuration lines that might cause issues
        if [[ "$line" =~ ^AWS_sso_ ]]; then
            continue
        fi
        # Export the variable if it's a valid assignment
        if [[ "$line" =~ ^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*= ]]; then
            export "$line"
        fi
    done < "$ENV_FILE"
fi

# Set Temporal configuration parameters
set_ssm_parameter "temporal_host" "${TEMPORAL_SERVER_URL%:*}" || true
set_ssm_parameter "temporal_port" "${TEMPORAL_SERVER_URL#*:}" || true
set_param_from_env "temporal_namespace" "TEMPORAL_NAMESPACE"
set_param_from_env "temporal_task_queue" "TEMPORAL_TASK_QUEUE"

# Set API keys (as SecureString for security)
set_param_from_env "temporal_api_key" "TEMPORAL_API_KEY" "SecureString"
set_param_from_env "anthropic_api_key" "ANTHROPIC_API_KEY" "SecureString"
set_param_from_env "github_token" "GITHUB_TOKEN" "SecureString"

# Set default values for required parameters if not in .env
print_status "Setting default values for required parameters..."

# Default Temporal configuration
if [ -z "$TEMPORAL_SERVER_URL" ]; then
    set_ssm_parameter "temporal_host" "localhost" || true
    set_ssm_parameter "temporal_port" "7233" || true
fi

# Set default values for parameters not provided in environment
set_param_with_default "temporal_namespace" "TEMPORAL_NAMESPACE" "default" "String"
set_param_with_default "temporal_task_queue" "TEMPORAL_TASK_QUEUE" "investigate-task-queue" "String"
set_param_with_default "temporal_api_key" "TEMPORAL_API_KEY" "CHANGE_ME" "SecureString"
set_param_with_default "anthropic_api_key" "ANTHROPIC_API_KEY" "CHANGE_ME" "SecureString"
set_param_with_default "github_token" "GITHUB_TOKEN" "CHANGE_ME" "SecureString"

print_success "SSM parameters set successfully for $ENVIRONMENT environment!"
print_status "You can verify the parameters with:"
if [ -n "$AWS_PROFILE" ]; then
    echo "  aws ssm get-parameters-by-path --path $SSM_BASE_PATH --recursive --region $AWS_REGION --profile $AWS_PROFILE"
else
    echo "  aws ssm get-parameters-by-path --path $SSM_BASE_PATH --recursive --region $AWS_REGION"
fi 