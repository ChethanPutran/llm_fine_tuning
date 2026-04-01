import torch
import torch.nn as nn
from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from .base import TrainingTask

class ImageCaptioningTask(TrainingTask):
    """Image captioning task"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.num_labels = config.get('num_labels', 2)
        self.label_mapping = config.get('label_mapping', {})
        
    def prepare_dataset(self, dataset: Any) -> Dict[str, Any]:
        """Prepare dataset for classification"""
        import pandas as pd

        texts = []
        labels = []
        
        if isinstance(dataset, pd.DataFrame):
            texts = dataset['text'].tolist() 
            labels = dataset['label'].tolist()
            
            # Map labels to indices if needed
            if self.label_mapping:
                labels = [self.label_mapping.get(label, 0) for label in labels]
            else:
                # Create label mapping
                unique_labels = sorted(set(labels))
                self.label_mapping = {label: i for i, label in enumerate(unique_labels)}
                labels = [self.label_mapping[label] for label in labels]
        
        # Split dataset
        split_ratio = self.config.get('split_ratio', 0.8)
        split_idx = int(len(texts) * split_ratio) 
        
        return {
            'train': {
                'texts': texts[:split_idx],  
                'labels': labels[:split_idx] 
            },
            'eval': {
                'texts': texts[split_idx:],  
                'labels': labels[split_idx:] 
            }
        }
    
    def compute_metrics(self, predictions: Any, labels: Any) -> Dict[str, float]:
        """Compute classification metrics"""
        # Convert predictions to labels
        if isinstance(predictions, torch.Tensor):
            pred_labels = torch.argmax(predictions, dim=-1).cpu().numpy()
        else:
            pred_labels = np.argmax(predictions, axis=-1)
        
        # Convert labels if needed
        if isinstance(labels, torch.Tensor):
            true_labels = labels.cpu().numpy()
        else:
            true_labels = np.array(labels)
        
        # Compute metrics
        accuracy = float(accuracy_score(true_labels, pred_labels))
        f1 = float(f1_score(true_labels, pred_labels, average='weighted'))
        
        return {
            'accuracy': accuracy,
            'f1_score': f1
        }
    
    def get_loss_function(self) -> nn.Module:
        """Get cross-entropy loss for classification"""
        return nn.CrossEntropyLoss()