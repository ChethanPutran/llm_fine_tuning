"""Worker runtime for shared-memory orchestration."""

from __future__ import annotations

import asyncio
import inspect
import logging
import socket
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional
from uuid import uuid4

from .models import OrchestrationEvent, OrchestrationTask, WorkerHeartbeat
from .shared_memory import SharedMemoryStore

logger = logging.getLogger(__name__)

TaskHandler = Callable[[OrchestrationTask], Awaitable[Dict[str, Any]] | Dict[str, Any]]


class SharedMemoryWorker:
    """Consumes Redis stream tasks and executes them with lease recovery."""

    def __init__(
        self,
        store: Optional[SharedMemoryStore] = None,
        worker_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        heartbeat_interval_seconds: int = 5,
        lease_timeout_seconds: int = 30,
    ):
        self.store = store or SharedMemoryStore()
        self.worker_id = worker_id or f"worker-{uuid4().hex[:8]}"
        self.machine_id = machine_id or socket.gethostname()
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self.lease_timeout_seconds = lease_timeout_seconds
        self._running = False
        self._handlers: Dict[str, TaskHandler] = {}
        self._active_tasks = 0

    def register_handler(self, name: str, handler: TaskHandler) -> None:
        self._handlers[name] = handler

    async def start(self) -> None:
        await self.store.ping()
        await self.store.ensure_consumer_group()
        self._running = True
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(), name=f"heartbeat-{self.worker_id}")
        try:
            while self._running:
                reclaimed = await self.store.claim_stale_tasks(self.worker_id, self.lease_timeout_seconds * 1000)
                if reclaimed:
                    await self._process_messages(reclaimed)

                messages = await self.store.read_tasks(self.worker_id, count=1, block_ms=self.heartbeat_interval_seconds * 1000)
                if messages:
                    await self._process_messages(messages)
        except asyncio.CancelledError:
            raise
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            await self.store.close()

    async def stop(self) -> None:
        self._running = False

    async def _heartbeat_loop(self) -> None:
        while self._running:
            heartbeat = WorkerHeartbeat(
                worker_id=self.worker_id,
                machine_id=self.machine_id,
                active_tasks=self._active_tasks,
                capacity=1,
                last_seen=datetime.now(timezone.utc),
                metadata={"consumer_group": self.store.consumer_group},
            )
            try:
                await self.store.write_heartbeat(heartbeat)
            except Exception:
                logger.exception("Failed to write worker heartbeat for %s", self.worker_id)
            await asyncio.sleep(self.heartbeat_interval_seconds)

    async def _process_messages(self, messages: list[tuple[str, Dict[str, str]]]) -> None:
        for message_id, payload in messages:
            task_payload = payload.get("task") or payload.get("value")
            if not task_payload:
                await self.store.acknowledge_task(message_id)
                continue

            task = OrchestrationTask.model_validate_json(task_payload)
            task.mark_running(self.worker_id)
            await self.store.update_task(task)
            self._active_tasks += 1

            try:
                handler = self._handlers.get(task.name) or self._handlers.get(task.payload.get("handler", ""))
                if handler is None:
                    result: Dict[str, Any] = {"message": f"No handler registered for task '{task.name}'"}
                else:
                    output = handler(task)
                    result = await output if inspect.isawaitable(output) else output

                task.mark_succeeded(result)
                await self.store.update_task(task)
                await self.store.record_event(
                    OrchestrationEvent(
                        event_type="task_succeeded",
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        data={"task_id": str(task.task_id), "result_keys": list(result.keys())},
                    )
                )
            except Exception as exc:
                task.mark_failed(str(exc))
                if task.should_retry():
                    await self.store.schedule_retry(task)
                else:
                    await self.store.update_task(task)
                    await self.store.record_event(
                        OrchestrationEvent(
                            event_type="task_failed",
                            task_id=task.task_id,
                            worker_id=self.worker_id,
                            data={"task_id": str(task.task_id), "error": str(exc)},
                        )
                    )
            finally:
                self._active_tasks = max(0, self._active_tasks - 1)
                await self.store.acknowledge_task(message_id)