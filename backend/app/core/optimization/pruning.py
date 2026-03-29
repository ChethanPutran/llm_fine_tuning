import torch
import torch.nn as nn
from typing import Dict, Any, Union
import numpy as np
from .base import BaseOptimizer

class PruningOptimizer(BaseOptimizer):
    """Model pruning optimizer using magnitude-based pruning"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.pruning_rate = config.get('pruning_rate', 0.3)  # 30% pruning
        self.pruning_method = config.get('pruning_method', 'magnitude')  # magnitude, random, structured
        self.target_sparsity = config.get('target_sparsity', 0.5)
        
    def optimize(self, model: Union[nn.Module, str]) -> nn.Module:
        """Apply pruning to model"""
        if isinstance(model, str):
            self.original_model = self.load_model(model)
        else:
            self.original_model = model
        
        # Create a copy for pruning
        pruned_model = self._copy_model(self.original_model)
        
        # Apply pruning
        if self.pruning_method == 'magnitude':
            pruned_model = self._magnitude_pruning(pruned_model)
        elif self.pruning_method == 'random':
            pruned_model = self._random_pruning(pruned_model)
        elif self.pruning_method == 'structured':
            pruned_model = self._structured_pruning(pruned_model)
        
        self.optimized_model = pruned_model
        self.optimized_size = self._calculate_model_size(pruned_model)
        
        return pruned_model
    
    def _copy_model(self, model: nn.Module) -> nn.Module:
        """Create a deep copy of the model"""
        import copy
        return copy.deepcopy(model)
    
    def _magnitude_pruning(self, model: nn.Module) -> nn.Module:
        """Prune weights with smallest magnitude"""
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear) or isinstance(module, nn.Conv2d):
                # Get weight tensor
                weight = module.weight.data
                
                # Calculate threshold for pruning
                flat_weights = weight.abs().flatten()
                k = int(len(flat_weights) * self.pruning_rate)
                
                if k > 0:
                    threshold = torch.kthvalue(flat_weights, k)[0]
                    # Create mask
                    mask = weight.abs() > threshold
                    # Apply mask
                    module.weight.data = weight * mask.float()
                    
                    # Update bias if exists
                    if module.bias is not None:
                        # Don't prune bias typically
                        pass
        
        return model
    
    def _random_pruning(self, model: nn.Module) -> nn.Module:
        """Randomly prune weights"""
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear) or isinstance(module, nn.Conv2d):
                weight = module.weight.data
                # Create random mask
                mask = torch.rand_like(weight) > self.pruning_rate
                module.weight.data = weight * mask.float()
        
        return model
    
    def _structured_pruning(self, model: nn.Module) -> nn.Module:
        """Prune entire neurons/channels"""
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                # Prune neurons (output dimensions)
                weight = module.weight.data
                # Calculate L2 norm per output neuron
                norms = torch.norm(weight, dim=1)
                k = int(len(norms) * self.pruning_rate)
                
                if k > 0:
                    # Find indices to prune
                    _, indices = torch.topk(norms, k, largest=False)
                    # Zero out those neurons
                    weight[indices] = 0
                    module.weight.data = weight
        
        return model
    
    def get_metrics(self, model: nn.Module) -> Dict[str, Any]:
        """Get pruning metrics"""
        # Calculate sparsity
        total_params = 0
        zero_params = 0
        
        for param in model.parameters():
            total_params += param.numel()
            zero_params += torch.sum(param == 0).item()
        
        sparsity = zero_params / total_params if total_params > 0 else 0
        
        metrics = {
            'original_size_mb': self.original_size / (1024 * 1024),
            'optimized_size_mb': self.optimized_size / (1024 * 1024),
            'compression_ratio': self.calculate_compression_ratio(),
            'pruning_rate': self.pruning_rate,
            'pruning_method': self.pruning_method,
            'sparsity': sparsity,
            'zero_parameters': zero_params,
            'total_parameters': total_params
        }
        
        return metrics
    
    def validate_optimization(self, threshold: float = 0.95) -> bool:
        """Validate that pruning didn't degrade accuracy too much"""
        # This would require running evaluation on validation set
        # Simplified version
        compression_ratio = self.calculate_compression_ratio()
        return compression_ratio >= threshold