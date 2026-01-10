# Local Development Setup Guide

## Services Overview

This project runs 3 local services:

1. **Backend API (FastAPI)** - Port 8000
   - ML model predictions
   - Database management
   - WebSocket for stress analysis
   - API docs: http://localhost:8000/docs

2. **ECG Simulator (FastAPI)** - Port 8001
   - Simulates heartbeat data
   - WebSocket for real-time ECG
   - ML predictions from backend
   - UI: http://localhost:8001/

3. **Frontend (React + Vite)** - Port 5173
   - Main UI with camera/face analysis
   - ECG monitoring dashboard
   - Interactive stress analysis
   - UI: http://localhost:5173/

## Quick Start

### 1. Start All Services
```bash
start_all_local.bat
```

This will:
- Kill any existing processes on ports 8000, 8001, 5173
- Start Backend API on port 8000
- Start ECG Simulator on port 8001
- Start Frontend on port 5173
- Open 3 terminal windows (one for each service)

### 2. Access Services

- **Frontend**: http://localhost:5173/
- **ECG Simulator**: http://localhost:8001/
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health

### 3. Stop All Services
```bash
stop_all_local.bat
```

Or close the 3 terminal windows manually.

## Manual Setup (if needed)

### Backend API
```bash
cd d:\Yodha26\backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### ECG Simulator
```bash
cd d:\Yodha26\ecg-deployment
python heartbeat_sim.py
```

### Frontend
```bash
cd d:\Yodha26\opencvfront\project
npm run dev
```

## Testing Integration

### 1. Start ECG Simulation
```bash
curl -X POST http://localhost:8001/simulation/start
```

### 2. Get Current Heartbeat with ML Prediction
```bash
curl http://localhost:8001/heartbeat/current
```

Expected response:
```json
{
  "timestamp": "2026-01-10T...",
  "bpm": 75,
  "systolic": 120,
  "diastolic": 80,
  "stress_level": 0.3,
  "variability": 0.05,
  "state": "running",
  "prediction": "Normal",
  "confidence": 0.85,
  "stress_score": 0.15
}
```

### 3. Test ML API Directly
```bash
curl -X POST http://localhost:8000/api/ml/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"bpm\": 95}"
```

### 4. Trigger Stress Simulation
```bash
curl -X POST "http://localhost:8001/simulation/trigger-stress?stress_level=0.8"
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (5173)                      │
│  React + Vite + TypeScript + Tailwind                   │
│  - Camera/Face Analysis UI                              │
│  - ECG Dashboard                                        │
└───────────────┬─────────────────────┬───────────────────┘
                │                     │
                │ WebSocket           │ WebSocket
                │ (stress)            │ (ECG)
                ▼                     ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│   Backend API (8000)      │ │  ECG Simulator (8001)    │
│   - ML Models             │◄┤  - Heartbeat generation  │
│   - Database              │ │  - ML prediction calls   │
│   - Stress Analysis       │ │  - Real-time streaming   │
└───────────────────────────┘ └──────────────────────────┘
```

## Environment Variables (optional)

### ECG Simulator
- `PORT`: Port for ECG simulator (default: 8001)
- `ML_API_URL`: Backend ML API URL (default: http://localhost:8000)

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Port for backend (default: 8000)

## Troubleshooting

### Port Already in Use
Run `stop_all_local.bat` first to kill existing processes.

### Backend Won't Start
- Check if PostgreSQL/Supabase is accessible
- Verify `DATABASE_URL` in backend/.env
- Check backend requirements: `pip install -r backend/requirements.txt`

### Frontend Won't Start
- Install dependencies: `cd opencvfront/project && npm install`
- Check Node.js version: `node --version` (should be v16+)

### ECG Simulator Shows No Predictions
- Verify backend is running on port 8000
- Check backend ML models exist in `backend/models/`
- Test ML API directly: http://localhost:8000/docs

### ML Models Missing
If predictions show null:
1. Train the model: `python backend/train_heartrate_classifier.py`
2. Verify models exist: `backend/models/heartrate_stress_classifier.pkl`

## Development Tips

- All services have hot-reload enabled
- Backend API has interactive docs at `/docs`
- WebSocket connections auto-reconnect on disconnect
- ECG simulator runs at 4 Hz (250ms updates)
- Frontend uses Vite for instant HMR (Hot Module Replacement)

## Next Steps

- Deploy to Google Cloud Run (see `ecg-deployment/DEPLOY_NOW.md`)
- Configure production database
- Set up environment variables for production
- Enable HTTPS for WebSocket secure connections
