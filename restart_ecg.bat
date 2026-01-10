@echo off
echo Restarting ECG Simulator with ML integration...

echo Stopping ECG Simulator...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1

timeout /t 2 /nobreak >nul

echo Starting ECG Simulator on port 8001...
start "ECG Simulator" cmd /k "cd /d d:\Yodha26\ecg-deployment && python heartbeat_sim.py"

timeout /t 3 /nobreak >nul

echo.
echo ✅ ECG Simulator restarted!
echo    URL: http://localhost:8001/
echo.
pause
