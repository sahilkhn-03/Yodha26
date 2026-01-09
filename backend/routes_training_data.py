"""
Training Data Collection Routes
Endpoints for collecting and managing labeled heart rate data for ML model training.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import csv
import io

from database import get_db
from models import HeartRateTrainingData

router = APIRouter(prefix="/api/training", tags=["Training Data"])


class TrainingDataCreate(BaseModel):
    """Schema for creating a new training data point"""
    bpm: int = Field(..., ge=30, le=220, description="Heart rate in BPM")
    stress_level: float = Field(..., ge=0.0, le=1.0, description="Stress level from 0 (normal) to 1 (stressed)")
    systolic: Optional[int] = Field(None, ge=60, le=250)
    diastolic: Optional[int] = Field(None, ge=40, le=150)
    patient_id: Optional[str] = None
    session_id: Optional[str] = None
    notes: Optional[str] = None


class TrainingDataResponse(BaseModel):
    """Schema for training data response"""
    id: int
    timestamp: datetime
    bpm: int
    stress_level: float
    systolic: Optional[int]
    diastolic: Optional[int]
    patient_id: Optional[str]
    session_id: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class DatasetStats(BaseModel):
    """Statistics about the collected dataset"""
    total_samples: int
    normal_samples: int  # stress_level < 0.5
    stress_samples: int  # stress_level >= 0.5
    avg_bpm: float
    min_bpm: int
    max_bpm: int


@router.post("/record", response_model=TrainingDataResponse)
async def record_training_data(
    data: TrainingDataCreate,
    db: Session = Depends(get_db)
):
    """
    Record a labeled heart rate sample for training.
    
    This endpoint saves a single heart rate reading with its stress label.
    Use this while monitoring the EKG simulation to build your dataset.
    """
    try:
        # Create new training data record
        db_record = HeartRateTrainingData(
            bpm=data.bpm,
            stress_level=data.stress_level,
            systolic=data.systolic,
            diastolic=data.diastolic,
            patient_id=data.patient_id,
            session_id=data.session_id,
            notes=data.notes
        )
        
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        return db_record
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save training data: {str(e)}")


@router.get("/stats", response_model=DatasetStats)
async def get_dataset_stats(db: Session = Depends(get_db)):
    """
    Get statistics about the collected training dataset.
    
    Shows how many samples you've collected, class distribution, and BPM ranges.
    """
    try:
        records = db.query(HeartRateTrainingData).all()
        
        if not records:
            return DatasetStats(
                total_samples=0,
                normal_samples=0,
                stress_samples=0,
                avg_bpm=0.0,
                min_bpm=0,
                max_bpm=0
            )
        
        total = len(records)
        normal = sum(1 for r in records if r.stress_level < 0.5)
        stress = total - normal
        bpms = [r.bpm for r in records]
        
        return DatasetStats(
            total_samples=total,
            normal_samples=normal,
            stress_samples=stress,
            avg_bpm=sum(bpms) / len(bpms),
            min_bpm=min(bpms),
            max_bpm=max(bpms)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/data", response_model=List[TrainingDataResponse])
async def get_training_data(
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """
    Retrieve collected training data.
    
    Use this to review your dataset or for manual inspection.
    """
    try:
        records = db.query(HeartRateTrainingData)\
            .order_by(HeartRateTrainingData.timestamp.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        return records
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve data: {str(e)}")


@router.get("/export/csv")
async def export_dataset_csv(db: Session = Depends(get_db)):
    """
    Export the entire training dataset as a CSV file.
    
    Download this file to train your ML model.
    Format: timestamp,bpm,systolic,diastolic,stress_level,patient_id,session_id,notes
    """
    try:
        records = db.query(HeartRateTrainingData)\
            .order_by(HeartRateTrainingData.timestamp)\
            .all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'id', 'timestamp', 'bpm', 'systolic', 'diastolic', 
            'stress_level', 'patient_id', 'session_id', 'notes'
        ])
        
        # Write data
        for record in records:
            writer.writerow([
                record.id,
                record.timestamp.isoformat(),
                record.bpm,
                record.systolic or '',
                record.diastolic or '',
                record.stress_level,
                record.patient_id or '',
                record.session_id or '',
                record.notes or ''
            ])
        
        # Prepare response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=heartrate_training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")


@router.delete("/data/{record_id}")
async def delete_training_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a specific training data record.
    
    Use this to remove mislabeled or erroneous data points.
    """
    try:
        record = db.query(HeartRateTrainingData).filter(HeartRateTrainingData.id == record_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        db.delete(record)
        db.commit()
        
        return {"message": f"Record {record_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete record: {str(e)}")


@router.delete("/data/clear-all")
async def clear_all_training_data(
    confirm: str,
    db: Session = Depends(get_db)
):
    """
    Clear ALL training data. USE WITH CAUTION!
    
    Must provide confirm="DELETE_ALL" to proceed.
    """
    if confirm != "DELETE_ALL":
        raise HTTPException(
            status_code=400, 
            detail="Must provide confirm='DELETE_ALL' to clear all data"
        )
    
    try:
        count = db.query(HeartRateTrainingData).delete()
        db.commit()
        
        return {"message": f"Deleted {count} training records"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")
