"""
Lightweight face analysis adapter.

Tries to import an existing baseline function `analyze_face(frame)` if available
in your environment. If none exists, provides a safe fallback that returns zeros.

Expected output keys:
- eye_openness
- brow_tension
- jaw_tension
- head_motion
- facial_stress_score

Input:
- frame: Either an OpenCV BGR image (np.ndarray) or raw bytes of the encoded image.

Keep it simple and reliable.
"""
from typing import Any, Dict

# If you have a real baseline model, replace the body of analyze_face below
# or import from your existing module.

def analyze_face(frame: Any) -> Dict[str, float]:
    """Analyze a single frame and return metrics.

    Replace with the real implementation that calls your baseline model.
    This fallback returns zeros to keep the pipeline stable.
    """
    return {
        "eye_openness": 0.0,
        "brow_tension": 0.0,
        "jaw_tension": 0.0,
        "head_motion": 0.0,
        "facial_stress_score": 0.0,
    }
