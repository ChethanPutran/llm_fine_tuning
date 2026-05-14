"""Distributed coordinator for shared-memory orchestration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from .models import OrchestrationEvent, OrchestrationTask, TaskState, WorkerHeartbeat
from .shared_memory import SharedMemoryStore

logger = logging.getLogger(__name__)


class DistributedOrchestrationCoordinator:
    """Coordinates work across workers using Redis as the shared memory layer."""

    def __init__(
        self,
        store: Optional[SharedMemoryStore] = None,
        heartbeat_timeout_seconds: int = 30,
        retry_scan_interval_seconds: int = 5,
    ):
        self.store = store or SharedMemoryStore()
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.retry_scan_interval_seconds = retry_scan_interval_seconds
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        await self.store.ping()
        await self.store.ensure_consumer_group()
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(), name="shared-memory-coordinator")
        logger.info("Shared-memory orchestration coordinator started")

    async def stop(self) -> None:
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        await self.store.close()
        logger.info("Shared-memory orchestration coordinator stopped")

    async def submit_task(self, task: OrchestrationTask) -> OrchestrationTask:
        await self.store.enqueue_task(task)
        return task

    async def register_worker(self, heartbeat: WorkerHeartbeat) -> None:
        await self.store.write_heartbeat(heartbeat)

    async def set_shared_memory(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        await self.store.set_shared_value(namespace, key, value, ttl_seconds=ttl_seconds)

    async def get_shared_memory(self, namespace: str, key: str) -> Optional[Any]:
        return await self.store.get_shared_value(namespace, key)

    async def snapshot(self) -> Dict[str, Any]:
        tasks = await self.store.list_tasks()
        workers = await self.store.list_worker_heartbeats()
        stale_workers = await self.store.stale_worker_ids(self.heartbeat_timeout_seconds)
        state_counts: Dict[str, int] = {}
        for task in tasks:
            state_counts[task.state.value] = state_counts.get(task.state.value, 0) + 1

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "task_counts": state_counts,
            "task_total": len(tasks),
            "worker_total": len(workers),
            "stale_workers": stale_workers,
        }

    async def list_tasks(self) -> List[OrchestrationTask]:
        return await self.store.list_tasks()

    async def get_task(self, task_id: UUID) -> Optional[OrchestrationTask]:
        return await self.store.load_task(task_id)

    async def cancel_task(self, task_id: UUID) -> Optional[OrchestrationTask]:
        task = await self.store.load_task(task_id)
        if not task:
            return None
        task.state = TaskState.CANCELLED
        task.completed_at = datetime.now(timezone.utc)
        await self.store.update_task(task)
        await self.store.record_event(
            OrchestrationEvent(event_type="task_cancelled", task_id=task.task_id, data={"task_id": str(task.task_id)})
        )
        return task

    async def _monitor_loop(self) -> None:
        while self._running:
            try:
                released = await self.store.release_due_retries()
                if released:
                    logger.info("Requeued %s delayed task(s)", len(released))

                stale_workers = await self.store.stale_worker_ids(self.heartbeat_timeout_seconds)
                if stale_workers:
                    logger.warning("Detected stale workers: %s", ", ".join(stale_workers))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Coordinator monitor loop failed: %s", exc)

            await asyncio.sleep(self.retry_scan_interval_seconds)