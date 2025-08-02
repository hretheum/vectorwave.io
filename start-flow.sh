#!/bin/bash

# Start script for AI Kolegium with CrewAI Flow

echo "🚀 Starting AI Kolegium Redakcyjne with CrewAI Flow..."
echo ""

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start backend with Flow
echo "📡 Starting backend server with CrewAI Flow..."
# Check for Python virtual environment
if [ -d "ai_publishing_cycle/.venv" ]; then
    echo "🐍 Activating backend virtual environment..."
    source ai_publishing_cycle/.venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🐍 Activating global virtual environment..."
    source .venv/bin/activate
fi

cd ai_publishing_cycle && USE_CREWAI_FLOW=true python src/ai_publishing_cycle/copilot_backend.py &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend..."
# We need to go back to the main kolegium directory first
cd ..
if [ -d "vector-wave-ui" ]; then
    cd vector-wave-ui
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    npm run dev &
    FRONTEND_PID=$!
    cd ..
else
    echo "❌ Frontend directory not found!"
    echo "   Current directory: $(pwd)"
    echo "   Looking for: ./vector-wave-ui"
fi

echo ""
echo "✅ Services started!"
echo "   Backend (Flow): http://localhost:8001"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait