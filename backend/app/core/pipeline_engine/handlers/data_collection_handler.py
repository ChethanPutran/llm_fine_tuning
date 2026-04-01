# app/core/pipeline_engine/handlers/data_collection_handler.py

from typing import Dict, Any
import logging

from app.common.job_models import DataCollectionJob
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.data_collection import ScraperFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataCollectionHandler(BaseHandler):
    """Handler for data collection jobs"""
    
    async def get_job_config(self, source: str, scraper_config: Dict[str, Any]) -> Dict[str, Any]:
        if source == 'web':
            scraper_config = {
                "num_workers": scraper_config.get("num_workers", 4),
                "rate_limit": scraper_config.get("rate_limit", 1),
                "timeout": scraper_config.get("timeout", 10),
                "search_engine": scraper_config.get("search_engine", "wikipedia"),

            }
        elif source == 'social_media':
            scraper_config = {
                "num_workers": scraper_config.get("num_workers", 4),
                "rate_limit": scraper_config.get("rate_limit", 1),
                "timeout": scraper_config.get("timeout", 10),
                "platform": scraper_config.get("platform", "twitter"),
            }
        elif source == 'api':
            scraper_config = {
                "num_workers": scraper_config.get("num_workers", 4),
                "rate_limit": scraper_config.get("rate_limit", 1),
                "timeout": scraper_config.get("timeout", 10),
                "api_endpoint": scraper_config.get("api_endpoint"),
                "api_key": scraper_config.get("api_key"),
            }
        elif source == 'file':
            scraper_config = {
                "file_path": scraper_config.get("file_path"),
                "file_type": scraper_config.get("file_type", "csv"),
            }
        else:
            scraper_config = {
                "num_workers": scraper_config.get("num_workers", 4),
                "rate_limit": scraper_config.get("rate_limit", 1),
                "timeout": scraper_config.get("timeout", 10),
            }
        return scraper_config

    async def execute(self, job: DataCollectionJob) -> Dict[str, Any]:
        """Execute data collection"""
        
        await self._mark_started(job)
        
        try:
            config = job.config
            scraper_config = config.scraper_config 
            # scraper_config = await self.get_job_config(config.source, scraper_config)
            
            await self._update_progress(job.job_id, 10, "Initializing crawler")
            
            # Get scraper
            scraper = ScraperFactory.get_scraper(config.source, scraper_config)
            
            await self._update_progress(job.job_id, 30, f"Scraping {config.topic} from {config.source}")
            
            # Start scraping
            await scraper.scrape(config.topic, num_workers=scraper_config.num_workers, save=False)
            
            await self._update_progress(job.job_id, 80, f"Saving {len(scraper.documents)} documents")
            
            # Save documents
            output_path = f"{settings.DATA_STORAGE_PATH}/raw/{job.job_id}.json"

            await scraper.save_documents(output_path)
            
            documents = [{
                    "id": str(doc.id),
                    "content": f"{doc.content[:1000]}...",  # Clean truncation
                    "metadata": doc.metadata,
                    "source": getattr(doc, 'source', 'web'), # Safe access
                    "timestamp": doc.timestamp.isoformat() if hasattr(doc.timestamp, 'isoformat') else str(doc.timestamp)
                } 
                for doc in scraper.documents]
            

            result = {
                "success": True,
                "count": len(scraper.documents),
                "output_path": output_path,
                "source": config.source,
                "topic": config.topic,
                "scraper_config": scraper_config,
                 "documents": documents
            }
            
            
            # Update job with results
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise