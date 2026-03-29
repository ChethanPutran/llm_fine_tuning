from typing import Dict, Any
from .base import BaseTokenizer
from .bpe_tokenizer import BPETokenizer
from .wordpiece_tokenizer import WordPieceTokenizer
from .sentencepiece_tokenizer import SentencePieceTokenizer

class TokenizerFactory:
    """Factory pattern for tokenizer creation"""
    
    _tokenizers = {
        'bpe': BPETokenizer,
        'wordpiece': WordPieceTokenizer,
        'sentencepiece': SentencePieceTokenizer
    }
    
    @classmethod
    def get_tokenizer(cls, tokenizer_type: str, config: Dict[str, Any]) -> BaseTokenizer:
        """Get tokenizer instance by type"""
        tokenizer_class = cls._tokenizers.get(tokenizer_type)
        if not tokenizer_class:
            raise ValueError(f"Unknown tokenizer type: {tokenizer_type}")
        return tokenizer_class(config)
    
    @classmethod
    def register_tokenizer(cls, name: str, tokenizer_class):
        """Register new tokenizer type"""
        cls._tokenizers[name] = tokenizer_class