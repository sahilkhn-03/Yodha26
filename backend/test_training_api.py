"""
Quick test script to verify the training data collection system.
Run this to test the API endpoints before using the web interface.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_api():
    print("🧪 Testing Training Data Collection API\n")
    
    # Test 1: Check stats (should be empty initially)
    print("1️⃣  Testing /api/training/stats...")
    response = requests.get(f"{BASE_URL}/api/training/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"   ✅ Stats endpoint working: {stats['total_samples']} samples")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Test 2: Record a normal heart rate sample
    print("\n2️⃣  Recording a NORMAL sample (BPM=72, stress=0.2)...")
    normal_data = {
        "bpm": 72,
        "stress_level": 0.2,
        "systolic": 120,
        "diastolic": 80,
        "notes": "Test normal sample"
    }
    response = requests.post(f"{BASE_URL}/api/training/record", json=normal_data)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Recorded: ID={result['id']}, BPM={result['bpm']}, Stress={result['stress_level']}")
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return
    
    # Test 3: Record a stressed heart rate sample
    print("\n3️⃣  Recording a STRESS sample (BPM=125, stress=0.85)...")
    stress_data = {
        "bpm": 125,
        "stress_level": 0.85,
        "systolic": 145,
        "diastolic": 95,
        "notes": "Test stress sample"
    }
    response = requests.post(f"{BASE_URL}/api/training/record", json=stress_data)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Recorded: ID={result['id']}, BPM={result['bpm']}, Stress={result['stress_level']}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Test 4: Check updated stats
    print("\n4️⃣  Checking updated stats...")
    response = requests.get(f"{BASE_URL}/api/training/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"   ✅ Total samples: {stats['total_samples']}")
        print(f"   ✅ Normal samples: {stats['normal_samples']}")
        print(f"   ✅ Stress samples: {stats['stress_samples']}")
        print(f"   ✅ Average BPM: {stats['avg_bpm']:.1f}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Test 5: Retrieve data
    print("\n5️⃣  Retrieving collected data...")
    response = requests.get(f"{BASE_URL}/api/training/data?limit=10")
    if response.status_code == 200:
        records = response.json()
        print(f"   ✅ Retrieved {len(records)} records")
        for record in records[:2]:  # Show first 2
            print(f"      - BPM={record['bpm']}, Stress={record['stress_level']}, Time={record['timestamp']}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Test 6: Test CSV export
    print("\n6️⃣  Testing CSV export...")
    response = requests.get(f"{BASE_URL}/api/training/export/csv")
    if response.status_code == 200:
        csv_lines = response.text.split('\n')
        print(f"   ✅ CSV export working: {len(csv_lines)} lines")
        print(f"   Header: {csv_lines[0]}")
        if len(csv_lines) > 1:
            print(f"   Sample: {csv_lines[1][:80]}...")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Open: http://localhost:8001/heartbeat_monitor.html")
    print("2. Click 'Start' to begin simulation")
    print("3. Enable 'Auto-Collection' checkbox")
    print("4. Click 'Stress' button to trigger stress events")
    print("5. Let it run for 5-10 minutes")
    print("6. Download CSV: http://localhost:8000/api/training/export/csv")
    print("\n🎯 Aim for 200+ samples with balanced normal/stress classes!")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend!")
        print("\nMake sure the server is running:")
        print("   cd D:\\Yodha26\\backend")
        print("   uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ ERROR: {e}")
