#!/bin/bash
# Script to set up and start the speech-agent on a DigitalOcean droplet

set -e  # Exit on error

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "=== Installing Docker ==="
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo "=== Installing Docker Compose ==="
    curl -L "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
fi

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "=== Installing Nginx ==="
    apt-get update
    apt-get install -y nginx
    systemctl enable nginx
    systemctl start nginx
fi

# Set up Nginx configuration
echo "=== Configuring Nginx ==="
cp nginx.conf /etc/nginx/sites-available/speech-agent
ln -sf /etc/nginx/sites-available/speech-agent /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Create cache directory if it doesn't exist
mkdir -p speech-agent/cache
chmod -R 777 speech-agent/cache

# Start the services
echo "=== Starting services ==="
docker-compose down || true  # Stop any existing containers
docker-compose up -d --build

echo "=== Setup Complete ==="
echo "The speech agent is now running!"
