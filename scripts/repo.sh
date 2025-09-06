#!/bin/bash

echo "Setting up Claude Investigator..."
uv sync

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable is not set"
    echo "Please set your Claude API key:"
    echo "export ANTHROPIC_API_KEY='your-api-key-here'"
    exit 1
fi

echo "🔍 Investigating repository with Claude Investigator..."
echo "Repository: https://github.com/leachim6/hello-world"
echo "This will analyze a simple hello-world repository (fast and small)..."
echo "Logging level: INFO (use 'mise repo-debug' for detailed logging)"

cd src/investigator
python investigator.py https://github.com/leachim6/hello-world

echo "✅ Investigation complete!"
echo "Check the generated {repository-name}-arch.md file in the temporary directory for the analysis." 