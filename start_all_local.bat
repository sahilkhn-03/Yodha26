@echo off
echo ====================================
echo Starting All Services Locally
echo ====================================
echo.

REM Kill any existing processes on required ports
echo 🧹 Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do taskkill /F /PID %%a >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo ====================================
echo Starting Services:
echo   🔧 Backend API (FastAPI)     - Port 8000
echo   💓 ECG Simulator (FastAPI)   - Port 8001
echo   🌐 Frontend (React + Vite)   - Port 5173
echo ====================================
echo.

REM Start Backend API (Port 8000)
echo 🚀 Starting Backend API on port 8000...
start "Backend API" cmd /k "cd /d d:\Yodha26\backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

REM Start ECG Simulator (Port 8001)
echo 💓 Starting ECG Simulator on port 8001...
start "ECG Simulator" cmd /k "cd /d d:\Yodha26\ecg-deployment && python heartbeat_sim.py"
timeout /t 3 /nobreak >nul

REM Start Frontend (Port 5173)
echo 🌐 Starting Frontend on port 5173...
start "Frontend" cmd /k "cd /d d:\Yodha26\opencvfront\project && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ====================================
echo ✅ All services started!
echo ====================================
echo.
echo Service URLs:
echo   📋 Backend API:      http://localhost:8000/docs
echo   💓 ECG Simulator:    http://localhost:8001/
echo   🌐 Frontend:         http://localhost:5173/
echo.
echo Press Ctrl+C to stop this script (services will keep running)
echo To stop all services, close their terminal windows or run stop_all_local.bat
echo.
pause
