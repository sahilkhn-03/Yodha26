"""
WebSocket routes for real-time data streaming.

Why WebSockets?
- Real-time bidirectional communication
- Lower latency than HTTP polling
- Efficient for continuous data streams like live stress monitoring
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import random
import json
from datetime import datetime
<<<<<<< HEAD
import httpx
=======
<<<<<<< HEAD
import httpx
=======
import base64

# Try importing OpenCV + NumPy for image decode; optional
try:
    import numpy as np  # type: ignore
    import cv2  # type: ignore
except Exception:
    np = None  # type: ignore
    cv2 = None  # type: ignore

# Try to import baseline facial stress engine for landmark visualization
baseline_engine = None
try:
    import os, sys
    repo_root = os.path.dirname(os.path.dirname(__file__))
    baseline_dir = os.path.join(repo_root, 'facial_emotion_recognition_baseline')
    if baseline_dir not in sys.path:
        sys.path.append(baseline_dir)
    from facial_stress_inference_v2 import FacialStressInference, StressConfig  # type: ignore
    baseline_engine = FacialStressInference(StressConfig(show_landmarks=True, show_connections=True))
except Exception:
    baseline_engine = None
    try:
        from utils.face_analysis import analyze_face  # type: ignore
    except Exception:
        analyze_face = None  # type: ignore
>>>>>>> d996b41 (Include local frontend + backend changes (mesh overlay + baseline wiring))
>>>>>>> 94f2d3ea339fd48608dc024b1df32f82b33374b2

router = APIRouter()

# Configuration for heartbeat simulation service
HEARTBEAT_SIM_URL = "http://localhost:8001"

# Connection manager to handle multiple clients
class ConnectionManager:
    """
    Manages multiple WebSocket connections.
    
    Why?
    - Multiple clinicians can watch simulations simultaneously
    - Broadcast data to all connected clients
    - Clean up disconnected clients automatically
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
        self.active_connections.remove(websocket)
        print(f"[INFO] Client disconnected. Total clients: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """
        Send message to all connected clients.
        
        Handles disconnected clients gracefully:
        - If send fails, mark for removal
        - Clean up after broadcast
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


async def get_heartbeat_data():
    """
    Fetch real heartbeat data from heartbeat simulation service.
    
    Returns data from heartbeat_sim.py which includes:
    - Both NORMAL and ELEVATED heart rates
    - Real stress levels (not fake)
    - Blood pressure data
    - Timestamp
    
    This ensures the model gets ALL heart rate data, not just elevated.
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


async def generate_stress_data():
    """
    Generate comprehensive stress monitoring data using REAL heartbeat simulation.
    
    NOW INCLUDES:
    - ✅ NORMAL heart rates (60-80 BPM baseline)
    - ✅ ELEVATED heart rates (90-180 BPM during stress)
    - ✅ Real stress levels from heartbeat_sim.py
    - ✅ Blood pressure data
    - ✅ Facial stress simulation
    
    Model will receive ALL data points, both normal and elevated!
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


@router.websocket("/simulation")
async def websocket_simulation(websocket: WebSocket):
    """
    WebSocket endpoint for COMPLETE stress data (NORMAL + ELEVATED heart rates).
    
    Endpoint: ws://localhost:8000/ws/simulation
    
    ⚠️ IMPORTANT: Now includes ALL heart rate data:
    - ✅ Normal baseline (60-80 BPM)
    - ✅ Elevated stress (90-180 BPM)
    - ✅ Everything in between
    
    Data format (JSON every 500ms):
    {
        "timestamp": "2026-01-09T12:34:56.789Z",
        "stress_score": 0.742,      // 0.0 = calm, 1.0 = high stress
        "heart_rate": 95,            // Current BPM (can be normal OR elevated)
        "systolic_bp": 135,          // Blood pressure
        "diastolic_bp": 87,
        "facial_stress": 0.631,      // From facial analysis
        "status": "elevated",        // normal, slightly_elevated, elevated, high_stress
        "data_source": "heartbeat_simulation"
    }
    
    Frontend/Model usage:
        const ws = new WebSocket('ws://localhost:8000/ws/simulation');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Model now gets ALL data, not just high stress!
            if (data.status === "normal") {
                console.log("Normal heart rate:", data.heart_rate);
            } else {
                console.log("Elevated heart rate:", data.heart_rate);
            }
            
            // Send to ML model for analysis
            analyzeStressLevel(data);
        };
    
    Why this matters for ML:
    - Model needs normal data to establish baseline
    - Can't detect stress without knowing what's normal
    - Balanced dataset (normal + elevated) = better predictions
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
        # Client disconnected (closed browser, lost connection, etc.)
        manager.disconnect(websocket)
        print("Client disconnected from simulation")
        
    except Exception as e:
        # Handle any other errors gracefully
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Additional endpoint: Broadcast mode (all clients see same data)
@router.websocket("/simulation/broadcast")
async def websocket_broadcast(websocket: WebSocket):
    """
    Broadcast mode: All connected clients see the same data stream.
    
    Use case: Demo mode where multiple viewers watch one simulation.
    
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
        
        # Keep connection alive (actual broadcasting happens in background)
        while True:
            # Wait for client messages (keep-alive, commands, etc.)
            message = await websocket.receive_text()
            
            # Echo back for debugging
            await websocket.send_json({
                "type": "echo",
                "received": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Background task for broadcast mode (optional)
async def broadcast_simulation():
    """
    Background task that broadcasts same data to all clients.
    
    How to use:
    1. Start this as a background task when server starts
    2. All clients in broadcast mode receive same data
    
    Add to main.py startup:
        @app.on_event("startup")
        async def startup():
            asyncio.create_task(broadcast_simulation())
    """
    async for data in generate_stress_data():
        if manager.active_connections:
            await manager.broadcast(data)


# -------------------------------
# Face Analysis WebSocket (Realtime)
# -------------------------------

def _decode_base64_image(data_url_or_b64: str):
    """
    Decode a base64-encoded image string to an OpenCV BGR image if possible.
    Accepts data URLs (e.g., "data:image/jpeg;base64,....") or raw base64.
    Returns:
        image: np.ndarray (BGR) if cv2 is available, else None
        raw_bytes: bytes of the decoded image for custom pipelines
    """
    try:
        # Strip data URL header if present
        if "," in data_url_or_b64 and data_url_or_b64.startswith("data:"):
            b64_part = data_url_or_b64.split(",", 1)[1]
        else:
            b64_part = data_url_or_b64
        raw = base64.b64decode(b64_part)
        if cv2 is not None and np is not None:
            buf = np.frombuffer(raw, dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            return img, raw
        return None, raw
    except Exception:
        return None, None


def _safe_analyze(frame_img, frame_bytes, last_metrics: dict | None):
    """
    Call the existing analyze_face(frame) if available; otherwise return fallback metrics.
    - frame_img: np.ndarray (BGR) or None
    - frame_bytes: bytes or None
    """
    # Default zeros or last known
    default = {
        "eye_openness": 0.0,
        "brow_tension": 0.0,
        "jaw_tension": 0.0,
        "head_motion": 0.0,
        "facial_stress_score": 0.0,
    }
    try:
        # Prefer baseline engine with landmarks visualization if available
        if baseline_engine is not None and frame_img is not None:
            # baseline returns dict with keys: facial_stress, eye_closure, eyebrow_tension, jaw_tension
            result = baseline_engine.process_frame(frame_img)  # type: ignore
            mapped = {
                # Convert closure to openness
                "eye_openness": float(1.0 - float(result.get("eye_closure", 0.0))),
                "brow_tension": float(result.get("eyebrow_tension", 0.0)),
                "jaw_tension": float(result.get("jaw_tension", 0.0)),
                "head_motion": 0.0,
                "facial_stress_score": float(result.get("facial_stress", 0.0)),
            }
            return mapped
        # Otherwise call simple analyze_face if available
        if 'analyze_face' in globals() and analyze_face:
            inp = frame_img if frame_img is not None else frame_bytes
            if inp is None:
                return last_metrics or default
            result = analyze_face(inp)  # type: ignore
            for k in default.keys():
                if k not in result:
                    result[k] = 0.0
            # Maintain keys expected by frontend
            mapped = {
                "eye_openness": float(result.get("eye_openness", 0.0)),
                "brow_tension": float(result.get("brow_tension", 0.0)),
                "jaw_tension": float(result.get("jaw_tension", 0.0)),
                "head_motion": float(result.get("head_motion", 0.0)),
                "facial_stress_score": float(result.get("facial_stress_score", 0.0)),
            }
            return mapped
        # Fallback
        return last_metrics or default
    except Exception:
        return last_metrics or default


def _generate_overlay(frame_img):
    """Return base64 JPEG of frame with landmarks overlay if baseline available."""
    try:
        if baseline_engine is not None and frame_img is not None:
            result, processed = baseline_engine.process_frame_with_visualization(frame_img)  # type: ignore
            # Encode processed image to JPEG base64 data URL
            _, buf = cv2.imencode('.jpg', processed)
            b64 = base64.b64encode(buf.tobytes()).decode('ascii')
            return f"data:image/jpeg;base64,{b64}"
    except Exception:
        pass
    return None


@router.websocket("/face-analysis")
async def websocket_face_analysis(websocket: WebSocket):
    """
    Real-time face analysis WebSocket.

    Frontend → Backend:
    {
      "frame": "<base64>",
      "timestamp": 1736420000000
    }

    Backend → Frontend:
    {
      "timestamp": "2026-01-09T12:34:56.789Z",
      "eye_openness": 0.0,
      "brow_tension": 0.0,
      "jaw_tension": 0.0,
      "head_motion": 0.0,
      "facial_stress_score": 0.0
    }

    Performance rules:
    - Max 10 FPS processing (every ~100ms)
    - Skip frames if backlog builds up (process latest only)
    - Handle face-not-detected gracefully (zeros or last values)
    """
    await manager.connect(websocket)

    last_frame_payload: dict | None = None
    last_metrics: dict | None = None
    process_interval = 0.1  # 100ms
    running = True

    async def receiver_loop():
        nonlocal last_frame_payload, running
        try:
            while running:
                # Receive latest frame; overwrite to drop backlog
                msg = await websocket.receive_text()
                try:
                    payload = json.loads(msg)
                    # Expect keys: frame (base64), timestamp
                    if isinstance(payload, dict) and "frame" in payload:
                        last_frame_payload = payload
                except Exception:
                    # Ignore malformed messages
                    continue
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    async def processor_loop():
        nonlocal last_frame_payload, last_metrics, running
        try:
            while running:
                start = asyncio.get_event_loop().time()
                payload = last_frame_payload
                metrics = last_metrics
                if payload is not None:
                    img, raw = _decode_base64_image(str(payload.get("frame", "")))
                    metrics = _safe_analyze(img, raw, metrics)
                    last_metrics = metrics
                    message = {"timestamp": datetime.utcnow().isoformat(), **metrics}
                    overlay = _generate_overlay(img)
                    if overlay:
                        message["frame_overlay"] = overlay
                    await websocket.send_json(message)
                # Sleep to enforce ~10 FPS
                elapsed = asyncio.get_event_loop().time() - start
                await asyncio.sleep(max(0.0, process_interval - elapsed))
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    try:
        # Start receiver and processor concurrently
        recv_task = asyncio.create_task(receiver_loop())
        proc_task = asyncio.create_task(processor_loop())
        await asyncio.gather(recv_task, proc_task)
    except WebSocketDisconnect:
        running = False
        manager.disconnect(websocket)
    except Exception as e:
        running = False
        print(f"WebSocket /face-analysis error: {e}")
        manager.disconnect(websocket)


# How to test:
# 
# Python client:
#   pip install websockets
#   
#   import asyncio
#   import websockets
#   import json
#   
#   async def test_client():
#       uri = "ws://localhost:8000/ws/simulation"
#       async with websockets.connect(uri) as ws:
#           while True:
#               data = await ws.recv()
#               print(json.loads(data))
#   
#   asyncio.run(test_client())
#
# JavaScript client:
#   const ws = new WebSocket('ws://localhost:8000/ws/simulation');
#   ws.onmessage = (event) => {
#       const data = JSON.parse(event.data);
#       console.log('Stress:', data.stress_score, 'HR:', data.heart_rate);
#   };
