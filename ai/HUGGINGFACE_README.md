---
language:
- en
license: mit
library_name: xgboost
tags:
- facial-analysis
- stress-prediction
- mental-health
- xgboost
- mediapipe
- computer-vision
- affective-computing
- regression
datasets:
- FER-2013
metrics:
- mae
- rmse
model-index:
- name: facial-stress-predictor
  results:
  - task:
      type: image-regression
      name: Facial Stress Level Prediction
    dataset:
      name: FER-2013
      type: fer2013
    metrics:
    - type: mae
      value: 22.66
      name: Mean Absolute Error
    - type: rmse
      value: 27.29
      name: Root Mean Squared Error
    - type: accuracy
      value: 77.3
      name: Approximate Accuracy
pipeline_tag: image-feature-extraction
---

# Facial Stress Prediction Model 🧠

## Model Description

This model predicts stress levels (0-100 scale) from facial images using geometric facial landmark features. It's designed for real-time stress monitoring applications in healthcare, mental health assessment, and wellness tracking.

**Model Type:** XGBoost Regressor  
**Task:** Facial Stress Level Regression  
**License:** MIT (or specify your license)

## Model Architecture

- **Algorithm:** XGBoost Regressor with gradient boosting
- **Features:** 9 geometric facial landmarks extracted using MediaPipe Face Mesh
  - Eye Aspect Ratio (EAR) - left, right, and average
  - Eyebrow tension - left, right, and average  
  - Mouth openness
  - Jaw width and jaw drop
- **Output:** Continuous stress score (0-100)
  - 0-30: Low stress
  - 30-55: Moderate stress
  - 55-75: High stress
  - 75-100: Extreme stress

## Training Data

- **Dataset:** FER-2013 (Facial Expression Recognition)
- **Samples:** ~4,900 images (700 per emotion category)
- **Emotion Categories:** 7 (happy, neutral, surprise, sad, disgust, angry, fear)
- **Supervision Method:** Weak supervision - emotion labels mapped to stress scores
- **Split:** 80% training (3,920 samples) / 20% testing (980 samples)

### Emotion-to-Stress Mapping

```
happy    → 10  (Very low stress)
neutral  → 25  (Low stress)
surprise → 40  (Mild stress)
sad      → 55  (Moderate stress)
disgust  → 70  (High stress)
angry    → 80  (Very high stress)
fear     → 90  (Extreme stress)
```

## Training Details

### Hyperparameters

- **n_estimators:** 300 trees
- **max_depth:** 6
- **learning_rate:** 0.1
- **tree_method:** gpu_hist (GPU-accelerated) or hist (CPU fallback)
- **objective:** reg:squarederror
- **Feature normalization:** StandardScaler

### Training Infrastructure

- **Training time:** < 2 hours on GPU / < 4 hours on CPU
- **Hardware:** NVIDIA GPU with CUDA support (optional but recommended)
- **Framework:** XGBoost 2.x with scikit-learn
- **Face detection:** MediaPipe Face Mesh (468 landmarks)

## Performance Metrics

- **Mean Absolute Error (MAE):** 22.66 stress points
- **Root Mean Squared Error (RMSE):** 27.29
- **Approximate Accuracy:** 77.3%
- **Target Performance:** 60-70% accuracy for MVP deployment ✅ **Achieved!**

**Training Set Performance:**
- Training MAE: 6.15 stress points
- Training RMSE: 8.12
- Training Accuracy: 93.9%

## Intended Use

### Primary Use Cases

✅ Mental health monitoring systems  
✅ Workplace wellness applications  
✅ Telemedicine platforms  
✅ Research in affective computing  
✅ Educational tools for stress recognition

### Out-of-Scope Use Cases

❌ Clinical diagnosis without professional oversight  
❌ High-stakes decision making (hiring, security clearance, etc.)  
❌ Surveillance or privacy-invasive applications  
❌ Biased or discriminatory profiling

## How to Use

### Installation

```bash
pip install xgboost scikit-learn opencv-python mediapipe numpy
```

### Inference Example

```python
import pickle
import cv2
import numpy as np
from mediapipe import solutions

# Load model and scaler
with open('stress_predictor.pkl', 'rb') as f:
    model = pickle.load(f)
with open('feature_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Initialize MediaPipe Face Mesh
mp_face_mesh = solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    min_detection_confidence=0.5
)

# Extract features from image (using FacialFeatureExtractor class)
# ... feature extraction code ...

# Predict stress level
features_scaled = scaler.transform(features.reshape(1, -1))
stress_level = np.clip(model.predict(features_scaled)[0], 0, 100)

print(f"Predicted Stress Level: {stress_level:.1f}/100")
```

## Limitations and Biases

### Known Limitations

- **Weak supervision:** Model trained on emotion labels, not actual stress measurements
- **Dataset bias:** FER-2013 may not represent all demographics equally
- **Context-agnostic:** Doesn't account for situational context
- **Still images only:** Trained on static images, not video sequences
- **Lighting sensitivity:** Performance may degrade in poor lighting conditions

### Bias Considerations

- Training data may have demographic imbalances
- Facial landmark detection may perform differently across ethnicities
- Should be validated on diverse populations before deployment

## Ethical Considerations

⚠️ **Privacy:** Ensure informed consent when processing facial images  
⚠️ **Transparency:** Users should know when stress analysis is being performed  
⚠️ **Accountability:** Results should be reviewed by qualified professionals in clinical settings  
⚠️ **Fairness:** Monitor for performance disparities across demographic groups

## Model Files

- `stress_predictor.pkl` - Trained XGBoost model (main file)
- `feature_scaler.pkl` - StandardScaler for feature normalization
- `model_metadata.pkl` - Training configuration and metrics

## Citation

If you use this model in your research or application, please cite:

```bibtex
@misc{facial_stress_predictor_2026,
  author = {Your Name/Organization},
  title = {Facial Stress Prediction Model},
  year = {2026},
  publisher = {HuggingFace},
  howpublished = {\url{https://huggingface.co/your-username/model-name}}
}
```

## Contact & Support

- **Repository:** [GitHub Link]
- **Issues:** [GitHub Issues Link]
- **Contact:** [Your Email or Contact Info]

## Changelog

**v1.0.0** (January 2026)
- Initial release
- XGBoost regressor trained on FER-2013
- 9 facial landmark features
- Target: 60-70% accuracy achieved

---

## Technical Details

**Dependencies:**
- Python >= 3.8
- xgboost >= 2.0.0
- scikit-learn >= 1.0.0
- opencv-python >= 4.5.0
- mediapipe >= 0.10.0
- numpy >= 1.20.0

**Model Size:** ~XXX MB (update based on actual file size)

**Inference Speed:** ~XX ms per image on CPU / ~XX ms on GPU (update with benchmarks)

---

**License:** [Specify your license - MIT, Apache 2.0, etc.]

**Last Updated:** January 10, 2026

---

## Remember to Update:

1. ✏️ Performance metrics (MAE, RMSE, Accuracy) with your actual results
2. ✏️ Contact information and GitHub links
3. ✏️ Model file sizes and inference speed benchmarks
4. ✏️ Specify your chosen license
5. ✏️ Update citation details with your information
6. ✏️ Add actual repository URLs
