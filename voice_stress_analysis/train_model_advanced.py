"""
ADVANCED Voice Stress Detection Model Training Pipeline
Target: >75% accuracy with comprehensive feature engineering
XGBoost with hyperparameter tuning and cross-validation
Optimized for JL-Corpus dataset (2400 samples)
"""

import os
import numpy as np
import librosa
from pathlib import Path
import pickle
import json
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

print("\n" + "="*80)
print(" "*15 + "🚀 ADVANCED VOICE STRESS MODEL TRAINING")
print(" "*20 + "Target: >75% Accuracy")
print("="*80)

# Configuration
DATASET_PATH = Path(__file__).parent / "dataset" / "Raw JL corpus (unchecked and unannotated)" / "JL(wav+txt)"
MODEL_SAVE_PATH = Path(__file__).parent / "models"
SAMPLE_RATE = 22050  # Higher sample rate for better quality
BATCH_SIZE = 30  # Smaller batches for RAM efficiency

# IMPROVED emotion to stress mapping (based on arousal + valence)
# Using psychological stress correlation with emotions
EMOTION_STRESS_MAP = {
    'neutral': 10,      # Very low stress - baseline
    'happy': 15,        # Low stress - positive low arousal
    'encouraging': 18,  # Low stress - positive moderate arousal
    'assertive': 35,    # Low-moderate - controlled high arousal
    'excited': 50,      # Moderate - positive high arousal
    'apologetic': 58,   # Moderate-high - negative moderate arousal
    'concerned': 72,    # High - negative high arousal (worry)
    'sad': 68,          # High - negative moderate arousal (distress)
}

print(f"\n📂 Dataset: {DATASET_PATH}")
print(f"💾 Output: {MODEL_SAVE_PATH}")
MODEL_SAVE_PATH.mkdir(exist_ok=True)


def parse_filename(filename):
    """Extract emotion label from filename."""
    parts = filename.stem.split('_')
    if len(parts) >= 2:
        return parts[1]
    return None


