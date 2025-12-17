#!/bin/bash

echo "============================================"
echo "  Digital Signage System"
echo "============================================"
echo

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup first..."
    ./setup.sh
fi

if ! command -v node &> /dev/null; then
    echo "WARNING: Node.js not installed. Starting server only."
    ./start-server.sh
    exit
fi

echo "Starting server and UI..."

# Start server in background
./start-server.sh &
SERVER_PID=$!

sleep 3

# Start UI in background
./start-ui.sh &
UI_PID=$!

echo
echo "============================================"
echo "Server: http://localhost:8000"
echo "Web UI: http://localhost:5173"
echo "============================================"
echo "Press Ctrl+C to stop both services"

# Open browser
if command -v open &> /dev/null; then
    sleep 2
    open http://localhost:5173
fi

# Wait and cleanup on exit
trap "kill $SERVER_PID $UI_PID 2>/dev/null" EXIT
wait
