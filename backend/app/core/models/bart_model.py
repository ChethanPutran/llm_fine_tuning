from transformers import BartForConditionalGeneration, BartTokenizer, BartConfig
import torch
from .base import BaseModel

class BARTModel(BaseModel):
    """BART model implementation for sequence-to-sequence tasks"""
    
    def __init__(self, model_name: str, config: dict):
        super().__init__(model_name, config)
        self.max_length = config.get('max_length', 512)
        self.num_beams = config.get('num_beams', 4)
        
    def load_model(self) -> None:
        """Load BART model and tokenizer"""
        self.tokenizer = BartTokenizer.from_pretrained(self.model_name)
        self.model = BartForConditionalGeneration.from_pretrained(self.model_name)
        
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None,
                decoder_input_ids: torch.Tensor = None, labels: torch.Tensor = None,
                **kwargs) -> torch.Tensor:
        """Forward pass for BART"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            labels=labels,
            **kwargs
        )
        return outputs
    
    def generate(self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None,
                 **kwargs) -> torch.LongTensor :
        """Generate text using BART"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        return self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=self.max_length,
            num_beams=self.num_beams,
            **kwargs
        )
    
    def save(self, path: str) -> None:
        """Save model and tokenizer"""
        if self.model:
            self.model.save_pretrained(f"{path}/model")
            self.tokenizer.save_pretrained(f"{path}/tokenizer")
    
    def load(self, path: str) -> None:
        """Load model and tokenizer from disk"""
        self.tokenizer = BartTokenizer.from_pretrained(f"{path}/tokenizer")
        self.model = BartForConditionalGeneration.from_pretrained(f"{path}/model")