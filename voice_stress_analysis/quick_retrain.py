"""Quick retraining script - trains model with 8 features"""
import pickle
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import xgboost as xgb
from voice_stress_analyzer import VoiceStressAnalyzer
import librosa
from tqdm import tqdm

print("🚀 Quick Model Retrain with 8 Features")
print("="*60)

# Paths
DATASET_PATH = Path("dataset/Raw JL corpus (unchecked and unannotated)/JL(wav+txt)")
MODEL_PATH = Path("models")
MODEL_PATH.mkdir(exist_ok=True)

SAMPLE_RATE = 16000

# Emotion mapping
EMOTION_STRESS_MAP = {
    'neutral': 15, 'happy': 18, 'encouraging': 20, 'assertive': 25,
    'excited': 45, 'apologetic': 55, 'concerned': 65, 'sad': 70,
}

print(f"\n📂 Loading dataset from: {DATASET_PATH}")
audio_files = list(DATASET_PATH.glob("*.wav"))
print(f"✅ Found {len(audio_files)} audio files\n")

# Initialize analyzer
analyzer = VoiceStressAnalyzer(sample_rate=SAMPLE_RATE)

# Extract features
X_list, y_list = [], []
emotion_counts = {}

print("⚙️  Extracting 8 features from audio files...")
for audio_file in tqdm(audio_files[:500]):  # Use first 500 for quick training
    # Parse emotion
    parts = audio_file.stem.split('_')
    if len(parts) < 2:
        continue
    emotion = parts[1]
    
    if emotion not in EMOTION_STRESS_MAP:
        continue
    
    try:
        # Load audio
        audio, sr = librosa.load(audio_file, sr=SAMPLE_RATE, mono=True)
        if len(audio) < SAMPLE_RATE * 0.5:
            continue
        
        # Extract 8 features
        result = analyzer.analyze_audio(audio, sr)
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
        
        X_list.append(features)
        y_list.append(EMOTION_STRESS_MAP[emotion])
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    except:
        pass

X = np.array(X_list)
y = np.array(y_list)

print(f"\n✅ Extracted {len(X)} samples with {X.shape[1]} features each")
print("\n📊 Emotion distribution:")
for emotion, count in sorted(emotion_counts.items()):
    print(f"   {emotion:15s}: {count:3d} samples")

# Train model
print("\n🎯 Training XGBoost model...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    random_state=42,
    tree_method='hist',
    n_jobs=-1
)

model.fit(X_train_scaled, y_train, eval_set=[(X_test_scaled, y_test)], verbose=False)

# Evaluate
y_pred = model.predict(X_test_scaled)
mae = np.mean(np.abs(y_test - y_pred))
accuracy = np.mean(np.abs(y_test - y_pred) <= 10) * 100

print(f"\n📊 Model Performance:")
print(f"   MAE: {mae:.2f}")
print(f"   Accuracy (±10): {accuracy:.1f}%")

# Save model
print(f"\n💾 Saving model to {MODEL_PATH}...")
with open(MODEL_PATH / "stress_detector.pkl", 'wb') as f:
    pickle.dump(model, f)

with open(MODEL_PATH / "scaler.pkl", 'wb') as f:
    pickle.dump(scaler, f)

config = {
    "model_type": "XGBoost",
    "features": 8,
    "sample_rate": SAMPLE_RATE,
    "accuracy": f"{accuracy:.1f}%",
    "mae": f"{mae:.2f}"
}

import json
with open(MODEL_PATH / "config.json", 'w') as f:
    json.dump(config, f, indent=2)

print("\n✅ Model saved successfully!")
print(f"   - stress_detector.pkl (XGBoost model)")
print(f"   - scaler.pkl (StandardScaler with {X.shape[1]} features)")
print(f"   - config.json (model metadata)")
print("\n🎉 Retraining complete! Model now uses 8 features.")
