# app/core/pipeline_engine/handlers/finetuning_handler.py

from typing import Dict, Any
import pandas as pd
import logging

from app.common.job_models import FinetuningJob
from app.core.finetuning.pipeline import FinetuningPipeline
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.models.model_factory import ModelFactory
from app.core.finetuning.strategies import FinetuningStrategyFactory
from app.core.finetuning.tasks import FinetuningTaskFactory
from app.core.config import settings
from app.core.training.config import TrainingConfig
from app.core.datasets.factory import DatasetFactory

logger = logging.getLogger(__name__)


class FinetuningHandler(BaseHandler):
    """Handler for fine-tuning jobs"""
    
    async def execute(self, job: FinetuningJob) -> Dict[str, Any]:
        """Execute fine-tuning"""
        
        await self._mark_started(job.job_id)
        
        try:
            tuning_config = job.config
            model_config = job.base_model_config
            dataset_config = job.dataset_config

            await self._update_progress(job.job_id, 10, "Loading dataset")
            
            
            dataset = DatasetFactory.get_dataset(dataset_config.dataset_type, dataset_config)
            
            await self._update_progress(job.job_id, 30, "Loading model")
            
            # Get model
            model = ModelFactory.get_model(model_config)
            
            # Apply fine-tuning strategy
            strategy = FinetuningStrategyFactory.get_strategy(tuning_config.strategy_type, tuning_config)

            await self._update_progress(job.job_id, 40, "Applying fine-tuning strategy")
            model.model = strategy.apply(model.model)

            task = FinetuningTaskFactory.get_task(tuning_config.task_type, tuning_config)

            trainer_config = TrainingConfig(
                learning_rate=tuning_config.learning_rate,
                num_epochs=tuning_config.num_epochs,
                batch_size=tuning_config.batch_size
            )
            trainer = FinetuningPipeline(model=model,
                                         strategy=strategy,
                                         task=task,
                                         trainer_config=trainer_config)
           
            
            await self._update_progress(job.job_id, 50, "Preparing data")
        
            dataset = DatasetFactory.get_dataset(dataset_config.dataset_type, dataset_config)
            trainer.setup(dataset)

            await self._update_progress(job.job_id, 70, "Fine-tuning model")
            # Train
            results = trainer.train()
            
            await self._update_progress(job.job_id, 90, "Saving model")
            
            # Save fine-tuned model
            output_path = f"{settings.MODEL_STORAGE_PATH}/finetuned/{job.job_id}"
            model.save(output_path)
            
            result = {
                "success": True,
                "output_path": output_path,
                "strategy": tuning_config.strategy_type,
                "task": tuning_config.task_type,
                "metrics": {
                    "train_loss": results['train_losses'][-1] if results['train_losses'] else None,
                    "eval_loss": results['eval_losses'][-1] if results['eval_losses'] else None,
                    "train_accuracy": results['train_accuracies'][-1] if results['train_accuracies'] else None
                },
                "trainable_params": strategy.get_trainable_params(model.model)
            }
            
            tuning_config.output_model_path = output_path
            job.metrics = result["metrics"]
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise