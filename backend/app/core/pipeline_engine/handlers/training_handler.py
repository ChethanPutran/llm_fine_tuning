# app/core/pipeline_engine/handlers/training_handler.py

"""
Handler for training jobs
"""

from typing import Dict, Any
import pandas as pd
import logging

from app.common.job_models import TrainingJob
from app.core.datasets.factory import DatasetFactory
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.training.pipeline import TrainingPipeline
from app.core.training.tasks.factory import TrainingTaskFactory
from app.core.training.config import TrainingConfig,TrainingTaskConfig
from app.core.models.model_factory import ModelFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


class TrainingHandler(BaseHandler):
    """Handler for training jobs"""
    
    async def execute(self, job: TrainingJob) -> Dict[str, Any]:
        """Execute training"""
        
        await self._mark_started(job.job_id)
        
        try:
            config = job.config
            task_config = job.config.task
            dataset_config = job.dataset_config
            model_config = job.train_model_config

            await self._update_progress(job.job_id, 10, "Loading dataset")
            
            # Load dataset
            df = pd.read_csv(dataset_config.dataset_path)
            
            await self._update_progress(job.job_id, 30, "Loading model")
            
            # Get model
            model = ModelFactory.get_model(model_config)
            
            await self._update_progress(job.job_id, 50, "Preparing data")

            dataset = DatasetFactory.get_dataset(dataset_config.dataset_type, dataset_config)
            task = TrainingTaskFactory.get_task(task_config)
            pipeline = TrainingPipeline(model, task, config)
            pipeline.setup(dataset)
            
            await self._update_progress(job.job_id, 70, "Training model")
            
            results = await pipeline.train()

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
            
            config.output_model_path = output_path
            job.metrics = result["metrics"]
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise