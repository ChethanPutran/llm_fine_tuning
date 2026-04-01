# app/core/pipeline_engine/handlers/deployment_handler.py

"""
Handler for deployment jobs
"""

from typing import Dict, Any
import logging

from app.common.job_models import DeploymentJob
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.deployment.factory import DeploymentFactory
from app.core.deployment.pipeline import DeploymentPipeline

logger = logging.getLogger(__name__)


class DeploymentHandler(BaseHandler):
    """Handler for deployment jobs"""
    
    async def execute(self, job: DeploymentJob) -> Dict[str, Any]:
        """Execute deployment"""
        
        await self._mark_started(job.job_id)
        
        try:
            config = job.config
            await self._update_progress(job.job_id, 10, "Creating deployment pipeline")
            
            # Create deployment pipeline
            pipeline = DeploymentPipeline(config)
            
            await self._update_progress(job.job_id, 30, f"Using {config.serving_framework}")
            
            # Select deployment strategy
            deployer = DeploymentFactory.get_deployer(config.serving_framework, config)
            
            await self._update_progress(job.job_id, 50, f"Deploying to {config.deployment_target}")
            
            # Deploy the model
            deployment_info = await deployer.deploy(
                config.model_path,
                config.deployment_target
            )
            
            await self._update_progress(job.job_id, 80, "Finalizing deployment")
            
            # Add to pipeline
            pipeline.add_deployment(deployer)
            pipeline_result = pipeline.execute()
            
            result = {
                "success": True,
                "endpoint": deployment_info.get("endpoint"),
                "model_id": deployment_info.get("model_id"),
                "status": "active",
                "deployment_info": deployment_info,
                "pipeline_result": pipeline_result,
                "serving_framework": config.serving_framework,
                "deployment_target": config.deployment_target
            }
            
            config.deployment_id = deployment_info.get("model_id", str(job.job_id))
            config.endpoint = deployment_info.get("endpoint")
            config.status_info = deployment_info
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise