"""
Quick Test Script - Verify Normal & Elevated Heart Rates

This script tests that FastAPI now maps BOTH normal and elevated heart rates.
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"
HEARTBEAT_SIM_URL = "http://localhost:8001"

def test_connection():
    """Test 1: Check services are running"""
    print("=" * 60)
    print("TEST 1: Checking Service Connectivity")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ Main API (port 8000): {response.json()['status']}")
    except:
        print("❌ Main API not running. Start with: uvicorn main:app --port 8000 --reload")
        return False
    
    try:
        response = requests.get(f"{HEARTBEAT_SIM_URL}/health", timeout=2)
        print(f"✅ Heartbeat Sim (port 8001): {response.json()['status']}")
    except:
        print("❌ Heartbeat simulation not running. Start with: uvicorn heartbeat_sim:app --port 8001 --reload")
        return False
    
    return True


def test_start_simulation():
    """Test 2: Start heartbeat simulation"""
    print("\n" + "=" * 60)
    print("TEST 2: Starting Heartbeat Simulation")
    print("=" * 60)
    
    response = requests.post(f"{BASE_URL}/heartbeat/start")
    data = response.json()
    print(f"Response: {data}")
    
    if "error" in data:
        print("❌ Failed to start simulation")
        return False
    
    print("✅ Simulation started successfully")
    return True


def test_normal_heart_rates():
    """Test 3: Verify NORMAL heart rates are being sent"""
    print("\n" + "=" * 60)
    print("TEST 3: Collecting Normal Heart Rate Data (10 seconds)")
    print("=" * 60)
    print("Waiting for baseline data (this should show 60-80 BPM)...")
    
    normal_count = 0
    elevated_count = 0
    
    for i in range(20):  # 10 seconds at 0.5s intervals
        response = requests.get(f"{BASE_URL}/heartbeat/current")
        data = response.json()
        
        if "bpm" in data:
            bpm = data['bpm']
            stress = data['stress_level']
            
            if bpm < 85:
                normal_count += 1
                status_icon = "✅"
            else:
                elevated_count += 1
                status_icon = "⚠️"
            
            print(f"{status_icon} Reading {i+1}/20: BPM={bpm}, Stress={stress:.3f}")
        
        time.sleep(0.5)
    
    print(f"\nResults:")
    print(f"  Normal readings (< 85 BPM): {normal_count}/20")
    print(f"  Elevated readings (>= 85 BPM): {elevated_count}/20")
    
    if normal_count > 0:
        print("✅ SUCCESS: Normal heart rates ARE being sent!")
        return True
    else:
        print("❌ PROBLEM: Only elevated rates detected. Wait a bit longer.")
        return False


def test_elevated_heart_rates():
    """Test 4: Trigger stress and verify ELEVATED heart rates"""
    print("\n" + "=" * 60)
    print("TEST 4: Testing Elevated Heart Rates (Stress Event)")
    print("=" * 60)
    
    # Trigger stress test
    print("Triggering 5-second stress event...")
    response = requests.post(f"{BASE_URL}/heartbeat/stress-test")
    print(f"Response: {response.json()}")
    
    time.sleep(0.5)
    
    elevated_detected = False
    print("\nMonitoring for elevated heart rate...")
    
    for i in range(10):  # 5 seconds
        response = requests.get(f"{BASE_URL}/heartbeat/current")
        data = response.json()
        
        if "bpm" in data:
            bpm = data['bpm']
            stress = data['stress_level']
            
            if bpm >= 90:
                elevated_detected = True
                print(f"⚠️ Reading {i+1}/10: BPM={bpm} (ELEVATED!), Stress={stress:.3f}")
            else:
                print(f"✅ Reading {i+1}/10: BPM={bpm}, Stress={stress:.3f}")
        
        time.sleep(0.5)
    
    if elevated_detected:
        print("✅ SUCCESS: Elevated heart rates ARE being detected!")
        return True
    else:
        print("❌ PROBLEM: Stress event did not elevate heart rate")
        return False


def test_data_completeness():
    """Test 5: Verify all data fields are present"""
    print("\n" + "=" * 60)
    print("TEST 5: Checking Data Completeness")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/heartbeat/current")
    data = response.json()
    
    required_fields = ['timestamp', 'bpm', 'systolic', 'diastolic', 'stress_level', 'state']
    
    print("Checking required fields...")
    all_present = True
    for field in required_fields:
        if field in data:
            print(f"  ✅ {field}: {data[field]}")
        else:
            print(f"  ❌ {field}: MISSING!")
            all_present = False
    
    if all_present:
        print("✅ SUCCESS: All data fields present!")
        return True
    else:
        print("❌ PROBLEM: Some fields are missing")
        return False


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  FASTAPI HEARTBEAT INTEGRATION TEST SUITE              ║")
    print("║  Testing: Normal + Elevated Heart Rate Mapping        ║")
    print("╚" + "=" * 58 + "╝")
    
    tests_passed = 0
    tests_total = 5
    
    # Run all tests
    if test_connection():
        tests_passed += 1
    else:
        print("\n❌ Cannot proceed without services running.")
        return
    
    if test_start_simulation():
        tests_passed += 1
    
    if test_data_completeness():
        tests_passed += 1
    
    if test_normal_heart_rates():
        tests_passed += 1
    
    if test_elevated_heart_rates():
        tests_passed += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n✅✅✅ ALL TESTS PASSED! ✅✅✅")
        print("\nYour FastAPI now correctly maps BOTH:")
        print("  - Normal heart rates (60-80 BPM baseline)")
        print("  - Elevated heart rates (90-180 BPM during stress)")
        print("\nYour ML model can now access complete data!")
    else:
        print(f"\n⚠️ {tests_total - tests_passed} test(s) failed.")
        print("\nCheck the output above for details.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
        sys.exit(1)
