#!/bin/bash

# Usage:
# With version tag
# ./scripts/push_image.sh v1.0.0
# With default -dev suffix
# ./scripts/push_image.sh

set -e

IMAGE="rafalstepien/themis"
TAG="${1:-dev}"
PLATFORMS="linux/amd64,linux/arm64"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if ! docker buildx inspect themis-builder &>/dev/null; then
    docker buildx create --name themis-builder --use
else
    docker buildx use themis-builder
fi

echo "Building and pushing $IMAGE:$TAG for $PLATFORMS..."
docker buildx build \
    --platform "$PLATFORMS" \
    --tag "$IMAGE:$TAG" \
    --push \
    .

echo "Done: $IMAGE:$TAG"
