# 🚀 Voice Stress API - Docker & Google Cloud Deployment

## 📦 Docker Setup

### Prerequisites
- Docker Desktop installed
- Google Cloud SDK (gcloud CLI) installed
- GCP project created

### Local Docker Development

#### 1. Build Docker Image
```bash
cd voice_stress_analysis
docker build -t voice-stress-api .
```

#### 2. Run Container Locally
```bash
docker run -p 8001:8001 voice-stress-api
```

#### 3. Using Docker Compose (Recommended)
```bash
docker-compose up -d
```

Stop the container:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f
```

### Test Local Docker Container
```bash
# Health check
curl http://localhost:8001/

# Model info
curl http://localhost:8001/api/model-info

# Test analysis with audio file
curl -X POST -F "audio=@test.wav" http://localhost:8001/api/analyze-voice
```

## ☁️ Google Cloud Deployment

### Option 1: Using Deployment Script (Easiest)

#### Windows:
```batch
cd voice_stress_analysis

# Set your project ID
set GCLOUD_PROJECT_ID=your-project-id
set GCLOUD_REGION=us-central1

# Run deployment
deploy-gcloud.bat
```

#### Linux/Mac:
```bash
cd voice_stress_analysis

# Set your project ID
export GCLOUD_PROJECT_ID=your-project-id
export GCLOUD_REGION=us-central1

# Run deployment
chmod +x deploy-gcloud.sh
./deploy-gcloud.sh
```

### Option 2: Manual Deployment

#### Step 1: Set up GCP
```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Step 2: Build and Push to GCR
```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT_ID/voice-stress-api .

# Configure Docker for GCR
gcloud auth configure-docker

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/voice-stress-api
```

#### Step 3: Deploy to Cloud Run
```bash
gcloud run deploy voice-stress-api \
  --image gcr.io/YOUR_PROJECT_ID/voice-stress-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8001 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --timeout 300
```

#### Step 4: Get Service URL
```bash
gcloud run services describe voice-stress-api \
  --region us-central1 \
  --format 'value(status.url)'
```

### Option 3: Using Cloud Build (CI/CD)

#### Setup Cloud Build Trigger
```bash
# Submit build manually
gcloud builds submit --config cloudbuild.yaml ..

# Or set up automatic builds from GitHub
gcloud builds triggers create github \
  --repo-name=Yodha26 \
  --repo-owner=sahilkhn-03 \
  --branch-pattern="^main$" \
  --build-config=voice_stress_analysis/cloudbuild.yaml
```

## 🔧 Configuration

### Environment Variables
Set these in Cloud Run:
```bash
PORT=8001
PYTHONUNBUFFERED=1
```

### Resource Allocation
- **Memory**: 2Gi (adjustable based on load)
- **CPU**: 2 cores
- **Max Instances**: 10 (auto-scaling)
- **Timeout**: 300 seconds

### Update Resources:
```bash
gcloud run services update voice-stress-api \
  --region us-central1 \
  --memory 4Gi \
  --cpu 4
```

## 🌐 Update Frontend

After deployment, update your frontend API URL:

**File**: `voice_stress_analysis/project/src/utils/voiceAnalysis.ts`

```typescript
// Replace localhost with your Cloud Run URL
const API_URL = 'https://voice-stress-api-xxxxxx-uc.a.run.app';
```

Or use environment variable:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
```

Create `.env` file in project folder:
```
VITE_API_URL=https://your-cloud-run-url.run.app
```

## 🔒 Security (Optional)

### Add Authentication
```bash
gcloud run services update voice-stress-api \
  --region us-central1 \
  --no-allow-unauthenticated
```

Then add auth to your frontend requests.

### CORS Configuration
Already configured in `api_server.py` to allow:
- http://localhost:5173 (development)
- http://localhost:3000 (alternative)
- Add production URL when deploying frontend

## 📊 Monitoring

### View Logs
```bash
# Real-time logs
gcloud run services logs tail voice-stress-api --region us-central1

# Recent logs
gcloud run services logs read voice-stress-api --region us-central1 --limit 50
```

### Check Metrics
```bash
# Open Cloud Console
gcloud run services describe voice-stress-api --region us-central1
```

### Health Check
```bash
# Your Cloud Run URL
curl https://voice-stress-api-xxxxx.run.app/
curl https://voice-stress-api-xxxxx.run.app/api/model-info
```

## 💰 Cost Optimization

### Cloud Run Pricing
- **Free Tier**: 2 million requests/month
- **After free tier**: $0.00002400 per request
- **Memory**: $0.00000250 per GB-second
- **CPU**: $0.00002400 per vCPU-second

### Tips to Reduce Costs:
1. **Set Min Instances to 0**: Cold starts are acceptable
2. **Optimize Memory**: Start with 1Gi, scale if needed
3. **Use Caching**: Implement response caching
4. **Request Limits**: Add rate limiting

```bash
gcloud run services update voice-stress-api \
  --region us-central1 \
  --min-instances 0 \
  --memory 1Gi
```

## 🐛 Troubleshooting

### Container won't start
```bash
# Check build logs
gcloud builds list --limit 5

# Check specific build
gcloud builds describe BUILD_ID
```

### Out of Memory
```bash
# Increase memory
gcloud run services update voice-stress-api \
  --region us-central1 \
  --memory 4Gi
```

### Cold Start Issues
```bash
# Set minimum instances
gcloud run services update voice-stress-api \
  --region us-central1 \
  --min-instances 1
```

### CORS Errors
Check allowed origins in `api_server.py`:
```python
allow_origins=["http://localhost:5173", "https://your-frontend.com"]
```

## 📁 File Structure

```
voice_stress_analysis/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Local Docker orchestration
├── .dockerignore          # Files to exclude from image
├── cloudbuild.yaml        # GCP Cloud Build config
├── deploy-gcloud.sh       # Linux/Mac deployment script
├── deploy-gcloud.bat      # Windows deployment script
├── api_server.py          # FastAPI application
├── voice_stress_predictor.py
├── api_requirements.txt
└── models/
    ├── stress_detector.pkl
    ├── scaler.pkl
    └── config.json
```

## ✅ Deployment Checklist

- [ ] Docker Desktop installed and running
- [ ] gcloud CLI installed
- [ ] GCP project created
- [ ] Billing enabled on GCP project
- [ ] Required APIs enabled
- [ ] Docker image builds successfully
- [ ] Container runs locally
- [ ] Deployed to Cloud Run
- [ ] Service URL obtained
- [ ] Frontend updated with new URL
- [ ] API tested from frontend
- [ ] Monitoring set up

## 🔄 CI/CD Pipeline

For automatic deployments on git push:

1. Connect GitHub to Cloud Build
2. Create trigger for main branch
3. Use `cloudbuild.yaml` configuration
4. Auto-deploy on every commit

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)

---

**Need Help?**
- Check logs: `gcloud run services logs tail voice-stress-api`
- Test API: `curl YOUR_SERVICE_URL/api/model-info`
- Verify Docker: `docker run -p 8001:8001 voice-stress-api`
