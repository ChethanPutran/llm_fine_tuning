import sentencepiece as spm
from typing import List, Dict, Any
import os
from .base import BaseTokenizer
from .config import TokenizationConfig

class SentencePieceTokenizer(BaseTokenizer):
    """SentencePiece tokenizer implementation"""
    
    def __init__(self, config: TokenizationConfig):
        super().__init__(config)
        self.model_path = config.tokenization_model_config.model_path
        self.sp = None
        self.model_config = config.tokenization_model_config
        
    def train(self, texts: List[str]) -> None:
        """Train SentencePiece tokenizer"""
        # Save texts to temporary file
        temp_file = 'temp_corpus.txt'
        with open(temp_file, 'w', encoding='utf-8') as f:
            for text in texts:
                f.write(text + '\n')
        
        # Train SentencePiece model
        model_prefix = self.model_path.replace('.model', '')
        
        spm.SentencePieceTrainer.Train(
            input=temp_file,
            model_prefix=model_prefix,
            vocab_size=self.vocab_size,
            character_coverage=self.model_config.character_coverage,
            model_type=self.model_config.model_name,
            input_sentence_size=self.model_config.input_sentence_size,
            shuffle_input_sentence=self.model_config.shuffle_input_sentence,
            normalization_rule_name=self.model_config.normalization_rule_name,
            remove_extra_whitespaces=self.model_config.remove_extra_whitespaces,
            pad_id=0,
            unk_id=1,
            bos_id=2,
            eos_id=3
        )
        
        # Load the trained model
        self.sp = spm.SentencePieceProcessor()
        self.sp.Load(f"{model_prefix}.model")
        
        # Build vocabulary
        self.vocab = {}
        for i in range(self.sp.GetPieceSize()):
            piece = self.sp.IdToPiece(i)
            self.vocab[piece] = i
        
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
        
        # Clean up
        os.remove(temp_file)
        os.remove(f"{model_prefix}.model")
        os.remove(f"{model_prefix}.vocab")
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs"""
        if self.sp is None:
            raise ValueError("Tokenizer not trained or loaded")
        
        return self.sp.EncodeAsIds(text)
    
    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs to text"""
        if self.sp is None:
            raise ValueError("Tokenizer not trained or loaded")
        
        return self.sp.DecodeIds(token_ids)
    
    def get_vocab_size(self) -> int:
        if self.sp:
            return self.sp.GetPieceSize()
        return len(self.vocab)
    
    def load(self, path: str) -> None:
        """Load pre-trained tokenizer"""
        self.sp = spm.SentencePieceProcessor()
        self.sp.Load(path)
        
        # Build vocabulary
        self.vocab = {}
        for i in range(self.sp.GetPieceSize()):
            piece = self.sp.IdToPiece(i)
            self.vocab[piece] = i
        
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
    
    def save(self, path: str) -> None:
        """Save tokenizer to disk"""
        if self.sp:
            # SentencePiece saves its own files
            import shutil
            shutil.copy(self.model_path, path)