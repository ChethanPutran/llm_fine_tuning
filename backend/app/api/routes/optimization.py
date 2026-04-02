# app/api/routes/optimization.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_optimization_controller
from app.controllers.optimization_controller import OptimizationController
from app.api.models import ListResourcesResponse, MetricResponse, RequestBase, StartOptimizationRequest, ExecutionStatusResponse, JobCreationResponse, JobStatusResponse, ListJobsResponse, StartCollectionRequest, StatisticsResponse 


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.post("/add", response_model=JobCreationResponse)
async def create_optimization_job(
    request: StartOptimizationRequest,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Create an optimization job"""
    try:
        # Create the job
        result = await controller.add_job(
            config=request.config,
            user_id="system",  # In real implementation, get from auth context
            tags=request.tags,
            auto_execute=request.auto_execute
        )
        return JobCreationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create optimization job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=ExecutionStatusResponse)
async def execute_optimization_job(
    job_id: str,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Execute an existing optimization job"""
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ExecutionStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute optimization job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_optimization_status(
    job_id: str,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Get optimization job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**status)


@router.get("/jobs", response_model=ListJobsResponse)
async def list_optimization_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    optimization_type: Optional[str] = Query(None, description="Filter by optimization type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """List all optimization jobs with pagination and filters"""
    result = await controller.list_jobs(
        status=status,
        optimization_type=optimization_type,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return ListJobsResponse(**result)


@router.delete("/jobs/{job_id}", response_model=JobStatusResponse)
async def cancel_optimization_job(
    job_id: str,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Cancel an optimization job"""
    cancelled = await controller.cancel_job(job_id)
    if cancelled:
        return JobStatusResponse(**cancelled)
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_optimization_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Get optimization statistics"""
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get optimization statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{job_id}", response_model=MetricResponse)
async def get_optimization_metrics(
    job_id: str,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Get detailed optimization metrics"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if status.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    return MetricResponse(**status.get("metrics", {}))


@router.get("/types", response_model=ListResourcesResponse)
async def get_optimization_types(
):
    """Get available optimization types"""
    return ListResourcesResponse(
        items=[
            {"name": "pruning", "description": "Model pruning to reduce size and improve inference speed"},
            {"name": "quantization", "description": "Model quantization to reduce precision and improve efficiency"},
            {"name": "distillation", "description": "Model distillation to create smaller models with similar performance"}
        ],
        user_id=None,
        status="success",
        message="Available optimization types retrieved successfully",
        error=None,
        tags=[] 
    )