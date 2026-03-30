# app/core/pipeline_engine/handlers/data_collection_handler.py

"""
Handler for data collection jobs
"""

from typing import Dict, Any
import logging

from app.common.job_models import DataCollectionJob
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.data_collection import CrawlerFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataCollectionHandler(BaseHandler):
    """Handler for data collection jobs"""
    
    async def execute(self, job: DataCollectionJob) -> Dict[str, Any]:
        """Execute data collection"""
        
        await self._mark_started(job.job_id)
        
        try:
            config = job.metadata.get("node_config", {})
            source = config.get("source", job.source)
            topic = config.get("topic", job.topic)
            limit = config.get("limit", job.limit)
            search_engine = config.get("search_engine", job.search_engine)
            crawler_config = config.get("crawler_config", job.metadata.get("config", {}))
            
            await self._update_progress(job.job_id, 10, "Initializing crawler")
            
            # Get crawler
            crawler = CrawlerFactory.get_crawler(source, crawler_config)
            
            await self._update_progress(job.job_id, 30, f"Crawling {topic} from {source}")
            
            # Start crawling
            documents = await crawler.crawl(topic, limit)
            
            await self._update_progress(job.job_id, 80, f"Saving {len(documents)} documents")
            
            # Save documents
            output_path = f"{settings.DATA_STORAGE_PATH}/raw/{job.job_id}.json"
            crawler.save_documents(output_path, documents)
            
            result = {
                "success": True,
                "documents": documents,
                "count": len(documents),
                "output_path": output_path,
                "source": source,
                "topic": topic,
                "search_engine": search_engine
            }
            
            # Update job with results
            job.documents = documents
            job.output_path = output_path
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise