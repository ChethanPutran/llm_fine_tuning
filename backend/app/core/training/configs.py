from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class OptimizerType(str, Enum):
    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"

class SchedulerType(str, Enum):
    LINEAR = "linear"
    COSINE = "cosine"
    CONSTANT = "constant"

@dataclass
class TrainingConfig:
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

@dataclass
class FinetuningConfig(TrainingConfig):
    """Fine-tuning specific configuration"""
    
    # Fine-tuning strategy
    strategy: str = "full"  # full, lora, adapter, prefix_tuning
    
    # LoRA specific
    lora_r: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    lora_target_modules: List[str] = None
    
    # Adapter specific
    adapter_bottleneck_size: int = 64
    
    # Prefix tuning specific
    prefix_length: int = 10
    prefix_projection: bool = True
    
    def __post_init__(self):
        if self.lora_target_modules is None:
            self.lora_target_modules = ['q_proj', 'v_proj']