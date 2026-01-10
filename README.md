# NeuroBalance AI - Multi-Modal Stress Detection Platform

> **A production-ready psychosomatic AI system combining facial analysis, heart rate monitoring, and voice analysis for comprehensive stress detection.**

---

## 🎯 Project Overview

NeuroBalance AI is an intelligent stress detection platform that leverages multiple physiological signals to provide accurate, real-time stress assessments. Unlike traditional single-modal approaches, our system fuses data from facial expressions, heart rate patterns, and vocal characteristics through an LLM orchestration layer for superior accuracy and clinical reliability.

**What Makes Us Unique:**
- **Multi-Modal Fusion:** Combines facial landmarks, heart rate variability, and vocal stress patterns for comprehensive assessment
- **LLM Orchestration:** Intelligent reasoning layer that weighs and interprets signals contextually (planned)
- **Production-Ready MLOps:** LangSmith tracing for model observability and debugging across the multi-model pipeline (planned)
- **Weakly Supervised Learning:** Innovative approach using emotion labels to train stress prediction without expensive ground-truth labeling
- **GPU-Accelerated Training:** Fast model iteration using XGBoost GPU acceleration
- **Clinical Focus:** Designed for real healthcare applications with explainability and reliability in mind

---

## ✅ Current Implementation Status

### Completed Components


### Completed Components

#### 1. **Facial Stress Detection Model** ✅
- **XGBoost Regression Model** trained on FER-2013 dataset (~4,900 samples)
- **Performance Metrics:**
  - Test Accuracy: 77.3% (exceeded 60-70% MVP target)
  - MAE: 22.66 stress points
  - RMSE: 27.29
- **9 Geometric Features** extracted from MediaPipe Face Mesh:
  - Eye Aspect Ratio (EAR) × 3
  - Eyebrow tension × 3
  - Mouth openness
  - Jaw metrics × 2
- **Weak Supervision:** Emotion labels mapped to stress scores (happy→10, fear→90, etc.)
- **GPU Acceleration:** XGBoost configured for GPU training with CPU fallback
- **Interactive Training Notebook:** Full Jupyter notebook for experimentation and retraining
- **Model Artifacts:** Saved model, scaler, and metadata for production deployment

#### 2. **FastAPI Backend** ✅
- RESTful API with comprehensive endpoints
- **Patient Management:** CRUD operations for patient records
- **Assessment System:** Session management and result storage
- **Real-time Capabilities:** WebSocket support for live data streaming
- **ML Integration:** Routes for stress prediction and heart rate analysis
- **Training Data Collection:** API endpoints for gathering labeled training data
- **Authentication:** JWT-based auth system with Supabase integration
- **Database:** PostgreSQL with SQLAlchemy ORM

#### 3. **React Frontend** ✅
- Modern React + TypeScript + Vite setup
- **Live Camera Feed:** MediaPipe Face Mesh integration in browser
- **Real-time Visualization:** Facial landmark rendering
- **Responsive Design:** Mobile-first UI with Tailwind CSS
- **Component Library:** Modular architecture (Header, CameraDisplay, etc.)

#### 4. **Deployment Infrastructure** ✅
- **Docker Support:** Containerized backend and frontend
- **Docker Compose:** Multi-service orchestration
- **Google Cloud Platform:** Ready for deployment with Cloud Build configs
- **Automated Scripts:** PowerShell and Bash deployment scripts
- **Production Builds:** Nginx configuration for optimized frontend serving

#### 5. **Documentation** ✅
- **Hugging Face Model Card:** Complete documentation for model publication
- **Deployment Guides:** Step-by-step instructions for local and cloud deployment
- **API Documentation:** Auto-generated FastAPI docs
- **Training README:** Comprehensive guide for model retraining

---

## 🚀 Planned Features (In Progress)

### 1. **LLM Orchestration Layer** 🔄
**Status:** Architecture designed, implementation pending

**Purpose:** Intelligent fusion and interpretation of multi-modal stress signals

**Capabilities:**
- **Contextual Reasoning:** Understands relationships between facial, vocal, and heart rate signals
- **Conflict Resolution:** Handles contradictory signals (e.g., smiling face but elevated heart rate)
- **Temporal Analysis:** Considers stress pattern evolution over time
- **Explainable Outputs:** Generates natural language explanations for stress assessments
- **Adaptive Weighting:** Dynamically adjusts model weights based on signal quality

**Architecture:**
```
Facial Model (77.3% acc) ─┐
                          ├─> LLM Orchestrator ──> Final Stress Score + Explanation
Heart Rate Model ────────┤
                          │
Voice Stress Model ──────┘
```

**Benefits for Hackathon:**
- **Innovation Factor:** Most stress systems use simple averaging; LLM reasoning is novel
- **Clinical Adoption:** Explainability is critical for medical acceptance
- **Demo-Friendly:** Natural language output is more compelling than raw numbers

### 2. **LangSmith Tracing Integration** 🔄
**Status:** Configuration prepared, deployment pending

**Purpose:** Production-grade observability for multi-model AI system

