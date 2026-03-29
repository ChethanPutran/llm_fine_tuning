from typing import Dict, Any, Optional, List
from .base import FinetuningStrategy, FinetuningTask
from ..models.base import BaseModel
from ..training.trainer import Trainer
import torch

class FinetuningPipeline:
    """Pipeline for fine-tuning models"""
    
    def __init__(self, model: BaseModel, strategy: FinetuningStrategy,
                 task: FinetuningTask, trainer_config: Dict[str, Any]):
        self.model = model
        self.strategy = strategy
        self.task = task
        self.trainer_config = trainer_config
        self.trainer = None
        
    def setup(self, dataset: Any) -> None:
        """Setup pipeline with dataset"""
        # Apply fine-tuning strategy
        self.model.model = self.strategy.apply(self.model.model)
        
        # Prepare dataset for task
        self.task_dataset = self.task.prepare_dataset(dataset)
        
        # Initialize trainer
        self.trainer = Trainer(
            model=self.model.model,
            config=self.trainer_config
        )
    
    def train(self) -> Dict[str, Any]:
        """Execute fine-tuning"""
        if not self.trainer:
            raise ValueError("Pipeline not set up")
        
        # Train model
        results = self.trainer.train(
            train_dataset=self.task_dataset['train'],
            eval_dataset=self.task_dataset.get('eval')
        )
        
        return results
    
    def evaluate(self, test_dataset: Any) -> Dict[str, float]:
        """Evaluate fine-tuned model"""
        if not self.trainer:
            raise ValueError("Pipeline not set up")
        
        return self.trainer.evaluate(test_dataset)