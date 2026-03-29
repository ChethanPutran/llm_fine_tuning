from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from app.core.finetuning.pipeline import FinetuningPipeline
from app.core.finetuning.strategies import FinetuningStrategyFactory
from app.core.finetuning import FinetuningTaskFactory
from app.core.models.model_factory import ModelFactory
from app.core.config import settings
import uuid

router = APIRouter(prefix="/finetuning", tags=["fine-tuning"])

# Store job statuses
jobs = {}

class FinetuningJob:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "pending"
        self.progress = 0
        self.result = None
        self.error = None

@router.post("/start")
async def start_finetuning(
    background_tasks: BackgroundTasks,
    model_type: str,
    model_name: str,
    strategy_type: str,
    task_type: str,
    dataset_path: str,
    config: Dict[str, Any]
):
    """Start a fine-tuning job"""
    job_id = str(uuid.uuid4())
    jobs[job_id] = FinetuningJob(job_id)
    
    background_tasks.add_task(
        run_finetuning,
        job_id,
        model_type,
        model_name,
        strategy_type,
        task_type,
        dataset_path,
        config
    )
    
    return {"job_id": job_id, "status": "started"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get fine-tuning job status"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error
    }

@router.get("/strategies")
async def get_strategies() -> List[str]:
    """Get available fine-tuning strategies"""
    return ["full_finetune", "lora", "adapter", "prefix_tuning"]

@router.get("/tasks")
async def get_tasks() -> List[str]:
    """Get available fine-tuning tasks"""
    return ["classification", "summarization", "qa", "generation"]


@router.get("/datasets")
async def get_finetuning_dataset(
    task_type: str
):
    """Get fine-tuning dataset for a specific task"""
    from ...core.finetuning.datasets import datasets
    return datasets.get(task_type, [])



async def run_finetuning(job_id, model_type, model_name, strategy_type, 
                         task_type, dataset_path, config):
    """Background task for fine-tuning"""
    job = jobs[job_id]
    job.status = "running"
    
    try:
        # Load dataset
        import pandas as pd
        dataset = pd.read_csv(dataset_path)
        
        # Get model
        model = ModelFactory.get_model(model_type, model_name, config)
        
        # Get strategy
        strategy = FinetuningStrategyFactory.get_strategy(strategy_type, config)
        
        # Get task
        task = FinetuningTaskFactory.get_task(task_type, config)
        
        # Create pipeline
        pipeline = FinetuningPipeline(model, strategy, task, config)
        pipeline.setup(dataset)
        
        # Update progress
        job.progress = 50
        
        # Train
        results = pipeline.train()
        
        # Save model
        model_path = f"{settings.MODEL_STORAGE_PATH}/{job_id}"
        model.save(model_path)
        
        job.result = {
            "model_path": model_path,
            "metrics": results
        }
        job.status = "completed"
        job.progress = 100
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
