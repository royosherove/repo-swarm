#!/bin/bash

echo "📋 Available repositories for testing:"
echo "========================================"
python3 -c "
import json
try:
    with open('prompts/repos.json') as f:
        data = json.load(f)
    print(f\"Default: {data['default']}\")
    print()
    print(\"Named repositories:\")
    for name, repo in data['repositories'].items():
        print(f\"  {name}: {repo['description']}\")
        print(f\"    URL: {repo['url']}\")
        print()
except Exception as e:
    print(f\"Error reading repos.json: {e}\")
"
echo "========================================"
echo "Usage: mise test [repository_name]"
echo "Examples:"
echo "  mise test                    # Use default"
echo "  mise test hello-world        # Use hello-world"
echo "  mise test https://github.com/user/repo  # Use direct URL" 