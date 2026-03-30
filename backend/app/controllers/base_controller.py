# app/controllers/base_controller.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from app.core.pipeline_engine.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)


class BaseController(ABC):
    """Base controller with common functionality"""
    
    def __init__(self, orchestrator:PipelineOrchestrator):
        self.orchestrator = orchestrator
        self._jobs: Dict[UUID, Any] = {}  # Use UUID as key
    
    @abstractmethod
    async def start_job(self, **kwargs) -> Dict[str, Any]:
        """
        Start a new job
        
        Args:
            **kwargs: Job-specific parameters
            
        Returns:
            Job information dictionary
        """
        pass
    
    @abstractmethod
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        pass
    
    @abstractmethod
    async def list_jobs(
        self, 
        status: Optional[str] = None, 
        limit: int = 50, 
        offset: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """List jobs with filters"""
        pass
    
    def _register_job(self, job_id: UUID, job: Any):
        """Register a job in memory"""
        self._jobs[job_id] = job
        logger.debug(f"Job {job_id} registered in controller")
    
    def _get_job(self, job_id: UUID) -> Optional[Any]:
        """Get a job by ID"""
        return self._jobs.get(job_id)
    
    def _update_job(self, job_id: UUID, **kwargs):
        """Update job attributes"""
        if job_id in self._jobs:
            for key, value in kwargs.items():
                if hasattr(self._jobs[job_id], key):
                    setattr(self._jobs[job_id], key, value)
            logger.debug(f"Job {job_id} updated")
    
    def _job_to_dict(self, job: Any) -> Dict[str, Any]:
        """Convert job to dictionary for listing"""
        return {
            "job_id": str(job.job_id),
            "job_type": job.job_type.value if hasattr(job, 'job_type') else None,
            "status": job.status.value if hasattr(job.status, 'value') else job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat() if hasattr(job, 'created_at') else None,
            "started_at": job.started_at.isoformat() if hasattr(job, 'started_at') and job.started_at else None,
            "completed_at": job.completed_at.isoformat() if hasattr(job, 'completed_at') and job.completed_at else None,
            "user_id": getattr(job, 'user_id', None),
            "tags": getattr(job, 'tags', [])
        }