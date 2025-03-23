#!/bin/bash

# Variables
APP_DIR="/opt/speech-agent"
REPO_URL="https://github.com/Jblast94/-hybrid-text-to-speech.git"
DOCKER_HUB_USERNAME="jimmynap"
IMAGE_NAME="grok-tts"
IMAGE_TAG="latest"

# Check if target host is provided
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <target_host> [ssh_key_path]"
    echo "Example: ./deploy.sh user@192.168.1.100 ~/.ssh/id_rsa"
    exit 1
fi

TARGET_HOST=$1
SSH_KEY=${2:-"~/.ssh/id_rsa"}
SSH_CMD="ssh -i $SSH_KEY $TARGET_HOST"

# Function to run remote commands
remote_exec() {
    echo "Executing on $TARGET_HOST: $1"
    $SSH_CMD "$1"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to execute '$1' on $TARGET_HOST"
        exit 1
    fi
}

# Copy deployment files to remote host
echo "Copying deployment files to $TARGET_HOST..."
scp -i $SSH_KEY -r ../Dockerfile ../docker-compose.yml $TARGET_HOST:$APP_DIR/

# Install dependencies on remote host
remote_exec "apt-get update && apt-get install -y docker-compose-plugin git curl"

# Login to Docker Hub on remote host
echo "Logging into Docker Hub on $TARGET_HOST..."
remote_exec "docker login --username $DOCKER_HUB_USERNAME"

# Clone/update repository on remote host
remote_exec "
if [ -d '$APP_DIR' ]; then
    cd $APP_DIR && git pull
else
    git clone $REPO_URL $APP_DIR
fi"

# Build and deploy on remote host
remote_exec "cd $APP_DIR && docker compose pull && docker compose up -d --build"

# Display results
echo "Deployment completed successfully on $TARGET_HOST!"
IP=$($SSH_CMD "curl -s ifconfig.me")
echo "Application running at http://$IP"
