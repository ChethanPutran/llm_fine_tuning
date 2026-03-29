import torch
import torch.nn as nn
from typing import Dict, Any, List
import numpy as np
from rouge_score import rouge_scorer
from ..base import FinetuningTask

class SummarizationTask(FinetuningTask):
    """Text summarization task"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_source_length = config.get('max_source_length', 512)
        self.max_target_length = config.get('max_target_length', 128)
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        
    def prepare_dataset(self, dataset: Any) -> Dict[str, Any]:
        """Prepare dataset for summarization"""
        import pandas as pd

        documents = []
        summaries = []
        
        if isinstance(dataset, pd.DataFrame):
            documents = dataset['document'].tolist()
            summaries = dataset['summary'].tolist()
        
        # Split dataset
        split_ratio = self.config.get('split_ratio', 0.8)
        split_idx = int(len(documents) * split_ratio)
        
        return {
            'train': {
                'document': documents[:split_idx],
                'summary': summaries[:split_idx]
            },
            'eval': {
                'document': documents[split_idx:],
                'summary': summaries[split_idx:]
            }
        }
    
    def compute_metrics(self, predictions: Any, labels: Any) -> Dict[str, float]:
        """Compute ROUGE scores for summarization"""
        if isinstance(predictions, torch.Tensor):
            # Decode predictions if they're token IDs
            predictions = [str(p) for p in predictions]
        
        scores = {
            'rouge1': [],
            'rouge2': [],
            'rougeL': []
        }
        
        for pred, label in zip(predictions, labels):
            if isinstance(pred, torch.Tensor):
                pred = str(pred)
            if isinstance(label, torch.Tensor):
                label = str(label)
                
            score = self.rouge_scorer.score(pred, label)
            for key in scores.keys():
                scores[key].append(score[key].fmeasure)
        
        return {
            'rouge1': float(np.mean(scores['rouge1'])),
            'rouge2': float(np.mean(scores['rouge2'])),
            'rougeL': float(np.mean(scores['rougeL']))
        }
    
    def get_loss_function(self) -> nn.Module:
        """Get cross-entropy loss for summarization"""
        return nn.CrossEntropyLoss()