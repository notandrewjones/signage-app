#!/bin/bash

echo "============================================"
echo "  Digital Signage Player"
echo "============================================"
echo

cd "$(dirname "$0")/.."

if [ -d "venv" ]; then
    source venv/bin/activate
else
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python not found."
        exit 1
    fi
fi

# Install pywebview with macOS dependencies if needed
python -c "import webview" 2>/dev/null || {
    echo "Installing pywebview..."
    pip install pywebview pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-WebKit
}

echo "Starting player..."
cd player
python player.py
