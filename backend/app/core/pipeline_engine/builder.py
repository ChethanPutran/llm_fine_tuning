from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from uuid import uuid4
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
from datetime import datetime


from .models import (
    Pipeline, PipelineNode, PipelineEdge, NodeType, 
    NodeConfig, VisualNode, VisualEdge
)
from .models import Pipeline

    
class NodePosition:
    """Represents node position in visual layout"""
    
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y
    
    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'NodePosition':
        return cls(data.get("x", 0), data.get("y", 0))


class LayoutAlgorithm(ABC):
    """Abstract strategy for node layout algorithms"""
    
    @abstractmethod
    def layout(self, nodes: List[VisualNode], edges: List[VisualEdge]) -> List[NodePosition]:
        """Calculate positions for nodes"""
        pass


class HierarchicalLayout(LayoutAlgorithm):
    """Hierarchical/tree layout for DAG"""
    
    def __init__(self, horizontal_spacing: float = 200, vertical_spacing: float = 100):
        self.horizontal_spacing = horizontal_spacing
        self.vertical_spacing = vertical_spacing
    
    def layout(self, nodes: List[VisualNode], edges: List[VisualEdge]) -> List[NodePosition]:
        """Calculate hierarchical layout based on node levels"""
        # Build adjacency and compute levels
        adjacency = {node.node.id: [] for node in nodes}
        in_degree = {node.node.id: 0 for node in nodes}
        
        for edge in edges:
            adjacency[edge.edge.source].append(edge.edge.target)
            in_degree[edge.edge.target] += 1
        
        # Find root nodes
        roots = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        # Assign levels using BFS
        levels = {node_id: 0 for node_id in roots}
        queue = list(roots)
        
        while queue:
            current = queue.pop(0)
            for neighbor in adjacency[current]:
                if neighbor not in levels or levels[neighbor] < levels[current] + 1:
                    levels[neighbor] = levels[current] + 1
                    queue.append(neighbor)
        
        # Group nodes by level
        level_groups = {}
        for node in nodes:
            level = levels.get(node.node.id, 0)
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node)
        
        # Assign positions
        positions = []
        for level, level_nodes in level_groups.items():
            y = level * self.vertical_spacing
            total_width = (len(level_nodes) - 1) * self.horizontal_spacing
            start_x = -total_width / 2
            
            for i, node in enumerate(level_nodes):
                x = start_x + i * self.horizontal_spacing
                positions.append(NodePosition(x, y))
        
        return positions


class ForceDirectedLayout(LayoutAlgorithm):
    """Force-directed layout for organic positioning"""
    
    def __init__(self, iterations: int = 100, repulsion: float = 100, attraction: float = 0.1):
        self.iterations = iterations
        self.repulsion = repulsion
        self.attraction = attraction
    
    def layout(self, nodes: List[VisualNode], edges: List[VisualEdge]) -> List[NodePosition]:
        """Calculate positions using force-directed algorithm"""
        import random
        
        # Initialize random positions
        positions = []
        for i, node in enumerate(nodes):
            positions.append(NodePosition(
                x=random.uniform(-500, 500),
                y=random.uniform(-500, 500)
            ))
        
        # Run iterations
        for _ in range(self.iterations):
            # Calculate forces
            forces = [{"x": 0, "y": 0} for _ in nodes]
            
            # Repulsion forces
            for i in range(len(nodes)):
                for j in range(len(nodes)):
                    if i == j:
                        continue
                    
                    dx = positions[i].x - positions[j].x
                    dy = positions[i].y - positions[j].y
                    distance = max(0.1, (dx ** 2 + dy ** 2) ** 0.5)
                    
                    force = self.repulsion / (distance ** 2)
                    forces[i]["x"] += (dx / distance) * force
                    forces[i]["y"] += (dy / distance) * force
            
            # Attraction forces (edges)
            for edge in edges:
                source_idx = self._find_node_index(nodes, edge.edge.source)
                target_idx = self._find_node_index(nodes, edge.edge.target)
                
                if source_idx is None or target_idx is None:
                    continue
                
                dx = positions[target_idx].x - positions[source_idx].x
                dy = positions[target_idx].y - positions[source_idx].y
                distance = max(0.1, (dx ** 2 + dy ** 2) ** 0.5)
                
                force = self.attraction * distance
                forces[source_idx]["x"] += (dx / distance) * force
                forces[source_idx]["y"] += (dy / distance) * force
                forces[target_idx]["x"] -= (dx / distance) * force
                forces[target_idx]["y"] -= (dy / distance) * force
            
            # Apply forces
            for i in range(len(nodes)):
                positions[i].x += forces[i]["x"]
                positions[i].y += forces[i]["y"]
        
        return positions
    
    def _find_node_index(self, nodes: List[VisualNode], node_id: str) -> Optional[int]:
        """Find node index by ID"""
        for i, node in enumerate(nodes):
            if node.node.id == node_id:
                return i
        return None


