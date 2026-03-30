# app/core/pipeline_engine/executor.py

import asyncio
import inspect
import logging
from typing import Dict, Any, Optional, Callable, List
from uuid import UUID
from datetime import datetime, timezone

from .models import Pipeline, PipelineNode, NodeStatus, ExecutionStatus, ExecutionEvent
from .scheduler import PipelineScheduler, SchedulingContext, FIFOScheduler
from .state_manager import PipelineStateManager
from .retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """
    Orchestrates pipeline execution following the Command pattern
    """
    
    def __init__(
        self,
        state_manager: PipelineStateManager,
        scheduler: Optional[PipelineScheduler] = None,
        retry_handler: Optional[RetryHandler] = None
    ):
        self.state_manager = state_manager
        self.scheduler = scheduler or PipelineScheduler(FIFOScheduler())
        self.retry_handler = retry_handler or RetryHandler()
        self._event_handlers: Dict[ExecutionEvent, List[Callable]] = {event: [] for event in ExecutionEvent}
        self._running_pipelines: Dict[UUID, asyncio.Task] = {}
        self._node_handlers: Dict[str, Callable] = {}
    
    def on(self, event: ExecutionEvent):
        """
        Decorator to register event handlers
        
        Usage:
            @executor.on(ExecutionEvent.NODE_COMPLETED)
            async def handler(data):
                print(data)
        
        Args:
            event: The event to listen for
        
        Returns:
            Decorator function
        """
        def decorator(handler: Callable) -> Callable:
            self._event_handlers[event].append(handler)
            logger.debug(f"Registered handler for event: {event.value}")
            return handler
        return decorator
    
    def register_handler(self, event: ExecutionEvent, handler: Callable) -> 'PipelineExecutor':
        """
        Direct method to register event handlers
        
        Usage:
            executor.register_handler(ExecutionEvent.NODE_COMPLETED, my_handler)
        
        Args:
            event: The event to listen for
            handler: The handler function
        
        Returns:
            Self for method chaining
        """
        self._event_handlers[event].append(handler)
        logger.debug(f"Registered handler for event: {event.value}")
        return self
    
    def once(self, event: ExecutionEvent):
        """
        Decorator to register a one-time event handler (executes only once)
        
        Usage:
            @executor.once(ExecutionEvent.PIPELINE_COMPLETED)
            async def handler(data):
                print("Pipeline completed!")
        
        Args:
            event: The event to listen for
        
        Returns:
            Decorator function
        """
        def decorator(handler: Callable) -> Callable:
            async def wrapper(data):
                await handler(data) if inspect.iscoroutinefunction(handler) else handler(data)
                if wrapper in self._event_handlers[event]:
                    self._event_handlers[event].remove(wrapper)
            
            self._event_handlers[event].append(wrapper)
            return handler
        return decorator
    
    def remove_handler(self, event: ExecutionEvent, handler: Callable) -> bool:
        """
        Remove a specific event handler
        
        Args:
            event: The event to remove handler from
            handler: The handler function to remove
        
        Returns:
            True if handler was removed, False otherwise
        """
        if handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)
            logger.debug(f"Removed handler for event: {event.value}")
            return True
        return False
    
    def clear_handlers(self, event: Optional[ExecutionEvent] = None):
        """
        Clear all handlers for an event or all events
        
        Args:
            event: Optional specific event to clear, clears all if None
        """
        if event:
            self._event_handlers[event].clear()
            logger.debug(f"Cleared handlers for event: {event.value}")
        else:
            for e in ExecutionEvent:
                self._event_handlers[e].clear()
            logger.debug("Cleared all event handlers")
    
    async def _emit_event(self, event: ExecutionEvent, data: Dict[str, Any]):
        """
        Emit event to all registered handlers
        
        Args:
            event: The event being emitted
            data: Event data
        """
        handlers = self._event_handlers.get(event, [])
        if not handlers:
            return
        
        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event.value}: {e}", exc_info=True)
    
    def register_node_handler(self, node_type: str, handler: Callable) -> 'PipelineExecutor':
        """
        Register a handler for a specific node type
        
        Args:
            node_type: Type of node (e.g., "data_ingestion", "model_training")
            handler: Async function to execute for this node type
        
        Returns:
            Self for method chaining
        """
        self._node_handlers[node_type] = handler
        logger.info(f"Registered handler for node type: {node_type}")
        return self
    
    async def execute_pipeline(
        self, 
        pipeline: Pipeline,
        execution_id: UUID,
        resource_availability: Dict[str, float]
    ) -> Dict[str, Any]:
        """Execute pipeline asynchronously"""
        
        resource_availability = resource_availability or {"cpu": 4, "memory_gb": 16}
        
        # Create task for this pipeline
        task = asyncio.current_task()
        if task:
            self._running_pipelines[execution_id] = task
        
        try:
            logger.info(f"Starting pipeline execution: {pipeline.name} (ID: {execution_id})")
            
            # Initialize execution
            await self._emit_event(ExecutionEvent.PIPELINE_STARTED, {
                "pipeline_id": pipeline.id,
                "execution_id": execution_id,
                "pipeline_name": pipeline.name
            })
            
            # Save initial state
            await self.state_manager.save_state(execution_id, pipeline)
            
            # Main execution loop
            completed_nodes: List[str] = []
            failed_nodes: List[str] = []
            running_nodes: List[str] = []
            node_results: Dict[str, Any] = {}
            
            total_nodes = len(pipeline.nodes)
            
            while len(completed_nodes) + len(failed_nodes) < total_nodes:
                # Create scheduling context
                context = SchedulingContext(
                    pipeline=pipeline,
                    completed_nodes=completed_nodes,
                    failed_nodes=failed_nodes,
                    running_nodes=running_nodes,
                    resource_availability=resource_availability,
                    node_results=node_results
                )
                
                # Get next nodes to execute
                nodes_to_execute = self.scheduler.schedule_pipeline(pipeline, context)
                
                if not nodes_to_execute:
                    if running_nodes:
                        await asyncio.sleep(1)
                        continue
                    else:
                        break
                
                # Execute nodes concurrently
                execution_tasks = []
                for node_id in nodes_to_execute:
                    node = pipeline.nodes[node_id]
                    task = self._execute_node(node, execution_id, pipeline)
                    execution_tasks.append(task)
                    running_nodes.append(node_id)
                
                # Wait for all nodes to complete
                results = await asyncio.gather(*execution_tasks, return_exceptions=True)
                
                # Process results
                for node_id, result in zip(nodes_to_execute, results):
                    if isinstance(result, Exception):
                        failed_nodes.append(node_id)
                        node_results[node_id] = {"error": str(result)}
                        await self._emit_event(ExecutionEvent.NODE_FAILED, {
                            "pipeline_id": pipeline.id,
                            "execution_id": execution_id,
                            "node_id": node_id,
                            "error": str(result)
                        })
                    else:
                        completed_nodes.append(node_id)
                        node_results[node_id] = result
                        await self._emit_event(ExecutionEvent.NODE_COMPLETED, {
                            "pipeline_id": pipeline.id,
                            "execution_id": execution_id,
                            "node_id": node_id,
                            "result": result
                        })
                    
                    running_nodes.remove(node_id)
                
                # Save state after each batch
                await self.state_manager.save_state(execution_id, pipeline)
            
            # Final status
            final_status = ExecutionStatus.COMPLETED if not failed_nodes else ExecutionStatus.FAILED
            
            await self._emit_event(ExecutionEvent.PIPELINE_COMPLETED, {
                "pipeline_id": pipeline.id,
                "execution_id": execution_id,
                "status": final_status.value,
                "completed_nodes": completed_nodes,
                "failed_nodes": failed_nodes,
                "node_results": node_results
            })
            
            return {
                "execution_id": execution_id,
                "status": final_status.value,
                "completed_nodes": completed_nodes,
                "failed_nodes": failed_nodes,
                "node_results": node_results,
                "total_nodes": total_nodes
            }
            
        except asyncio.CancelledError:
            await self._emit_event(ExecutionEvent.PIPELINE_FAILED, {
                "pipeline_id": pipeline.id,
                "execution_id": execution_id,
                "error": "Pipeline execution cancelled"
            })
            raise
            
        except Exception as e:
            logger.exception(f"Pipeline execution failed: {e}")
            await self._emit_event(ExecutionEvent.PIPELINE_FAILED, {
                "pipeline_id": pipeline.id,
                "execution_id": execution_id,
                "error": str(e)
            })
            raise
        
        finally:
            if execution_id in self._running_pipelines:
                del self._running_pipelines[execution_id]
    
    async def _execute_node(
        self, 
        node: PipelineNode, 
        execution_id: UUID,
        pipeline: Pipeline
    ) -> Any:
        """Execute a single pipeline node with retry logic"""
        
        node.status = NodeStatus.RUNNING
        node.start_time = datetime.now(timezone.utc)
        
        await self._emit_event(ExecutionEvent.NODE_STARTED, {
            "pipeline_id": pipeline.id,
            "execution_id": execution_id,
            "node_id": node.id,
            "node_name": node.name,
            "node_type": node.type.value
        })
        
        try:
            result = await self.retry_handler.execute_with_retry(
                func=self._run_node_task,
                args=(node, execution_id, pipeline),
                retry_config=node.config.retry_policy
            )
            
            node.status = NodeStatus.COMPLETED
            node.end_time = datetime.now(timezone.utc)
            node.metadata["output"] = result
            node.metadata["execution_time"] = (node.end_time - node.start_time).total_seconds()
            
            return result
            
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            node.end_time = datetime.now(timezone.utc)
            raise
    
    async def _run_node_task(
        self, 
        node: PipelineNode, 
        execution_id: UUID,
        pipeline: Pipeline
    ) -> Any:
        """Execute node using registered handler"""
        
        node_type = node.type.value
        
        if node_type not in self._node_handlers:
            raise ValueError(f"No handler registered for node type: {node_type}")
        
        handler = self._node_handlers[node_type]
        
        # Create job-like object for handler
        class JobProxy:
            def __init__(self, node, execution_id, pipeline):
                self.job_id = execution_id
                self.metadata = {
                    'node_config': node.config.parameters,
                    'node_id': node.id,
                    'pipeline_id': pipeline.id,
                    'execution_id': execution_id,
                    'node_type': node_type,
                    'node_name': node.name
                }
        
        job = JobProxy(node, execution_id, pipeline)
        
        if inspect.iscoroutinefunction(handler):
            return await handler(job)
        else:
            return handler(job)
    
    async def _get_event_type(self, job_type: str, action: str = 'complete', failed: bool = False) -> ExecutionEvent:
        """
        Determine the execution event type based on job type and action.
        
        Args:
            job_type: Type of job/stage being executed
            action: The action being performed ('start', 'complete', 'fail', etc.)
            failed: Whether the job has failed (overrides action if True)
            
        Returns:
            ExecutionEvent: Appropriate event type
        """
        # Action to event mapping
        action_map = {
            'start': {
                'data_collection': ExecutionEvent.NODE_STARTED,
                'preprocessing': ExecutionEvent.NODE_STARTED,
                'tokenization': ExecutionEvent.NODE_STARTED,
                'finetuning': ExecutionEvent.NODE_STARTED,
                'optimization': ExecutionEvent.NODE_STARTED,
                'deployment': ExecutionEvent.NODE_STARTED,
                'pipeline': ExecutionEvent.NODE_STARTED
            },
            'complete': {
                'data_collection': ExecutionEvent.NODE_COMPLETED,
                'preprocessing': ExecutionEvent.NODE_COMPLETED,
                'tokenization': ExecutionEvent.NODE_COMPLETED,
                'finetuning': ExecutionEvent.NODE_COMPLETED,
                'optimization': ExecutionEvent.NODE_COMPLETED,
                'deployment': ExecutionEvent.NODE_COMPLETED,
                'pipeline': ExecutionEvent.NODE_COMPLETED
            },
            'fail': {
                'data_collection': ExecutionEvent.NODE_FAILED,
                'preprocessing': ExecutionEvent.NODE_FAILED,
                'tokenization': ExecutionEvent.NODE_FAILED,
                'finetuning': ExecutionEvent.NODE_FAILED,
                'optimization': ExecutionEvent.NODE_FAILED,
                'deployment': ExecutionEvent.NODE_FAILED,
                'pipeline': ExecutionEvent.NODE_FAILED
            }
        }
        
        if failed:
            return action_map['fail'].get(job_type, ExecutionEvent.NODE_FAILED)
        
        return action_map.get(action, {}).get(job_type, ExecutionEvent.NODE_STARTED)
        
    def cancel_pipeline(self, execution_id: UUID) -> bool:
        """Cancel a running pipeline"""
        if execution_id in self._running_pipelines:
            task = self._running_pipelines[execution_id]
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled pipeline execution: {execution_id}")
                return True
        return False