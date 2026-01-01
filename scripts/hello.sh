#!/bin/bash

echo "Starting Temporal server..."
mise run dev-server &
SERVER_PID=$!
sleep 5

echo "Installing dependencies..."
uv sync

echo "Starting worker (investigate)..."
cd src && python -m investigate_worker &
WORKER_PID=$!
sleep 3

echo "Running workflow client (investigate)..."
cd src && python -m client investigate

echo "Cleaning up..."
kill $WORKER_PID
kill $SERVER_PID 