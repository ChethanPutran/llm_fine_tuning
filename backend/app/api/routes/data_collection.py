# app/api/routes/data_collection.py

from fastapi import APIRouter, Depends, HTTPException, Query
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
    auto_execute: bool = Field(True, description="Automatically execute the job after creation")


@router.post("/add", response_model=Dict[str, Any])
async def create_collection_job(
    request: StartCollectionRequest,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """
    Create a data collection job
    
    Creates a job that can be executed later. If auto_execute is True,
    the job will be executed immediately.
    """
    try:
        # Create the job
        result = await controller.add_job(
            source=request.source,
            topic=request.topic,
            search_engine=request.search_engine,
            limit=request.limit,
            config=request.config,
            user_id="system",  # In real implementation, get from auth context
            tags=["api_created"]
        )
        
        # Auto-execute if requested
        if request.auto_execute and result.get("job_id"):
            job_id = result["job_id"]
            execution_result = await controller.execute_job(job_id)
            result["execution_id"] = execution_result.get("execution_id")
            result["execution_status"] = "started"
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to create data collection job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=Dict[str, Any])
async def execute_collection_job(
    job_id: str,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """
    Execute an existing data collection job
    
    Starts the execution of a previously created job.
    """
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute data collection job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_job_status(
    job_id: str,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """Get collection job status with details"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.post("/cancel/{job_id}", response_model=Dict[str, Any])
async def cancel_collection_job(
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
async def get_available_sources():
    """Get available data sources"""
    return ["web", "books", "news", "academic", "social_media"]


@router.get("/jobs", response_model=Dict[str, Any])
async def list_collection_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    source: Optional[str] = Query(None, description="Filter by data source"),
    topic: Optional[str] = Query(None, description="Filter by topic (partial match)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """
    List all data collection jobs with pagination and filters
    
    Returns a paginated list of jobs with total count.
    """
    result = await controller.list_jobs(
        status=status,
        limit=limit,
        offset=offset,
        source=source,
        topic=topic,
        user_id=user_id
    )
    return result


@router.get("/statistics", response_model=Dict[str, Any])
async def get_collection_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """
    Get statistics about data collection jobs
    
    Returns counts by status, source, and total documents collected.
    """
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get collection statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))