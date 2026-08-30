@echo off
REM =========================================================
REM RailMadat — Start both frontend and backend servers
REM =========================================================
REM Usage: start.bat
REM Frontend: http://localhost:3000
REM Backend:  http://localhost:8000
REM API Docs: http://localhost:8000/docs
REM =========================================================

echo Starting RailMadat...

REM Check if backend .env exists
if not exist "backend\.env" (
    echo Warning: backend\.env not found. Copy .env.example to backend\.env
)

REM Start backend in new window
echo Starting backend server on port 8000...
start "RailMadat Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 2 /nobreak > nul

REM Start frontend in new window
echo Starting frontend server on port 3000...
start "RailMadat Frontend" cmd /k "cd railmadat-frontend && python -m http.server 3000"

echo.
echo RailMadat is running!
echo.
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo Close the command windows to stop the servers.
