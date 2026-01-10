@echo off
echo ========================================
echo Voice Stress Analysis API Server
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Installing/checking required packages...
python -m pip install -q fastapi uvicorn[standard] python-multipart librosa soundfile 2>nul

echo.
echo ========================================
echo Starting API server on http://localhost:8001
echo Press Ctrl+C to stop
echo ========================================
echo.

python api_server.py

pause
