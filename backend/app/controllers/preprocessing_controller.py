# app/controllers/preprocessing_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import os
import logging

from app.core.config import settings
from app.common.job_models import PreprocessingConfig, JobStatus, JobFactory
from app.controllers.base_controller import BaseController
from app.api.websocket import manager
from app.core.pipeline_engine.models import NodeType

logger = logging.getLogger(__name__)


class PreprocessingController(BaseController):
    """Controller for preprocessing operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def start_job(
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
            # Clear pipeline and build preprocessing pipeline
            self.orchestrator.clear_pipeline()
            
            # Set output path
            if not output_path:
                output_path = os.path.join(settings.DATA_STORAGE_PATH, "processed", str(uuid4()))
            
            self.orchestrator.add_node_to_pipeline(
                node_id="preprocessor",
                name="Data Preprocessing",
                node_type=NodeType.DATA_PROCESSING,
                config={
                    "input_path": input_path,
                    "output_path": output_path,
                    "config": config.model_dump()
                },
                resources={"cpu": 2, "memory_gb": 4},
                metadata={
                    "input_path": input_path,
                    "output_path": output_path
                }
            )
            
            # Create job using factory
            job = JobFactory.create_preprocessing_job(
                input_path=input_path,
                config=config.model_dump(),
                output_path=output_path,
                user_id=user_id,
                tags=tags or ["preprocessing"]
            )
            
            # Register job
            self._register_job(job.job_id, job)
            
            # Execute pipeline
            result = await self.orchestrator.execute_current_pipeline(user_id=user_id)
            
            # Link execution to job
            execution_id = result.get("execution_id")
            if execution_id:
                job.execution_id = execution_id
                job.mark_started()
                self._update_job(job.job_id, execution_id=execution_id)
            
            logger.info(f"Preprocessing job {job.job_id} started for {input_path}")
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_id) if execution_id else None,
                "status": "started",
                "output_path": output_path,
                "message": "Preprocessing job started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start preprocessing job: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get preprocessing job status"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return None
            
            return {
                "job_id": str(job.job_id),
                "job_type": job.job_type.value,
                "status": job.status.value if hasattr(job.status, 'value') else job.status,
                "progress": job.progress,
                "result": job.result,
                "error": job.error,
                "input_path": job.input_path,
                "output_path": job.output_path,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "user_id": job.user_id,
                "tags": job.tags,
                "metrics": job.metrics,
                "config": job.config
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return None
    
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
        result = self.orchestrator.list_jobs(
            job_type="data_processing",
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Add local jobs
        local_jobs = []
        for job in self._jobs.values():
            if status and job.status != status:
                continue
            if user_id and job.user_id != user_id:
                continue
            local_jobs.append(self._job_to_dict(job))
        
        # Combine and sort
        all_jobs = result.get("jobs", []) + local_jobs
        all_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        total = len(all_jobs)
        paginated_jobs = all_jobs[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": paginated_jobs
        }
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a preprocessing job"""
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
                    self._update_job(job.job_id, status=job.status, completed_at=job.completed_at)
                    await manager.notify_job_update(job_id, {
                        "status": "cancelled",
                        "message": "Job cancelled by user"
                    })
                    logger.info(f"Job {job_id} cancelled successfully")
                    return True
            
            return False
            
        except ValueError:
            return False