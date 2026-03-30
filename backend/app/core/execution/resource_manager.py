import psutil
import GPUtil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

class ResourceType(Enum):
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"

@dataclass
class Resource:
    type: ResourceType
    total: float
    available: float
    allocated: float = 0.0
    metadata: Optional[Dict] = None

class ResourceManager:
    """
    Manages compute resources following Singleton pattern
    Implements resource allocation and tracking
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._resources: Dict[ResourceType, Resource] = {}
        self._allocations: Dict[str, Dict] = {}  # job_id -> allocated resources
        self._lock = asyncio.Lock()
        self._refresh_resources()
    
    def _refresh_resources(self):
        """Refresh available resources"""
        # CPU and Memory
        cpu_count = psutil.cpu_count() or 0
        memory = psutil.virtual_memory()
        
        self._resources[ResourceType.CPU] = Resource(
            type=ResourceType.CPU,
            total=float(cpu_count),
            available=float(cpu_count),
            allocated=0.0
        )
        
        self._resources[ResourceType.MEMORY] = Resource(
            type=ResourceType.MEMORY,
            total=memory.total / (1024**3),  # Convert to GB
            available=memory.available / (1024**3),
            allocated=0.0
        )
        
        # GPU
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_count = len(gpus)
                self._resources[ResourceType.GPU] = Resource(
                    type=ResourceType.GPU,
                    total=float(gpu_count),
                    available=float(gpu_count),
                    allocated=0.0,
                    metadata={"gpu_details": [{"id": gpu.id, "memory": gpu.memoryTotal} for gpu in gpus]}
                )
        except:
            # No GPUs available
            pass
    
    async def allocate_resources(self, job_id: str, requirements: Dict[str, float]) -> bool:
        """
        Allocate resources for a job
        Returns True if allocation successful
        """
        async with self._lock:
            # Refresh current resources
            self._refresh_resources()
            
            # Check if enough resources available
            for resource_type, amount in requirements.items():
                resource_enum = ResourceType[resource_type.upper()]
                if resource_enum not in self._resources:
                    return False
                
                if self._resources[resource_enum].available < amount:
                    return False
            
            # Allocate resources
            allocated_resources = {}
            for resource_type, amount in requirements.items():
                resource_enum = ResourceType[resource_type.upper()]
                self._resources[resource_enum].available -= amount
                self._resources[resource_enum].allocated += amount
                allocated_resources[resource_type] = amount
            
            self._allocations[job_id] = allocated_resources
            return True
    
    async def release_resources(self, job_id: str) -> None:
        """Release resources allocated to a job"""
        async with self._lock:
            if job_id not in self._allocations:
                return
            
            allocated_resources = self._allocations[job_id]
            for resource_type, amount in allocated_resources.items():
                resource_enum = ResourceType[resource_type.upper()]
                if resource_enum in self._resources:
                    self._resources[resource_enum].available += amount
                    self._resources[resource_enum].allocated -= amount
            
            del self._allocations[job_id]
    
    async def get_available_resources(self) -> Dict[str, float]:
        """Get currently available resources"""
        async with self._lock:
            self._refresh_resources()
            return {
                resource_type.value: resource.available
                for resource_type, resource in self._resources.items()
            }
    
    async def get_resource_utilization(self) -> Dict[str, Dict[str, float]]:
        """Get detailed resource utilization"""
        async with self._lock:
            return {
                resource_type.value: {
                    "total": resource.total,
                    "available": resource.available,
                    "allocated": resource.allocated,
                    "utilization_percent": (resource.allocated / resource.total * 100) if resource.total > 0 else 0
                }
                for resource_type, resource in self._resources.items()
            }
    
    async def health_check(self) -> Dict[str, str]:
        """Perform health check on resources"""
        async with self._lock:
            health_status = {}
            for resource_type, resource in self._resources.items():
                if resource.available < (0.1 * resource.total):  # If less than 10% available
                    health_status[resource_type.value] = "Warning: Low availability"
                else:
                    health_status[resource_type.value] = "Healthy"
            return health_status
    
    async def can_schedule(self, requirements: Dict[str, float]) -> bool:
        """Check if resources are available for a job"""
        async with self._lock:
            self._refresh_resources()
            
            for resource_type, amount in requirements.items():
                resource_enum = ResourceType[resource_type.upper()]
                if resource_enum not in self._resources:
                    return False
                
                if self._resources[resource_enum].available < amount:
                    return False
            
            return True