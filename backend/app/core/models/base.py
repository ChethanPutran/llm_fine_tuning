from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import torch
import torch.nn as nn
from transformers import PreTrainedModel, PreTrainedTokenizer

class BaseModel(ABC):
    """Abstract base class for all models"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        self.model_name = model_name
        self.config = config
        self.model = None
        self.tokenizer = None
    
    @abstractmethod
    def load_model(self) -> None:
        """Load the model from pretrained weights"""
        pass
    
    @abstractmethod
    def forward(self, input_ids: torch.Tensor, **kwargs) -> torch.Tensor:
        """Forward pass"""
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """Save model to disk"""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load model from disk"""
        pass
    
    def to_device(self, device: str = 'cuda') -> None:
        """Move model to device"""
        if self.model:
            self.model.to(device)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get model parameters"""
        if not self.model:
            return {}
        
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'total_params': total_params,
            'trainable_params': trainable_params,
            'non_trainable_params': total_params - trainable_params
        }