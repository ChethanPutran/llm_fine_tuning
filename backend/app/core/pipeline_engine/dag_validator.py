from typing import Any, List, Set, Dict, Tuple
from collections import deque, defaultdict
from .models import Pipeline

class DAGValidationError(Exception):
    pass

class DAGValidator:
    """Validates DAG structure and detects cycles"""
    
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self._graph: Dict[str, List[str]] = defaultdict(list)
        self._reverse_graph: Dict[str, List[str]] = defaultdict(list)
    
    async def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the pipeline DAG
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Build graphs
        self._build_graphs()
        
        # Check for cycles
        if cycle := self._detect_cycle():
            errors.append(f"Cycle detected: {' -> '.join(cycle)}")
        
        # Check for orphaned nodes
        if orphans := self._find_orphaned_nodes():
            errors.append(f"Orphaned nodes found: {orphans}")
        
        # Validate node references
        if invalid_edges := self._validate_node_references():
            errors.append(f"Invalid edge references: {invalid_edges}")
        
        return len(errors) == 0, errors
    
    async def _build_graphs(self) -> None:
        """Build adjacency lists for the DAG"""
        self._graph.clear()
        self._reverse_graph.clear()
        
        for edge in self.pipeline.edges:
            if edge.source in self.pipeline.nodes and edge.target in self.pipeline.nodes:
                self._graph[edge.source].append(edge.target)
                self._reverse_graph[edge.target].append(edge.source)
    
    async def _detect_cycle(self) -> List[str]:
        """Detect cycles using DFS"""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def dfs(node: str, path: List[str]) -> List[str]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self._graph.get(node, []):
                if neighbor not in visited:
                    if cycle := dfs(neighbor, path.copy()):
                        return cycle
                elif neighbor in rec_stack:
                    # Cycle detected, return the cycle path
                    cycle_start_index = path.index(neighbor)
                    return path[cycle_start_index:] + [neighbor]
            
            rec_stack.remove(node)
            return []
        
        for node in self.pipeline.nodes:
            if node not in visited:
                if cycle := dfs(node, []):
                    return cycle
        
        return []
    
    def _find_orphaned_nodes(self) -> List[str]:
        """Find nodes with no path from root"""
        all_nodes = set(self.pipeline.nodes.keys())
        
        # Find root nodes (nodes with no incoming edges)
        nodes_with_incoming = set()
        for edge in self.pipeline.edges:
            nodes_with_incoming.add(edge.target)
        
        roots = all_nodes - nodes_with_incoming
        
        if not roots:
            return list(all_nodes)  # All nodes are orphaned if no roots
        
        # BFS to find reachable nodes
        reachable = set()
        queue = deque(roots)
        
        while queue:
            node = queue.popleft()
            if node not in reachable:
                reachable.add(node)
                queue.extend(self._graph.get(node, []))
        
        # Orphaned nodes are those not reachable from any root
        return list(all_nodes - reachable)
    
    def _validate_node_references(self) -> List[str]:
        """Validate that all edge references point to existing nodes"""
        invalid_edges = []
        
        for edge in self.pipeline.edges:
            if edge.source not in self.pipeline.nodes:
                invalid_edges.append(f"Source {edge.source} not found")
            if edge.target not in self.pipeline.nodes:
                invalid_edges.append(f"Target {edge.target} not found")
        
        return invalid_edges
    
    def get_execution_order(self) -> List[str]:
        """Get topological sort order for execution"""
        if not self.validate()[0]:
            raise DAGValidationError("Pipeline contains cycles or other validation errors")
        
        in_degree = defaultdict(int)
        for edge in self.pipeline.edges:
            in_degree[edge.target] += 1
        
        queue = deque([node_id for node_id in self.pipeline.nodes if in_degree[node_id] == 0])
        execution_order = []
        
        while queue:
            node_id = queue.popleft()
            execution_order.append(node_id)
            
            for neighbor in self._graph.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return execution_order
    @staticmethod
    async def from_dict(data: Dict[str, Any]) -> 'DAGValidator':
        """Create a DAGValidator from a dictionary representation of a pipeline"""
        pipeline = Pipeline.from_dict(data)
        return DAGValidator(pipeline)