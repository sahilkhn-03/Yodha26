#!/bin/bash
# Deploy Frontend to Google Cloud Run

set -e

# Configuration
PROJECT_ID="brilliant-flame-475104-c2"
REGION="us-central1"
SERVICE_NAME="facial-stress-frontend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
BACKEND_URL="https://facial-stress-api-XXXXXXXXXX-uc.a.run.app"

echo "🚀 Deploying Frontend to Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Get backend URL from deployment
echo "📡 Fetching backend URL..."
BACKEND_SERVICE_URL=$(gcloud run services describe facial-stress-api --region ${REGION} --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$BACKEND_SERVICE_URL" ]; then
    echo "⚠️  Backend not found. Using placeholder."
    echo "   Update VITE_API_URL in Cloud Run environment after backend deployment."
else
    BACKEND_URL=$BACKEND_SERVICE_URL
    echo "✅ Backend URL: ${BACKEND_URL}"
fi

# Set project
gcloud config set project ${PROJECT_ID}

# Build and push Docker image
echo "🏗️  Building Docker image..."
cd opencvfront/project
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --max-instances 10 \
  --set-env-vars "VITE_API_URL=${BACKEND_URL}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Frontend deployed successfully!"
echo "🔗 Service URL: ${SERVICE_URL}"
echo ""
echo "Open in browser:"
echo "${SERVICE_URL}"
