#!/bin/bash

# Automated Sales Forecasting System - Run Script
# This script starts both the backend and frontend servers

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}➜${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

echo "=================================================="
echo "Automated Sales Forecasting System"
echo "=================================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create a .env file with your ANTHROPIC_API_KEY"
    echo "You can use .env.example as a template:"
    echo "  cp .env.example .env"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create log directory
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $(jobs -p) 2>/dev/null
    print_success "Servers stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
print_info "Starting backend server..."
source venv/bin/activate
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    print_success "Backend server started on http://localhost:8000"
else
    echo "❌ Failed to start backend server"
    echo "Check logs/backend.log for details"
    exit 1
fi

# Start frontend server
print_info "Starting frontend server..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    print_success "Frontend server started on http://localhost:3000"
else
    echo "❌ Failed to start frontend server"
    echo "Check logs/frontend.log for details"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=================================================="
echo "✓ System is running!"
echo "=================================================="
echo ""
echo "  🌐 Frontend: http://localhost:3000"
echo "  🔧 Backend:  http://localhost:8000"
echo "  📊 API Docs: http://localhost:8000/docs"
echo ""
echo "  📝 Logs:"
echo "     Backend:  logs/backend.log"
echo "     Frontend: logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
