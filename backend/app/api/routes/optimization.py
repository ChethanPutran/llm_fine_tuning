# app/api/routes/optimization.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_optimization_controller
from app.controllers.optimization_controller import OptimizationController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["optimization"])


class StartOptimizationRequest(BaseModel):
    """Request model for starting optimization"""
    model_path: str = Field(..., description="Path to the model to optimize")
    optimization_type: str = Field(..., description="Type of optimization (pruning, quantization, distillation)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Optimization configuration")
    auto_execute: bool = Field(True, description="Automatically execute the job after creation")
    tags: Optional[List[str]] = Field(None, description="Optional tags for categorization")


@router.post("/add", response_model=Dict[str, Any])
async def create_optimization_job(
    request: StartOptimizationRequest,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Create an optimization job"""
    try:
        # Create the job
        result = await controller.add_job(
            model_path=request.model_path,
            optimization_type=request.optimization_type,
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
        logger.error(f"Failed to create optimization job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=Dict[str, Any])
async def execute_optimization_job(
    job_id: str,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Execute an existing optimization job"""
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute optimization job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_optimization_status(
    job_id: str,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Get optimization job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/jobs", response_model=Dict[str, Any])
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
    return result


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
async def cancel_optimization_job(
    job_id: str,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Cancel an optimization job"""
    cancelled = await controller.cancel_job(job_id)
    if cancelled:
        return {"message": "Job cancelled successfully", "job_id": job_id}
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_optimization_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Get optimization statistics"""
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get optimization statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{job_id}", response_model=Dict[str, Any])
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
    
    return status.get("metrics", {})


@router.get("/types", response_model=List[str])
async def get_optimization_types():
    """Get available optimization types"""
    return ["pruning", "quantization", "distillation"]