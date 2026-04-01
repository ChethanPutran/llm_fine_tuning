import torch
import torch.nn as nn
from typing import Dict, Any, List
import numpy as np
from .base import TrainingTask

class GenerationTask(TrainingTask):
    """Text generation task"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_length = config.get('max_length', 512)
        
    def prepare_dataset(self, dataset: Any) -> Dict[str, Any]:
        """Prepare dataset for generation"""
        import pandas as pd
        
        inputs = []
        outputs = []
        
        if isinstance(dataset, pd.DataFrame):
            inputs = dataset['input'].tolist()
            outputs = dataset['output'].tolist()
        
        # Split dataset
        split_ratio = self.config.get('split_ratio', 0.8)
        split_idx = int(len(inputs) * split_ratio) 
        
        return {
            'train': {
                'input_ids': inputs[:split_idx],
                'labels': outputs[:split_idx] 
            },
            'eval': {
                'input_ids': inputs[split_idx:], 
                'labels': outputs[split_idx:] 
            }
        }
    
    def compute_metrics(self, predictions: Any, labels: Any) -> Dict[str, float]:
        """Compute generation metrics"""
        # Calculate perplexity
        if isinstance(predictions, torch.Tensor):
            loss = nn.CrossEntropyLoss()(predictions, labels)
            perplexity = torch.exp(loss).item()
        else:
            perplexity = 0.0
        
        return {
            'perplexity': perplexity
        }
    
    def get_loss_function(self) -> nn.Module:
        """Get cross-entropy loss for generation"""
        return nn.CrossEntropyLoss()