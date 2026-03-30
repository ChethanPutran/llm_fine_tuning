# app/controllers/training_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging

from app.common.job_models import TrainingJob, FinetuningJob, JobStatus, JobFactory
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType

logger = logging.getLogger(__name__)


class TrainingController(BaseController):
    """Controller for training and fine-tuning operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)

    async def start_job(
        self,
        *,
        model_type: str,
        model_name: str,
        dataset_path: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Start a training job"""
        
        try:
            # Clear pipeline and build training pipeline
            self.orchestrator.clear_pipeline()
            
            self.orchestrator.add_node_to_pipeline(
                node_id="trainer",
                name=f"Train {model_name}",
                node_type=NodeType.MODEL_TRAINING,
                config={
                    "model_type": model_type,
                    "model_name": model_name,
                    "dataset_path": dataset_path,
                    "training_config": config
                },
                resources={"cpu": 4, "memory_gb": 16, "gpu": 1}
            )
            
            # Create job
            job = JobFactory.create_training_job(
                model_type=model_type,
                model_name=model_name,
                dataset_path=dataset_path,
                config=config,
                user_id=user_id,
                tags=tags or ["training"]
            )
            
            self._register_job(job.job_id, job)
            
            # Execute pipeline
            result = await self.orchestrator.execute_current_pipeline(user_id=user_id)
            
            # Link execution
            execution_id = result.get("execution_id")
            if execution_id:
                job.execution_id = execution_id
                job.mark_started()
                self._update_job(job.job_id, execution_id=execution_id)
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_id) if execution_id else None,
                "status": "started",
                "message": f"Training job started for {model_name}"
            }
            
        except Exception as e:
            logger.error(f"Failed to start training job: {e}")
            raise

    async def start_finetuning(
        self,
        base_model_type: str,
        base_model_name: str,
        strategy_type: str,
        task_type: str,
        dataset_path: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs

    ) -> Dict[str, Any]:
        """Start a fine-tuning job"""
        
        try:
            # Clear pipeline and build fine-tuning pipeline
            self.orchestrator.clear_pipeline()
            
            self.orchestrator.add_node_to_pipeline(
                node_id="finetuner",
                name=f"Fine-tune {base_model_name}",
                node_type=NodeType.MODEL_FINETUNING,
                config={
                    "base_model_type": base_model_type,
                    "base_model_name": base_model_name,
                    "strategy_type": strategy_type,
                    "task_type": task_type,
                    "dataset_path": dataset_path,
                    "finetuning_config": config
                },
                resources={"cpu": 4, "memory_gb": 16, "gpu": 1}
            )
            
            # Create job
            job = JobFactory.create_finetuning_job(
                base_model_type=base_model_type,
                base_model_name=base_model_name,
                strategy_type=strategy_type,
                task_type=task_type,
                dataset_path=dataset_path,
                config=config,
                user_id=user_id,
                tags=tags or ["finetuning", strategy_type]
            )
            
            self._register_job(job.job_id, job)
            
            # Execute pipeline
            result = await self.orchestrator.execute_current_pipeline(user_id=user_id)
            
            # Link execution
            execution_id = result.get("execution_id")
            if execution_id:
                job.execution_id = execution_id
                job.mark_started()
                self._update_job(job.job_id, execution_id=execution_id)
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_id) if execution_id else None,
                "status": "started",
                "message": f"Fine-tuning job started for {base_model_name} with {strategy_type}"
            }
            
        except Exception as e:
            logger.error(f"Failed to start fine-tuning job: {e}")
            raise

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get training job status"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return None
            
            response = {
                "job_id": str(job.job_id),
                "job_type": job.job_type.value,
                "status": job.status.value if hasattr(job.status, 'value') else job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "user_id": job.user_id,
                "tags": job.tags
            }
            
            # Add type-specific fields
            if isinstance(job, TrainingJob):
                response.update({
                    "model_type": job.model_type,
                    "model_name": job.model_name,
                    "dataset_path": job.dataset_path,
                    "model_path": job.model_path,
                    "metrics": job.metrics
                })
            elif isinstance(job, FinetuningJob):
                response.update({
                    "base_model_type": job.base_model_type,
                    "base_model_name": job.base_model_name,
                    "strategy_type": job.strategy_type,
                    "task_type": job.task_type,
                    "dataset_path": job.dataset_path,
                    "output_path": job.output_path,
                    "metrics": job.metrics,
                    "trainable_params": job.trainable_params
                })
            
            if job.error:
                response["error"] = job.error
            
            if job.result:
                response["result"] = job.result
            
            return response
            
        except ValueError:
            return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a training job"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return False
            
            if job.status not in [JobStatus.RUNNING, JobStatus.QUEUED, JobStatus.PENDING]:
                return False
            
            if job.execution_id:
                cancelled = await self.orchestrator.cancel_execution(job.execution_id)
                if cancelled:
                    job.mark_cancelled()
                    self._update_job(job.job_id, status=job.status)
                    return True
            
            return False
            
        except ValueError:
            return False

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

    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get training job statistics"""
        stats = await self.orchestrator.get_statistics(user_id=user_id)
        return stats

    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        job_type: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """List training jobs"""
        
        # Get from orchestrator
        result = self.orchestrator.list_jobs(
            job_type=job_type,
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return result