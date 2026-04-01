import asyncio
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from .job_queue import JobQueue
from ...common.job_models import BaseJob, JobPriority, JobType, JobStatus
from .worker import Worker
from .resource_manager import ResourceManager
from ..pipeline_engine.models import PipelineNode

class AsyncExecutor:
    """
    Async job execution wrapper with worker pool management
    Implements the Facade pattern for the execution layer
    """
    
    def __init__(self, pipeline_executor, resource_manager, num_workers: int = 4):
        self.pipeline_executor = pipeline_executor
        self.job_queue = JobQueue()
        self.resource_manager = resource_manager
        self.workers: List[Worker] = []
        self._worker_tasks: List[asyncio.Task] = []
        
        # Create workers
        for i in range(num_workers):
            worker = Worker(f"worker-{i}", pipeline_executor, self.job_queue, self.resource_manager)

            self.workers.append(worker)
            
    async def get_queued_jobs(self) -> List[Dict[str, Any]]:
        """Get list of queued jobs"""
        jobs = await self.job_queue.list_jobs(JobStatus.QUEUED)
        return [job.to_dict() for job in jobs]
    
    async def start(self):
        """Start all workers"""
        for worker in self.workers:
            await worker.start()
    
    async def stop(self):
        """Stop all workers"""
        for worker in self.workers:
            await worker.stop()
    
    async def submit_job(
        self,
        node: PipelineNode,
        pipeline_id: UUID,
        execution_id: UUID,
        priority: JobPriority = JobPriority.NORMAL
    ) -> UUID:
        """Submit a job for execution"""
        
        # Map node type to job type
        job_type = self._map_node_type_to_job_type(node.type)
        
        job = BaseJob(
            priority=priority,
            job_type=job_type,
            pipeline_id=pipeline_id,
            node_id=node.id,
            execution_id=execution_id,
            metadata={
                "node_config": node.config.parameters,
                "resource_requirements": node.config.resources
            },
            max_retries=node.config.retry_policy.get("max_retries", 3)
        )
        
        # Add to queue
        await self.job_queue.enqueue(job)
        
        return job.job_id
    
    def _map_node_type_to_job_type(self, node_type) -> JobType:
        """Map pipeline node type to job type"""
        mapping = {
            "data_ingestion": JobType.DATA_PROCESSING,
            "data_processing": JobType.DATA_PROCESSING,
            "model_training": JobType.TRAINING,
            "model_evaluation": JobType.EVALUATION,
            "model_deployment": JobType.DEPLOYMENT
        }
        return mapping.get(node_type.value, JobType.DATA_PROCESSING)
    
    async def get_job_status(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        job = await self.job_queue.get_job_status(job_id)
        return job.to_dict() if job else None
    
    async def cancel_job(self, job_id: UUID) -> bool:
        """Cancel a pending or queued job"""
        return await self.job_queue.cancel_job(job_id)
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_size": await self.job_queue.get_queue_size(),
            "resources": await self.resource_manager.get_resource_utilization(),
            "jobs_by_status": {
                status.value: len([j for j in await self.job_queue.list_jobs(status)])
                for status in JobStatus
            }
        }
    
    async def list_jobs(self, status: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        """List all jobs"""
        jobs = await self.job_queue.list_jobs(status)
        return [job.to_dict() for job in jobs]