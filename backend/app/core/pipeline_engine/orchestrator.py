# app/core/pipeline_engine/orchestrator.py

import asyncio
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Import all components
from app.core.pipeline_engine.builder import PipelineBuilder
from app.core.pipeline_engine.retry_handler import RetryHandler
from app.core.pipeline_engine.models import Pipeline, NodeType
from app.core.pipeline_engine.executor import PipelineExecutor, ExecutionEvent
from app.core.pipeline_engine.scheduler import PipelineScheduler, PriorityScheduler
from app.core.pipeline_engine.dag_validator import DAGValidator
from app.core.pipeline_engine.state_manager import PipelineStateManager, RedisStateStorage
from app.core.execution.resource_manager import ResourceManager
from app.core.execution.async_executor import AsyncExecutor
from app.api.websocket import manager
from app.common.job_models import JobPriority

logger = logging.getLogger(__name__)


class ExecutionContext:
    """Tracks state of a single pipeline execution"""
    
    def __init__(self, execution_id: UUID, pipeline: Pipeline, user_id: Optional[str], 
                 priority: JobPriority, start_time: datetime):
        self.execution_id = execution_id
        self.pipeline = pipeline
        self.user_id = user_id
        self.priority = priority
        self.start_time = start_time
        self.end_time: Optional[datetime] = None
        self.status: str = "created"
        self.error: Optional[str] = None
        self.completed_nodes: List[str] = []
        self.failed_nodes: List[str] = []
        self.node_results: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}
        self.retry_counts: Dict[str, int] = {}
        self.result: Optional[Dict] = None


