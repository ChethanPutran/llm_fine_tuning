# app/core/pipeline_engine/handlers/base_handler.py

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Any,Optional
import logging

from app.common.job_models import BaseJob
from app.api.websocket import manager


logger = logging.getLogger(__name__)


# Create a Type Variable that must be a subclass of BaseJob
T = TypeVar('T', bound=BaseJob)

class BaseHandler(ABC, Generic[T]):
    """Base class for all job handlers"""
    
    @abstractmethod
    async def execute(self, job: T) -> Dict[str, Any]:
        """Execute the job"""
        pass
    
    async def _update_progress(self, job: T, progress: float, message: Optional[str] = None):
        """Update job progress"""
        if job:
            if hasattr(job, "update_progress"):
                job.update_progress(progress)
            status = getattr(getattr(job, "status", None), "value", getattr(job, "status", "running"))
            job_id = getattr(job, "job_id", job)
            await manager.notify_job_update(str(job_id), {
                "status": status,
                "progress": progress,
                "message": message
            })
    
    async def _mark_started(self, job: T):
        """Mark job as started"""
        if job:
            if hasattr(job, "mark_started"):
                job.mark_started()
            job_id = getattr(job, "job_id", job)
            await manager.notify_job_update(str(job_id), {
                "status": "running",
                "progress": 0,
                "message": "Job started"
            })
    
    async def _mark_completed(self, job: T, result: Dict[str, Any]):
        """Mark job as completed"""
        if job:
            if hasattr(job, "mark_completed"):
                job.mark_completed(result)
            job_id = getattr(job, "job_id", job)
            await manager.notify_job_update(str(job_id), {
                "status": "completed",
                "progress": 100,
                "result": result
            })
    
    async def _mark_failed(self, job: T, error: str):
        """Mark job as failed"""
        if job:
            if hasattr(job, "mark_failed"):
                job.mark_failed(error)
            job_id = getattr(job, "job_id", job)
            await manager.notify_job_update(str(job_id), {
                "status": "failed",
                "error": error
            })
