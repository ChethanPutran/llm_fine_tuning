# app/api/routes/data_collection.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_data_collection_controller
from app.controllers.data_collection_controller import DataCollectionController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-collection", tags=["data-collection"])


class StartCollectionRequest(BaseModel):
    """Request model for starting data collection"""
    source: str = Field(..., description="Data source (web, books, etc.)")
    topic: str = Field(..., description="Topic to collect data about")
    search_engine: str = Field("google", description="Search engine to use")
    limit: int = Field(100, ge=1, le=10000, description="Maximum number of documents")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")


@router.post("/start", response_model=Dict[str, Any])
async def start_collection(
    request: StartCollectionRequest,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """
    Start data collection job
    
    Creates a pipeline with data collection node and executes it
    """
    try:
        result = await controller.start_job(
            source=request.source,
            topic=request.topic,
            search_engine=request.search_engine,
            limit=request.limit,
            config=request.config,
            user_id="system"  # In real implementation, get from auth context
        )
        return result
    except Exception as e:
        logger.error(f"Failed to start data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_status(
    job_id: str,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """Get collection job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.post("/cancel/{job_id}", response_model=Dict[str, Any])
async def cancel_collection(
    job_id: str,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """Cancel a running data collection job"""
    cancelled = await controller.cancel_job(job_id)
    if cancelled:
        return {
            "job_id": job_id,
            "message": "Job cancelled successfully",
            "status": "cancelled"
        }
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/sources", response_model=List[str])
async def get_sources():
    """Get available data sources"""
    return ["web", "books", "news", "academic", "social_media"]


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """List all data collection jobs"""
    return await controller.list_jobs(status=status, limit=limit, offset=offset)