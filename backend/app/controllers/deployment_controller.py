# app/controllers/deployment_controller.py

from typing import Dict, Any, Optional, List
import logging

from app.common.job_models import JobFactory
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType
from app.common.job_models import DeploymentConfig

logger = logging.getLogger(__name__)


class DeploymentController(BaseController):
    """Controller for model deployment operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def add_job(
        self,
        *,
        config: DeploymentConfig,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_execute: bool = True,
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
            
            # Create job using factory
            job = JobFactory.create_deployment_job(
                deployment_config=config,
                **kwargs
            )
            metadata = JobFactory.create_job_metadata(
                name=f"Deployment model", 
                node_type=NodeType.MODEL_DEPLOYMENT,
                job=job,
                description=f"Deploying model {config.model_path} using {config.serving_framework}",
                config={},
                tags=tags or [])

            return await self.register(job, metadata, auto_execute=auto_execute)

        except Exception as e:
            logger.error(f"Failed to start deployment job: {e}")
            raise
    
    