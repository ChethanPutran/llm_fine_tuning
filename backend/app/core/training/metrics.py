import numpy as np
from typing import Dict, List, Any, Union
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import torch

class MetricsCalculator:
    """Calculate and track training metrics"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all metrics"""
        self.predictions = []
        self.labels = []
        self.losses = []
        
    def update(self, predictions: Union[torch.Tensor, np.ndarray], 
               labels: Union[torch.Tensor, np.ndarray], 
               loss: float):
        """Update metrics with batch results"""
        # Convert to numpy if tensor
        if isinstance(predictions, torch.Tensor):
            predictions = predictions.cpu().numpy()

        if isinstance(labels, torch.Tensor):
            labels = labels.cpu().numpy()
        
        self.predictions.extend(predictions)
        self.labels.extend(labels)
        self.losses.append(loss)
    
    def compute_classification_metrics(self) -> Dict[str, float]:
        """Compute classification metrics"""
        if len(self.predictions) == 0:
            return {}
        
        # Get predictions
        if len(self.predictions[0].shape) > 1:
            pred_labels = np.argmax(self.predictions, axis=1)
        else:
            pred_labels = self.predictions
        
        true_labels = self.labels
        
        # Compute metrics
        accuracy = accuracy_score(true_labels, pred_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, pred_labels, average='weighted'
        )
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1)
        }
    
    def compute_regression_metrics(self) -> Dict[str, float]:
        """Compute regression metrics"""
        if len(self.predictions) == 0:
            return {}
        
        predictions = np.array(self.predictions).flatten()
        labels = np.array(self.labels).flatten()
        
        # Compute metrics
        mse = np.mean((predictions - labels) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions - labels))
        
        # R-squared
        ss_res = np.sum((labels - predictions) ** 2)
        ss_tot = np.sum((labels - np.mean(labels)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2': float(r2)
        }
    
    def compute_sequence_metrics(self) -> Dict[str, float]:
        """Compute sequence generation metrics"""
        if len(self.predictions) == 0:
            return {}
        
        # Compute perplexity
        avg_loss = np.mean(self.losses)
        perplexity = np.exp(avg_loss)
        
        return {
            'perplexity': float(perplexity),
            'avg_loss': float(avg_loss)
        }
    
    def get_confusion_matrix(self) -> np.ndarray:
        """Get confusion matrix for classification"""
        if len(self.predictions) == 0:
            return np.array([])
        
        if len(self.predictions[0].shape) > 1:
            pred_labels = np.argmax(self.predictions, axis=1)
        else:
            pred_labels = self.predictions
        
        return confusion_matrix(self.labels, pred_labels)


class ModelMetrics:
    """Utility class for model metrics calculation"""
    
    @staticmethod
    def calculate_accuracy(predictions: List, labels: List) -> float:
        """Calculate accuracy"""
        correct = sum(1 for p, l in zip(predictions, labels) if p == l)
        return correct / len(predictions) if predictions else 0.0
    
    @staticmethod
    def calculate_precision_recall(predictions: List, labels: List, 
                                   average: str = 'binary') -> Dict[str, float]:
        """Calculate precision and recall"""
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        return {
            'precision': float(precision_score(labels, predictions, average=average, zero_division=0)),
            'recall': float(recall_score(labels, predictions, average=average, zero_division=0)),
            'f1': float(f1_score(labels, predictions, average=average, zero_division=0))
        }
    
    @staticmethod
    def calculate_perplexity(losses: List[float]) -> float:
        """Calculate perplexity from losses"""
        avg_loss = np.mean(losses)
        return np.exp(avg_loss)
    
    @staticmethod
    def calculate_training_speed(total_samples: int, total_time: float) -> float:
        """Calculate training speed (samples per second)"""
        return total_samples / total_time if total_time > 0 else 0.0
    
class TrainingMetricsTracker:
    """Track metrics across training epochs"""
    
    def __init__(self):
        self.train_metrics = []
        self.eval_metrics = []
        self.best_metrics = {}
        self.best_epoch = -1
        
    def add_train_metrics(self, epoch: int, metrics: Dict[str, float]):
        """Add training metrics for an epoch"""
        self.train_metrics.append({
            'epoch': epoch,
            **metrics
        })
    
    def add_eval_metrics(self, epoch: int, metrics: Dict[str, float]):
        """Add evaluation metrics for an epoch"""
        self.eval_metrics.append({
            'epoch': epoch,
            **metrics
        })
        
        # Check if this is the best epoch
        current_score = metrics.get('accuracy', metrics.get('f1_score', metrics.get('perplexity', 0)))
        
        if not self.best_metrics or current_score > self.best_metrics.get('score', 0):
            self.best_metrics = {
                'epoch': epoch,
                'score': current_score,
                'metrics': metrics
            }
            self.best_epoch = epoch
    
    def get_best_epoch(self) -> int:
        """Get the best epoch number"""
        return self.best_epoch
    
    def get_best_metrics(self) -> Dict[str, Any]:
        """Get metrics from the best epoch"""
        return self.best_metrics
    
    def get_training_history(self) -> Dict[str, List]:
        """Get full training history"""
        return {
            'train': self.train_metrics,
            'eval': self.eval_metrics
        }
    
    def is_early_stop(self, patience: int = 3, threshold: float = 0.01) -> bool:
        """Check if early stopping should be triggered"""
        if len(self.eval_metrics) < patience + 1:
            return False
        
        recent_metrics = self.eval_metrics[-patience:]
        best_score = self.best_metrics.get('score', 0)
        current_score = recent_metrics[-1].get('accuracy', 
                                                recent_metrics[-1].get('f1_score',
                                                recent_metrics[-1].get('perplexity', 0)))
        
        # If no improvement for patience steps
        return current_score < best_score - threshold