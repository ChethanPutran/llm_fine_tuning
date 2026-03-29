import torch.nn as nn
from typing import Dict, Any
from ..base import FinetuningStrategy

class FullFinetuneStrategy(FinetuningStrategy):
    """Full fine-tuning strategy (all parameters trainable)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
    def apply(self, model: nn.Module) -> nn.Module:
        """Make all parameters trainable"""
        for param in model.parameters():
            param.requires_grad = True
        
        return model
    
    def get_trainable_params(self, model: nn.Module) -> int:
        """Count all trainable parameters"""
        return sum(p.numel() for p in model.parameters() if p.requires_grad)