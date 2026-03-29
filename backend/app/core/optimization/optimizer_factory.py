from typing import Dict, Any
from .base import BaseOptimizer
from .pruning import PruningOptimizer
from .distillation import DistillationOptimizer
from .quantization import QuantizationOptimizer

class OptimizerFactory:
    """Factory pattern for creating optimizers"""
    
    _optimizers = {
        'pruning': PruningOptimizer,
        'distillation': DistillationOptimizer,
        'quantization': QuantizationOptimizer
    }
    
    @classmethod
    def get_optimizer(cls, optimizer_type: str, config: Dict[str, Any]) -> BaseOptimizer:
        """Get optimizer instance by type"""
        optimizer_class = cls._optimizers.get(optimizer_type.lower())
        if not optimizer_class:
            raise ValueError(f"Unknown optimizer type: {optimizer_type}. Available: {list(cls._optimizers.keys())}")
        return optimizer_class(config)
    
    @classmethod
    def register_optimizer(cls, name: str, optimizer_class):
        """Register new optimizer type"""
        cls._optimizers[name] = optimizer_class
    
    @classmethod
    def list_optimizers(cls) -> list:
        """List available optimizers"""
        return list(cls._optimizers.keys())