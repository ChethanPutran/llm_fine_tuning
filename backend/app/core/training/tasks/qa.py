import torch
import torch.nn as nn
from typing import Dict, Any, List
import numpy as np
from .base import TrainingTask

class QATask(TrainingTask):
    """Question answering task"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
    def prepare_dataset(self, dataset: Any) -> Dict[str, Any]:
        """Prepare dataset for QA"""
        import pandas as pd

        contexts = []
        questions = []
        answers = []
        answer_starts = []
        
        if isinstance(dataset, pd.DataFrame):
            contexts = dataset['context'].tolist()
            questions = dataset['question'].tolist()
            answers = dataset['answer'].tolist()
            answer_starts = dataset.get('answer_start', [0] * len(answers))
        
        # Split dataset
        split_ratio = self.config.get('split_ratio', 0.8)
        split_idx = int(len(contexts) * split_ratio) 
        
        return {
            'train': {
                'context': contexts[:split_idx],
                'question': questions[:split_idx],
                'answer': answers[:split_idx],
                'answer_start': answer_starts[:split_idx]
            },
            'eval': {
                'context': contexts[split_idx:],
                'question': questions[split_idx:],
                'answer': answers[split_idx:],
                'answer_start': answer_starts[split_idx:]
            }
        }
    
    def compute_metrics(self, predictions: Any, labels: Any) -> Dict[str, float]:
        """Compute QA metrics"""
        # Calculate exact match and F1 score
        exact_matches = 0
        f1_scores = []
        
        for pred, label in zip(predictions, labels):
            if pred == label:
                exact_matches += 1
            
            # Calculate F1
            pred_tokens = set(pred.split())
            label_tokens = set(label.split())
            
            if len(pred_tokens) == 0 or len(label_tokens) == 0:
                f1 = 0.0
            else:
                intersection = pred_tokens & label_tokens
                precision = len(intersection) / len(pred_tokens)
                recall = len(intersection) / len(label_tokens)
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            f1_scores.append(f1)
        
        return {
            'exact_match': exact_matches / len(predictions),
            'f1_score': float(np.mean(f1_scores))
        }
    
    def get_loss_function(self) -> nn.Module:
        """Get loss function for QA (span prediction)"""
        return nn.CrossEntropyLoss()