from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import uuid
from ...core.data_collection import CrawlerFactory
from ...core.config import settings
from ...api.websocket import manager

router = APIRouter(prefix="/data-collection", tags=["data-collection"])

# Store job statuses
jobs = {}

class DataCollectionJob:
    def __init__(self, job_id: str, config: Dict[str, Any]):
        self.job_id = job_id
        self.config = config
        self.status = "pending"
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.progress = 0
        self.result = None
        self.error = None
        self.documents = []

@router.post("/start")
async def start_collection(
    background_tasks: BackgroundTasks,
    source: str,
    topic: str,
    search_engine: str = "google",
    limit: int = 100,
    config: Dict[str, Any] = {}
):
    """Start data collection job
    - **source**: Data source (e.g., "web", "books")
    - **topic**: Topic to collect data about
    - **search_engine**: Search engine to use for web crawling (e.g., "google", "bing") - default: "google"
    - **limit**: Maximum number of documents to collect
    - **config**: Additional configuration for the crawler
    """

    job_id = str(uuid.uuid4())
    jobs[job_id] = DataCollectionJob(job_id, {
        'source': source,
        'topic': topic,
        'search_engine': search_engine,
        'limit': limit,
        **config
    })
    
    background_tasks.add_task(
        run_collection,
        job_id,
        source,
        topic,
        limit,
        config
    )
    
    return {"job_id": job_id, "status": "started"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get collection job status"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
        "documents_count": len(job.documents)
    }

@router.get("/sources")
async def get_sources() -> List[str]:
    """Get available data sources"""
    return ["web", "books"]

async def run_collection(job_id: str, source: str, topic: str, limit: int, config: Dict[str, Any]):
    """Background task for data collection"""
    job = jobs[job_id]
    job.status = "running"
    
    try:
        # Get crawler
        crawler = CrawlerFactory.get_crawler(source, config)
        
        # Update progress
        job.progress = 10
        
        # Start crawling
        documents = await crawler.crawl(topic, limit)
        
        # Update progress
        job.progress = 80
        
        # Save documents
        output_path = f"{settings.DATA_STORAGE_PATH}/raw/{job_id}.json"
        crawler.save_documents(output_path)
        
        job.documents = documents
        job.result = {
            "output_path": output_path,
            "document_count": len(documents),
            "source": source,
            "topic": topic
        }
        job.status = "completed"
        job.progress = 100
        
        # Send WebSocket update
        await manager.notify_job_update(job_id, {
            "status": "completed",
            "progress": 100,
            "result": job.result
        })
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        await manager.notify_job_update(job_id, {
            "status": "failed",
            "error": str(e)
        })