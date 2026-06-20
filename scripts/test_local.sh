#!/bin/bash
# Local testing script - Simulates GitLab CI environment

set -e

SCRIPT_DIR=$(pwd)
REPO_ROOT="$HOME/repos/sandbox/themis-repos/themis"
ENV_FILE="$REPO_ROOT/env_files/.env.test"

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

# Anchor the review to a real checkout of the consumer repo, exactly as GitLab
# does via CI_PROJECT_DIR. Defaults to the sibling themis-example checkout; the
# engine still runs from the themis repo (its own venv) but reads .themis-ai/
# config, rules and architecture from here — no copying required.
export CI_PROJECT_DIR="${TARGET_REPO:-${CI_PROJECT_DIR:-$HOME/repos/sandbox/themis-repos/themis-example}}"

if [[ ! -f "$CI_PROJECT_DIR/.themis-ai/config.yaml" ]]; then
    echo "❌ Error: no .themis-ai/config.yaml under CI_PROJECT_DIR=$CI_PROJECT_DIR"
    echo "   Set TARGET_REPO to a checkout of the consumer repo under review."
    exit 1
fi

echo "🚀 Running engine with simulated GitLab CI environment..."
echo "   Project: $CI_PROJECT_NAMESPACE/$CI_PROJECT_NAME (ID: $CI_PROJECT_ID)"
echo "   Repo under review: $CI_PROJECT_DIR"
echo "   MR ID: $CI_MERGE_REQUEST_IID"
echo "   Branch: $CI_MERGE_REQUEST_SOURCE_BRANCH → $CI_MERGE_REQUEST_TARGET_BRANCH"
echo ""

# Call the engine via task
task run-engine
