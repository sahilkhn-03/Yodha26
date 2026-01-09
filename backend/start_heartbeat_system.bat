@echo off
REM Quick Start Script for Heartbeat Integration System
REM This starts both services needed for the complete system

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  NeuroBalance AI - Heartbeat Integration System          ║
echo ║  Starting both services...                                ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if httpx is installed
python -c "import httpx" 2>nul
if errorlevel 1 (
    echo ⚠️  httpx not installed. Installing...
    pip install httpx
)

echo.
echo 📋 INSTRUCTIONS:
echo   1. Heartbeat Simulation will start on port 8001
echo   2. Main FastAPI will start on port 8000
echo   3. Open http://localhost:8000/docs for API documentation
echo   4. Open http://localhost:8001 for heartbeat monitor
echo.
echo 🔄 Starting services...
echo.

REM Start heartbeat simulation in new window
start "Heartbeat Simulation (Port 8001)" cmd /k "cd /d %~dp0 && uvicorn heartbeat_sim:app --port 8001 --reload"

REM Wait a bit for first service to start
timeout /t 3 /nobreak >nul

REM Start main API in new window
start "Main FastAPI (Port 8000)" cmd /k "cd /d %~dp0 && uvicorn main:app --port 8000 --reload"

REM Wait for services to start
timeout /t 5 /nobreak >nul

echo.
echo ✅ Services starting in separate windows!
echo.
echo 🌐 URLs:
echo   - Main API Docs:      http://localhost:8000/docs
echo   - Heartbeat Monitor:  http://localhost:8001
echo   - WebSocket Stream:   ws://localhost:8000/ws/simulation
echo.
echo 📝 To test the system:
echo   python test_heartbeat_integration.py
echo.
echo Press any key to start the simulation automatically...
pause >nul

REM Start the simulation
curl -X POST http://localhost:8000/heartbeat/start >nul 2>&1

echo.
echo ✅ Heartbeat simulation started!
echo.
echo 📊 Check heart rate:
echo   curl http://localhost:8000/heartbeat/current
echo.
echo 🔥 Trigger stress test:
echo   curl -X POST http://localhost:8000/heartbeat/stress-test
echo.
echo Press any key to run the test suite...
pause >nul

python test_heartbeat_integration.py

echo.
echo Press any key to exit...
pause >nul
