# app/controllers/deployment_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

from app.core.config import settings
from app.common.job_models import DeploymentJob, JobStatus, JobFactory, JobPriority
from app.controllers.base_controller import BaseController
from app.core.deployment.deployment_pipeline import DeploymentPipeline
from app.core.deployment.torchserve import TorchServeDeployment
from app.core.deployment.tensorflow_serving import TensorFlowServing
from app.core.deployment.onnx import ONNXDeployment
from app.core.pipeline_engine.models import NodeType
from app.api.websocket import manager

logger = logging.getLogger(__name__)


class DeploymentController(BaseController):
    """Controller for model deployment operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def add_job(
        self,
        *,
        model_path: str,
        serving_framework: str,
        deployment_target: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a deployment job
        
        Args:
            model_path: Path to the model to deploy
            serving_framework: Framework for serving (torchserve, tensorflow-serving, onnx)
            deployment_target: Deployment target (local, cloud, edge)
            config: Deployment configuration
            user_id: User ID
            tags: Optional tags for categorization
        
        Returns:
            Job information
        """
        
        try:
            config = config or {}
            metadata = {
                "node_id": "deployment",
                "name": f"Deploy {model_path} to {serving_framework}",
                "node_type": NodeType.MODEL_DEPLOYMENT,
                "resources": {"cpu": 2, "memory_gb": 4},
                "metadata": {
                    "model_path": model_path,
                    "serving_framework": serving_framework,
                    "deployment_target": deployment_target,
                    "deployment_config": config
                },
                "retry_policy": config.get("retry_policy", {"retries": 3, "delay_seconds": 5}),
                "position": config.get("position", (0, 0))
            }
            
            # Create job using factory
            job = JobFactory.create_deployment_job(
                model_path=model_path,
                serving_framework=serving_framework,
                deployment_target=deployment_target,
                config=config,
                user_id=user_id,
                tags=tags or ["deployment", serving_framework]
            )
            
            # Register job with orchestrator
            self.orchestrator.register_job(job, metadata)
            
            return {
                "job_id": str(job.job_id),
                "message": "Deployment job created successfully",
            }
            
        except Exception as e:
            logger.error(f"Failed to start deployment job: {e}")
            raise
    
    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a registered deployment job
        
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
        """Get deployment job status"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
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
                "deployment_id": job.deployment_id,
                "endpoint": job.endpoint,
                "model_path": job.model_path,
                "serving_framework": job.serving_framework,
                "deployment_target": job.deployment_target,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "updated_at": job.updated_at.isoformat(),
                "user_id": job.user_id,
                "tags": job.tags,
                "config": job.config,
                "status_info": job.status_info,
                "execution_details": execution_status
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a deployment job"""
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return False
            
            # Check if job can be cancelled
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                logger.warning(f"Job {job_id} cannot be cancelled in status {job.status}")
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
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        serving_framework: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """List deployment jobs"""
        
        # Get from orchestrator
        orchestrator_jobs = self.orchestrator.list_jobs(
            job_type="deployment",
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
                job = DeploymentJob(
                    job_id=job_id,
                    model_path=job_dict.get("model_path", ""),
                    serving_framework=job_dict.get("serving_framework", ""),
                    deployment_target=job_dict.get("deployment_target", ""),
                    status=JobStatus(job_dict["status"]),
                    progress=job_dict.get("progress", 0),
                    created_at=datetime.fromisoformat(job_dict["created_at"])
                )
                jobs_list.append(job)
        
        # Sort by creation time (newest first)
        jobs_list.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply filters
        if serving_framework:
            jobs_list = [j for j in jobs_list if j.serving_framework == serving_framework]
        
        total = len(jobs_list)
        paginated_jobs = jobs_list[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [self._job_to_dict(job) for job in paginated_jobs]
        }
    
    async def list_deployments(self) -> List[Dict[str, Any]]:
        """List all active deployments"""
        active_deployments = []
        
        for job in self._jobs.values():
            if job.status == JobStatus.COMPLETED:
                active_deployments.append({
                    "deployment_id": job.deployment_id or str(job.job_id),
                    "endpoint": job.endpoint,
                    "framework": job.serving_framework,
                    "status": job.status.value,
                    "model_path": job.model_path,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                })
        
        return active_deployments
    
    async def undeploy_model(self, deployment_id: str) -> bool:
        """Undeploy a model"""
        # Find job with matching deployment_id
        for job in self._jobs.values():
            if job.deployment_id == deployment_id:
                if job.status == JobStatus.COMPLETED:
                    try:
                        deployer = self._get_deployer(job.serving_framework, job.config)
                        await deployer.undeploy(deployment_id)
                        job.status = JobStatus.CANCELLED
                        self._update_job(job.job_id, status=job.status)
                        await manager.notify_job_update(str(job.job_id), {
                            "status": "undeployed",
                            "message": f"Model {deployment_id} undeployed"
                        })
                        logger.info(f"Model {deployment_id} undeployed successfully")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to undeploy {deployment_id}: {e}")
                        return False
        
        return False
    
    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get deployment statistics"""
        jobs_list = list(self._jobs.values())
        
        if user_id:
            jobs_list = [j for j in jobs_list if j.user_id == user_id]
        
        # Count by status
        status_counts = {}
        for status in JobStatus:
            count = len([j for j in jobs_list if j.status == status])
            if count > 0:
                status_counts[status.value] = count
        
        # Count by framework
        framework_counts = {}
        for job in jobs_list:
            framework_counts[job.serving_framework] = framework_counts.get(job.serving_framework, 0) + 1
        
        return {
            "total_jobs": len(jobs_list),
            "by_status": status_counts,
            "by_framework": framework_counts,
            "active_deployments": len([j for j in jobs_list if j.status == JobStatus.COMPLETED]),
            "failed_deployments": len([j for j in jobs_list if j.status == JobStatus.FAILED])
        }
    
    def _get_deployer(self, framework: str, config: Dict[str, Any]):
        """Get deployer instance based on framework"""
        if framework == "torchserve":
            return TorchServeDeployment(config)
        elif framework == "tensorflow-serving":
            return TensorFlowServing(config)
        elif framework == "onnx":
            return ONNXDeployment(config)
        else:
            raise ValueError(f"Unsupported framework: {framework}")