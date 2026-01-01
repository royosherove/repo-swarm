#!/bin/bash

# Script to run single repository investigation locally for testing
# Usage: ./single.sh [REPO_NAME_OR_URL] [force] [model MODEL] [max-tokens NUM] [type TYPE]
# Default repository is "is-odd" if not specified

# Sanitize input to prevent command injection
sanitize_input() {
    local input="$1"
    # Remove shell metacharacters and control characters
    echo "$input" | tr -d ';|&$`<>(){}[]!*?~#'
}

# Cleanup function for error handling
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo ""
        echo "❌ Script failed with exit code $exit_code"
    fi
    echo "🧹 Cleaning up..."
    [ -n "$WORKER_PID" ] && kill $WORKER_PID 2>/dev/null && echo "   Stopped worker (PID: $WORKER_PID)"
    [ -n "$SERVER_PID" ] && kill $SERVER_PID 2>/dev/null && echo "   Stopped Temporal server (PID: $SERVER_PID)"
    echo "✅ Cleanup complete"
}

# Register cleanup for all exit conditions
trap cleanup EXIT ERR INT TERM

# Validate and load .env.local file for local testing
if [ -f ".env.local" ]; then
    echo "📂 Loading configuration from .env.local..."

    # Security check: verify file ownership and permissions
    if [ "$(stat -f '%u' .env.local 2>/dev/null || stat -c '%u' .env.local 2>/dev/null)" != "$(id -u)" ]; then
        echo "⚠️  Warning: .env.local is not owned by current user"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Aborted for security reasons"
            exit 1
        fi
    fi

    # Check if file has overly permissive permissions
    file_perms=$(stat -f '%Lp' .env.local 2>/dev/null || stat -c '%a' .env.local 2>/dev/null)
    if [ "${file_perms: -1}" != "0" ]; then
        echo "⚠️  Warning: .env.local has world-readable permissions ($file_perms)"
        echo "💡 Recommended: chmod 600 .env.local"
    fi

    set -a  # Export all variables
    source .env.local
    set +a  # Stop exporting
    echo "✅ Loaded .env.local"
else
    echo "⚠️  Warning: .env.local not found, using default local settings"
    # Set default environment variables for local testing
    export PROMPT_CONTEXT_STORAGE=file
    export SKIP_DYNAMODB_CHECK=true
    export LOCAL_TESTING=true
fi

echo "Setting up Single Repository Investigation (Local Mode)..."
echo "📝 Environment configured for local testing:"
echo "   PROMPT_CONTEXT_STORAGE=${PROMPT_CONTEXT_STORAGE:-file}"
echo "   SKIP_DYNAMODB_CHECK=${SKIP_DYNAMODB_CHECK:-true}"
echo "   LOCAL_TESTING=${LOCAL_TESTING:-true}"
echo ""

uv sync

# Start Temporal server in background
echo "Starting Temporal server..."
mise run dev-server &
SERVER_PID=$!
sleep 5

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable is not set"
    echo "Please set your Claude API key:"
    echo "export ANTHROPIC_API_KEY='your-api-key-here'"
    exit 1
fi

# Default repository if not specified
DEFAULT_REPO="is-odd"
REPO_ARG=$(sanitize_input "${1:-$DEFAULT_REPO}")