class PipelineOrchestrator:
    """
    Main orchestrator that connects all components
    Single source of truth for pipeline execution
    """
    
    def __init__(self, num_workers: int = 4):
        """
        Initialize all components and connect them
        
        Args:
            num_workers: Number of worker threads/processes
        """
        # Core components
        self.redis = RedisStateStorage()
        self.state_manager = PipelineStateManager(self.redis)
        self.scheduler = PipelineScheduler(PriorityScheduler())
        self.resource_manager = ResourceManager()
        self.retry_handler = RetryHandler()  # Use existing RetryHandler
        
        # Global pipeline builder - users add nodes to this
        self.pipeline_builder = PipelineBuilder()
        
        # Pipeline executor (passes retry_handler to handle retries)
        self.pipeline_executor = PipelineExecutor(
            state_manager=self.state_manager,
            scheduler=self.scheduler,
            retry_handler=self.retry_handler,  # Retry logic handled by RetryHandler
        )
        
        # Async execution
        self.async_executor = AsyncExecutor(self.pipeline_executor, num_workers)
        
        # Track state
        self.active_executions: Dict[UUID, ExecutionContext] = {}
        self._jobs: Dict[UUID, Any] = {}  # All job types
        
        # WebSocket connections
        self.websocket_connections: List[Any] = []
        
        # Register all job handlers
        self._register_all_handlers()
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _register_all_handlers(self):
        """Register handlers for all job types"""
        
        # Import handlers
        from app.core.pipeline_engine.handlers.data_collection_handler import DataCollectionHandler
        from app.core.pipeline_engine.handlers.preprocessing_handler import PreprocessingHandler
        from app.core.pipeline_engine.handlers.training_handler import TrainingHandler
        from app.core.pipeline_engine.handlers.finetuning_handler import FinetuningHandler
        from app.core.pipeline_engine.handlers.optimization_handler import OptimizationHandler
        from app.core.pipeline_engine.handlers.deployment_handler import DeploymentHandler
        from app.core.pipeline_engine.handlers.tokenization_handler import TokenizationHandler
        
        # Create handler instances (pass orchestrator reference)
        self.handlers = {
            "data_ingestion": DataCollectionHandler(self),
            "data_processing": PreprocessingHandler(self),
            "training": TrainingHandler(self),
            "finetuning": FinetuningHandler(self),
            "optimization": OptimizationHandler(self),
            "deployment": DeploymentHandler(self),
            "tokenization": TokenizationHandler(self),
        }
        
        # Register handlers with workers
        for node_type, handler in self.handlers.items():
            for worker in self.async_executor.workers:
                worker.register_handler(node_type, handler.execute)
        
        logger.info(f"Registered {len(self.handlers)} job handlers")


    def _setup_event_handlers(self):
        """Setup pipeline event handlers using decorator pattern"""
        
        @self.pipeline_executor.on(ExecutionEvent.NODE_COMPLETED)
        async def on_node_completed(data: Dict[str, Any]):
            """Handle node completion"""
            execution_id = data.get("execution_id")
            node_id = data.get("node_id") 
            result = data.get("result")
            
            # Validate required fields
            if execution_id is None or node_id is None:
                logger.error(f"Invalid NODE_COMPLETED event: missing execution_id or node_id")
                return
            
            # Convert to strings (handles UUID objects)
            execution_id = UUID(execution_id)
            node_id_str = str(node_id)
            
            logger.info(f"Node {node_id_str} completed for execution {execution_id}")
            
            # Update execution context
            if execution_id in self.active_executions:
                ctx = self.active_executions[execution_id]  # type: ignore
                ctx.completed_nodes.append(node_id_str)
                ctx.node_results[node_id_str] = result
                
                # Check if pipeline is complete
                if len(ctx.completed_nodes) == len(ctx.pipeline.nodes):
                    ctx.status = "completed"
                    ctx.end_time = datetime.now(timezone.utc)
                    await self._notify_execution_complete(execution_id, ctx)
            else:
                logger.warning(f"Execution {execution_id} not found in active executions")
            
            # Notify via WebSocket
            await self._broadcast_status({
                "type": "node_completed",
                "execution_id": execution_id,
                "node_id": node_id_str,
                "result": result
            })
        
        @self.pipeline_executor.on(ExecutionEvent.NODE_FAILED)
        async def on_node_failed(data: Dict[str, Any]):
            """Handle node failure"""
            execution_id = data.get("execution_id")
            node_id = data.get("node_id")
            error = data.get("error")
            
            # Validate required fields
            if execution_id is None or node_id is None:
                logger.error(f"Invalid NODE_FAILED event: missing execution_id or node_id")
                return
            
            # Convert to strings
            execution_id = UUID(execution_id)
            node_id_str = str(node_id)
            
            logger.error(f"Node {node_id_str} failed for execution {execution_id}: {error}")
            
            ctx = self.active_executions[execution_id]
            ctx.failed_nodes.append(node_id_str)
            ctx.errors[node_id_str] = str(error)
            ctx.status = "failed"
            ctx.end_time = datetime.now(timezone.utc)
            
            await self._notify_execution_failed(execution_id, ctx)
                   
            
            # Notify via WebSocket
            await self._broadcast_status({
                "type": "node_failed",
                "execution_id": execution_id,
                "node_id": node_id_str,
                "error": str(error),
                "retry_count": ctx.retry_counts.get(node_id_str, 0) if execution_id in self.active_executions else 0
            })
        
        @self.pipeline_executor.on(ExecutionEvent.PIPELINE_STARTED)
        async def on_pipeline_started(data: Dict[str, Any]):
            """Handle pipeline start"""
            execution_id = data.get("execution_id")
            pipeline_name = data.get("pipeline_name")
            
            if execution_id is None:
                logger.error("Invalid PIPELINE_STARTED event: missing execution_id")
                return
            
            execution_id = UUID(execution_id)
            
            logger.info(f"Pipeline {pipeline_name} started (execution: {execution_id})")
            
            if execution_id in self.active_executions:
                self.active_executions[execution_id].status = "running"
                self.active_executions[execution_id].start_time = datetime.now(timezone.utc)
            
            await self._broadcast_status({
                "type": "pipeline_started",
                "execution_id": execution_id,
                "pipeline_name": pipeline_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        @self.pipeline_executor.on(ExecutionEvent.PIPELINE_COMPLETED)
        async def on_pipeline_completed(data: Dict[str, Any]):
            """Handle pipeline completion"""
            execution_id = data.get("execution_id")
            status = data.get("status", "completed")
            
            if execution_id is None:
                logger.error("Invalid PIPELINE_COMPLETED event: missing execution_id")
                return
            
            execution_id_str = UUID(execution_id)
            
            logger.info(f"Pipeline {execution_id_str} completed with status: {status}")
            
            if execution_id_str in self.active_executions:
                self.active_executions[execution_id_str].status = status
                self.active_executions[execution_id_str].end_time = datetime.now(timezone.utc)
            
            await self._broadcast_status({
                "type": "pipeline_completed",
                "execution_id": execution_id_str,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        @self.pipeline_executor.on(ExecutionEvent.PIPELINE_FAILED)
        async def on_pipeline_failed(data: Dict[str, Any]):
            """Handle pipeline failure"""
            execution_id = data.get("execution_id")
            error = data.get("error")
            
            if execution_id is None:
                logger.error("Invalid PIPELINE_FAILED event: missing execution_id")
                return
            
            execution_id_str = UUID(execution_id)
            
            logger.error(f"Pipeline {execution_id_str} failed: {error}")
            
            if execution_id_str in self.active_executions:
                self.active_executions[execution_id_str].status = "failed"
                self.active_executions[execution_id_str].end_time = datetime.now(timezone.utc)
                self.active_executions[execution_id_str].error = str(error)
            
            await self._broadcast_status({
                "type": "pipeline_failed",
                "execution_id": execution_id_str,
                "error": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    # ==================== Job Management ====================
    
    async def execute_job(self, job_id: UUID) -> Dict[str, Any]:
        """Execute a job by ID"""
        job = self._jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return {
                "error": "Job not found"
            }
        return {
            "message": "Job execution started",
            "job_id": str(job_id),
            "execution_id": str(job.execution_id) if hasattr(job, 'execution_id') else None
        }
        print(f"Executing job {job_id} of type {job.job_type.value}")
        # # Convert job to pipeline and execute
        # pipeline = job.to_pipeline()
        # asyncio.create_task(self.execute_pipeline(pipeline, user_id=job.user_id, priority=job.priority))


    def register_job(self, job: Any, metadata: Dict[str, Any]) -> UUID:
        """
        Register a job in the orchestrator
        
        Args:
            job: Job object (DataCollectionJob, TrainingJob, etc.)
            metadata: Node metadata
        
        Returns:
            Job ID
        """

         # Add data collection node to pipeline
        self.add_node_to_pipeline(
            name=metadata["name"],
            node_type=metadata["node_type"],
            resources=metadata["resources"],
            metadata=metadata["metadata"],
            retry_policy=metadata["retry_policy"],
            position=metadata["position"],
            job = job
        )
        self._jobs[job.job_id] = job
        logger.info(f"Job {job.job_id} registered with type {job.job_type.value}")
        return job.job_id
    
    def get_job(self, job_id: UUID) -> Optional[Any]:
        """Get job by ID"""
        return self._jobs.get(job_id)
    
    def update_job(self, job_id: UUID, **kwargs) -> bool:
        """Update job attributes"""
        job = self._jobs.get(job_id)
        if job:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = datetime.now(timezone.utc)
            return True
        return False
    
    def list_jobs(
        self,
        job_type: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List jobs with filters"""
        jobs_list = list(self._jobs.values())
        
        # Sort by creation time (newest first)
        jobs_list.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply filters
        if job_type:
            jobs_list = [j for j in jobs_list if j.job_type.value == job_type]
        
        if status:
            jobs_list = [j for j in jobs_list if j.status.value == status]
        
        if user_id:
            jobs_list = [j for j in jobs_list if j.user_id == user_id]
        
        total = len(jobs_list)
        paginated_jobs = jobs_list[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [self._job_to_dict(job) for job in paginated_jobs]
        }
    
    def _job_to_dict(self, job: Any) -> Dict[str, Any]:
        """Convert job to dictionary for listing"""
        from app.common.job_models import (
            DataCollectionJob, TrainingJob, FinetuningJob, DeploymentJob
        )
        
        base_dict = {
            "job_id": str(job.job_id),
            "job_type": job.job_type.value,
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "user_id": job.user_id,
            "tags": job.tags
        }
        
        # Add type-specific fields
        if isinstance(job, DataCollectionJob):
            base_dict.update({
                "source": job.source,
                "topic": job.topic,
                "documents_count": len(job.documents) if job.documents else 0
            })
        elif isinstance(job, TrainingJob):
            base_dict.update({
                "model_name": job.model_name,
                "model_type": job.model_type
            })
        elif isinstance(job, FinetuningJob):
            base_dict.update({
                "base_model_name": job.base_model_name,
                "strategy_type": job.strategy_type
            })
        elif isinstance(job, DeploymentJob):
            base_dict.update({
                "serving_framework": job.serving_framework,
                "endpoint": job.endpoint
            })
        
        return base_dict
    
    # ==================== Pipeline Builder Operations ====================
    
    def add_node_to_pipeline(
        self,
        name: str,
        node_type: NodeType,
        resources: Dict,
        retry_policy: Dict,
        metadata: Dict,
        position: tuple,
        job: Optional[Any] = None
    ) -> 'PipelineOrchestrator':
        """
        Add a node to the global pipeline
        
        Args:
            node_id: Unique node identifier
            name: Display name
            node_type: Type of node
            config: Node configuration parameters
            resources: Resource requirements
            retry_policy: Retry configuration (uses RetryHandler)
            metadata: Additional metadata
            position: Visual position (x, y)
        
        Returns:
            Self for method chaining
        """
        self.pipeline_builder.add_node(
            name=name,
            node_type=node_type,
            resources=resources,
            retry_policy=retry_policy or {"max_retries": 3, "strategy": "exponential"},
            metadata=metadata,
            position=position,
            job = job
        )
        return self
    
    def add_edge_to_pipeline(
        self, 
        source: str, 
        target: str, 
        condition: str,
        label: str
    ) -> 'PipelineOrchestrator':
        """Add an edge to the global pipeline"""
        self.pipeline_builder.add_edge(source, target, condition, label)
        return self
    
    def clear_pipeline(self) -> 'PipelineOrchestrator':
        """Clear the current pipeline"""
        # self.pipeline_builder = PipelineBuilder()
        return self
    
    def get_pipeline(self) -> Pipeline:
        """Get the current pipeline"""
        return self.pipeline_builder.build()
    
    # ==================== Execution Methods ====================
    
    async def execute_current_pipeline(
        self,
        user_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> Dict[str, Any]:
        """Execute the current pipeline built by the user"""
        pipeline = self.pipeline_builder.build()
        return await self.execute_pipeline(pipeline, user_id, priority)
    
    async def execute_pipeline(
        self,
        pipeline: Pipeline,
        user_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> Dict[str, Any]:
        """Execute a pipeline"""
        
        # Validate
        validator = DAGValidator(pipeline)
        is_valid, errors = validator.validate()
        if not is_valid:
            raise ValueError(f"Invalid pipeline: {errors}")
        
        # Create execution context
        execution_id = uuid4()
        execution_context = ExecutionContext(
            execution_id=execution_id,
            pipeline=pipeline,
            user_id=user_id,
            priority=priority,
            start_time=datetime.now(timezone.utc)
        )
        self.active_executions[execution_id] = execution_context
        
        logger.info(f"Created execution {execution_id} for pipeline {pipeline.name}")
        
        # Save initial state
        await self.state_manager.save_state(execution_id, pipeline)
        
        # Start execution
        asyncio.create_task(
            self._execute_pipeline_async(execution_id, pipeline, execution_context)
        )
        
        return {
            "execution_id": execution_id,
            "pipeline_id": pipeline.id,
            "pipeline_name": pipeline.name,
            "status": "started",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _execute_pipeline_async(
        self,
        execution_id: UUID,
        pipeline: Pipeline,
        context: ExecutionContext
    ):
        """Execute pipeline asynchronously"""
        try:
            context.status = "running"
            await self._broadcast_status({
                "type": "execution_started",
                "execution_id": str(execution_id),
                "pipeline_name": pipeline.name
            })
            
            # Execute using pipeline executor (retries handled by RetryHandler internally)
            result = await self.pipeline_executor.execute_pipeline(
                pipeline=pipeline,
                execution_id=execution_id,
                resource_availability = await self.resource_manager.get_available_resources()
            )
            
            context.status = result["status"]
            context.end_time = datetime.now(timezone.utc)
            context.result = result
            
            await self.state_manager.save_state(execution_id, pipeline)
            
            await self._broadcast_status({
                "type": "execution_completed",
                "execution_id": str(execution_id),
                "status": result["status"],
                "duration": (context.end_time - context.start_time).total_seconds()
            })
            
            logger.info(f"Execution {execution_id} completed with status: {result['status']}")
            
        except Exception as e:
            logger.exception(f"Execution {execution_id} failed: {e}")
            context.status = "failed"
            context.error = str(e)
            
            # Update associated job
            for job_id, job in self._jobs.items():
                if hasattr(job, 'execution_id') and job.execution_id == execution_id:
                    job.mark_failed(str(e))
                    await manager.notify_job_update(str(job_id), {
                        "status": "failed",
                        "error": str(e)
                    })
                    break
            
            await self._broadcast_status({
                "type": "execution_failed",
                "execution_id": str(execution_id),
                "error": str(e)
            })
        
        finally:
            await self.state_manager.cleanup_checkpoints(execution_id)
    
    async def get_execution_status(self, execution_id: UUID) -> Dict[str, Any]:
        """Get execution status"""
        if execution_id not in self.active_executions:
            pipeline = await self.state_manager.load_state(execution_id)
            if pipeline:
                return {
                    "execution_id": execution_id,
                    "status": "completed",
                    "pipeline": pipeline.name
                }
            return {"error": "Execution not found"}
        
        context = self.active_executions[execution_id]
        return {
            "execution_id": execution_id,
            "status": context.status,
            "pipeline_name": context.pipeline.name,
            "completed_nodes": len(context.completed_nodes),
            "failed_nodes": len(context.failed_nodes),
            "total_nodes": len(context.pipeline.nodes),
            "progress": len(context.completed_nodes) / len(context.pipeline.nodes) * 100 if context.pipeline.nodes else 0,
            "start_time": context.start_time.isoformat(),
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "node_results": context.node_results,
            "errors": context.errors
        }
    
    async def cancel_execution(self, execution_id: UUID) -> bool:
        """Cancel a running execution"""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            if context.status == "running":
                cancelled = self.pipeline_executor.cancel_pipeline(execution_id)
                if cancelled:
                    context.status = "cancelled"
                    
                    # Update associated job
                    for job_id, job in self._jobs.items():
                        if hasattr(job, 'execution_id') and job.execution_id == execution_id:
                            job.mark_cancelled()
                            await manager.notify_job_update(str(job_id), {
                                "status": "cancelled"
                            })
                            break
                    
                    logger.info(f"Execution {execution_id} cancelled")
                return cancelled
        return False
    
    # ==================== Resource Management ====================
    async def get_execution_logs(self, execution_id: UUID, node_id:str="*") -> Optional[List[str]]:  
        """Get execution logs"""
        return await self.state_manager.get_logs(execution_id)

    # ==================== Notification Methods ====================

    async def _broadcast_status(self, status_update: Dict[str, Any]):
        """Broadcast status updates to WebSocket clients"""
        logger.debug(f"Status update: {status_update}")
        # WebSocket broadcast would go here
        for connection in self.websocket_connections:
            try:
                await connection.send_json(status_update)
            except Exception as e:
                logger.error(f"Failed to send status update: {e}")
    
    async def _notify_execution_complete(self, execution_id: UUID, context: ExecutionContext):
        """Notify execution completion"""
        logger.info(f"Execution {execution_id} complete: {len(context.completed_nodes)} nodes succeeded")
    
    async def _notify_execution_failed(self, execution_id: UUID, context: ExecutionContext):
        """Notify execution failure"""
        logger.error(f"Execution {execution_id} failed: {len(context.failed_nodes)} nodes failed")

    async def _calculate_average_duration(self, user_id: Optional[str] = None) -> float:
        """Calculate average duration of completed executions"""
        durations = []
        for ctx in self.active_executions.values():
            if ctx.status == "completed" and (user_id is None or ctx.user_id == user_id):
                if ctx.end_time and ctx.start_time:
                    durations.append((ctx.end_time - ctx.start_time).total_seconds())
        return sum(durations) / len(durations) if durations else 0.0
    
    # ==================== Statistics Methods ====================
    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get execution statistics"""
        stats = {
            "total_executions": len(self.active_executions),
            "running_executions": sum(1 for ctx in self.active_executions.values() if ctx.status == "running"),
            "completed_executions": sum(1 for ctx in self.active_executions.values() if ctx.status == "completed"),
            "failed_executions": sum(1 for ctx in self.active_executions.values() if ctx.status == "failed"),
            "average_duration": self._calculate_average_duration(user_id)
        }
        return stats
    # ==================== Lifecycle Methods ====================
      
    async def start(self):
        """Start all workers"""
        await self.async_executor.start()
        logger.info("Pipeline orchestrator started")
    
    async def stop(self):
        """Stop all workers"""
        await self.async_executor.stop()
        logger.info("Pipeline orchestrator stopped")