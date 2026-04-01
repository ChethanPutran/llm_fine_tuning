
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

import torch

class OptimizerType(str, Enum):
    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"

class SchedulerType(str, Enum):
    LINEAR = "linear"
    COSINE = "cosine"
    CONSTANT = "constant"

@dataclass
class TrainingParameters:
    """Training configuration dataclass"""
    
    # Model parameters
    model_name: str = "bert-base-uncased"
    model_type: str = "bert"
    
    # Training hyperparameters
    learning_rate: float = 2e-5
    num_epochs: int = 3
    batch_size: int = 16
    eval_batch_size: int = 32
    
    # Optimizer settings
    optimizer: OptimizerType = OptimizerType.ADAMW
    weight_decay: float = 0.01
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8
    
    # Scheduler settings
    scheduler: SchedulerType = SchedulerType.LINEAR
    warmup_steps: int = 0
    warmup_ratio: float = 0.0
    
    # Regularization
    dropout: float = 0.1
    attention_dropout: float = 0.1
    
    # Gradient settings
    max_grad_norm: float = 1.0
    gradient_accumulation_steps: int = 1
    
    # Data parameters
    max_seq_length: int = 512
    pad_to_max_length: bool = False
    
    # Validation
    eval_steps: int = 500
    save_steps: int = 1000
    logging_steps: int = 100
    
    # Mixed precision
    fp16: bool = False
    fp16_opt_level: str = "O1"
    
    # Distributed training
    local_rank: int = -1
    distributed: bool = False
    n_gpu: int = 1
    
    # Checkpointing
    output_dir: str = "./outputs"
    overwrite_output_dir: bool = True
    save_total_limit: Optional[int] = 3
    
    # Early stopping
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.01
    
    # MLflow tracking
    use_mlflow: bool = True
    mlflow_experiment: str = "llm_finetuning"
    mlflow_uri: str = "./mlruns"
    mlflow_params: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'learning_rate': self.learning_rate,
            'num_epochs': self.num_epochs,
            'batch_size': self.batch_size,
            'eval_batch_size': self.eval_batch_size,
            'optimizer': self.optimizer.value,
            'weight_decay': self.weight_decay,
            'scheduler': self.scheduler.value,
            'warmup_steps': self.warmup_steps,
            'max_seq_length': self.max_seq_length,
            'fp16': self.fp16,
            'output_dir': self.output_dir
        }



class TrainingConfig(BaseModel):
    """Training configuration model"""
    device: str = Field(default="cuda" if torch.cuda.is_available() else "cpu", description="Device for training")
    error_function: str = Field(default="cross_entropy", description="Loss function for training")
    optimizer: str = Field(default="adamw", description="Optimizer for training")
    batch_size: int = Field(default=16, ge=1, le=128, description="Batch size for training")
    learning_rate: float = Field(default=5e-5, ge=1e-6, le=1e-3, description="Learning rate for training")
    num_epochs: int = Field(default=3, ge=1, le=100, description="Number of epochs for training")
    max_length: int = Field(default=512, ge=128, le=4096, description="Maximum sequence length for training")
    additional_params: TrainingParameters = Field(default_factory=TrainingParameters, description="Additional parameters for training")
    output_model_path: Optional[str] = None
    