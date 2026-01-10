# 🎙️ Voice Stress Analysis - Complete Setup

## ✅ What's Been Created

### 1. Docker Configuration
- ✅ **Dockerfile** - Container image definition
- ✅ **docker-compose.yml** - Local orchestration
- ✅ **.dockerignore** - Optimized build context

### 2. Google Cloud Deployment
- ✅ **cloudbuild.yaml** - GCP Cloud Build config
- ✅ **deploy-gcloud.bat** - Windows deployment script
- ✅ **deploy-gcloud.sh** - Linux/Mac deployment script

### 3. API Server
- ✅ **api_server.py** - Production-ready FastAPI
- ✅ Environment variable support
- ✅ CORS configuration
- ✅ Health checks

### 4. Frontend Integration
- ✅ Environment variable support (.env files)
- ✅ Automatic API URL configuration
- ✅ Fallback to local analysis if API unavailable

### 5. Documentation
- ✅ **DEPLOYMENT_GUIDE.md** - Complete deployment instructions
- ✅ **DOCKER_QUICKSTART.md** - Quick Docker commands
- ✅ **INTEGRATION_GUIDE.md** - Full integration details

## 🚀 Quick Start Options

### Option 1: Local Docker (Recommended for Testing)

```bash
# Navigate to voice_stress_analysis folder
cd voice_stress_analysis

# Start with Docker Compose
docker-compose up -d

# API running at: http://localhost:8001
```

### Option 2: Local Python Server

```bash
cd voice_stress_analysis
python api_server.py

# API running at: http://localhost:8001
```

### Option 3: Deploy to Google Cloud

```bash
# Windows
set GCLOUD_PROJECT_ID=your-project-id
deploy-gcloud.bat

# Linux/Mac
export GCLOUD_PROJECT_ID=your-project-id
./deploy-gcloud.sh

# API running at: https://voice-stress-api-xxxxx.run.app
```

## 📋 Prerequisites

### For Local Development:
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ Docker Desktop (for containerization)

### For Google Cloud:
- ✅ Google Cloud account
- ✅ gcloud CLI installed
- ✅ Billing enabled on GCP project
- ✅ Docker Desktop

## 🔄 Complete Workflow

### 1. Test Locally with Docker

```bash
# Build and run
cd voice_stress_analysis
docker-compose up -d

# Test API
curl http://localhost:8001/
curl http://localhost:8001/api/model-info

# View logs
docker-compose logs -f

# Stop when done
docker-compose down
```

### 2. Start Frontend

```bash
cd voice_stress_analysis/project
npm install
npm run dev

# Frontend at: http://localhost:5173
```

### 3. Test Integration

1. Open http://localhost:5173 in browser
2. Grant microphone permission
3. Speak naturally
4. See real-time analysis every 5 seconds

### 4. Deploy to Google Cloud

```bash
cd voice_stress_analysis

# Set your project ID
set GCLOUD_PROJECT_ID=your-project-id  # Windows
# OR
export GCLOUD_PROJECT_ID=your-project-id  # Linux/Mac

# Deploy
deploy-gcloud.bat  # Windows
# OR
./deploy-gcloud.sh  # Linux/Mac
```

### 5. Update Frontend for Production

After deployment, you'll get a URL like:
`https://voice-stress-api-xxxxx-uc.a.run.app`

**Option A: Using .env file (Recommended)**

Create `voice_stress_analysis/project/.env`:
```
VITE_API_URL=https://voice-stress-api-xxxxx-uc.a.run.app
```

**Option B: Direct edit**

Edit `project/src/utils/voiceAnalysis.ts`:
```typescript
const API_URL = 'https://voice-stress-api-xxxxx-uc.a.run.app';
```

### 6. Deploy Frontend (Optional)

Deploy to Vercel, Netlify, or Firebase:

```bash
cd project
npm run build

# Deploy dist/ folder to your hosting provider
```

## 📁 Project Structure

```
voice_stress_analysis/
├── 🐳 Docker Files
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── ☁️ Google Cloud Files
│   ├── cloudbuild.yaml
│   ├── deploy-gcloud.bat
│   └── deploy-gcloud.sh
│
├── 🔧 API Server
│   ├── api_server.py
│   ├── voice_stress_predictor.py
│   ├── api_requirements.txt
│   └── models/
│       ├── stress_detector.pkl
│       ├── scaler.pkl
│       └── config.json
│
├── 🎨 Frontend
│   └── project/
│       ├── .env.example
│       ├── .env.local
│       └── src/
│           ├── components/
│           └── utils/
│               └── voiceAnalysis.ts
│
└── 📚 Documentation
    ├── DEPLOYMENT_GUIDE.md
    ├── DOCKER_QUICKSTART.md
    ├── INTEGRATION_GUIDE.md
    └── README_DOCKER_GCLOUD.md (this file)
```

## 🔍 API Endpoints

### Health Check
```bash
GET /
```

