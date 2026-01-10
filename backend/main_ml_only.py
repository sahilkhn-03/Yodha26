"""
NeuroBalance AI - ML-Only Backend
==================================
Minimal FastAPI backend for facial stress prediction WITHOUT database.
Perfect for edge AI deployment.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ML-based stress prediction with trained XGBoost model
from routes_ml_stress import router as ml_stress_router

app = FastAPI(
    title="NeuroBalance Facial Stress API",
    version="1.0.0",
    description="Edge AI facial stress prediction using XGBoost model",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "service": "facial-stress-api",
        "version": "1.0.0",
        "ml_model": "XGBoost 77.3%",
        "mode": "edge-ai"
    }

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "NeuroBalance Facial Stress API",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "websocket": "ws://[host]/ws/ml-stress-analysis"
        }
    }

# Include ML stress prediction router
app.include_router(ml_stress_router, prefix="/ws", tags=["ML Stress"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
