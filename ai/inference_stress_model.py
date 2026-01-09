"""
Stress Prediction Inference Module
===================================
Use the trained model to predict stress levels from images or facial features.
"""

import cv2
import numpy as np
import pickle
from pathlib import Path
import sys

# Add parent directory to path if needed
sys.path.append(str(Path(__file__).parent))

from train_stress_model import FacialFeatureExtractor, Config

class StressPredictor:
    """
    Easy-to-use stress prediction interface
    """
    
    def __init__(self, model_path=None, scaler_path=None):
        """
        Initialize the stress predictor
        
        Args:
            model_path: Path to trained XGBoost model (.pkl)
            scaler_path: Path to feature scaler (.pkl)
        """
        if model_path is None:
            model_path = Path("models/stress_predictor.pkl")
        if scaler_path is None:
            scaler_path = Path("models/feature_scaler.pkl")
        
        # Load model and scaler
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        # Initialize feature extractor
        self.extractor = FacialFeatureExtractor()
        
        print(f"✓ Stress predictor loaded")
        print(f"  Model: {model_path}")
        print(f"  Scaler: {scaler_path}")
    
    def predict_from_image(self, image_path):
        """
        Predict stress level from an image file
        
        Args:
            image_path: Path to image file (str or Path)
        
        Returns:
            dict with:
                - stress_score: float (0-100)
                - stress_level: str (Low/Moderate/High/Extreme)
                - features: dict of extracted features
                - success: bool
        """
        # Extract features
        features = self.extractor.extract_features(image_path)
        
        if features is None:
            return {
                'success': False,
                'stress_score': None,
                'stress_level': 'Unknown',
                'error': 'No face detected in image'
            }
        
        return self.predict_from_features(features)
    
    def predict_from_frame(self, frame):
        """
        Predict stress level from a video frame (numpy array)
        
        Args:
            frame: BGR image (numpy array)
        
        Returns:
            dict with stress prediction results
        """
        # Save frame temporarily
        temp_path = Path("temp_frame.jpg")
        cv2.imwrite(str(temp_path), frame)
        
        # Predict
        result = self.predict_from_image(temp_path)
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
        
        return result
    
    def predict_from_features(self, features):
        """
        Predict stress level from extracted facial features
        
        Args:
            features: numpy array (9 features)
        
        Returns:
            dict with stress prediction results
        """
        # Reshape if needed
        if len(features.shape) == 1:
            features = features.reshape(1, -1)
        
        # Normalize
        features_normalized = self.scaler.transform(features)
        
        # Predict
        stress_score = self.model.predict(features_normalized)[0]
        stress_score = np.clip(stress_score, 0, 100)
        
        # Categorize stress level
        if stress_score < 30:
            stress_level = "Low"
        elif stress_score < 55:
            stress_level = "Moderate"
        elif stress_score < 75:
            stress_level = "High"
        else:
            stress_level = "Extreme"
        
        # Feature breakdown
        feature_names = [
            'avg_eye_aspect_ratio',
            'left_ear',
            'right_ear',
            'avg_eyebrow_tension',
            'left_eyebrow_tension',
            'right_eyebrow_tension',
            'mouth_openness',
            'jaw_width',
            'jaw_drop'
        ]
        
        feature_dict = {
            name: float(val) 
            for name, val in zip(feature_names, features[0])
        }
        
        return {
            'success': True,
            'stress_score': float(stress_score),
            'stress_level': stress_level,
            'features': feature_dict
        }
    
    def batch_predict(self, image_paths):
        """
        Predict stress levels for multiple images
        
        Args:
            image_paths: List of image paths
        
        Returns:
            List of prediction dicts
        """
        results = []
        for img_path in image_paths:
            result = self.predict_from_image(img_path)
            result['image_path'] = str(img_path)
            results.append(result)
        return results


def demo():
    """Demo usage of stress predictor"""
    print("\n" + "="*70)
    print("STRESS PREDICTION DEMO")
    print("="*70)
    
    # Initialize predictor
    predictor = StressPredictor()
    
    # Example: Predict from test images
    print("\nLooking for test images in fer2013_data/test/...")
    
    test_dir = Path("fer2013_data/test")
    if test_dir.exists():
        # Get sample images from each emotion
        sample_images = []
        for emotion_dir in test_dir.iterdir():
            if emotion_dir.is_dir():
                images = list(emotion_dir.glob("*.jpg"))[:2]  # 2 per emotion
                sample_images.extend(images)
        
        if sample_images:
            print(f"\nTesting on {len(sample_images)} sample images...\n")
            
            for img_path in sample_images[:5]:  # Show first 5
                result = predictor.predict_from_image(img_path)
                
                if result['success']:
                    print(f"Image: {img_path.parent.name}/{img_path.name}")
                    print(f"  Stress Score: {result['stress_score']:.1f}/100")
                    print(f"  Level: {result['stress_level']}")
                    print(f"  Key features:")
                    print(f"    - Eye openness (EAR): {result['features']['avg_eye_aspect_ratio']:.3f}")
                    print(f"    - Eyebrow tension: {result['features']['avg_eyebrow_tension']:.3f}")
                    print(f"    - Mouth openness: {result['features']['mouth_openness']:.3f}")
                    print()
                else:
                    print(f"Image: {img_path.name} - {result['error']}\n")
        else:
            print("No test images found.")
    else:
        print(f"Test directory not found: {test_dir}")
    
    print("="*70)
    print("Demo complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    demo()
