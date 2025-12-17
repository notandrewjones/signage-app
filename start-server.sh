#!/bin/bash

echo "============================================"
echo "  Digital Signage Server"
echo "============================================"
echo

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

source venv/bin/activate

mkdir -p server/uploads/content
mkdir -p server/uploads/logos
mkdir -p server/uploads/backgrounds

echo "Starting server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo "============================================"
echo

python server/main.py
