"""
Voice Stress Detection Model Training Pipeline
XGBoost model trained on JL-Corpus dataset
Optimized for laptop specs (7GB RAM, CPU-only)
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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# Import our feature extractor
from voice_stress_analyzer import VoiceStressAnalyzer

print("\n" + "="*80)
print(" "*20 + "🎯 VOICE STRESS MODEL TRAINING")
print("="*80)

# Configuration
DATASET_PATH = Path(__file__).parent / "dataset" / "Raw JL corpus (unchecked and unannotated)" / "JL(wav+txt)"
MODEL_SAVE_PATH = Path(__file__).parent / "models"
SAMPLE_RATE = 16000
BATCH_SIZE = 50  # Process in batches to manage RAM

# Emotion to stress mapping (0-100 scale)
EMOTION_STRESS_MAP = {
    'neutral': 15,      # Low stress - calm baseline
    'assertive': 25,    # Low-moderate - confident, controlled
    'encouraging': 20,  # Low - positive, supportive
    'happy': 18,        # Low - positive emotion
    'excited': 45,      # Moderate - high arousal, but positive
    'concerned': 65,    # High - worried, anxious
    'apologetic': 55,   # Moderate-high - tense, uncomfortable
    'sad': 70,          # High - emotional distress
}

print(f"\n📂 Dataset location: {DATASET_PATH}")
print(f"💾 Models will be saved to: {MODEL_SAVE_PATH}")
MODEL_SAVE_PATH.mkdir(exist_ok=True)


def parse_filename(filename):
    """
    Extract emotion label from filename.
    Format: speaker_emotion_utterance_version.wav
    Example: male2_concerned_10a_1.wav → concerned
    """
    parts = filename.stem.split('_')
    if len(parts) >= 2:
        emotion = parts[1]
        return emotion
    return None


def extract_features_from_file(audio_path, analyzer):
    """Extract all voice stress features from audio file."""
    try:
        # Load audio
        audio, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
        
        # Skip very short files
        if len(audio) < sr * 0.5:  # Less than 0.5 seconds
            return None
        
        # Use our analyzer to get features
        result = analyzer.analyze_audio(audio, sr)
        
        # Create feature vector
        features = np.array([
            result['pitch_variability'],
            result['jitter'],
            result['energy'],
            result['speaking_rate'],
            result['raw_features']['pitch_std_hz'],
            result['raw_features']['jitter_hz'],
            result['raw_features']['energy_std'],
            result['raw_features']['zcr_std'],
        ])
        
        return features
        
    except Exception as e:
        print(f"Error processing {audio_path.name}: {e}")
        return None


def load_dataset():
    """Load and process the JL-Corpus dataset."""
    print("\n" + "="*80)
    print("📥 LOADING DATASET")
    print("="*80)
    
    if not DATASET_PATH.exists():
        print(f"❌ Dataset not found at: {DATASET_PATH}")
        print("\n💡 Make sure you've extracted the JL-Corpus dataset to the correct location.")
        return None, None
    
    # Get all WAV files
    audio_files = list(DATASET_PATH.glob("*.wav"))
    print(f"\n✅ Found {len(audio_files)} audio files")
    
    # Initialize analyzer
    print("\n🔧 Initializing feature extractor...")
    analyzer = VoiceStressAnalyzer(sample_rate=SAMPLE_RATE)
    
    # Extract features and labels
    print("\n⚙️  Extracting features (this may take 10-15 minutes)...")
    print("💡 Tip: Close other applications to free up RAM\n")
    
    X_list = []
    y_list = []
    emotion_counts = {}
    
    # Process in batches
    for i in tqdm(range(0, len(audio_files), BATCH_SIZE), desc="Processing batches"):
        batch_files = audio_files[i:i+BATCH_SIZE]
        
        for audio_file in batch_files:
            # Parse emotion from filename
            emotion = parse_filename(audio_file)
            
            if emotion not in EMOTION_STRESS_MAP:
                continue
            
            # Extract features
            features = extract_features_from_file(audio_file, analyzer)
            
            if features is not None:
                X_list.append(features)
                y_list.append(EMOTION_STRESS_MAP[emotion])
                
                # Count emotions
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    # Convert to numpy arrays
    X = np.array(X_list)
    y = np.array(y_list)
    
    print(f"\n✅ Feature extraction complete!")
    print(f"\n📊 Dataset Statistics:")
    print(f"   Total samples: {len(X)}")
    print(f"   Features per sample: {X.shape[1]}")
    print(f"\n📈 Emotion distribution:")
    for emotion, count in sorted(emotion_counts.items()):
        stress_level = EMOTION_STRESS_MAP[emotion]
        print(f"   {emotion:15s}: {count:4d} samples (stress: {stress_level}/100)")
    
    return X, y


def train_xgboost_model(X, y):
    """Train XGBoost model optimized for laptop specs."""
    print("\n" + "="*80)
    print("🚀 TRAINING XGBOOST MODEL")
    print("="*80)
    
    # Split dataset
    print("\n📊 Splitting dataset (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Training samples: {len(X_train)}")
    print(f"   Testing samples:  {len(X_test)}")
    
    # Normalize features
    print("\n⚙️  Normalizing features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost model (optimized for CPU)
    print("\n🎯 Training XGBoost model...")
    print("   (This will take 10-20 minutes...)\n")
    
    model = xgb.XGBRegressor(
        n_estimators=200,           # Number of trees
        max_depth=6,                # Tree depth (prevents overfitting)
        learning_rate=0.1,          # Step size
        subsample=0.8,              # Use 80% of data per tree
        colsample_bytree=0.8,       # Use 80% of features per tree
        random_state=42,
        tree_method='hist',         # Fast histogram-based method (CPU-friendly)
        n_jobs=-1,                  # Use all CPU cores
        verbosity=1
    )
    
    # Train with progress
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=True
    )
    
    # Evaluate
    print("\n✅ Training complete!")
    print("\n📊 MODEL EVALUATION")
    print("="*80)
    
    # Training predictions
    y_train_pred = model.predict(X_train_scaled)
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    
    print(f"\n📈 Training Set Performance:")
    print(f"   MAE (Mean Absolute Error): {train_mae:.2f}")
    print(f"   RMSE (Root Mean Squared):  {train_rmse:.2f}")
    print(f"   R² Score:                  {train_r2:.4f}")
    
    # Test predictions
    y_test_pred = model.predict(X_test_scaled)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_r2 = r2_score(y_test, y_test_pred)
    
    print(f"\n📉 Test Set Performance:")
    print(f"   MAE (Mean Absolute Error): {test_mae:.2f}")
    print(f"   RMSE (Root Mean Squared):  {test_rmse:.2f}")
    print(f"   R² Score:                  {test_r2:.4f}")
    
    # Calculate accuracy (within ±10 points)
    accuracy_10 = np.mean(np.abs(y_test - y_test_pred) <= 10) * 100
    accuracy_15 = np.mean(np.abs(y_test - y_test_pred) <= 15) * 100
    
    print(f"\n🎯 Accuracy Metrics:")
    print(f"   Within ±10 points: {accuracy_10:.1f}%")
    print(f"   Within ±15 points: {accuracy_15:.1f}%")
    
    # Feature importance
    print(f"\n🔍 Feature Importance:")
    feature_names = [
        'Pitch Variability',
        'Jitter',
        'Energy',
        'Speaking Rate',
        'Pitch Std (Hz)',
        'Jitter (Hz)',
        'Energy Std',
        'ZCR Std'
    ]
    
    importances = model.feature_importances_
    for name, importance in zip(feature_names, importances):
        bar = "█" * int(importance * 50)
        print(f"   {name:20s}: {bar} {importance:.4f}")
    
    return model, scaler, {
        'train_mae': float(train_mae),
        'train_rmse': float(train_rmse),
        'train_r2': float(train_r2),
        'test_mae': float(test_mae),
        'test_rmse': float(test_rmse),
        'test_r2': float(test_r2),
        'accuracy_10': float(accuracy_10),
        'accuracy_15': float(accuracy_15),
    }


def save_model(model, scaler, metrics):
    """Save trained model and scaler."""
    print("\n" + "="*80)
    print("💾 SAVING MODEL")
    print("="*80)
    
    # Save XGBoost model
    model_path = MODEL_SAVE_PATH / "voice_stress_xgboost.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✅ Model saved: {model_path}")
    
    # Save scaler
    scaler_path = MODEL_SAVE_PATH / "feature_scaler.pkl"
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"✅ Scaler saved: {scaler_path}")
    
    # Save metrics
    metrics_path = MODEL_SAVE_PATH / "training_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=4)
    print(f"✅ Metrics saved: {metrics_path}")
    
    # Save emotion mapping
    mapping_path = MODEL_SAVE_PATH / "emotion_stress_map.json"
    with open(mapping_path, 'w') as f:
        json.dump(EMOTION_STRESS_MAP, f, indent=4)
    print(f"✅ Emotion mapping saved: {mapping_path}")
    
    print(f"\n📦 All files saved to: {MODEL_SAVE_PATH}")


def main():
    """Main training pipeline."""
    print("\n🔧 System Check:")
    print(f"   Working directory: {Path.cwd()}")
    print(f"   Dataset path: {DATASET_PATH}")
    print(f"   Dataset exists: {DATASET_PATH.exists()}")
    
    try:
        # Step 1: Load dataset
        X, y = load_dataset()
        
        if X is None:
            print("\n❌ Failed to load dataset. Exiting.")
            return
        
        if len(X) < 100:
            print(f"\n⚠️  Warning: Only {len(X)} samples found. Recommended: 500+")
            proceed = input("\n   Continue anyway? (y/n): ")
            if proceed.lower() != 'y':
                return
        
        # Step 2: Train model
        model, scaler, metrics = train_xgboost_model(X, y)
        
        # Step 3: Save model
        save_model(model, scaler, metrics)
        
        # Success!
        print("\n" + "="*80)
        print("🎉 MODEL TRAINING COMPLETE!")
        print("="*80)
        
        print(f"\n✅ Final Performance:")
        print(f"   Test MAE:  {metrics['test_mae']:.2f} points")
        print(f"   Test RMSE: {metrics['test_rmse']:.2f} points")
        print(f"   R² Score:  {metrics['test_r2']:.4f}")
        print(f"   Accuracy (±10): {metrics['accuracy_10']:.1f}%")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Test the model with: python test_trained_model.py")
        print(f"   2. Use in production with the ML-powered analyzer")
        print(f"   3. Integrate into your FastAPI backend")
        
        print("\n✨ Your voice stress model is ready for deployment!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
