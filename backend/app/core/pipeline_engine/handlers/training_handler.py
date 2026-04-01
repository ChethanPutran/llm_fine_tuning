# app/core/pipeline_engine/handlers/training_handler.py

"""
Handler for training jobs
"""

from typing import Dict, Any
import pandas as pd
import logging

from app.common.job_models import TrainingJob
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.training.trainer import Trainer
from app.core.training.config import TrainingConfig
from app.core.models.model_factory import ModelFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


class TrainingHandler(BaseHandler):
    """Handler for training jobs"""
    
    async def execute(self, job: TrainingJob) -> Dict[str, Any]:
        """Execute training"""
        
        await self._mark_started(job.job_id)
        
        try:
            await self._update_progress(job.job_id, 10, "Loading dataset")
            
            # Load dataset
            df = pd.read_csv(job.dataset_path)
            
            await self._update_progress(job.job_id, 30, "Loading model")
            
            # Get model
            model = ModelFactory.get_model(
                job.model_type,
                job.model_name,
                job.config
            )
            
            await self._update_progress(job.job_id, 50, "Preparing data")
            
            # Prepare dataset
            texts = df['text'].tolist()
            labels = df['label'].tolist()
            
            # Split dataset
            split_idx = int(len(texts) * 0.8)
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
            
            await self._update_progress(job.job_id, 70, "Training model")
            
            # Create trainer
            config = TrainingConfig()
            for key, value in job.config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            trainer = Trainer(model.model, config.to_dict())
            
            # Train
            results = trainer.train(train_dataset, eval_dataset)
            
            await self._update_progress(job.job_id, 90, "Saving model")
            
            # Save model
            output_path = f"{settings.MODEL_STORAGE_PATH}/training/{job.job_id}"
            model.save(output_path)
            
            result = {
                "success": True,
                "output_path": output_path,
                "metrics": {
                    "train_loss": results['train_losses'][-1] if results['train_losses'] else None,
                    "eval_loss": results['eval_losses'][-1] if results['eval_losses'] else None,
                    "train_accuracy": results['train_accuracies'][-1] if results['train_accuracies'] else None
                },
                "model_params": model.get_parameters()
            }
            
            job.model_path = output_path
            job.metrics = result["metrics"]
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise