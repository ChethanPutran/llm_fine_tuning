"""Redis-backed shared memory, leases, and task transport."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.core.config import settings

from .models import OrchestrationEvent, OrchestrationTask, SharedMemoryRecord, TaskState, WorkerHeartbeat


class SharedMemoryStore:
    """Redis namespace used by the orchestration layer."""

    task_stream_name = "shared-memory:tasks"
    delayed_queue_name = "shared-memory:delayed"
    event_stream_name = "shared-memory:events"
    worker_heartbeat_prefix = "shared-memory:worker:"
    task_record_prefix = "shared-memory:task:"
    shared_memory_prefix = "shared-memory:namespace:"
    consumer_group = "shared-memory-workers"

    def __init__(self, redis_url: Optional[str] = None):
        self.redis = Redis.from_url(redis_url or settings.REDIS_URL, decode_responses=True)
        self._connected = False

    async def ping(self) -> None:
        await self.redis.ping()
        self._connected = True

    async def ensure_consumer_group(self) -> None:
        try:
            await self.redis.xgroup_create(self.task_stream_name, self.consumer_group, id="$", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def close(self) -> None:
        if self._connected:
            await self.redis.close()
            self._connected = False

    async def record_event(self, event: OrchestrationEvent) -> None:
        await self.redis.xadd(self.event_stream_name, {"event": event.model_dump_json()})

    async def store_task(self, task: OrchestrationTask) -> None:
        await self.redis.set(self._task_key(task.task_id), task.model_dump_json())

    async def load_task(self, task_id: UUID) -> Optional[OrchestrationTask]:
        payload = await self.redis.get(self._task_key(task_id))
        if not payload:
            return None
        return OrchestrationTask.model_validate_json(payload)

    async def update_task(self, task: OrchestrationTask) -> None:
        task.touch()
        await self.store_task(task)

    async def enqueue_task(self, task: OrchestrationTask) -> str:
        await self.store_task(task)
        message_id = await self.redis.xadd(
            self.task_stream_name,
            {"task_id": str(task.task_id), "task": task.model_dump_json()},
        )
        await self.record_event(
            OrchestrationEvent(
                event_type="task_enqueued",
                task_id=task.task_id,
                data={"task_id": str(task.task_id), "priority": task.priority.value, "message_id": message_id},
            )
        )
        return message_id

    async def read_tasks(
        self,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 1000,
    ) -> List[Tuple[str, Dict[str, str]]]:
        entries = await self.redis.xreadgroup(
            groupname=self.consumer_group,
            consumername=consumer_name,
            streams={self.task_stream_name: ">"},
            count=count,
            block=block_ms,
        )
        return self._normalize_stream_entries(entries)

    async def claim_stale_tasks(
        self,
        consumer_name: str,
        min_idle_ms: int,
        count: int = 10,
    ) -> List[Tuple[str, Dict[str, str]]]:
        response = await self.redis.xautoclaim(
            name=self.task_stream_name,
            groupname=self.consumer_group,
            consumername=consumer_name,
            min_idle_time=min_idle_ms,
            start_id="0-0",
            count=count,
        )

        if isinstance(response, tuple) and len(response) >= 2:
            messages = response[1]
            return self._normalize_stream_entries([(self.task_stream_name, messages)])
        return []

    async def acknowledge_task(self, message_id: str) -> None:
        await self.redis.xack(self.task_stream_name, self.consumer_group, message_id)

    async def schedule_retry(self, task: OrchestrationTask) -> None:
        task.schedule_retry()
        await self.update_task(task)
        due_at = datetime.now(timezone.utc).timestamp() + task.retry_delay_seconds
        await self.redis.zadd(self.delayed_queue_name, {str(task.task_id): due_at})
        await self.record_event(
            OrchestrationEvent(
                event_type="task_retry_scheduled",
                task_id=task.task_id,
                data={"task_id": str(task.task_id), "attempt": task.attempt, "retry_at": due_at},
            )
        )

    async def release_due_retries(self, limit: int = 100) -> List[OrchestrationTask]:
        now_ts = datetime.now(timezone.utc).timestamp()
        task_ids = await self.redis.zrangebyscore(self.delayed_queue_name, min="-inf", max=now_ts, start=0, num=limit)
        released: List[OrchestrationTask] = []
        for task_id in task_ids:
            removed = await self.redis.zrem(self.delayed_queue_name, task_id)
            if not removed:
                continue
            task = await self.load_task(UUID(task_id))
            if task is None:
                continue
            task.state = TaskState.QUEUED
            task.assigned_worker = None
            task.updated_at = datetime.now(timezone.utc)
            await self.store_task(task)
            await self.redis.xadd(
                self.task_stream_name,
                {"task_id": str(task.task_id), "task": task.model_dump_json()},
            )
            released.append(task)
        return released

    async def set_shared_value(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        record = SharedMemoryRecord(namespace=namespace, key=key, value=value, ttl_seconds=ttl_seconds)
        redis_key = self._shared_key(namespace, key)
        payload = record.model_dump_json()
        if ttl_seconds:
            await self.redis.setex(redis_key, ttl_seconds, payload)
        else:
            await self.redis.set(redis_key, payload)

    async def get_shared_value(self, namespace: str, key: str) -> Optional[Any]:
        payload = await self.redis.get(self._shared_key(namespace, key))
        if not payload:
            return None
        record = SharedMemoryRecord.model_validate_json(payload)
        return record.value

    async def delete_shared_value(self, namespace: str, key: str) -> None:
        await self.redis.delete(self._shared_key(namespace, key))

    async def list_shared_keys(self, namespace: str) -> List[str]:
        pattern = f"{self.shared_memory_prefix}{namespace}:*"
        keys = await self.redis.keys(pattern)
        return [key.split(":", 3)[-1] for key in keys]

    async def write_heartbeat(self, heartbeat: WorkerHeartbeat) -> None:
        redis_key = f"{self.worker_heartbeat_prefix}{heartbeat.worker_id}"
        await self.redis.setex(redis_key, heartbeat.capacity * 10, heartbeat.model_dump_json())
        await self.redis.hset("shared-memory:worker-heartbeats", heartbeat.worker_id, heartbeat.model_dump_json())

    async def list_worker_heartbeats(self) -> List[WorkerHeartbeat]:
        values = await self.redis.hvals("shared-memory:worker-heartbeats")
        return [WorkerHeartbeat.model_validate_json(value) for value in values]

    async def list_tasks(self) -> List[OrchestrationTask]:
        tasks: List[OrchestrationTask] = []
        async for key in self.redis.scan_iter(match=f"{self.task_record_prefix}*"):
            payload = await self.redis.get(key)
            if payload:
                tasks.append(OrchestrationTask.model_validate_json(payload))
        return tasks

    async def stale_worker_ids(self, heartbeat_timeout_seconds: int) -> List[str]:
        heartbeats = await self.list_worker_heartbeats()
        cutoff = datetime.now(timezone.utc).timestamp() - heartbeat_timeout_seconds
        stale_workers: List[str] = []
        for heartbeat in heartbeats:
            if heartbeat.last_seen.timestamp() < cutoff:
                stale_workers.append(heartbeat.worker_id)
        return stale_workers

    def _task_key(self, task_id: UUID) -> str:
        return f"{self.task_record_prefix}{task_id}"

    def _shared_key(self, namespace: str, key: str) -> str:
        return f"{self.shared_memory_prefix}{namespace}:{key}"

    def _normalize_stream_entries(self, entries: Iterable[Any]) -> List[Tuple[str, Dict[str, str]]]:
        normalized: List[Tuple[str, Dict[str, str]]] = []
        for _, stream_entries in entries:
            for message_id, payload in stream_entries:
                normalized.append((message_id, payload))
        return normalized