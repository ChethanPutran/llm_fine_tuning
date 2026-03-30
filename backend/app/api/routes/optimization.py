# app/api/routes/optimization.py

from fastapi import APIRouter, Depends, HTTPException
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


@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_model(
    request: StartOptimizationRequest,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """Optimize a model"""
    try:
        result = await controller.start_job(
            model_path=request.model_path,
            optimization_type=request.optimization_type,
            config=request.config
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start optimization: {e}")
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
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    controller: OptimizationController = Depends(get_optimization_controller)
):
    """List all optimization jobs"""
    return await controller.list_jobs(limit=limit, offset=offset, status=status)


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


@router.get("/types", response_model=List[str])
async def get_optimization_types():
    """Get available optimization types"""
    return ["pruning", "quantization", "distillation"]


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