"""Command line entrypoint for the shared-memory orchestration demo."""

from __future__ import annotations

import argparse
import asyncio
import logging
import socket
from typing import Any, Dict

from .coordinator import DistributedOrchestrationCoordinator
from .models import OrchestrationTask, TaskPriority
from .shared_memory import SharedMemoryStore
from .worker import SharedMemoryWorker


logging.basicConfig(level=logging.INFO)


def build_demo_worker(store: SharedMemoryStore, worker_id: str) -> SharedMemoryWorker:
    worker = SharedMemoryWorker(store=store, worker_id=worker_id)

    async def memory_write(task: OrchestrationTask) -> Dict[str, Any]:
        namespace = task.payload["namespace"]
        key = task.payload["key"]
        value = task.payload["value"]
        ttl_seconds = task.payload.get("ttl_seconds")
        await store.set_shared_value(namespace, key, value, ttl_seconds=ttl_seconds)
        return {"namespace": namespace, "key": key, "written": True}

    async def memory_read(task: OrchestrationTask) -> Dict[str, Any]:
        namespace = task.payload["namespace"]
        key = task.payload["key"]
        value = await store.get_shared_value(namespace, key)
        return {"namespace": namespace, "key": key, "value": value}

    async def echo(task: OrchestrationTask) -> Dict[str, Any]:
        return {"payload": task.payload, "worker_id": worker.worker_id}

    worker.register_handler("memory.write", memory_write)
    worker.register_handler("memory.read", memory_read)
    worker.register_handler("echo", echo)
    return worker


async def run_coordinator() -> None:
    coordinator = DistributedOrchestrationCoordinator()
    await coordinator.start()
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        raise
    finally:
        await coordinator.stop()


async def run_worker(worker_id: str) -> None:
    store = SharedMemoryStore()
    resolved_worker_id = worker_id or socket.gethostname()
    worker = build_demo_worker(store, resolved_worker_id)
    await worker.start()


async def submit_demo_task() -> None:
    store = SharedMemoryStore()
    coordinator = DistributedOrchestrationCoordinator(store=store)
    await coordinator.start()
    try:
        task = OrchestrationTask(
            name="echo",
            priority=TaskPriority.NORMAL,
            payload={"message": "hello from the shared-memory queue"},
        )
        await coordinator.submit_task(task)
        print(task.model_dump_json(indent=2))
    finally:
        await coordinator.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared-memory orchestration runtime")
    parser.add_argument("mode", choices=["coordinator", "worker", "submit-demo"], help="Runtime mode")
    parser.add_argument("--worker-id", default=None, help="Worker identifier")
    args = parser.parse_args()

    if args.mode == "coordinator":
        asyncio.run(run_coordinator())
    elif args.mode == "worker":
        asyncio.run(run_worker(args.worker_id))
    else:
        asyncio.run(submit_demo_task())


if __name__ == "__main__":
    main()