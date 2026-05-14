# app/controllers/pipeline_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging
from datetime import datetime, timezone

from app.common.job_models import PipelineJob, JobStatus, JobFactory, JobPriority
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.builder import PipelineBuilder
from app.core.pipeline_engine.config import PipelineConfig
from app.core.pipeline_engine.models import NodeType, Pipeline
from app.api.websocket import manager

logger = logging.getLogger(__name__)


class PipelineController(BaseController):
    """Controller for pipeline operations"""

    def __init__(self, orchestrator):
        super().__init__(orchestrator)
    
    async def add_job(
        self,
        *,
        config: PipelineConfig,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_execute: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a pipeline execution job
        
        Args:
            config: Pipeline configuration
            user_id: User ID
            tags: Optional tags for categorization
            auto_execute: Whether to automatically execute the job
        
        Returns:
            Job information
        """
        try:
            # Create pipeline job using factory
            job = JobFactory.create_pipeline_job(pipeline_config=config, **kwargs)
            metadata = JobFactory.create_job_metadata(
                name=f"Pipeline execution",
                node_type=NodeType.PIPELINE_EXE,
                job=job,
                description=f"Executing pipeline...",
                config=config.dict(),
                tags=tags or []
            )
            
            # Register job with orchestrator
            return await self.register(job, metadata, message="Pipeline job created successfully", auto_execute=auto_execute)
            
        except ValueError as e:
            logger.error(f"Failed to create pipeline job: {e}")
            raise

    async def validate_pipeline(self, pipeline_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a pipeline definition without executing it
        
        Args:
            pipeline_json: Pipeline definition as a dictionary
        
        Returns:
            Validation result
        """
        try:
            pipeline = self._pipeline_from_definition(pipeline_json)
            self.orchestrator.pipeline_optimizer.optimize(pipeline)
            return {
                "valid": True,
                "nodes": len(pipeline_json.get("nodes", [])),
                "edges": len(pipeline_json.get("edges", [])),
                "errors": []
            }
           
            
        except ValueError as e:
            logger.error(f"Pipeline validation failed: {e}")
            raise

    async def execute_pipeline_definition(
        self,
        pipeline_json: Dict[str, Any],
        user_id: Optional[str],
        priority: JobPriority
    ) -> Dict[str, Any]:
        """Execute a pipeline definition supplied by the API client."""
        if not pipeline_json:
            return await self.execute_pipeline(user_id=user_id or "system", priority=priority)

        pipeline = self._pipeline_from_definition(pipeline_json)
        result = await self.orchestrator._execute_pipeline(pipeline, user_id=user_id, priority=priority)
        return {
            "execution_id": str(result.get("execution_id")),
            "job_id": str(result.get("pipeline_id") or pipeline.id),
            "status": result.get("status", "started"),
            "message": "Pipeline execution started successfully",
            "progress": 0,
            "optimization": result.get("optimization"),
            "execution_plan": result.get("execution_plan"),
            "generated_code_path": result.get("generated_code_path"),
        }

    def _pipeline_from_definition(self, pipeline_json: Dict[str, Any]) -> Pipeline:
        return Pipeline.from_dict({
            "name": pipeline_json.get("name", "Ad hoc Pipeline"),
            "description": pipeline_json.get("description", "Pipeline submitted from the UI"),
            "nodes": [
                {
                    "id": node["id"],
                    "name": node.get("name", node["id"]),
                    "type": self._frontend_node_type(node.get("type", "custom")),
                    "config": {"parameters": node.get("config", {})},
                    "metadata": node.get("metadata", {}),
                    "job": self._job_from_node(node),
                }
                for node in pipeline_json.get("nodes", [])
            ],
            "edges": pipeline_json.get("edges", []),
            "tags": pipeline_json.get("tags", []),
        })

    def _frontend_node_type(self, stage_type: str) -> str:
        """Map UI stage identifiers to backend node types."""
        return {
            "data_collection": NodeType.DATA_INGESTION.value,
            "preprocessing": NodeType.DATA_PROCESSING.value,
            "tokenization": NodeType.TOKENIZATION.value,
            "training": NodeType.MODEL_TRAINING.value,
            "finetuning": NodeType.MODEL_FINETUNING.value,
            "evaluation": NodeType.MODEL_EVALUATION.value,
            "optimization": NodeType.OPTIMIZATION.value,
            "deployment": NodeType.MODEL_DEPLOYMENT.value,
        }.get(stage_type, stage_type)

    def _job_from_node(self, node: Dict[str, Any]):
        job_id = node.get("job_id") or node.get("jobId")
        if not job_id:
            return None
        try:
            return self._get_job(UUID(str(job_id)))
        except ValueError:
            logger.warning("Ignoring invalid pipeline node job_id: %s", job_id)
            return None
    async def get_execution_logs(
        self,
        execution_id: UUID,
        node_id: Optional[str] = None,
        tail: int = 100
    ) -> Dict[str, Any]:
        """
        Get logs for an execution
        
        Args:
            execution_id: Execution ID
            node_id: Optional node ID to filter logs
            tail: Number of lines to return from the end
        
        Returns:
            Logs
        """
        try:
            logs = await self.orchestrator.get_execution_logs(execution_id, node_id=node_id or "*")
            
            # Apply tail if logs is a list
            if isinstance(logs, list) and len(logs) > tail:
                logs = logs[-tail:]
            
            return {
                "execution_id": str(execution_id),
                "node_id": node_id,
                "logs": logs,
                "tail": tail
            }
        except Exception as e:
            logger.error(f"Failed to get execution logs: {e}")
            return {"error": str(e)}
    
    async def get_pipeline_templates(self) -> Dict[str, Any]:
        """
        Get available pipeline templates
        
        Returns:
            Dictionary of templates
        """
        return {
            "rag": {
                "name": "RAG Pipeline",
                "description": "Retrieval-Augmented Generation pipeline",
                "nodes": 6,
                "tags": ["rag", "retrieval", "generation"]
            },
            "classification": {
                "name": "Classification Pipeline",
                "description": "Text classification pipeline",
                "nodes": 6,
                "tags": ["classification", "text"]
            },
            "lora_finetuning": {
                "name": "LoRA Fine-tuning",
                "description": "Parameter-efficient fine-tuning pipeline",
                "nodes": 6,
                "tags": ["finetuning", "lora", "efficient"]
            },
            "hyperparameter_tuning": {
                "name": "Hyperparameter Tuning",
                "description": "Automated hyperparameter search pipeline",
                "nodes": 4,
                "tags": ["tuning", "optimization", "search"]
            },
            "data_preprocessing": {
                "name": "Data Preprocessing",
                "description": "End-to-end data preprocessing pipeline",
                "nodes": 5,
                "tags": ["preprocessing", "cleaning", "transformation"]
            },
            "model_deployment": {
                "name": "Model Deployment",
                "description": "Model deployment pipeline with optimization",
                "nodes": 4,
                "tags": ["deployment", "optimization", "serving"]
            }
        }
    
    async def instantiate_template(
        self,
        template_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Instantiate a pipeline template
        
        Args:
            template_name: Name of the template
            config: Configuration overrides
        
        Returns:
            Instantiated pipeline
        """
        from app.core.pipeline_engine.builder import PipelineTemplate
        
        templates = {
            "rag": PipelineTemplate.rag_pipeline,
            "classification": PipelineTemplate.classification_pipeline,
            "lora_finetuning": PipelineTemplate.lora_finetuning_pipeline,
            "hyperparameter_tuning": PipelineTemplate.hyperparameter_tuning_pipeline,
            "data_preprocessing": PipelineTemplate.data_preprocessing_pipeline,
            "model_deployment": PipelineTemplate.model_deployment_pipeline
        }
        
        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        try:
            builder = templates[template_name]()
            
            # Apply configuration overrides if provided
            if config:
                builder = self._apply_template_config(builder, config)
            
            pipeline = builder.build()
            
            return {
                "template_name": template_name,
                "pipeline": {
                    "nodes": [node.__dict__ for node in pipeline.nodes],
                    "edges": [edge.__dict__ for edge in pipeline.edges],
                },
                "nodes": len(pipeline.nodes),
                "edges": len(pipeline.edges)
            }
        except Exception as e:
            logger.error(f"Failed to instantiate template: {e}")
            raise

    def _apply_template_config(self, builder, config: Dict[str, Any]):
        """Apply configuration overrides to template builder"""
        # This is a placeholder - implement based on your builder's configuration methods
        # You might want to add methods to your builder to allow configuration
        for key, value in config.items():
            if hasattr(builder, key):
                setattr(builder, key, value)
        return builder
