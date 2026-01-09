"""
ML-Powered Face Analysis
========================
Uses the trained XGBoost stress model to analyze facial features in real-time.
Converts raw MediaPipe features to UI-friendly percentages.
"""

import sys
import os
from pathlib import Path
import numpy as np
import cv2
import base64
from typing import Dict, Any, Optional

# Add AI directory to path
repo_root = Path(__file__).parent.parent
ai_dir = repo_root / "ai"
if str(ai_dir) not in sys.path:
    sys.path.insert(0, str(ai_dir))

# Import trained model components
try:
    from train_stress_model import FacialFeatureExtractor
    from inference_stress_model import StressPredictor
    PREDICTOR = None
    EXTRACTOR = None
    
    def get_predictor():
        """Lazy load predictor (initialize only when needed)."""
        global PREDICTOR, EXTRACTOR
        if PREDICTOR is None:
            model_path = ai_dir / "models" / "stress_predictor.pkl"
            scaler_path = ai_dir / "models" / "feature_scaler.pkl"
            if model_path.exists() and scaler_path.exists():
                PREDICTOR = StressPredictor(model_path, scaler_path)
                EXTRACTOR = FacialFeatureExtractor()
                print("✓ ML Stress Predictor loaded successfully")
            else:
                print(f"⚠ Model files not found: {model_path}")
        return PREDICTOR, EXTRACTOR
    
except Exception as e:
    print(f"⚠ Could not load ML model: {e}")
    PREDICTOR = None
    EXTRACTOR = None
    def get_predictor():
        return None, None


def decode_frame(frame_data: Any) -> Optional[np.ndarray]:
    """
    Decode frame from various formats to OpenCV BGR image.
    
    Supports:
    - Base64 encoded string
    - Raw bytes
    - NumPy array (already decoded)
    """
    if isinstance(frame_data, np.ndarray):
        return frame_data
    
    try:
        # Handle base64 encoded image
        if isinstance(frame_data, str):
            # Remove data URL prefix if present
            if "base64," in frame_data:
                frame_data = frame_data.split("base64,")[1]
            img_bytes = base64.b64decode(frame_data)
        else:
            img_bytes = frame_data
        
        # Decode to OpenCV image
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    
    except Exception as e:
        print(f"Error decoding frame: {e}")
        return None


def scale_to_percentage(value: float, min_val: float, max_val: float, invert: bool = False) -> float:
    """
    Scale a raw feature value to 0-100 percentage.
    
    Args:
        value: Raw feature value
        min_val: Minimum expected value
        max_val: Maximum expected value
        invert: If True, flip the scale (e.g., lower = higher %)
    
    Returns:
        Percentage value (0-100)
    """
    clamped = np.clip(value, min_val, max_val)
    percentage = ((clamped - min_val) / (max_val - min_val)) * 100.0
    
    if invert:
        percentage = 100.0 - percentage
    
    return round(float(percentage), 1)


def features_to_ui_metrics(features: np.ndarray) -> Dict[str, float]:
    """
    Convert raw MediaPipe features to UI-friendly percentage metrics.
    
    Feature array (9 values):
    [0] avg_eye_aspect_ratio: 0.15 (closed) - 0.45 (wide open)
    [1] left_ear
    [2] right_ear
    [3] avg_eyebrow_tension: -0.05 (relaxed) - 0.15 (furrowed)
    [4] left_eyebrow_tension
    [5] right_eyebrow_tension
    [6] mouth_openness: 0.0 - 0.6
    [7] jaw_width: 80 - 150 pixels
    [8] jaw_drop: 0 - 40 pixels
    
    Returns:
        Dict with percentage metrics:
        - eye_openness: Higher = more open (alert)
        - brow_tension: Higher = more furrowed (stressed)
        - jaw_tension: Higher = more clenched (stressed)
        - head_motion: Derived from jaw/mouth movement
    """
    # Extract individual features
    avg_ear = features[0]              # Eye Aspect Ratio
    avg_eyebrow = features[3]          # Eyebrow tension
    mouth_open = features[6]           # Mouth openness
    jaw_width = features[7]            # Jaw width
    jaw_drop = features[8]             # Jaw drop
    
    # Scale to UI percentages with realistic ranges
    metrics = {
        # Eye Openness: 0.15-0.45 -> 0-100%
        # Higher EAR = more open eyes = higher percentage
        "eye_openness": scale_to_percentage(avg_ear, 0.15, 0.45),
        
        # Brow Tension: -0.05 to 0.15 -> 0-100%
        # Higher positive value = more furrowed = higher percentage
        "brow_tension": scale_to_percentage(avg_eyebrow, -0.05, 0.15),
        
        # Jaw Tension: Based on jaw width (clenching narrows jaw)
        # Narrower jaw (80px) = 100%, wider (150px) = 0%
        "jaw_tension": scale_to_percentage(jaw_width, 80, 150, invert=True),
        
        # Head Motion: Based on jaw drop and mouth movement
        # Combine jaw drop + mouth openness for movement indicator
        "head_motion": scale_to_percentage(
            jaw_drop * 0.7 + mouth_open * 30,  # Weighted combination
            0, 40
        ),
    }
    
    return metrics


