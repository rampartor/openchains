#!/bin/bash

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Function to handle cleanup on exit
cleanup() {
  echo "Shutting down services..."
  if [ ! -z "$BACKEND_PID" ]; then
    kill $BACKEND_PID
  fi
  if [ ! -z "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID
  fi
  exit 0
}

# Install dependencies if needed
echo "Installing backend dependencies..."
poetry install

# Start frontend development server
echo "Starting Vite frontend development server..."
cd frontend || exit
yarn install
yarn dev &
FRONTEND_PID=$!
cd ..

echo "Frontend started at http://localhost:5173"

# Set up trap to handle SIGINT (Ctrl+C)
trap cleanup SIGINT SIGTERM

# Start the backend application
echo "Starting backend API server..."
poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Backend API running at http://localhost:8000"
echo "API Documentation available at http://localhost:8000/docs"
echo "Press Ctrl+C to stop all services"

# Wait for processes to finish
wait
