#!/bin/bash

# List of target VMs
TARGETS=(
    "user@vm1.example.com"
    "user@vm2.example.com"
    # Add more targets as needed
)

SSH_KEY="~/.ssh/id_rsa"

# Deploy to each target
for target in "${TARGETS[@]}"; do
    echo "Deploying to $target..."
    ./deploy.sh "$target" "$SSH_KEY"
    echo "----------------------------------------"
done
