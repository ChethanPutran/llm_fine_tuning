# app/core/pipeline_engine/handlers/finetuning_handler.py

"""
Handler for fine-tuning jobs
"""

from typing import Dict, Any
import pandas as pd
import logging

from app.common.job_models import FinetuningJob
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.training.trainer import Trainer
from app.core.training.configs import FinetuningConfig
from app.core.models.model_factory import ModelFactory
from app.core.finetuning.strategies import FinetuningStrategyFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


class FinetuningHandler(BaseHandler):
    """Handler for fine-tuning jobs"""
    
    async def execute(self, job: FinetuningJob) -> Dict[str, Any]:
        """Execute fine-tuning"""
        
        await self._mark_started(job.job_id)
        
        try:
            await self._update_progress(job.job_id, 10, "Loading dataset")
            
            # Load dataset
            df = pd.read_csv(job.dataset_path)
            
            await self._update_progress(job.job_id, 30, "Loading model")
            
            # Get model
            model = ModelFactory.get_model(
                job.base_model_type,
                job.base_model_name,
                job.config
            )
            
            await self._update_progress(job.job_id, 40, "Applying fine-tuning strategy")
            
            # Apply fine-tuning strategy
            strategy = FinetuningStrategyFactory.get_strategy(
                job.strategy_type,
                job.config
            )
            model.model = strategy.apply(model.model)
            
            await self._update_progress(job.job_id, 50, "Preparing data")
            
            # Prepare dataset based on task
            if job.task_type == "classification":
                texts = df['text'].tolist()
                labels = df['label'].tolist()
                
                split_idx = int(len(texts) * 0.8)
                from app.core.pipeline_engine.handlers.training_handler import TextDataset
                train_dataset = TextDataset(
                    texts[:split_idx],
                    labels[:split_idx],
                    model.tokenizer,
                    job.config.get('max_length', 512)
                )
                eval_dataset = TextDataset(
                    texts[split_idx:],
                    labels[split_idx:],
                    model.tokenizer,
                    job.config.get('max_length', 512)
                )
            else:
                # For other tasks, implement similar dataset preparation
                train_dataset = None
                eval_dataset = None
            
            await self._update_progress(job.job_id, 70, "Fine-tuning model")
            
            # Create trainer
            config = FinetuningConfig()
            for key, value in job.config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            trainer = Trainer(model.model, config.to_dict())
            
            # Train
            results = trainer.train(train_dataset, eval_dataset)
            
            await self._update_progress(job.job_id, 90, "Saving model")
            
            # Save fine-tuned model
            output_path = f"{settings.MODEL_STORAGE_PATH}/finetuned/{job.job_id}"
            model.save(output_path)
            
            result = {
                "success": True,
                "output_path": output_path,
                "strategy": job.strategy_type,
                "task": job.task_type,
                "metrics": {
                    "train_loss": results['train_losses'][-1] if results['train_losses'] else None,
                    "eval_loss": results['eval_losses'][-1] if results['eval_losses'] else None,
                    "train_accuracy": results['train_accuracies'][-1] if results['train_accuracies'] else None
                },
                "trainable_params": strategy.get_trainable_params(model.model)
            }
            
            job.output_path = output_path
            job.metrics = result["metrics"]
            job.trainable_params = result["trainable_params"]
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise