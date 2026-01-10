"""
FastAPI Backend for Voice Stress Analysis
Serves the trained ML model with REST API
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import numpy as np
import librosa
import tempfile
import os
from pathlib import Path
from voice_stress_predictor import VoiceStressPredictor

# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:5174"
).split(",")

app = FastAPI(
    title="Voice Stress Analysis API",
    version="1.0.0",
    description="ML-powered voice stress detection with XGBoost model",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + ["*"],  # Allow all for now, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor
predictor = VoiceStressPredictor()

class AnalysisResponse(BaseModel):
    overall_stress_score: float
    stress_level: str
    emotion_detected: str
    ml_score: float
    mathematical_score: float
    duration: float
    audio_features: dict

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Voice Stress Analysis API",
        "model_loaded": predictor.model is not None,
        "version": "1.0.0"
    }

@app.post("/api/analyze-voice", response_model=AnalysisResponse)
async def analyze_voice(audio: UploadFile = File(...)):
    """
    Analyze voice from audio file.
    Accepts: WAV, MP3, OGG, FLAC, WebM
    Returns: Stress analysis results
    """
    try:
        # Save uploaded file temporarily as WAV (frontend already converts to WAV)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Load WAV audio with librosa
            audio_data, sr = librosa.load(tmp_file_path, sr=predictor.sample_rate, mono=True)
            
            if audio_data is None or len(audio_data) == 0:
                raise HTTPException(status_code=400, detail="Failed to load audio data - empty audio")
            
            duration = len(audio_data) / sr
            
            # Validate audio duration
            if duration < 0.5:
                raise HTTPException(status_code=400, detail="Audio too short (minimum 0.5 seconds)")
            if duration > 30:
                raise HTTPException(status_code=400, detail="Audio too long (maximum 30 seconds)")
            
            # Get prediction from trained model
            results = predictor.predict_from_audio(audio_data, sr)
            
            # Map emotion to format expected by frontend
            emotion_map = {
                'neutral': 'Calm',
                'happy': 'Happy',
                'encouraging': 'Excited',
                'assertive': 'Neutral',
                'excited': 'Excited',
                'apologetic': 'Anxious',
                'sad': 'Sad',
                'concerned': 'Stressed'
            }
            
            emotion_frontend = emotion_map.get(results.get('emotion', 'neutral'), 'Neutral')
            
            # Map stress level
            stress_level_map = {
                'LOW': 'Low',
                'MODERATE': 'Moderate',
                'HIGH': 'High',
                'VERY HIGH': 'High'
            }
            stress_level_frontend = stress_level_map.get(results['stress_level'], 'Moderate')
            
            # Extract audio features for response
            audio_features = {
                'sample_rate': int(sr),
                'duration': round(duration, 2),
                'samples': len(audio_data),
                'rms_energy': float(np.sqrt(np.mean(audio_data**2))),
                'max_amplitude': float(np.max(np.abs(audio_data)))
            }
            
            # Prepare response
            response = {
                'overall_stress_score': int(results['combined_stress']),
                'stress_level': stress_level_frontend,
                'emotion_detected': emotion_frontend,
                'ml_score': int(results['ml_stress']) if results['ml_stress'] else int(results['math_stress']),
                'mathematical_score': int(results['math_stress']),
                'duration': round(duration, 1),
                'audio_features': audio_features
            }
            
            return response
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@app.post("/api/analyze-raw-audio")
async def analyze_raw_audio(audio: UploadFile = File(...)):
    """
    Analyze raw audio data (for WebAudio API integration).
    """
    try:
        content = await audio.read()
        
        # Try to parse as raw audio bytes
        audio_array = np.frombuffer(content, dtype=np.float32)
        
        if len(audio_array) == 0:
            raise HTTPException(status_code=400, detail="Empty audio data")
        
        # Assume 22050 Hz sample rate for raw data
        sr = predictor.sample_rate
        duration = len(audio_array) / sr
        
        # Get prediction
        results = predictor.predict_from_audio(audio_array, sr)
        
        # Map to frontend format
        emotion_map = {
            'neutral': 'Calm',
            'happy': 'Happy',
            'encouraging': 'Excited',
            'assertive': 'Neutral',
            'excited': 'Excited',
            'apologetic': 'Anxious',
            'sad': 'Sad',
            'concerned': 'Stressed'
        }
        
        stress_level_map = {
            'LOW': 'Low',
            'MODERATE': 'Moderate',
            'HIGH': 'High',
            'VERY HIGH': 'High'
        }
        
        response = {
            'overall_stress_score': int(results['combined_stress']),
            'stress_level': stress_level_map.get(results['stress_level'], 'Moderate'),
            'emotion_detected': emotion_map.get(results.get('emotion', 'neutral'), 'Neutral'),
            'ml_score': int(results['ml_stress']) if results['ml_stress'] else int(results['math_stress']),
            'mathematical_score': int(results['math_stress']),
            'duration': round(duration, 1),
            'audio_features': {
                'sample_rate': int(sr),
                'duration': round(duration, 2),
                'samples': len(audio_array)
            }
        }
        
        return response
        
    except Exception as e:
        print(f"Error processing raw audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/model-info")
async def model_info():
    """Get information about the loaded model."""
    return {
        "model_loaded": predictor.model is not None,
        "model_type": "XGBoost Classifier",
        "accuracy": "74%",
        "features": "51 audio features (MFCC, Spectral, Pitch, Energy)",
        "emotions": list(predictor.emotion_stress.keys()),
        "sample_rate": predictor.sample_rate,
        "config": predictor.config if predictor.config else None
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8001))
    
    print("\n" + "="*60)
    print("   🚀 Voice Stress Analysis API Server")
    print("   Model: XGBoost (74% accuracy)")
    print(f"   Endpoint: http://0.0.0.0:{port}")
    print("   Environment:", os.getenv("ENVIRONMENT", "development"))
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
