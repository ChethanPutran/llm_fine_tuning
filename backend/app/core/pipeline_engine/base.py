from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any
from .models import Pipeline

class RetryStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


class BaseRetryStrategy(ABC):
    """Abstract base class for retry strategies"""
    
    @abstractmethod
    def calculate_delay(self, attempt: int, config: Dict[str, Any]) -> float:
        """Calculate delay before next retry"""
        pass


class SchedulingStrategy(ABC):
    """Strategy pattern for different scheduling algorithms"""
    
    @abstractmethod
    def schedule(self, pipeline: Pipeline, ready_nodes: List[str]) -> List[str]:
        """Return the order of ready nodes to execute"""
        pass