# app/controllers/optimization_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

from app.common.job_models import JobFactory
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType
from app.common.job_models import OptimizationConfig

logger = logging.getLogger(__name__)


class OptimizationController(BaseController):
    """Controller for model optimization operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def add_job(
        self,
        *,
        config: OptimizationConfig,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_execute: bool = True,
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
            config = config or {}
            # Create job using factory
            job = JobFactory.create_optimization_job(
                optimization_config=config,
                **kwargs
            )
            metadata = JobFactory.create_job_metadata(
                name=f"Optimization job", 
                node_type=NodeType.OPTIMIZATION,
                job=job,
                description=f"Optimizing model. Type: {config.optimization_type}",
                config={},
                tags=tags or [])
           
            # Register job with orchestrator
            return await self.register(job, metadata, auto_execute=auto_execute)

        except Exception as e:
            logger.error(f"Failed to start optimization job: {e}")
            raise
    
   