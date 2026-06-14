#!/bin/bash
# Local testing script - Simulates GitLab CI environment

set -e

SCRIPT_DIR=$(pwd)
ENV_FILE="$SCRIPT_DIR/.env.test"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ Error: .env.test not found"
    echo ""
    echo "To get started, copy the example file and fill in your values:"
    echo "  cp .env.test.example .env.test"
    echo ""
    echo "Then update .env.test with your GitLab token and project details."
    exit 1
fi

# Source the test environment
set -a
source "$ENV_FILE"
set +a

echo "🚀 Running engine with simulated GitLab CI environment..."
echo "   Project: $CI_PROJECT_NAMESPACE/$CI_PROJECT_NAME (ID: $CI_PROJECT_ID)"
echo "   MR ID: $CI_MERGE_REQUEST_IID"
echo "   Branch: $CI_MERGE_REQUEST_SOURCE_BRANCH → $CI_MERGE_REQUEST_TARGET_BRANCH"
echo ""

# Call the engine via task
task run-engine
