# Pipeline Engine Module

This module builds, validates, schedules, executes, and tracks DAG-based workflows.

## Key Files

- `models.py`: Pipeline, node, edge, visual node, and scheduling context models.
- `builder.py`: Fluent builder and predefined pipeline templates.
- `optimizer.py`: Conservative DAG optimizer that removes redundant edges, computes parallel levels, and annotates nodes.
- `code_generator.py`: Generates Python scripts that reconstruct and execute optimized pipelines through the engine.
- `dag_validator.py`: DAG validation and dependency checks.
- `scheduler.py`: Node scheduling logic.
- `executor.py`: Pipeline execution and event emission.
- `orchestrator.py`: Main coordinator for jobs, handlers, execution state, and WebSocket notifications.
- `retry_handler.py`: Retry policy behavior.
- `state_manager.py`: State persistence and checkpoint helpers.
- `config.py`: Pipeline configuration model.
- `handlers/`: Node-type handlers that call domain modules.

## Flow

1. Jobs are registered with the orchestrator.
2. Jobs become pipeline nodes through the builder.
3. The optimizer validates the DAG, removes duplicate/transitive edges, topologically orders nodes, and creates a parallel execution plan.
4. The code generator writes a Python execution script for the optimized graph.
5. The scheduler identifies executable nodes at runtime.
6. Workers or direct engine handlers execute each node type.
7. Events update execution state and notify connected clients.

## Extension Points

Add a pipeline stage by adding a node type if needed, implementing a handler in `handlers/`, registering the handler in `orchestrator.py`, and ensuring the frontend/API sends compatible node config.

## Operational Notes

Pipeline definitions should be acyclic and explicit about dependencies. Execution events should remain structured so the dashboard can update progress without parsing log text.

The optimizer is intentionally conservative. It should not merge stages or remove nodes unless the engine can prove semantic equivalence. Redundant dependency edges may be removed because they are already enforced by another path in the DAG.
