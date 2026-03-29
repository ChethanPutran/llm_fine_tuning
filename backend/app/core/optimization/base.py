from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import torch
import torch.nn as nn
import numpy as np
import os

class BaseOptimizer(ABC):
    """Abstract base class for model optimization"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.original_size = 0
        self.optimized_size = 0
        self.original_model = None
        self.optimized_model = None
        
    @abstractmethod
    def optimize(self, model: Union[nn.Module, str]) -> nn.Module:
        """Apply optimization to model"""
        pass
    
    @abstractmethod
    def get_metrics(self, model: nn.Module) -> Dict[str, Any]:
        """Get optimization metrics"""
        pass
    
    def load_model(self, model_path: str) -> nn.Module:
        """Load model from path"""
        if os.path.isdir(model_path):
            # Load from saved transformers model
            from transformers import AutoModel
            model = AutoModel.from_pretrained(model_path)
            self.original_size = self._calculate_model_size(model)
            return model
        else:
            # Load from checkpoint
            model = torch.load(model_path)
            self.original_size = self._calculate_model_size(model)
            return model
    
    def save_model(self, model: nn.Module, output_path: str) -> None:
        """Save optimized model"""
        os.makedirs(output_path, exist_ok=True)
        torch.save(model, f"{output_path}/optimized_model.pt")
        
    def _calculate_model_size(self, model: nn.Module) -> int:
        """Calculate model size in bytes"""
        param_size = 0
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        
        buffer_size = 0
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        return param_size + buffer_size
    
    def calculate_compression_ratio(self) -> float:
        """Calculate compression ratio"""
        if self.optimized_size > 0:
            return self.original_size / self.optimized_size
        return 0.0
    
    def validate_optimization(self, threshold: float = 0.95) -> bool:
        """Validate that optimization didn't degrade quality too much"""
        # This should be implemented by subclasses with actual metrics
        return True