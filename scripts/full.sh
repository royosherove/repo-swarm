#!/bin/bash

# Always load .env.local file for local testing
if [ -f ".env.local" ]; then
    echo "📂 Loading configuration from .env.local..."
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

echo "Setting up Investigate Repositories Workflow (Local Mode)..."
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

echo "🔄 Starting repository investigation workflow (runs every X hours)..."
echo "This will analyze all repositories defined in prompts/repos.json"

# Parse positional arguments for configuration overrides
FORCE_FLAG=""
CLAUDE_MODEL=""
MAX_TOKENS=""
SLEEP_HOURS=""
CHUNK_SIZE=""

i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case $arg in
        force)
            echo "⚡ FORCE MODE ENABLED - all repositories will be investigated regardless of cache!"
            FORCE_FLAG="--force"
            ;;
        model)
            i=$((i + 1))
            if [ $i -le $# ]; then
                CLAUDE_MODEL="${!i}"
                echo "🔧 Claude model override: $CLAUDE_MODEL"
            else
                echo "❌ Error: 'model' requires a model name argument"
                exit 1
            fi
            ;;
        max-tokens)
            i=$((i + 1))
            if [ $i -le $# ]; then
                MAX_TOKENS="${!i}"
                echo "🔧 Max tokens override: $MAX_TOKENS"
            else
                echo "❌ Error: 'max-tokens' requires a number argument"
                exit 1
            fi
            ;;
        sleep-hours)
            i=$((i + 1))
            if [ $i -le $# ]; then
                SLEEP_HOURS="${!i}"
                echo "🔧 Sleep hours override: $SLEEP_HOURS"
            else
                echo "❌ Error: 'sleep-hours' requires a number argument"
                exit 1
            fi
            ;;
        chunk-size)
            i=$((i + 1))
            if [ $i -le $# ]; then
                CHUNK_SIZE="${!i}"
                echo "🔧 Chunk size override: $CHUNK_SIZE"
            else
                echo "❌ Error: 'chunk-size' requires a number argument"
                exit 1
            fi
            ;;
        dry-run)
            echo "🧪 DRY RUN MODE - will not execute full workflow"
            DRY_RUN=true
            ;;
        h)
            echo "📚 Local Investigation Workflow Help"
            echo ""
            echo "Usage: mise full [ARGUMENTS]"
            echo ""
            echo "Arguments (can be used in any order):"
            echo "  force                                    Forces investigation of all repos ignoring cache"
            echo "  model MODEL_NAME                         Override Claude model to use"
            echo "  max-tokens NUMBER                        Override max tokens (100-100000)"
            echo "  sleep-hours NUMBER                       Override hours between executions (0.01-168, supports decimals)"
            echo "  chunk-size NUMBER                        Override number of repos to process in parallel (1-20)"
            echo "  dry-run                                  Show what would be executed without running"
            echo "  h                                        Show this help message"
            echo ""
            echo "Valid Claude Models:"
            echo "  claude-3-5-sonnet-20241022              Latest Sonnet (recommended)"
            echo "  claude-3-5-haiku-20241022               Fast and cost-effective"
            echo "  claude-3-opus-20240229                  Most capable model"
            echo "  claude-3-sonnet-20240229                Balanced performance"
            echo "  claude-3-haiku-20240307                 Fastest model"
            echo "  claude-sonnet-4-20250514                Current default"
            echo ""
            echo "Examples:"
            echo "  mise full                               # Default settings"
            echo "  mise full force                         # Force investigation"
            echo "  mise full model claude-3-opus-20240229 max-tokens 8000"
            echo "  mise full sleep-hours 0.5               # 30 minutes between cycles"
            echo "  mise full chunk-size 4                  # Process 4 repos in parallel"
            echo "  mise full force sleep-hours 12 chunk-size 10  # Force with custom settings"
            echo "  mise full dry-run force model claude-3-haiku-20241022"
            echo ""
            echo "Sleep Hours Examples:"
            echo "  0.1     = 6 minutes     (testing)"
            echo "  0.25    = 15 minutes    (rapid iteration)"
            echo "  0.5     = 30 minutes    (development)"
            echo "  2       = 2 hours       (frequent updates)"
            echo "  6       = 6 hours       (default)"
            echo "  24      = 24 hours      (daily updates)"
            echo ""
            echo "Note: This runs locally with .env.local configuration"
            echo ""
            exit 0
            ;;
        *)
            echo "⚠️  Warning: Unknown argument '$arg' ignored"
            echo "💡 Use 'mise full h' to see available options"
            ;;
    esac
    i=$((i + 1))
done

# Build arguments for client
CLIENT_ARGS="$FORCE_FLAG"
if [[ -n "$CLAUDE_MODEL" ]]; then
    CLIENT_ARGS="$CLIENT_ARGS --claude-model=$CLAUDE_MODEL"
fi
if [[ -n "$MAX_TOKENS" ]]; then
    CLIENT_ARGS="$CLIENT_ARGS --max-tokens=$MAX_TOKENS"
fi
if [[ -n "$SLEEP_HOURS" ]]; then
    CLIENT_ARGS="$CLIENT_ARGS --sleep-hours=$SLEEP_HOURS"
fi
if [[ -n "$CHUNK_SIZE" ]]; then
    CLIENT_ARGS="$CLIENT_ARGS --chunk-size=$CHUNK_SIZE"
fi

# Check if dry-run mode before starting services
if [[ "$DRY_RUN" == "true" ]]; then
    echo "🧪 DRY RUN - Would execute: python -m client investigate $CLIENT_ARGS"
    echo "Final parsed values:"
    echo "  FORCE_FLAG: '$FORCE_FLAG'"
    echo "  CLAUDE_MODEL: '$CLAUDE_MODEL'"
    echo "  MAX_TOKENS: '$MAX_TOKENS'"
    echo "  SLEEP_HOURS: '$SLEEP_HOURS'"
    echo "  CHUNK_SIZE: '$CHUNK_SIZE'"
    echo "✅ DRY RUN completed - no services started"
    exit 0
fi

echo "The workflow will repeat every X hours until stopped (Ctrl+C)"
echo ""

# Ensure environment variables are exported for worker process
export PROMPT_CONTEXT_STORAGE=${PROMPT_CONTEXT_STORAGE:-file}
export SKIP_DYNAMODB_CHECK=${SKIP_DYNAMODB_CHECK:-true}
export LOCAL_TESTING=${LOCAL_TESTING:-true}

echo "🔧 Worker environment:"
echo "   PROMPT_CONTEXT_STORAGE=$PROMPT_CONTEXT_STORAGE"
echo "   SKIP_DYNAMODB_CHECK=$SKIP_DYNAMODB_CHECK"
echo "   LOCAL_TESTING=$LOCAL_TESTING"
echo ""

cd src && python -m investigate_worker &
WORKER_PID=$!
sleep 2

# Pass all arguments (including config overrides) to the client
cd src && python -m client investigate $CLIENT_ARGS

kill $WORKER_PID
kill $SERVER_PID

echo "✅ Investigation workflow stopped!"
echo "Check the temp/ directory for the generated {repository-name}-arch.md files." 