from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

from .dag_validator import DAGValidator
from .models import Pipeline, PipelineEdge


@dataclass
class PipelineOptimizationResult:
    """Result produced by the pipeline optimizer."""

    pipeline: Pipeline
    execution_plan: List[List[str]]
    summary: Dict[str, Any] = field(default_factory=dict)


class PipelineOptimizer:
    """
    Optimizes a pipeline DAG before execution.

    The optimizer keeps semantics conservative: it removes duplicate edges,
    removes dependency edges that are already implied by another path, orders
    nodes topologically, and annotates nodes with execution levels.
    """

    def optimize(self, pipeline: Pipeline) -> PipelineOptimizationResult:
        optimized = deepcopy(pipeline)
        original_edges = len(optimized.edges)

        self._validate(optimized)
        duplicate_edges_removed = self._deduplicate_edges(optimized)
        transitive_edges_removed = self._remove_transitive_edges(optimized)
        execution_order = DAGValidator(optimized).get_execution_order()
        execution_plan = self._build_parallel_execution_plan(optimized, execution_order)
        self._reorder_nodes(optimized, execution_order)
        self._annotate_nodes(optimized, execution_plan)

        optimized.tags = sorted(set(optimized.tags + ["optimized"]))

        return PipelineOptimizationResult(
            pipeline=optimized,
            execution_plan=execution_plan,
            summary={
                "original_nodes": len(pipeline.nodes),
                "optimized_nodes": len(optimized.nodes),
                "original_edges": original_edges,
                "optimized_edges": len(optimized.edges),
                "duplicate_edges_removed": duplicate_edges_removed,
                "transitive_edges_removed": transitive_edges_removed,
                "parallel_stages": len(execution_plan),
                "execution_order": execution_order,
            },
        )

    def _validate(self, pipeline: Pipeline) -> None:
        is_valid, errors = DAGValidator(pipeline).validate()
        if not is_valid:
            raise ValueError(f"Invalid pipeline: {errors}")

    def _deduplicate_edges(self, pipeline: Pipeline) -> int:
        seen: Set[Tuple[str, str, str | None]] = set()
        unique_edges: List[PipelineEdge] = []

        for edge in pipeline.edges:
            key = (edge.source, edge.target, edge.condition)
            if key in seen:
                continue
            seen.add(key)
            unique_edges.append(edge)

        removed = len(pipeline.edges) - len(unique_edges)
        pipeline.edges = unique_edges
        return removed

    def _remove_transitive_edges(self, pipeline: Pipeline) -> int:
        removable: Set[Tuple[str, str, str | None]] = set()

        for edge in pipeline.edges:
            if self._has_alternate_path(pipeline, edge.source, edge.target, edge):
                removable.add((edge.source, edge.target, edge.condition))

        if not removable:
            return 0

        pipeline.edges = [
            edge for edge in pipeline.edges
            if (edge.source, edge.target, edge.condition) not in removable
        ]
        return len(removable)

    def _has_alternate_path(
        self,
        pipeline: Pipeline,
        source: str,
        target: str,
        ignored_edge: PipelineEdge,
    ) -> bool:
        adjacency: Dict[str, List[str]] = {node_id: [] for node_id in pipeline.nodes}
        for edge in pipeline.edges:
            if edge is ignored_edge:
                continue
            adjacency.setdefault(edge.source, []).append(edge.target)

        visited: Set[str] = set()
        stack = list(adjacency.get(source, []))

        while stack:
            node_id = stack.pop()
            if node_id == target:
                return True
            if node_id in visited:
                continue
            visited.add(node_id)
            stack.extend(adjacency.get(node_id, []))

        return False

    def _build_parallel_execution_plan(
        self,
        pipeline: Pipeline,
        execution_order: List[str],
    ) -> List[List[str]]:
        completed: Set[str] = set()
        remaining = list(execution_order)
        plan: List[List[str]] = []

        while remaining:
            ready = [
                node_id for node_id in remaining
                if all(dep in completed for dep in pipeline.get_dependencies(node_id))
            ]
            if not ready:
                raise ValueError("Unable to build execution plan; DAG may be invalid")

            plan.append(ready)
            completed.update(ready)
            remaining = [node_id for node_id in remaining if node_id not in ready]

        return plan

    def _reorder_nodes(self, pipeline: Pipeline, execution_order: List[str]) -> None:
        pipeline.nodes = {
            node_id: pipeline.nodes[node_id]
            for node_id in execution_order
        }

    def _annotate_nodes(self, pipeline: Pipeline, execution_plan: List[List[str]]) -> None:
        level_by_node = {
            node_id: level
            for level, node_ids in enumerate(execution_plan)
            for node_id in node_ids
        }

        for node_id, node in pipeline.nodes.items():
            node.metadata["optimization"] = {
                "execution_level": level_by_node[node_id],
                "can_run_in_parallel_with": [
                    peer_id
                    for peer_id in execution_plan[level_by_node[node_id]]
                    if peer_id != node_id
                ],
            }
