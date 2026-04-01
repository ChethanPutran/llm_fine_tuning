# app/api/routes/pipeline.py

from urllib import request

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID
import logging

from app.dependencies.controller import get_pipeline_controller
from app.controllers.pipeline_controller import PipelineController
from app.api.models import (ExecutePipelineRequest, CreatePipelineJobRequest, LogsResponse, RequestBase, TemplateListResponse, ValidationResponse)
from app.api.models import ExecutionStatusResponse, JobCreationResponse, JobStatusResponse, ListJobsResponse, StartCollectionRequest, StatisticsResponse 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post("/execute", response_model=ExecutionStatusResponse)
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
            user_id=request.user_id,
            priority=request.priority
        )
        return ExecutionStatusResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=JobCreationResponse)
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
            config=request.config,
            user_id="system",  # In real implementation, get from auth context
            tags=request.tags
        )
        
        # Auto-execute if requested
        if request.auto_execute and result.get("job_id"):
            job_id = result["job_id"]
            execution_result = await controller.execute_job(job_id)
            result["execution_id"] = execution_result.get("execution_id")
            result["execution_status"] = "started"
        
        return JobCreationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create pipeline job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{job_id}", response_model=ExecutionStatusResponse)
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
        
        return ExecutionStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute pipeline job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
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
    return JobStatusResponse(**status)


@router.get("/jobs", response_model=ListJobsResponse)
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
    return ListJobsResponse(**result)


@router.delete("/jobs/{job_id}", response_model=JobStatusResponse)
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
        return JobStatusResponse(**cancelled)
    raise HTTPException(status_code=400, detail="Job cannot be cancelled or not found")


@router.get("/executions/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Get execution status directly
    
    Returns status information for a specific execution.
    """
    status = await controller.get_execution_status(execution_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return ExecutionStatusResponse(**status)


@router.delete("/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def cancel_execution(
    execution_id: str,
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Cancel a running execution
    
    Cancels an active pipeline execution.
    """
    result = await controller.cancel_execution(execution_id)
    if not result:
        raise HTTPException(status_code=400, detail="Execution cannot be cancelled or not found")
    return ExecutionStatusResponse(**result)


@router.get("/executions/{execution_id}/logs", response_model=LogsResponse)
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
    return LogsResponse(**result)


@router.get("/statistics", response_model=StatisticsResponse)
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
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get pipeline statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=TemplateListResponse)
async def get_pipeline_templates(
    request: RequestBase = Field(..., description="Request model for pipeline templates"),
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Get available pipeline templates
    
    Returns a list of predefined pipeline templates.
    """
    try:
        templates = await controller.get_pipeline_templates()
        return TemplateListResponse(
            templates=templates,
            **request.dict()
            )
    except Exception as e:
        logger.error(f"Failed to get pipeline templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_name}", response_model=TemplateListResponse)
async def get_pipeline_template(
    template_name: str,
    request: RequestBase = Field(..., description="Request model for pipeline template"),
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
        
        return TemplateListResponse(
            templates={template_name: templates[template_name]},
            **request.dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_name}/instantiate", response_model=ExecutionStatusResponse)
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
        return ExecutionStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to instantiate template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidationResponse)
async def validate_pipeline(
    pipeline_json: Dict[str, Any],
    request: RequestBase = Field(..., description="Request model for pipeline validation"),
    controller: PipelineController = Depends(get_pipeline_controller)
):
    """
    Validate a pipeline definition
    
    Checks if a pipeline definition is valid without executing it.
    """
    try:
        await controller.validate_pipeline(pipeline_json)
        
        return ValidationResponse(
            valid=True,
            message="Pipeline definition is valid",
            **request.dict()
        )
    except Exception as e:
        return ValidationResponse(
            valid=False,
            message="Pipeline definition is invalid",
            error=str(e),
            **request.dict()
        )