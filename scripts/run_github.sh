set -e

export SETTINGS_DIR_PATH=$1
ENV_FILE="$SETTINGS_DIR_PATH/.env"

echo $ENV_FILE

if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ Error: .env not found"
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

echo "🚀 Running engine with simulated GitHub CI environment..."
echo ""


uv run main.py github
