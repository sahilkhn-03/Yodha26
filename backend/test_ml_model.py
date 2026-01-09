"""
Test ML Model with ECG Simulator
Demonstrates the trained model classifying heart rate from your ECG simulator.
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"
SIMULATOR_URL = "http://localhost:8001"

print("=" * 70)
print("🧪 TESTING ML MODEL WITH ECG SIMULATOR")
print("=" * 70)

# Step 1: Check model status
print("\n1️⃣  Checking ML model status...")
try:
    response = requests.get(f"{BASE_URL}/api/ml/model/info")
    info = response.json()
    if info.get("status") == "loaded":
        print(f"   ✅ Model loaded successfully")
        print(f"      Accuracy: {info.get('accuracy', 0)*100:.1f}%")
        print(f"      Training samples: {info.get('training_samples')}")
    else:
        print(f"   ❌ Model not loaded")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    print(f"   Make sure backend is running: uvicorn main:app --reload")
    exit(1)

# Step 2: Start ECG simulator
print("\n2️⃣  Starting ECG simulator...")
try:
    response = requests.post(f"{SIMULATOR_URL}/simulation/start")
    if response.status_code == 200:
        print(f"   ✅ ECG simulator started")
    time.sleep(1)  # Let it generate some data
except Exception as e:
    print(f"   ⚠️  Simulator may already be running: {e}")

# Step 3: Get current heart rate from simulator and predict
print("\n3️⃣  Testing predictions with NORMAL heart rate...")
try:
    # Get current heart rate from simulator
    response = requests.get(f"{SIMULATOR_URL}/heartbeat/current")
    data = response.json()
    current_bpm = data['bpm']
    
    print(f"   📊 Current BPM from simulator: {current_bpm}")
    
    # Predict stress level
    pred_response = requests.post(
        f"{BASE_URL}/api/ml/predict",
        json={"bpm": current_bpm}
    )
    prediction = pred_response.json()
    
    print(f"   🤖 ML Prediction: {prediction['prediction']}")
    print(f"      Confidence: {prediction['confidence']*100:.1f}%")
    print(f"      Stress Score: {prediction['stress_score']*100:.1f}%")
    print(f"      Probabilities:")
    print(f"         Normal: {prediction['probabilities']['Normal']*100:.1f}%")
    print(f"         Stress: {prediction['probabilities']['Stress']*100:.1f}%")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 4: Trigger stress and test again
print("\n4️⃣  Triggering STRESS in simulator and testing...")
try:
    # Trigger stress
    requests.post(f"{SIMULATOR_URL}/simulation/stress-test")
    print(f"   ⚡ Stress triggered, waiting 2 seconds...")
    time.sleep(2)
    
    # Get stressed heart rate
    response = requests.get(f"{SIMULATOR_URL}/heartbeat/current")
    data = response.json()
    stressed_bpm = data['bpm']
    
    print(f"   📊 Stressed BPM from simulator: {stressed_bpm}")
    
    # Predict stress level
    pred_response = requests.post(
        f"{BASE_URL}/api/ml/predict",
        json={"bpm": stressed_bpm}
    )
    prediction = pred_response.json()
    
    print(f"   🤖 ML Prediction: {prediction['prediction']}")
    print(f"      Confidence: {prediction['confidence']*100:.1f}%")
    print(f"      Stress Score: {prediction['stress_score']*100:.1f}%")
    print(f"      Probabilities:")
    print(f"         Normal: {prediction['probabilities']['Normal']*100:.1f}%")
    print(f"         Stress: {prediction['probabilities']['Stress']*100:.1f}%")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 5: Test batch prediction with multiple readings
print("\n5️⃣  Testing BATCH prediction (simulating continuous monitoring)...")
try:
    # Collect 5 readings over time
    readings = []
    print(f"   📊 Collecting 5 readings...")
    
    for i in range(5):
        response = requests.get(f"{SIMULATOR_URL}/heartbeat/current")
        data = response.json()
        readings.append({"bpm": data['bpm']})
        print(f"      Reading {i+1}: {data['bpm']} BPM")
        time.sleep(0.5)
    
    # Batch predict
    pred_response = requests.post(
        f"{BASE_URL}/api/ml/predict/batch",
        json=readings
    )
    result = pred_response.json()
    
    print(f"\n   🤖 Batch Prediction Summary:")
    print(f"      Total readings: {result['summary']['total_readings']}")
    print(f"      Normal readings: {result['summary']['normal_readings']}")
    print(f"      Stress readings: {result['summary']['stress_readings']}")
    print(f"      Average stress score: {result['summary']['avg_stress_score']*100:.1f}%")
    print(f"      Overall assessment: {result['summary']['overall_assessment']}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 6: Manual test cases
print("\n6️⃣  Testing with MANUAL test cases...")
test_cases = [
    {"bpm": 70, "description": "Resting (Normal)"},
    {"bpm": 85, "description": "Slightly elevated (Normal)"},
    {"bpm": 110, "description": "Elevated (Borderline)"},
    {"bpm": 130, "description": "High (Stress)"}
]

for case in test_cases:
    try:
        pred_response = requests.post(
            f"{BASE_URL}/api/ml/predict",
            json={"bpm": case['bpm']}
        )
        prediction = pred_response.json()
        
        print(f"\n   BPM: {case['bpm']:3d} - {case['description']}")
        print(f"   → {prediction['prediction']:6s} (confidence: {prediction['confidence']*100:.0f}%)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETE!")
print("=" * 70)
print("\n📋 Usage Summary:")
print("   • Model predicts stress from heart rate (BPM)")
print("   • Normal: BPM < ~95, Stress: BPM > ~105")
print("   • Confidence indicates model certainty")
print("   • Stress score (0-1) shows stress probability")
print("\n🔗 API Endpoints:")
print("   • POST /api/ml/predict - Single prediction")
print("   • POST /api/ml/predict/batch - Multiple readings")
print("   • GET /api/ml/model/info - Model information")
print("\n💡 Integration:")
print("   Your ECG simulator → ML Model → Stress/Normal classification")
print("   Use this to analyze any heart rate data in real-time!")
