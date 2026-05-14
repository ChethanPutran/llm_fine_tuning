"""Shared-memory orchestration package.

This package provides a Redis-backed control plane for coordinating work
across multiple containers or machines with shared state, leases, retries,
and heartbeat-based failure detection.
"""

from .coordinator import DistributedOrchestrationCoordinator
from .models import OrchestrationTask, TaskPriority, TaskState, WorkerHeartbeat
from .shared_memory import SharedMemoryStore
from .worker import SharedMemoryWorker

__all__ = [
    "DistributedOrchestrationCoordinator",
    "OrchestrationTask",
    "SharedMemoryStore",
    "SharedMemoryWorker",
    "TaskPriority",
    "TaskState",
    "WorkerHeartbeat",
]