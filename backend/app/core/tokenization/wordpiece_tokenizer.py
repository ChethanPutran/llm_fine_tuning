from typing import List, Dict, Any
from collections import defaultdict

from app.core.tokenization.config import TokenizationConfig
from .base import BaseTokenizer

class WordPieceTokenizer(BaseTokenizer):
    """WordPiece tokenizer implementation (BERT-style)"""
    
    def __init__(self, config: TokenizationConfig):
        super().__init__(config)
        self.unk_token = config.default_tokens.unk_token
        self.pad_token = config.default_tokens.pad_token
        self.cls_token = config.default_tokens.cls_token
        self.sep_token = config.default_tokens.sep_token
        self.mask_token = config.default_tokens.mask_token
        
    def train(self, texts: List[str]) -> None:
        """Train WordPiece tokenizer"""
        # Initialize vocabulary with special tokens
        self.vocab = {
            self.pad_token: 0,
            self.unk_token: 1,
            self.cls_token: 2,
            self.sep_token: 3,
            self.mask_token: 4
        }
        next_id = len(self.vocab)
        
        # Initialize with character vocabulary
        chars = set()
        for text in texts:
            for char in text:
                chars.add(char)
        
        for char in sorted(chars):
            if char not in self.vocab:
                self.vocab[char] = next_id
                next_id += 1
        
        # Build initial word inventory
        words = []
        for text in texts:
            words.extend(text.split())
        
        # Count word frequencies
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        
        # Learn subword units
        target_vocab_size = self.config.get('vocab_size', 30000)
        
        while len(self.vocab) < target_vocab_size:
            # Score all possible splits
            best_score = -1
            best_subword = None
            
            for word, count in word_counts.items():
                subwords = self._get_subwords(word)
                
                for i in range(len(subwords) - 1):
                    for j in range(i + 1, len(subwords) + 1):
                        candidate = ''.join(subwords[i:j])
                        if len(candidate) > 1 and candidate not in self.vocab:
                            score = self._compute_score(candidate, word_counts)
                            
                            if score > best_score:
                                best_score = score
                                best_subword = candidate
            
            if best_subword is None:
                break
                
            # Add best subword to vocabulary
            self.vocab[best_subword] = next_id
            next_id += 1
            
            # Update word tokenization
            new_word_counts = defaultdict(int)
            for word, count in word_counts.items():
                tokenized = self._tokenize_word(word)
                new_word_counts[word] = count
            
            word_counts = new_word_counts
        
        # Build inverse vocabulary
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs"""
        tokens = []
        
        # Add CLS token
        tokens.append(self.vocab[self.cls_token])
        
        # Tokenize words
        words = text.split()
        for word in words:
            word_tokens = self._tokenize_word(word)
            for token in word_tokens:
                tokens.append(self.vocab.get(token, self.vocab[self.unk_token]))
        
        # Add SEP token
        tokens.append(self.vocab[self.sep_token])
        
        return tokens
    
    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs to text"""
        tokens = []
        
        for token_id in token_ids:
            token = self.inverse_vocab.get(token_id, self.unk_token)
            
            # Skip special tokens
            if token in [self.cls_token, self.sep_token, self.pad_token]:
                continue
                
            tokens.append(token)
        
        # Join tokens and handle ## prefixes
        text = ''
        for token in tokens:
            if token.startswith('##'):
                text += token[2:]
            else:
                text += ' ' + token
        
        return text.strip()
    
    def _tokenize_word(self, word: str) -> List[str]:
        """Tokenize a single word"""
        if word in self.vocab:
            return [word]
        
        subwords = []
        remaining = word
        
        while remaining:
            # Find the longest subword that matches
            matched = False
            for i in range(len(remaining), 0, -1):
                subword = remaining[:i]
                
                # Check with and without ## prefix
                if subword in self.vocab:
                    subwords.append(subword)
                    remaining = remaining[i:]
                    matched = True
                    break
                    
                subword_with_prefix = '##' + subword
                if subword_with_prefix in self.vocab:
                    subwords.append(subword_with_prefix)
                    remaining = remaining[i:]
                    matched = True
                    break
            
            if not matched:
                # Unknown character
                subwords.append(self.unk_token)
                remaining = remaining[1:]
        
        return subwords
    
    def _get_subwords(self, word: str) -> List[str]:
        """Get all subwords of a word"""
        subwords = []
        for i in range(len(word)):
            for j in range(i + 1, len(word) + 1):
                subwords.append(word[i:j])
        return list(set(subwords))
    
    def _compute_score(self, candidate: str, word_counts: Dict[str, int]) -> float:
        """Compute score for candidate subword"""
        # Simplified scoring based on frequency and length
        score = 0
        for word, count in word_counts.items():
            if candidate in word:
                score += count * len(candidate)
        
        return score
    
    def get_vocab_size(self) -> int:
        return len(self.vocab)