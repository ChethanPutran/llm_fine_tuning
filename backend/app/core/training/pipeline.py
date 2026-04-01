from typing import Dict, Any, Optional, List
from .tasks.base import TrainingTask
from ..models.base import BaseModel
from ..training.trainer import Trainer
from ..training.config import TrainingConfig
import torch

class TrainingPipeline:
    """Pipeline for fine-tuning models"""
    
    def __init__(self, model: BaseModel,task: TrainingTask, trainer_config:TrainingConfig):
        self.model = model
        self.task = task
        self.trainer_config = trainer_config
        self.trainer = None
        
    def setup(self, dataset: Any) -> None:
        """Setup pipeline with dataset"""
        
        # Prepare dataset for task
        self.task_dataset = self.task.prepare_dataset(dataset)
        
        # Initialize trainer
        self.trainer = Trainer(
            model=self.model.model,
            config=self.trainer_config
        )
    
    async def train(self) -> Dict[str, Any]:
        """Execute fine-tuning"""
        if not self.trainer:
            raise ValueError("Pipeline not set up")
        
        # Train model
        results = await self.trainer.train(
            train_dataset=self.task_dataset.get_train_data(),
            eval_dataset=self.task_dataset.get_eval_data()
        )
        
        return results
    
    def evaluate(self, test_dataset: Any) -> Dict[str, float]:
        """Evaluate fine-tuned model"""
        if not self.trainer:
            raise ValueError("Pipeline not set up")
        
        return self.trainer.evaluate(test_dataset)
    