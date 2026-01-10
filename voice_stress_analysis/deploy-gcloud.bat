@echo off
REM Voice Stress API - Google Cloud Deployment Script (Windows)

echo ==========================================
echo Voice Stress API - Google Cloud Deployment
echo ==========================================
echo.

cd /d "%~dp0"

REM Configuration
set PROJECT_ID=%GCLOUD_PROJECT_ID%
if "%PROJECT_ID%"=="" set PROJECT_ID=your-project-id
set REGION=%GCLOUD_REGION%
if "%REGION%"=="" set REGION=us-central1
set SERVICE_NAME=voice-stress-api
set IMAGE_NAME=gcr.io/%PROJECT_ID%/%SERVICE_NAME%

echo Project: %PROJECT_ID%
echo Region: %REGION%
echo Image: %IMAGE_NAME%
echo.

REM Check if gcloud is installed
where gcloud >nul 2>nul
if errorlevel 1 (
    echo ERROR: gcloud CLI not found. Please install it first.
    echo Visit: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Check if Docker is installed
where docker >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker not found. Please install Docker Desktop.
    pause
    exit /b 1
)

echo Setting GCP project...
gcloud config set project %PROJECT_ID%

echo.
echo Enabling required Google Cloud APIs...
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo.
echo Building Docker image...
docker build -t %IMAGE_NAME%:latest .

echo.
echo Configuring Docker authentication...
gcloud auth configure-docker

echo.
echo Pushing image to GCR...
docker push %IMAGE_NAME%:latest

echo.
echo Deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --image %IMAGE_NAME%:latest ^
    --platform managed ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --port 8001 ^
    --memory 2Gi ^
    --cpu 2 ^
    --max-instances 10 ^
    --timeout 300 ^
    --set-env-vars "PORT=8001"

echo.
echo ========================================
echo Deployment complete!
echo ========================================
echo.

REM Get service URL
for /f "delims=" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format "value(status.url)"') do set SERVICE_URL=%%i

echo Service URL: %SERVICE_URL%
echo.
echo Test the API:
echo   curl %SERVICE_URL%/
echo   curl %SERVICE_URL%/api/model-info
echo.
echo Update your frontend API_URL to:
echo   const API_URL = '%SERVICE_URL%';
echo.

pause
