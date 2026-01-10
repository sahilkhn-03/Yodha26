# Deploy Frontend to Google Cloud Run (Windows PowerShell)

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "neurobalanceai"
$REGION = "us-central1"
$SERVICE_NAME = "neurobalance-frontend"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "🚀 Deploying Frontend to Cloud Run" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host ""

# Get backend URL from deployment
Write-Host "📡 Fetching backend URL..." -ForegroundColor Yellow
try {
    $BACKEND_URL = gcloud run services describe facial-stress-api --region $REGION --format 'value(status.url)' 2>$null
    if ($BACKEND_URL) {
        Write-Host "✅ Backend URL: $BACKEND_URL" -ForegroundColor Green
    } else {
        throw "Backend not found"
    }
} catch {
    Write-Host "⚠️  Backend not found. Using placeholder." -ForegroundColor Yellow
    Write-Host "   Update VITE_API_URL in Cloud Run environment after backend deployment."
    $BACKEND_URL = "https://facial-stress-api-placeholder.run.app"
}

# Set project
gcloud config set project $PROJECT_ID

# Build and push Docker image
Write-Host "🏗️  Building Docker image..." -ForegroundColor Yellow
Set-Location opencvfront\project
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
Write-Host "🚢 Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE_NAME `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 60 `
  --max-instances 10 `
  --set-env-vars "VITE_API_URL=$BACKEND_URL"

# Get service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'

Write-Host ""
Write-Host "✅ Frontend deployed successfully!" -ForegroundColor Green
Write-Host "🔗 Service URL: $SERVICE_URL"
Write-Host ""
Write-Host "Open in browser:"
Write-Host "$SERVICE_URL"
