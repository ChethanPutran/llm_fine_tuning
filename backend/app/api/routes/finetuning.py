# app/api/routes/finetuning.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_training_controller
from app.controllers.training_controller import TrainingController
from app.api.models import ListResourcesResponse, LogsResponse, MetricResponse, StartFinetuningRequest, FinetuningStatusResponse, FinetuningResponse
from app.api.models import ExecutionStatusResponse, JobCreationResponse, JobStatusResponse, ListJobsResponse, StartCollectionRequest, StatisticsResponse 


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finetuning", tags=["fine-tuning"])



@router.post("/add", response_model=JobCreationResponse)
async def create_finetuning_job(
    request: StartFinetuningRequest,
    controller: TrainingController = Depends(get_training_controller)
):
    """
    Create a fine-tuning job
    
    Creates a job that can be executed later. If auto_execute is True,
    the job will be executed immediately.
    """
    try:
        # Create the job
        result = await controller.add_finetuning_job(
            base_model_config=request.base_model_config,
            dataset_config=request.dataset_config,
            config=request.config,
            user_id="system",  # In real implementation, get from auth context
            tags=request.tags,
            auto_execute=request.auto_execute
        )
        return JobCreationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create fine-tuning job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=ExecutionStatusResponse)
async def execute_finetuning_job(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """Execute an existing fine-tuning job"""
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ExecutionStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute fine-tuning job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_finetuning_status(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """
    Get fine-tuning job status
    
    Args:
        job_id: Job identifier
    
    Returns:
        Job status information
    """
    status = await controller.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Filter to ensure it's a fine-tuning job
    if status.get("job_type") not in ["finetuning", "fine-tuning"]:
        raise HTTPException(status_code=400, detail="Not a fine-tuning job")
    
    return JobStatusResponse(**status)


@router.get("/jobs", response_model=ListJobsResponse)
async def list_finetuning_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    strategy_type: Optional[str] = Query(None, description="Filter by strategy type"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    controller: TrainingController = Depends(get_training_controller)
):
    """
    List fine-tuning jobs with pagination and filters
    """
    result = await controller.list_jobs(
        job_type="finetuning",
        status=status,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    # Filter by strategy_type and task_type if provided
    if strategy_type or task_type:
        filtered_jobs = []
        for job in result.get("jobs", []):
            if strategy_type and job.get("strategy_type") != strategy_type:
                continue
            if task_type and job.get("task_type") != task_type:
                continue
            filtered_jobs.append(job)
        
        result["jobs"] = filtered_jobs
        result["total"] = len(filtered_jobs)
    
    return ListJobsResponse(**result)


@router.post("/cancel/{job_id}", response_model=JobStatusResponse)
async def cancel_finetuning(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """
    Cancel a running fine-tuning job
    
    Args:
        job_id: Job identifier
    
    Returns:
        Cancellation status
    """
    cancelled = await controller.cancel_job(job_id)
    
    if cancelled:
        return JobStatusResponse(**cancelled)
    else:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_finetuning_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: TrainingController = Depends(get_training_controller)
):
    """Get fine-tuning statistics"""
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get fine-tuning statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{job_id}", response_model=MetricResponse)
async def get_finetuning_metrics(
    job_id: str,
    controller: TrainingController = Depends(get_training_controller)
):
    """
    Get detailed metrics for a completed fine-tuning job
    
    Args:
        job_id: Job identifier
    
    Returns:
        Job metrics
    """
    metrics = await controller.get_job_metrics(job_id)
    
    if not metrics:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if metrics.get("error"):
        raise HTTPException(status_code=400, detail=metrics["error"])
    
    return MetricResponse(**metrics)


@router.get("/logs/{job_id}", response_model=LogsResponse)
async def get_finetuning_logs(
    job_id: str,
    tail: int = Query(100, ge=1, le=1000, description="Number of lines to return"),
    controller: TrainingController = Depends(get_training_controller)
):
    """
    Get logs for a fine-tuning job
    
    Args:
        job_id: Job identifier
        tail: Number of lines to return from the end
    
    Returns:
        Job logs
    """
    logs = await controller.get_job_logs(job_id)
    
    if not logs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Return only the last 'tail' lines if logs is a list
    if isinstance(logs, list) and len(logs) > tail:
        logs = logs[-tail:]
    
    return LogsResponse(**{"job_id": job_id, "logs": logs, "tail": tail})


@router.get("/strategies", response_model=ListResourcesResponse)
async def get_strategies():
    """Get available fine-tuning strategies"""
    return ListResourcesResponse(
        items=[
            {"name": "full_finetune", "description": "Full fine-tuning"},
            {"name": "lora", "description": "Low-Rank Adaptation"},
            {"name": "adapter", "description": "Adapter fine-tuning"},
            {"name": "prefix_tuning", "description": "Prefix tuning"}
        ],
        user_id=None,
        status="success",
        message="Available fine-tuning strategies retrieved successfully",
        error=None,
        tags=[]
    )


@router.get("/tasks", response_model=ListResourcesResponse)
async def get_tasks():
    """Get available fine-tuning tasks"""
    return ListResourcesResponse(
        items=[
            {"name": "classification", "description": "Text classification"},
            {"name": "summarization", "description": "Text summarization"},
            {"name": "qa", "description": "Question answering"},
            {"name": "generation", "description": "Text generation"}
        ],
        user_id=None,
        status="success",
        message="Available fine-tuning tasks retrieved successfully",
        error=None,
        tags=[]
    )