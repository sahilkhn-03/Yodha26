"""
Simple, Fast, Reliable Voice Stress Model Training
No GPU complications - just CPU training that works
Target: >75% accuracy in 30-40 minutes
"""

import numpy as np
import librosa
from pathlib import Path
import pickle
import json
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

print("\n" + "="*80)
print(" "*25 + "VOICE STRESS TRAINING")
print(" "*20 + "Simple, Fast, Reliable")
print("="*80)

DATASET_PATH = Path(__file__).parent / "dataset" / "Raw JL corpus (unchecked and unannotated)" / "JL(wav+txt)"
MODEL_SAVE_PATH = Path(__file__).parent / "models"
MODEL_SAVE_PATH.mkdir(exist_ok=True)

SAMPLE_RATE = 22050
BATCH_SIZE = 50

# Improved emotion mapping
EMOTION_MAP = {
    'neutral': 10, 'happy': 15, 'encouraging': 18, 'assertive': 35,
    'excited': 50, 'apologetic': 58, 'sad': 68, 'concerned': 72,
}


def extract_features(audio_path):
    """Extract 55 comprehensive audio features."""
    try:
        audio, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
        if len(audio) < sr * 0.3:
            return None
        
        audio = librosa.util.normalize(audio)
        features = []
        
        # MFCC (26 features)
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        features.extend(np.mean(mfcc, axis=1).flatten().tolist())
        features.extend(np.std(mfcc, axis=1).flatten().tolist())
        
        # Spectral (10 features)
        features.append(float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))))
        features.append(float(np.std(librosa.feature.spectral_centroid(y=audio, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr))))
        features.append(float(np.std(librosa.feature.spectral_rolloff(y=audio, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr))))
        features.append(float(np.std(librosa.feature.spectral_bandwidth(y=audio, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_contrast(y=audio, sr=sr))))
        features.append(float(np.std(librosa.feature.spectral_contrast(y=audio, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_flatness(y=audio))))
        features.append(float(np.std(librosa.feature.spectral_flatness(y=audio))))
        
        # Chroma (2 features)
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        features.append(float(np.mean(chroma)))
        features.append(float(np.std(chroma)))
        
        # ZCR (2 features)
        zcr = librosa.feature.zero_crossing_rate(audio)
        features.append(float(np.mean(zcr)))
        features.append(float(np.std(zcr)))
        
        # RMS Energy (4 features)
        rms = librosa.feature.rms(y=audio)
        features.append(float(np.mean(rms)))
        features.append(float(np.std(rms)))
        features.append(float(np.max(rms)))
        features.append(float(np.min(rms)))
        
        # Pitch (6 features)
        f0, _, _ = librosa.pyin(audio, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr)
        f0_clean = f0[~np.isnan(f0)]
        if len(f0_clean) > 1:
            features.extend([
                float(np.mean(f0_clean)), float(np.std(f0_clean)),
                float(np.max(f0_clean)), float(np.min(f0_clean)),
                float(np.ptp(f0_clean)), float(np.mean(np.abs(np.diff(f0_clean))))
            ])
        else:
            features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        # Tempo (2 features)
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
        features.append(float(tempo))
        features.append(float(len(beats) / (len(audio) / sr)))
        
        # Prosodic (3 features)
        features.append(float(np.var(rms[0])))
        features.append(float(np.var(f0_clean)) if len(f0_clean) > 0 else 0.0)
        features.append(float(np.sum(zcr) / (len(audio) / sr)))
        
        return np.array(features)
    except:
        return None


def load_dataset():
    """Load and process dataset."""
    print(f"\n📂 Loading from: {DATASET_PATH}")
    
    audio_files = list(DATASET_PATH.glob("*.wav"))
    print(f"✅ Found {len(audio_files)} files\n")
    
    print("⚙️  Extracting features (15-20 minutes)...\n")
    
    X_list, y_list = [], []
    emotion_counts = {}
    
    for i in tqdm(range(0, len(audio_files), BATCH_SIZE), desc="Processing"):
        for audio_file in audio_files[i:i+BATCH_SIZE]:
            emotion = audio_file.stem.split('_')[1] if len(audio_file.stem.split('_')) >= 2 else None
            if emotion not in EMOTION_MAP:
                continue
            
            features = extract_features(audio_file)
            if features is not None:
                X_list.append(features)
                y_list.append(EMOTION_MAP[emotion])
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    X, y = np.array(X_list), np.array(y_list)
    
    print(f"\n✅ Extracted {len(X)} samples with {X.shape[1]} features")
    print(f"\n📊 Distribution:")
    for emotion, count in sorted(emotion_counts.items(), key=lambda x: EMOTION_MAP[x[0]]):
        print(f"   {emotion:12s} ({EMOTION_MAP[emotion]:2d}): {count:4d} samples")
    
    return X, y


def train_model(X, y):
    """Train emotion classifier, then map to stress scores."""
    print("\n" + "="*80)
    print("🚀 TRAINING EMOTION CLASSIFIER")
    print("="*80)
    
    # Convert stress scores back to emotion labels for classification
    stress_to_emotion = {10: 0, 15: 1, 18: 2, 35: 3, 50: 4, 58: 5, 68: 6, 72: 7}
    y_emotion = np.array([stress_to_emotion[score] for score in y])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_emotion, test_size=0.2, random_state=42, stratify=y_emotion)
    print(f"\n📊 Train: {len(X_train)} | Test: {len(X_test)}")
    
    print("\n⚙️  Normalizing features...")
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("\n🎯 Training XGBoost Classifier (CPU only)...")
    print("   Training for emotion recognition...\n")
    
    model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=8,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=2,
        gamma=0.1,
        random_state=42,
        tree_method='hist',
        device='cpu',
        num_class=8
    )
    
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    print("✅ Training complete!\n")
    
    # Evaluate emotion classification
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    train_accuracy = np.mean(y_train_pred == y_train) * 100
    test_accuracy = np.mean(y_test_pred == y_test) * 100
    
    # Convert predictions back to stress scores
    emotion_to_stress = {0: 10, 1: 15, 2: 18, 3: 35, 4: 50, 5: 58, 6: 68, 7: 72}
    y_test_stress_pred = np.array([emotion_to_stress[e] for e in y_test_pred])
    y_test_stress_true = np.array([emotion_to_stress[e] for e in y_test])
    
    test_mae = mean_absolute_error(y_test_stress_true, y_test_stress_pred)
    test_r2 = r2_score(y_test_stress_true, y_test_stress_pred)
    
    print("="*80)
    print("📊 RESULTS")
    print("="*80)
    print(f"\n✅ Emotion Classification Accuracy:")
    print(f"   Train: {train_accuracy:.1f}%")
    print(f"   Test:  {test_accuracy:.1f}%")
    
    print(f"\n✅ Stress Detection Performance:")
    print(f"   MAE:  {test_mae:.2f} points")
    print(f"   R²:   {test_r2:.4f}")
    
    if test_accuracy >= 70:
        print(f"\n🎉 SUCCESS! Emotion accuracy {test_accuracy:.1f}% >= 70%")
        print(f"   → Stress detection is reliable!")
    elif test_accuracy >= 60:
        print(f"\n✅ Good: {test_accuracy:.1f}% emotion accuracy")
    else:
        print(f"\n⚠️  {test_accuracy:.1f}% - needs improvement")
    
    return model, scaler, {
        'emotion_train_accuracy': float(train_accuracy),
        'emotion_test_accuracy': float(test_accuracy),
        'stress_mae': float(test_mae),
        'stress_r2': float(test_r2)
    }


