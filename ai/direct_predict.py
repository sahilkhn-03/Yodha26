"""
Direct Model Usage Example
===========================
Load and use the model directly without the wrapper class.
"""

import pickle
import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))
from train_stress_model import FacialFeatureExtractor

# Load model and scaler
print("Loading model...")
with open("models/stress_predictor.pkl", 'rb') as f:
    model = pickle.load(f)

with open("models/feature_scaler.pkl", 'rb') as f:
    scaler = pickle.load(f)

with open("models/model_metadata.pkl", 'rb') as f:
    metadata = pickle.load(f)

print("✓ Model loaded successfully!")
print(f"  Test MAE: {metadata['test_mae']:.2f}")
print(f"  Test Accuracy: {metadata['test_accuracy']:.1f}%")
print(f"  Training samples: {metadata['n_samples']}")

# Extract features from an image
extractor = FacialFeatureExtractor()

image_path = "fer2013_data/test/happy/im0.png"  # Change this
print(f"\nProcessing: {image_path}")

features = extractor.extract_features(image_path)

if features is not None:
    # Normalize features
    features_normalized = scaler.transform(features.reshape(1, -1))
    
    # Predict stress
    stress_score = model.predict(features_normalized)[0]
    stress_score = np.clip(stress_score, 0, 100)
    
    # Categorize
    if stress_score < 30:
        level = "Low"
    elif stress_score < 55:
        level = "Moderate"
    elif stress_score < 75:
        level = "High"
    else:
        level = "Extreme"
    
    print(f"\n✅ Results:")
    print(f"   Stress Score: {stress_score:.1f}/100")
    print(f"   Level: {level}")
    
    print(f"\n📊 Raw Features:")
    for name, value in zip(metadata['feature_names'], features):
        print(f"   {name}: {value:.4f}")
else:
    print("❌ No face detected in image")
