#!/bin/bash
# Script to build and deploy the RunPod TTS service

set -e  # Exit on error

# Configuration
DOCKER_IMAGE="your-dockerhub-username/runpod-tts-service:latest"
RUNPOD_API_KEY="${RUNPOD_API_KEY:-}"
SERVICE_NAME="tts-service"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if RunPod CLI is installed
if ! command -v runpodctl &> /dev/null; then
    echo "Error: RunPod CLI is not installed. Please install it first."
    echo "Visit: https://github.com/runpod/runpodctl for installation instructions."
    exit 1
fi

# Check for API key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "Error: RUNPOD_API_KEY environment variable is not set."
    echo "Please set it with: export RUNPOD_API_KEY=your-api-key"
    exit 1
fi

echo "=== Building Docker image ==="
cd "$(dirname "$0")/.."
docker build -t "$DOCKER_IMAGE" ./runpod-tts-service

echo "=== Pushing Docker image to Docker Hub ==="
docker push "$DOCKER_IMAGE"

echo "=== Deploying to RunPod Serverless ==="
# Check if the endpoint already exists
ENDPOINT_ID=$(runpodctl endpoint list --template-only | grep "$SERVICE_NAME" | awk '{print $1}')

if [ -n "$ENDPOINT_ID" ]; then
    echo "Updating existing endpoint: $ENDPOINT_ID"
    runpodctl endpoint update \
        --id "$ENDPOINT_ID" \
        --image "$DOCKER_IMAGE" \
        --gpu "NVIDIA RTX A4000" \
        --concurrency 1 \
        --idle-timeout 5
else
    echo "Creating new endpoint"
    runpodctl endpoint create \
        --name "$SERVICE_NAME" \
        --image "$DOCKER_IMAGE" \
        --gpu "NVIDIA RTX A4000" \
        --concurrency 1 \
        --idle-timeout 5
fi

echo "=== Deployment Complete ==="
echo "To get your endpoint URL, run: runpodctl endpoint list"
echo "Remember to update your DigitalOcean server with the new endpoint URL and API key."
