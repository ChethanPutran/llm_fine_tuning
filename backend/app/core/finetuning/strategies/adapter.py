import torch.nn as nn
from typing import Dict, Any
from ..base import FinetuningStrategy

class AdapterLayer(nn.Module):
    """Adapter layer for parameter-efficient fine-tuning"""
    
    def __init__(self, input_dim: int, bottleneck_dim: int):
        super().__init__()
        self.down_proj = nn.Linear(input_dim, bottleneck_dim)
        self.up_proj = nn.Linear(bottleneck_dim, input_dim)
        self.activation = nn.GELU()
        
    def forward(self, x):
        return self.up_proj(self.activation(self.down_proj(x))) + x

class AdapterStrategy(FinetuningStrategy):
    """Adapter-based fine-tuning strategy"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bottleneck_size = config.get('bottleneck_size', 64)
        self.adapter_layers = []
        
    def apply(self, model: nn.Module) -> nn.Module:
        """Inject adapter layers into the model"""
        # Freeze all parameters
        for param in model.parameters():
            param.requires_grad = False
        
        # Inject adapter layers
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                adapter = AdapterLayer(
                    module.out_features,
                    self.bottleneck_size
                )
                setattr(module, 'adapter', adapter)
                self.adapter_layers.append(adapter)
        
        # Only adapters are trainable
        for layer in self.adapter_layers:
            for param in layer.parameters():
                param.requires_grad = True
        
        return model
    
    def get_trainable_params(self, model: nn.Module) -> int:
        """Count trainable parameters (adapters only)"""
        trainable_params = 0
        for layer in self.adapter_layers:
            trainable_params += sum(p.numel() for p in layer.parameters())
        return trainable_params