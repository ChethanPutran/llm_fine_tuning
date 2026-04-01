import asyncio
from typing import Optional, List, Dict, Any
from uuid import UUID
from queue import PriorityQueue
from ...common.job_models import BaseJob, JobStatus

class JobQueue:
    """
    Thread-safe job queue with priority support
    Implements Singleton pattern for global queue access
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._queue = PriorityQueue()
        self._job_status: Dict[UUID, BaseJob] = {}
        self._lock = asyncio.Lock()
    
    async def enqueue(self, job: BaseJob) -> None:
        """Add job to queue"""
        async with self._lock:
            job.status = JobStatus.QUEUED
            self._job_status[job.job_id] = job
            # PriorityQueue uses tuple (priority, job) where lower priority number = higher priority
            self._queue.put((job.priority.value, job.job_id))
    
    async def dequeue(self) -> Optional[BaseJob]:
        """Get next job from queue"""
        try:
            _, job_id = self._queue.get_nowait()
            async with self._lock:
                job = self._job_status.get(job_id)
                if job:
                    job.status = JobStatus.RUNNING
                return job
        except:
            return None
    
    async def get_job_status(self, job_id: UUID) -> Optional[BaseJob]:
        """Get status of a specific job"""
        async with self._lock:
            return self._job_status.get(job_id)
    
    async def update_job_status(self, job_id: UUID, status: JobStatus, error: str = '') -> None:
        """Update job status"""
        async with self._lock:
            if job_id in self._job_status:
                self._job_status[job_id].status = status
                if error:
                    self._job_status[job_id].error = error
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        return self._queue.qsize()
    
    async def cancel_job(self, job_id: UUID) -> bool:
        """Cancel a pending or queued job"""
        async with self._lock:
            if job_id in self._job_status:
                job = self._job_status[job_id]
                if job.status in [JobStatus.PENDING, JobStatus.QUEUED]:
                    job.status = JobStatus.CANCELLED
                    return True
        return False
    
    async def list_jobs(self, status: Optional[JobStatus] = None) -> List[BaseJob]:
        """List all jobs, optionally filtered by status"""
        async with self._lock:
            jobs = list(self._job_status.values())
            if status:
                jobs = [job for job in jobs if job.status == status]
            return sorted(jobs, key=lambda j: j.created_at, reverse=True)