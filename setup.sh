#!/bin/bash

echo "============================================"
echo "  Digital Signage System - Setup (macOS)"
echo "============================================"
echo

cd "$(dirname "$0")"

# Check for Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "ERROR: Python not found. Install from https://python.org or via Homebrew:"
    echo "  brew install python"
    exit 1
fi

echo "Using $($PYTHON --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
echo "Installing server dependencies..."
pip install -r server/requirements.txt

# Create upload directories
mkdir -p server/uploads/content
mkdir -p server/uploads/logos
mkdir -p server/uploads/backgrounds

echo
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo
echo "Run './start-server.sh' to start the server"
echo "Run './start-ui.sh' to start the web interface"
echo "Run './player/run-player.sh' to start the player"
