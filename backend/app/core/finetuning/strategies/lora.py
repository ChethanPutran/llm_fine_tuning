from peft import LoraConfig, get_peft_model, TaskType
import torch.nn as nn
from ..base import FinetuningStrategy

class LoRAStrategy(FinetuningStrategy):
    """LoRA (Low-Rank Adaptation) fine-tuning strategy"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.lora_config = LoraConfig(
            task_type=TaskType.SEQ_CLS,
            inference_mode=False,
            r=config.get('lora_r', 8),
            lora_alpha=config.get('lora_alpha', 32),
            lora_dropout=config.get('lora_dropout', 0.1),
            target_modules=config.get('target_modules', ['q_proj', 'v_proj'])
        )
    
    def apply(self, model: nn.Module) -> nn.Module:
        """Apply LoRA to model"""
        return get_peft_model(model, self.lora_config)
    
    def get_trainable_params(self, model: nn.Module) -> int:
        """Count trainable parameters after applying strategy"""
        lora_model = self.apply(model)
        return sum(p.numel() for p in lora_model.parameters() if p.requires_grad)