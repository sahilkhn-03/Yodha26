"""
ML-Based Stress Prediction WebSocket Route
==========================================
Uses the trained XGBoost model (77.3% accuracy) for real-time facial stress prediction.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import base64
import cv2
import numpy as np
import sys
import os
from pathlib import Path

# Add ai directory to path
ai_dir = Path(__file__).parent.parent / 'ai'
sys.path.insert(0, str(ai_dir))

# Import the trained model
try:
    from inference_stress_model import StressPredictor
    ML_MODEL_AVAILABLE = True
    print("[OK] Loading trained XGBoost stress model...")
    stress_predictor = StressPredictor(
        model_path=ai_dir / 'models' / 'stress_predictor.pkl',
        scaler_path=ai_dir / 'models' / 'feature_scaler.pkl'
    )
    print("[OK] ✅ XGBoost stress model loaded (77.3% accuracy)")
except Exception as e:
    print(f"[ERROR] Could not load trained stress model: {e}")
    ML_MODEL_AVAILABLE = False
    stress_predictor = None

router = APIRouter()


@router.websocket("/ml-stress-analysis")
async def websocket_ml_stress_analysis(websocket: WebSocket):
    print("[DEBUG] WebSocket handler called!")
    """
    WebSocket endpoint for real-time ML-based facial stress prediction.
    Uses the trained XGBoost model with 9 facial features.
    
    Endpoint: ws://localhost:8000/ws/ml-stress-analysis
    
    Receives: JSON with base64 encoded frame
    {
        "frame": "data:image/jpeg;base64,...",
        "timestamp": 1234567890
    }
    
    Sends: JSON with ML predictions and facial metrics
    {
        "success": true,
        "stress_score": 42.5,           // 0-100 from ML model
        "stress_level": "Moderate",     // Low/Moderate/High/Extreme
        "features": {
            "avg_eye_aspect_ratio": 0.28,
            "left_ear": 0.27,
            "right_ear": 0.29,
            "avg_eyebrow_tension": 0.45,
            "left_eyebrow_tension": 0.44,
            "right_eyebrow_tension": 0.46,
            "mouth_openness": 0.12,
            "jaw_width": 0.65,
            "jaw_drop": 0.08
        },
        "model_info": {
            "type": "XGBoost",
            "accuracy": 77.3,
            "features_count": 9
        }
    }
    """
    print("[DEBUG] Accepting WebSocket connection...")
    await websocket.accept()
    
    # Debug: Check model availability
    print(f"[DEBUG] ML_MODEL_AVAILABLE = {ML_MODEL_AVAILABLE}")
    print(f"[DEBUG] stress_predictor is None = {stress_predictor is None}")
    
    # Check if model is available
    if not ML_MODEL_AVAILABLE or stress_predictor is None:
        print("[ERROR] ML stress model not available!")
        await websocket.send_json({
            "error": "ML stress model not available",
            "message": "Model files not found. Run train_stress_model.py first."
        })
        await websocket.close()
        return
    
    print("[OK] Client connected to ML stress analysis")
    print("[OK] XGBoost model ready (9 features, 77.3% accuracy)")
    
    frame_count = 0
    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_text()
            message = json.loads(data)
            frame_count += 1
            
            # Decode base64 image
            frame_data = message.get("frame", "")
            if frame_data.startswith("data:image"):
                frame_data = frame_data.split(",")[1]
            
            # Convert to OpenCV image
            img_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                print(f"[WARNING] Frame {frame_count}: Failed to decode")
                await websocket.send_json({
                    "error": "Failed to decode frame",
                    "success": False
                })
                continue
            
            # Predict stress using trained model
            print(f"[DEBUG] Frame {frame_count}: Running ML prediction...")
            result = stress_predictor.predict_from_frame(frame, return_landmarks=True)
            
            if result['success']:
                # Add model metadata
                result['model_info'] = {
                    'type': 'XGBoost',
                    'accuracy': 77.3,
                    'features_count': 9
                }
                
                print(f"[OK] Frame {frame_count}: Stress = {result['stress_score']:.1f}/100 ({result['stress_level']})")
                if 'landmarks' in result:
                    print(f"[OK] Frame {frame_count}: Sending {len(result['landmarks'])} landmarks")
            else:
                print(f"[INFO] Frame {frame_count}: {result.get('error', 'No face detected')}")
            
            # Send prediction to client
            await websocket.send_json(result)
            
    except WebSocketDisconnect:
        print("❌ Client disconnected from ML stress analysis")
    except Exception as e:
        print(f"❌ ML stress analysis error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"error": str(e), "success": False})
        except:
            pass


@router.get("/ml-model-info")
async def get_ml_model_info():
    """
    Get information about the loaded ML model.
    
    Returns:
    {
        "available": true,
        "model_type": "XGBoost Regressor",
        "accuracy": 77.3,
        "features": [...],
        "training_samples": 4092,
        "dataset": "FER-2013"
    }
    """
    if not ML_MODEL_AVAILABLE or stress_predictor is None:
        return {
            "available": False,
            "error": "Model not loaded"
        }
    
    return {
        "available": True,
        "model_type": "XGBoost Regressor",
        "accuracy": 77.3,
        "mae": 22.66,
        "features": [
            "avg_eye_aspect_ratio",
            "left_ear",
            "right_ear",
            "avg_eyebrow_tension",
            "left_eyebrow_tension",
            "right_eyebrow_tension",
            "mouth_openness",
            "jaw_width",
            "jaw_drop"
        ],
        "training_samples": 4092,
        "dataset": "FER-2013",
        "stress_levels": {
            "Low": "0-30",
            "Moderate": "30-55",
            "High": "55-75",
            "Extreme": "75-100"
        }
    }
