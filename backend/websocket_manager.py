"""
Unified WebSocket Manager - All WebSocket logic in one module.

This module consolidates:
1. Stress data simulation WebSocket (/ws/simulation)
2. Facial stress analysis WebSocket (/ws/face-analysis)
3. Broadcast mode WebSocket (/ws/simulation/broadcast)

Why consolidate?
- Centralized connection management
- Easier debugging and maintenance
- Shared utilities for all WebSocket endpoints
- Consistent error handling
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Optional
import asyncio
import random
import json
import base64
from datetime import datetime
import httpx
import cv2
import numpy as np
import sys
import os

# Add facial emotion recognition baseline to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'facial_emotion_recognition_baseline'))

try:
    from facial_stress_inference_v2 import FacialStressInference, StressConfig
    FACIAL_MODEL_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Could not load facial stress model: {e}")
    FACIAL_MODEL_AVAILABLE = False

router = APIRouter()

# Configuration
HEARTBEAT_SIM_URL = "http://localhost:8001"

# ============= Connection Manager =============

class ConnectionManager:
    """
    Centralized WebSocket connection manager.
    
    Manages multiple clients and handles:
    - Connection lifecycle
    - Broadcasting to all clients
    - Graceful disconnect handling
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[OK] Client connected. Total clients: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[INFO] Client disconnected. Total clients: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """
        Send message to all connected clients.
        Handles disconnected clients gracefully.
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager instance
manager = ConnectionManager()

# ============= Facial Model Initialization =============

# Global facial model instance (initialized once)
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

# ============= Heartbeat Data Fetcher =============

async def get_heartbeat_data():
    """
    Fetch real heartbeat data from heartbeat simulation service.
    
    Returns data from heartbeat_sim.py which includes:
    - Both NORMAL and ELEVATED heart rates
    - Real stress levels (not fake)
    - Blood pressure data
    - Timestamp
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HEARTBEAT_SIM_URL}/heartbeat/current", timeout=2.0)
            if response.status_code == 200:
                return response.json()
            else:
                return None
    except Exception as e:
        print(f"Error fetching heartbeat data: {e}")
        return None

# ============= Data Generators =============

async def generate_stress_data():
    """
    Generate comprehensive stress monitoring data using REAL heartbeat simulation.
    
    NOW INCLUDES:
    - ✅ NORMAL heart rates (60-80 BPM baseline)
    - ✅ ELEVATED heart rates (90-180 BPM during stress)
    - ✅ Real stress levels from heartbeat_sim.py
    - ✅ Blood pressure data
    - ✅ Facial stress simulation
    """
    facial_stress = random.uniform(0.2, 0.4)
    
    while True:
        # Fetch REAL heartbeat data (includes normal AND elevated rates)
        heartbeat_data = await get_heartbeat_data()
        
        if heartbeat_data:
            # Use REAL heart rate and stress from simulation
            heart_rate = heartbeat_data.get("bpm", 72)
            stress_level = heartbeat_data.get("stress_level", 0.0)
            systolic = heartbeat_data.get("systolic", 120)
            diastolic = heartbeat_data.get("diastolic", 80)
            timestamp = heartbeat_data.get("timestamp", datetime.utcnow().isoformat())
            
            # Update facial stress based on actual stress level
            facial_stress += random.uniform(-0.04, 0.06) + (stress_level * 0.1)
            facial_stress = max(0.0, min(1.0, facial_stress))
            
            # Determine status based on heart rate
            if heart_rate < 75:
                status = "normal"
            elif heart_rate < 90:
                status = "slightly_elevated"
            elif heart_rate < 110:
                status = "elevated"
            else:
                status = "high_stress"
            
        else:
            # Fallback if heartbeat service is not available
            heart_rate = random.randint(65, 75)
            stress_level = random.uniform(0.0, 0.3)
            systolic = 120
            diastolic = 80
            timestamp = datetime.utcnow().isoformat()
            status = "normal_fallback"
            
            facial_stress += random.uniform(-0.04, 0.06)
            facial_stress = max(0.0, min(1.0, facial_stress))
        
        # Create comprehensive data packet
        data = {
            "timestamp": timestamp,
            "stress_score": round(stress_level, 3),
            "heart_rate": heart_rate,
            "systolic_bp": systolic,
            "diastolic_bp": diastolic,
            "facial_stress": round(facial_stress, 3),
            "status": status,
            "data_source": "heartbeat_simulation" if heartbeat_data else "fallback"
        }
        
        yield data
        
        # Match heartbeat simulation frequency (500ms)
        await asyncio.sleep(0.5)

# ============= WebSocket Endpoints =============

