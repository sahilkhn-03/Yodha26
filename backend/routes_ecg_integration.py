"""
Integrated ECG to ML Prediction Pipeline
Fetches heart rate from ECG simulator and returns ML stress prediction.
"""

from fastapi import APIRouter, HTTPException
import httpx
import asyncio

router = APIRouter(prefix="/api/ecg", tags=["ECG Integration"])

ECG_SIMULATOR_URL = "http://localhost:8001"


@router.get("/predict-stress")
async def predict_stress_from_ecg():
    """
    Fetch current heart rate from ECG simulator and predict stress.
    
    This endpoint:
    1. Gets current BPM from ECG simulator (port 8001)
    2. Passes it to ML model for prediction
    3. Returns stress classification with confidence
    
    Returns:
        {
            "bpm": 125,
            "prediction": "Stress",
            "confidence": 0.98,
            "stress_score": 0.98,
            "timestamp": "2026-01-10T...",
            "source": "ECG Simulator"
        }
    
    Use case: Real-time stress monitoring from ECG readings
    """
    try:
        # Fetch current heart rate from ECG simulator
        async with httpx.AsyncClient() as client:
            ecg_response = await client.get(f"{ECG_SIMULATOR_URL}/heartbeat/current", timeout=5.0)
            
            if ecg_response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail=f"ECG simulator not responding properly: {ecg_response.status_code}"
                )
            
            ecg_data = ecg_response.json()
            bpm = ecg_data.get('bpm')
            timestamp = ecg_data.get('timestamp')
            actual_stress = ecg_data.get('stress_level', 0)  # From simulator
            
            if not bpm:
                raise HTTPException(status_code=500, detail="No BPM data from ECG simulator")
            
            # Call ML prediction endpoint
            ml_response = await client.post(
                "http://localhost:8000/api/ml/predict",
                json={"bpm": bpm},
                timeout=5.0
            )
            
            if ml_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"ML prediction failed: {ml_response.text}"
                )
            
            ml_prediction = ml_response.json()
            
            # Return combined result
            return {
                "bpm": bpm,
                "prediction": ml_prediction['prediction'],
                "confidence": ml_prediction['confidence'],
                "stress_score": ml_prediction['stress_score'],
                "probabilities": ml_prediction['probabilities'],
                "timestamp": timestamp,
                "source": "ECG Simulator",
                "simulator_stress_level": actual_stress,
                "status": "success"
            }
    
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="ECG simulator not running. Start it with: uvicorn heartbeat_sim:app --port 8001 --reload"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="ECG simulator timeout. Check if port 8001 is responding."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error integrating ECG with ML: {str(e)}"
        )


@router.get("/monitor-stress")
async def monitor_stress_continuous():
    """
    Monitor stress continuously by fetching multiple readings.
    
    Returns last 5 predictions with trend analysis.
    """
    try:
        readings = []
        
        async with httpx.AsyncClient() as client:
            # Collect 5 readings over 3 seconds
            for i in range(5):
                ecg_response = await client.get(
                    f"{ECG_SIMULATOR_URL}/heartbeat/current",
                    timeout=5.0
                )
                ecg_data = ecg_response.json()
                bpm = ecg_data.get('bpm')
                
                # Predict
                ml_response = await client.post(
                    "http://localhost:8000/api/ml/predict",
                    json={"bpm": bpm},
                    timeout=5.0
                )
                prediction = ml_response.json()
                
                readings.append({
                    "reading_number": i + 1,
                    "bpm": bpm,
                    "prediction": prediction['prediction'],
                    "stress_score": prediction['stress_score']
                })
                
                if i < 4:  # Don't wait after last reading
                    await asyncio.sleep(0.6)
        
        # Calculate trend
        stress_scores = [r['stress_score'] for r in readings]
        avg_stress = sum(stress_scores) / len(stress_scores)
        stress_count = sum(1 for r in readings if r['prediction'] == 'Stress')
        
        # Determine trend
        if len(stress_scores) >= 3:
            recent_avg = sum(stress_scores[-3:]) / 3
            earlier_avg = sum(stress_scores[:3]) / 3
            if recent_avg > earlier_avg + 0.15:
                trend = "Increasing"
            elif recent_avg < earlier_avg - 0.15:
                trend = "Decreasing"
            else:
                trend = "Stable"
        else:
            trend = "Insufficient data"
        
        return {
            "readings": readings,
            "analysis": {
                "total_readings": len(readings),
                "stress_readings": stress_count,
                "normal_readings": len(readings) - stress_count,
                "average_stress_score": round(avg_stress, 3),
                "trend": trend,
                "overall_status": "High Stress" if avg_stress > 0.6 else "Moderate" if avg_stress > 0.3 else "Normal"
            },
            "recommendation": "Consider stress reduction techniques" if avg_stress > 0.6 else "Monitoring normal"
        }
    
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="ECG simulator not running on port 8001"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")


@router.get("/status")
async def check_system_status():
    """
    Check if both ECG simulator and ML model are operational.
    
    Returns system health status.
    """
    status = {
        "ecg_simulator": {"status": "unknown", "url": ECG_SIMULATOR_URL},
        "ml_model": {"status": "unknown", "url": "http://localhost:8000/api/ml"},
        "overall": "unknown"
    }
    
    # Check ECG simulator
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ECG_SIMULATOR_URL}/heartbeat/current", timeout=3.0)
            if response.status_code == 200:
                status["ecg_simulator"]["status"] = "operational"
                data = response.json()
                status["ecg_simulator"]["current_bpm"] = data.get('bpm')
            else:
                status["ecg_simulator"]["status"] = "error"
    except:
        status["ecg_simulator"]["status"] = "offline"
    
    # Check ML model
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/ml/model/info", timeout=3.0)
            if response.status_code == 200:
                info = response.json()
                if info.get('status') == 'loaded':
                    status["ml_model"]["status"] = "operational"
                    status["ml_model"]["accuracy"] = info.get('accuracy')
                else:
                    status["ml_model"]["status"] = "not_loaded"
            else:
                status["ml_model"]["status"] = "error"
    except:
        status["ml_model"]["status"] = "offline"
    
    # Overall status
    if (status["ecg_simulator"]["status"] == "operational" and 
        status["ml_model"]["status"] == "operational"):
        status["overall"] = "fully_operational"
    elif (status["ecg_simulator"]["status"] == "offline" or 
          status["ml_model"]["status"] == "offline"):
        status["overall"] = "services_offline"
    else:
        status["overall"] = "partial_operational"
    
    return status
