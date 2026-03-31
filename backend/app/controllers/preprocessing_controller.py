# app/controllers/preprocessing_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import os
import logging

from app.core.config import settings
from app.common.job_models import PreprocessingConfig, JobStatus, JobFactory, JobPriority
from app.controllers.base_controller import BaseController
from app.api.websocket import manager
from app.core.pipeline_engine.models import NodeType

logger = logging.getLogger(__name__)


class PreprocessingController(BaseController):
    """Controller for preprocessing operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def add_job(
        self,
        *,
        input_path: str,
        config: PreprocessingConfig,
        output_path: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a preprocessing job
        
        Args:
            input_path: Path to input data
            config: Preprocessing configuration
            output_path: Optional output path
            user_id: User ID
            tags: Optional tags for categorization
        
        Returns:
            Job information
        """
        # Validate input path
        if not os.path.exists(input_path):
            raise ValueError(f"Input path not found: {input_path}")
        
        try:
            config_dict = config.model_dump() if hasattr(config, 'model_dump') else config
            config_dict = config_dict or {}
            
            # Set output path
            if not output_path:
                output_path = os.path.join(settings.DATA_STORAGE_PATH, "processed", str(uuid4()))
            
            metadata = {
                "node_id": "preprocessor",
                "name": f"Preprocess {os.path.basename(input_path)}",
                "node_type": NodeType.DATA_PROCESSING,
                "resources": {"cpu": 2, "memory_gb": 4},
                "metadata": {
                    "input_path": input_path,
                    "output_path": output_path,
                    "config": config_dict
                },
                "retry_policy": config_dict.get("retry_policy", {"retries": 3, "delay_seconds": 5}),
                "position": config_dict.get("position", (0, 0))
            }
            
            # Create job using factory
            job = JobFactory.create_preprocessing_job(
                input_path=input_path,
                config=config_dict,
                output_path=output_path,
                user_id=user_id,
                tags=tags or ["preprocessing"]
            )
            
            # Register job with orchestrator
            self.orchestrator.register_job(job, metadata)
            
            return {
                "job_id": str(job.job_id),
                "message": "Preprocessing job created successfully",
            }
            
        except Exception as e:
            logger.error(f"Failed to start preprocessing job: {e}")
            raise
    
    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a registered preprocessing job
        
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
        """Get preprocessing job status"""
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
            
            return {
                "job_id": str(job.job_id),
                "job_type": job.job_type.value,
                "execution_id": str(job.execution_id) if job.execution_id else None,
                "status": job.status.value if hasattr(job.status, 'value') else job.status,
                "progress": job.progress,
                "result": job.result,
                "error": job.error,
                "input_path": job.input_path,
                "output_path": job.output_path,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "updated_at": job.updated_at.isoformat(),
                "user_id": job.user_id,
                "tags": job.tags,
                "metrics": job.metrics,
                "config": job.config,
                "execution_details": execution_status
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a preprocessing job"""
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
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """List preprocessing jobs"""
        
        # Get from orchestrator
        orchestrator_jobs = self.orchestrator.list_jobs(
            job_type="data_processing",
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
                # Create job object from dict
                from app.common.job_models import PreprocessingJob
                job = PreprocessingJob(
                    job_id=job_id,
                    input_path=job_dict.get("input_path", ""),
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
        """Get preprocessing statistics"""
        jobs_list = list(self._jobs.values())
        
        if user_id:
            jobs_list = [j for j in jobs_list if j.user_id == user_id]
        
        # Count by status
        status_counts = {}
        for status in JobStatus:
            count = len([j for j in jobs_list if j.status == status])
            if count > 0:
                status_counts[status.value] = count
        
        # Calculate total data processed
        total_processed = sum(j.metrics.get("records_processed", 0) if j.metrics else 0 for j in jobs_list)
        
        return {
            "total_jobs": len(jobs_list),
            "by_status": status_counts,
            "completed_jobs": len([j for j in jobs_list if j.status == JobStatus.COMPLETED]),
            "failed_jobs": len([j for j in jobs_list if j.status == JobStatus.FAILED]),
            "total_records_processed": total_processed
        }