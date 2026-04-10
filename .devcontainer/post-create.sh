#!/usr/bin/env bash

# Install dependencies for the development container

# Note: This script must be fully self-contained, and must be able to be run on a clean Ubuntu image without any dependencies installed.
# It must also be fully idempotent, meaning that it can be run multiple times without causing any issues - this is useful for Claude and
# other agents, so they can add dependencies to this script, run the script, and if the container is torn down, the dependencies are preserved.

# First, update APT and make sure we're fully up to date
sudo apt-get update
sudo apt-get upgrade -y

# Install Claude Code
if ! command -v claude &> /dev/null; then
    echo "Installing Claude Code..."
    npm install -g @anthropic-ai/claude-code
else
    echo "Claude Code is already installed, skipping..."
fi

# Install Google Chrome (needed for Selenium e2e tests)
if ! command -v google-chrome &> /dev/null; then
    echo "Installing Google Chrome..."
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo dpkg -i /tmp/chrome.deb || true
    sudo apt-get install -f -y
    rm -f /tmp/chrome.deb
else
    echo "Google Chrome is already installed, skipping..."
fi

# Install backend Python dependencies
if [ -f "${containerWorkspaceFolder:-.}/backend/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r "${containerWorkspaceFolder:-.}/backend/requirements.txt"
fi

# Install waitress WSGI server (used in production Dockerfile, useful for local testing)
pip install waitress==3.0.2

# Install frontend Node dependencies
if [ -f "${containerWorkspaceFolder:-.}/frontend/package.json" ]; then
    echo "Installing Node dependencies..."
    cd "${containerWorkspaceFolder:-.}/frontend" && npm install
fi
