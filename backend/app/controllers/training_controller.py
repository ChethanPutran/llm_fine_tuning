# app/controllers/training_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from datetime import datetime

from app.common.job_models import TrainingJob, FinetuningJob, JobStatus, JobFactory, JobPriority
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType
from app.api.websocket import manager

logger = logging.getLogger(__name__)


class TrainingController(BaseController):
    """Controller for training and fine-tuning operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)

    async def add_job(
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
            config = config or {}
            metadata = {
                "node_id": "trainer",
                "name": f"Train {model_name}",
                "node_type": NodeType.MODEL_TRAINING,
                "resources": {"cpu": 4, "memory_gb": 16, "gpu": config.get("use_gpu", 1)},
                "metadata": {
                    "model_type": model_type,
                    "model_name": model_name,
                    "dataset_path": dataset_path,
                    "training_config": config
                },
                "retry_policy": config.get("retry_policy", {"retries": 3, "delay_seconds": 5}),
                "position": config.get("position", (0, 0))
            }
            
            # Create job
            job = JobFactory.create_training_job(
                model_type=model_type,
                model_name=model_name,
                dataset_path=dataset_path,
                config=config,
                user_id=user_id,
                tags=tags or ["training"]
            )
            
            # Register job with orchestrator
            self.orchestrator.register_job(job, metadata)
            
            return {
                "job_id": str(job.job_id),
                "message": "Training job created successfully",
            }
            
        except Exception as e:
            logger.error(f"Failed to start training job: {e}")
            raise

    async def add_finetuning_job(
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
            config = config or {}
            metadata = {
                "node_id": "finetuner",
                "name": f"Fine-tune {base_model_name}",
                "node_type": NodeType.MODEL_FINETUNING,
                "resources": {"cpu": 4, "memory_gb": 16, "gpu": config.get("use_gpu", 1)},
                "metadata": {
                    "base_model_type": base_model_type,
                    "base_model_name": base_model_name,
                    "strategy_type": strategy_type,
                    "task_type": task_type,
                    "dataset_path": dataset_path,
                    "finetuning_config": config
                },
                "retry_policy": config.get("retry_policy", {"retries": 3, "delay_seconds": 5}),
                "position": config.get("position", (0, 0))
            }
            
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
            
            # Register job with orchestrator
            self.orchestrator.register_job(job, metadata)
            
            return {
                "job_id": str(job.job_id),
                "message": "Fine-tuning job created successfully",
            }
            
        except Exception as e:
            logger.error(f"Failed to start fine-tuning job: {e}")
            raise

    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a registered training job
        
        Args:
            job_id: Job ID to execute
        
        Returns:
            Execution result information
        """
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                logger.error(f"Job {job_id} not found for execution")
                return {"error": "Job not found"}
            
            # Execute the job using orchestrator
            execution_result = await self.orchestrator.execute_job(job.job_id)
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_result.get("execution_id", "")),
                "message": "Job execution started successfully"
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return {"error": "Invalid job ID"}
        except Exception as e:
            logger.error(f"Failed to execute job: {e}")
            return {"error": "Failed to execute job"}

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get training job status"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return None
            
            # Get execution status if execution exists
            execution_status = None
            if job.execution_id:
                execution_status = await self.orchestrator.get_execution_status(job.execution_id)
            
            response = {
                "job_id": str(job.job_id),
                "job_type": job.job_type.value,
                "execution_id": str(job.execution_id) if job.execution_id else None,
                "status": job.status.value if hasattr(job.status, 'value') else job.status,
                "progress": job.progress,
                "result": job.result,
                "error": job.error,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "updated_at": job.updated_at.isoformat(),
                "user_id": job.user_id,
                "tags": job.tags,
                "execution_details": execution_status
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
            
            return response
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
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
            
            # Check if job can be cancelled
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                logger.warning(f"Job {job_id} cannot be cancelled in status {job.status}")
                return False
            
            if job.execution_id:
                cancelled = await self.orchestrator.cancel_execution(job.execution_id)
                if cancelled:
                    job.mark_cancelled()
                    self._update_job(job.job_id, status=job.status, completed_at=job.completed_at)
                    await manager.notify_job_update(job_id, {
                        "status": "cancelled",
                        "message": "Job cancelled by user"
                    })
                    logger.info(f"Job {job_id} cancelled successfully")
                    return True
            else:
                # Job hasn't started execution yet
                job.mark_cancelled()
                self._update_job(job.job_id, status=job.status, completed_at=job.completed_at)
                await manager.notify_job_update(job_id, {
                    "status": "cancelled",
                    "message": "Job cancelled before execution"
                })
                logger.info(f"Job {job_id} cancelled before execution")
                return True
            
            return False
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
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
        orchestrator_jobs = self.orchestrator.list_jobs(
            job_type=job_type,
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Combine with local jobs
        jobs_list = list(self._jobs.values())
        
        # Add orchestrator jobs
        for job_dict in orchestrator_jobs.get("jobs", []):
            job_id = UUID(job_dict["job_id"])
            if job_id not in self._jobs:
                # Determine job type and create appropriate job object
                if job_dict.get("job_type") == "training":
                    job = TrainingJob(
                        job_id=job_id,
                        model_type=job_dict.get("model_type", ""),
                        model_name=job_dict.get("model_name", ""),
                        dataset_path=job_dict.get("dataset_path", ""),
                        status=JobStatus(job_dict["status"]),
                        progress=job_dict.get("progress", 0),
                        created_at=datetime.fromisoformat(job_dict["created_at"])
                    )
                else:
                    job = FinetuningJob(
                        job_id=job_id,
                        base_model_type=job_dict.get("base_model_type", ""),
                        base_model_name=job_dict.get("base_model_name", ""),
                        strategy_type=job_dict.get("strategy_type", ""),
                        task_type=job_dict.get("task_type", ""),
                        dataset_path=job_dict.get("dataset_path", ""),
                        status=JobStatus(job_dict["status"]),
                        progress=job_dict.get("progress", 0),
                        created_at=datetime.fromisoformat(job_dict["created_at"])
                    )
                jobs_list.append(job)
        
        # Sort by creation time (newest first)
        jobs_list.sort(key=lambda x: x.created_at, reverse=True)
        
        total = len(jobs_list)
        paginated_jobs = jobs_list[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [self._job_to_dict(job) for job in paginated_jobs]
        }

    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get training job statistics"""
        jobs_list = list(self._jobs.values())
        
        if user_id:
            jobs_list = [j for j in jobs_list if j.user_id == user_id]
        
        # Count by status
        status_counts = {}
        for status in JobStatus:
            count = len([j for j in jobs_list if j.status == status])
            if count > 0:
                status_counts[status.value] = count
        
        # Separate training and fine-tuning
        training_jobs = [j for j in jobs_list if isinstance(j, TrainingJob)]
        finetuning_jobs = [j for j in jobs_list if isinstance(j, FinetuningJob)]
        
        return {
            "total_jobs": len(jobs_list),
            "by_status": status_counts,
            "training_jobs": len(training_jobs),
            "finetuning_jobs": len(finetuning_jobs),
            "completed_jobs": len([j for j in jobs_list if j.status == JobStatus.COMPLETED]),
            "failed_jobs": len([j for j in jobs_list if j.status == JobStatus.FAILED]),
            "running_jobs": len([j for j in jobs_list if j.status == JobStatus.RUNNING])
        }