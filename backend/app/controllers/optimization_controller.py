# app/controllers/optimization_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

from app.core.config import settings
from app.common.job_models import OptimizationJob, JobStatus, JobFactory
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType

logger = logging.getLogger(__name__)


class OptimizationController(BaseController):
    """Controller for model optimization operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def start_job(
        self,
        *,
        model_path: str,
        optimization_type: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start an optimization job
        
        Args:
            model_path: Path to the model to optimize
            optimization_type: Type of optimization (pruning, quantization, distillation)
            config: Optimization configuration
            user_id: User ID
            tags: Optional tags for categorization
        
        Returns:
            Job information
        """
        try:
            # Clear pipeline and build optimization pipeline
            self.orchestrator.clear_pipeline()
            
            self.orchestrator.add_node_to_pipeline(
                node_id="optimizer",
                name=f"{optimization_type.title()} Optimization",
                node_type=NodeType.OPTIMIZATION,
                config={
                    "model_path": model_path,
                    "optimization_type": optimization_type,
                    "optimization_config": config
                },
                resources={"cpu": 2, "memory_gb": 8},
                metadata={
                    "model_path": model_path,
                    "optimization_type": optimization_type
                }
            )
            
            # Create job using factory
            job = JobFactory.create_optimization_job(
                optimization_type=optimization_type,
                input_model_path=model_path,
                config=config,
                user_id=user_id,
                tags=tags or ["optimization", optimization_type]
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
            
            logger.info(f"Optimization job {job.job_id} started for {model_path}")
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_id) if execution_id else None,
                "status": "started",
                "optimization_type": optimization_type,
                "message": "Optimization job started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start optimization job: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get optimization job status"""
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
                "optimization_type": job.optimization_type,
                "input_model_path": job.input_model_path,
                "output_model_path": job.output_model_path,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "user_id": job.user_id,
                "tags": job.tags,
                "metrics": job.metrics,
                "original_size": job.original_size,
                "optimized_size": job.optimized_size,
                "compression_ratio": job.compression_ratio
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return None
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        optimization_type: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """List optimization jobs"""
        
        # Get from orchestrator
        result = self.orchestrator.list_jobs(
            job_type="optimization",
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Add local jobs
        local_jobs = []
        for job in self._jobs.values():
            if optimization_type and job.optimization_type != optimization_type:
                continue
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
        """Cancel an optimization job"""
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
                    logger.info(f"Job {job_id} cancelled successfully")
                    return True
            
            return False
            
        except ValueError:
            return False