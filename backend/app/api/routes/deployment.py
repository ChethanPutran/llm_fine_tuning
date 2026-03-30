# app/api/routes/deployment.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.dependencies.controller import get_deployment_controller
from app.controllers.deployment_controller import DeploymentController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deployment", tags=["deployment"])


class StartDeploymentRequest(BaseModel):
    """Request model for starting deployment"""
    model_path: str = Field(..., description="Path to the model to deploy")
    serving_framework: str = Field(..., description="Framework for serving (torchserve, tensorflow-serving, onnx)")
    deployment_target: str = Field("local", description="Deployment target (local, cloud, edge)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Deployment configuration")


@router.post("/deploy", response_model=Dict[str, Any])
async def deploy_model(
    request: StartDeploymentRequest,
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """Deploy a model"""
    try:
        result = await controller.start_job(
            model_path=request.model_path,
            serving_framework=request.serving_framework,
            deployment_target=request.deployment_target,
            config=request.config
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start deployment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_deployment_status(
    job_id: str,
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """Get deployment job status"""
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/jobs", response_model=Dict[str, Any])
async def list_deployment_jobs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """List all deployment jobs"""
    return await controller.list_jobs(limit=limit, offset=offset, status=status)


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_deployments(
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """List all active deployments"""
    return await controller.list_deployments()


@router.delete("/{deployment_id}", response_model=Dict[str, Any])
async def undeploy_model(
    deployment_id: str,
    controller: DeploymentController = Depends(get_deployment_controller)
):
    """Undeploy a model"""
    undeployed = await controller.undeploy_model(deployment_id)
    if undeployed:
        return {"status": "undeployed", "deployment_id": deployment_id}
    raise HTTPException(status_code=404, detail="Deployment not found")


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


@router.get("/targets", response_model=List[str])
async def get_deployment_targets():
    """Get available deployment targets"""
    return ["local", "cloud", "edge"]


@router.get("/frameworks", response_model=List[str])
async def get_serving_frameworks():
    """Get available serving frameworks"""
    return ["torchserve", "tensorflow-serving", "onnx"]