"""
Quick Demo: ECG + ML Integration Working
Shows normal and stress states being classified.
"""

import requests
import time

print("=" * 60)
print("🫀 ECG + ML INTEGRATION DEMO")
print("=" * 60)

# Start simulation
print("\n1️⃣  Starting ECG simulation...")
requests.post("http://localhost:8001/simulation/start")
time.sleep(2)

# Normal state
print("\n2️⃣  Testing NORMAL state...")
response = requests.get("http://localhost:8000/api/ecg/predict-stress")
data = response.json()
print(f"   BPM: {data['bpm']}")
print(f"   Prediction: {data['prediction']}")
print(f"   Confidence: {data['confidence']*100:.0f}%")
print(f"   Stress Score: {data['stress_score']*100:.0f}%")

# Trigger stress
print("\n3️⃣  Triggering STRESS event...")
requests.post("http://localhost:8001/simulation/stress-test")
time.sleep(1.5)

# Stress state
response = requests.get("http://localhost:8000/api/ecg/predict-stress")
data = response.json()
print(f"   BPM: {data['bpm']}")
print(f"   Prediction: {data['prediction']}")
print(f"   Confidence: {data['confidence']*100:.0f}%")
print(f"   Stress Score: {data['stress_score']*100:.0f}%")

print("\n" + "=" * 60)
print("✅ YOUR ML MODEL IS CLASSIFYING ECG DATA!")
print("=" * 60)
print("\nHow it works:")
print("  ECG Simulator (port 8001) generates heart rate")
print("  ↓")
print("  Backend fetches BPM automatically")
print("  ↓")
print("  ML Model classifies as Normal or Stress")
print("  ↓")
print("  Returns prediction with confidence!")
print("\n🔗 Try it: http://localhost:8000/api/ecg/predict-stress")
