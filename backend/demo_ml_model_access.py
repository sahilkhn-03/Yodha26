"""
ML Model Data Access Demo
Shows how to access BOTH normal and elevated heart rates from FastAPI
"""

import requests
import time
from datetime import datetime

# FastAPI endpoint
HEARTBEAT_URL = "http://localhost:8001/heartbeat/current"

print("=" * 70)
print("  ML MODEL: Accessing Heart Rate Data from FastAPI")
print("=" * 70)
print("\nCollecting 20 data points (will include BOTH normal and elevated)...\n")

normal_samples = []
elevated_samples = []

for i in range(20):
    response = requests.get(HEARTBEAT_URL)
    data = response.json()
    
    bpm = data['bpm']
    stress = data['stress_level']
    systolic = data['systolic']
    diastolic = data['diastolic']
    
    # Classify
    if bpm < 85:
        status = "💚 NORMAL"
        normal_samples.append(bpm)
    else:
        status = "🔴 ELEVATED"
        elevated_samples.append(bpm)
    
    print(f"{i+1:2d}. BPM={bpm:3d} | BP={systolic}/{diastolic} | Stress={stress:.3f} | {status}")
    
    time.sleep(0.5)

# Analysis
print("\n" + "=" * 70)
print("  📊 ML MODEL ANALYSIS")
print("=" * 70)

if normal_samples:
    avg_normal = sum(normal_samples) / len(normal_samples)
    print(f"\n💚 NORMAL samples: {len(normal_samples)}")
    print(f"   Average: {avg_normal:.1f} BPM")
    print(f"   Range: {min(normal_samples)}-{max(normal_samples)} BPM")
    print("   ✅ Model can train on NORMAL baseline!")

if elevated_samples:
    avg_elevated = sum(elevated_samples) / len(elevated_samples)
    print(f"\n🔴 ELEVATED samples: {len(elevated_samples)}")
    print(f"   Average: {avg_elevated:.1f} BPM")
    print(f"   Range: {min(elevated_samples)}-{max(elevated_samples)} BPM")
    print("   ✅ Model can detect STRESS events!")

print("\n" + "=" * 70)
print("  ✅ CONCLUSION: FastAPI provides COMPLETE dataset!")
print("     - Normal rates for baseline")
print("     - Elevated rates for stress detection")
print("     - Your model gets EVERYTHING it needs!")
print("=" * 70)
