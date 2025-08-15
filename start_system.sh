#!/bin/bash

echo "Starting SAM.gov Opportunity Analysis System"
echo "============================================"
echo ""

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use. Please stop the existing process first."
        echo "   To find what's using port $1: lsof -i :$1"
        echo "   To kill it: kill -9 \$(lsof -t -i:$1)"
        return 1
    fi
    return 0
}

# Check if ports are available
echo "Checking ports..."
check_port 5000
backend_check=$?
check_port 3000
frontend_check=$?

if [ $backend_check -ne 0 ] || [ $frontend_check -ne 0 ]; then
    echo ""
    echo "Please free up the ports and try again."
    exit 1
fi

# Start backend
echo ""
echo "Starting Backend API on port 5000..."
python app.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Check if backend is running
if ! curl -s http://localhost:5000/ > /dev/null; then
    echo "❌ Backend failed to start"
    exit 1
fi

echo "✅ Backend is running at http://localhost:5000"
echo ""

# Start frontend
echo "Starting Frontend on port 3000..."
echo "Note: If node_modules doesn't exist, this will install dependencies first"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo ""
echo "============================================"
echo "✅ System is starting!"
echo ""
echo "Backend API: http://localhost:5000"
echo "Frontend UI: http://localhost:3000 (starting...)"
echo ""
echo "Press Ctrl+C to stop both services"
echo "============================================"
echo ""

# Start frontend (this will block and keep both running)
npm start

# When npm start is interrupted, kill the backend too
kill $BACKEND_PID 2>/dev/null