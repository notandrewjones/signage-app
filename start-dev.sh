#!/bin/bash

# Digital Signage System - Development Startup Script

echo "╔══════════════════════════════════════════╗"
echo "║     Digital Signage System               ║"
echo "║     Development Environment              ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "server/main.py" ]; then
    echo -e "${RED}Error: Run this script from the signage-system directory${NC}"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    kill $SERVER_PID 2>/dev/null
    kill $UI_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Create uploads directories
mkdir -p uploads/content uploads/logos uploads/backgrounds

# Check Python dependencies
echo -e "${YELLOW}Checking server dependencies...${NC}"
cd server
if ! pip show fastapi > /dev/null 2>&1; then
    echo "Installing server dependencies..."
    pip install -r requirements.txt
fi
cd ..

# Check Node dependencies
echo -e "${YELLOW}Checking UI dependencies...${NC}"
cd web-ui
if [ ! -d "node_modules" ]; then
    echo "Installing UI dependencies..."
    npm install
fi
cd ..

# Start the server
echo ""
echo -e "${GREEN}Starting API server on http://localhost:8000${NC}"
cd server
python main.py &
SERVER_PID=$!
cd ..

# Wait for server to start
sleep 2

# Start the UI
echo -e "${GREEN}Starting Web UI on http://localhost:5173${NC}"
cd web-ui
npm run dev &
UI_PID=$!
cd ..

echo ""
echo "════════════════════════════════════════════"
echo -e "${GREEN}Services running:${NC}"
echo "  • API Server: http://localhost:8000"
echo "  • Web UI:     http://localhost:5173"
echo "  • API Docs:   http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo "════════════════════════════════════════════"

# Wait for processes
wait
