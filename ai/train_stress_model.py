"""
GPU-Accelerated Facial Stress Prediction Model Training
========================================================
One-line justification:
"We use GPU-accelerated XGBoost on facial landmark features with weakly 
supervised labels to reliably predict stress levels in an MVP timeframe."

Training time: < 2 hours on GPU
Dataset: FER-2013 (3k-5k subsample)
Model: XGBoost Regressor with GPU acceleration
"""

import os
import cv2
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from tqdm import tqdm
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# MediaPipe imports - using tasks API for version 0.10+
try:
    from mediapipe import solutions
    from mediapipe.framework.formats import landmark_pb2
    mp_face_mesh = solutions.face_mesh
    MEDIAPIPE_LEGACY = True
except (ImportError, AttributeError):
    # Newer MediaPipe uses tasks API
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_LEGACY = False

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Training configuration"""
    # Paths
    DATA_DIR = Path("fer2013_data/train")
    OUTPUT_DIR = Path("models")
    MODEL_PATH = OUTPUT_DIR / "stress_predictor.pkl"
    SCALER_PATH = OUTPUT_DIR / "feature_scaler.pkl"
    
    # Dataset
    MAX_SAMPLES_PER_EMOTION = 700  # 7 emotions × 700 = ~4900 images
    TARGET_TOTAL_SAMPLES = 5000
    
    # XGBoost GPU parameters
    TREE_METHOD = "gpu_hist"  # GPU acceleration
    PREDICTOR = "gpu_predictor"
    N_ESTIMATORS = 300
    MAX_DEPTH = 6
    LEARNING_RATE = 0.1
    
    # Training
    TEST_SIZE = 0.2
    RANDOM_STATE = 42
    
    # MediaPipe
    CONFIDENCE_THRESHOLD = 0.5

# ============================================================================
# EMOTION TO STRESS MAPPING (Weak Supervision)
# ============================================================================

EMOTION_TO_STRESS = {
    'happy': 10,      # Very low stress
    'neutral': 25,    # Low stress
    'surprise': 40,   # Mild stress
    'sad': 55,        # Moderate stress
    'disgust': 70,    # High stress
    'angry': 80,      # Very high stress
    'fear': 90        # Extreme stress
}

# ============================================================================
# FACIAL LANDMARK FEATURE EXTRACTION
# ============================================================================

class FacialFeatureExtractor:
    """Extract features from facial landmarks using MediaPipe"""
    
    def __init__(self):
        if MEDIAPIPE_LEGACY:
            self.mp_face_mesh = mp_face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=Config.CONFIDENCE_THRESHOLD
            )
            self.use_legacy = True
        else:
            # Use new tasks API
            base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                num_faces=1,
                min_face_detection_confidence=Config.CONFIDENCE_THRESHOLD
            )
            self.face_mesh = vision.FaceLandmarker.create_from_options(options)
            self.use_legacy = False
        
        # Landmark indices (MediaPipe 468 landmarks)
        # Left eye: 33, 160, 158, 133, 153, 144
        # Right eye: 362, 385, 387, 263, 373, 380
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        
        # Eyebrows
        self.LEFT_EYEBROW = [70, 63, 105, 66, 107]
        self.RIGHT_EYEBROW = [300, 293, 334, 296, 336]
        
        # Mouth
        self.MOUTH_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409]
        
        # Jaw
        self.JAW = [234, 93, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454]
    
    def compute_eye_aspect_ratio(self, landmarks, eye_indices):
        """
        Compute Eye Aspect Ratio (EAR)
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        Lower EAR indicates closed/squinting eyes (stress indicator)
        """
        points = np.array([[landmarks[i].x, landmarks[i].y] for i in eye_indices])
        
        # Vertical distances
        vertical_1 = np.linalg.norm(points[1] - points[5])
        vertical_2 = np.linalg.norm(points[2] - points[4])
        
        # Horizontal distance
        horizontal = np.linalg.norm(points[0] - points[3])
        
        if horizontal == 0:
            return 0.0
        
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear
    
    def compute_eyebrow_tension(self, landmarks, eyebrow_indices, eye_indices):
        """
        Measure eyebrow height relative to eye
        Higher values indicate raised eyebrows (stress/surprise)
        Lower values indicate furrowed brows (anger/concentration)
        """
        eyebrow_points = np.array([[landmarks[i].x, landmarks[i].y] for i in eyebrow_indices])
        eye_points = np.array([[landmarks[i].x, landmarks[i].y] for i in eye_indices])
        
        eyebrow_y = np.mean(eyebrow_points[:, 1])
        eye_y = np.mean(eye_points[:, 1])
        
        tension = eye_y - eyebrow_y  # Positive when eyebrow is above eye
        return tension
    
    def compute_mouth_openness(self, landmarks):
        """
        Measure mouth opening (vertical distance)
        Higher values indicate open mouth (surprise/fear)
        """
        mouth_points = np.array([[landmarks[i].x, landmarks[i].y] for i in self.MOUTH_OUTER])
        
        # Top vs bottom mouth points
        top_y = np.min(mouth_points[:, 1])
        bottom_y = np.max(mouth_points[:, 1])
        
        openness = bottom_y - top_y
        return openness
    
    def compute_jaw_tension(self, landmarks):
        """
        Measure jaw clenching (width of jaw area)
        Wider jaw indicates clenching (stress/anger)
        """
        jaw_points = np.array([[landmarks[i].x, landmarks[i].y] for i in self.JAW])
        
        # Measure jaw width
        jaw_width = np.max(jaw_points[:, 0]) - np.min(jaw_points[:, 0])
        
        # Measure jaw drop
        jaw_drop = np.max(jaw_points[:, 1]) - np.min(jaw_points[:, 1])
        
        return jaw_width, jaw_drop
    
    def extract_features(self, image_path):
        """
        Extract all facial features from an image
        Returns: numpy array of features or None if face not detected
        """
        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            return None
        
        # Convert to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        if self.use_legacy:
            results = self.face_mesh.process(image_rgb)
            if not results.multi_face_landmarks:
                return None
            landmarks = results.multi_face_landmarks[0].landmark
        else:
            # New tasks API
            from mediapipe import Image as MPImage, ImageFormat
            mp_image = MPImage(image_format=ImageFormat.SRGB, data=image_rgb)
            results = self.face_mesh.detect(mp_image)
            
            if not results.face_landmarks:
                return None
            landmarks = results.face_landmarks[0]
        
        # Extract features
        left_ear = self.compute_eye_aspect_ratio(landmarks, self.LEFT_EYE)
        right_ear = self.compute_eye_aspect_ratio(landmarks, self.RIGHT_EYE)
        avg_ear = (left_ear + right_ear) / 2.0
        
        left_eyebrow_tension = self.compute_eyebrow_tension(
            landmarks, self.LEFT_EYEBROW, self.LEFT_EYE
        )
        right_eyebrow_tension = self.compute_eyebrow_tension(
            landmarks, self.RIGHT_EYEBROW, self.RIGHT_EYE
        )
        avg_eyebrow_tension = (left_eyebrow_tension + right_eyebrow_tension) / 2.0
        
        mouth_openness = self.compute_mouth_openness(landmarks)
        jaw_width, jaw_drop = self.compute_jaw_tension(landmarks)
        
        # Compile feature vector
        features = np.array([
            avg_ear,                  # 0: Average Eye Aspect Ratio
            left_ear,                 # 1: Left EAR
            right_ear,                # 2: Right EAR
            avg_eyebrow_tension,      # 3: Average eyebrow tension
            left_eyebrow_tension,     # 4: Left eyebrow tension
            right_eyebrow_tension,    # 5: Right eyebrow tension
            mouth_openness,           # 6: Mouth openness
            jaw_width,                # 7: Jaw width
            jaw_drop,                 # 8: Jaw drop
        ])
        
        return features
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()

# ============================================================================
# DATASET LOADING
# ============================================================================

def load_fer2013_dataset(data_dir, max_samples_per_emotion=700):
    """
    Load FER-2013 dataset with subsampling
    Returns: (features, stress_labels, emotion_labels)
    """
    print("=" * 70)
    print("LOADING FER-2013 DATASET")
    print("=" * 70)
    
    data_dir = Path(data_dir)
    extractor = FacialFeatureExtractor()
    
    features_list = []
    stress_labels = []
    emotion_labels = []
    
    # Get all emotion directories
    emotion_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
    
    print(f"\nFound {len(emotion_dirs)} emotion categories")
    print(f"Target: {max_samples_per_emotion} samples per emotion\n")
    
    for emotion_dir in emotion_dirs:
        emotion = emotion_dir.name
        
        if emotion not in EMOTION_TO_STRESS:
            print(f"⚠️  Skipping unknown emotion: {emotion}")
            continue
        
        # Get stress score for this emotion
        stress_score = EMOTION_TO_STRESS[emotion]
        
        # Get all image files
        image_files = list(emotion_dir.glob("*.jpg")) + \
                     list(emotion_dir.glob("*.png"))
        
        # Subsample if needed
        if len(image_files) > max_samples_per_emotion:
            np.random.seed(Config.RANDOM_STATE)
            image_files = np.random.choice(
                image_files, 
                max_samples_per_emotion, 
                replace=False
            )
        
        print(f"Processing {emotion:12s} → stress={stress_score:3d} | {len(image_files)} images")
        
        # Process images
        successful = 0
        for img_path in tqdm(image_files, desc=f"  {emotion}", leave=False):
            features = extractor.extract_features(img_path)
            
            if features is not None:
                features_list.append(features)
                stress_labels.append(stress_score)
                emotion_labels.append(emotion)
                successful += 1
        
        print(f"  ✓ Successfully processed: {successful}/{len(image_files)}")
    
    # Convert to numpy arrays
    X = np.array(features_list)
    y = np.array(stress_labels)
    
    print("\n" + "=" * 70)
    print(f"Dataset loaded: {len(X)} samples with {X.shape[1]} features")
    print("=" * 70)
    
    return X, y, emotion_labels

# ============================================================================
# MODEL TRAINING
# ============================================================================

def train_xgboost_model(X_train, y_train, X_test, y_test):
    """
    Train GPU-accelerated XGBoost regressor
    """
    print("\n" + "=" * 70)
    print("TRAINING XGBOOST MODEL")
    print("=" * 70)
    
    # Check GPU availability and XGBoost GPU support
    gpu_available = False
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            # GPU hardware detected, now check if XGBoost supports it
            try:
                # Test if gpu_hist is available
                test_model = xgb.XGBRegressor(tree_method='gpu_hist', n_estimators=1)
                test_model.fit(X_train[:10], y_train[:10])
                gpu_available = True
                print("\n✓ GPU detected and XGBoost GPU support available")
                print(f"Using: tree_method='{Config.TREE_METHOD}', predictor='{Config.PREDICTOR}'")
            except:
                print("\n✓ GPU hardware detected but XGBoost GPU support not available")
                print("⚠️  Falling back to CPU (hist method)")
                Config.TREE_METHOD = "hist"
                Config.PREDICTOR = "cpu_predictor"
    except:
        print("\n⚠️  No GPU detected, using CPU")
        Config.TREE_METHOD = "hist"
        Config.PREDICTOR = "cpu_predictor"
    
    # Create model
    model = xgb.XGBRegressor(
        tree_method=Config.TREE_METHOD,
        predictor=Config.PREDICTOR,
        n_estimators=Config.N_ESTIMATORS,
        max_depth=Config.MAX_DEPTH,
        learning_rate=Config.LEARNING_RATE,
        random_state=Config.RANDOM_STATE,
        objective='reg:squarederror',
        n_jobs=-1
    )
    
    print(f"\nModel configuration:")
    print(f"  • n_estimators: {Config.N_ESTIMATORS}")
    print(f"  • max_depth: {Config.MAX_DEPTH}")
    print(f"  • learning_rate: {Config.LEARNING_RATE}")
    print(f"  • tree_method: {Config.TREE_METHOD}")
    
    # Train
    print("\nTraining...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50
    )
    
    print("\n✓ Training complete!")
    
    return model

# ============================================================================
# EVALUATION
# ============================================================================

def evaluate_model(model, X_train, y_train, X_test, y_test):
    """
    Evaluate model performance
    """
    print("\n" + "=" * 70)
    print("MODEL EVALUATION")
    print("=" * 70)
    
    # Create output directory
    Config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Clip predictions to valid stress range
    y_train_pred = np.clip(y_train_pred, 0, 100)
    y_test_pred = np.clip(y_test_pred, 0, 100)
    
    # Compute MAE
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    
    print(f"\nMean Absolute Error (MAE):")
    print(f"  • Training:   {train_mae:.2f} stress points")
    print(f"  • Testing:    {test_mae:.2f} stress points")
    
    # Additional metrics
    train_accuracy = 100 * (1 - train_mae / 100)
    test_accuracy = 100 * (1 - test_mae / 100)
    
    print(f"\nApproximate Accuracy:")
    print(f"  • Training:   {train_accuracy:.1f}%")
    print(f"  • Testing:    {test_accuracy:.1f}%")
    
    # Plot predictions vs actual
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.scatter(y_test, y_test_pred, alpha=0.5, s=20)
    plt.plot([0, 100], [0, 100], 'r--', lw=2, label='Perfect prediction')
    plt.xlabel('Actual Stress Level')
    plt.ylabel('Predicted Stress Level')
    plt.title(f'Test Set: Predicted vs Actual\nMAE = {test_mae:.2f}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xlim([0, 100])
    plt.ylim([0, 100])
    
    plt.subplot(1, 2, 2)
    errors = y_test_pred - y_test
    plt.hist(errors, bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel('Prediction Error (predicted - actual)')
    plt.ylabel('Frequency')
    plt.title('Error Distribution')
    plt.axvline(x=0, color='r', linestyle='--', lw=2)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(Config.OUTPUT_DIR / 'evaluation_plot.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Evaluation plot saved to: {Config.OUTPUT_DIR / 'evaluation_plot.png'}")
    
    return {
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_accuracy': train_accuracy,
        'test_accuracy': test_accuracy
    }

# ============================================================================
# SAVE MODEL
# ============================================================================

def save_model(model, scaler):
    """Save trained model and scaler"""
    print("\n" + "=" * 70)
    print("SAVING MODEL")
    print("=" * 70)
    
    # Create output directory
    Config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Save model
    with open(Config.MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"✓ Model saved to: {Config.MODEL_PATH}")
    
    # Save scaler
    with open(Config.SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"✓ Scaler saved to: {Config.SCALER_PATH}")
    
    # Save metadata
    metadata = {
        'feature_names': [
            'avg_eye_aspect_ratio',
            'left_ear',
            'right_ear',
            'avg_eyebrow_tension',
            'left_eyebrow_tension',
            'right_eyebrow_tension',
            'mouth_openness',
            'jaw_width',
            'jaw_drop'
        ],
        'emotion_to_stress_mapping': EMOTION_TO_STRESS,
        'model_type': 'XGBoost Regressor',
        'tree_method': Config.TREE_METHOD
    }
    
    metadata_path = Config.OUTPUT_DIR / 'model_metadata.pkl'
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"✓ Metadata saved to: {metadata_path}")

# ============================================================================
# INFERENCE FUNCTION
# ============================================================================

def predict_stress(facial_features, model_path=None, scaler_path=None):
    """
    Predict stress level from facial features
    
    Args:
        facial_features: numpy array of shape (9,) with features:
            [avg_ear, left_ear, right_ear, avg_eyebrow_tension, 
             left_eyebrow_tension, right_eyebrow_tension, 
             mouth_openness, jaw_width, jaw_drop]
        model_path: path to trained model (optional)
        scaler_path: path to feature scaler (optional)
    
    Returns:
        stress_score: float between 0-100
    """
    # Load model and scaler if not provided
    if model_path is None:
        model_path = Config.MODEL_PATH
    if scaler_path is None:
        scaler_path = Config.SCALER_PATH
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    # Ensure features are 2D
    if len(facial_features.shape) == 1:
        facial_features = facial_features.reshape(1, -1)
    
    # Normalize
    features_normalized = scaler.transform(facial_features)
    
    # Predict
    stress_score = model.predict(features_normalized)[0]
    
    # Clip to valid range
    stress_score = np.clip(stress_score, 0, 100)
    
    return float(stress_score)

# ============================================================================
# MAIN TRAINING PIPELINE
# ============================================================================

def main():
    """Main training pipeline"""
    print("\n" + "=" * 70)
    print("GPU-ACCELERATED FACIAL STRESS PREDICTION MODEL")
    print("=" * 70)
    print("\nJustification:")
    print("We use GPU-accelerated XGBoost on facial landmark features")
    print("with weakly supervised labels to reliably predict stress levels")
    print("in an MVP timeframe.\n")
    
    # Load dataset
    X, y, emotion_labels = load_fer2013_dataset(
        Config.DATA_DIR,
        max_samples_per_emotion=Config.MAX_SAMPLES_PER_EMOTION
    )
    
    # Split dataset
    print("\n" + "=" * 70)
    print("SPLITTING DATASET")
    print("=" * 70)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=Config.TEST_SIZE,
        random_state=Config.RANDOM_STATE,
        stratify=y  # Ensure balanced split
    )
    
    print(f"Training set:   {len(X_train)} samples")
    print(f"Testing set:    {len(X_test)} samples")
    
    # Normalize features
    print("\n" + "=" * 70)
    print("NORMALIZING FEATURES")
    print("=" * 70)
    
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    print("✓ Features normalized (StandardScaler)")
    print(f"  Mean: {scaler.mean_}")
    print(f"  Std:  {scaler.scale_}")
    
    # Train model
    model = train_xgboost_model(X_train, y_train, X_test, y_test)
    
    # Evaluate
    metrics = evaluate_model(model, X_train, y_train, X_test, y_test)
    
    # Save
    save_model(model, scaler)
    
    # Summary
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE ✓")
    print("=" * 70)
    print(f"\nFinal Test MAE: {metrics['test_mae']:.2f} stress points")
    print(f"Final Test Accuracy: {metrics['test_accuracy']:.1f}%")
    print(f"\nModel saved to: {Config.MODEL_PATH}")
    print("\nUse predict_stress() function for inference:")
    print("  stress = predict_stress(facial_features)")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
