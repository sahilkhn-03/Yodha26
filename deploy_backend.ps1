# Deploy Facial Stress API to Google Cloud Run (Windows PowerShell)

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "neurobalanceai"
$REGION = "us-central1"
$SERVICE_NAME = "facial-stress-api"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "🚀 Deploying Facial Stress API to Cloud Run" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host ""

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host "📦 Enabling required GCP APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push Docker image
Write-Host "🏗️  Building Docker image..." -ForegroundColor Yellow
Set-Location backend
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run (no database required for ML-only mode)
Write-Host "🚢 Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE_NAME `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10

# Get service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'

Write-Host ""
Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
Write-Host "🔗 Service URL: $SERVICE_URL"
Write-Host ""
Write-Host "Test it with:"
Write-Host "curl $SERVICE_URL/health"
