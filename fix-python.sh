#!/bin/bash

echo "Fixing Python dependencies..."

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r server/requirements.txt

echo "Done! Try running the player again."
