from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import torch.nn as nn

class FinetuningStrategy(ABC):
    """Abstract base class for fine-tuning strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def apply(self, model: nn.Module) -> nn.Module:
        """Apply fine-tuning strategy to model"""
        pass
    
    @abstractmethod
    def get_trainable_params(self, model: nn.Module) -> int:
        """Get number of trainable parameters after applying strategy"""
        pass
    
    def get_optimizer_params(self) -> Dict[str, Any]:
        """Get optimizer parameters for the strategy"""
        return {
            'learning_rate': self.config.get('learning_rate', 2e-5),
            'weight_decay': self.config.get('weight_decay', 0.01)
        }

class FinetuningTask(ABC):
    """Abstract base class for fine-tuning tasks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def prepare_dataset(self, dataset: Any) -> Dict[str, Any]:
        """Prepare dataset for the task"""
        pass
    
    @abstractmethod
    def compute_metrics(self, predictions: Any, labels: Any) -> Dict[str, float]:
        """Compute task-specific metrics"""
        pass
    
    @abstractmethod
    def get_loss_function(self) -> nn.Module:
        """Get task-specific loss function"""
        pass