#!/bin/bash

# Script to run the investigate workflow with optional configuration overrides
# Usage: ./investigate.sh [force] [model MODEL] [max-tokens NUM] [sleep-hours NUM]

echo "🔄 Starting investigation workflow on deployed worker..."
echo "Using Temporal configuration from .env file..."

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
            echo "🚀 FORCE MODE ENABLED!"
            echo "⚡ All repositories will be investigated regardless of cache on first run!"
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
            echo "📚 Investigation Workflow Help"
            echo ""
            echo "Usage: mise investigate [ARGUMENTS]"
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
            echo "  mise investigate                        # Default settings"
            echo "  mise investigate force                  # Force investigation"
            echo "  mise investigate model claude-3-opus-20240229 max-tokens 8000"
            echo "  mise investigate sleep-hours 0.5        # 30 minutes between cycles"
            echo "  mise investigate chunk-size 4           # Process 4 repos in parallel"
            echo "  mise investigate force sleep-hours 24 chunk-size 10  # Force with custom settings"
            echo "  mise investigate dry-run force model claude-3-haiku-20241022"
            echo ""
            echo "Sleep Hours Examples:"
            echo "  0.1     = 6 minutes     (testing)"
            echo "  0.25    = 15 minutes    (rapid iteration)"
            echo "  0.5     = 30 minutes    (development)"
            echo "  2       = 2 hours       (frequent updates)"
            echo "  6       = 6 hours       (default)"
            echo "  24      = 24 hours      (daily updates)"
            echo ""
            exit 0
            ;;
        *)
            echo "⚠️  Warning: Unknown argument '$arg' ignored"
            echo "💡 Use 'mise investigate h' to see available options"
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

echo ""
if [[ "$DRY_RUN" == "true" ]]; then
    echo "🧪 DRY RUN - Would execute: python -m client investigate $CLIENT_ARGS"
    echo "Final parsed values:"
    echo "  FORCE_FLAG: '$FORCE_FLAG'"
    echo "  CLAUDE_MODEL: '$CLAUDE_MODEL'"
    echo "  MAX_TOKENS: '$MAX_TOKENS'"
    echo "  SLEEP_HOURS: '$SLEEP_HOURS'"
    echo "  CHUNK_SIZE: '$CHUNK_SIZE'"
    EXIT_CODE=0
else
    cd src && mise exec python@3.12 -- python -m client investigate $CLIENT_ARGS
    EXIT_CODE=$?
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Investigation workflow started!"
else
    echo "❌ Failed to start investigation workflow"
    exit $EXIT_CODE
fi
