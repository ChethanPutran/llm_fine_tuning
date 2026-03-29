import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup
from tqdm import tqdm
import mlflow
from typing import Dict, Any, Optional
import numpy as np

class Trainer:
    """Training class with MLflow tracking"""
    
    def __init__(self, model: nn.Module, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.device = torch.device(config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
        self.model.to(self.device)
        
        # Training parameters
        self.learning_rate = config.get('learning_rate', 2e-5)
        self.num_epochs = config.get('num_epochs', 3)
        self.batch_size = config.get('batch_size', 16)
        self.warmup_steps = config.get('warmup_steps', 0)
        self.weight_decay = config.get('weight_decay', 0.01)
        
        # Metrics
        self.train_losses = []
        self.eval_losses = []
        self.train_accuracies = []
        
        # MLflow setup
        mlflow.set_tracking_uri(config.get('mlflow_uri', './mlruns'))
        
    def train(self, train_dataset, eval_dataset=None) -> Dict[str, Any]:
        """Train the model"""
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True
        )
        
        optimizer = AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay
        )
        
        total_steps = len(train_loader) * self.num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=self.warmup_steps,
            num_training_steps=total_steps
        )
        
        # MLflow tracking
        with mlflow.start_run() as run:
            mlflow.log_params(self.config)
            
            for epoch in range(self.num_epochs):
                # Training
                self.model.train()
                train_loss = 0
                train_correct = 0
                train_total = 0
                
                progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{self.num_epochs}")
                
                for batch in progress_bar:
                    # Move batch to device
                    batch = {k: v.to(self.device) for k, v in batch.items()}
                    
                    # Forward pass
                    outputs = self.model(**batch)
                    loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                    
                    # Backward pass
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                    
                    # Track metrics
                    train_loss += loss.item()
                    
                    if hasattr(outputs, 'logits'):
                        predictions = torch.argmax(outputs.logits, dim=-1)
                        train_correct += (predictions == batch['labels']).sum().item()
                        train_total += batch['labels'].size(0)
                    
                    # Update progress bar
                    progress_bar.set_postfix({'loss': loss.item()})
                
                # Calculate epoch metrics
                avg_train_loss = train_loss / len(train_loader)
                train_accuracy = train_correct / train_total if train_total > 0 else 0
                self.train_losses.append(avg_train_loss)
                self.train_accuracies.append(train_accuracy)
                
                # Log metrics
                mlflow.log_metrics({
                    'train_loss': avg_train_loss,
                    'train_accuracy': train_accuracy
                }, step=epoch)
                
                # Evaluation
                if eval_dataset:
                    eval_metrics = self.evaluate(eval_dataset)
                    self.eval_losses.append(eval_metrics['loss'])
                    
                    mlflow.log_metrics({
                        'eval_loss': eval_metrics['loss'],
                        'eval_accuracy': eval_metrics.get('accuracy', 0)
                    }, step=epoch)
        
        return {
            'train_losses': self.train_losses,
            'eval_losses': self.eval_losses,
            'train_accuracies': self.train_accuracies,
            'final_model': self.model
        }
    
    def evaluate(self, eval_dataset) -> Dict[str, float]:
        """Evaluate the model"""
        self.model.eval()
        
        eval_loader = DataLoader(
            eval_dataset,
            batch_size=self.batch_size,
            shuffle=False
        )
        
        total_loss = 0
        total_correct = 0
        total_samples = 0
        
        with torch.no_grad():
            for batch in tqdm(eval_loader, desc="Evaluating"):
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                outputs = self.model(**batch)
                loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                total_loss += loss.item()
                
                if hasattr(outputs, 'logits'):
                    predictions = torch.argmax(outputs.logits, dim=-1)
                    total_correct += (predictions == batch['labels']).sum().item()
                    total_samples += batch['labels'].size(0)
        
        metrics = {
            'loss': total_loss / len(eval_loader),
        }
        
        if total_samples > 0:
            metrics['accuracy'] = total_correct / total_samples
        
        return metrics
    
    def save_checkpoint(self, path: str) -> None:
        """Save model checkpoint"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': self.config,
            'train_losses': self.train_losses,
            'eval_losses': self.eval_losses
        }, path)
    
    def load_checkpoint(self, path: str) -> None:
        """Load model checkpoint"""
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.train_losses = checkpoint['train_losses']
        self.eval_losses = checkpoint['eval_losses']