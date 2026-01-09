"""
Quick Stress Prediction Script
===============================
Load the trained model and predict stress from an image.
"""

import pickle
import numpy as np
from pathlib import Path
from inference_stress_model import StressPredictor

# Initialize predictor (loads model automatically)
predictor = StressPredictor(
    model_path="models/stress_predictor.pkl",
    scaler_path="models/feature_scaler.pkl"
)

# Example 1: Predict from a single image
image_path = "fer2013_data/test/happy/im0.png"  # Change this to your image
result = predictor.predict_from_image(image_path)

if result['success']:
    print(f"\n🎯 Stress Prediction Results:")
    print(f"   Stress Score: {result['stress_score']:.1f}/100")
    print(f"   Stress Level: {result['stress_level']}")
    print(f"\n📊 Facial Features:")
    for feature, value in result['features'].items():
        print(f"   {feature}: {value:.4f}")
else:
    print(f"❌ Error: {result.get('error', 'Unknown error')}")

# Example 2: Batch predict multiple images
print("\n" + "="*60)
print("Batch Prediction Example")
print("="*60)

test_images = [
    "fer2013_data/test/happy/im0.png",
    "fer2013_data/test/sad/im0.png",
    "fer2013_data/test/angry/im0.png"
]

# Only use existing images
test_images = [img for img in test_images if Path(img).exists()]

if test_images:
    results = predictor.batch_predict(test_images)
    
    for result in results:
        if result['success']:
            print(f"\n{result['image_path']}:")
            print(f"  → Stress: {result['stress_score']:.1f}/100 ({result['stress_level']})")
else:
    print("No test images found. Update the paths above.")
