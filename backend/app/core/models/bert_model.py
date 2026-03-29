from typing import Dict, Any
from transformers import BertForSequenceClassification, BertTokenizer, BertConfig
import torch
from .base import BaseModel

class BERTModel(BaseModel):
    """BERT model implementation"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.num_labels = config.get('num_labels', 2)
        
    def load_model(self) -> None:
        """Load BERT model"""
        self.tokenizer = BertTokenizer.from_pretrained(self.model_name)
        self.model = BertForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=self.num_labels
        )
    
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None,
                labels: torch.Tensor = None, **kwargs) -> torch.Tensor:
        """Forward pass"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
            **kwargs
        )
        return outputs
    
    def save(self, path: str) -> None:
        """Save model and tokenizer"""
        if self.model:
            self.model.save_pretrained(f"{path}/model")
            self.tokenizer.save_pretrained(f"{path}/tokenizer")
    
    def load(self, path: str) -> None:
        """Load model and tokenizer"""
        self.tokenizer = BertTokenizer.from_pretrained(f"{path}/tokenizer")
        self.model = BertForSequenceClassification.from_pretrained(f"{path}/model")