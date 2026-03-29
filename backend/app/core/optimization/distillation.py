import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from typing import Dict, Any, Union, Optional
import numpy as np
from .base import BaseOptimizer

class DistillationOptimizer(BaseOptimizer):
    """Knowledge distillation optimizer"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.temperature = config.get('temperature', 3.0)
        self.alpha = config.get('alpha', 0.7)  # Distillation loss weight
        self.num_epochs = config.get('num_epochs', 3)
        self.learning_rate = config.get('learning_rate', 1e-4)
        self.student_config = config.get('student_config', {
            'hidden_size': 384,  # Half of teacher
            'num_layers': 6,      # Half of teacher
            'num_heads': 8
        })
        
    def optimize(self, model: Union[nn.Module, str]) -> nn.Module:
        """Perform knowledge distillation"""
        # Load teacher model
        if isinstance(model, str):
            teacher = self.load_model(model)
        else:
            teacher = model
        
        # Create student model (smaller version)
        student = self._create_student_model(teacher)
        
        # Distill knowledge
        distilled_model = self._distill_knowledge(teacher, student)
        
        self.optimized_model = distilled_model
        self.optimized_size = self._calculate_model_size(distilled_model)
        
        return distilled_model
    
    def _create_student_model(self, teacher: nn.Module) -> nn.Module:
        """Create smaller student model based on teacher architecture"""
        from transformers import AutoConfig, AutoModel
        
        # Get teacher config
        if hasattr(teacher, 'config'):
            teacher_config = teacher.config
            # Create student config with reduced dimensions
            student_config = AutoConfig.from_pretrained(teacher.config._name_or_path)
            student_config.hidden_size = self.student_config['hidden_size']
            student_config.num_hidden_layers = self.student_config['num_layers']
            student_config.num_attention_heads = self.student_config['num_heads']
            student_config.intermediate_size = student_config.hidden_size * 4
            
            # Create student model
            student = AutoModel.from_config(student_config)
        else:
            # Fallback: create a simple distilled model
            student = self._create_simple_student(teacher)
        
        return student
    
    def _create_simple_student(self, teacher: nn.Module) -> nn.Module:
        """Create a simple distilled student model"""
        class DistilledModel(nn.Module):
            def __init__(self, input_dim, hidden_dim, output_dim):
                super().__init__()
                self.fc1 = nn.Linear(input_dim, hidden_dim)
                self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
                self.fc3 = nn.Linear(hidden_dim // 2, output_dim)
                self.dropout = nn.Dropout(0.1)
                self.relu = nn.ReLU()
                
            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.dropout(x)
                x = self.relu(self.fc2(x))
                x = self.dropout(x)
                x = self.fc3(x)
                return x
        
        # Get dimensions from teacher
        if hasattr(teacher, 'classifier'):
            output_dim = teacher.classifier.out_features
        else:
            output_dim = 2
            
        input_dim = 768  # Default BERT dimension
        
        return DistilledModel(input_dim, 384, output_dim)
    
    def _distill_knowledge(self, teacher: nn.Module, student: nn.Module) -> nn.Module:
        """Perform knowledge distillation training"""
        teacher.eval()
        student.train()
        
        optimizer = torch.optim.Adam(student.parameters(), lr=self.learning_rate)
        
        # Dummy training data for demonstration
        # In production, this should use actual training data
        for epoch in range(self.num_epochs):
            total_loss = 0
            # Simulate training batches
            for batch_idx in range(100):
                # Create dummy data
                batch_size = 32
                input_ids = torch.randint(0, 1000, (batch_size, 512))
                attention_mask = torch.ones(batch_size, 512)
                
                # Get teacher predictions
                with torch.no_grad():
                    teacher_outputs = teacher(input_ids, attention_mask=attention_mask)
                    if hasattr(teacher_outputs, 'logits'):
                        teacher_logits = teacher_outputs.logits
                    else:
                        teacher_logits = teacher_outputs
                    
                    # Soften with temperature
                    teacher_soft = F.softmax(teacher_logits / self.temperature, dim=-1)
                
                # Get student predictions
                student_logits = student(input_ids, attention_mask=attention_mask)
                if hasattr(student_logits, 'logits'):
                    student_logits = student_logits.logits
                
                # Calculate distillation loss
                student_soft = F.log_softmax(student_logits / self.temperature, dim=-1)
                distillation_loss = F.kl_div(student_soft, teacher_soft, reduction='batchmean')
                
                # Calculate student loss (if labels available)
                student_loss = torch.tensor(0.0)
                
                # Combined loss
                loss = self.alpha * distillation_loss + (1 - self.alpha) * student_loss
                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / 100
            print(f"Distillation epoch {epoch + 1}, loss: {avg_loss:.4f}")
        
        return student
    
    def get_metrics(self, model: nn.Module) -> Dict[str, Any]:
        """Get distillation metrics"""
        metrics = {
            'original_size_mb': self.original_size / (1024 * 1024),
            'optimized_size_mb': self.optimized_size / (1024 * 1024),
            'compression_ratio': self.calculate_compression_ratio(),
            'temperature': self.temperature,
            'alpha': self.alpha,
            'student_config': self.student_config
        }
        
        # Calculate parameter reduction
        if self.original_model and self.optimized_model:
            original_params = sum(p.numel() for p in self.original_model.parameters())
            optimized_params = sum(p.numel() for p in self.optimized_model.parameters())
            metrics['parameter_reduction'] = original_params / optimized_params
        
        return metrics