def extract_advanced_features(audio_path):
    """
    Extract comprehensive audio features for stress detection.
    Returns 40+ features covering multiple acoustic dimensions.
    """
    try:
        # Load audio with higher sample rate
        audio, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
        
        # Skip very short files
        if len(audio) < sr * 0.3:
            return None
        
        # Normalize audio
        audio = librosa.util.normalize(audio)
        
        features = []
        
        # ==================== MFCC Features (26 features) ====================
        # Mel-frequency cepstral coefficients - capture timbral texture
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1).flatten()
        mfcc_std = np.std(mfcc, axis=1).flatten()
        features.extend(mfcc_mean.tolist())  # 13 features
        features.extend(mfcc_std.tolist())   # 13 features
        
        # ==================== Spectral Features (10 features) ====================
        # Spectral centroid - "brightness" of sound
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
        features.append(float(np.mean(spectral_centroid)))
        features.append(float(np.std(spectral_centroid)))
        
        # Spectral rolloff - frequency below which 85% of energy is concentrated
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
        features.append(float(np.mean(spectral_rolloff)))
        features.append(float(np.std(spectral_rolloff)))
        
        # Spectral bandwidth - width of frequency range
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)
        features.append(float(np.mean(spectral_bandwidth)))
        features.append(float(np.std(spectral_bandwidth)))
        
        # Spectral contrast - difference between peaks and valleys
        spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
        features.append(float(np.mean(spectral_contrast)))
        features.append(float(np.std(spectral_contrast)))
        
        # Spectral flatness - how noise-like vs tone-like
        spectral_flatness = librosa.feature.spectral_flatness(y=audio)
        features.append(float(np.mean(spectral_flatness)))
        features.append(float(np.std(spectral_flatness)))
        
        # ==================== Chroma Features (2 features) ====================
        # Chroma STFT - pitch class distribution
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        features.append(float(np.mean(chroma)))
        features.append(float(np.std(chroma)))
        
        # ==================== Zero Crossing Rate (2 features) ====================
        zcr = librosa.feature.zero_crossing_rate(audio)
        features.append(float(np.mean(zcr)))
        features.append(float(np.std(zcr)))
        
        # ==================== Energy Features (4 features) ====================
        # RMS energy
        rms = librosa.feature.rms(y=audio)
        features.append(float(np.mean(rms)))
        features.append(float(np.std(rms)))
        features.append(float(np.max(rms)))
        features.append(float(np.min(rms)))
        
        # ==================== Pitch Features (6 features) ====================
        # F0 (fundamental frequency) using pYIN
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio, 
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr
        )
        f0_clean = f0[~np.isnan(f0)]
        
        if len(f0_clean) > 0:
            features.append(float(np.mean(f0_clean)))
            features.append(float(np.std(f0_clean)))
            features.append(float(np.max(f0_clean)))
            features.append(float(np.min(f0_clean)))
            features.append(float(np.ptp(f0_clean)))  # Peak-to-peak (range)
            
            # Jitter (pitch perturbation)
            if len(f0_clean) > 1:
                jitter = float(np.mean(np.abs(np.diff(f0_clean))))
                features.append(jitter)
            else:
                features.append(0.0)
        else:
            features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        # ==================== Tempo/Rhythm (2 features) ====================
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
        features.append(float(tempo))
        features.append(float(len(beats) / (len(audio) / sr)))  # Beats per second
        
        # ==================== Prosodic Features (3 features) ====================
        # Energy contour variance
        energy_contour = librosa.feature.rms(y=audio)[0]
        features.append(float(np.var(energy_contour)))
        
        # Pitch contour variance
        if len(f0_clean) > 0:
            features.append(float(np.var(f0_clean)))
        else:
            features.append(0.0)
        
        # Speaking rate proxy (zero crossings / duration)
        duration = len(audio) / sr
        features.append(float(np.sum(zcr) / duration))
        
        return np.array(features)
        
    except Exception as e:
        print(f"\n⚠️  Error processing {audio_path.name}: {e}")
        return None


