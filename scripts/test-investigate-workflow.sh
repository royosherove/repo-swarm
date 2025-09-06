#!/bin/bash

# Script to test the investigate repositories workflow

# Set environment variables for local testing
export PROMPT_CONTEXT_STORAGE=file
export SKIP_DYNAMODB_CHECK=true
export LOCAL_TESTING=true

echo "Starting Temporal worker in background (Local Mode)..."
python src/worker.py &
WORKER_PID=$!

# Give the worker time to start
sleep 2

echo "Running investigate repositories workflow..."
python src/client.py investigate

# Kill the worker
echo "Stopping worker..."
kill $WORKER_PID

echo "Test complete!" 