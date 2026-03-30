import asyncio
import logging
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, timezone
import traceback

from .job_queue import JobQueue
from .resource_manager import ResourceManager
from ...common.job_models import BaseJob, JobStatus

if TYPE_CHECKING:
    from ..pipeline_engine.executor import PipelineExecutor

logger = logging.getLogger(__name__)

class Worker:
    """
    Worker that processes jobs from the queue
    Implements Command pattern for job execution
    """
    def __init__(self, worker_id: str, executor: 'PipelineExecutor', job_queue: JobQueue, resource_manager: ResourceManager):
        self.worker_id = worker_id
        self.executor = executor
        self.job_queue = job_queue
        self.resource_manager = resource_manager
        self._running = False
        self._current_job: Optional[BaseJob] = None
        self._current_job_future: Optional[asyncio.Future] = None
        self._task: Optional[asyncio.Task] = None
        self._handlers: Dict[str, Callable] = {}
        self._metrics = {
            "jobs_processed": 0,
            "jobs_failed": 0,
            "total_processing_time": 0.0
        }
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register handler for specific job type"""
        self._handlers[job_type] = handler
        logger.debug(f"Registered handler for job type: {job_type}")
    
    async def start(self):
        """Start the worker"""
        if self._running:
            logger.warning(f"Worker {self.worker_id} already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._work_loop())
        logger.info(f"Worker {self.worker_id} started")
    
    async def stop(self, graceful: bool = True):
        """
        Stop the worker
        
        Args:
            graceful: If True, wait for current job to complete before stopping
        """
        self._running = False
        
        if graceful and self._current_job:
            logger.info(f"Waiting for job {self._current_job.job_id} to complete...")
            if self._current_job_future:
                try:
                    await asyncio.wait_for(self._current_job_future, timeout=30)
                except asyncio.TimeoutError:
                    logger.warning(f"Job {self._current_job.job_id} did not complete in time")
                    await self._cancel_current_job()
        elif self._current_job:
            await self._cancel_current_job()
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    async def _work_loop(self):
        """Main worker loop"""
        while self._running:
            try:
                # Get next job from queue (with timeout)
                job = await self.job_queue.dequeue()
                
                if job is None:
                    await asyncio.sleep(1)
                    continue
                
                self._current_job = job
                self._current_job_future = asyncio.Future()
                
                # Check if resources are available
                resource_requirements = job.metadata.get("resource_requirements", {
                    "cpu": 1,
                    "memory_gb": 2,  # Changed from "memory" to be more explicit
                    "gpu": 0
                })
                
                if not await self.resource_manager.can_schedule(resource_requirements):
                    logger.debug(f"Insufficient resources for job {job.job_id}, requeuing")
                    await self.job_queue.enqueue(job)
                    await asyncio.sleep(5)
                    continue
                
                # Allocate resources
                allocated = await self.resource_manager.allocate_resources(
                    str(job.job_id),
                    resource_requirements
                )
                
                if not allocated:
                    logger.warning(f"Failed to allocate resources for job {job.job_id}")
                    await self.job_queue.enqueue(job)
                    await asyncio.sleep(5)
                    continue
                
                # Execute job
                try:
                    start_time = datetime.now(timezone.utc)
                    await self._execute_job(job)
                    self._metrics["jobs_processed"] += 1
                    self._metrics["total_processing_time"] += (datetime.now(timezone.utc) - start_time).total_seconds()
                    
                    # Update job status
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(timezone.utc)
                    await self.job_queue.update_job_status(job.job_id, JobStatus.COMPLETED)
                    
                    self._current_job_future.set_result(True)
                    
                except asyncio.CancelledError:
                    logger.info(f"Job {job.job_id} was cancelled")
                    job.status = JobStatus.CANCELLED
                    await self.job_queue.update_job_status(job.job_id, JobStatus.CANCELLED)
                    self._current_job_future.set_exception(asyncio.CancelledError())
                    raise
                    
                except Exception as e:
                    self._metrics["jobs_failed"] += 1
                    logger.error(f"Job {job.job_id} failed: {e}")
                    await self._handle_job_failure(job, e)
                    self._current_job_future.set_exception(e)
                    
                finally:
                    # Release resources
                    await self.resource_manager.release_resources(str(job.job_id))
                    self._current_job = None
                    self._current_job_future = None
                
            except asyncio.CancelledError:
                logger.info(f"Worker {self.worker_id} work loop cancelled")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}\n{traceback.format_exc()}")
                await asyncio.sleep(1)
    
    async def _execute_job(self, job: BaseJob):
        """Execute a job with timeout and progress tracking"""
        job.started_at = datetime.now(timezone.utc)
        
        # Find handler for job type
        handler = self._handlers.get(job.job_type.value)
        
        if not handler:
            raise ValueError(f"No handler registered for job type: {job.job_type}")
        
        # Get timeout from job metadata (default 1 hour)
        timeout = job.metadata.get("timeout_seconds", 3600)
        
        try:
            # Execute handler with timeout
            result = await asyncio.wait_for(handler(job), timeout=timeout)
            
            # Update pipeline state through executor
            await self.executor._emit_event(
                await self.executor._get_event_type(job.job_type.value, action="complete"),
                {
                    "job_id": str(job.job_id),
                    "pipeline_id": str(job.pipeline_id) if job.pipeline_id else None,
                    "execution_id": str(job.execution_id) if job.execution_id else None,
                    "node_id": job.node_id,
                    "result": result,
                    "worker_id": self.worker_id
                }
            )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Job {job.job_id} timed out after {timeout} seconds")
            raise TimeoutError(f"Job execution timed out after {timeout}s")
    
    async def _handle_job_failure(self, job: BaseJob, error: Exception):
        """Handle job failure with retry logic"""
        # Get retry configuration from job metadata
        max_retries = job.metadata.get("max_retries", 3)
        retry_count = job.metadata.get("retry_count", 0)
        
        # Emit failure event first
        await self.executor._emit_event(
            await self.executor._get_event_type(job.job_type.value, action="fail", failed=True),
            {
                "job_id": str(job.job_id),
                "pipeline_id": str(job.pipeline_id) if job.pipeline_id else None,
                "execution_id": str(job.execution_id) if job.execution_id else None,
                "node_id": job.node_id,
                "error": str(error),
                "retry_count": retry_count,
                "max_retries": max_retries
            }
        )
        
        # Check if retry is possible
        if retry_count < max_retries:
            job.metadata["retry_count"] = retry_count + 1
            job.status = JobStatus.RETRYING
            job.error = str(error)
            
            # Calculate exponential backoff with jitter
            backoff_seconds = min(2 ** retry_count, 60)  # Cap at 60 seconds
            import random
            jitter = random.uniform(0, 0.1 * backoff_seconds)
            wait_time = backoff_seconds + jitter
            
            logger.info(f"Job {job.job_id} failed, retrying in {wait_time:.2f}s (attempt {retry_count + 1}/{max_retries})")
            
            await asyncio.sleep(wait_time)
            await self.job_queue.enqueue(job)
            
        else:
            job.status = JobStatus.FAILED
            job.error = str(error)
            job.completed_at = datetime.now(timezone.utc)
            logger.error(f"Job {job.job_id} failed permanently after {max_retries} attempts: {error}")
            
            # Log traceback for debugging
            logger.debug(f"Job {job.job_id} failure traceback:\n{traceback.format_exc()}")
    
    async def _cancel_current_job(self):
        """Cancel currently running job"""
        if self._current_job:
            logger.info(f"Cancelling job {self._current_job.job_id}")
            
            # Update job status
            self._current_job.status = JobStatus.CANCELLED
            self._current_job.completed_at = datetime.now(timezone.utc)
            await self.job_queue.update_job_status(self._current_job.job_id, JobStatus.CANCELLED)
            
            # Emit cancellation event
            await self.executor._emit_event(
                await self.executor._get_event_type(self._current_job.job_type.value, action="cancel", failed=True),
                {
                    "job_id": str(self._current_job.job_id),
                    "pipeline_id": str(self._current_job.pipeline_id) if self._current_job.pipeline_id else None,
                    "execution_id": str(self._current_job.execution_id) if self._current_job.execution_id else None,
                    "node_id": self._current_job.node_id,
                    "message": "Job cancelled by worker shutdown"
                }
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get worker metrics"""
        return {
            "worker_id": self.worker_id,
            "running": self._running,
            "current_job": str(self._current_job.job_id) if self._current_job else None,
            "jobs_processed": self._metrics["jobs_processed"],
            "jobs_failed": self._metrics["jobs_failed"],
            "avg_processing_time": self._metrics["total_processing_time"] / self._metrics["jobs_processed"] 
                if self._metrics["jobs_processed"] > 0 else 0,
            "registered_handlers": list(self._handlers.keys())
        }
    
    async def health_check(self) -> bool:
        """Check if worker is healthy"""
        try:
            # Check if worker is running
            if not self._running:
                return False
            
            # Check if task is alive
            if self._task and self._task.done():
                return False
            
            # Check resource manager
            await self.resource_manager.health_check()
            
            return True
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id} health check failed: {e}")
            return False