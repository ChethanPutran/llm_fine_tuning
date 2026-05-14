# Shared-Memory Orchestration Guide

This guide describes the new Redis-backed orchestration system added for multi-container and multi-machine execution.

## Architecture

- `models.py` defines the task and heartbeat contract.
- `shared_memory.py` owns Redis stream transport, shared memory entries, delayed retries, and worker liveness.
- `coordinator.py` acts as the control plane and monitor.
- `worker.py` executes tasks and reports health.
- `runner.py` starts the coordinator or a worker from the command line.

## Fault Tolerance

- Redis streams provide at-least-once delivery.
- Consumer groups allow tasks to survive worker crashes.
- Worker heartbeats let the coordinator mark stale members.
- Failed tasks can be rescheduled into a delayed retry set.

## Scaling Model

- Run the coordinator as a single instance.
- Run any number of worker containers.
- Keep all task state and shared memory in Redis.
- Scale workers horizontally with Docker Compose or a container orchestrator.

Example:

```bash
docker compose -f backend/docker-compose.shared-memory.yml up --build --scale worker=4
```

## Example Flow

1. Submit a task.
2. Coordinator writes the task to Redis.
3. Any healthy worker claims the task.
4. The worker writes result data into shared memory.
5. The coordinator reports task and worker snapshots.

## Module Responsibilities

- `models.py`: data contracts.
- `shared_memory.py`: Redis transport and state storage.
- `coordinator.py`: health, monitoring, and task visibility.
- `worker.py`: execution and retry handling.
- `runner.py`: container-friendly startup path.

## Next Steps

- Add an HTTP API around `DistributedOrchestrationCoordinator.snapshot()`.
- Attach domain-specific handlers for your pipeline stages.
- Replace the demo handlers with your actual pipeline executors.