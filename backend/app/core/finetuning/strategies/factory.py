from typing import Dict, Any
from ..base import FinetuningStrategy
from .adapter import AdapterLayer
from .full_finetune import FinetuningStrategy
from .lora import LoRAStrategy
from .prefix_tuning import PrefixTuningStrategy
from ..config import FinetuningConfig

class FinetuningStrategyFactory:
    """Factory pattern for creating finetuning strategies"""
    
    _strategies = {
        'adapter': AdapterLayer,
        'full': FinetuningStrategy,
        'lora': LoRAStrategy,
        'prefix': PrefixTuningStrategy
    }
    
    @classmethod
    def get_strategy(cls, strategy_type: str, config: FinetuningConfig) -> FinetuningStrategy:
        """Get finetuning strategy instance by type"""
        strategy_class = cls._strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown finetuning strategy type: {strategy_type}")
        return strategy_class(config)
    
    @classmethod
    def register_strategy(cls, name: str, strategy_class):
        """Register new finetuning strategy type"""
        cls._strategies[name] = strategy_class