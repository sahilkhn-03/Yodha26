"""
WebSocket route for real-time facial stress analysis.
Uses facial_stress_inference_v2.py for actual face detection and stress scoring.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import base64
import json
import sys
import os
from typing import Optional

# Add facial emotion recognition baseline to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'facial_emotion_recognition_baseline'))

try:
    from facial_stress_inference_v2 import FacialStressInference, StressConfig
    FACIAL_MODEL_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Could not load facial stress model: {e}")
    FACIAL_MODEL_AVAILABLE = False

router = APIRouter()

# Global model instance (initialized once)
facial_model: Optional[FacialStressInference] = None

def get_facial_model():
    """Lazy initialization of facial stress model."""
    global facial_model
    if facial_model is None and FACIAL_MODEL_AVAILABLE:
        try:
            config = StressConfig(
                show_landmarks=True,
                show_connections=True,
                smoothing_window=5
            )
            facial_model = FacialStressInference(config)
            print("[OK] Facial stress model initialized")
        except Exception as e:
            print(f"[ERROR] Error initializing facial model: {e}")
            return None
    return facial_model


@router.websocket("/face-analysis")
async def websocket_face_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for real-time facial stress analysis.
    
    Receives: JSON with base64 encoded frame
    {
        "frame": "data:image/jpeg;base64,...",
        "timestamp": 1234567890
    }
    
    Sends: JSON with facial metrics and annotated frame
    {
        "eye_openness": 0.8,
        "brow_tension": 0.3,
        "jaw_tension": 0.2,
        "facial_asymmetry": 0.1,
        "head_motion": 0.15,
        "facial_stress_score": 25,
        "frame_overlay": "data:image/jpeg;base64,..."  // Frame with mesh
    }
    """
    await websocket.accept()
    
    # Get facial model
    model = get_facial_model()
    if model is None:
        print("[ERROR] Facial model failed to load!")
        await websocket.send_json({
            "error": "Facial stress model not available",
            "message": "Install dependencies: pip install mediapipe opencv-python numpy"
        })
        await websocket.close()
        return
    
    print("[OK] Client connected to face analysis")
    print("[OK] Facial model ready, waiting for frames...")
    
    frame_count = 0
    try:
        while True:
            print(f"[DEBUG] Waiting to receive frame #{frame_count + 1}...")
            # Receive frame from client
            data = await websocket.receive_text()
            message = json.loads(data)
            frame_count += 1
            print(f"[DEBUG] Frame {frame_count}: Received data, decoding...")
            
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
                continue
            
            # Resize frame for faster processing (optional but helps with lag)
            height, width = frame.shape[:2]
            if width > 640:
                scale = 640 / width
                frame = cv2.resize(frame, (640, int(height * scale)))
            
            # Process frame with facial stress model
            print(f"[DEBUG] Frame {frame_count}: Processing {width}x{height} image...")
            results, annotated_frame = model.process_frame_with_visualization(frame)
            
            # Check if face detected
            face_detected = results.get('face_detected', False)
            print(f"[DEBUG] Frame {frame_count}: Face detected = {face_detected}, Stress = {results.get('facial_stress', 0.0)}")
            
            # Send "no face" message if not detected
            if not face_detected:
                print(f"[INFO] Frame {frame_count}: No face detected, sending no-face message...")
                await websocket.send_json({
                    "face_detected": False,
                    "message": "No face detected"
                })
                continue
            
            # Encode annotated frame with mesh back to base64
            _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            frame_overlay = f"data:image/jpeg;base64,{frame_base64}"
            
            # Extract metrics from results
            metrics = {
                "face_detected": True,
                "eye_openness": float(results.get("eye_closure", 0.0)),
                "brow_tension": float(results.get("eyebrow_tension", 0.0)),
                "jaw_tension": float(results.get("jaw_tension", 0.0)),
                "facial_asymmetry": float(results.get("facial_stress", 0.0)) * 0.01,
                "head_motion": 0.15,
                "facial_stress_score": float(results.get("facial_stress", 0.0)),
                "frame_overlay": frame_overlay
            }
            
            print(f"[OK] Frame {frame_count}: Sending annotated frame with mesh (size: {len(frame_base64)} bytes)")
            
            # Send back to client
            await websocket.send_json(metrics)
            
    except WebSocketDisconnect:
        print("❌ Client disconnected from face analysis")
    except Exception as e:
        print(f"❌ Face analysis error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
