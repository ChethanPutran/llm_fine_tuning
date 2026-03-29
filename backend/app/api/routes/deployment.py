from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import uuid
from datetime import datetime
import asyncio
from app.core.deployment.deployment_pipeline import DeploymentPipeline
from app.core.deployment.torchserve import TorchServeDeployment
from app.core.deployment.tensorflow_serving import TensorFlowServing
from app.core.deployment.onnx import ONNXDeployment
from app.core.config import settings
from ..models import DeploymentRequest, DeploymentInfo, JobResponse

router = APIRouter(prefix="/deployment", tags=["deployment"])

# Store deployment jobs
deployments = {}

class DeploymentJob:
    def __init__(self, job_id: str, request: DeploymentRequest):
        self.job_id = job_id
        self.request = request
        self.status = "pending"
        self.progress = 0
        self.result = None
        self.error = None
        self.deployment_id = None

@router.post("/deploy", response_model=JobResponse)
async def deploy_model(
    background_tasks: BackgroundTasks,
    request: DeploymentRequest
):
    """Deploy a model"""
    job_id = str(uuid.uuid4())
    deployments[job_id] = DeploymentJob(job_id, request)
    
    background_tasks.add_task(
        run_deployment,
        job_id,
        request
    )
    
    return JobResponse(job_id=job_id, status="started", message="Deployment started")

@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_status(job_id: str):
    """Get deployment status"""
    job = deployments.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Deployment job not found")
    
    return {
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
        "deployment_id": job.deployment_id
    }

@router.get("/targets", response_model=List[str])
async def get_deployment_targets():
    """Get available deployment targets"""
    return ["local", "cloud", "edge"]

@router.get("/frameworks", response_model=List[str])
async def get_serving_frameworks():
    """Get available serving frameworks"""
    return ["torchserve", "tensorflow-serving", "onnx"]

@router.get("/list", response_model=List[DeploymentInfo])
async def list_deployments():
    """List all active deployments"""
    active_deployments = []
    for job_id, job in deployments.items():
        if job.status == "completed":
            active_deployments.append(DeploymentInfo(
                deployment_id=job.deployment_id or job_id,
                endpoint=job.result.get("endpoint", ""),
                framework=job.request.serving_framework,
                status=job.status,
                model_path=job.request.model_path,
                config=job.request.config,
                created_at=datetime.now()
            ))
    return active_deployments

@router.delete("/{deployment_id}")
async def undeploy_model(deployment_id: str):
    """Undeploy a model"""
    # Find and stop the deployment
    for job_id, job in deployments.items():
        if job.deployment_id == deployment_id:
            # Stop the deployment
            await stop_deployment(job)
            return {"status": "undeployed", "deployment_id": deployment_id}
    
    raise HTTPException(status_code=404, detail="Deployment not found")

async def run_deployment(job_id: str, request: DeploymentRequest):
    """Background task for model deployment"""
    job = deployments[job_id]
    job.status = "running"
    
    try:
        # Update progress
        job.progress = 10
        
        # Create deployment pipeline
        pipeline = DeploymentPipeline(request.config)
        
        # Select deployment strategy
        if request.serving_framework == "torchserve":
            deployer = TorchServeDeployment(request.config)
        elif request.serving_framework == "tensorflow-serving":
            deployer = TensorFlowServing(request.config)
        elif request.serving_framework == "onnx":
            deployer = ONNXDeployment(request.config)
        else:
            raise ValueError(f"Unsupported framework: {request.serving_framework}")
        
        job.progress = 30
        
        # Deploy model
        deployment_info = await deployer.deploy(
            request.model_path,
            request.deployment_target
        )
        
        job.progress = 80
        
        # Add to pipeline
        pipeline.add_deployment(deployer)
        result = pipeline.execute()
        
        job.result = {
            "endpoint": deployment_info.get("endpoint"),
            "model_id": deployment_info.get("model_id"),
            "status": "active",
            "deployment_info": deployment_info,
            "pipeline_result": result
        }
        job.deployment_id = deployment_info.get("model_id", job_id)
        job.status = "completed"
        job.progress = 100
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)

async def stop_deployment(job: DeploymentJob):
    """Stop a deployment"""
    if job.result and "deployment_info" in job.result:
        # Call undeploy on the deployer
        job.status = "stopped"