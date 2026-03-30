import asyncio
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class WorkerStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"

@dataclass
class WorkerInfo:
    worker_id: str
    status: WorkerStatus
    current_job: Optional[UUID]
    resources: Dict[str, float]
    last_heartbeat: float

class DistributedCoordinator:
    """
    Coordinates distributed execution across multiple workers/nodes
    Implements Singleton pattern for global coordination
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._workers: Dict[str, WorkerInfo] = {}
        self._task_distribution: Dict[UUID, str] = {}  # job_id -> worker_id
        self._lock = asyncio.Lock()
    
    async def register_worker(self, worker_id: str, resources: Dict[str, float]) -> None:
        """Register a worker in the cluster"""
        async with self._lock:
            self._workers[worker_id] = WorkerInfo(
                worker_id=worker_id,
                status=WorkerStatus.IDLE,
                current_job=None,
                resources=resources,
                last_heartbeat=asyncio.get_event_loop().time()
            )
            logger.info(f"Worker {worker_id} registered with resources: {resources}")
    
    async def unregister_worker(self, worker_id: str) -> None:
        """Unregister a worker"""
        async with self._lock:
            if worker_id in self._workers:
                del self._workers[worker_id]
                logger.info(f"Worker {worker_id} unregistered")
    
    async def heartbeat(self, worker_id: str) -> None:
        """Update worker heartbeat"""
        async with self._lock:
            if worker_id in self._workers:
                self._workers[worker_id].last_heartbeat = asyncio.get_event_loop().time()
    
    async def assign_job(self, job_id: UUID, requirements: Dict[str, float]) -> Optional[str]:
        """
        Assign job to best available worker based on requirements
        Returns worker_id if assigned, None if no suitable worker
        """
        async with self._lock:
            # Find suitable workers
            suitable_workers = []
            
            for worker_id, worker in self._workers.items():
                if worker.status != WorkerStatus.IDLE:
                    continue
                
                # Check if worker has required resources
                if self._worker_has_resources(worker, requirements):
                    suitable_workers.append((worker_id, worker))
            
            if not suitable_workers:
                return None
            
            # Select worker with most available resources (load balancing)
            suitable_workers.sort(key=lambda x: sum(x[1].resources.values()), reverse=True)
            best_worker = suitable_workers[0][0]
            
            # Assign job
            self._workers[best_worker].status = WorkerStatus.BUSY
            self._workers[best_worker].current_job = job_id
            self._task_distribution[job_id] = best_worker
            
            return best_worker
    
    async def complete_job(self, job_id: UUID) -> None:
        """Mark job as completed"""
        async with self._lock:
            if job_id in self._task_distribution:
                worker_id = self._task_distribution[job_id]
                if worker_id in self._workers:
                    self._workers[worker_id].status = WorkerStatus.IDLE
                    self._workers[worker_id].current_job = None
                del self._task_distribution[job_id]
    
    def _worker_has_resources(self, worker: WorkerInfo, requirements: Dict[str, float]) -> bool:
        """Check if worker has required resources"""
        for resource_type, amount in requirements.items():
            if worker.resources.get(resource_type, 0) < amount:
                return False
        return True
    
    async def get_cluster_status(self) -> Dict[str, Any]:
        """Get overall cluster status"""
        async with self._lock:
            total_workers = len(self._workers)
            busy_workers = sum(1 for w in self._workers.values() if w.status == WorkerStatus.BUSY)
            idle_workers = sum(1 for w in self._workers.values() if w.status == WorkerStatus.IDLE)
            
            # Check for stale workers (no heartbeat for > 60 seconds)
            current_time = asyncio.get_event_loop().time()
            stale_workers = [
                w.worker_id for w in self._workers.values()
                if current_time - w.last_heartbeat > 60
            ]
            
            return {
                "total_workers": total_workers,
                "busy_workers": busy_workers,
                "idle_workers": idle_workers,
                "stale_workers": stale_workers,
                "active_jobs": len(self._task_distribution),
                "workers": {
                    worker_id: {
                        "status": worker.status.value,
                        "current_job": str(worker.current_job) if worker.current_job else None,
                        "resources": worker.resources,
                        "last_heartbeat": worker.last_heartbeat
                    }
                    for worker_id, worker in self._workers.items()
                }
            }