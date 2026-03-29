from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
import numpy as np

class BaseTokenizer(ABC):
    """Abstract base class for tokenizers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vocab_size = config.get('vocab_size', 50000)
        self.vocab = {}
        self.inverse_vocab = {}
    
    @abstractmethod
    def train(self, texts: List[str]) -> None:
        """Train tokenizer on texts"""
        pass
    
    @abstractmethod
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs"""
        pass
    
    @abstractmethod
    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs to text"""
        pass
    
    @abstractmethod
    def get_vocab_size(self) -> int:
        """Return vocabulary size"""
        pass
    
    def save(self, path: str) -> None:
        """Save tokenizer to disk"""
        import json
        with open(path, 'w') as f:
            json.dump({
                'vocab': self.vocab,
                'config': self.config
            }, f)
    
    def load(self, path: str) -> None:
        """Load tokenizer from disk"""
        import json
        with open(path, 'r') as f:
            data = json.load(f)
            self.vocab = data['vocab']
            self.inverse_vocab = {v: k for k, v in self.vocab.items()}
            self.config = data['config']