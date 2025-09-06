#!/bin/bash

# Script to run the single repository investigation workflow with optional configuration overrides
# Usage: ./investigate-single.sh REPO_NAME_OR_URL [force] [model MODEL] [max-tokens NUM] [type TYPE]

# Check if repository argument is provided or if help is requested
if [ $# -eq 0 ]; then
    echo "❌ Error: Repository name or URL is required"
    echo "💡 Use 'mise investigate-single h' to see usage information"
    exit 1
fi

# Check if help is requested as first argument
if [ "$1" = "h" ]; then
    echo "📚 Single Repository Investigation Help"
    echo ""
    echo "Usage: mise investigate-single REPO_NAME_OR_URL [ARGUMENTS]"
    echo ""
    echo "Repository Argument:"
    echo "  REPO_NAME_OR_URL                         Repository name from repos.json or direct GitHub URL"
    echo ""
    echo "Arguments (can be used in any order):"
    echo "  force                                    Forces investigation ignoring cache"
    echo "  force-section SECTION_NAME               Force re-execution of specific section"
    echo "  model MODEL_NAME                         Override Claude model to use"
    echo "  max-tokens NUMBER                        Override max tokens (100-100000)"
    echo "  type TYPE                                Override repository type"
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
    echo "Valid Repository Types:"
    echo "  generic                                  Generic repository (default)"
    echo "  backend                                  Backend service"
    echo "  frontend                                 Frontend application"
    echo "  mobile                                   Mobile application"
    echo "  infra-as-code                           Infrastructure as code"
    echo "  libraries                               Library/package"
    echo ""
    echo "Examples:"
    echo "  mise investigate-single is-odd                           # Investigate 'is-odd' from repos.json"
    echo "  mise investigate-single https://github.com/user/repo    # Investigate direct URL"
    echo "  mise investigate-single is-odd force                     # Force investigation"
    echo "  mise investigate-single is-odd force-section monitoring  # Force only monitoring section"
    echo "  mise investigate-single is-odd model claude-3-opus-20240229 max-tokens 8000"
    echo "  mise investigate-single is-odd type libraries              # Override repository type"
    echo "  mise investigate-single is-odd dry-run force model claude-3-haiku-20241022"
    echo ""
    exit 0
fi

REPO_ARG="$1"
shift  # Remove first argument so we can process the rest

echo "🔍 Starting single repository investigation..."
echo "Repository: $REPO_ARG"
echo "Using Temporal configuration from .env file..."

# Parse positional arguments for configuration overrides
FORCE_FLAG=""
CLAUDE_MODEL=""
MAX_TOKENS=""
REPO_TYPE=""
FORCE_SECTION=""

i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case $arg in
        force)
            echo "🚀 FORCE MODE ENABLED!"
            echo "⚡ Repository will be investigated regardless of cache!"
            FORCE_FLAG="--force"
            ;;
        force-section)
            i=$((i + 1))
            if [ $i -le $# ]; then
                FORCE_SECTION="${!i}"
                echo "🔧 Force section override: $FORCE_SECTION"
            else
                echo "❌ Error: 'force-section' requires a section name argument"
                exit 1
            fi
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
        type)
            i=$((i + 1))
            if [ $i -le $# ]; then
                REPO_TYPE="${!i}"
                echo "🔧 Repository type override: $REPO_TYPE"
            else
                echo "❌ Error: 'type' requires a type argument"
                exit 1
            fi
            ;;
        dry-run)
            echo "🧪 DRY RUN MODE - will not execute investigation"
            DRY_RUN=true
            ;;
        h)
            echo "💡 Use 'mise investigate-single h' (as first argument) to see help information"
            ;;
        *)
            echo "⚠️  Warning: Unknown argument '$arg' ignored"
            echo "💡 Use 'mise investigate-single h' to see available options"
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
if [[ -n "$REPO_TYPE" ]]; then
    CLIENT_ARGS="$CLIENT_ARGS --repo-type=$REPO_TYPE"
fi
if [[ -n "$FORCE_SECTION" ]]; then
    CLIENT_ARGS="$CLIENT_ARGS --force-section=$FORCE_SECTION"
fi

echo ""
if [[ "$DRY_RUN" == "true" ]]; then
    echo "🧪 DRY RUN - Would execute: python -m client investigate-single \"$REPO_ARG\" $CLIENT_ARGS"
    echo "Final parsed values:"
    echo "  REPO_ARG: '$REPO_ARG'"
    echo "  FORCE_FLAG: '$FORCE_FLAG'"
    echo "  FORCE_SECTION: '$FORCE_SECTION'"
    echo "  CLAUDE_MODEL: '$CLAUDE_MODEL'"
    echo "  MAX_TOKENS: '$MAX_TOKENS'"
    echo "  REPO_TYPE: '$REPO_TYPE'"
    EXIT_CODE=0
else
    cd src && mise exec python@3.12 -- python -m client investigate-single "$REPO_ARG" $CLIENT_ARGS
    EXIT_CODE=$?
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Single repository investigation completed!"
else
    echo "❌ Failed to investigate repository"
    exit $EXIT_CODE
fi
