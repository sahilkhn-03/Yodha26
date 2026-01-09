@echo off
echo ================================================
echo Starting All Servers for Yodha26
echo ================================================

echo.
echo [1/3] Starting Main Backend (Port 8000)...
start "Backend-8000" cmd /k "cd /d D:\Yodha26\backend && D:\Yodha26\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
timeout /t 3 >nul

echo.
echo [2/3] Starting ECG Simulator (Port 8001)...
start "ECG-Simulator-8001" cmd /k "cd /d D:\Yodha26\backend && D:\Yodha26\.venv\Scripts\python.exe -m uvicorn heartbeat_sim:app --reload --port 8001"
timeout /t 3 >nul

echo.
echo [3/3] Starting Frontend (Port 5173)...
start "Frontend-5173" cmd /k "cd /d D:\Yodha26\opencvfront\project && npm run dev"
timeout /t 3 >nul

echo.
echo ================================================
echo All Servers Started!
echo ================================================
echo.
echo Backend API:        http://localhost:8000
echo API Docs:           http://localhost:8000/docs
echo ECG Simulator:      http://localhost:8001
echo ECG Data Collection: http://localhost:8001/data-collection
echo Frontend (Camera):  http://localhost:5173
echo.
echo ================================================
echo Test Integrated Endpoint:
echo   http://localhost:8000/api/ecg/predict-stress
echo   http://localhost:8000/api/ecg/status
echo ================================================
pause