**Use Cases:**
- **Model Debugging:** Trace predictions through each model in the pipeline
- **Performance Monitoring:** Track inference latency per component
- **Quality Assurance:** Identify when specific models are underperforming
- **A/B Testing:** Compare different fusion strategies
- **Error Analysis:** Debug cases where models disagree or fail

**Why It Matters:**
- **Production Readiness:** Shows awareness of real-world MLOps requirements
- **Differentiator:** Most hackathon projects lack monitoring infrastructure
- **Scalability:** Essential for multi-model systems where debugging is complex
- **Judge Appeal:** Demonstrates professional software engineering practices

**Implementation Plan:**
- Instrument LLM orchestrator calls
- Track individual model predictions
- Monitor fusion logic execution
- Capture user feedback loops

### 3. **Voice Stress Analysis Model** 🔄
**Status:** Architecture defined, data pipeline planned

**Features to Extract:**
- Pitch variations and jitter
- Speaking rate and pauses
- Energy envelope and spectral features
- Voice tremor detection
- Librosa-based feature engineering

**Integration:** Will feed into LLM orchestrator alongside facial and heart rate models

### 4. **Heart Rate Analysis Enhancement** 🔄
**Status:** Basic implementation exists, advanced features planned

**Current:** Simple heart rate classification

**Planned:** 
- Heart Rate Variability (HRV) analysis
- Stress pattern recognition
- Baseline comparison and anomaly detection

### 5. **Remote Photoplethysmography (rPPG)** 🔮
**Status:** Future enhancement - contactless heart rate detection

**Purpose:** Video-based heart rate measurement as a second method for cardiovascular monitoring

**Technology:**
- Remote photoplethysmography (rPPG) extracts heart rate from subtle color changes in facial skin
- Uses standard webcam video without any physical contact
- Analyzes blood volume pulse through pixel intensity variations

**Benefits:**
- **Contactless:** No wearables or sensors required
- **Multi-Modal Validation:** Cross-validates with existing heart rate methods
- **Accessibility:** Works with any standard camera
- **Clinical Value:** Provides additional cardiovascular stress indicators

**Implementation Approach:**
- Extract facial ROI (forehead, cheeks) from MediaPipe landmarks
- Apply signal processing to isolate pulse frequency
- Use Independent Component Analysis (ICA) or POS (Plane-Orthogonal-to-Skin)
- Integrate rPPG heart rate into multi-modal stress assessment

**Research Foundation:**
- Established medical technique validated in numerous studies
- Accuracy comparable to finger-based pulse oximeters in controlled conditions
- Complements existing facial stress analysis pipeline

---

## 🏗️ Technical Architecture

### Current Stack

**Backend:**
- Python 3.10+
- FastAPI for REST APIs
- WebSockets for real-time streaming
- PostgreSQL + SQLAlchemy
- Supabase for auth
- XGBoost for ML inference
- MediaPipe for facial landmarks

**Frontend:**
- React 18 + TypeScript
- Vite for fast builds
- Tailwind CSS for styling
- MediaPipe Tasks Vision API
- Axios for API calls

**ML/AI:**
- XGBoost 2.x (GPU-accelerated)
- MediaPipe Face Mesh (468 landmarks)
- scikit-learn for preprocessing
- NumPy/Pandas for data processing

**DevOps:**
- Docker & Docker Compose
- Google Cloud Platform (Cloud Run, Cloud Build)
- Nginx reverse proxy
- Environment-based configuration

### Planned Stack Additions

- **LLM Integration:** OpenAI GPT-4 / Anthropic Claude for orchestration
- **Observability:** LangSmith for tracing and monitoring
- **Voice Processing:** Librosa, PyAudio for real-time audio analysis

---

## 📊 Model Performance

### Facial Stress Predictor
| Metric | Training | Testing |
|--------|----------|---------|
| Accuracy | 93.9% | 77.3% |
| MAE | 6.15 | 22.66 |
| RMSE | 9.94 | 27.29 |

**Dataset:** FER-2013 (7 emotions, ~700 samples each)  
**Features:** 9 geometric facial metrics  
**Algorithm:** XGBoost Regressor (300 trees, depth 6)  
**Training Time:** < 2 hours on GPU

---

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL (or use Supabase)
- GPU with CUDA (optional, for training)

### Quick Start - Local Development

#### 1. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your database and API keys
python main.py
```

Backend runs at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

#### 2. **Frontend Setup**
```bash
cd opencvfront/project
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

#### 3. **Docker Deployment**
```bash
# Build and run all services
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:80
```

### Cloud Deployment

#### Deploy Backend to Google Cloud Run
```bash
cd backend
./deploy_backend.sh  # Linux/Mac
# or
./deploy_backend.ps1  # Windows
```

