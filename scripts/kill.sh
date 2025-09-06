#!/bin/bash

echo "Killing Temporal servers and workers..."
lsof -ti:7233 | xargs kill -9 2>/dev/null || echo "No Temporal server found on port 7233"
lsof -ti:8233 | xargs kill -9 2>/dev/null || echo "No Temporal UI found on port 8233"
pkill -f "python.*worker" 2>/dev/null || echo "No Python workers found"
pkill -f "temporal server" 2>/dev/null || echo "No Temporal server processes found"
echo "Cleanup complete!" 