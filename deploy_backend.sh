#!/bin/bash
# Deploy Facial Stress API to Google Cloud Run

set -e

# Configuration
PROJECT_ID="brilliant-flame-475104-c2"
REGION="us-central1"
SERVICE_NAME="facial-stress-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Facial Stress API to Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Set project
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "📦 Enabling required GCP APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push Docker image
echo "🏗️  Building Docker image..."
cd backend
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "DATABASE_URL=${DATABASE_URL},SUPABASE_URL=${SUPABASE_URL},SUPABASE_KEY=${SUPABASE_KEY}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Backend deployed successfully!"
echo "🔗 Service URL: ${SERVICE_URL}"
echo ""
echo "Test it with:"
echo "curl ${SERVICE_URL}/health"
