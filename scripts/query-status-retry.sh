#!/bin/bash

# Query the Temporal workflow's get_status via CLI with retry logic
# Usage: ./query-status-retry.sh <workflow_id>

if [ -z "$1" ]; then
    echo "Usage: $0 <workflow_id>"
    echo "Example: $0 investigate-repos-workflow"
    exit 1
fi

WORKFLOW_ID="$1"
TEMPORAL_ADDRESS="${TEMPORAL_ADDRESS:-localhost:7233}"
TEMPORAL_NAMESPACE="${TEMPORAL_NAMESPACE:-default}"
MAX_RETRIES=2
RETRY_DELAY=1

echo "Querying workflow: $WORKFLOW_ID"
echo "Using address: $TEMPORAL_ADDRESS"
echo "Using namespace: $TEMPORAL_NAMESPACE"
echo ""

# Try the query with retry logic
for i in $(seq 1 $MAX_RETRIES); do
    echo "Attempt $i of $MAX_RETRIES..."
    
    # Run the query with a shorter initial timeout
    if temporal workflow query \
        --workflow-id "$WORKFLOW_ID" \
        --name get_status \
        --address "$TEMPORAL_ADDRESS" \
        --namespace "$TEMPORAL_NAMESPACE" \
        --command-timeout 5s 2>/dev/null; then
        # Success - exit with success code
        exit 0
    else
        # Failed - check if we should retry
        if [ $i -lt $MAX_RETRIES ]; then
            echo "Query timed out, retrying in $RETRY_DELAY second(s)..."
            sleep $RETRY_DELAY
        else
            echo "Query failed after $MAX_RETRIES attempts"
            exit 1
        fi
    fi
done
