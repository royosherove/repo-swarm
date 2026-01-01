#!/bin/bash

uv sync

# Start Temporal server in background
echo "Starting Temporal server..."
mise run dev-server &
SERVER_PID=$!
sleep 5

cd src && python -m investigate_worker &
WORKER_PID=$!
sleep 2

cd src && python -m client investigate

kill $WORKER_PID
kill $SERVER_PID