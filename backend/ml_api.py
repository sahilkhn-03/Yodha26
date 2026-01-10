"""
Minimal ML Prediction API for ECG Simulator
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI(title="ML Prediction API")

# Load model
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
    bpm: int


class StressPrediction(BaseModel):
    bpm: int
    prediction: str
    confidence: float
    stress_score: float


@app.get("/")
def root():
    return {"service": "ML Prediction API", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/api/ml/predict", response_model=StressPrediction)
async def predict_stress(data: HeartRateInput):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="ML model not loaded")
    
    try:
        # Prepare features
        features = pd.DataFrame({
            'bpm': [data.bpm],
            'bpm_squared': [data.bpm ** 2],
            'bpm_normalized': [(data.bpm - 70) / 30]
        })
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Predict
        prediction = model.predict(features_scaled)[0]
        probabilities = model.predict_proba(features_scaled)[0]
        
        # Get class labels
        classes = model.classes_
        pred_label = classes[prediction]
        
        # Calculate confidence and stress score
        stress_idx = list(classes).index("Stress") if "Stress" in classes else 1
        confidence = float(max(probabilities))
        stress_score = float(probabilities[stress_idx])
        
        return StressPrediction(
            bpm=data.bpm,
            prediction=pred_label,
            confidence=confidence,
            stress_score=stress_score
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
