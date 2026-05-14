# Execution Module

This module provides asynchronous execution primitives used by the pipeline engine.

## Key Files

- `async_executor.py`: Runs scheduled pipeline work asynchronously.
- `worker.py`: Worker implementation and handler registration.
- `job_queue.py`: Queueing primitives for submitted work.
- `resource_manager.py`: CPU, memory, and GPU resource availability helpers.
- `distributed_coordinator.py`: Coordination helpers for distributed execution.
- `config.py`: Execution-related settings.

## Flow

1. The pipeline orchestrator registers handlers with workers.
2. The scheduler identifies ready nodes.
3. The async executor submits work to available workers.
4. Workers call registered handlers and return structured results.
5. Resource manager data helps gate or annotate execution decisions.

## Extension Points

Add worker behavior by registering a new node-type handler. Add resource constraints by extending `ResourceManager` and ensuring scheduler decisions consume the new resource data.

## Operational Notes

Handlers should be idempotent where practical because retry behavior can re-run failed nodes. Worker results should include enough metadata to debug failed pipeline stages.
