from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

class NodeType(Enum):
    DATA_INGESTION = "data_ingestion"
    DATA_PROCESSING = "data_processing"
    MODEL_TRAINING = "model_training"
    MODEL_FINETUNING = "model_finetuning"
    TOKENIZATION = "tokenization"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_DEPLOYMENT = "model_deployment"
    OPTIMIZATION = "optimization"
    CUSTOM = "custom"

class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

class ExecutionStatus(Enum):
    CREATED = "created"
    VALIDATING = "validating"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExecutionEvent(Enum):
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_RETRYING = "node_retrying"
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DATA_INGESTION_COMPLETED = "data_ingestion_completed"
    DATA_INGESTION_FAILED = "data_ingestion_failed"
    DATA_PROCESSING_COMPLETED = "data_processing_completed"
    DATA_PROCESSING_FAILED = "data_processing_failed"
    MODEL_TRAINING_COMPLETED = "model_training_completed"
    MODEL_TRAINING_FAILED = "model_training_failed"
    MODEL_EVALUATION_COMPLETED = "model_evaluation_completed"
    MODEL_EVALUATION_FAILED = "model_evaluation_failed"
    MODEL_DEPLOYMENT_COMPLETED = "model_deployment_completed"
    MODEL_DEPLOYMENT_FAILED = "model_deployment_failed"



@dataclass
class NodeConfig:
    """Configuration for a pipeline node"""
    parameters: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=lambda: {"cpu": 1, "memory": "2Gi"})
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {"max_retries": 3, "delay": 5})

@dataclass
class PipelineNode:
    """Represents a node in the pipeline DAG"""
    id: str
    name: str
    type: NodeType
    config: NodeConfig
    status: NodeStatus = NodeStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "config": self.config.parameters,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
            "metadata": self.metadata
        }

@dataclass
class PipelineEdge:
    """Represents a dependency between nodes"""
    source: str
    target: str
    condition: Optional[str] = None  # Optional condition for conditional execution

@dataclass
class Pipeline:
    """Main pipeline model"""
    id: UUID = field(default_factory=uuid4)
    name: str = "Unnamed Pipeline"
    description: Optional[str] = None
    nodes: Dict[str, PipelineNode] = field(default_factory=dict)
    edges: List[PipelineEdge] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    
    def add_node(self, node: PipelineNode) -> None:
        self.nodes[node.id] = node
    
    def add_edge(self, edge: PipelineEdge) -> None:
        self.edges.append(edge)
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """Get all dependencies for a node"""
        return [edge.source for edge in self.edges if edge.target == node_id]
    
    def get_dependents(self, node_id: str) -> List[str]:
        """Get all nodes that depend on this node"""
        return [edge.target for edge in self.edges if edge.source == node_id]
    

@dataclass
class SchedulingContext:
    """Context object for scheduling decisions"""
    pipeline: Pipeline
    completed_nodes: List[str]
    failed_nodes: List[str]
    running_nodes: List[str]
    resource_availability: Dict[str, int]
    node_results: Dict[str, Any]
    