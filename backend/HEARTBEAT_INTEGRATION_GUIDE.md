# Heartbeat Integration Guide

## ✅ PROBLEM SOLVED: FastAPI Now Maps BOTH Normal AND Elevated Heart Rates

### What Was Wrong Before?
- WebSocket only sent artificial stress data
- No connection to real heartbeat simulation
- Model couldn't see normal baseline heart rates
- Only elevated rates were being sent

### What's Fixed Now?
- ✅ WebSocket fetches REAL heartbeat data from `heartbeat_sim.py`
- ✅ Includes BOTH normal (60-80 BPM) AND elevated (90-180 BPM) heart rates
- ✅ Blood pressure data included
- ✅ Real stress levels from simulation
- ✅ ML model can access ALL data via REST API or WebSocket

---

## 🚀 Quick Start

### Step 1: Start Heartbeat Simulation (Port 8001)
```bash
cd d:\Yodha26\backend
uvicorn heartbeat_sim:app --port 8001 --reload
```

### Step 2: Start Main FastAPI Backend (Port 8000)
```bash
cd d:\Yodha26\backend
uvicorn main:app --port 8000 --reload
```

### Step 3: Start the Simulation
```bash
# Using curl or browser
curl -X POST http://localhost:8000/heartbeat/start
```

---

## 📊 Data Flow Architecture

```
┌─────────────────────────┐
│  heartbeat_sim.py       │  Generates REAL heart rate data
│  (Port 8001)            │  - Normal: 60-80 BPM
│  - Baseline: 72 BPM     │  - Elevated: 90-180 BPM
│  - Stress events        │  - Blood pressure
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  main.py                │  Fetches & forwards data
│  (Port 8000)            │
│  /heartbeat/* endpoints │
└───────────┬─────────────┘
            │
            ├─────────────────────────┐
            ▼                         ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│  REST API Endpoints     │  │  WebSocket Stream       │
│  (For polling)          │  │  (Real-time)            │
│  GET /heartbeat/current │  │  ws://8000/ws/simulation│
└─────────────────────────┘  └─────────────────────────┘
            │                         │
            └────────────┬────────────┘
                         ▼
            ┌─────────────────────────┐
            │  Frontend / ML Model    │
            │  Gets ALL data:         │
            │  - Normal heart rates   │
            │  - Elevated heart rates │
            │  - Blood pressure       │
            │  - Stress levels        │
            └─────────────────────────┘
```

---

## 🔌 API Endpoints for ML Model

### 1. Get Current Heart Rate (Normal OR Elevated)

**GET** `http://localhost:8000/heartbeat/current`

**Response:**
```json
{
  "timestamp": "2026-01-09T12:34:56.789Z",
  "bpm": 72,                    // Can be 60-180 (normal OR elevated!)
  "systolic": 120,              // Blood pressure
  "diastolic": 80,
  "stress_level": 0.0,          // 0.0 = calm, 1.0 = stressed
  "state": "running"
}
```

**Python Example:**
```python
import requests

# Get current heartbeat (could be normal or elevated)
response = requests.get("http://localhost:8000/heartbeat/current")
data = response.json()

print(f"Heart Rate: {data['bpm']} BPM")
print(f"Stress Level: {data['stress_level']}")

if data['bpm'] < 80:
    print("✅ Normal heart rate")
else:
    print("⚠️ Elevated heart rate")
```

### 2. Start Simulation

**POST** `http://localhost:8000/heartbeat/start`

Starts generating heart rate data (normal baseline + stress events)

### 3. Trigger Stress Test

**POST** `http://localhost:8000/heartbeat/stress-test`

Forces elevated heart rate for 5 seconds (90-140 BPM), then returns to normal.

### 4. Check Simulation Status

**GET** `http://localhost:8000/heartbeat/status`

Returns whether simulation is running or stopped.

---

## 🌐 WebSocket for Real-Time Streaming

### Connect to WebSocket

**Endpoint:** `ws://localhost:8000/ws/simulation`

**Python Example:**
```python
import asyncio
import websockets
import json

async def monitor_heartbeat():
    uri = "ws://localhost:8000/ws/simulation"
    async with websockets.connect(uri) as websocket:
        print("Connected to heartbeat stream...")
        
        while True:
            data = await websocket.recv()
            heartbeat = json.loads(data)
            
            # You'll receive BOTH normal and elevated rates!
            print(f"BPM: {heartbeat['heart_rate']}, Status: {heartbeat['status']}")
            
            if heartbeat['status'] == 'normal':
                print("  ✅ Normal baseline heart rate")
            elif heartbeat['status'] == 'elevated':
                print("  ⚠️ Elevated heart rate detected!")

asyncio.run(monitor_heartbeat())
```

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/simulation');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    console.log(`Heart Rate: ${data.heart_rate} BPM`);
    console.log(`Status: ${data.status}`);
    console.log(`Stress Level: ${data.stress_score}`);
    console.log(`Blood Pressure: ${data.systolic_bp}/${data.diastolic_bp}`);
    
    // Send to ML model
    analyzeForStress(data);
};

