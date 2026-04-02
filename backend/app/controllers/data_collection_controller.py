# app/controllers/data_collection_controller.py

from typing import Dict, Any, Optional, List
import logging


from app.common.job_models import JobFactory, DataCollectionConfig
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.models import NodeType

logger = logging.getLogger(__name__)


class DataCollectionController(BaseController):
    """Controller for data collection operations"""
    def __init__(self, orchestrator):
        super().__init__(orchestrator)

    async def add_job(
        self,
        *,
        config: DataCollectionConfig,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_execute: bool = True,
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
            # Create data collection job
            job = JobFactory.create_data_collection_job(data_collection_config=config,**kwargs)
            metadata = JobFactory.create_job_metadata(
                name=f"Data Collection", 
                node_type=NodeType.DATA_INGESTION,
                job=job,
                description=f"Collecting data from {config.source} on topic {config.topic}",
                config={},
                tags=tags or [])

            return await self.register(job, metadata, auto_execute=auto_execute)

            
        except Exception as e:
            logger.error(f"Failed to start data collection job: {e}")
            raise
    
    