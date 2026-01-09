from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Optional

# Import database and models
from database import Base, engine
from models import User, Patient, Assessment

# Import routers
from routes_auth import router as auth_router
from routes_patients import router as patients_router
from routes_assessments import router as assessments_router
from routes_training_data import router as training_router
from routes_ml_heartrate import router as ml_router
from routes_ecg_integration import router as ecg_router
# Unified WebSocket manager (consolidates routes_websocket + routes_face_analysis)
from websocket_manager import router as websocket_router
# ML-based stress prediction with trained XGBoost model
from routes_ml_stress import router as ml_stress_router

# Heartbeat simulation service URL
HEARTBEAT_SIM_URL = "http://localhost:8001"

# Heartbeat simulation service URL
HEARTBEAT_SIM_URL = "http://localhost:8001"

# Create database tables (only if database is configured)
# NOTE: Update DATABASE_URL in .env with your Supabase connection string
try:
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified")
except Exception as e:
    print(f"[WARNING] Database not connected: {e}")
    print("[INFO] Update DATABASE_URL in .env with your Supabase connection string")
    print("       Get it from: Supabase Dashboard -> Settings -> Database -> Connection String")

app = FastAPI(
    title="NeuroBalance AI Backend",
    version="1.0.0",
    description="AI-driven psychosomatic assessment platform backend API",
    docs_url="/docs",  # Interactive API documentation
    redoc_url="/redoc"  # Alternative documentation view
)

# Configure CORS - allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# This connects all route files to the main app
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(patients_router, prefix="/patients", tags=["Patients"])
app.include_router(assessments_router, prefix="/assessments", tags=["Assessments"])
app.include_router(training_router, tags=["Training Data"])
app.include_router(ml_router, tags=["ML Predictions"])
app.include_router(ecg_router, tags=["ECG Integration"])
# Unified WebSocket router handles all WebSocket endpoints under /ws/*
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
# ML stress prediction endpoints (WebSocket + REST)
app.include_router(ml_stress_router, prefix="/ws", tags=["ML Stress Analysis"])


@app.get("/")
def root():
    """Root endpoint - basic health check"""
    return {
        "message": "NeuroBalance AI Backend API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "NeuroBalance AI Backend"
    }


# ============= Heartbeat Data Endpoints for ML Model =============

@app.get("/heartbeat/current")
async def get_current_heartbeat():
    """
    Get current heartbeat data (NORMAL or ELEVATED).
    
    Returns:
        {
            "timestamp": "2026-01-09T12:34:56.789Z",
            "bpm": 72,                    # Can be 60-180 (normal OR elevated)
            "systolic": 120,              # Blood pressure
            "diastolic": 80,
            "stress_level": 0.0,          # 0.0 = calm, 1.0 = high stress
            "state": "running"
        }
    
    Use cases:
    - ML model polling for latest heart rate
    - Check if heart rate is normal or elevated
    - Continuous monitoring without WebSocket
    
    ⚠️ Returns ALL data (normal + elevated), not filtered!
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HEARTBEAT_SIM_URL}/heartbeat/current", timeout=3.0)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": "Heartbeat simulation not available",
                    "status_code": response.status_code,
                    "message": "Start heartbeat simulation: POST http://localhost:8001/simulation/start"
                }
    except Exception as e:
        return {
            "error": "Cannot connect to heartbeat simulation",
            "message": str(e),
            "solution": "Make sure heartbeat_sim.py is running on port 8001"
        }


@app.post("/heartbeat/start")
async def start_heartbeat_simulation():
    """
    Start the heartbeat simulation.
    
    This will generate:
    - Normal heart rates (60-80 BPM baseline)
    - Elevated heart rates during stress (90-180 BPM)
    - Blood pressure data
    - Stress levels
    
    Call this BEFORE fetching heartbeat data!
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{HEARTBEAT_SIM_URL}/simulation/start", timeout=3.0)
            return response.json()
    except Exception as e:
        return {
            "error": "Cannot start heartbeat simulation",
            "message": str(e),
            "solution": "Run: uvicorn heartbeat_sim:app --port 8001 --reload"
        }


@app.post("/heartbeat/stress-test")
async def trigger_stress_test():
    """
    Trigger a 5-second stress event.
    
    This will:
    - Elevate heart rate to 90-140 BPM
    - Increase blood pressure
    - Set stress_level to 0.7-0.95
    - Return to normal after 5 seconds
    
    Perfect for testing ML model's ability to detect stress!
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{HEARTBEAT_SIM_URL}/simulation/stress-test", timeout=3.0)
            return response.json()
    except Exception as e:
        return {
            "error": "Cannot trigger stress test",
            "message": str(e)
        }


@app.post("/heartbeat/stop")
async def stop_heartbeat_simulation():
    """
    Stop the heartbeat simulation.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{HEARTBEAT_SIM_URL}/simulation/stop", timeout=3.0)
            return response.json()
    except Exception as e:
        return {
            "error": "Cannot stop heartbeat simulation",
            "message": str(e)
        }


@app.get("/heartbeat/status")
async def get_heartbeat_status():
    """
    Check if heartbeat simulation is running.
    
    Returns:
        {
            "status": "healthy",
            "simulation_state": "running" or "stopped",
            "base_bpm": 72,
            "websocket_clients": 2
        }
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HEARTBEAT_SIM_URL}/health", timeout=3.0)
            return response.json()
    except Exception as e:
        return {
            "error": "Heartbeat service not available",
            "message": str(e),
            "solution": "Start service: uvicorn heartbeat_sim:app --port 8001 --reload"
        }


if __name__ == "__main__":
    import uvicorn
    # Run server on localhost:8000 with auto-reload for development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-restart on code changes
    )
