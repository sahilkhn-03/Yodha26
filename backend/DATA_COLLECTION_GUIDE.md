# 🫀 Heart Rate Training Data Collection System

## ✅ System Ready!

Your training data collection system is **fully set up** and ready to use! Here's how to collect labeled heart rate data for your ML model.

---

## 🚀 How to Use

### Step 1: Start Both Servers

You need **TWO terminals** running simultaneously:

**Terminal 1 - Main Backend (Port 8000):**
```powershell
cd D:\Yodha26\backend
uvicorn main:app --reload
```

**Terminal 2 - Heartbeat Simulator (Port 8001):**
```powershell
cd D:\Yodha26\backend
uvicorn heartbeat_sim:app --port 8001 --reload
```

### Step 2: Open the Data Collection Interface

Open in your browser:
```
http://localhost:8001/heartbeat_monitor.html
```

### Step 3: Collect Training Data

1. **Start Simulation**: Click "▶️ Start" button
2. **Enable Auto-Collection**: Check the "Enable Auto-Collection" checkbox
3. **Monitor Collection**: Watch the stats update in real-time:
   - Total Samples collected
   - Normal samples (stress_level ≤ 0.5)
   - Abnormal samples (stress_level > 0.5)

4. **Trigger Stress Events**: Click "⚡ Stress" button to simulate stress episodes
   - This increases heart rate and stress level
   - Collects abnormal/stressed samples for balanced dataset

5. **Let it Run**: The system auto-collects data every 2 seconds while running

### Step 4: Download Your Dataset

Once you've collected enough samples (aim for 200+ minimum):

**Option A - Browser Download:**
```
http://localhost:8000/api/training/export/csv
```

**Option B - Using curl:**
```powershell
curl -o heartrate_dataset.csv http://localhost:8000/api/training/export/csv
```

---

## 📊 Dataset Format

The exported CSV contains:
- `id` - Record ID
- `timestamp` - When recorded
- `bpm` - Heart rate in beats per minute
- `stress_level` - **Your ML target variable** (0.0 = normal, 1.0 = stressed)
- `systolic` / `diastolic` - Blood pressure (optional)
- `notes` - Auto-added metadata

---

## 🎯 Recommended Collection Strategy

For a **balanced dataset**:

1. **Normal State (5 minutes)**: Let simulation run normally
   - Collects ~150 normal samples
   - stress_level around 0.0-0.3

2. **Stress Episodes (3-4 times)**: Click "⚡ Stress" button
   - Triggers elevated heart rate
   - Collects stressed samples (0.5-1.0)
   - Wait 30-60 seconds between episodes

3. **Mixed State**: Let it naturally transition
   - Captures variation in both states

**Target**: 200+ samples with 40-60% stress samples

---

## 🔍 Check Your Data Stats

**API Endpoint:**
```
GET http://localhost:8000/api/training/stats
```

**Response:**
```json
{
  "total_samples": 250,
  "normal_samples": 140,
  "stress_samples": 110,
  "avg_bpm": 82.5,
  "min_bpm": 60,
  "max_bpm": 135
}
```

---

## 🤖 Next Steps: Train Your Model

Once you have your dataset, use this simple training script:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Load your exported dataset
df = pd.read_csv("heartrate_dataset.csv")

# Prepare features and target
X = df[["bpm"]]  # Can add more features: systolic, diastolic, etc.
y = (df["stress_level"] > 0.5).astype(int)  # Binary: 0=normal, 1=stress

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# Train classifier
clf = RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",  # Handle imbalance
    random_state=42
)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred, target_names=["Normal", "Stress"]))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save model
joblib.dump(clf, "heartrate_classifier.pkl")
print("\n✅ Model saved as heartrate_classifier.pkl")
```

---

## 🛠️ Troubleshooting

**Problem**: Stats not updating
- **Solution**: Refresh the page and check both servers are running

**Problem**: No data being saved
- **Solution**: Check terminal for errors, ensure database is connected

**Problem**: Need to reset data
- **Solution**: Use clear endpoint:
```
DELETE http://localhost:8000/api/training/data/clear-all?confirm=DELETE_ALL
```

---

## 📁 Database Table Structure

Table: `heartrate_training_data`

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Auto-increment primary key |
| timestamp | DateTime | When recorded |
| bpm | Integer | Heart rate (30-220) |
| stress_level | Float | 0.0 (normal) to 1.0 (stressed) |
| systolic | Integer | Systolic BP (optional) |
| diastolic | Integer | Diastolic BP (optional) |
| patient_id | String | Optional patient ID |
| session_id | String | Group readings by session |
| notes | Text | Additional metadata |

---

## 🎓 Tips for Better Models

1. **Collect More Data**: 500+ samples = better model
2. **Balance Classes**: Equal normal and stress samples
3. **Add Features**: Use time of day, duration, patient demographics
4. **Feature Engineering**: Calculate BPM variance, rate of change
5. **Cross-Validation**: Test on new patients, not just held-out data

---

## ✨ What You've Built

✅ Live heart rate monitoring interface  
✅ Automatic data collection (every 2 seconds)  
✅ Real-time stress level labeling (0-1 scale)  
✅ PostgreSQL storage with timestamps  
✅ CSV export for ML training  
✅ Statistics dashboard  
✅ Balanced dataset collection (normal + stress)  

**You're now ready to build your heart rate classification model!** 🚀
