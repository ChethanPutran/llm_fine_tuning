from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.common.node_models import NodeType, NodeStatus

class NodeConfig(BaseModel):
    """Configuration for a pipeline node"""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the node execution")
    resources: Dict[str, Any] = Field(default_factory=lambda: {"cpu": 1, "memory": "2Gi"}, description="Resources required for the node execution")
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 3, "delay": 5}, description="Retry policy for the node execution")


class PipelineNode(BaseModel):
    """Represents a node in the pipeline DAG"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the node")
    name: str = Field(default="Unnamed Node", description="Human-readable name for the node")
    type: NodeType  = Field(description="Type of the node (e.g., data_ingestion, model_training)")
    config: NodeConfig = Field(default_factory=NodeConfig, description="Configuration for the node")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="Current status of the node")
    start_time: Optional[datetime] = Field(default=None, description="Start time of the node execution")
    end_time: Optional[datetime] = Field(default=None, description="End time of the node execution")
    error: Optional[str] = Field(default=None, description="Error message if the node failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the node")
    job: Optional[Any] = Field(default=None, description="Reference to the job associated with this node, if any")
    
  

class PipelineEdge(BaseModel):
    """Represents a dependency between nodes"""
    source: str = Field(description="ID of the source node")
    target: str = Field(description="ID of the target node")
    condition: Optional[str] = Field(default=None, description="Condition for this edge to be followed (e.g., 'on_success', 'on_failure')")

class Pipeline(BaseModel):
    """Main pipeline model"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(default="Unnamed Pipeline")
    description: Optional[str] = Field(default=None)
    nodes: Dict[str, PipelineNode] = Field(default_factory=dict)
    edges: List[PipelineEdge] = Field(default_factory=list)
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    
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
    
    @staticmethod
    def from_dict( data: Dict[str, Any]) -> 'Pipeline':
        """Create a Pipeline instance from a dictionary"""
        nodes = {node_data['id']: PipelineNode(**node_data) for node_data in data.get('nodes', [])}
        edges = [PipelineEdge(**edge_data) for edge_data in data.get('edges', [])]
        return Pipeline(
            id=data.get('id', uuid4()),
            name=data.get('name', "Unnamed Pipeline"),
            description=data.get('description'),
            nodes=nodes,
            edges=edges,
            version=data.get('version', 1),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now()),
            tags=data.get('tags', [])
        )

class SchedulingContext(BaseModel):
    """Context object for scheduling decisions"""
    pipeline: Pipeline = Field(description="The pipeline being scheduled")
    completed_nodes: List[str] = Field(default_factory=list)
    failed_nodes: List[str]     = Field(default_factory=list)
    running_nodes: List[str] = Field(default_factory=list)
    resource_availability: Dict[str, int] = Field(default_factory=dict, description="Current resource availability in the system")
    node_results: Dict[str, Any] = Field(default_factory=dict, description="Results from completed nodes that may be needed for scheduling decisions")
    execution_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of execution events for this pipeline run")
    

class NodePosition(BaseModel):
    """Position of a node in the UI graph"""
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
    
    
class VisualNode(BaseModel):
    """Node with visual properties for UI rendering"""
    node: PipelineNode
    position: NodePosition = Field(default_factory=NodePosition)
    style: Dict[str, Any] = Field(default_factory=dict)
    selected: bool = Field(default=False)
    collapsed: bool = Field(default=False)
    
class VisualEdge(BaseModel):
    """Edge with visual properties for UI rendering"""
    edge: PipelineEdge
    style: Dict[str, Any] = Field(default_factory=dict)
    label: Optional[str] = Field(default=None)

