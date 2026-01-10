@echo off
echo ====================================
echo Stopping All Services
echo ====================================
echo.

echo 🛑 Stopping services on ports 8000, 8001, 5173...

REM Stop Backend API (Port 8000)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo Stopping process on port 8000 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

REM Stop ECG Simulator (Port 8001)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do (
    echo Stopping process on port 8001 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

REM Stop Frontend (Port 5173)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do (
    echo Stopping process on port 5173 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ✅ All services stopped
echo.
pause
