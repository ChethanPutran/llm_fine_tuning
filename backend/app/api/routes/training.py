# app/api/routes/training.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_training_controller
from app.controllers.training_controller import TrainingController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])


class StartTrainingRequest(BaseModel):
    """Request model for starting training"""
    model_type: str = Field(..., description="Type of model (bert, gpt, etc.)")
    model_name: str = Field(..., description="Model name/identifier")
    dataset_path: str = Field(..., description="Path to training dataset")
    config: Dict[str, Any] = Field(default_factory=dict, description="Training configuration")
    auto_execute: bool = Field(True, description="Automatically execute the job after creation")
    tags: Optional[List[str]] = Field(None, description="Optional tags for categorization")


class StartFinetuningRequest(BaseModel):
    """Request model for starting fine-tuning"""
    model_type: str = Field(..., description="Type of model")
    model_name: str = Field(..., description="Model name/identifier")
    strategy_type: str = Field(..., description="Fine-tuning strategy (lora, full, etc.)")
    task_type: str = Field(..., description="Task type (classification, generation, etc.)")
    dataset_path: str = Field(..., description="Path to dataset")
    config: Dict[str, Any] = Field(default_factory=dict, description="Fine-tuning configuration")
    auto_execute: bool = Field(True, description="Automatically execute the job after creation")
    tags: Optional[List[str]] = Field(None, description="Optional tags for categorization")


@router.post("/add", response_model=Dict[str, Any])
async def create_training_job(
    request: StartTrainingRequest,
    controller: TrainingController = Depends(get_training_controller)
):
    """Create a training job"""
    try:
        # Create the job
        result = await controller.add_job(
            model_type=request.model_type,
            model_name=request.model_name,
            dataset_path=request.dataset_path,
            config=request.config,
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
        logger.error(f"Failed to create training job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finetune", response_model=Dict[str, Any])
async def create_finetuning_job(
    request: StartFinetuningRequest,
    controller: TrainingController = Depends(get_training_controller)
):
    """Create a fine-tuning job"""
    try:
        # Create the job
        result = await controller.add_finetuning_job(
            base_model_type=request.model_type,
            base_model_name=request.model_name,
            strategy_type=request.strategy_type,
            task_type=request.task_type,
            dataset_path=request.dataset_path,
            config=request.config,
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
        logger.error(f"Failed to create fine-tuning job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=Dict[str, Any])
async def execute_training_job(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Execute an existing training or fine-tuning job"""
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute training job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_training_status(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Get training job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/jobs", response_model=Dict[str, Any])
async def list_training_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type (training/finetuning)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    controller: TrainingController = Depends(get_training_controller)
):
    """List all training and fine-tuning jobs with pagination and filters"""
    result = await controller.list_jobs(
        job_type=job_type,
        status=status,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return result


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
async def cancel_training_job(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Cancel a training job"""
    cancelled = await controller.cancel_job(job_id)
    if cancelled:
        return {"message": "Job cancelled successfully", "job_id": job_id}
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_training_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: TrainingController = Depends(get_training_controller)
):
    """Get training statistics"""
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get training statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{job_id}", response_model=Dict[str, Any])
async def get_training_metrics(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Get detailed training metrics"""
    metrics = await controller.get_job_metrics(job_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Job not found")
    return metrics


@router.get("/logs/{job_id}", response_model=Dict[str, Any])
async def get_training_logs(
    job_id: str,
    tail: int = Query(100, ge=1, le=1000, description="Number of lines to return"),
    controller: TrainingController = Depends(get_training_controller)
):
    """Get training logs"""
    logs = await controller.get_job_logs(job_id)
    if not logs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Return only the last 'tail' lines if logs is a list
    if isinstance(logs, list) and len(logs) > tail:
        logs = logs[-tail:]
    
    return {"job_id": job_id, "logs": logs, "tail": tail}


@router.get("/strategies", response_model=List[str])
async def get_strategies():
    """Get available fine-tuning strategies"""
    return ["full_finetune", "lora", "adapter", "prefix_tuning"]


@router.get("/tasks", response_model=List[str])
async def get_tasks():
    """Get available fine-tuning tasks"""
    return ["classification", "summarization", "qa", "generation"]


@router.get("/configs", response_model=Dict[str, Any])
async def get_training_configs():
    """Get available training configurations"""
    return {
        "default": {
            "learning_rate": 2e-5,
            "batch_size": 32,
            "epochs": 3,
            "warmup_steps": 500,
            "weight_decay": 0.01
        },
        "finetuning": {
            "learning_rate": 5e-5,
            "batch_size": 16,
            "epochs": 5,
            "warmup_ratio": 0.1,
            "gradient_accumulation_steps": 2
        }
    }