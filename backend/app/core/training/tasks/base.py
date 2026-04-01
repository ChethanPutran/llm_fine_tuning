from abc import ABC, abstractmethod
from typing import Dict, Any
import torch.nn as nn
from ...datasets.base import BaseDataset 

class TrainingTask(ABC):
    """Abstract base class for fine-tuning strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    @abstractmethod
    def prepare_dataset(self, dataset: Any) -> BaseDataset:
        """Prepare dataset for training and evaluation"""
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
