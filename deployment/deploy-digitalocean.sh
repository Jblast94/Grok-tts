#!/bin/bash
# Script to deploy the speech-agent web server to DigitalOcean

set -e  # Exit on error

# Configuration
SSH_USER="root"
SSH_HOST=""  # Your DigitalOcean droplet IP
PROJECT_DIR="/opt/speech-agent"
ENV_FILE=".env"

# Check if SSH host is provided
if [ -z "$SSH_HOST" ]; then
    echo "Error: Please edit this script and set the SSH_HOST variable to your DigitalOcean droplet IP."
    exit 1
fi

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating sample .env file..."
    cat > "$ENV_FILE" << EOL
# RunPod API configuration
RUNPOD_API_ENDPOINT=https://api.runpod.ai/v2/your-endpoint-id/run
RUNPOD_API_KEY=your-runpod-api-key

# Cache configuration
CACHE_EXPIRATION_SECONDS=86400
EOL
    echo "Please edit the $ENV_FILE file with your actual RunPod API endpoint and key."
    echo "Then run this script again."
    exit 1
fi

echo "=== Preparing for deployment ==="
echo "Deploying to $SSH_USER@$SSH_HOST..."

# Create a temporary deployment package
DEPLOY_TMP=$(mktemp -d)
echo "Creating deployment package in $DEPLOY_TMP..."

# Copy necessary files
cp -r speech-agent "$DEPLOY_TMP/"
cp docker-compose.yml "$DEPLOY_TMP/"
cp "$ENV_FILE" "$DEPLOY_TMP/"
cp deployment/nginx.conf "$DEPLOY_TMP/"
cp deployment/start.sh "$DEPLOY_TMP/"

# Make scripts executable
chmod +x "$DEPLOY_TMP/start.sh"

echo "=== Setting up the server ==="
# Create project directory on the server
ssh "$SSH_USER@$SSH_HOST" "mkdir -p $PROJECT_DIR"

# Copy files to the server
echo "Copying files to the server..."
scp -r "$DEPLOY_TMP"/* "$SSH_USER@$SSH_HOST:$PROJECT_DIR/"

# Set up the server
echo "Setting up the server..."
ssh "$SSH_USER@$SSH_HOST" "cd $PROJECT_DIR && bash start.sh"

# Clean up
rm -rf "$DEPLOY_TMP"

echo "=== Deployment Complete ==="
echo "Your speech agent is now deployed to DigitalOcean!"
echo "You can access it at: http://$SSH_HOST/"