### Model Information
```bash
GET /api/model-info
```

### Analyze Voice
```bash
POST /api/analyze-voice
Content-Type: multipart/form-data
Body: audio file (WAV, MP3, WebM, etc.)

Response:
{
  "overall_stress_score": 45,
  "stress_level": "Moderate",
  "emotion_detected": "Neutral",
  "ml_score": 42,
  "mathematical_score": 48,
  "duration": 5.2,
  "audio_features": {...}
}
```

## 🎯 Features

### Backend (API Server)
- ✅ FastAPI with automatic documentation (/docs)
- ✅ XGBoost ML model (74% accuracy)
- ✅ 51 audio features extraction
- ✅ Dual scoring: ML + Mathematical
- ✅ 8 emotion categories
- ✅ CORS enabled for frontend
- ✅ Health checks
- ✅ Environment variable configuration
- ✅ Docker containerization
- ✅ Google Cloud ready

### Frontend (React UI)
- ✅ Always-on microphone monitoring
- ✅ Live audio waveform visualization
- ✅ Real-time stress gauge (0-100)
- ✅ Score breakdown (ML vs Math)
- ✅ Emotion detection with emojis
- ✅ Auto-updates every 5 seconds
- ✅ Color-coded stress levels
- ✅ Environment variable support
- ✅ API fallback mechanism

## 🔧 Configuration

### Backend Environment Variables

```bash
PORT=8001                    # Server port
ENVIRONMENT=production       # Environment name
ALLOWED_ORIGINS=*           # CORS origins (comma-separated)
```

### Frontend Environment Variables

```bash
VITE_API_URL=http://localhost:8001  # API endpoint
```

## 💰 Google Cloud Costs

### Estimated Monthly Cost (Low Traffic)

**Cloud Run:**
- Free tier: 2 million requests/month
- After: ~$0.000024 per request
- Memory (2Gi): ~$0.0000025 per GB-second
- CPU (2 cores): ~$0.000024 per vCPU-second

**Container Registry:**
- Storage: ~$0.026 per GB/month
- Network egress: ~$0.12 per GB

**Typical usage:**
- 10,000 requests/month: ~$1-5
- 100,000 requests/month: ~$10-20

### Cost Optimization:
- Use min-instances=0 for cold starts
- Optimize image size
- Use caching
- Set request timeouts

## 🐛 Troubleshooting

### Docker Issues

```bash
# Container won't start
docker logs voice-stress-api

# Port conflict
docker-compose down
# Edit docker-compose.yml to change port

# Clean rebuild
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up
```

### Google Cloud Issues

```bash
# Check deployment status
gcloud run services describe voice-stress-api --region us-central1

# View logs
gcloud run services logs tail voice-stress-api

# Update service
gcloud run services update voice-stress-api --region us-central1 --memory 4Gi
```

### API Connection Issues

```bash
# Test API directly
curl http://localhost:8001/
curl http://localhost:8001/api/model-info

# Check CORS
# Open browser console (F12) and check for CORS errors

# Verify frontend .env
cat project/.env
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)

## 🎓 Learning Path

1. ✅ **Start Local**: Test with Docker locally
2. ✅ **Verify Integration**: Frontend + Backend working together
3. ✅ **Deploy to Cloud**: Push to Google Cloud Run
4. ✅ **Update Frontend**: Connect to cloud API
5. ✅ **Monitor**: Check logs and metrics
6. ✅ **Optimize**: Adjust resources and costs

## 📝 Deployment Checklist

### Local Testing
- [ ] Docker Desktop installed and running
- [ ] Docker image builds successfully
- [ ] Container runs locally (port 8001)
- [ ] API responds to health check
- [ ] Frontend connects to local API
- [ ] Voice analysis working end-to-end

### Google Cloud Deployment
- [ ] GCP account created
- [ ] gcloud CLI installed and authenticated
- [ ] Project ID set in environment
- [ ] Billing enabled
- [ ] Required APIs enabled
- [ ] Docker image pushed to GCR
- [ ] Service deployed to Cloud Run
- [ ] Service URL obtained
- [ ] Frontend updated with Cloud URL
- [ ] CORS configured for production domain
- [ ] Monitoring/logging set up

## 🚀 Next Steps

1. **Test Locally**: `docker-compose up -d`
2. **Deploy to Cloud**: Run deployment script
3. **Update Frontend**: Set production API URL
4. **Test Production**: Verify end-to-end functionality
5. **Monitor**: Check logs and performance
6. **Scale**: Adjust resources as needed

---

**Quick Links:**
- Local API: http://localhost:8001
- Local Frontend: http://localhost:5173
- API Docs: http://localhost:8001/docs
- Deployment Guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Docker Quick Start: [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)

**Need Help?**
Check the troubleshooting sections in:
- DEPLOYMENT_GUIDE.md
- INTEGRATION_GUIDE.md
- Or review logs: `docker-compose logs -f`
