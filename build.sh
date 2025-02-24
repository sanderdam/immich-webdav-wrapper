#!/bin/bash

# Get the Docker registry from the first argument
REGISTRY="$1"
if [[ -n $REGISTRY ]]; then
  REGISTRY="${REGISTRY%/}/"
fi

echo "Used registry: ${REGISTRY}"

# Extract the version from version.py
VERSION=$(grep -oP '(?<=__version__ = ")[^"]*' version.py)
echo "Extracted version: ${VERSION}"

# Build the Docker image
echo "Building Docker image..."
docker compose -f docker-compose.build.yaml build

# Set Docker tags
IMAGE_ID=$(docker images -q | head -n 1)
IMAGE_REPOSITORY=$(docker images --format "{{.Repository}}" | head -n 1)

docker tag "$IMAGE_ID" "${REGISTRY}${IMAGE_REPOSITORY}:latest"
docker tag "$IMAGE_ID" "${REGISTRY}${IMAGE_REPOSITORY}:${VERSION}"
echo "Tags set: ${REGISTRY}${IMAGE_REPOSITORY}:latest and ${REGISTRY}${IMAGE_REPOSITORY}:${VERSION}"

# Push the Docker image
echo "Pushing Docker image..."
docker push "${REGISTRY}${IMAGE_REPOSITORY}:${VERSION}"
docker push "${REGISTRY}${IMAGE_REPOSITORY}:latest"