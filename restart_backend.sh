#!/bin/bash

echo "Restarting Backend Service"
echo "=========================="
echo ""

# Find and kill existing Flask processes on port 5000
echo "Stopping existing backend processes..."
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Wait a moment for port to be freed
sleep 2

# Check if port is free
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Port 5000 is still in use. Please manually stop it:"
    echo "   kill -9 \$(lsof -t -i:5000)"
    exit 1
fi

echo "✅ Port 5000 is free"
echo ""

# Start the backend
echo "Starting backend API..."
cd /Users/dponnappan/initiatives/2025/agentic-ai/tools/sam-search
python app.py