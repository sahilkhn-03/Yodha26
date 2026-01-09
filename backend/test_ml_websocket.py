"""
Test ML Stress Analysis WebSocket
=================================
Simple test script to verify the ML model integration
"""

import asyncio
import websockets
import json
import base64
from pathlib import Path

async def test_ml_stress_websocket():
    uri = "ws://localhost:8000/ws/ml-stress-analysis"
    
    print("Connecting to ML stress analysis WebSocket...")
    async with websockets.connect(uri) as websocket:
        print("✅ Connected!")
        
        # Test with a sample image
        test_image = Path(__file__).parent.parent / "ai" / "fer2013_data" / "test" / "happy" / "Training_3908.jpg"
        
        if not test_image.exists():
            print(f"❌ Test image not found: {test_image}")
            print("Please use an image from your dataset or provide a path to a face image")
            return
        
        print(f"📸 Loading test image: {test_image.name}")
        with open(test_image, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Send frame
        frame_data = {
            "frame": f"data:image/jpeg;base64,{img_data}",
            "timestamp": 1234567890
        }
        
        print("📤 Sending frame to ML model...")
        await websocket.send(json.dumps(frame_data))
        
        # Receive prediction
        print("⏳ Waiting for ML prediction...")
        response = await websocket.recv()
        data = json.parse(response)
        
        if data.get('success'):
            print(f"\n🎉 ML Prediction Results:")
            print(f"   Stress Score: {data['stress_score']:.1f}/100")
            print(f"   Stress Level: {data['stress_level']}")
            print(f"   Model: {data['model_info']['type']} ({data['model_info']['accuracy']}% accuracy)")
            print(f"\n   Facial Features:")
            for feature, value in data['features'].items():
                print(f"     - {feature}: {value:.3f}")
        else:
            print(f"❌ Error: {data.get('error', 'Unknown error')}")

if __name__ == "__main__":
    print("="*60)
    print("ML Stress Analysis WebSocket Test")
    print("="*60 + "\n")
    asyncio.run(test_ml_stress_websocket())
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)
