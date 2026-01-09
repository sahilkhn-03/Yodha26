"""
Heart Rate Stress Classification Model Training
Trains a classifier to predict stress vs normal state from heart rate data.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import json
from datetime import datetime

# Load dataset
print("=" * 60)
print("HEART RATE STRESS CLASSIFICATION MODEL TRAINING")
print("=" * 60)

dataset_path = "ml_dataset/heartrate_training_data_20260110_015535.csv"
df = pd.read_csv(dataset_path)

print(f"\n✅ Loaded dataset: {len(df)} samples")
print(f"   Columns: {list(df.columns)}")

# Prepare features and labels
# Binary classification: Normal (0) vs Stress (1)
# Threshold: stress_level >= 0.5 = Stressed
df['label'] = (df['stress_level'] >= 0.5).astype(int)

print(f"\n📊 Class Distribution:")
print(f"   Normal (label=0): {(df['label'] == 0).sum()} samples")
print(f"   Stress (label=1): {(df['label'] == 1).sum()} samples")

# Feature engineering
X = df[['bpm']].copy()  # Start with just BPM
y = df['label']

# Add derived features for better classification
X['bpm_squared'] = X['bpm'] ** 2
X['bpm_normalized'] = (X['bpm'] - 70) / 30  # Normalize around typical resting HR

print(f"\n🔧 Features: {list(X.columns)}")
print(f"   Feature shape: {X.shape}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

print(f"\n✂️  Train/Test Split:")
print(f"   Training samples: {len(X_train)}")
print(f"   Testing samples: {len(X_test)}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train Random Forest Classifier
print(f"\n🤖 Training Random Forest Classifier...")
clf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    class_weight='balanced',  # Handle any class imbalance
    random_state=42,
    n_jobs=-1
)

clf.fit(X_train_scaled, y_train)

# Evaluate on test set
y_pred = clf.predict(X_test_scaled)
y_pred_proba = clf.predict_proba(X_test_scaled)

print(f"\n" + "=" * 60)
print("📈 MODEL PERFORMANCE")
print("=" * 60)

accuracy = accuracy_score(y_test, y_pred)
print(f"\n✅ Accuracy: {accuracy * 100:.2f}%")

print(f"\n📊 Classification Report:")
print(classification_report(y_test, y_pred, target_names=['Normal', 'Stress']))

print(f"\n🎯 Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
print(f"                Predicted")
print(f"                Normal  Stress")
print(f"Actual Normal    {cm[0][0]:3d}     {cm[0][1]:3d}")
print(f"Actual Stress    {cm[1][0]:3d}     {cm[1][1]:3d}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': clf.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n🔍 Feature Importance:")
for idx, row in feature_importance.iterrows():
    print(f"   {row['feature']:20s}: {row['importance']:.4f}")

# Save model, scaler, and metadata
model_dir = "models"
import os
os.makedirs(model_dir, exist_ok=True)

model_path = f"{model_dir}/heartrate_stress_classifier.pkl"
scaler_path = f"{model_dir}/heartrate_scaler.pkl"
metadata_path = f"{model_dir}/heartrate_model_metadata.json"

joblib.dump(clf, model_path)
joblib.dump(scaler, scaler_path)

metadata = {
    "model_type": "RandomForestClassifier",
    "accuracy": float(accuracy),
    "training_samples": int(len(X_train)),
    "test_samples": int(len(X_test)),
    "features": list(X.columns),
    "classes": ["Normal", "Stress"],
    "threshold": 0.5,
    "trained_at": datetime.now().isoformat(),
    "dataset": dataset_path
}

with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n" + "=" * 60)
print("💾 MODEL SAVED")
print("=" * 60)
print(f"   Model: {model_path}")
print(f"   Scaler: {scaler_path}")
print(f"   Metadata: {metadata_path}")

# Test predictions on sample data
print(f"\n" + "=" * 60)
print("🧪 SAMPLE PREDICTIONS")
print("=" * 60)

test_cases = [
    {"bpm": 72, "expected": "Normal"},
    {"bpm": 65, "expected": "Normal"},
    {"bpm": 80, "expected": "Normal"},
    {"bpm": 125, "expected": "Stress"},
    {"bpm": 110, "expected": "Stress"},
    {"bpm": 135, "expected": "Stress"}
]

for case in test_cases:
    bpm = case['bpm']
    features = pd.DataFrame({
        'bpm': [bpm],
        'bpm_squared': [bpm ** 2],
        'bpm_normalized': [(bpm - 70) / 30]
    })
    features_scaled = scaler.transform(features)
    pred_proba = clf.predict_proba(features_scaled)[0]
    pred_label = clf.predict(features_scaled)[0]
    pred_class = "Stress" if pred_label == 1 else "Normal"
    
    print(f"\n   BPM: {bpm:3d} → {pred_class:6s} (confidence: {pred_proba[pred_label]*100:.1f}%)")
    print(f"      Expected: {case['expected']}")
    print(f"      Probabilities: Normal={pred_proba[0]*100:.1f}%, Stress={pred_proba[1]*100:.1f}%")

print(f"\n" + "=" * 60)
print("✅ TRAINING COMPLETE!")
print("=" * 60)
print("\nNext steps:")
print("1. Use the model via API: POST /api/ml/predict")
print("2. Test with ECG simulator data")
print("3. Retrain with more data as needed")