# Check if first argument is a special flag (h, help, dry-run, force, etc.)
if [[ "$1" == "h" ]] || [[ "$1" == "help" ]]; then
    echo "📚 Single Repository Investigation (Local Testing) Help"
    echo ""
    echo "Usage: mise single [REPO_NAME_OR_URL] [ARGUMENTS]"
    echo ""
    echo "Repository Argument:"
    echo "  REPO_NAME_OR_URL                         Repository name from repos.json or direct GitHub URL"
    echo "                                           Default: is-odd"
    echo ""
    echo "Arguments (can be used in any order):"
    echo "  force                                    Forces investigation ignoring cache"
    echo "  force-section SECTION_NAME               Force re-execution of specific section"
    echo "  model MODEL_NAME                         Override Claude model to use"
    echo "  max-tokens NUMBER                        Override max tokens (100-100000)"
    echo "  type TYPE                                Override repository type"
    echo "  dry-run                                  Show what would be executed without running"
    echo "  h, help                                  Show this help message"
    echo ""
    echo "Valid Claude models:"
    echo "  claude-3-5-sonnet-20241022 (default)"
    echo "  claude-3-opus-20240229"
    echo "  claude-3-sonnet-20240229"
    echo "  claude-3-haiku-20241022"
    echo ""
    echo "Valid repository types:"
    echo "  generic, backend, frontend, mobile, infra-as-code, libraries"
    echo ""
    echo "Examples:"
    echo "  mise single                                    # Investigate is-odd (default)"
    echo "  mise single is-even                             # Investigate is-even repository"
    echo "  mise single https://github.com/user/repo      # Direct URL"
    echo "  mise single is-odd force                # Force investigation of is-odd"
    echo "  mise single force                             # Force investigation of default (is-odd)"
    echo "  mise single force-section monitoring          # Force only monitoring section"
    echo "  mise single model claude-3-haiku-20241022     # Use default repo with different model"
    echo "  mise single is-odd type libraries max-tokens 5000"
    echo ""
    kill $SERVER_PID 2>/dev/null
    exit 0
fi

# If first argument is a flag (not a repo), use default repo
if [[ "$1" == "force" ]] || [[ "$1" == "force-section" ]] || [[ "$1" == "dry-run" ]] || [[ "$1" == "model" ]] || [[ "$1" == "max-tokens" ]] || [[ "$1" == "type" ]]; then
    REPO_ARG="$DEFAULT_REPO"
    # Don't shift, process all arguments as flags
    ARGS_TO_PROCESS="$@"
else
    # First argument is the repository, shift it and process the rest
    shift
    ARGS_TO_PROCESS="$@"
fi

echo "🔍 Starting single repository investigation (Local Mode)..."
echo "Repository: $REPO_ARG"

# Parse remaining arguments for configuration overrides
FORCE_FLAG=""
FORCE_SECTION=""
CLAUDE_MODEL_ARG=""
CLAUDE_MODEL_VALUE=""
MAX_TOKENS=""
REPO_TYPE=""
DRY_RUN=false

# Process arguments
for arg in $ARGS_TO_PROCESS; do
    case "$arg" in
        force)
            FORCE_FLAG="--force"
            echo "🔄 Force mode enabled - will ignore cache"
            ;;
        force-section)
            # Next argument should be the section name
            FORCE_SECTION_NEXT=true
            ;;
        dry-run)
            echo "🧪 DRY RUN MODE - will not execute investigation"
            DRY_RUN=true
            ;;
        model)
            # Next argument should be the model name
            CLAUDE_MODEL_NEXT=true
            ;;
        max-tokens)
            # Next argument should be the max tokens value
            MAX_TOKENS_NEXT=true
            ;;
        type)
            # Next argument should be the repository type
            REPO_TYPE_NEXT=true
            ;;
        *)
            # Check if this is a value for a previous flag
            if [ "$FORCE_SECTION_NEXT" = true ]; then
                FORCE_SECTION="--force-section=$arg"
                echo "🔧 Force section override: $arg"
                FORCE_SECTION_NEXT=false
            elif [ "$CLAUDE_MODEL_NEXT" = true ]; then
                CLAUDE_MODEL_ARG="--claude-model=$arg"
                CLAUDE_MODEL_VALUE="$arg"
                echo "🤖 Using Claude model: $arg"
                CLAUDE_MODEL_NEXT=false
            elif [ "$MAX_TOKENS_NEXT" = true ]; then
                # Validate max tokens
                if ! [[ "$arg" =~ ^[0-9]+$ ]] || [ "$arg" -lt 100 ] || [ "$arg" -gt 100000 ]; then
                    echo "❌ Error: max-tokens must be a number between 100 and 100000"
                    kill $SERVER_PID 2>/dev/null
                    exit 1
                fi
                MAX_TOKENS="--max-tokens=$arg"
                echo "📝 Using max tokens: $arg"
                MAX_TOKENS_NEXT=false
            elif [ "$REPO_TYPE_NEXT" = true ]; then
                # Validate repository type
                if [[ ! "$arg" =~ ^(generic|backend|frontend|mobile|infra-as-code|libraries)$ ]]; then
                    echo "❌ Error: Invalid repository type: $arg"
                    echo "Valid types: generic, backend, frontend, mobile, infra-as-code, libraries"
                    kill $SERVER_PID 2>/dev/null
                    exit 1
                fi
                REPO_TYPE="--type=$arg"
                echo "📦 Using repository type: $arg"
                REPO_TYPE_NEXT=false
            fi
            ;;
    esac
