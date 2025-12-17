#!/bin/bash

echo "============================================"
echo "  Digital Signage Player"
echo "============================================"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    echo "Please install Python 3"
    exit 1
fi

# Check if pywebview is installed
if ! python3 -c "import webview" 2>/dev/null; then
    echo "Installing dependencies..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Linux detected - installing system dependencies..."
        if command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-gobject gtk3 webkit2gtk3
        fi
    fi
    
    pip3 install pywebview
fi

# Run the player
python3 player.py