
from dataclasses import dataclass

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


@dataclass
class FinetuningParameters:
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

class FinetuningConfig(BaseModel):
    """Fine-tuning configuration model"""
    strategy_type: str = Field(default="lora", description="Fine-tuning strategy (lora, prefix_tuning, adapter)")
    task_type: str = Field(default="classification", description="Task type (classification, regression, generation)")
    max_length: int = Field(default=512, ge=128, le=4096, description="Maximum sequence length for fine-tuning")
    batch_size: int = Field(default=16, ge=1, le=128, description="Batch size for fine-tuning")
    learning_rate: float = Field(default=5e-5, ge=1e-6, le=1e-3, description="Learning rate for fine-tuning")
    num_epochs: int = Field(default=3, ge=1, le=100, description="Number of epochs for fine-tuning")
    additional_params: FinetuningParameters = Field(default=FinetuningParameters(), description="Additional parameters for fine-tuning")
    metrics: Dict[str, Any] = Field(default_factory=dict)
    trainable_params: Optional[int] = None
    output_model_path: Optional[str] = None
