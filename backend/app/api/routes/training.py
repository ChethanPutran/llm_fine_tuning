from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import uuid
import torch
from app.core.training.trainer import Trainer
from app.core.training.configs import TrainingConfig, FinetuningConfig
from app.core.models.model_factory import ModelFactory
from app.core.config import settings
from ..models import TrainingRequest, FinetuningRequest, JobResponse
import pandas as pd
from torch.utils.data import Dataset, DataLoader

router = APIRouter(prefix="/training", tags=["training"])

# Store training jobs
training_jobs = {}

class TrainingJob:
    def __init__(self, job_id: str, request: TrainingRequest):
        self.job_id = job_id
        self.request = request
        self.status = "pending"
        self.progress = 0
        self.result = None
        self.error = None

class TextDataset(Dataset):
    """Simple text dataset for training"""
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(label)
        }

@router.post("/start", response_model=JobResponse)
async def start_training(
    background_tasks: BackgroundTasks,
    request: TrainingRequest
):
    """Start model training"""
    job_id = str(uuid.uuid4())
    training_jobs[job_id] = TrainingJob(job_id, request)
    
    background_tasks.add_task(
        run_training,
        job_id,
        request
    )
    
    return JobResponse(job_id=job_id, status="started", message="Training job started successfully")

@router.post("/finetune", response_model=JobResponse)
async def start_finetuning(
    background_tasks: BackgroundTasks,
    request: FinetuningRequest
):
    """Start model fine-tuning"""
    job_id = str(uuid.uuid4())
    training_jobs[job_id] = TrainingJob(job_id, request)
    
    background_tasks.add_task(
        run_finetuning,
        job_id,
        request
    )
    
    return JobResponse(job_id=job_id, status="started", message="Fine-tuning job started successfully")

@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_status(job_id: str):
    """Get training status"""
    job = training_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    return {
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error
    }

@router.get("/configs")
async def get_training_configs():
    """Get available training configurations"""
    return {
        "default": TrainingConfig().to_dict(),
        "finetuning": FinetuningConfig().to_dict()
    }

async def run_training(job_id: str, request: TrainingRequest):
    """Background task for training"""
    job = training_jobs[job_id]
    job.status = "running"
    
    try:
        # Update progress
        job.progress = 10
        
        # Load dataset
        df = pd.read_csv(request.dataset_path)
        
        # Get model
        model = ModelFactory.get_model(
            request.model_type.value,
            request.model_name,
            request.config
        )
        
        job.progress = 30
        
        # Prepare dataset
        texts = df['text'].tolist()
        labels = df['label'].tolist()
        
        # Split dataset
        split_idx = int(len(texts) * 0.8)
        train_dataset = TextDataset(
            texts[:split_idx],
            labels[:split_idx],
            model.tokenizer,
            request.config.get('max_length', 512)
        )
        eval_dataset = TextDataset(
            texts[split_idx:],
            labels[split_idx:],
            model.tokenizer,
            request.config.get('max_length', 512)
        )
        
        job.progress = 50
        
        # Create trainer
        config = TrainingConfig()
        for key, value in request.config.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        trainer = Trainer(model.model, config.to_dict())
        
        job.progress = 70
        
        # Train
        results = trainer.train(train_dataset, eval_dataset)
        
        # Save model
        output_path = f"{settings.MODEL_STORAGE_PATH}/training/{job_id}"
        model.save(output_path)
        
        job.result = {
            "output_path": output_path,
            "metrics": {
                "train_loss": results['train_losses'][-1] if results['train_losses'] else None,
                "eval_loss": results['eval_losses'][-1] if results['eval_losses'] else None,
                "train_accuracy": results['train_accuracies'][-1] if results['train_accuracies'] else None
            },
            "model_params": model.get_parameters()
        }
        job.status = "completed"
        job.progress = 100
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)

async def run_finetuning(job_id: str, request: FinetuningRequest):
    """Background task for fine-tuning"""
    job = training_jobs[job_id]
    job.status = "running"
    
    try:
        # Update progress
        job.progress = 10
        
        # Load dataset
        df = pd.read_csv(request.dataset_path)
        
        # Get model
        model = ModelFactory.get_model(
            request.model_type.value,
            request.model_name,
            request.config
        )
        
        job.progress = 30
        
        # Apply fine-tuning strategy
        from ...finetuning.strategies import FinetuningStrategyFactory
        strategy = FinetuningStrategyFactory.get_strategy(
            request.strategy.value,
            request.config
        )
        model.model = strategy.apply(model.model)
        
        job.progress = 50
        
        # Prepare dataset based on task
        if request.task.value == "classification":
            texts = df['text'].tolist()
            labels = df['label'].tolist()
            
            split_idx = int(len(texts) * 0.8)
            train_dataset = TextDataset(
                texts[:split_idx],
                labels[:split_idx],
                model.tokenizer,
                request.config.get('max_length', 512)
            )
            eval_dataset = TextDataset(
                texts[split_idx:],
                labels[split_idx:],
                model.tokenizer,
                request.config.get('max_length', 512)
            )
        else:
            # For other tasks, implement similar dataset preparation
            train_dataset = None
            eval_dataset = None
        
        job.progress = 70
        
        # Create trainer
        config = FinetuningConfig()
        for key, value in request.config.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        trainer = Trainer(model.model, config.to_dict())
        
        # Train
        results = trainer.train(train_dataset, eval_dataset)
        
        # Save fine-tuned model
        output_path = f"{settings.MODEL_STORAGE_PATH}/finetuned/{job_id}"
        model.save(output_path)
        
        job.result = {
            "output_path": output_path,
            "strategy": request.strategy.value,
            "task": request.task.value,
            "metrics": {
                "train_loss": results['train_losses'][-1] if results['train_losses'] else None,
                "eval_loss": results['eval_losses'][-1] if results['eval_losses'] else None,
                "train_accuracy": results['train_accuracies'][-1] if results['train_accuracies'] else None
            },
            "trainable_params": strategy.get_trainable_params(model.model)
        }
        job.status = "completed"
        job.progress = 100
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)