#!/bin/bash

echo "============================================"
echo "  Digital Signage Web UI"
echo "============================================"
echo

if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed."
    echo "Install from https://nodejs.org or via Homebrew:"
    echo "  brew install node"
    exit 1
fi

cd "$(dirname "$0")/web-ui"

if [ ! -d "node_modules" ]; then
    echo "Installing UI dependencies..."
    npm install
fi

echo "Starting Web UI on http://localhost:5173"
echo "Make sure the server is running first!"
echo "Press Ctrl+C to stop"
echo "============================================"
echo

npm run dev
