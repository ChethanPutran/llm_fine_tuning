import sentencepiece as spm
from typing import List, Dict, Any
import os
from .base import BaseTokenizer

class SentencePieceTokenizer(BaseTokenizer):
    """SentencePiece tokenizer implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_path = config.get('model_path', 'sentencepiece.model')
        self.sp = None
        
    def train(self, texts: List[str]) -> None:
        """Train SentencePiece tokenizer"""
        # Save texts to temporary file
        temp_file = 'temp_corpus.txt'
        with open(temp_file, 'w', encoding='utf-8') as f:
            for text in texts:
                f.write(text + '\n')
        
        # Train SentencePiece model
        model_prefix = self.model_path.replace('.model', '')
        
        spm.SentencePieceTrainer.train(
            input=temp_file,
            model_prefix=model_prefix,
            vocab_size=self.vocab_size,
            character_coverage=self.config.get('character_coverage', 0.9995),
            model_type=self.config.get('model_type', 'unigram'),
            input_sentence_size=self.config.get('input_sentence_size', 1000000),
            shuffle_input_sentence=self.config.get('shuffle', True),
            normalization_rule_name=self.config.get('normalization', 'nmt_nfkc'),
            remove_extra_whitespaces=self.config.get('remove_whitespace', True),
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