def save_model(model, scaler, metrics):
    """Save everything."""
    print("\n" + "="*80)
    print("💾 SAVING")
    print("="*80 + "\n")
    
    with open(MODEL_SAVE_PATH / "voice_stress_model.pkl", 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ Model: voice_stress_model.pkl")
    
    with open(MODEL_SAVE_PATH / "scaler.pkl", 'wb') as f:
        pickle.dump(scaler, f)
    print(f"✅ Scaler: scaler.pkl")
    
    with open(MODEL_SAVE_PATH / "metrics.json", 'w') as f:
        json.dump(metrics, f, indent=4)
    print(f"✅ Metrics: metrics.json")
    
    print(f"\n📦 Saved to: {MODEL_SAVE_PATH}")


if __name__ == "__main__":
    try:
        X, y = load_dataset()
        if len(X) < 100:
            print("❌ Not enough data")
            exit(1)
        
        model, scaler, metrics = train_model(X, y)
        save_model(model, scaler, metrics)
        
        print("\n" + "="*80)
        print("🎉 DONE!")
        print("="*80)
        print(f"\nEmotion Recognition: {metrics['emotion_test_accuracy']:.1f}%")
        print(f"Stress Detection MAE: {metrics['stress_mae']:.1f} points")
        print("\n✅ Model maps emotions to stress levels")
        print("Ready to use!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
