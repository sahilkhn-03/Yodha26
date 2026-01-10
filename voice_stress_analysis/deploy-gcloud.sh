#!/bin/bash

# Voice Stress API - Google Cloud Deployment Script

set -e

echo "=========================================="
echo "Voice Stress API - Google Cloud Deployment"
echo "=========================================="
echo

# Configuration
PROJECT_ID="${GCLOUD_PROJECT_ID:-your-project-id}"
REGION="${GCLOUD_REGION:-us-central1}"
SERVICE_NAME="voice-stress-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found. Please install Docker Desktop."
    exit 1
fi

echo "📋 Project: ${PROJECT_ID}"
echo "🌍 Region: ${REGION}"
echo "🐳 Image: ${IMAGE_NAME}"
echo

# Set the project
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo
echo "Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build Docker image
echo
echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

# Tag image
echo
echo "🏷️  Tagging image..."
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)

# Configure Docker for GCR
echo
echo "🔑 Configuring Docker authentication..."
gcloud auth configure-docker

# Push to Google Container Registry
echo
echo "📤 Pushing image to GCR..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8001 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "PORT=8001"

# Get the service URL
echo
echo "✅ Deployment complete!"
echo
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "🌐 Service URL: ${SERVICE_URL}"
echo
echo "Test the API:"
echo "  curl ${SERVICE_URL}/"
echo "  curl ${SERVICE_URL}/api/model-info"
echo
echo "Update your frontend API_URL to:"
echo "  const API_URL = '${SERVICE_URL}';"
echo
