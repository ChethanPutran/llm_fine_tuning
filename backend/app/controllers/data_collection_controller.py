# app/controllers/data_collection_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging
from datetime import datetime, timezone

from app.common.job_models import DataCollectionJob, JobStatus, JobFactory, JobPriority
from app.controllers.base_controller import BaseController
from app.api.websocket import manager
from app.core.pipeline_engine.models import NodeType

logger = logging.getLogger(__name__)


class DataCollectionController(BaseController):
    """Controller for data collection operations"""
    def __init__(self, orchestrator):
        super().__init__(orchestrator)

    async def add_job(
        self,
        *,
        source: str,
        topic: str,
        search_engine: str = "google",
        limit: int = 100,
        config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a new data collection job
        
        Args:
            source: Data source (web, books, etc.)
            topic: Topic to collect
            search_engine: Search engine for web crawling
            limit: Maximum number of documents
            config: Additional configuration
            user_id: User ID
            tags: Optional tags for categorization
            **kwargs: Additional keyword arguments
        """
        
        try:
            config = config or {}
            metadata = {
            "node_id": "data_collector",
            "name": f"Collect {topic} from {source}",
            "node_type": NodeType.DATA_INGESTION,
            "resources": {"cpu": 1, "memory_gb": 2},
            "metadata": {
                "source": source,
                "topic": topic,
                "search_engine": search_engine,
                "limit": limit,
                "crawler_config": config.get('crawler_config', {}),
                "job_type": "data_collection"
            },
            "retry_policy": config.get("retry_policy", {"retries": 3, "delay_seconds": 5}),
            "position": config.get("position", (0,0))
            }
        
            # Create data collection job
            job = JobFactory.create_data_collection_job(
                source=source,
                topic=topic,
                search_engine=search_engine,
                limit=limit,
                config=config or {},
                user_id=user_id,
                tags=tags or ["data_collection"]
            )

            # Register job with orchestrator
            self.orchestrator.register_job(job, metadata)
            
            return {
                "job_id": str(job.job_id),
                "message": "Data collection job created successfully",
            }
            
        except Exception as e:
            logger.error(f"Failed to start data collection job: {e}")
            raise
    
    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a registered data collection job
        
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
        """
        Get status of a data collection job
        
        Args:
            job_id: Job ID
        
        Returns:
            Job status information
        """
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                # Try to get from orchestrator
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
                "documents_count": len(job.documents) if job.documents else 0,
                "source": job.source,
                "topic": job.topic,
                "search_engine": job.search_engine,
                "limit": job.limit,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "updated_at": job.updated_at.isoformat(),
                "user_id": job.user_id,
                "tags": job.tags,
                "execution_details": execution_status
            }
            
        except ValueError as e:
            logger.error(f"Invalid job ID: {job_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running data collection job
        
        Args:
            job_id: Job ID
        
        Returns:
            True if cancelled successfully
        """
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    logger.warning(f"Job {job_id} not found")
                    return False
            
            # Check if job can be cancelled
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                logger.warning(f"Job {job_id} cannot be cancelled in status {job.status}")
                return False
            
            # Cancel execution if running
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
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            return False

    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        source: Optional[str] = None,
        topic: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        List data collection jobs with filters
        
        Args:
            status: Filter by status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            source: Filter by data source
            topic: Filter by topic
            user_id: Filter by user ID
        
        Returns:
            Dictionary with total count and list of jobs
        """
        # Get all jobs from orchestrator
        orchestrator_jobs = self.orchestrator.list_jobs(
            job_type="data_collection",
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
                job = DataCollectionJob(
                    job_id=job_id,
                    source=job_dict.get("source", ""),
                    topic=job_dict.get("topic", ""),
                    status=JobStatus(job_dict["status"]),
                    progress=job_dict.get("progress", 0),
                    created_at=datetime.fromisoformat(job_dict["created_at"])
                )
                jobs_list.append(job)
        
        # Sort by creation time (newest first)
        jobs_list.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply filters
        if source:
            jobs_list = [j for j in jobs_list if j.source == source]
        
        if topic:
            jobs_list = [j for j in jobs_list if topic.lower() in j.topic.lower()]
        
        total = len(jobs_list)
        paginated_jobs = jobs_list[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [self._job_to_dict(job) for job in paginated_jobs]
        }
    
    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about data collection jobs
        
        Args:
            user_id: Filter by user ID
        
        Returns:
            Statistics dictionary
        """
        jobs_list = list(self._jobs.values())
        
        if user_id:
            jobs_list = [j for j in jobs_list if j.user_id == user_id]
        
        # Count by status
        status_counts = {}
        for status in JobStatus:
            count = len([j for j in jobs_list if j.status == status])
            if count > 0:
                status_counts[status.value] = count
        
        # Count by source
        source_counts = {}
        for job in jobs_list:
            source_counts[job.source] = source_counts.get(job.source, 0) + 1
        
        # Total documents collected
        total_documents = sum(len(j.documents) for j in jobs_list if j.documents)
        
        return {
            "total_jobs": len(jobs_list),
            "by_status": status_counts,
            "by_source": source_counts,
            "total_documents_collected": total_documents,
            "completed_jobs": len([j for j in jobs_list if j.status == JobStatus.COMPLETED]),
            "failed_jobs": len([j for j in jobs_list if j.status == JobStatus.FAILED]),
            "running_jobs": len([j for j in jobs_list if j.status == JobStatus.RUNNING])
        }