done

# Start the worker in background
echo "Starting Temporal worker..."
# Override CLAUDE_MODEL environment variable if specified via command-line
if [ -n "$CLAUDE_MODEL_VALUE" ]; then
    export CLAUDE_MODEL="$CLAUDE_MODEL_VALUE"
fi
# Debug: verify environment variables are set
echo "   CLAUDE_MODEL=${CLAUDE_MODEL}"
echo "   ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}"
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "   ANTHROPIC_API_KEY=********** (present)"
else
    echo "   ANTHROPIC_API_KEY=(not set)"
fi
# Ensure environment variables are exported before starting worker
export ANTHROPIC_BASE_URL ANTHROPIC_API_KEY CLAUDE_MODEL
(cd src && uv run python -m investigate_worker) &
WORKER_PID=$!
sleep 3

# Prepare the command
# Export environment variables to ensure they're available in subprocess
export LOCAL_TESTING SKIP_DYNAMODB_CHECK PROMPT_CONTEXT_STORAGE
CMD="cd src && uv run python -m client investigate-single \"$REPO_ARG\" $FORCE_FLAG $FORCE_SECTION $CLAUDE_MODEL_ARG $MAX_TOKENS $REPO_TYPE"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "🧪 DRY RUN - Would execute:"
    echo "   $CMD"
    echo ""
    echo "Configuration:"
    echo "   Repository: $REPO_ARG"
    [ -n "$FORCE_FLAG" ] && echo "   Force: enabled"
    [ -n "$FORCE_SECTION" ] && echo "   Force section: ${FORCE_SECTION#--force-section=}"
    [ -n "$CLAUDE_MODEL_ARG" ] && echo "   Model override: ${CLAUDE_MODEL_ARG#--claude-model=}"
    [ -n "$MAX_TOKENS" ] && echo "   Max tokens override: ${MAX_TOKENS#--max-tokens=}"
    [ -n "$REPO_TYPE" ] && echo "   Repository type override: ${REPO_TYPE#--type=}"
else
    echo ""
    echo "📊 Configuration:"
    echo "   Repository: $REPO_ARG"
    [ -n "$FORCE_FLAG" ] && echo "   Force: enabled"
    [ -n "$FORCE_SECTION" ] && echo "   Force section: ${FORCE_SECTION#--force-section=}"
    [ -n "$CLAUDE_MODEL_ARG" ] && echo "   Model: ${CLAUDE_MODEL_ARG#--claude-model=}"
    [ -n "$MAX_TOKENS" ] && echo "   Max tokens: ${MAX_TOKENS#--max-tokens=}"
    [ -n "$REPO_TYPE" ] && echo "   Repository type: ${REPO_TYPE#--type=}"
    echo ""
    echo "Running single repository investigation..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Run the workflow
    eval $CMD
fi

# Cleanup will be handled by trap
echo ""
echo "✅ Single repository investigation complete!"
