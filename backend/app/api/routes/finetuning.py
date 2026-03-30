# app/api/routes/finetuning.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_training_controller
from app.controllers.training_controller import TrainingController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finetuning", tags=["fine-tuning"])


class StartFinetuningRequest(BaseModel):
    """Request model for starting fine-tuning"""
    model_type: str = Field(..., description="Type of model (bert, gpt, llama, etc.)")
    model_name: str = Field(..., description="Model name/identifier")
    strategy_type: str = Field(..., description="Fine-tuning strategy (full_finetune, lora, adapter, prefix_tuning)")
    task_type: str = Field(..., description="Task type (classification, summarization, qa, generation)")
    dataset_path: str = Field(..., description="Path to dataset")
    config: Dict[str, Any] = Field(default_factory=dict, description="Fine-tuning configuration")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags for categorization")


class FinetuningStatusResponse(BaseModel):
    """Response model for fine-tuning status"""
    job_id: str
    job_type: str
    status: str
    progress: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    base_model_type: Optional[str] = None
    base_model_name: Optional[str] = None
    strategy_type: Optional[str] = None
    task_type: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/start", response_model=Dict[str, Any])
async def start_finetuning(
    request: StartFinetuningRequest,
    controller: TrainingController = Depends(get_training_controller)
):
    """
    Start a fine-tuning job
    
    Args:
        request: Fine-tuning request parameters
    
    Returns:
        Job information with job_id and execution_id
    """
    try:
        result = await controller.start_finetuning(
            base_model_type=request.model_type,
            base_model_name=request.model_name,
            strategy_type=request.strategy_type,
            task_type=request.task_type,
            dataset_path=request.dataset_path,
            config=request.config,
            tags=request.tags
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start fine-tuning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=FinetuningStatusResponse)
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
    
    return FinetuningStatusResponse(**status)


@router.get("/jobs", response_model=Dict[str, Any])
async def list_finetuning_jobs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    strategy_type: Optional[str] = None,
    task_type: Optional[str] = None,
    user_id: Optional[str] = None,
    controller: TrainingController = Depends(get_training_controller)
):
    """
    List fine-tuning jobs with filters
    
    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        status: Filter by status
        strategy_type: Filter by strategy type
        task_type: Filter by task type
        user_id: Filter by user ID
    
    Returns:
        List of fine-tuning jobs
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
    
    return result


@router.post("/cancel/{job_id}", response_model=Dict[str, Any])
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
        return {"message": "Job cancelled successfully", "job_id": job_id}
    else:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/strategies", response_model=List[str])
async def get_strategies():
    """Get available fine-tuning strategies"""
    return ["full_finetune", "lora", "adapter", "prefix_tuning"]


@router.get("/tasks", response_model=List[str])
async def get_tasks():
    """Get available fine-tuning tasks"""
    return ["classification", "summarization", "qa", "generation"]


@router.get("/datasets", response_model=Dict[str, Any])
async def get_finetuning_datasets(
    task_type: Optional[str] = None
):
    """
    Get available fine-tuning datasets
    
    Args:
        task_type: Optional task type filter
    
    Returns:
        List of available datasets
    """
    from app.core.finetuning.datasets import datasets
    
    if task_type:
        return {
            "task_type": task_type,
            "datasets": datasets.get(task_type, [])
        }
    else:
        return {
            "datasets": datasets
        }


@router.get("/metrics/{job_id}", response_model=Dict[str, Any])
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
    
    return metrics


@router.get("/logs/{job_id}", response_model=Dict[str, Any])
async def get_finetuning_logs(
    job_id: str,
    tail: int = 100,
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
    
    return logs


@router.get("/statistics", response_model=Dict[str, Any])
async def get_finetuning_statistics(
    user_id: Optional[str] = None,
    controller: TrainingController = Depends(get_training_controller)
):
    """
    Get statistics about fine-tuning jobs
    
    Args:
        user_id: Filter by user ID
    
    Returns:
        Statistics dictionary
    """
    return await controller.get_statistics(user_id)