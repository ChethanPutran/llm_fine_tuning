# app/controllers/pipeline_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging
from datetime import datetime, timezone

from app.common.job_models import PipelineJob, JobStatus, JobFactory, JobPriority
from app.controllers.base_controller import BaseController
from app.core.pipeline_engine.builder import PipelineBuilder
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
        pipeline_json: Dict[str, Any],
        priority: str = "NORMAL",
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a pipeline execution job
        
        Args:
            pipeline_json: Pipeline definition in JSON format
            priority: Execution priority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)
            user_id: User ID
            tags: Optional tags for categorization
        
        Returns:
            Job information
        """
        try:
            # Map priority
            priority_map = {
                "CRITICAL": JobPriority.CRITICAL,
                "HIGH": JobPriority.HIGH,
                "NORMAL": JobPriority.NORMAL,
                "LOW": JobPriority.LOW,
                "BACKGROUND": JobPriority.BACKGROUND
            }
            job_priority = priority_map.get(priority.upper(), JobPriority.NORMAL)
            
            # Reconstruct pipeline from JSON to validate
            try:
                pipeline = PipelineBuilder.from_dict(pipeline_json).build()
            except Exception as e:
                raise ValueError(f"Invalid pipeline definition: {e}")
            
            metadata = {
                "node_id": "pipeline_executor",
                "name": f"Pipeline Execution - {len(pipeline.nodes)} nodes",
                "node_type": NodeType.CUSTOM,
                "resources": {"cpu": 2, "memory_gb": 4},
                "metadata": {
                    "pipeline_json": pipeline_json,
                    "priority": job_priority.value,
                    "nodes_count": len(pipeline.nodes),
                    "edges_count": len(pipeline.edges)
                },
                "retry_policy": kwargs.get("retry_policy", {"retries": 1, "delay_seconds": 0}),
                "position": kwargs.get("position", (0, 0))
            }
            
            # Create pipeline job using factory
            job = JobFactory.create_pipeline_job(
                pipeline_json=pipeline_json,
                priority=job_priority,
                user_id=user_id,
                tags=tags or ["pipeline"]
            )
            
            # Register job with orchestrator
            self.orchestrator.register_job(job, metadata)
            
            return {
                "job_id": str(job.job_id),
                "message": "Pipeline job created successfully",
                "nodes": len(pipeline.nodes),
                "edges": len(pipeline.edges)
            }
            
        except ValueError as e:
            logger.error(f"Failed to create pipeline job: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create pipeline job: {e}")
            raise
    
    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a registered pipeline job
        
        Args:
            job_id: Job ID to execute
        
        Returns:
            Execution result information
        """
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                logger.error(f"Job {job_id} not found for execution")
                return {"error": "Job not found"}
            
            # Execute the job using orchestrator
            execution_result = await self.orchestrator.execute_job(job.job_id)
            
            return {
                "job_id": str(job.job_id),
                "execution_id": str(execution_result.get("execution_id", "")),
                "message": "Pipeline execution started successfully"
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return {"error": "Invalid job ID"}
        except Exception as e:
            logger.error(f"Failed to execute pipeline job: {e}")
            return {"error": "Failed to execute job"}
    
    async def execute_pipeline(
        self,
        *,
        pipeline_json: Dict[str, Any],
        user_id: Optional[str] = None,
        priority: str = "NORMAL",
        auto_register: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a pipeline directly (create and execute in one step)
        
        Args:
            pipeline_json: Pipeline definition in JSON format
            user_id: User ID
            priority: Execution priority
            auto_register: Whether to register the job
        
        Returns:
            Execution result
        """
        try:
            if auto_register:
                # Create job first
                job_result = await self.add_job(
                    pipeline_json=pipeline_json,
                    priority=priority,
                    user_id=user_id,
                    tags=["direct_execution"]
                )
                job_id = job_result.get("job_id")
                
                if not job_id:
                    raise ValueError("Failed to create job")
                
                # Execute the job
                execution_result = await self.execute_job(job_id)
                
                return {
                    "job_id": job_id,
                    "execution_id": execution_result.get("execution_id"),
                    "status": "started",
                    "message": "Pipeline execution started"
                }
            else:
                # Execute directly without registering
                # Map priority
                priority_map = {
                    "CRITICAL": JobPriority.CRITICAL,
                    "HIGH": JobPriority.HIGH,
                    "NORMAL": JobPriority.NORMAL,
                    "LOW": JobPriority.LOW,
                    "BACKGROUND": JobPriority.BACKGROUND
                }
                job_priority = priority_map.get(priority.upper(), JobPriority.NORMAL)
                
                # Reconstruct pipeline from JSON
                pipeline = PipelineBuilder.from_dict(pipeline_json).build()
                
                # Execute pipeline
                result = await self.orchestrator.execute_pipeline(
                    pipeline=pipeline,
                    user_id=user_id,
                    priority=job_priority
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to execute pipeline: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pipeline job status
        
        Args:
            job_id: Job ID
        
        Returns:
            Job status information
        """
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    return None
            
            # Get execution status if execution exists
            execution_status = None
            if job.execution_id:
                execution_status = await self.orchestrator.get_execution_status(job.execution_id)
            
            return {
                "job_id": str(job.job_id),
                "job_type": job.job_type.value,
                "execution_id": str(job.execution_id) if job.execution_id else None,
                "status": job.status.value if hasattr(job.status, 'value') else job.status,
                "progress": job.progress,
                "result": job.result,
                "error": job.error,
                "pipeline_json": job.pipeline_json,
                "priority": job.priority.value if hasattr(job.priority, 'value') else str(job.priority),
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "updated_at": job.updated_at.isoformat(),
                "user_id": job.user_id,
                "tags": job.tags,
                "execution_details": execution_status
            }
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pipeline job
        
        Args:
            job_id: Job ID
        
        Returns:
            True if cancelled successfully
        """
        try:
            job_uuid = UUID(job_id)
            job = self._get_job(job_uuid)
            
            if not job:
                job = self.orchestrator.get_job(job_uuid)
                if not job:
                    logger.warning(f"Job {job_id} not found")
                    return False
            
            # Check if job can be cancelled
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                logger.warning(f"Job {job_id} cannot be cancelled in status {job.status}")
                return False
            
            # Cancel execution if running
            if job.execution_id:
                cancelled = await self.orchestrator.cancel_execution(job.execution_id)
                if cancelled:
                    job.mark_cancelled()
                    self._update_job(job.job_id, status=job.status, completed_at=job.completed_at)
                    await manager.notify_job_update(job_id, {
                        "status": "cancelled",
                        "message": "Pipeline job cancelled by user"
                    })
                    logger.info(f"Pipeline job {job_id} cancelled successfully")
                    return True
            else:
                # Job hasn't started execution yet
                job.mark_cancelled()
                self._update_job(job.job_id, status=job.status, completed_at=job.completed_at)
                await manager.notify_job_update(job_id, {
                    "status": "cancelled",
                    "message": "Pipeline job cancelled before execution"
                })
                logger.info(f"Pipeline job {job_id} cancelled before execution")
                return True
            
            return False
            
        except ValueError:
            logger.error(f"Invalid job ID: {job_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            return False
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        List pipeline jobs with filters
        
        Args:
            status: Filter by status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            user_id: Filter by user ID
        
        Returns:
            Dictionary with total count and list of jobs
        """
        # Get all jobs from orchestrator
        orchestrator_jobs = self.orchestrator.list_jobs(
            job_type="pipeline",
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Combine with local jobs
        jobs_list = list(self._jobs.values())
        
        # Add orchestrator jobs
        for job_dict in orchestrator_jobs.get("jobs", []):
            job_id = UUID(job_dict["job_id"])
            if job_id not in self._jobs:
                # Create job object from dict
                job = PipelineJob(
                    job_id=job_id,
                    pipeline_json=job_dict.get("pipeline_json", {}),
                    status=JobStatus(job_dict["status"]),
                    progress=job_dict.get("progress", 0),
                    created_at=datetime.fromisoformat(job_dict["created_at"])
                )
                jobs_list.append(job)
        
        # Sort by creation time (newest first)
        jobs_list.sort(key=lambda x: x.created_at, reverse=True)
        
        total = len(jobs_list)
        paginated_jobs = jobs_list[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [self._job_to_dict(job) for job in paginated_jobs]
        }
    
    async def get_execution_status(self, execution_id: UUID) -> Dict[str, Any]:
        """
        Get execution status directly
        
        Args:
            execution_id: Execution ID
        
        Returns:
            Execution status
        """
        try:
            status = await self.orchestrator.get_execution_status(execution_id)
            return status
        except Exception as e:
            logger.error(f"Failed to get execution status: {e}")
            return {"error": str(e)}
    
    async def cancel_execution(self, execution_id: UUID) -> Dict[str, Any]:
        """
        Cancel an execution directly
        
        Args:
            execution_id: Execution ID
        
        Returns:
            Cancellation result
        """
        try:
            cancelled = await self.orchestrator.cancel_execution(execution_id)
            return {"cancelled": cancelled, "execution_id": str(execution_id)}
        except Exception as e:
            logger.error(f"Failed to cancel execution: {e}")
            return {"error": str(e)}
    
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
                    "metadata": pipeline.metadata
                },
                "nodes": len(pipeline.nodes),
                "edges": len(pipeline.edges)
            }
        except Exception as e:
            logger.error(f"Failed to instantiate template: {e}")
            raise
    
    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about pipeline jobs
        
        Args:
            user_id: Filter by user ID
        
        Returns:
            Statistics dictionary
        """
        jobs_list = list(self._jobs.values())
        
        if user_id:
            jobs_list = [j for j in jobs_list if j.user_id == user_id]
        
        # Count by status
        status_counts = {}
        for status in JobStatus:
            count = len([j for j in jobs_list if j.status == status])
            if count > 0:
                status_counts[status.value] = count
        
        # Count by priority
        priority_counts = {}
        for job in jobs_list:
            priority = job.priority.value if hasattr(job.priority, 'value') else str(job.priority)
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Calculate average execution time
        completed_jobs = [j for j in jobs_list if j.status == JobStatus.COMPLETED and j.started_at and j.completed_at]
        execution_times = []
        for job in completed_jobs:
            duration = (job.completed_at - job.started_at).total_seconds()
            execution_times.append(duration)
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_jobs": len(jobs_list),
            "by_status": status_counts,
            "by_priority": priority_counts,
            "completed_jobs": len([j for j in jobs_list if j.status == JobStatus.COMPLETED]),
            "failed_jobs": len([j for j in jobs_list if j.status == JobStatus.FAILED]),
            "running_jobs": len([j for j in jobs_list if j.status == JobStatus.RUNNING]),
            "queued_jobs": len([j for j in jobs_list if j.status == JobStatus.QUEUED]),
            "average_execution_time_seconds": avg_execution_time,
            "total_nodes_executed": sum(j.progress for j in jobs_list if j.progress)
        }
    
    def _apply_template_config(self, builder, config: Dict[str, Any]):
        """Apply configuration overrides to template builder"""
        # This is a placeholder - implement based on your builder's configuration methods
        # You might want to add methods to your builder to allow configuration
        for key, value in config.items():
            if hasattr(builder, key):
                setattr(builder, key, value)
        return builder