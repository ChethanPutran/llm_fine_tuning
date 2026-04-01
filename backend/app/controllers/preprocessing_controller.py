# app/controllers/preprocessing_controller.py

from typing import Dict, Any, Optional, List
import os
import logging

from app.common.job_models import PreprocessingConfig, JobFactory
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType
from app.common.job_models import PreprocessingConfig

logger = logging.getLogger(__name__)


class PreprocessingController(BaseController):
    """Controller for preprocessing operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def add_job(
        self,
        *,
        config: PreprocessingConfig,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_execute: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a preprocessing job
        
        Args:
            input_path: Path to input data
            config: Preprocessing configuration
            output_path: Optional output path
            user_id: User ID
            tags: Optional tags for categorization
        
        Returns:
            Job information
        """
        # Validate input path
        if not os.path.exists(config.input_path):
            raise ValueError(f"Input path not found: {config.input_path}")
        
        try:
            # Create job using factory
            job = JobFactory.create_preprocessing_job(
                preprocessing_config=config,
                **kwargs
            )
            metadata = JobFactory.create_job_metadata(
                name=f"Preprocessing job",
                node_type=NodeType.DATA_PROCESSING,
                job=job,
                description=f"Preprocessing data from {config.input_path}",
                config=config.dict(),
                tags=tags or []
            )
            # Register job with orchestrator
            return await self.register(job, metadata, message="Preprocessing job created successfully", auto_execute=auto_execute)
            
        except Exception as e:
            logger.error(f"Failed to start preprocessing job: {e}")
            raise
    
  