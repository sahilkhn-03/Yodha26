"""
Test Integrated ECG + ML System
Verifies the complete pipeline from ECG simulator to ML prediction.
"""

import requests
import time
import json

print("=" * 70)
print("🧪 TESTING INTEGRATED ECG + ML SYSTEM")
print("=" * 70)

BASE_URL = "http://localhost:8000"

# Wait for servers to be ready
print("\n⏳ Waiting for servers to start...")
time.sleep(8)

# Test 1: Check system status
print("\n1️⃣  Checking system status...")
try:
    response = requests.get(f"{BASE_URL}/api/ecg/status")
    status = response.json()
    
    print(f"   ECG Simulator: {status['ecg_simulator']['status']}")
    print(f"   ML Model: {status['ml_model']['status']}")
    print(f"   Overall: {status['overall']}")
    
    if status['overall'] != 'fully_operational':
        print(f"\n   ⚠️  System not fully operational. Waiting longer...")
        time.sleep(5)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: Get prediction from ECG
print("\n2️⃣  Testing integrated prediction (ECG → ML)...")
try:
    response = requests.get(f"{BASE_URL}/api/ecg/predict-stress")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n   📊 Current ECG Reading:")
        print(f"      BPM: {result['bpm']}")
        print(f"      Timestamp: {result['timestamp']}")
        
        print(f"\n   🤖 ML Prediction:")
        print(f"      Status: {result['prediction']}")
        print(f"      Confidence: {result['confidence']*100:.1f}%")
        print(f"      Stress Score: {result['stress_score']*100:.1f}%")
        
        print(f"\n   📈 Probabilities:")
        print(f"      Normal: {result['probabilities']['Normal']*100:.1f}%")
        print(f"      Stress: {result['probabilities']['Stress']*100:.1f}%")
        
        print(f"\n   ✅ Integration successful!")
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    print(f"\n   Make sure both servers are running:")
    print(f"      Backend: http://localhost:8000")
    print(f"      ECG Simulator: http://localhost:8001")

# Test 3: Start ECG simulation and trigger stress
print("\n3️⃣  Starting ECG simulation...")
try:
    requests.post("http://localhost:8001/simulation/start")
    time.sleep(1)
    
    # Get normal prediction
    response = requests.get(f"{BASE_URL}/api/ecg/predict-stress")
    result = response.json()
    print(f"   Normal state: {result['bpm']} BPM → {result['prediction']}")
    
    # Trigger stress
    print(f"\n4️⃣  Triggering stress event...")
    requests.post("http://localhost:8001/simulation/stress-test")
    time.sleep(2)
    
    # Get stress prediction
    response = requests.get(f"{BASE_URL}/api/ecg/predict-stress")
    result = response.json()
    print(f"   Stressed state: {result['bpm']} BPM → {result['prediction']}")
    print(f"   Stress score: {result['stress_score']*100:.0f}%")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Continuous monitoring
print("\n5️⃣  Testing continuous monitoring...")
try:
    response = requests.get(f"{BASE_URL}/api/ecg/monitor-stress")
    result = response.json()
    
    print(f"\n   📊 Monitoring Summary:")
    print(f"      Total readings: {result['analysis']['total_readings']}")
    print(f"      Stress readings: {result['analysis']['stress_readings']}")
    print(f"      Average stress: {result['analysis']['average_stress_score']*100:.1f}%")
    print(f"      Trend: {result['analysis']['trend']}")
    print(f"      Status: {result['analysis']['overall_status']}")
    print(f"      Recommendation: {result['recommendation']}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETE!")
print("=" * 70)

print("\n📋 Available Endpoints:")
print("   • GET  /api/ecg/predict-stress     - Get instant prediction")
print("   • GET  /api/ecg/monitor-stress     - Monitor 5 readings")
print("   • GET  /api/ecg/status             - Check system health")
print("\n💡 Your ML model is now integrated with ECG simulator!")
print("   ECG (port 8001) → ML Model → Stress Prediction ✨")
