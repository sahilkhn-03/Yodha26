"""
ML Heart Rate Stress Prediction API
Uses trained classifier to predict stress from heart rate data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import joblib
import pandas as pd
import os

router = APIRouter(prefix="/api/ml", tags=["ML Predictions"])

# Load model and scaler
MODEL_DIR = "models"
model_path = os.path.join(MODEL_DIR, "heartrate_stress_classifier.pkl")
scaler_path = os.path.join(MODEL_DIR, "heartrate_scaler.pkl")

try:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    print(f"✅ ML Model loaded: {model_path}")
except Exception as e:
    print(f"⚠️  ML Model not found: {e}")
    model = None
    scaler = None


class HeartRateInput(BaseModel):
    """Input schema for heart rate stress prediction"""
    bpm: int = Field(..., ge=30, le=220, description="Heart rate in BPM")


class StressPrediction(BaseModel):
    """Output schema for stress prediction"""
    bpm: int
    prediction: str  # "Normal" or "Stress"
    confidence: float  # 0.0 to 1.0
    probabilities: dict  # {"Normal": 0.xx, "Stress": 0.xx}
    stress_score: float  # 0.0 to 1.0


@router.post("/predict", response_model=StressPrediction)
async def predict_stress(data: HeartRateInput):
    """
    Predict stress level from heart rate.
    
    Returns:
        - prediction: "Normal" or "Stress"
        - confidence: Model confidence (0-1)
        - probabilities: Probability for each class
        - stress_score: Normalized stress score (0-1)
    
    Example:
        POST /api/ml/predict
        {"bpm": 125}
        
        Response:
        {
            "bpm": 125,
            "prediction": "Stress",
            "confidence": 0.98,
            "probabilities": {"Normal": 0.02, "Stress": 0.98},
            "stress_score": 0.98
        }
    """
    if model is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail="ML model not loaded. Run train_heartrate_classifier.py first."
        )
    
    try:
        # Prepare features (same as training)
        features = pd.DataFrame({
            'bpm': [data.bpm],
            'bpm_squared': [data.bpm ** 2],
            'bpm_normalized': [(data.bpm - 70) / 30]
        })
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Predict
        pred_label = model.predict(features_scaled)[0]
        pred_proba = model.predict_proba(features_scaled)[0]
        
        prediction = "Stress" if pred_label == 1 else "Normal"
        confidence = float(pred_proba[pred_label])
        stress_score = float(pred_proba[1])  # Probability of stress class
        
        return StressPrediction(
            bpm=data.bpm,
            prediction=prediction,
            confidence=confidence,
            probabilities={
                "Normal": float(pred_proba[0]),
                "Stress": float(pred_proba[1])
            },
            stress_score=stress_score
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/model/info")
async def get_model_info():
    """
    Get information about the loaded ML model.
    
    Returns model metadata, training stats, and status.
    """
    if model is None:
        return {
            "status": "not_loaded",
            "message": "Model not trained yet. Run train_heartrate_classifier.py"
        }
    
    try:
        import json
        metadata_path = os.path.join(MODEL_DIR, "heartrate_model_metadata.json")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return {
            "status": "loaded",
            "model_type": metadata.get("model_type"),
            "accuracy": metadata.get("accuracy"),
            "training_samples": metadata.get("training_samples"),
            "features": metadata.get("features"),
            "trained_at": metadata.get("trained_at")
        }
    except Exception as e:
        return {
            "status": "loaded",
            "message": f"Model loaded but metadata not available: {e}"
        }


@router.post("/predict/batch")
async def predict_stress_batch(data: list[HeartRateInput]):
    """
    Predict stress for multiple heart rate readings.
    
    Useful for analyzing a sequence of ECG readings.
    
    Example:
        POST /api/ml/predict/batch
        [
            {"bpm": 72},
            {"bpm": 85},
            {"bpm": 125}
        ]
    """
    if model is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail="ML model not loaded"
        )
    
    try:
        predictions = []
        for item in data:
            # Prepare features
            features = pd.DataFrame({
                'bpm': [item.bpm],
                'bpm_squared': [item.bpm ** 2],
                'bpm_normalized': [(item.bpm - 70) / 30]
            })
            
            features_scaled = scaler.transform(features)
            pred_label = model.predict(features_scaled)[0]
            pred_proba = model.predict_proba(features_scaled)[0]
            
            predictions.append({
                "bpm": item.bpm,
                "prediction": "Stress" if pred_label == 1 else "Normal",
                "confidence": float(pred_proba[pred_label]),
                "stress_score": float(pred_proba[1])
            })
        
        # Calculate aggregate statistics
        stress_count = sum(1 for p in predictions if p["prediction"] == "Stress")
        avg_stress_score = sum(p["stress_score"] for p in predictions) / len(predictions)
        
        return {
            "predictions": predictions,
            "summary": {
                "total_readings": len(predictions),
                "stress_readings": stress_count,
                "normal_readings": len(predictions) - stress_count,
                "avg_stress_score": round(avg_stress_score, 3),
                "overall_assessment": "High Stress" if avg_stress_score > 0.6 else "Moderate Stress" if avg_stress_score > 0.3 else "Normal"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")
