"""Data models for distributed shared-memory orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    """Priority levels used by the task queue."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class TaskState(str, Enum):
    """Lifecycle states for a distributed task."""

    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestrationTask(BaseModel):
    """A unit of work that can be executed by any worker."""

    task_id: UUID = Field(default_factory=uuid4)
    name: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    state: TaskState = Field(default=TaskState.QUEUED)
    attempt: int = Field(default=0)
    max_retries: int = Field(default=3)
    retry_delay_seconds: int = Field(default=5)
    lease_seconds: int = Field(default=30)
    assigned_worker: Optional[str] = Field(default=None)
    dependencies: List[UUID] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = Field(default=None)
    error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def mark_leased(self, worker_id: str) -> None:
        self.state = TaskState.LEASED
        self.assigned_worker = worker_id
        self.started_at = self.started_at or datetime.now(timezone.utc)
        self.touch()

    def mark_running(self, worker_id: str) -> None:
        self.state = TaskState.RUNNING
        self.assigned_worker = worker_id
        self.started_at = self.started_at or datetime.now(timezone.utc)
        self.touch()

    def mark_succeeded(self, result: Dict[str, Any]) -> None:
        self.state = TaskState.SUCCEEDED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)
        self.touch()

    def mark_failed(self, error: str) -> None:
        self.state = TaskState.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc)
        self.touch()

    def should_retry(self) -> bool:
        return self.attempt < self.max_retries

    def schedule_retry(self) -> None:
        self.attempt += 1
        self.state = TaskState.RETRYING
        self.assigned_worker = None
        self.touch()


class WorkerHeartbeat(BaseModel):
    """Heartbeat payload that workers publish periodically."""

    worker_id: str
    machine_id: str
    status: str = Field(default="healthy")
    active_tasks: int = Field(default=0)
    capacity: int = Field(default=1)
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SharedMemoryRecord(BaseModel):
    """Generic shared-memory entry stored in Redis."""

    namespace: str
    key: str
    value: Any
    version: int = Field(default=1)
    ttl_seconds: Optional[int] = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrchestrationEvent(BaseModel):
    """Event emitted by the coordinator or a worker."""

    event_type: str
    task_id: Optional[UUID] = Field(default=None)
    worker_id: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = Field(default_factory=dict)