set -e

SETTINGS_DIR_PATH=$1
ENV_FILE="$SETTINGS_DIR_PATH/.env"

echo $ENV_FILE

if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ Error: .env.test not found"
    echo ""
    echo "To get started, copy the example file and fill in your values:"
    echo "  cp .env.test.example .env.test"
    echo ""
    echo "Then update .env.test with your GitLab token and project details."
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [[ ! -f "$SETTINGS_DIR_PATH/.themis-ai/config.yaml" ]]; then
    echo "❌ Error: no .themis-ai/config.yaml under SETTINGS_DIR_PATH=$SETTINGS_DIR_PATH"
    echo "   Set TARGET_REPO to a checkout of the consumer repo under review."
    exit 1
fi

echo "🚀 Running engine with simulated GitLab CI environment..."
echo "   Project: $CI_PROJECT_NAMESPACE/$CI_PROJECT_NAME (ID: $CI_PROJECT_ID)"
echo "   Repo under review: $SETTINGS_DIR_PATH"
echo "   MR ID: $CI_MERGE_REQUEST_IID"
echo "   Branch: $CI_MERGE_REQUEST_SOURCE_BRANCH → $CI_MERGE_REQUEST_TARGET_BRANCH"
echo ""


uv run main.py github