def load_dataset_advanced():
    """Load dataset with advanced feature extraction."""
    print("\n" + "="*80)
    print("📥 LOADING DATASET WITH ADVANCED FEATURES")
    print("="*80)
    
    if not DATASET_PATH.exists():
        print(f"❌ Dataset not found at: {DATASET_PATH}")
        return None, None
    
    # Get all WAV files
    audio_files = list(DATASET_PATH.glob("*.wav"))
    print(f"\n✅ Found {len(audio_files)} audio files")
    
    # Extract features
    print(f"\n⚙️  Extracting 40+ features per file...")
    print("💡 This will take 15-25 minutes for comprehensive analysis\n")
    
    X_list = []
    y_list = []
    emotion_counts = {}
    skipped = 0
    
    # Process in batches
    for i in tqdm(range(0, len(audio_files), BATCH_SIZE), desc="Processing batches"):
        batch_files = audio_files[i:i+BATCH_SIZE]
        
        for audio_file in batch_files:
            # Parse emotion
            emotion = parse_filename(audio_file)
            
            if emotion not in EMOTION_STRESS_MAP:
                skipped += 1
                continue
            
            # Extract features
            features = extract_advanced_features(audio_file)
            
            if features is not None:
                X_list.append(features)
                y_list.append(EMOTION_STRESS_MAP[emotion])
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            else:
                skipped += 1
    
    # Convert to numpy arrays
    X = np.array(X_list)
    y = np.array(y_list)
    
    print(f"\n✅ Feature extraction complete!")
    print(f"\n📊 Dataset Statistics:")
    print(f"   Processed: {len(X)} samples")
    print(f"   Skipped:   {skipped} samples")
    print(f"   Features:  {X.shape[1]} per sample")
    
    print(f"\n📈 Emotion Distribution:")
    for emotion, count in sorted(emotion_counts.items(), key=lambda x: EMOTION_STRESS_MAP[x[0]]):
        stress = EMOTION_STRESS_MAP[emotion]
        bar = "█" * (count // 20)
        print(f"   {emotion:15s} ({stress:2d}): {bar} {count:4d} samples")
    
    return X, y


def train_xgboost_advanced(X, y):
    """Train XGBoost with hyperparameter tuning and cross-validation."""
    print("\n" + "="*80)
    print("🚀 TRAINING ADVANCED XGBOOST MODEL")
    print("="*80)
    
    # Split dataset
    print("\n📊 Splitting dataset (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Training:   {len(X_train)} samples")
    print(f"   Testing:    {len(X_test)} samples")
    
    # Use RobustScaler (better for outliers)
    print("\n⚙️  Normalizing features with RobustScaler...")
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Hyperparameter tuning with GridSearch
    print("\n🔍 Hyperparameter Tuning (this will take 20-30 minutes)...")
    print("   Testing different combinations to find optimal settings...\n")
    
    param_grid = {
        'n_estimators': [300, 500],
        'max_depth': [6, 8, 10],
        'learning_rate': [0.05, 0.1],
        'subsample': [0.8, 0.9],
        'colsample_bytree': [0.8, 0.9],
        'min_child_weight': [1, 3],
        'gamma': [0, 0.1],
    }
    
    # Try GPU acceleration first, fall back to CPU if unavailable
    try:
        base_model = xgb.XGBRegressor(
            random_state=42,
            tree_method='gpu_hist',  # GPU-accelerated histogram method
            gpu_id=0,
            predictor='gpu_predictor',
            verbosity=1
        )
        print("   🎮 GPU acceleration enabled!")
    except Exception as e:
        print(f"   ⚠️  GPU not available ({e}), using CPU with all cores")
        base_model = xgb.XGBRegressor(
            random_state=42,
            tree_method='hist',
            n_jobs=-1,
            verbosity=0
        )
    
    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=5,  # 5-fold cross-validation
        scoring='neg_mean_absolute_error',
        n_jobs=1,  # Fixed for Windows compatibility
        verbose=2
    )
    
    grid_search.fit(X_train_scaled, y_train)
    
    print(f"\n✅ Best parameters found:")
    for param, value in grid_search.best_params_.items():
        print(f"   {param}: {value}")
    
    # Get best model
    model = grid_search.best_estimator_
    
    # Evaluate
    print("\n" + "="*80)
    print("📊 MODEL EVALUATION")
    print("="*80)
    
    # Training predictions
    y_train_pred = model.predict(X_train_scaled)
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    
    print(f"\n📈 Training Set:")
    print(f"   MAE:  {train_mae:.2f} points")
    print(f"   RMSE: {train_rmse:.2f} points")
    print(f"   R²:   {train_r2:.4f}")
    
    # Test predictions
    y_test_pred = model.predict(X_test_scaled)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_r2 = r2_score(y_test, y_test_pred)
    
    print(f"\n📉 Test Set:")
    print(f"   MAE:  {test_mae:.2f} points")
    print(f"   RMSE: {test_rmse:.2f} points")
    print(f"   R²:   {test_r2:.4f}")
    
    # Accuracy metrics
    accuracy_5 = np.mean(np.abs(y_test - y_test_pred) <= 5) * 100
    accuracy_10 = np.mean(np.abs(y_test - y_test_pred) <= 10) * 100
    accuracy_15 = np.mean(np.abs(y_test - y_test_pred) <= 15) * 100
    
    print(f"\n🎯 Accuracy:")
    print(f"   Within ± 5 points:  {accuracy_5:.1f}%")
    print(f"   Within ±10 points:  {accuracy_10:.1f}%")
    print(f"   Within ±15 points:  {accuracy_15:.1f}%")
    
    # Cross-validation score
    print(f"\n🔄 Cross-Validation (5-fold):")
    cv_scores = cross_val_score(
        model, X_train_scaled, y_train,
        cv=5, scoring='neg_mean_absolute_error', n_jobs=1  # Windows fix
    )
    print(f"   CV MAE: {-cv_scores.mean():.2f} ± {cv_scores.std():.2f}")
    
    # Feature importance
    print(f"\n🔍 Top 15 Most Important Features:")
    feature_importance = model.feature_importances_
    top_indices = np.argsort(feature_importance)[-15:][::-1]
    
    for idx in top_indices:
        bar = "█" * int(feature_importance[idx] * 50)
        print(f"   Feature {idx:2d}: {bar} {feature_importance[idx]:.4f}")
    
    return model, scaler, {
        'train_mae': float(train_mae),
        'train_rmse': float(train_rmse),
        'train_r2': float(train_r2),
        'test_mae': float(test_mae),
        'test_rmse': float(test_rmse),
        'test_r2': float(test_r2),
        'accuracy_5': float(accuracy_5),
        'accuracy_10': float(accuracy_10),
        'accuracy_15': float(accuracy_15),
        'cv_mae_mean': float(-cv_scores.mean()),
        'cv_mae_std': float(cv_scores.std()),
        'best_params': grid_search.best_params_,
    }


