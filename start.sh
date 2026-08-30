#!/bin/bash
# =========================================================
# RailMadat — Start both frontend and backend servers
# =========================================================
# Usage: ./start.sh
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
# =========================================================

echo "🚂 Starting RailMadat..."

# Check if backend .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env not found. Copy .env.example to backend/.env"
fi

# Start backend in background
echo "🔧 Starting backend server on port 8000..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend in background
echo "🌐 Starting frontend server on port 3000..."
cd railmadat-frontend
python -m http.server 3000 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ RailMadat is running!"
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Trap to kill both processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Stopped"
}

trap cleanup EXIT INT TERM

# Wait for either process to exit
wait