#### Deploy Frontend to Google Cloud
```bash
cd opencvfront/project
./deploy_frontend.sh  # Linux/Mac
# or
./deploy_frontend.ps1  # Windows
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## 📁 Project Structure

```
Yodha26/
├── ai/                                  # ML Training & Models
│   ├── train_stress_model_interactive.ipynb  # Main training notebook
│   ├── HUGGINGFACE_README.md           # Model card for publication
│   ├── models/                         # Trained model artifacts
│   │   ├── stress_predictor.pkl
│   │   ├── feature_scaler.pkl
│   │   └── model_metadata.pkl
│   └── fer2013_data/                   # Training dataset
│
├── backend/                            # FastAPI Server
│   ├── main.py                         # Application entry point
│   ├── config.py                       # Environment configuration
│   ├── database.py                     # DB connection & models
│   ├── routes_*.py                     # API endpoint modules
│   ├── inference_stress_model.py       # ML inference wrapper
│   ├── Dockerfile                      # Container definition
│   └── requirements.txt                # Python dependencies
│
├── opencvfront/project/                # React Frontend
│   ├── src/
│   │   ├── App.tsx                     # Main application
│   │   ├── components/                 # React components
│   │   └── lib/faceMesh.ts            # MediaPipe integration
│   ├── Dockerfile                      # Container definition
│   └── package.json                    # Node dependencies
│
├── docker-compose.yml                  # Multi-service orchestration
├── deploy_backend.sh/ps1              # Deployment scripts
├── deploy_frontend.sh/ps1             # Deployment scripts
└── README.md                           # This file
```

---

## 🧪 Training Your Own Model

### Using the Interactive Notebook

1. **Open the notebook:**
   ```bash
   cd ai
   jupyter notebook train_stress_model_interactive.ipynb
   ```

2. **Configure parameters** in the `Config` class:
   - `MAX_SAMPLES_PER_EMOTION`: Dataset size per emotion
   - `N_ESTIMATORS`: Number of XGBoost trees
   - `MAX_DEPTH`: Tree complexity
   - `TREE_METHOD`: "gpu_hist" for GPU, "hist" for CPU

3. **Run all cells** to:
   - Load and process FER-2013 dataset
   - Extract facial features with MediaPipe
   - Train XGBoost model
   - Evaluate performance
   - Save model artifacts

4. **Deploy trained model:**
   ```bash
   cp ai/models/stress_predictor.pkl backend/ml_models/
   cp ai/models/feature_scaler.pkl backend/ml_models/
   ```

See [ai/TRAINING_README.md](ai/TRAINING_README.md) for detailed training instructions.

---

## 🔬 API Usage Examples

### Start Assessment Session
```bash
curl -X POST http://localhost:8000/assessment/start \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 123}'
```

### Get Stress Prediction
```bash
curl -X POST http://localhost:8000/ml/stress/predict \
  -H "Content-Type: application/json" \
  -d '{
    "facial_features": [0.25, 0.24, 0.26, 0.15, 0.14, 0.16, 0.08, 0.45, 0.12]
  }'
```

### WebSocket Real-time Stream
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/assessment/session-id');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Stress:', data.stress_score);
};
```

Full API documentation available at `http://localhost:8000/docs`

---

## 🎯 Roadmap

### Phase 1: MVP (Completed) ✅
- [x] Facial stress detection model (77.3% accuracy)
- [x] FastAPI backend with REST APIs
- [x] React frontend with live camera feed
- [x] Docker deployment infrastructure
- [x] Model training pipeline
- [x] Documentation and model card

### Phase 2: Multi-Modal Integration (In Progress) 🔄
- [ ] Voice stress analysis model
- [ ] Advanced heart rate variability analysis
- [ ] LLM orchestration layer
- [ ] LangSmith tracing integration
- [ ] Multi-modal fusion evaluation

### Phase 3: Production Enhancements (Planned) 📋
- [ ] User authentication and authorization
- [ ] Session history and analytics dashboard
- [ ] Personalized stress baselines
- [ ] Clinician reporting interface
- [ ] Mobile app (React Native)
- [ ] Real-time alerts and notifications

### Phase 4: Research & Validation (Future) 🔮
- [ ] Clinical trial data collection
- [ ] Model validation with ground-truth stress labels
- [ ] Privacy-preserving federated learning
- [ ] Edge deployment (mobile/IoT devices)
- [ ] Multi-language support
- [ ] Accessibility features

---

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT.md):** Step-by-step deployment instructions
- **[Training Guide](ai/TRAINING_README.md):** Model training and experimentation
- **[Hugging Face Model Card](ai/HUGGINGFACE_README.md):** Detailed model documentation
- **[API Docs](http://localhost:8000/docs):** Interactive API documentation (when server is running)

---

## 🤝 Contributing

This is a hackathon project currently under active development. We welcome:
- Bug reports and feature requests
- Code contributions and improvements
- Documentation enhancements
- Model training experiments

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **FER-2013 Dataset:** Emotion recognition training data
- **MediaPipe:** Facial landmark detection
- **XGBoost:** High-performance gradient boosting
- **FastAPI:** Modern Python web framework
- **React + Vite:** Frontend development tools

---

## 📧 Contact

Team Mission404  
For questions or collaboration: [GitHub Issues](https://github.com/sahilkhn-03/Yodha26/issues)

---

**Built with ❤️ for better mental health through AI**
