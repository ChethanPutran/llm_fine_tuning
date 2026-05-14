# Shared-Memory Orchestration

This package is a Redis-backed orchestration layer that can run across multiple Docker containers or multiple machines.

It is intentionally small and explicit so you can study the moving parts:

- `models.py` defines tasks, worker heartbeats, and shared-memory records.
- `shared_memory.py` owns Redis storage, task transport, leases, retries, and shared state.
- `coordinator.py` monitors health, requeues delayed tasks, and exposes orchestration snapshots.
- `worker.py` consumes tasks, executes handlers, and writes results back to Redis.
- `runner.py` is the CLI entrypoint for coordinator, worker, and demo task submission.

## Design Goals

- Stateless application containers.
- Shared control state stored in Redis.
- At-least-once task delivery through Redis streams and consumer groups.
- Crash recovery through stale task claiming and delayed retry requeueing.
- Heartbeat-based worker liveness detection.

## How It Works

1. A client creates an `OrchestrationTask` and submits it to the coordinator.
2. The coordinator stores task state and pushes the task into the Redis stream.
3. Workers claim tasks from the stream and execute registered handlers.
4. Successes are acknowledged and persisted back to Redis.
5. Failures can be retried through the delayed retry queue.
6. The coordinator continuously reissues due retries and reports stale workers.

## Running the Demo

Start Redis, then run the coordinator and one or more workers:

```bash
python -m app.core.shared_memory_orchestration.runner coordinator
python -m app.core.shared_memory_orchestration.runner worker --worker-id worker-a
python -m app.core.shared_memory_orchestration.runner worker --worker-id worker-b
```

Submit a sample task:

```bash
python -m app.core.shared_memory_orchestration.runner submit-demo
```

## Extending It

- Add handlers in `runner.py` or register them from your own integration layer.
- Store arbitrary shared values with `SharedMemoryStore.set_shared_value`.
- Use the snapshot output from `DistributedOrchestrationCoordinator.snapshot()` for a UI or API endpoint.