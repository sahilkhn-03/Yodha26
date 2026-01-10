"""
Virtual Person Heartbeat Simulation API
Fast API application that simulates realistic heartbeat data for ML model input.

Run with: uvicorn heartbeat_sim:app --reload
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import httpx
import asyncio
import random
import time
from datetime import datetime
from enum import Enum

# ============= Configuration =============

class SimulationState(str, Enum):
    """Simulation states"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class HeartbeatData(BaseModel):
    """Heartbeat data structure"""
    timestamp: str
    bpm: int
    systolic: int  # Systolic blood pressure (mmHg)
    diastolic: int  # Diastolic blood pressure (mmHg)
    stress_level: float  # Current stress level (0-1, internal)
    variability: float  # Heart rate variability
    state: str
    # Optional ML prediction fields (filled by simulator when available)
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    stress_score: Optional[float] = None
    

# ============= In-Memory Storage =============

class SimulationEngine:
    """
    Manages heartbeat simulation state and data generation.
    
    Why in-memory?
    - Fast access, no database overhead
    - Easy to replace with real sensor later
    - Perfect for hackathons
    """
    
    def __init__(self):
        self.state: SimulationState = SimulationState.STOPPED
        self.current_data: Optional[HeartbeatData] = None
        self.base_bpm: int = 72  # Resting heart rate
        self.current_bpm: float = 72.0
        self.stress_level: float = 0.0
        self.task: Optional[asyncio.Task] = None
        self.websocket_clients: List[WebSocket] = []
        # Internal random spike state (continuous random stress spikes)
        self.spike_active: bool = False
        self.spike_start_time: Optional[float] = None
        self.spike_duration: float = 0.0
        
        # Simulation parameters
        self.min_bpm = 60
        self.max_bpm = 180
        self.stress_threshold = 0.3  # When stress starts affecting HR
        self.spike_chance_per_tick = 0.03  # ~3% chance per tick to start a spike
        
    def reset(self):
        """Reset to baseline"""
        self.current_bpm = float(self.base_bpm)
        self.stress_level = 0.0
        
    def generate_heartbeat(self) -> HeartbeatData:
        """
        Generate realistic heartbeat data.
        
        Realistic patterns:
        1. Baseline: 60-80 bpm at rest (STAYS HERE unless stress button pressed)
        2. Variability: Small random fluctuations (±2-3 bpm)
        3. Stress response: ONLY when stress button pressed (90-140 bpm)
        4. Recovery: Slow return to baseline after stress button
        """
        
        # Random spike logic: start a spike randomly, spikes last at least 5s
        now = time.time()
        if not self.spike_active:
            if random.random() < self.spike_chance_per_tick:
                # Start a spike
                self.spike_active = True
                self.spike_start_time = now
                # Ensure at least 5s duration, allow up to 8s
                self.spike_duration = random.uniform(5.0, 8.0)
                # Set spike intensity
                self.stress_level = random.uniform(0.65, 0.95)
        else:
            elapsed = now - (self.spike_start_time or now)
            if elapsed < self.spike_duration:
                # Maintain spike (allow small fluctuations)
                self.stress_level = max(self.stress_level, random.uniform(0.6, 0.98))
            else:
                # End spike and start decay
                self.spike_active = False
                self.spike_start_time = None
                self.spike_duration = 0.0

        # Stress decay (return to baseline) when no spike
        if not self.spike_active:
            self.stress_level *= 0.92  # Decay to return to normal
            self.stress_level = max(0.0, self.stress_level)
        
        # Calculate target heart rate based on stress
        if self.stress_level > self.stress_threshold:
            # Stress increases heart rate significantly
            stress_factor = (self.stress_level - self.stress_threshold) / (1 - self.stress_threshold)
            target_bpm = self.base_bpm + (stress_factor * 60)  # Up to +60 bpm under stress (72 → 132)
        else:
            target_bpm = self.base_bpm
        
        # Faster transition when stressed, slower when calm (more realistic)
        transition_speed = 0.35 if self.spike_active else 0.08
        self.current_bpm += (target_bpm - self.current_bpm) * transition_speed
        
        # Add natural variability (breathing, minor fluctuations)
        variability = random.uniform(-2.5, 2.5)
        actual_bpm = self.current_bpm + variability
        
        # Clamp to realistic range
        actual_bpm = max(self.min_bpm, min(self.max_bpm, actual_bpm))
        
        # Calculate blood pressure (correlated with heart rate and stress)
        # Normal BP: 120/80, increases with stress
        base_systolic = 120
        base_diastolic = 80
        
        bp_increase = self.stress_level * 30  # Up to +30 mmHg under stress
        systolic = int(base_systolic + bp_increase + random.uniform(-5, 5))
        diastolic = int(base_diastolic + bp_increase * 0.5 + random.uniform(-3, 3))
        
        # Clamp to realistic ranges
        systolic = max(90, min(180, systolic))
        diastolic = max(60, min(110, diastolic))
        
        # Calculate heart rate variability (HRV) - higher when relaxed, lower when stressed
        hrv = round(abs(variability) * (1.0 - self.stress_level * 0.5), 3)
        
        # Create data packet
        data = HeartbeatData(
            timestamp=datetime.utcnow().isoformat(),
            bpm=int(round(actual_bpm)),
            systolic=systolic,
            diastolic=diastolic,
            stress_level=round(self.stress_level, 3),
            variability=hrv,
            state=self.state.value
        )
        
        self.current_data = data
        return data
    
    async def simulation_loop(self):
        """
        Background task that continuously generates heartbeat data.
        
        Runs at ~2 Hz (every 500ms) for realistic monitoring.
        """
        async with httpx.AsyncClient(timeout=5.0) as client:
            while self.state == SimulationState.RUNNING:
                # Generate new heartbeat data
                data = self.generate_heartbeat()

                # Call ML prediction endpoint (backend expected at localhost:8000)
                try:
                    ml_url = 'http://localhost:8000/api/ml/predict'
                    resp = await client.post(ml_url, json={"bpm": data.bpm})
                    if resp.status_code == 200:
                        j = resp.json()
                        # Attach ML fields to data
                        data.prediction = j.get('prediction')
                        data.confidence = float(j.get('confidence', 0.0))
                        data.stress_score = float(j.get('stress_score', 0.0))
                except Exception:
                    # If ML call fails, leave prediction fields None
                    pass

                # Broadcast to all WebSocket clients
                await self.broadcast_to_websockets(data)

                # Wait before next update (4 Hz = 250ms for faster ECG)
                await asyncio.sleep(0.25)
    
    async def broadcast_to_websockets(self, data: HeartbeatData):
        """Send data to all connected WebSocket clients"""
        disconnected = []
        for client in self.websocket_clients:
            try:
                await client.send_json(data.dict())
            except:
                disconnected.append(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            self.websocket_clients.remove(client)


# Global simulation engine instance
engine = SimulationEngine()


# ============= FastAPI Application =============

app = FastAPI(
    title="Virtual Heartbeat Simulation API",
    description="Simulates realistic heartbeat data for ML model training",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        - Service status
        - Simulation state
        - Uptime info
    """
    return {
        "status": "healthy",
        "service": "Heartbeat Simulation API",
        "simulation_state": engine.state.value,
        "base_bpm": engine.base_bpm,
        "websocket_clients": len(engine.websocket_clients)
    }


@app.post("/simulation/start")
async def start_simulation():
    """
    Start heartbeat simulation.
    
    Creates background task that continuously generates heartbeat data.
    Safe to call multiple times (won't create duplicate tasks).
    """
    if engine.state == SimulationState.RUNNING:
        return JSONResponse(
            status_code=200,
            content={
                "message": "Simulation already running",
                "state": engine.state.value
            }
        )
    
    # Reset to baseline
    engine.reset()
    engine.state = SimulationState.RUNNING
    
    # Start background simulation loop
    engine.task = asyncio.create_task(engine.simulation_loop())
    
    return {
        "message": "Simulation started",
        "state": engine.state.value,
        "base_bpm": engine.base_bpm
    }


@app.post("/simulation/stress-test")
async def stress_test():
    """
    Trigger manual stress test.
    
    Simulates a stress event for exactly 5 seconds, then returns to normal.
    Heart rate will fluctuate during the stress period.
    """
    if engine.state != SimulationState.RUNNING:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Simulation not running",
                "message": "Simulation not running"
            }
        )

    # Trigger a deterministic 5-second spike
    engine.spike_active = True
    engine.spike_start_time = time.time()
    engine.spike_duration = 5.0
    engine.stress_level = max(engine.stress_level, 0.75)

    return {
        "message": "Stress test initiated (5s spike)",
        "duration_seconds": 5,
        "state": engine.state.value
    }


@app.post("/simulation/stop")
async def stop_simulation():
    """
    Stop heartbeat simulation.
    
    Gracefully stops the background task and resets state.
    """
    if engine.state == SimulationState.STOPPED:
        return JSONResponse(
            status_code=200,
            content={
                "message": "Simulation already stopped",
                "state": engine.state.value
            }
        )
    
    engine.state = SimulationState.STOPPED
    
    # Cancel background task if running
    if engine.task and not engine.task.done():
        engine.task.cancel()
        try:
            await engine.task
        except asyncio.CancelledError:
            pass
    
    return {
        "message": "Simulation stopped",
        "state": engine.state.value
    }


@app.get("/heartbeat/current", response_model=HeartbeatData)
async def get_current_heartbeat():
    """
    Get latest simulated heartbeat data.
    
    Returns:
        Latest heartbeat measurement with:
        - timestamp: ISO format
        - bpm: Current heart rate
        - variability: Heart rate variability (0-1)
        - stress_level: Current stress level (0-1)
        - state: Simulation state
    
    Use case:
        - ML model polling for latest data
        - Dashboard displays
        - Health monitoring
    """
    if engine.current_data is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": "No data available",
                "message": "Start simulation first using POST /simulation/start"
            }
        )
    
    return engine.current_data


@app.websocket("/ws/heartbeat")
async def websocket_heartbeat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time heartbeat streaming.
    
    Endpoint: ws://localhost:8001/ws/heartbeat
    
    Streams heartbeat data at ~2 Hz (every 500ms).
    Data is pushed from the simulation loop via broadcast_to_websockets().
    
    Client example:
        const ws = new WebSocket('ws://localhost:8001/ws/heartbeat');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(`BPM: ${data.bpm}, Stress: ${data.stress_level}`);
        };
    
    Perfect for:
        - Real-time dashboards
        - Live monitoring displays
        - Continuous model input
    """
    await websocket.accept()
    engine.websocket_clients.append(websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to heartbeat stream",
            "state": engine.state.value,
            "base_bpm": engine.base_bpm
        })
        
        # Keep connection alive - wait for disconnect or close message
        # Data is pushed by broadcast_to_websockets() in simulation loop
        while True:
            try:
                # Wait for disconnection or client ping/pong
                # receive_text() will raise WebSocketDisconnect when client closes
                message = await websocket.receive_text()
                
                # Optional: Handle client commands
                if message == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                break
            except Exception:
                # Any other error means connection is broken
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        # Log unexpected errors but don't crash
        print(f"WebSocket error: {e}")
    finally:
        # Clean up on disconnect
        if websocket in engine.websocket_clients:
            engine.websocket_clients.remove(websocket)


# ============= Utility Endpoints =============

@app.get("/", response_class=HTMLResponse)
async def live_monitor():
    """
    Live ECG-style heartbeat monitor dashboard.
    
    Opens in browser at: http://localhost:8001/
    
    Real-time visualization with ECG waveform display.
    API accessible at /heartbeat/current for ML models.
    """
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ECG Heartbeat Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #000000;
            margin-bottom: 30px;
            font-size: 42px;
            text-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            letter-spacing: 2px;
        }
        .monitor {
            background: #e5e5e5;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            border: 2px solid #999999;
        }
        
        /* ECG Display */
        .ecg-container {
            background: #f5f5f5;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            border: 2px solid #999999;
            position: relative;
            overflow: hidden;
        }
        .ecg-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .ecg-title {
            color: #000000;
            font-size: 20px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .bpm-live {
            font-size: 48px;
            font-weight: bold;
            color: #000000;
            text-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
        }
        .bpm-unit {
            font-size: 20px;
            color: #888888;
            margin-left: 10px;
        }
        
        /* ECG Canvas */
        #ecgCanvas {
            width: 100%;
            height: 200px;
            background: #ffffff;
            border-radius: 8px;
            display: block;
        }
        
        /* Metrics Grid */
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric {
            background: linear-gradient(135deg, #e5e5e5 0%, #f5f5f5 100%);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid #999999;
            transition: transform 0.3s ease;
        }
        .metric:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        .metric-value {
            font-size: 48px;
            font-weight: bold;
            color: #000000;
            margin-bottom: 5px;
            text-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .metric-label {
            font-size: 14px;
            color: #888888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Blood Pressure Display */
        .bp-display {
            display: flex;
            align-items: baseline;
            justify-content: center;
            gap: 5px;
        }
        .bp-value {
            font-size: 48px;
            font-weight: bold;
            color: #000000;
            text-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .bp-separator {
            font-size: 36px;
            color: #999999;
        }
        
        /* Controls */
        .controls {
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }
        button {
            flex: 1;
            padding: 18px;
            border: 2px solid #000000;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            background: transparent;
            color: #000000;
        }
        button:hover {
            background: #000000;
            color: #ffffff;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
            transform: translateY(-2px);
        }
        .btn-start { border-color: #333333; color: #333333; }
        .btn-stress { border-color: #777777; color: #777777; }
        .btn-stop { border-color: #999999; color: #999999; }
        .btn-start:hover { background: #333333; color: #ffffff; }
        .btn-stress:hover { background: #777777; color: #ffffff; }
        .btn-stop:hover { background: #999999; color: #000000; }
        .btn-stress:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            background: rgba(136, 136, 136, 0.1);
        }
        
        /* Status */
        .status {
            text-align: center;
            padding: 20px;
            border-radius: 12px;
            margin-top: 25px;
            font-weight: 600;
            font-size: 16px;
            border: 2px solid;
        }
        .status-stopped { 
            background: rgba(102, 102, 102, 0.1);
            color: #777777;
            border-color: #999999;
        }
        .status-running { 
            background: rgba(0, 0, 0, 0.05);
            color: #000000;
            border-color: #333333;
        }
        .status-connecting { 
            background: rgba(136, 136, 136, 0.1);
            color: #555555;
            border-color: #777777;
        }
        
        /* Data Log */
        .data-log {
            max-height: 150px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            background: #ffffff;
            color: #333333;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border: 2px solid #999999;
        }
        .log-entry {
            padding: 3px 0;
            border-bottom: 1px solid #cccccc;
        }
        
        /* Info Panel */
        .info-panel {
            background: #e5e5e5;
            border-radius: 20px;
            padding: 30px;
            border: 2px solid #999999;
        }
        .info-panel h2 {
            color: #000000;
            margin-bottom: 15px;
            text-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .info-panel p {
            color: #777777;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        .api-endpoint {
            background: #f5f5f5;
            padding: 10px 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #333333;
            margin: 10px 0;
            border: 1px solid #999999;
        }
        
        /* Pulse animation */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .pulsing {
            animation: pulse 1s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ LIVE ECG MONITOR</h1>
        
        <div class="monitor">
            <!-- ECG Waveform Display -->
            <div class="ecg-container">
                <div class="ecg-header">
                    <div class="ecg-title">Electrocardiogram</div>
                    <div>
                        <span class="bpm-live" id="bpmLive">--</span>
                        <span class="bpm-unit">BPM</span>
                    </div>
                </div>
                <canvas id="ecgCanvas"></canvas>
            </div>
            
            <!-- Vital Signs -->
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value" id="heartRate">--</div>
                    <div class="metric-label">Heart Rate (BPM)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="mlPrediction">--</div>
                    <div class="metric-label">ML Prediction (Stress)</div>
                </div>
                <div class="metric">
                    <div class="bp-display">
                        <span class="bp-value" id="systolic">--</span>
                        <span class="bp-separator">/</span>
                        <span class="bp-value" id="diastolic">--</span>
                    </div>
                    <div class="metric-label">Blood Pressure (mmHg)</div>
                </div>
            </div>
            
            <div id="status" class="status status-running">
                🟢 LIVE MONITORING ACTIVE (auto)
            </div>
            
            <div class="data-log" id="dataLog">
                <div class="log-entry">📊 Awaiting connection...</div>
            </div>
        </div>
        
        <div class="info-panel">
            <h2>📡 API ACCESS FOR ML MODELS</h2>
            <p><strong>Real-time WebSocket Stream:</strong></p>
            <div class="api-endpoint">ws://localhost:8001/ws/heartbeat</div>
            
            <p><strong>HTTP Polling Endpoint:</strong></p>
            <div class="api-endpoint">GET http://localhost:8001/heartbeat/current</div>
            
            <p><strong>Set Normal/Baseline Heart Rate:</strong></p>
            <div class="api-endpoint">POST http://localhost:8001/input/set-normal-heartrate?baseline_bpm=72&reason=profile</div>
            
            <p><strong>Get Baseline Heart Rate:</strong></p>
            <div class="api-endpoint">GET http://localhost:8001/heartbeat/baseline</div>
            
            <p><strong>Video Stress Input (Facial Analysis):</strong></p>
            <div class="api-endpoint">POST http://localhost:8001/input/video-stress?stress_detected=true&intensity=0.7</div>
            
            <p><strong>Audio Stress Input (Voice Analysis):</strong></p>
            <div class="api-endpoint">POST http://localhost:8001/input/audio-stress?stress_detected=true&intensity=0.6</div>
            
            <p><strong>Combined Multi-Modal Input:</strong></p>
            <div class="api-endpoint">POST http://localhost:8001/input/combined-stress</div>
            
            <p><strong>Returns JSON:</strong></p>
            <div class="api-endpoint">{"timestamp": "...", "bpm": 72, "systolic": 120, "diastolic": 80}</div>
            
            <p style="margin-top: 20px; font-size: 14px; color: #000000;">
                💡 <strong>PUBLIC API:</strong> Any ML model can access this data at any time via the endpoints above.
            </p>
            <p style="margin-top: 10px; font-size: 13px; color: #777777;">
                ⚡ <strong>STRESS TRIGGERS:</strong> Stress occurs randomly (5-8% chance per update). 
                ML models analyzing video/audio can trigger additional stress via input endpoints.
            </p>
        </div>
    </div>

    <script>
        let ws = null;
        let updateCount = 0;
        const maxLogEntries = 30;
        const API_BASE = window.location.origin;
        
        // ECG Canvas Setup
        const canvas = document.getElementById('ecgCanvas');
        const ctx = canvas.getContext('2d');
        let ecgData = [];
        const maxDataPoints = 120;  // Reduced for faster scroll
        let animationId = null;
        
        // Set canvas size
        function resizeCanvas() {
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Generate ECG waveform based on BPM
        function generateECGPoint(bpm, index) {
            const beatsPerSecond = bpm / 60;
            // Keep consistent samples for proper waveform rendering
            const samplesPerBeat = 25;
            const beatProgress = (index % samplesPerBeat) / samplesPerBeat;
            
            // Amplitude scales UP significantly with BPM (higher HR = much bigger waves)
            // 60 BPM: scale 1.0, 90 BPM: scale 2.0, 120 BPM: scale 3.0, 150 BPM: scale 4.0
            const amplitudeScale = 0.5 + (bpm / 30);
            
            let amplitude = 0;
            if (beatProgress < 0.1) {
                // P wave
                amplitude = Math.sin(beatProgress * 10 * Math.PI) * 35 * amplitudeScale;
            } else if (beatProgress < 0.3) {
                // QRS complex
                if (beatProgress < 0.2) {
                    amplitude = -50 * amplitudeScale;
                } else if (beatProgress < 0.25) {
                    amplitude = 150 * amplitudeScale; // R peak - scales dramatically
                } else {
                    amplitude = -45 * amplitudeScale;
                }
            } else if (beatProgress < 0.5) {
                // T wave
                amplitude = Math.sin((beatProgress - 0.3) * 5 * Math.PI) * 40 * amplitudeScale;
            }
            
            // Noise scales with BPM
            const noiseLevel = 3 + (bpm / 50);
            return amplitude + (Math.random() * 2 - 1) * noiseLevel;
        }
        
        // Draw ECG waveform
        function drawECG() {
            ctx.fillStyle = '#fff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw grid
            ctx.strokeStyle = '#dddddd';
            ctx.lineWidth = 1;
            for (let x = 0; x < canvas.width; x += 20) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }
            for (let y = 0; y < canvas.height; y += 20) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }
            
            // Draw waveform
            if (ecgData.length > 1) {
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 2;
                ctx.shadowBlur = 10;
                ctx.shadowColor = '#000000';
                ctx.beginPath();
                
                const xStep = canvas.width / maxDataPoints;
                const yCenter = canvas.height / 2;
                
                for (let i = 0; i < ecgData.length; i++) {
                    const x = i * xStep;
                    const y = yCenter - ecgData[i];
                    
                    if (i === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                }
                ctx.stroke();
                ctx.shadowBlur = 0;
            }
            
            animationId = requestAnimationFrame(drawECG);
        }

        // Controls removed — simulation runs continuously on server.

        function connectWebSocket() {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/heartbeat`);
            
            ws.onopen = () => {
                addLog('🔗 WebSocket connected');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'connected') {
                    addLog('📡 Monitor online - receiving data');
                    return;
                }
                
                updateCount++;
                
                // Update displays
                document.getElementById('bpmLive').textContent = data.bpm;
                document.getElementById('heartRate').textContent = data.bpm;
                document.getElementById('systolic').textContent = data.systolic;
                document.getElementById('diastolic').textContent = data.diastolic;
                
                // Update ECG waveform
                const ecgPoint = generateECGPoint(data.bpm, updateCount);
                ecgData.push(ecgPoint);
                if (ecgData.length > maxDataPoints) {
                    ecgData.shift();
                }
                
                // Update ML prediction display if available
                const predLabel = data.prediction || '--';
                const predScore = (data.stress_score !== undefined && data.stress_score !== null) ? (data.stress_score).toFixed(3) : '--';
                document.getElementById('mlPrediction').textContent = `${predLabel} (${predScore})`;

                // Log high stress events
                if (data.stress_level > 0.5) {
                    addLog(`🔴 ELEVATED: HR=${data.bpm} BP=${data.systolic}/${data.diastolic}`);
                }
            };
            
            ws.onerror = () => {
                updateStatus('stopped', '⚫ Connection Error');
                addLog('❌ WebSocket error');
            };
            
            ws.onclose = () => {
                updateStatus('stopped', '⚫ Disconnected');
                addLog('🔌 Monitor disconnected');
            };
        }

        function updateStatus(state, text) {
            const statusEl = document.getElementById('status');
            statusEl.textContent = text;
            statusEl.className = `status status-${state}`;
        }

        function addLog(message) {
            const logEl = document.getElementById('dataLog');
            const timestamp = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = `[${timestamp}] ${message}`;
            logEl.insertBefore(entry, logEl.firstChild);
            while (logEl.children.length > maxLogEntries) {
                logEl.removeChild(logEl.lastChild);
            }
        }

        // Auto-connect on load (simulation runs on server automatically)
        window.onload = async () => {
            try {
                updateStatus('running', '🟢 LIVE MONITORING ACTIVE');
                addLog('📊 Connecting to live session...');
                connectWebSocket();
                drawECG();
            } catch (error) {
                console.log('Startup connection failed:', error);
            }
        };
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.get("/data-collection")
async def data_collection_interface():
    """
    Data collection interface with auto-labeling for ML training.
    
    Opens at: http://localhost:8001/data-collection
    
    Allows you to collect labeled heart rate data for training ML models.
    """
    with open("heartbeat_monitor.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.post("/input/video-stress")
async def video_stress_input(stress_detected: bool, intensity: float = 0.5):
    """
    Input flag from video analysis (facial expression, body language).
    
    Args:
        stress_detected: Boolean flag indicating stress detected in video
        intensity: Stress intensity (0.0 to 1.0)
    
    Use case:
        - ML model analyzing facial expressions
        - Body language detection
        - Visual stress indicators
    """
    if intensity < 0 or intensity > 1:
        return JSONResponse(
            status_code=400,
            content={"error": "intensity must be between 0 and 1"}
        )
    
    if stress_detected:
        engine.stress_level = max(engine.stress_level, intensity)
    
    return {
        "message": "Video input processed",
        "stress_detected": stress_detected,
        "current_stress_level": engine.stress_level,
        "current_bpm": int(engine.current_bpm) if engine.current_data else None
    }


@app.post("/input/audio-stress")
async def audio_stress_input(stress_detected: bool, intensity: float = 0.5):
    """
    Input flag from audio analysis (voice tone, speech patterns).
    
    Args:
        stress_detected: Boolean flag indicating stress detected in audio
        intensity: Stress intensity (0.0 to 1.0)
    
    Use case:
        - ML model analyzing voice stress
        - Speech pattern analysis
        - Vocal stress indicators
    """
    if intensity < 0 or intensity > 1:
        return JSONResponse(
            status_code=400,
            content={"error": "intensity must be between 0 and 1"}
        )
    
    if stress_detected:
        engine.stress_level = max(engine.stress_level, intensity)
    
    return {
        "message": "Audio input processed",
        "stress_detected": stress_detected,
        "current_stress_level": engine.stress_level,
        "current_bpm": int(engine.current_bpm) if engine.current_data else None
    }


@app.post("/input/combined-stress")
async def combined_stress_input(
    video_stress: bool = False,
    audio_stress: bool = False,
    video_intensity: float = 0.5,
    audio_intensity: float = 0.5
):
    """
    Combined input from both video and audio analysis.
    Takes the maximum stress level from both sources.
    
    Args:
        video_stress: Stress detected in video
        audio_stress: Stress detected in audio
        video_intensity: Video stress intensity (0.0 to 1.0)
        audio_intensity: Audio stress intensity (0.0 to 1.0)
    
    Use case:
        - Multi-modal stress detection
        - Combined ML model outputs
        - Comprehensive stress assessment
    """
    if video_intensity < 0 or video_intensity > 1:
        return JSONResponse(
            status_code=400,
            content={"error": "video_intensity must be between 0 and 1"}
        )
    if audio_intensity < 0 or audio_intensity > 1:
        return JSONResponse(
            status_code=400,
            content={"error": "audio_intensity must be between 0 and 1"}
        )
    
    # Take maximum stress from both sources
    max_intensity = 0.0
    if video_stress:
        max_intensity = max(max_intensity, video_intensity)
    if audio_stress:
        max_intensity = max(max_intensity, audio_intensity)
    
    if max_intensity > 0:
        engine.stress_level = max(engine.stress_level, max_intensity)
    
    return {
        "message": "Combined input processed",
        "video_stress": video_stress,
        "audio_stress": audio_stress,
        "applied_intensity": max_intensity,
        "current_stress_level": engine.stress_level,
        "current_bpm": int(engine.current_bpm) if engine.current_data else None
    }


@app.post("/input/set-normal-heartrate")
async def set_normal_heartrate(baseline_bpm: int, reason: str = "manual"):
    """
    Set normal/baseline heart rate from external input.
    This is the resting heart rate when there's no stress.
    
    Args:
        baseline_bpm: Normal resting heart rate (40-120 BPM)
        reason: Source of the input ("profile", "calibration", "ml_model", "manual")
    
    Use case:
        - User profile (age, fitness level)
        - Initial calibration from actual measurement
        - ML model estimation from historical data
        - Different person simulation
    
    Examples:
        - Athlete: 45-60 BPM
        - Average adult: 60-80 BPM
        - Sedentary/anxious: 80-100 BPM
    """
    if baseline_bpm < 40 or baseline_bpm > 120:
        return JSONResponse(
            status_code=400,
            content={"error": "baseline_bpm must be between 40 and 120"}
        )
    
    old_baseline = engine.base_bpm
    engine.base_bpm = baseline_bpm
    engine.current_bpm = float(baseline_bpm)  # Reset current to new baseline
    
    # Determine profile
    if baseline_bpm < 60:
        profile = "athlete"
    elif baseline_bpm < 80:
        profile = "average"
    elif baseline_bpm < 100:
        profile = "above_average"
    else:
        profile = "elevated"
    
    return {
        "message": "Normal heart rate updated",
        "old_baseline_bpm": old_baseline,
        "new_baseline_bpm": baseline_bpm,
        "profile": profile,
        "reason": reason,
        "current_bpm": int(engine.current_bpm) if engine.current_data else baseline_bpm
    }


@app.get("/heartbeat/baseline")
async def get_baseline_heartrate():
    """
    Get current baseline/normal heart rate.
    
    Returns the resting heart rate (no stress baseline).
    Useful for ML models to understand the person's normal state.
    """
    return {
        "baseline_bpm": engine.base_bpm,
        "current_bpm": int(engine.current_bpm) if engine.current_data else engine.base_bpm,
        "current_stress_level": engine.stress_level,
        "profile": "athlete" if engine.base_bpm < 60 else "average" if engine.base_bpm < 80 else "elevated",
        "state": engine.state.value
    }


@app.post("/simulation/set-baseline")
async def set_baseline_bpm(baseline_bpm: int = 72):
    """
    Set baseline heart rate.
    
    Args:
        baseline_bpm: Resting heart rate (60-100 recommended)
    
    Use case:
        - Simulate different person profiles (athlete vs sedentary)
        - Testing different baseline scenarios
    """
    if baseline_bpm < 40 or baseline_bpm > 120:
        return JSONResponse(
            status_code=400,
            content={"error": "baseline_bpm must be between 40 and 120"}
        )
    
    engine.base_bpm = baseline_bpm
    
    return {
        "message": "Baseline heart rate updated",
        "baseline_bpm": baseline_bpm,
        "profile": "athlete" if baseline_bpm < 60 else "average" if baseline_bpm < 80 else "elevated"
    }


# ============= Startup Event =============

@app.on_event("startup")
async def startup_event():
    """Initialize simulation on startup"""
    print("="*60)
    print("🫀 Virtual Heartbeat Simulation API (auto-starting simulation)")
    print("="*60)
    print("Ready to simulate realistic heartbeat data!")
    # Auto-start continuous simulation on startup
    if engine.state != SimulationState.RUNNING:
        engine.reset()
        engine.state = SimulationState.RUNNING
        engine.task = asyncio.create_task(engine.simulation_loop())
        print("✅ Simulation auto-started")
    print("\nQuick Info:")
    print("  - WebSocket stream: ws://localhost:8001/ws/heartbeat")
    print("  - HTTP current:  GET http://localhost:8001/heartbeat/current")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    if engine.state == SimulationState.RUNNING:
        engine.state = SimulationState.STOPPED
        if engine.task:
            engine.task.cancel()
    print("Simulation stopped")


# ============= Run Instructions =============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "heartbeat_sim:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# How to use:
#
# 1. Start server:
#    uvicorn heartbeat_sim:app --reload
#
# 2. Start simulation:
#    curl -X POST http://localhost:8000/simulation/start
#
# 3. Get current heartbeat:
#    curl http://localhost:8000/heartbeat/current
#
# 4. Test WebSocket (Python):
#    pip install websockets
#    
#    import asyncio
#    import websockets
#    import json
#    
#    async def test():
#        async with websockets.connect('ws://localhost:8000/ws/heartbeat') as ws:
#            while True:
#                data = json.loads(await ws.recv())
#                print(f"BPM: {data['bpm']}, Stress: {data['stress_level']}")
#    
#    asyncio.run(test())
#
# 5. Trigger stress (optional):
#    curl -X POST "http://localhost:8000/simulation/trigger-stress?stress_level=0.8"
#
# 6. Stop simulation:
#    curl -X POST http://localhost:8000/simulation/stop
