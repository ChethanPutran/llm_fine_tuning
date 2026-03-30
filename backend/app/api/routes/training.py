# app/api/routes/training.py

from fastapi import APIRouter, Depends, HTTPException
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


class StartFinetuningRequest(BaseModel):
    """Request model for starting fine-tuning"""
    model_type: str = Field(..., description="Type of model")
    model_name: str = Field(..., description="Model name/identifier")
    strategy_type: str = Field(..., description="Fine-tuning strategy (lora, full, etc.)")
    task_type: str = Field(..., description="Task type (classification, generation, etc.)")
    dataset_path: str = Field(..., description="Path to dataset")
    config: Dict[str, Any] = Field(default_factory=dict, description="Fine-tuning configuration")


@router.post("/start", response_model=Dict[str, Any])
async def start_training(
    request: StartTrainingRequest,
    controller: TrainingController = Depends(get_training_controller)
):
    """Start model training"""
    try:
        result = await controller.start_job(
            model_type=request.model_type,
            model_name=request.model_name,
            dataset_path=request.dataset_path,
            config=request.config
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finetune", response_model=Dict[str, Any])
async def start_finetuning(
    request: StartFinetuningRequest,
    controller: TrainingController = Depends(get_training_controller)
):
    """Start model fine-tuning"""
    try:
        result = await controller.start_job(
            model_type=request.model_type,
            model_name=request.model_name,
            strategy_type=request.strategy_type,
            task_type=request.task_type,
            dataset_path=request.dataset_path,
            config=request.config
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start fine-tuning: {e}")
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
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    controller: TrainingController = Depends(get_training_controller)
):
    """List all training jobs"""
    return await controller.list_jobs(limit=limit, offset=offset, status=status)


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