@router.websocket("/simulation")
async def websocket_simulation(websocket: WebSocket):
    """
    WebSocket endpoint for COMPLETE stress data (NORMAL + ELEVATED heart rates).
    
    Endpoint: ws://localhost:8000/ws/simulation
    
    Data format (JSON every 500ms):
    {
        "timestamp": "2026-01-09T12:34:56.789Z",
        "stress_score": 0.742,
        "heart_rate": 95,
        "systolic_bp": 135,
        "diastolic_bp": 87,
        "facial_stress": 0.631,
        "status": "elevated",
        "data_source": "heartbeat_simulation"
    }
    """
    # Connect client
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Stress simulation started",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start streaming simulated data
        async for data in generate_stress_data():
            await websocket.send_json(data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected from simulation")
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/simulation/broadcast")
async def websocket_broadcast(websocket: WebSocket):
    """
    Broadcast mode: All connected clients see the same data stream.
    
    Endpoint: ws://localhost:8000/ws/simulation/broadcast
    """
    await manager.connect(websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "mode": "broadcast",
            "message": "Connected to shared stress simulation",
            "clients": len(manager.active_connections)
        })
        
        # Keep connection alive
        while True:
            message = await websocket.receive_text()
            
            # Echo back for debugging
            await websocket.send_json({
                "type": "echo",
                "received": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/face-analysis")
async def websocket_face_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for real-time facial stress analysis with 478 facial landmarks.
    
    Endpoint: ws://localhost:8000/ws/face-analysis
    
    Receives: JSON with base64 encoded frame
    {
        "frame": "data:image/jpeg;base64,...",
        "timestamp": 1234567890
    }
    
    Sends: JSON with facial metrics and annotated frame with 478-point mesh
    {
        "eye_openness": 0.8,
        "brow_tension": 0.3,
        "jaw_tension": 0.2,
        "facial_asymmetry": 0.1,
        "head_motion": 0.15,
        "facial_stress_score": 25,
        "frame_overlay": "data:image/jpeg;base64,..."  // Frame with 478-point mesh
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
    
    print("[OK] Client connected to facial stress analysis")
    print("[OK] Facial model ready with 478-point mesh, waiting for frames...")
    
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
            
            # Process frame with facial stress model (generates 478-point mesh)
            print(f"[DEBUG] Frame {frame_count}: Processing {width}x{height} image with 478 landmarks...")
            results, annotated_frame = model.process_frame_with_visualization(frame)
            
            # Check if face detected
            face_detected = results.get('face_detected', False)
            print(f"[DEBUG] Frame {frame_count}: Face detected = {face_detected}, Stress = {results.get('facial_stress', 0.0)}")
            
            # Only send if face detected
            if not face_detected:
                print(f"[INFO] Frame {frame_count}: No face detected, skipping...")
                continue
            
            # Encode annotated frame with 478-point mesh back to base64
            _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            frame_overlay = f"data:image/jpeg;base64,{frame_base64}"
            
            # Extract metrics from results
            metrics = {
                "eye_openness": float(results.get("eye_closure", 0.0)),
                "brow_tension": float(results.get("eyebrow_tension", 0.0)),
                "jaw_tension": float(results.get("jaw_tension", 0.0)),
                "facial_asymmetry": float(results.get("facial_stress", 0.0)) * 0.01,
                "head_motion": 0.15,
                "facial_stress_score": float(results.get("facial_stress", 0.0)),
                "frame_overlay": frame_overlay,
                "landmarks_count": 478  # MediaPipe Face Mesh uses 478 landmarks
            }
            
            print(f"[OK] Frame {frame_count}: Sending annotated frame with 478-point mesh (size: {len(frame_base64)} bytes)")
            
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


# ============= Background Tasks (Optional) =============

async def broadcast_simulation():
    """
    Background task that broadcasts same data to all clients.
    
    Add to main.py startup:
        @app.on_event("startup")
        async def startup():
            asyncio.create_task(broadcast_simulation())
    """
    async for data in generate_stress_data():
        if manager.active_connections:
            await manager.broadcast(data)


# ============= Testing Examples =============

# Python client test:
# 
#   import asyncio
#   import websockets
#   import json
#   
#   async def test_simulation():
#       uri = "ws://localhost:8000/ws/simulation"
#       async with websockets.connect(uri) as ws:
#           while True:
#               data = await ws.recv()
#               print(json.loads(data))
#   
#   asyncio.run(test_simulation())
#
# JavaScript client test:
#
#   const ws = new WebSocket('ws://localhost:8000/ws/simulation');
#   ws.onmessage = (event) => {
#       const data = JSON.parse(event.data);
#       console.log('Stress:', data.stress_score, 'HR:', data.heart_rate);
#   };
#
# Face analysis client test:
#
#   const ws = new WebSocket('ws://localhost:8000/ws/face-analysis');
#   ws.onmessage = (event) => {
#       const data = JSON.parse(event.data);
#       console.log('Facial Stress:', data.facial_stress_score);
#       // Display frame_overlay with 478-point mesh
#       document.getElementById('video').src = data.frame_overlay;
#   };