def save_model(model, scaler, metrics):
    """Save trained model and metadata."""
    print("\n" + "="*80)
    print("💾 SAVING MODEL")
    print("="*80)
    
    # Save XGBoost model
    model_path = MODEL_SAVE_PATH / "voice_stress_xgboost_advanced.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✅ Model saved: {model_path}")
    
    # Save scaler
    scaler_path = MODEL_SAVE_PATH / "feature_scaler_advanced.pkl"
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"✅ Scaler saved: {scaler_path}")
    
    # Save metrics
    metrics_path = MODEL_SAVE_PATH / "training_metrics_advanced.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=4)
    print(f"✅ Metrics saved: {metrics_path}")
    
    # Save emotion mapping
    mapping_path = MODEL_SAVE_PATH / "emotion_stress_map_advanced.json"
    with open(mapping_path, 'w') as f:
        json.dump(EMOTION_STRESS_MAP, f, indent=4)
    print(f"✅ Emotion mapping saved: {mapping_path}")
    
    print(f"\n📦 All files saved to: {MODEL_SAVE_PATH}")


def main():
    """Main training pipeline."""
    print("\n🔧 System Check:")
    print(f"   Dataset: {DATASET_PATH.exists()}")
    print(f"   Path: {DATASET_PATH}")
    
    try:
        # Step 1: Load dataset with advanced features
        X, y = load_dataset_advanced()
        
        if X is None or len(X) < 100:
            print("\n❌ Insufficient data. Need at least 100 samples.")
            return
        
        print(f"\n✅ Ready to train with {len(X)} samples and {X.shape[1]} features")
        
        # Step 2: Train model with hyperparameter tuning
        model, scaler, metrics = train_xgboost_advanced(X, y)
        
        # Step 3: Save model
        save_model(model, scaler, metrics)
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 TRAINING COMPLETE!")
        print("="*80)
        
        accuracy_10 = metrics['accuracy_10']
        test_mae = metrics['test_mae']
        test_r2 = metrics['test_r2']
        
        print(f"\n✅ Final Performance:")
        print(f"   Accuracy (±10): {accuracy_10:.1f}%")
        print(f"   Test MAE:       {test_mae:.2f} points")
        print(f"   R² Score:       {test_r2:.4f}")
        
        if accuracy_10 >= 75:
            print(f"\n🎯 SUCCESS! Achieved target accuracy: {accuracy_10:.1f}% >= 75%")
        elif accuracy_10 >= 65:
            print(f"\n✅ Good accuracy: {accuracy_10:.1f}% (target was 75%)")
        else:
            print(f"\n⚠️  Accuracy {accuracy_10:.1f}% below target of 75%")
            print("   Consider: more data, different features, or ensemble methods")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Test with: python test_trained_model.py")
        print(f"   2. Integrate into your voice analyzer")
        print(f"   3. Deploy to production!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
