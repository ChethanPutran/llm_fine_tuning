# app/controllers/training_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging

from app.common.job_models import  JobFactory
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType
from app.api.websocket import manager
from app.common.job_models import TrainingConfig, ModelConfig, DatasetConfig, FinetuningConfig

logger = logging.getLogger(__name__)


class TrainingController(BaseController):
    """Controller for training and fine-tuning operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)

    async def add_job(
        self,
        *,
        model_config: ModelConfig,
        dataset_config: DatasetConfig,
        config: TrainingConfig,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_execute: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Start a training job"""
        
        try:
            config = config or {}
            
            # Create job
            job = JobFactory.create_training_job(
                dataset_config=dataset_config,
                model_config=model_config,
                training_config=config)
            
            metadata = JobFactory.create_job_metadata(
                name=f"Train {model_config.model_name}", 
                node_type=NodeType.MODEL_TRAINING,
                job=job,
                description=f"Training model {model_config.model_name} on dataset {dataset_config.dataset_path}",    
                config=config.dict(),
                tags=tags or ["training"]
            )
            # Register job with orchestrator
            return await self.register(job, metadata, message="Training job created successfully", auto_execute=auto_execute)
            
        except Exception as e:
            logger.error(f"Failed to start training job: {e}")
            raise

    async def add_finetuning_job(
        self,
        base_model_config: ModelConfig,
        dataset_config: DatasetConfig,
        config: FinetuningConfig,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
            auto_execute: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Start a fine-tuning job"""
        
        try:
            config = config or {}
            
            
            # Create job
            job = JobFactory.create_finetuning_job(
                base_model_config=base_model_config,
                dataset_config=dataset_config,
                finetune_config=config,
                **kwargs
            )
            
            metadata = JobFactory.create_job_metadata(
                name=f"Fine-tune {base_model_config.model_name}", 
                node_type=NodeType.MODEL_FINETUNING,
                job=job,
                description=f"Fine-tuning model {base_model_config.model_name} on dataset {dataset_config.dataset_path} with strategy {config.strategy_type}",    
                config=config.dict(),
                tags=tags or ["fine-tuning"]
            )
            # Register job with orchestrator
            return await self.register(job, metadata, message="Fine-tuning job created successfully", auto_execute=auto_execute)
            
        except Exception as e:
            logger.error(f"Failed to start fine-tuning job: {e}")
            raise

    async def get_job_metrics(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get training job metrics"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return None
            
            return job.metrics
        
        except ValueError:
            return None
    
    async def get_job_logs(self, job_id: str) -> Optional[List[str]]:
        """Get training job logs"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return None
            
            if job.execution_id:
                logs = await self.orchestrator.get_execution_logs(job.execution_id)
                return logs
            
            return None
        
        except ValueError:
            return None

   