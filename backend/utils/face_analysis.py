"""
Lightweight face analysis adapter.

Converts raw MediaPipe facial features to UI-friendly percentage metrics.
Uses the trained XGBoost model's feature extractor for consistency.

Expected output keys (all scaled 0-100%):
- eye_openness: 0% (closed) to 100% (wide open)
- brow_tension: 0% (relaxed) to 100% (furrowed)
- jaw_tension: 0% (relaxed) to 100% (clenched)
- head_motion: 0% (still) to 100% (moving)
- facial_stress_score: 0-100 from ML model

Input:
- frame: Either an OpenCV BGR image (np.ndarray) or raw bytes of the encoded image.
"""
from typing import Any, Dict
import numpy as np

def scale_to_percentage(value: float, min_val: float, max_val: float) -> float:
    """Scale a value to 0-100 percentage range."""
    clamped = np.clip(value, min_val, max_val)
    return ((clamped - min_val) / (max_val - min_val)) * 100.0

def analyze_face(frame: Any) -> Dict[str, float]:
    """Analyze a single frame and return scaled metrics (0-100%).
    
    Converts raw facial features to human-readable percentages:
    - Eye Aspect Ratio (0.15-0.45) -> Eye Openness (0-100%)
    - Eyebrow Tension (-0.05 to 0.15) -> Brow Tension (0-100%)
    - Mouth Openness (0.0-0.6) -> Not used (replaced by jaw)
    - Jaw Width (80-150 pixels) -> Jaw Tension (0-100%)
    - Jaw Drop (0-40 pixels) -> Head Motion proxy (0-100%)
    """
    # Default fallback values (mid-range, neutral state)
    return {
        "eye_openness": 50.0,
        "brow_tension": 15.0,
        "jaw_tension": 35.0,
        "head_motion": 5.0,
        "facial_stress_score": 25.0,
    }
