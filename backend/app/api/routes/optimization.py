from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import uuid
from app.core.optimization.optimizer_factory import OptimizerFactory
from app.core.config import settings
from ..models import OptimizationRequest, JobResponse

router = APIRouter(prefix="/optimization", tags=["optimization"])

# Store optimization jobs
optimizations = {}

class OptimizationJob:
    def __init__(self, job_id: str, request: OptimizationRequest):
        self.job_id = job_id
        self.request = request
        self.status = "pending"
        self.progress = 0
        self.result = None
        self.error = None

@router.post("/optimize", response_model=JobResponse)
async def optimize_model(
    background_tasks: BackgroundTasks,
    request: OptimizationRequest
):
    """Optimize a model"""
    job_id = str(uuid.uuid4())
    optimizations[job_id] = OptimizationJob(job_id, request)
    
    background_tasks.add_task(
        run_optimization,
        job_id,
        request
    )
    
    return JobResponse(job_id=job_id, status="started", message="Optimization job started")

@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_status(job_id: str):
    """Get optimization status"""
    job = optimizations.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Optimization job not found")
    
    return {
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error
    }

@router.get("/types", response_model=List[str])
async def get_optimization_types():
    """Get available optimization types"""
    return ["pruning", "distillation", "quantization"]

async def run_optimization(job_id: str, request: OptimizationRequest):
    """Background task for model optimization"""
    job = optimizations[job_id]
    job.status = "running"
    
    try:
        # Update progress
        job.progress = 10
        
        # Get optimizer
        optimizer = OptimizerFactory.get_optimizer(
            request.optimization_type,
            request.config
        )
        
        job.progress = 30
        
        # Load model
        model = optimizer.load_model(request.model_path)
        
        job.progress = 50
        
        # Apply optimization
        optimized_model = optimizer.optimize(model)
        
        job.progress = 80
        
        # Save optimized model
        output_path = f"{settings.MODEL_STORAGE_PATH}/optimized/{job_id}"
        optimizer.save_model(optimized_model, output_path)
        
        # Get metrics
        metrics = optimizer.get_metrics(optimized_model)
        
        job.result = {
            "output_path": output_path,
            "optimization_type": request.optimization_type,
            "metrics": metrics,
            "original_size": optimizer.original_size,
            "optimized_size": optimizer.optimized_size,
            "compression_ratio": optimizer.original_size / optimizer.optimized_size if optimizer.optimized_size > 0 else 0
        }
        job.status = "completed"
        job.progress = 100
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)