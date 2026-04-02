# app/controllers/base_controller.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from app.common.job_models import BaseJob, JobPriority, JobStatus
from app.core.pipeline_engine.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)


class BaseController(ABC):
    """Base controller with common functionality"""
    
    def __init__(self, orchestrator:PipelineOrchestrator):
        self.orchestrator = orchestrator
    
    async def register(self, job, metadata, auto_execute=True,message=None) -> Dict[str, Any]:
        """Register controller routes - to be implemented by subclasses if needed"""
        res = {
                "job_id": str(job.job_id),
                "status": "created",
                "message": message
            }

        # Register job with orchestrator
        self.orchestrator.register_job(job, metadata)

            # Auto-execute if requested
        if auto_execute and res.get("job_id"):
            job_id = res["job_id"]
            execution_result = await self.execute_job(job_id)
            res["execution_id"] = str(execution_result.get("execution_id"))
            res["execution_status"] = "started"
            
        return res
    
    @abstractmethod
    async def add_job(self, **kwargs) -> Dict[str, Any]:
        """
        Add a new job
        
        Args:
            **kwargs: Job-specific parameters
            
        Returns:
            Job information dictionary
        """
        pass
    
    def _get_job(self, job_id: UUID) -> Optional[BaseJob]:
        """Get a job by ID"""
        return self.orchestrator.get_job(job_id)
    
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

    async def execute_pipeline(self, user_id: str, priority: JobPriority) -> Dict[str, Any]:
        """
        Execute a pipeline with given configuration
        
        Args:
            config: Pipeline configuration dictionary
            user_id: User ID for tracking
            priority: Execution priority (1-10)
            auto_register: Whether to automatically register the pipeline as a job
            
        Returns:
            Execution result information
        """
        try:
            execution_result = await self.orchestrator.execute_current_pipeline(user_id, priority)
            
            return {
                "execution_id": str(execution_result.get("execution_id", "")),
                "message": "Pipeline execution started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to execute pipeline: {e}")
            return {"error": "Failed to execute pipeline"}
        
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
                **job.model_dump(),
                "execution_details": execution_status
            }
            
        except ValueError as e:
            logger.error(f"Invalid job ID: {job_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get status of a specific execution
        
        Args:
            execution_id: Execution ID
        
        Returns:
            Execution status information
        """
        try:
            execution_uuid = UUID(execution_id)
            status = await self.orchestrator.get_execution_status(execution_uuid)
            if not status:
                return {"error": "Execution not found"}
            return status
        except ValueError as e:
            logger.error(f"Invalid execution ID: {execution_id}")
            return {"error": "Invalid execution ID"}
        except Exception as e:
            logger.error(f"Failed to get execution status: {e}")
            return {"error": "Failed to get execution status"}
        
    async def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Cancel a running execution
        
        Args:
            execution_id: Execution ID to cancel
        
        Returns:
            True if cancelled successfully
        """
        try:
            execution_uuid = UUID(execution_id)
            await self.orchestrator.cancel_execution(execution_uuid)
            return {
                "execution_id": execution_id,
                "message": "Execution cancelled successfully",
                "status": "cancelled"
            }
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return {
                "error": "Failed to cancel execution"
            }
        
    async def remove_job(self, job_id: str) -> Dict[str, Any]:
        """
        Remove a running data collection job
        
        Args:
            job_id: Job ID
        
        Returns:
            True if removed successfully
        """
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            await self.orchestrator.remove_job(job_uuid)
            return {
                "job_id": job_id,
                "message": "Job removed successfully",
                "status": "removed",
                "job_type": job.job_type.value if job else "unknown"

            }
        except Exception as e:
            logger.error(f"Invalid job ID: {job_id}")
            return {
                "error": "Invalid job ID"   
            }

    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
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
    
        jobs_list:List[BaseJob] = orchestrator_jobs.get("jobs", [])
        
        # Sort by creation time (newest first)
        jobs_list.sort(key=lambda x: x.created_at, reverse=True)
        
        
        total = len(jobs_list)
        paginated_jobs = jobs_list[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [job.model_dump() for job in paginated_jobs],
            "status": "success",
            "message": "Jobs retrieved successfully",
            "error": None,
            "tags": []
        }
    
    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about data collection jobs
        
        Args:
            user_id: Filter by user ID
        
        Returns:
            Statistics dictionary
        """
        orchestrator_jobs = await self.orchestrator.get_statistics(
            job_type="data_collection",
            user_id=user_id
        )
        return orchestrator_jobs
    
    def _update_job(self, job_id: UUID, **kwargs):
        """Update job attributes"""
        status = self.orchestrator.update_job(job_id, **kwargs)
        if status:
            logger.debug(f"Job {job_id} updated")
        else:
            logger.warning(f"Failed to update job {job_id} with {kwargs}")
        return status
    
   