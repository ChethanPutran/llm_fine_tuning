# app/api/routes/pipeline.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID
import logging

from app.dependencies.controller import get_pipeline_controller
from app.controllers.pipeline_controller import PipelineController

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


class ExecutePipelineRequest(BaseModel):
    """Request model for executing a pipeline"""
    pipeline_json: Dict[str, Any] = Field(..., description="Pipeline definition in JSON format")
    user_id: Optional[str] = Field(None, description="User ID who triggered execution")
    priority: str = Field("NORMAL", description="Execution priority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)")
    auto_register: bool = Field(True, description="Whether to register the job in the system")


class CreatePipelineJobRequest(BaseModel):
    """Request model for creating a pipeline job"""
    pipeline_json: Dict[str, Any] = Field(..., description="Pipeline definition in JSON format")
    priority: str = Field("NORMAL", description="Execution priority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)")
    auto_execute: bool = Field(True, description="Automatically execute the job after creation")
    tags: Optional[list[str]] = Field(None, description="Optional tags for categorization")


@router.post("/execute", response_model=Dict[str, Any])
async def execute_pipeline(
    request: ExecutePipelineRequest,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Execute a pipeline from JSON definition
    
    This endpoint creates and executes a pipeline in one step.
    """
    try:
        result = await controller.execute_pipeline(
            pipeline_json=request.pipeline_json,
            user_id=request.user_id,
            priority=request.priority,
            auto_register=request.auto_register
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=Dict[str, Any])
async def create_pipeline_job(
    request: CreatePipelineJobRequest,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Create a pipeline execution job
    
    Creates a job that can be executed later. If auto_execute is True,
    the job will be executed immediately.
    """
    try:
        # Create the job
        result = await controller.add_job(
            pipeline_json=request.pipeline_json,
            priority=request.priority,
            user_id="system",  # In real implementation, get from auth context
            tags=request.tags
        )
        
        # Auto-execute if requested
        if request.auto_execute and result.get("job_id"):
            job_id = result["job_id"]
            execution_result = await controller.execute_job(job_id)
            result["execution_id"] = execution_result.get("execution_id")
            result["execution_status"] = "started"
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create pipeline job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=Dict[str, Any])
async def execute_pipeline_job(
    job_id: str,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Execute an existing pipeline job
    
    Starts the execution of a previously created pipeline job.
    """
    try:
        result = await controller.execute_job(job_id)
        
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute pipeline job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_pipeline_job_status(
    job_id: str,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Get pipeline job status
    
    Returns detailed status information about a pipeline job.
    """
    status = await controller.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/jobs", response_model=Dict[str, Any])
async def list_pipeline_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    List all pipeline jobs with pagination and filters
    
    Returns a paginated list of pipeline jobs with total count.
    """
    result = await controller.list_jobs(
        status=status,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return result


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
async def cancel_pipeline_job(
    job_id: str,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Cancel a pipeline job
    
    Cancels a running or queued pipeline job.
    """
    cancelled = await controller.cancel_job(job_id)
    if cancelled:
        return {"message": "Job cancelled successfully", "job_id": job_id}
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/executions/{execution_id}/status", response_model=Dict[str, Any])
async def get_execution_status(
    execution_id: UUID,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Get execution status directly
    
    Returns status information for a specific execution.
    """
    status = await controller.get_execution_status(execution_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@router.delete("/executions/{execution_id}", response_model=Dict[str, Any])
async def cancel_execution(
    execution_id: UUID,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Cancel a running execution
    
    Cancels an active pipeline execution.
    """
    result = await controller.cancel_execution(execution_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/executions/{execution_id}/logs", response_model=Dict[str, Any])
async def get_execution_logs(
    execution_id: UUID,
    node_id: Optional[str] = Query(None, description="Filter logs by node ID"),
    tail: int = Query(100, ge=1, le=10000, description="Number of lines to return from the end"),
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Get logs for an execution
    
    Returns execution logs, optionally filtered by node ID.
    """
    result = await controller.get_execution_logs(execution_id, node_id=node_id, tail=tail)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/statistics", response_model=Dict[str, Any])
async def get_pipeline_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Get pipeline statistics
    
    Returns aggregated statistics about pipeline jobs.
    """
    try:
        stats = await controller.get_statistics(user_id=user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get pipeline statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=Dict[str, Any])
async def get_pipeline_templates(
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Get available pipeline templates
    
    Returns a list of predefined pipeline templates.
    """
    try:
        templates = await controller.get_pipeline_templates()
        return templates
    except Exception as e:
        logger.error(f"Failed to get pipeline templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_name}", response_model=Dict[str, Any])
async def get_pipeline_template(
    template_name: str,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Get a specific pipeline template by name
    
    Returns details about a specific pipeline template.
    """
    try:
        templates = await controller.get_pipeline_templates()
        if template_name not in templates:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        return {
            "template_name": template_name,
            "template": templates[template_name]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_name}/instantiate", response_model=Dict[str, Any])
async def instantiate_template(
    template_name: str,
    config: Optional[Dict[str, Any]] = None,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Instantiate a pipeline template
    
    Creates a pipeline instance from a template with optional configuration overrides.
    """
    try:
        result = await controller.instantiate_template(template_name, config=config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to instantiate template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=Dict[str, Any])
async def validate_pipeline(
    pipeline_json: Dict[str, Any],
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Validate a pipeline definition
    
    Checks if a pipeline definition is valid without executing it.
    """
    try:
        from app.core.pipeline_engine.builder import PipelineBuilder
        
        # Try to build the pipeline to validate
        pipeline = PipelineBuilder.from_dict(pipeline_json).build()
        
        return {
            "valid": True,
            "nodes": len(pipeline.nodes),
            "edges": len(pipeline.edges),
            "message": "Pipeline definition is valid"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Pipeline definition is invalid"
        }