ws.onopen = () => {
    console.log('Connected! Receiving ALL heart rate data...');
};
```

---

## 📈 Data Fields Explained

| Field | Description | Range | When It Changes |
|-------|-------------|-------|----------------|
| `heart_rate` | Current BPM | 60-180 | ✅ Changes for BOTH normal and elevated |
| `stress_score` | Stress level | 0.0-1.0 | Increases during stress events |
| `status` | Current state | normal, slightly_elevated, elevated, high_stress | Based on heart_rate |
| `systolic_bp` | Upper blood pressure | 90-180 mmHg | Increases with stress |
| `diastolic_bp` | Lower blood pressure | 60-110 mmHg | Increases with stress |
| `facial_stress` | Facial analysis | 0.0-1.0 | Simulated facial stress |

---

## 🧪 Testing the System

### Test 1: Verify Normal Heart Rates
```bash
# Start simulation
curl -X POST http://localhost:8000/heartbeat/start

# Check heart rate (should be around 60-80 BPM)
curl http://localhost:8000/heartbeat/current
```

### Test 2: Trigger Elevated Heart Rate
```bash
# Trigger stress test
curl -X POST http://localhost:8000/heartbeat/stress-test

# Immediately check heart rate (should be 90-140 BPM)
curl http://localhost:8000/heartbeat/current

# Wait 6 seconds and check again (should return to 60-80 BPM)
sleep 6
curl http://localhost:8000/heartbeat/current
```

### Test 3: WebSocket Stream
```bash
# Install websocat
# Windows: choco install websocat
# Mac: brew install websocat

# Connect and see live stream
websocat ws://localhost:8000/ws/simulation
```

You should see:
- Normal heart rates (60-80 BPM) most of the time
- Occasional stress events (90-180 BPM)
- Smooth transitions between normal and elevated

---

## 🤖 ML Model Integration Example

```python
import requests
import time

class StressDetector:
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.baseline_bpm = []
        
    def collect_baseline(self, duration=30):
        """Collect 30 seconds of baseline data"""
        print("Collecting baseline heart rate data...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            response = requests.get(f"{self.api_url}/heartbeat/current")
            data = response.json()
            
            if 'bpm' in data:
                self.baseline_bpm.append(data['bpm'])
                print(f"  Collected: {data['bpm']} BPM")
            
            time.sleep(0.5)
        
        self.baseline_avg = sum(self.baseline_bpm) / len(self.baseline_bpm)
        print(f"✅ Baseline established: {self.baseline_avg:.1f} BPM")
    
    def detect_stress(self):
        """Monitor for stress events"""
        print("\n🔍 Monitoring for stress...")
        
        while True:
            response = requests.get(f"{self.api_url}/heartbeat/current")
            data = response.json()
            
            if 'bpm' in data:
                current_bpm = data['bpm']
                stress_level = data['stress_level']
                
                # Compare to baseline
                deviation = current_bpm - self.baseline_avg
                
                if deviation > 15:
                    print(f"⚠️ STRESS DETECTED! BPM: {current_bpm} (Baseline: {self.baseline_avg:.1f})")
                    print(f"   Deviation: +{deviation:.1f} BPM")
                    print(f"   Stress Level: {stress_level:.2f}")
                else:
                    print(f"✅ Normal - BPM: {current_bpm}")
            
            time.sleep(1)

# Usage
detector = StressDetector()
detector.collect_baseline(duration=30)  # Get normal baseline
detector.detect_stress()                # Monitor for elevated rates
```

---

## 🎯 Key Takeaways

1. **✅ Both Normal and Elevated Rates**: The system now sends ALL heart rate data, not just elevated
2. **✅ Real Data Source**: Connected to `heartbeat_sim.py` for realistic simulation
3. **✅ Multiple Access Methods**: REST API (polling) or WebSocket (streaming)
4. **✅ Complete Data**: Heart rate, blood pressure, stress level, facial analysis
5. **✅ ML-Ready**: Perfect for training models on both normal and stressed states

---

## 🛠️ Troubleshooting

### Problem: "Cannot connect to heartbeat simulation"
**Solution:**
```bash
# Start the heartbeat simulation service first
cd d:\Yodha26\backend
uvicorn heartbeat_sim:app --port 8001 --reload
```

### Problem: "No data available"
**Solution:**
```bash
# Start the simulation
curl -X POST http://localhost:8000/heartbeat/start
```

### Problem: "Only seeing elevated heart rates"
**Solution:** This is now fixed! The WebSocket streams ALL data. If you only see elevated rates, the simulation might be in stress mode. Wait a few seconds for it to return to normal (60-80 BPM).

---

## 📚 Related Files

- `heartbeat_sim.py` - Core heartbeat simulation engine
- `routes_websocket.py` - Updated WebSocket routes with real data
- `main.py` - FastAPI main app with heartbeat endpoints
- `HEARTBEAT_README.md` - Detailed heartbeat simulation documentation

---

**Last Updated:** January 9, 2026  
**Status:** ✅ FULLY FUNCTIONAL - Normal & Elevated Heart Rates Both Mapped