def analyze_face(frame_data: Any) -> Dict[str, float]:
    """
    Analyze facial features and return stress metrics.
    
    Args:
        frame_data: Image data (base64 string, bytes, or numpy array)
    
    Returns:
        Dict with metrics:
        - eye_openness: 0-100%
        - brow_tension: 0-100%
        - jaw_tension: 0-100%
        - head_motion: 0-100%
        - facial_stress_score: 0-100 (from ML model)
    """
    # Default neutral values
    default_metrics = {
        "eye_openness": 50.0,
        "brow_tension": 15.0,
        "jaw_tension": 35.0,
        "head_motion": 5.0,
        "facial_stress_score": 25.0,
    }
    
    # Decode frame
    frame = decode_frame(frame_data)
    if frame is None:
        return default_metrics
    
    # Get ML predictor
    predictor, extractor = get_predictor()
    if predictor is None or extractor is None:
        return default_metrics
    
    try:
        # Extract raw features using trained model's feature extractor
        features = extractor.extract_features_from_array(frame)
        
        if features is None:
            # No face detected
            return default_metrics
        
        # Get stress prediction from ML model
        result = predictor.predict_from_features(features)
        
        if not result['success']:
            return default_metrics
        
        # Convert raw features to UI percentages
        ui_metrics = features_to_ui_metrics(features)
        
        # Add ML stress score
        ui_metrics['facial_stress_score'] = round(result['stress_score'], 1)
        
        return ui_metrics
    
    except Exception as e:
        print(f"Error analyzing face: {e}")
        return default_metrics


def analyze_face_detailed(frame_data: Any) -> Dict[str, Any]:
    """
    Extended analysis with both UI metrics and raw ML output.
    
    Returns:
        Dict with:
        - metrics: UI-friendly percentages
        - ml_result: Full ML prediction with features
        - detected: Whether face was found
    """
    frame = decode_frame(frame_data)
    if frame is None:
        return {
            "detected": False,
            "metrics": analyze_face(frame_data),
            "ml_result": None
        }
    
    predictor, extractor = get_predictor()
    if predictor is None:
        return {
            "detected": False,
            "metrics": analyze_face(frame_data),
            "ml_result": None
        }
    
    try:
        features = extractor.extract_features_from_array(frame)
        
        if features is None:
            return {
                "detected": False,
                "metrics": analyze_face(frame_data),
                "ml_result": None
            }
        
        # Get full ML prediction
        ml_result = predictor.predict_from_features(features)
        ui_metrics = features_to_ui_metrics(features)
        ui_metrics['facial_stress_score'] = round(ml_result['stress_score'], 1)
        
        return {
            "detected": True,
            "metrics": ui_metrics,
            "ml_result": ml_result
        }
    
    except Exception as e:
        print(f"Error in detailed analysis: {e}")
        return {
            "detected": False,
            "metrics": analyze_face(frame_data),
            "ml_result": None,
            "error": str(e)
        }


# Test function
if __name__ == "__main__":
    print("Testing ML Face Analyzer...")
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam")
        exit()
    
    print("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Analyze frame
        result = analyze_face_detailed(frame)
        
        # Display results on frame
        if result['detected']:
            metrics = result['metrics']
            y_pos = 30
            cv2.putText(frame, f"Stress: {metrics['facial_stress_score']:.1f}/100", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_pos += 30
            cv2.putText(frame, f"Eye: {metrics['eye_openness']:.0f}%", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_pos += 25
            cv2.putText(frame, f"Brow: {metrics['brow_tension']:.0f}%", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_pos += 25
            cv2.putText(frame, f"Jaw: {metrics['jaw_tension']:.0f}%", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_pos += 25
            cv2.putText(frame, f"Motion: {metrics['head_motion']:.0f}%", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        else:
            cv2.putText(frame, "No face detected", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('ML Face Analyzer Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
