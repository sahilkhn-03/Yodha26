# 🐳 Quick Start - Docker Setup

## Prerequisites
✅ Docker Desktop installed and running
✅ Models folder with trained model files

## 🚀 Quick Commands

### Build and Run (Simplest)
```bash
cd voice_stress_analysis

# Build the image
docker build -t voice-stress-api .

# Run the container
docker run -p 8001:8001 voice-stress-api
```

### Using Docker Compose (Recommended)
```bash
cd voice_stress_analysis

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## 🧪 Test the API

```bash
# Health check
curl http://localhost:8001/

# Model info
curl http://localhost:8001/api/model-info

# Test with audio (if you have a WAV file)
curl -X POST -F "audio=@test.wav" http://localhost:8001/api/analyze-voice
```

## 🌐 Frontend Integration

Your frontend will automatically connect to the containerized API at `http://localhost:8001`

Just make sure both are running:
- Backend (Docker): http://localhost:8001
- Frontend (npm): http://localhost:5173

## 📦 What's in the Container?

- Python 3.11 slim
- FastAPI + Uvicorn
- Librosa + audio processing libraries
- Your trained ML model
- All required dependencies

## 🔧 Troubleshooting

### Container won't start?
```bash
# Check Docker is running
docker ps

# View container logs
docker logs voice-stress-api

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Port already in use?
```bash
# Stop local Python server first
# Or change port in docker-compose.yml:
ports:
  - "8002:8001"
```

### Models not found?
Make sure the `models/` folder exists with:
- stress_detector.pkl
- scaler.pkl
- config.json

---

**Next Steps:**
1. ✅ Test locally with Docker
2. 🚀 Deploy to Google Cloud (see DEPLOYMENT_GUIDE.md)
3. 🌐 Update frontend with Cloud URL
