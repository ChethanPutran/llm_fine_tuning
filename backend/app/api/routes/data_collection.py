# app/api/routes/data_collection.py

from pydantic import Field

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging

from app.dependencies.controller import get_data_collection_controller
from app.controllers.data_collection_controller import DataCollectionController
from app.api.models import ExecutionStatusResponse, JobCreationResponse, JobStatusResponse, ListJobsResponse, ListResourcesResponse, RequestBase, StartCollectionRequest, StatisticsResponse 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-collection", tags=["data-collection"])


@router.post("/add", response_model=JobCreationResponse)
async def create_collection_job(
    request: StartCollectionRequest,
    user_id: Optional[str] = Query(None, description="User ID for job ownership (optional)"),
    controller: DataCollectionController = Depends(get_data_collection_controller),
):
    """
    Create a data collection job
    
    Creates a job that can be executed later. If auto_execute is True,
    the job will be executed immediately.
    """
    try:
        # Create the job
        result = await controller.add_job(config=request.config, user_id=user_id,
                                          auto_execute=request.auto_execute)
        return JobCreationResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to create data collection job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=ExecutionStatusResponse)
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
        
        return ExecutionStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute data collection job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """Get collection job status with details"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**status)


@router.post("/remove/{job_id}", response_model=JobStatusResponse)
async def remove_collection_job(
    job_id: str,
    controller: DataCollectionController = Depends(get_data_collection_controller)
):
    """Remove a running data collection job"""
    removed = await controller.remove_job(job_id)
    if removed:
        return JobStatusResponse(**removed)
    else:
        raise HTTPException(status_code=400, detail="Job cannot be removed or not found")


@router.get("/sources", response_model=ListResourcesResponse)
async def get_available_sources(
):
    """Get available data sources"""

    return ListResourcesResponse(
        items=[
            {"name": "web", "description": "Web scraping"},
            {"name": "books", "description": "Book collection"},
            {"name": "news", "description": "News articles"},
            {"name": "academic", "description": "Academic papers"},
            {"name": "social_media", "description": "Social media posts"}
        ],
        user_id=None,
        status="success",
        message="Available data sources retrieved successfully",
        error=None,
        tags=[]
    )


@router.get("/jobs", response_model=ListJobsResponse)
async def list_collection_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
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
        job_type="data_collection",
        user_id=user_id
    )
    return ListJobsResponse(**result)


@router.get("/statistics", response_model=StatisticsResponse)
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
        return StatisticsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Failed to get collection statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))