class PipelineBuilder:
    """
    Builder for constructing pipelines with visual layout support
    Implements Builder pattern for step-by-step pipeline construction
    """
    
    def __init__(self, name: str = None, description: str = None):
        """
        Initialize pipeline builder
        
        Args:
            name: Pipeline name
            description: Pipeline description
        """
        self.pipeline = Pipeline(
            name=name or f"Pipeline_{uuid4().hex[:8]}",
            description=description
        )
        self.visual_nodes: Dict[str, VisualNode] = {}
        self.visual_edges: List[VisualEdge] = []
        self._node_templates: Dict[str, Dict[str, Any]] = {}
        self._layout_algorithm: LayoutAlgorithm = HierarchicalLayout()
        self._change_handlers: List[Callable] = []
    
    # ==================== Node Operations ====================
    def add_job(self, job):
        self.add_node(
            name=job.metadata.get("name", job.job_id),
            node_type=job.type.value,
            resources=job.metadata.get("resource_requirements"),
            retry_policy={"max_retries": job.max_retries},
            metadata={"job_metadata": job.metadata}
        )

    def add_node(
        self,
        name: str,
        node_type: Union[NodeType, str],
        resources: Optional[Dict[str, Any]] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
        position: Optional[Tuple[float, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        job: Optional[Any] = None

    ) -> 'PipelineBuilder':
        """
        Add a node to the pipeline
        
        Args:
            node_id: Unique node identifier
            name: Display name
            node_type: Type of node (data_ingestion, processing, training, etc.)
            config: Node configuration parameters
            resources: Resource requirements
            retry_policy: Retry configuration
            position: Visual position (x, y)
            metadata: Additional metadata
        
        Returns:
            Self for method chaining
        """
        # Convert string type to NodeType enum if needed
        if isinstance(node_type, str):
            node_type = NodeType(node_type)
        
        # Create node config
        node_config = NodeConfig(
            parameters=metadata or {},
            resources=resources or {"cpu": 1, "memory_gb": 2},
            retry_policy=retry_policy or {"max_retries": 3, "strategy": "exponential"}
        )

        node_id = f"node_{uuid4().hex[:8]}"
        
        # Create pipeline node
        node = PipelineNode(
            id=node_id,
            name=name,
            type=node_type,
            config=node_config,
            metadata= {},
            job= job
        )
        
        # Add to pipeline
        self.pipeline.add_node(node)
        
        # Create visual node
        visual_node = VisualNode(
            node=node,
            position=NodePosition(position[0], position[1]) if position else NodePosition(),
            style=self._get_default_style(node_type)
        )
        
        self.visual_nodes[node_id] = visual_node
        
        # Notify changes
        self._notify_change("node_added", {"node_id": node_id})
        
        return self
    
    def remove_node(self, node_id: str) -> 'PipelineBuilder':
        """
        Remove a node and its associated edges
        
        Args:
            node_id: Node identifier to remove
        
        Returns:
            Self for method chaining
        """
        # Remove node
        if node_id in self.pipeline.nodes:
            del self.pipeline.nodes[node_id]
        
        # Remove visual node
        if node_id in self.visual_nodes:
            del self.visual_nodes[node_id]
        
        # Remove edges connected to this node
        self.pipeline.edges = [
            edge for edge in self.pipeline.edges
            if edge.source != node_id and edge.target != node_id
        ]
        
        self.visual_edges = [
            edge for edge in self.visual_edges
            if edge.edge.source != node_id and edge.edge.target != node_id
        ]
        
        self._notify_change("node_removed", {"node_id": node_id})
        
        return self
    
    def update_node_config(
        self,
        node_id: str,
        config: Optional[Dict[str, Any]] = None,
        resources: Optional[Dict[str, Any]] = None,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> 'PipelineBuilder':
        """
        Update node configuration
        
        Args:
            node_id: Node identifier
            config: New configuration parameters
            resources: New resource requirements
            retry_policy: New retry policy
        
        Returns:
            Self for method chaining
        """
        if node_id not in self.pipeline.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.pipeline.nodes[node_id]
        
        if config:
            node.config.parameters.update(config)
        
        if resources:
            node.config.resources.update(resources)
        
        if retry_policy:
            node.config.retry_policy.update(retry_policy)
        
        self._notify_change("node_updated", {"node_id": node_id})
        
        return self
    
    # ==================== Edge Operations ====================
    
    def add_edge(
        self,
        source: str,
        target: str,
        condition: Optional[str] = None,
        label: Optional[str] = None
    ) -> 'PipelineBuilder':
        """
        Add a dependency edge between nodes
        
        Args:
            source: Source node ID
            target: Target node ID
            condition: Optional condition for conditional execution
            label: Optional edge label for visualization
        
        Returns:
            Self for method chaining
        """
        # Validate nodes exist
        if source not in self.pipeline.nodes:
            raise ValueError(f"Source node {source} not found")
        if target not in self.pipeline.nodes:
            raise ValueError(f"Target node {target} not found")
        
        # Create edge
        edge = PipelineEdge(source=source, target=target, condition=condition)
        self.pipeline.add_edge(edge)
        
        # Create visual edge
        visual_edge = VisualEdge(edge=edge, label=label)
        self.visual_edges.append(visual_edge)
        
        self._notify_change("edge_added", {"source": source, "target": target})
        
        return self
    
    def remove_edge(self, source: str, target: str) -> 'PipelineBuilder':
        """
        Remove an edge between nodes
        
        Args:
            source: Source node ID
            target: Target node ID
        
        Returns:
            Self for method chaining
        """
        # Remove from pipeline
        self.pipeline.edges = [
            edge for edge in self.pipeline.edges
            if not (edge.source == source and edge.target == target)
        ]
        
        # Remove from visual edges
        self.visual_edges = [
            edge for edge in self.visual_edges
            if not (edge.edge.source == source and edge.edge.target == target)
        ]
        
        self._notify_change("edge_removed", {"source": source, "target": target})
        
        return self
    
    # ==================== Layout Operations ====================
    
    def set_layout_algorithm(self, algorithm: LayoutAlgorithm) -> 'PipelineBuilder':
        """
        Set the layout algorithm for node positioning
        
        Args:
            algorithm: Layout algorithm instance
        
        Returns:
            Self for method chaining
        """
        self._layout_algorithm = algorithm
        return self
    
    def apply_layout(self) -> 'PipelineBuilder':
        """
        Apply current layout algorithm to position nodes
        
        Returns:
            Self for method chaining
        """
        nodes = list(self.visual_nodes.values())
        
        if not nodes:
            return self
        
        positions = self._layout_algorithm.layout(nodes, self.visual_edges)
        
        for node, position in zip(nodes, positions):
            node.position = position
        
        self._notify_change("layout_applied", {})
        
        return self
    
    def update_node_position(self, node_id: str, x: float, y: float) -> 'PipelineBuilder':
        """
        Manually update node position
        
        Args:
            node_id: Node identifier
            x: X coordinate
            y: Y coordinate
        
        Returns:
            Self for method chaining
        """
        if node_id in self.visual_nodes:
            self.visual_nodes[node_id].position = NodePosition(x, y)
            self._notify_change("node_moved", {"node_id": node_id, "x": x, "y": y})
        
        return self
    
    # ==================== Template Operations ====================
    
    def register_node_template(self, name: str, template: Dict[str, Any]) -> 'PipelineBuilder':
        """
        Register a reusable node template
        
        Args:
            name: Template name
            template: Template configuration
        
        Returns:
            Self for method chaining
        """
        self._node_templates[name] = template
        return self
    
    def add_node_from_template(
        self,
        template_name: str,
        overrides: Optional[Dict[str, Any]] = None,
        position: Optional[Tuple[float, float]] = None
    ) -> 'PipelineBuilder':
        """
        Add a node using a registered template
        
        Args:
            node_id: Unique node identifier
            template_name: Name of registered template
            overrides: Configuration overrides
            position: Visual position
        
            name=template.get("name", node_id),
        Returns:
            Self for method chaining
        """
        if template_name not in self._node_templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = self._node_templates[template_name].copy()
        
        # Apply overrides
        if overrides:
            template.update(overrides)
        
        return self.add_node(
            name=template.get("name", f"node_{uuid4().hex[:8]}"),
            node_type=template.get("type", "custom"),
            resources=template.get("resources"),
            retry_policy=template.get("retry_policy"),
            position=position,
            metadata=template.get("config")
        )
    
    # ==================== Pipeline Operations ====================
    
    def build(self) -> Pipeline:
        """
        Build and return the final pipeline
        
        Returns:
            Constructed Pipeline object
        """
        # Validate pipeline before building
        self.validate()
        
        # Update pipeline metadata
        self.pipeline.updated_at = datetime.utcnow()
        self.pipeline.tags = self._generate_tags()
        
        return self.pipeline
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the pipeline structure
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for empty pipeline
        if not self.pipeline.nodes:
            errors.append("Pipeline has no nodes")
        
        # Check for isolated nodes (no edges)
        nodes_with_edges = set()
        for edge in self.pipeline.edges:
            nodes_with_edges.add(edge.source)
            nodes_with_edges.add(edge.target)
        
        isolated_nodes = set(self.pipeline.nodes.keys()) - nodes_with_edges
        if isolated_nodes and len(self.pipeline.nodes) > 1:
            errors.append(f"Isolated nodes found: {isolated_nodes}")
        
        # Check for cycles
        if self._has_cycle():
            errors.append("Pipeline contains cycles")
        
        # Validate node types and configurations
        for node_id, node in self.pipeline.nodes.items():
            if not node.name:
                errors.append(f"Node {node_id} has no name")
            
            if node.type not in NodeType:
                errors.append(f"Node {node_id} has invalid type: {node.type}")
        
        return len(errors) == 0, errors
    
    def _has_cycle(self) -> bool:
        """Detect cycles in the pipeline graph"""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            # Find edges from this node
            for edge in self.pipeline.edges:
                if edge.source == node_id:
                    if edge.target not in visited:
                        if dfs(edge.target):
                            return True
                    elif edge.target in rec_stack:
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.pipeline.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    def _generate_tags(self) -> List[str]:
        """Generate tags based on pipeline content"""
        tags = set()
        
        for node in self.pipeline.nodes.values():
            tags.add(node.type.value)
        
        # Add complexity tag
        if len(self.pipeline.nodes) > 10:
            tags.add("complex")
        elif len(self.pipeline.nodes) > 5:
            tags.add("medium")
        else:
            tags.add("simple")
        
        return list(tags)
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert builder state to dictionary for serialization
        
        Returns:
            Dictionary representation
        """
        return {
            "pipeline": {
                "id": str(self.pipeline.id),
                "name": self.pipeline.name,
                "description": self.pipeline.description,
                "version": self.pipeline.version,
                "tags": self.pipeline.tags
            },
            "nodes": [
                visual_node.to_dict()
                for visual_node in self.visual_nodes.values()
            ],
            "edges": [
                visual_edge.to_dict()
                for visual_edge in self.visual_edges
            ],
            "metadata": {
                "node_templates": list(self._node_templates.keys()),
                "layout_algorithm": self._layout_algorithm.__class__.__name__
            }
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert builder state to JSON
        
        Args:
            indent: JSON indentation
        
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineBuilder':
        """
        Create builder from dictionary
        
        Args:
            data: Dictionary representation
        
        Returns:
            PipelineBuilder instance
        """
        builder = cls(
            name=data["pipeline"]["name"],
            description=data["pipeline"].get("description")
        )
        
        # Add nodes
        for node_data in data.get("nodes", []):
            builder.add_node(
                node_id=node_data["id"],
                name=node_data["name"],
                node_type=node_data["type"],
                config=node_data.get("config", {}),
                position=(
                    node_data["position"]["x"],
                    node_data["position"]["y"]
                ) if "position" in node_data else None,
                metadata=node_data.get("metadata")
            )
        
        # Add edges
        for edge_data in data.get("edges", []):
            builder.add_edge(
                source=edge_data["source"],
                target=edge_data["target"],
                condition=edge_data.get("condition"),
                label=edge_data.get("label")
            )
        
        return builder
    
    # ==================== Helper Methods ====================
    
    def _get_default_style(self, node_type: NodeType) -> Dict[str, Any]:
        """Get default visual style for node type"""
        styles = {
            NodeType.DATA_INGESTION: {
                "backgroundColor": "#4CAF50",
                "borderColor": "#388E3C",
                "icon": "cloud_upload"
            },
            NodeType.DATA_PROCESSING: {
                "backgroundColor": "#2196F3",
                "borderColor": "#1976D2",
                "icon": "filter_alt"
            },
            NodeType.MODEL_TRAINING: {
                "backgroundColor": "#FF9800",
                "borderColor": "#F57C00",
                "icon": "model_training"
            },
            NodeType.MODEL_EVALUATION: {
                "backgroundColor": "#9C27B0",
                "borderColor": "#7B1FA2",
                "icon": "assessment"
            },
            NodeType.MODEL_DEPLOYMENT: {
                "backgroundColor": "#00BCD4",
                "borderColor": "#0097A7",
                "icon": "rocket_launch"
            },
            NodeType.CUSTOM: {
                "backgroundColor": "#9E9E9E",
                "borderColor": "#757575",
                "icon": "extension"
            }
        }
        
        return styles.get(node_type, styles[NodeType.CUSTOM])
    
    def _notify_change(self, change_type: str, data: Dict[str, Any]) -> None:
        """Notify all change handlers of pipeline modification"""
        for handler in self._change_handlers:
            try:
                handler(change_type, data, self)
            except Exception as e:
                print(f"Error in change handler: {e}")
    
    def on_change(self, handler: Callable) -> 'PipelineBuilder':
        """
        Register handler for pipeline changes
        
        Args:
            handler: Callback function receiving (change_type, data, builder)
        
        Returns:
            Self for method chaining
        """
        self._change_handlers.append(handler)
        return self
    
    # ==================== Export/Import ====================
    
    def export_to_dag_json(self) -> Dict[str, Any]:
        """
        Export pipeline in DAG format for visualization tools
        
        Returns:
            DAG representation compatible with DAG visualization libraries
        """
        return {
            "nodes": [
                {
                    "id": node.node.id,
                    "name": node.node.name,
                    "type": node.node.type.value,
                    "config": node.node.config.parameters,
                    "position": {"x": node.position.x, "y": node.position.y},
                    "metadata": node.node.metadata
                }
                for node in self.visual_nodes.values()
            ],
            "edges": [
                {
                    "from": edge.edge.source,
                    "to": edge.edge.target,
                    "condition": edge.edge.condition,
                    "label": edge.label
                }
                for edge in self.visual_edges
            ]
        }
    
    def get_subgraph(self, node_ids: List[str]) -> 'PipelineBuilder':
        """
        Create a subgraph containing only specified nodes
        
        Args:
            node_ids: List of node IDs to include
        
        Returns:
            New PipelineBuilder containing only the subgraph
        """
        sub_builder = PipelineBuilder(
            name=f"{self.pipeline.name}_subgraph",
            description=f"Subgraph of {self.pipeline.name}"
        )
        
        # Add selected nodes
        for node_id in node_ids:
            if node_id in self.pipeline.nodes:
                node = self.pipeline.nodes[node_id]
                visual_node = self.visual_nodes[node_id]
                
                sub_builder.add_node(
                    node_id=node_id,
                    name=node.name,
                    node_type=node.type,
                    config=node.config.parameters,
                    resources=node.config.resources,
                    retry_policy=node.config.retry_policy,
                    position=(visual_node.position.x, visual_node.position.y),
                    metadata=node.metadata
                )
        
        # Add edges between selected nodes
        for edge in self.visual_edges:
            if edge.edge.source in node_ids and edge.edge.target in node_ids:
                sub_builder.add_edge(
                    source=edge.edge.source,
                    target=edge.edge.target,
                    condition=edge.edge.condition,
                    label=edge.label
                )
        
        return sub_builder
    
    def merge_pipeline(self, other: 'PipelineBuilder', prefix: str = "") -> 'PipelineBuilder':
        """
        Merge another pipeline into this one
        
        Args:
            other: Another PipelineBuilder instance
            prefix: Prefix to add to node IDs to avoid conflicts
        
        Returns:
            Self for method chaining
        """
        # Add nodes from other pipeline
        for node_id, visual_node in other.visual_nodes.items():
            new_node_id = f"{prefix}{node_id}" if prefix else node_id
            node = visual_node.node
            
            self.add_node(
                node_id=new_node_id,
                name=node.name,
                node_type=node.type,
                config=node.config.parameters,
                resources=node.config.resources,
                retry_policy=node.config.retry_policy,
                position=(visual_node.position.x, visual_node.position.y),
                metadata=node.metadata
            )
        
        # Add edges from other pipeline
        for visual_edge in other.visual_edges:
            source = f"{prefix}{visual_edge.edge.source}" if prefix else visual_edge.edge.source
            target = f"{prefix}{visual_edge.edge.target}" if prefix else visual_edge.edge.target
            
            self.add_edge(
                source=source,
                target=target,
                condition=visual_edge.edge.condition,
                label=visual_edge.label
            )
        
        return self


class PipelineTemplate:
    """
    Pre-defined pipeline templates for common use cases
    """
    
    @staticmethod
    def rag_pipeline() -> PipelineBuilder:
        """RAG (Retrieval-Augmented Generation) pipeline template"""
        builder = PipelineBuilder(name="RAG Pipeline", description="Retrieval-Augmented Generation pipeline")
        
        # Data ingestion
        builder.add_node(
            name="Data Loader",
            node_type=NodeType.DATA_INGESTION,
            metadata={"source": "documents", "format": "pdf"}
        )
        
        # Document processing
        builder.add_node(
            name="Document Processor",
            node_type=NodeType.DATA_PROCESSING,
            metadata={"chunk_size": 512, "overlap": 50}
        )
        
        # Embedding generation
        builder.add_node(
            name="Embedding Generator",
            node_type=NodeType.DATA_PROCESSING,
            metadata={"model": "text-embedding-ada-002"},
            resources={"cpu": 2, "memory_gb": 4, "gpu": 1}
        )
        
        # Vector store
        builder.add_node(
            name="Vector Store",
            node_type=NodeType.DATA_PROCESSING,
            metadata={"db": "pinecone", "dimension": 1536}
        )
        
        # LLM fine-tuning
        builder.add_node(
            name="LLM Fine-tuning",
            node_type=NodeType.MODEL_TRAINING,
            metadata={"model": "llama2-7b", "epochs": 3},
            resources={"cpu": 8, "memory_gb": 32, "gpu": 4}
        )
        
        # Deployment
        builder.add_node(
            name="Deploy RAG API",
            node_type=NodeType.MODEL_DEPLOYMENT,
            metadata={"endpoint": "/rag", "replicas": 2}
        )
        
        # Add edges
        builder.add_edge("data_loader", "doc_processor")
        builder.add_edge("doc_processor", "embedding_gen")
        builder.add_edge("embedding_gen", "vector_store")
        builder.add_edge("vector_store", "llm_finetune")
        builder.add_edge("llm_finetune", "deploy_rag")
        
        return builder
    
    @staticmethod
    def classification_pipeline() -> PipelineBuilder:
        """Text classification pipeline template"""
        builder = PipelineBuilder(name="Classification Pipeline", description="Text classification pipeline")
        
        builder.add_node(
            name="Load Dataset",
            node_type=NodeType.DATA_INGESTION,
            metadata={"dataset": "imdb", "split": "train"}
        )
        
        builder.add_node(
            name="Text Preprocessing",
            node_type=NodeType.DATA_PROCESSING,
            metadata={"lowercase": True, "remove_stopwords": True}
        )
        
        builder.add_node(
            name="Tokenization",
            node_type=NodeType.DATA_PROCESSING,
            metadata={"tokenizer": "bert-base-uncased", "max_length": 512}
        )
        
        builder.add_node(
            name="Train BERT Classifier",
            node_type=NodeType.MODEL_TRAINING,
            metadata={"model": "bert-base-uncased", "num_labels": 2, "epochs": 5},
            resources={"cpu": 4, "memory_gb": 16, "gpu": 2}
        )
        
        builder.add_node(
            name="Evaluate Model",
            node_type=NodeType.MODEL_EVALUATION,
            metadata={"metrics": ["accuracy", "f1", "precision", "recall"]}
        )
        
        builder.add_node(
            name="Deploy Classifier",
            node_type=NodeType.MODEL_DEPLOYMENT,
            metadata={"endpoint": "/classify", "batch_size": 32}
        )
        
        # Add edges
        builder.add_edge("data_ingest", "preprocess")
        builder.add_edge("preprocess", "tokenize")
        builder.add_edge("tokenize", "train_bert")
        builder.add_edge("train_bert", "evaluate")
        builder.add_edge("evaluate", "deploy")
        
        return builder
    
    @staticmethod
    def lora_finetuning_pipeline() -> PipelineBuilder:
        """LoRA fine-tuning pipeline template"""
        builder = PipelineBuilder(name="LoRA Fine-tuning", description="Parameter-efficient fine-tuning")
        
        builder.add_node(
            name="Load Training Data",
            node_type=NodeType.DATA_INGESTION,
            metadata={"format": "instruction", "source": "huggingface"}
        )
        
        builder.add_node(
            name="Format as Instructions",
            node_type=NodeType.DATA_PROCESSING,
            metadata={"template": "alpaca", "add_eos": True}
        )
        
        builder.add_node(
            name="Apply LoRA",
            node_type=NodeType.MODEL_TRAINING,
            metadata={
                "base_model": "llama2-7b",
                "lora_r": 8,
                "lora_alpha": 16,
                "lora_dropout": 0.1,
                "target_modules": ["q_proj", "v_proj"]
            },
            resources={"cpu": 4, "memory_gb": 16, "gpu": 1}
        )
        
        builder.add_node(
            name="Merge LoRA Weights",
            node_type=NodeType.MODEL_TRAINING,
            metadata={"merge_strategy": "linear"}
        )
        
        builder.add_node(
            name="Quantize Model",
            node_type=NodeType.MODEL_TRAINING,
            metadata={"bits": 4, "quantization_type": "nf4"}
        )
        
        builder.add_node(
            name="Deploy Quantized Model",
            node_type=NodeType.MODEL_DEPLOYMENT,
            metadata={"endpoint": "/generate", "max_tokens": 512}
        )
        
        # Add edges
        builder.add_edge("load_data", "format_data")
        builder.add_edge("format_data", "apply_lora")
        builder.add_edge("apply_lora", "merge_weights")
        builder.add_edge("merge_weights", "quantize")
        builder.add_edge("quantize", "deploy_lora")
        
        return builder
    
    @staticmethod
    def hyperparameter_tuning_pipeline() -> PipelineBuilder:
        """Hyperparameter optimization pipeline"""
        builder = PipelineBuilder(name="Hyperparameter Tuning", description="Automated hyperparameter search")
        
        builder.add_node(
            name="Train/Val Split",
            node_type=NodeType.DATA_PROCESSING,
            metadata={"train_ratio": 0.8, "stratify": True}
        )
        
        builder.add_node(
            name="Hyperparameter Search",
            node_type=NodeType.MODEL_TRAINING,
            metadata={
                "search_algorithm": "bayesian",
                "n_trials": 50,
                "params": {
                    "learning_rate": [1e-5, 1e-4, 1e-3],
                    "batch_size": [16, 32, 64],
                    "epochs": [3, 5, 10]
                }
            },
            resources={"cpu": 8, "memory_gb": 32, "gpu": 4}
        )
        
        builder.add_node(
            name="Train Best Model",
            node_type=NodeType.MODEL_TRAINING,
            metadata={"use_best_params": True}
        )
        
        builder.add_node(
            name="Deploy Best Model",
            node_type=NodeType.MODEL_DEPLOYMENT,
            metadata={"version": "best"}
        )
        
        # Add edges
        builder.add_edge("data_split", "hpo_search")
        builder.add_edge("hpo_search", "best_model")
        builder.add_edge("best_model", "deploy_best")
        
        return builder

    @staticmethod
    def data_preprocessing_pipeline() -> PipelineBuilder:
        """Data preprocessing pipeline template"""
        builder = PipelineBuilder(name="Data Preprocessing", description="Pipeline for data cleaning and transformation")

        builder.add_node(
            name="Data Loader",
            node_type=NodeType.DATA_INGESTION,
            metadata={"dataset": "imdb", "split": "train"}
        )

        builder.add_node(
            name="Data Processor",
            node_type=NodeType.DATA_PROCESSING,
            metadata={"clean_text": True, "normalize": True}
        )

        # Add edges
        builder.add_edge("data_loader", "data_processor")

        return builder

    @staticmethod
    def model_deployment_pipeline() -> PipelineBuilder:
        """Model deployment pipeline template"""
        builder = PipelineBuilder(name="Model Deployment", description="Pipeline for deploying trained models")

        builder.add_node(
            name="Model Loader",
            node_type=NodeType.DATA_INGESTION,
            metadata={"model_source": "local", "model_path": "/models/bert"}
        )

        builder.add_node(
            name="API Server",
            node_type=NodeType.MODEL_DEPLOYMENT,
            metadata={"endpoint": "/predict", "replicas": 2}
        )

        # Add edges
        builder.add_edge("model_loader", "api_server")

        return builder

# Example usage and demonstration
if __name__ == "__main__":
    # Example 1: Building a simple pipeline
    print("=== Example 1: Simple Pipeline ===")
    builder = PipelineBuilder(name="Simple Training Pipeline")
    
    builder.add_node(
        name="Data Ingestion",
        node_type=NodeType.DATA_INGESTION,
        metadata={"dataset": "imdb", "split": "train"}
    )
    
    builder.add_node(
        name="Data Processing",
        node_type=NodeType.DATA_PROCESSING,
        metadata={"clean_text": True, "normalize": True}
    )
    
    builder.add_node(
        name="Model Training",
        node_type=NodeType.MODEL_TRAINING,
        metadata={"model": "bert-base", "epochs": 3},
        resources={"cpu": 4, "memory_gb": 16, "gpu": 1}
    )
    
    builder.add_edge("ingest", "process")
    builder.add_edge("process", "train")
    
    # Apply layout
    builder.apply_layout()
    
    # Build pipeline
    pipeline = builder.build()
    print(f"Built pipeline: {pipeline.name}")
    print(f"Nodes: {len(pipeline.nodes)}")
    print(f"Edges: {len(pipeline.edges)}")
    print()
    
    # Example 2: Using templates
    print("=== Example 2: Using Templates ===")
    rag_pipeline = PipelineTemplate.rag_pipeline()
    rag_pipeline.apply_layout()
    rag_pipeline.validate()
    
    print(f"RAG Pipeline: {rag_pipeline.pipeline.name}")
    print(f"Nodes: {len(rag_pipeline.pipeline.nodes)}")
    print(f"Edges: {len(rag_pipeline.pipeline.edges)}")
    
    # Export to DAG format
    dag_json = rag_pipeline.export_to_dag_json()
    print(f"DAG Export: {len(dag_json['nodes'])} nodes, {len(dag_json['edges'])} edges")
    print()
    
    # Example 3: JSON serialization
    print("=== Example 3: JSON Serialization ===")
    json_str = rag_pipeline.to_json(indent=2)
    print(f"JSON length: {len(json_str)} characters")
    
    # Rebuild from JSON
    data = rag_pipeline.to_dict()
    rebuilt = PipelineBuilder.from_dict(data)
    print(f"Rebuilt pipeline: {rebuilt.pipeline.name}")
    print(f"Rebuilt nodes: {len(rebuilt.pipeline.nodes)}")
    print()
    
    # Example 4: Subgraph extraction
    print("=== Example 4: Subgraph Extraction ===")
    subgraph = rag_pipeline.get_subgraph(["data_loader", "doc_processor", "embedding_gen"])
    print(f"Subgraph: {subgraph.pipeline.name}")
    print(f"Nodes in subgraph: {len(subgraph.pipeline.nodes)}")
    
    # Example 5: Pipeline merging
    print("\n=== Example 5: Pipeline Merging ===")
    classification = PipelineTemplate.classification_pipeline()
    classification.merge_pipeline(rag_pipeline, prefix="rag_")
    print(f"Merged pipeline: {classification.pipeline.name}")
    print(f"Total nodes: {len(classification.pipeline.nodes)}")
    print(f"Total edges: {len(classification.pipeline.edges)}")
    
    # Example 6: Change tracking
    print("\n=== Example 6: Change Tracking ===")
    def on_change(change_type, data, builder):
        print(f"  Change: {change_type} - {data}")
    
    builder = PipelineTemplate.classification_pipeline()
    builder.on_change(on_change)
    builder.update_node_config("train_bert", config={"epochs": 10})
    builder.add_node(
        name="New Node",
        node_type=NodeType.DATA_PROCESSING
    )