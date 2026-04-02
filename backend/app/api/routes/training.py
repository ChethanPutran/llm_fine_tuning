# app/api/routes/training.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging

from app.dependencies.controller import get_training_controller
from app.controllers.training_controller import TrainingController
from app.api.models import LogsResponse, StartTrainingRequest
from app.api.models import ListResourcesResponse, MetricResponse, RequestBase, StartOptimizationRequest, ExecutionStatusResponse, JobCreationResponse, JobStatusResponse, ListJobsResponse, StartCollectionRequest, StatisticsResponse 


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])


@router.post("/add", response_model=JobCreationResponse)
async def create_training_job(
    request: StartTrainingRequest,
    controller: TrainingController = Depends(get_training_controller)
):
    """Create a training job"""
    try:
        # Create the job
        result = await controller.add_job(
            config=request.config,
            model_config=request.train_model_config,
            dataset_config=request.dataset_config,
            user_id=request.user_id,  # In real implementation, get from auth context
            tags=request.tags
        )
        return JobCreationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create training job: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/execute/{job_id}", response_model=ExecutionStatusResponse)
async def execute_training_job(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Execute an existing training or fine-tuning job"""
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ExecutionStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute training job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_training_status(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Get training job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**status)


@router.get("/jobs", response_model=ListJobsResponse)
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
    return ListJobsResponse(**result)


@router.delete("/jobs/{job_id}", response_model=JobStatusResponse)
async def cancel_training_job(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Cancel a training job"""
    cancelled = await controller.remove_job(job_id)
    if cancelled:
        return JobStatusResponse(**cancelled)
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_training_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: TrainingController = Depends(get_training_controller)
):
    """Get training statistics"""
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get training statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{job_id}", response_model=MetricResponse)
async def get_training_metrics(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Get detailed training metrics"""
    metrics = await controller.get_job_metrics(job_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Job not found")
    return MetricResponse(**metrics)


@router.get("/logs/{job_id}", response_model=LogsResponse)
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
    
    return LogsResponse(logs=logs, tail=tail,user_id=None,
                        status="success", message="Logs retrieved successfully", error=None, tags=[])


@router.get("/strategies", response_model=ListResourcesResponse)
async def get_strategies(
):
    """Get available fine-tuning strategies"""
    return ListResourcesResponse(
        items=[
            {"name": "full_finetune", "description": "Full fine-tuning strategy"},
            {"name": "lora", "description": "Low-Rank Adaptation strategy"},
            {"name": "adapter", "description": "Adapter strategy"},
            {"name": "prefix_tuning", "description": "Prefix tuning strategy"}
        ],
        user_id=None,
        status="success",
        message="Available strategies retrieved successfully",
        error=None,
        tags=[]
    )


@router.get("/tasks", response_model=ListResourcesResponse)
async def get_tasks(
):
    """Get available fine-tuning tasks"""
    return ListResourcesResponse(
        items=[
            {"name": "classification", "description": "Classification task"},
            {"name": "summarization", "description": "Summarization task"},
            {"name": "qa", "description": "Question Answering task"},
            {"name": "generation", "description": "Text Generation task"}
        ],
        user_id=None,
        status="success",
        message="Available tasks retrieved successfully",
        error=None,
        tags=[]
    )


@router.get("/configs", response_model=ListResourcesResponse)
async def get_training_configs(
    request: RequestBase = Depends(),
):
    """Get available training configurations"""
    return ListResourcesResponse(
        items=[
            {
                "name": "default_training",
                "description": "Default training configuration",
                "parameters": {
                    "learning_rate": 3e-5,
                    "batch_size": 32,
                    "epochs": 3,
                    "warmup_steps": 500,
                    "weight_decay": 0.01
                }
            },
            {
                "name": "default_finetuning",
                "description": "Default fine-tuning configuration",
                "parameters": {
                    "learning_rate": 5e-5,
                    "batch_size": 16,
                    "epochs": 5,
                    "warmup_ratio": 0.1,
                    "gradient_accumulation_steps": 2
                }
            }   
        ],
        **request.dict()
    )
         