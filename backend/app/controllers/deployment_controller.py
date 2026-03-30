# app/controllers/deployment_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

from app.core.config import settings
from app.common.job_models import DeploymentJob, JobStatus, JobFactory
from app.controllers.base_controller import BaseController
from app.core.deployment.deployment_pipeline import DeploymentPipeline
from app.core.deployment.torchserve import TorchServeDeployment
from app.core.deployment.tensorflow_serving import TensorFlowServing
from app.core.deployment.onnx import ONNXDeployment
from app.core.pipeline_engine.models import NodeType

logger = logging.getLogger(__name__)


class DeploymentController(BaseController):
    """Controller for model deployment operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def start_job(
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
            # Clear pipeline and build deployment pipeline
            self.orchestrator.clear_pipeline()
            
            self.orchestrator.add_node_to_pipeline(
                node_id="deployer",
                name=f"Deploy to {serving_framework}",
                node_type=NodeType.MODEL_DEPLOYMENT,
                config={
                    "model_path": model_path,
                    "serving_framework": serving_framework,
                    "deployment_target": deployment_target,
                    "deployment_config": config
                },
                resources={"cpu": 2, "memory_gb": 4},
                metadata={
                    "model_path": model_path,
                    "serving_framework": serving_framework,
                    "deployment_target": deployment_target
                }
            )
            
            # Create job using factory
            job = JobFactory.create_deployment_job(
                model_path=model_path,
                serving_framework=serving_framework,
                deployment_target=deployment_target,
                config=config,
                user_id=user_id,
                tags=tags or ["deployment", serving_framework]
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
            
            logger.info(f"Deployment job {job.job_id} started for {model_path}")
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_id) if execution_id else None,
                "status": "started",
                "serving_framework": serving_framework,
                "deployment_target": deployment_target,
                "message": "Deployment job started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start deployment job: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment job status"""
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
                "deployment_id": job.deployment_id,
                "endpoint": job.endpoint,
                "model_path": job.model_path,
                "serving_framework": job.serving_framework,
                "deployment_target": job.deployment_target,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "user_id": job.user_id,
                "tags": job.tags,
                "config": job.config,
                "status_info": job.status_info
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return None
    
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
        result = self.orchestrator.list_jobs(
            job_type="deployment",
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Add local jobs
        local_jobs = []
        for job in self._jobs.values():
            if serving_framework and job.serving_framework != serving_framework:
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
        """Cancel a deployment job"""
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
                        logger.info(f"Model {deployment_id} undeployed successfully")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to undeploy {deployment_id}: {e}")
                        return False
        
        return False
    
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