from typing import List, Dict, Optional, Callable
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from .models import Pipeline, PipelineNode, NodeStatus, SchedulingContext
from app.common.enums import NodeType
from .dag_validator import DAGValidator
from .base import SchedulingStrategy


class FIFOScheduler(SchedulingStrategy):
    """First In First Out scheduler"""
    
    def schedule(self, pipeline: Pipeline, ready_nodes: List[str]) -> List[str]:
        return ready_nodes  # Preserve order

class PriorityScheduler(SchedulingStrategy):
    """Priority-based scheduler"""
    
    def __init__(self, priority_func: Optional[Callable[[PipelineNode], int]] = None):
        self.priority_func = priority_func or self._default_priority
    
    def _default_priority(self, node: PipelineNode) -> int:
        priority_map = {
            "model_training": 1,
            "data_processing": 2,
            "data_ingestion": 3,
            "model_evaluation": 4,
            "model_deployment": 5,
        }
        return priority_map.get(node.type.value, 10)
    
    def schedule(self, pipeline: Pipeline, ready_nodes: List[str]) -> List[str]:
        nodes_with_priority = [
            (node_id, self.priority_func(pipeline.nodes[node_id]))
            for node_id in ready_nodes
        ]
        nodes_with_priority.sort(key=lambda x: x[1])
        return [node_id for node_id, _ in nodes_with_priority]

class PipelineScheduler:
    """Main scheduler orchestrating pipeline execution"""
    
    def __init__(self, strategy: Optional[SchedulingStrategy] = None):
        self.strategy = strategy or FIFOScheduler()
        self._dependency_counter: Dict[str, int] = defaultdict(int)
        self._reverse_dependencies: Dict[str, List[str]] = defaultdict(list)
    
    def get_ready_nodes(self, pipeline: Pipeline, context: SchedulingContext) -> List[str]:
        """Determine which nodes are ready to execute"""
        ready_nodes = []
        
        for node_id, node in pipeline.nodes.items():
            # Skip nodes that are already completed, running, or failed
            if node.status in [NodeStatus.COMPLETED, NodeStatus.RUNNING, NodeStatus.FAILED]:
                continue
            
            # Check all dependencies are completed
            dependencies = pipeline.get_dependencies(node_id)
            all_deps_completed = all(
                pipeline.nodes[dep].status == NodeStatus.COMPLETED
                for dep in dependencies
            )
            
            if all_deps_completed:
                ready_nodes.append(node_id)
        
        return ready_nodes
    
    def schedule_pipeline(self, pipeline: Pipeline, context: SchedulingContext) -> List[str]:
        """
        Schedule the pipeline execution
        Returns: List of node IDs to execute in order
        """
        ready_nodes = self.get_ready_nodes(pipeline, context)
        
        if not ready_nodes:
            return []
        
        # Apply scheduling strategy
        scheduled_nodes = self.strategy.schedule(pipeline, ready_nodes)
        
        # Apply resource constraints
        scheduled_nodes = self._apply_resource_constraints(
            scheduled_nodes, 
            pipeline, 
            context.resource_availability
        )
        
        return scheduled_nodes
    
    def _apply_resource_constraints(
        self, 
        nodes: List[str], 
        pipeline: Pipeline,
        resource_availability: Dict[str, int]
    ) -> List[str]:
        """Filter nodes that can be executed based on resource availability"""
        available_nodes = []
        
        for node_id in nodes:
            node = pipeline.nodes[node_id]
            required_cpu = node.config.resources.get("cpu", 1)
            required_memory = node.config.resources.get("memory_gb", 2)
            
            if (resource_availability.get("cpu", 0) >= required_cpu and
                resource_availability.get("memory_gb", 0) >= required_memory):
                available_nodes.append(node_id)
        
        return available_nodes