from transformers import GPT2LMHeadModel, GPT2Tokenizer, GPT2Config
import torch
from .base import BaseModel

class GPTModel(BaseModel):
    """GPT model implementation for causal language modeling"""
    
    def __init__(self, model_name: str, config: dict):
        super().__init__(model_name, config)
        self.max_length = config.get('max_length', 512)
        self.temperature = config.get('temperature', 0.7)
        self.top_k = config.get('top_k', 50)
        self.top_p = config.get('top_p', 0.9)
        
    def load_model(self) -> None:
        """Load GPT model and tokenizer"""
        self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
        
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None,
                labels: torch.Tensor = None, **kwargs) -> torch.Tensor:
        """Forward pass for GPT"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
            **kwargs
        )
        return outputs
    
    def generate(self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None,
                 **kwargs) -> torch.LongTensor :
        """Generate text using GPT"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        return self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=self.max_length,
            temperature=self.temperature,
            top_k=self.top_k,
            top_p=self.top_p,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            **kwargs
        )
    
    def save(self, path: str) -> None:
        """Save model and tokenizer"""
        if self.model:
            self.model.save_pretrained(f"{path}/model")
            self.tokenizer.save_pretrained(f"{path}/tokenizer")
    
    def load(self, path: str) -> None:
        """Load model and tokenizer from disk"""
        self.tokenizer = GPT2Tokenizer.from_pretrained(f"{path}/tokenizer")
        self.model = GPT2LMHeadModel.from_pretrained(f"{path}/model")