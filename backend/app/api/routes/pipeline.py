# app/api/routes/pipeline.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID
import logging

from app.core.pipeline_engine.builder import PipelineBuilder
from app.core.pipeline_engine.orchestrator import PipelineOrchestrator
from app.common.job_models import JobPriority
from app.dependencies.controller import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


class ExecutePipelineRequest(BaseModel):
    """Request model for executing a pipeline"""
    pipeline_json: Dict[str, Any] = Field(..., description="Pipeline definition in JSON format")
    user_id: Optional[str] = Field(None, description="User ID who triggered execution")
    priority: str = Field("NORMAL", description="Execution priority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)")


@router.post("/execute", response_model=Dict[str, Any])
async def execute_pipeline(
    request: ExecutePipelineRequest,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """
    Execute a pipeline from JSON definition
    """
    try:
        # Reconstruct pipeline from JSON
        pipeline = PipelineBuilder.from_dict(request.pipeline_json).build()
        
        # Map priority
        priority_map = {
            "CRITICAL": JobPriority.CRITICAL,
            "HIGH": JobPriority.HIGH,
            "NORMAL": JobPriority.NORMAL,
            "LOW": JobPriority.LOW,
            "BACKGROUND": JobPriority.BACKGROUND
        }
        priority = priority_map.get(request.priority, JobPriority.NORMAL)
        
        # Execute pipeline
        result = await orchestrator.execute_pipeline(
            pipeline=pipeline,
            user_id=request.user_id,
            priority=priority
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}/status", response_model=Dict[str, Any])
async def get_execution_status(
    execution_id: UUID,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Get execution status"""
    status = await orchestrator.get_execution_status(execution_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@router.delete("/executions/{execution_id}", response_model=Dict[str, Any])
async def cancel_execution(
    execution_id: UUID,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Cancel a running execution"""
    cancelled = await orchestrator.cancel_execution(execution_id)
    return {"cancelled": cancelled, "execution_id": str(execution_id)}


@router.get("/executions/{execution_id}/logs", response_model=Dict[str, Any])
async def get_execution_logs(
    execution_id: UUID,
    node_id: Optional[str] = None,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Get logs for an execution"""
    # This would fetch logs from storage
    return {
        "execution_id": str(execution_id),
        "node_id": node_id,
        "logs": []  # TODO: Implement log retrieval
    }


@router.get("/templates", response_model=Dict[str, Any])
async def get_pipeline_templates():
    """Get available pipeline templates"""
    from app.core.pipeline_engine.builder import PipelineTemplate
    
    return {
        "rag": {
            "name": "RAG Pipeline",
            "description": "Retrieval-Augmented Generation pipeline",
            "nodes": 6
        },
        "classification": {
            "name": "Classification Pipeline",
            "description": "Text classification pipeline",
            "nodes": 6
        },
        "lora_finetuning": {
            "name": "LoRA Fine-tuning",
            "description": "Parameter-efficient fine-tuning",
            "nodes": 6
        },
        "hyperparameter_tuning": {
            "name": "Hyperparameter Tuning",
            "description": "Automated hyperparameter search",
            "nodes": 4
        }
    }



@router.post("/templates/{template_name}/instantiate", response_model=Dict[str, Any])
async def instantiate_template(
    template_name: str,
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator)
):
    """Instantiate a pipeline template"""
    from app.core.pipeline_engine.builder import PipelineTemplate
    
    templates = {
        "rag": PipelineTemplate.rag_pipeline,
        "classification": PipelineTemplate.classification_pipeline,
        "lora_finetuning": PipelineTemplate.lora_finetuning_pipeline,
        "hyperparameter_tuning": PipelineTemplate.hyperparameter_tuning_pipeline
    }
    
    if template_name not in templates:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    
    try:
        builder = templates[template_name]()
        pipeline = builder.build()
        
        return {
            "template_name": template_name,
            "pipeline": pipeline.__dict__,
            "nodes": len(pipeline.nodes),
            "edges": len(pipeline.edges)
        }
    except Exception as e:
        logger.error(f"Failed to instantiate template: {e}")
        raise HTTPException(status_code=500, detail=str(e))