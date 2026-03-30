# app/core/pipeline_engine/handlers/base_handler.py

from abc import ABC, abstractmethod
from typing import Dict, Any
from uuid import UUID
import logging

from app.common.job_models import BaseJob
from app.api.websocket import manager

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """Base class for all job handlers"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    @abstractmethod
    async def execute(self, job: BaseJob) -> Dict[str, Any]:
        """Execute the job"""
        pass
    
    async def _update_progress(self, job_id: UUID, progress: float, message: str = None):
        """Update job progress"""
        job = self.orchestrator.get_job(job_id)
        if job:
            job.update_progress(progress)
            await manager.notify_job_update(str(job_id), {
                "status": job.status.value,
                "progress": progress,
                "message": message
            })
    
    async def _mark_started(self, job_id: UUID):
        """Mark job as started"""
        job = self.orchestrator.get_job(job_id)
        if job:
            job.mark_started()
            await manager.notify_job_update(str(job_id), {
                "status": "running",
                "progress": 0,
                "message": "Job started"
            })
    
    async def _mark_completed(self, job_id: UUID, result: Dict[str, Any]):
        """Mark job as completed"""
        job = self.orchestrator.get_job(job_id)
        if job:
            job.mark_completed(result)
            await manager.notify_job_update(str(job_id), {
                "status": "completed",
                "progress": 100,
                "result": result
            })
    
    async def _mark_failed(self, job_id: UUID, error: str):
        """Mark job as failed"""
        job = self.orchestrator.get_job(job_id)
        if job:
            job.mark_failed(error)
            await manager.notify_job_update(str(job_id), {
                "status": "failed",
                "error": error
            })