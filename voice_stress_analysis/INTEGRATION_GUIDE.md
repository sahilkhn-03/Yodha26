# Voice Stress Analysis - Full Stack Integration

## 🎯 Overview
This integrates your trained voice stress model (stress_detector.pkl) with the React frontend UI.

## 📦 Components
1. **Backend API** (`api_server.py`) - FastAPI server serving the ML model
2. **Frontend UI** (`project/`) - React + TypeScript interface
3. **ML Model** (`models/stress_detector.pkl`) - Your trained XGBoost model (74% accuracy)

## 🚀 Quick Start

### 1. Install Backend Dependencies
```bash
cd voice_stress_analysis
pip install fastapi uvicorn[standard] python-multipart librosa soundfile
```

### 2. Start Backend API Server
```bash
cd voice_stress_analysis
python api_server.py
```
The API will start on: **http://localhost:8001**

### 3. Start Frontend (Already Running)
The frontend is already running on: **http://localhost:5173**

## 🔄 How It Works

### Data Flow:
1. **Microphone** → Captures live audio automatically
2. **Frontend** → Records audio every 5 seconds
3. **API** → Sends audio blob to `/api/analyze-voice`
4. **ML Model** → Extracts 51 features + predicts stress
5. **Response** → Returns ML score, math score, emotion, stress level
6. **Display** → Shows results in real-time UI

### API Endpoints:

**POST `/api/analyze-voice`**
- Input: Audio file (WAV, MP3, WebM)
- Output: Complete stress analysis with ML + Math scores

**GET `/api/model-info`**
- Returns model details and configuration

**GET `/`**
- Health check endpoint

## 📊 Features Extracted (51 total)
- **MFCC**: 26 features (mean + std of 13 coefficients)
- **Spectral**: 8 features (centroid, rolloff, bandwidth, flatness)
- **Chroma**: 2 features
- **Zero Crossing Rate**: 2 features
- **Energy/RMS**: 4 features
- **Pitch/F0**: 6 features
- **Tempo**: 1 feature

## 🎨 UI Features
✅ Always-on microphone monitoring
✅ Live audio waveform visualization
✅ Real-time stress gauge (0-100)
✅ ML Score vs Mathematical Score breakdown
✅ Emotion detection with emojis
✅ Auto-updates every 5 seconds
✅ Color-coded stress levels (Green/Yellow/Red)

## 🔧 Configuration

### Change API URL (if needed):
Edit `project/src/utils/voiceAnalysis.ts`:
```typescript
const API_URL = 'http://localhost:8001'; // Change port if needed
```

### Change Analysis Interval:
Edit `project/src/components/VoiceRecorder.tsx`:
```typescript
analysisIntervalRef.current = window.setInterval(() => {
  performAnalysis();
}, 5000); // Change 5000 to desired milliseconds
```

## 📁 File Structure
```
voice_stress_analysis/
├── api_server.py              # FastAPI backend
├── voice_stress_predictor.py  # ML predictor class
├── models/
│   ├── stress_detector.pkl    # Trained XGBoost model
│   ├── scaler.pkl             # Feature scaler
│   └── config.json            # Model configuration
└── project/
    └── src/
        ├── components/
        │   ├── VoiceRecorder.tsx       # Main recording component
        │   ├── VoiceStressDisplay.tsx  # Results display
        │   ├── AudioWaveform.tsx       # Waveform visualization
        │   ├── StressGauge.tsx         # Circular gauge
        │   └── MetricCard.tsx          # Metric cards
        └── utils/
            └── voiceAnalysis.ts        # API integration
```

## 🐛 Troubleshooting

### API Server Not Starting:
```bash
# Check if packages are installed
python -c "import fastapi, librosa; print('OK')"

# Install missing packages
pip install -r api_requirements.txt
```

### CORS Errors:
Make sure the API server is running and the frontend URL is in the CORS allowed origins.

### Model Not Found:
```
⚠️ Model not found, using mathematical analysis only
```
This means `stress_detector.pkl` wasn't found in the `models/` folder. The system will fall back to mathematical analysis only.

### Microphone Permission:
The browser will ask for microphone permission. Click "Allow" to enable live monitoring.

## 📈 Performance
- **ML Model Accuracy**: 74%
- **Inference Time**: ~200-500ms
- **Sample Rate**: 22050 Hz
- **Update Frequency**: Every 5 seconds

## 🎯 Next Steps
1. ✅ Backend API created
2. ✅ Frontend integrated with API
3. ✅ Real-time monitoring active
4. 🔄 Test with voice input
5. 🔄 Deploy to production (optional)

## 💡 Tips
- Speak naturally for best results
- Minimum 0.5 seconds of audio required
- Works best with 3-10 seconds of speech
- Background noise may affect accuracy
- Model trained on 8 emotions: neutral, happy, encouraging, assertive, excited, apologetic, sad, concerned
