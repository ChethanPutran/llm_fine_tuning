# app/api/routes/preprocessing.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import json
import os
import logging
from uuid import uuid4

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
    auto_execute: bool = Field(True, description="Automatically execute the job after creation")
    tags: Optional[List[str]] = Field(None, description="Optional tags for categorization")


@router.post("/add", response_model=Dict[str, Any])
async def create_preprocessing_job(
    request: StartPreprocessingRequest,
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Create a preprocessing job"""
    try:
        # Create the job
        result = await controller.add_job(
            input_path=request.input_path,
            config=request.config,
            output_path=request.output_path,
            user_id="system",  # In real implementation, get from auth context
            tags=request.tags
        )
        
        # Auto-execute if requested
        if request.auto_execute and result.get("job_id"):
            job_id = result["job_id"]
            execution_result = await controller.execute_job(job_id)
            result["execution_id"] = execution_result.get("execution_id")
            result["execution_status"] = "started"
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create preprocessing job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=Dict[str, Any])
async def execute_preprocessing_job(
    job_id: str,
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Execute an existing preprocessing job"""
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute preprocessing job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=Dict[str, Any])
async def upload_and_preprocess(
    file: UploadFile = File(...),
    config: str = Form(...),
    auto_execute: bool = Form(True),
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Upload a file and start preprocessing"""
    try:
        # Parse config
        config_dict = json.loads(config)
        config_obj = PreprocessingConfig(**config_dict)
        
        # Save uploaded file
        upload_dir = os.path.join(settings.DATA_STORAGE_PATH, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create job
        result = await controller.add_job(
            input_path=file_path,
            config=config_obj,
            user_id="system",
            tags=["uploaded"]
        )
        
        # Auto-execute if requested
        if auto_execute and result.get("job_id"):
            job_id = result["job_id"]
            execution_result = await controller.execute_job(job_id)
            result["execution_id"] = execution_result.get("execution_id")
            result["execution_status"] = "started"
        
        return result
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON config: {e}")
    except Exception as e:
        logger.error(f"Failed to upload and preprocess: {e}")
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
    status: Optional[str] = Query(None, description="Filter by job status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """List all preprocessing jobs with pagination and filters"""
    result = await controller.list_jobs(
        status=status,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return result


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


@router.get("/statistics", response_model=Dict[str, Any])
async def get_preprocessing_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Get preprocessing statistics"""
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get preprocessing statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{job_id}", response_model=Dict[str, Any])
async def get_preprocessing_metrics(
    job_id: str,
    controller: PreprocessingController = Depends(get_preprocessing_controller)
):
    """Get detailed preprocessing metrics"""
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