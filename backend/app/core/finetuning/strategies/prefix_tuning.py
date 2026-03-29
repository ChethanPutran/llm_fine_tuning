import torch
import torch.nn as nn
from typing import Dict, Any
from ..base import FinetuningStrategy

class PrefixTuningStrategy(FinetuningStrategy):
    """Prefix tuning strategy for generative models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prefix_length = config.get('prefix_length', 10)
        self.num_layers = config.get('num_layers', 12)
        self.prefix_embeddings = None
        
    def apply(self, model: nn.Module) -> nn.Module:
        """Add prefix embeddings to model"""
        # Freeze all parameters
        for param in model.parameters():
            param.requires_grad = False
        
        # Get embedding dimension
        embed_dim = model.config.hidden_size if hasattr(model, 'config') else 768
        
        # Create prefix embeddings
        self.prefix_embeddings = nn.Parameter(
            torch.randn(self.num_layers, 2, self.prefix_length, embed_dim)
        )
        
        # Add prefix embeddings as trainable parameters
        model.register_parameter('prefix_embeddings', self.prefix_embeddings)
        
        # Monkey-patch forward method to include prefix
        original_forward = model.forward
        
        def forward_with_prefix(*args, **kwargs):
            # Add prefix to input
            if 'input_ids' in kwargs:
                batch_size = kwargs['input_ids'].size(0)
                prefix = self.prefix_embeddings.mean(dim=0, keepdim=True)
                prefix = prefix.expand(batch_size, -1, -1, -1)
                # This is simplified - actual implementation would be more complex
                
            return original_forward(*args, **kwargs)
        
        model.forward = forward_with_prefix
        
        return model
    
    def get_trainable_params(self, model: nn.Module) -> int:
        """Count prefix parameters only"""
        return self.prefix_embeddings.numel() if self.prefix_embeddings is not None else 0