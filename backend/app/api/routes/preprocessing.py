# app/api/routes/preprocessing.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import json
import os
import logging

from app.core.config import settings
from app.common.job_models import PreprocessingConfig
from app.dependencies.controller import get_preprocessing_controller
from app.controllers.preprocessing_controller import PreprocessingController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])


class StartPreprocessingRequest(BaseModel):
    """Request model for starting preprocessing"""
    input_path: str = Field(..., description="Path to input data")
    output_path: Optional[str] = Field(None, description="Output path (optional)")
    config: PreprocessingConfig = Field(..., description="Preprocessing configuration")


@router.post("/start", response_model=Dict[str, Any])
async def start_preprocessing(
    request: StartPreprocessingRequest,
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Start a preprocessing job"""
    try:
        result = await controller.start_job(
            input_path=request.input_path,
            config=request.config,
            output_path=request.output_path
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start preprocessing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-from-upload", response_model=Dict[str, Any])
async def start_preprocessing_from_upload(
    file: UploadFile = File(...),
    config: str = Form(...),
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Start preprocessing from uploaded file"""
    try:
        # Parse config
        config_dict = json.loads(config)
        config_obj = PreprocessingConfig(**config_dict)
        
        # Save uploaded file
        upload_dir = os.path.join(settings.DATA_STORAGE_PATH, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, str(file.filename))
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Start job
        result = await controller.start_job(
            input_path=file_path,
            config=config_obj
        )
        
        return result
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON config: {e}")
    except Exception as e:
        logger.error(f"Failed to start preprocessing from upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_preprocessing_status(
    job_id: str,
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Get preprocessing job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/jobs", response_model=Dict[str, Any])
async def list_preprocessing_jobs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """List all preprocessing jobs"""
    return await controller.list_jobs(limit=limit, offset=offset, status=status)


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
async def cancel_preprocessing_job(
    job_id: str,
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Cancel a preprocessing job"""
    cancelled = await controller.cancel_job(job_id)
    if cancelled:
        return {"message": "Job cancelled successfully", "job_id": job_id}
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/statistics/{job_id}", response_model=Dict[str, Any])
async def get_preprocessing_statistics(
    job_id: str,
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Get detailed statistics about preprocessing"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if status.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    return status.get("metrics", {})


@router.get("/supported-formats", response_model=Dict[str, Any])
async def get_supported_formats():
    """Get supported input/output formats"""
    return {
        "input_formats": ["csv", "json", "parquet", "txt", "html", "pdf", "docx"],
        "output_formats": ["parquet", "csv", "json", "avro"],
        "max_file_size_mb": 1024,
        "supported_languages": ["en", "zh", "es", "fr", "de", "ja", "ko"]
    }