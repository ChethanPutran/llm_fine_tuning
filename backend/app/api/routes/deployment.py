# app/api/routes/deployment.py

from aiohttp import request
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_deployment_controller
from app.controllers.deployment_controller import DeploymentController
from app.api.models import ListResourcesResponse, RequestBase, StartDeploymentRequest
from app.api.models import ExecutionStatusResponse, JobCreationResponse, JobStatusResponse, ListJobsResponse, StartCollectionRequest, StatisticsResponse 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deployment", tags=["deployment"])

@router.post("/add", response_model=JobCreationResponse)
async def create_deployment_job(
    request: StartDeploymentRequest,
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """Create a deployment job"""
    try:
        # Create the job
        result = await controller.add_job(
            model_path=request.config.model_path,
            serving_framework=request.config.serving_framework,
            deployment_target=request.config.deployment_target,
            config=request.config,
            user_id="system",  # In real implementation, get from auth context
            tags=request.tags
        )
        return JobCreationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create deployment job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=ExecutionStatusResponse)
async def execute_deployment_job(
    job_id: str,
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """Execute an existing deployment job"""
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return ExecutionStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute deployment job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_deployment_status(
    job_id: str,
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """Get deployment job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**status)


@router.get("/jobs", response_model=ListJobsResponse)
async def list_deployment_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    serving_framework: Optional[str] = Query(None, description="Filter by serving framework"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """List all deployment jobs with pagination and filters"""
    result = await controller.list_jobs(
        status=status,
        serving_framework=serving_framework,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return ListJobsResponse(**result)


@router.get("/active", response_model=List[Dict[str, Any]])
async def list_active_deployments(
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """List all active deployments"""
    jobs = await controller.list_jobs()
    active_deployments = [job for job in jobs.get("jobs", []) if job.get("status") == "deployed"]
    return active_deployments


# @router.delete("/{deployment_id}", response_model=Dict[str, Any])
# async def undeploy_model(
#     deployment_id: str,
#     controller: DeploymentController = Depends(get_deployment_controller)
# ):
#     """Undeploy a model"""
#     undeployed = await controller.undeploy_model(deployment_id)
#     if undeployed:
#         return {"status": "undeployed", "deployment_id": deployment_id}
#     raise HTTPException(status_code=404, detail="Deployment not found")


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
async def cancel_deployment_job(
    job_id: str,
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """Cancel a deployment job"""
    cancelled = await controller.cancel_job(job_id)
    if cancelled:
        return {"message": "Job cancelled successfully", "job_id": job_id}
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_deployment_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """Get deployment statistics"""
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get deployment statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/targets",  response_model=ListResourcesResponse)
async def get_deployment_targets(
):
    """Get available deployment targets"""
    return ListResourcesResponse(
        items=[
        {"name": "local", "description": "Deploy on local machine"},
        {"name": "cloud", "description": "Deploy on cloud platforms (AWS, GCP, Azure)"},
        {"name": "edge", "description": "Deploy on edge devices (NVIDIA Jetson, Raspberry Pi)"}
    ],
    user_id=None,
    status="success",
    message="Available deployment targets retrieved successfully",
    error=None,
    tags=[]
    )


@router.get("/frameworks", response_model=ListResourcesResponse)
async def get_serving_frameworks(
):
    """Get available serving frameworks"""
    return ListResourcesResponse(
        items=[
            {"name": "torchserve", "description": "TorchServe"},
            {"name": "tensorflow-serving", "description": "TensorFlow Serving"},
            {"name": "onnx", "description": "ONNX Runtime"}
        ],
        user_id=None,
        status="success",   
        message="Available serving frameworks retrieved successfully",
        error=None,
        tags=[]
    )