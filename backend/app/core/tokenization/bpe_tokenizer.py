from typing import Any, List, Dict, Tuple
from collections import defaultdict
from .base import BaseTokenizer
from .config import TokenizationConfig

class BPETokenizer(BaseTokenizer):
    """Byte Pair Encoding tokenizer implementation"""
    
    def __init__(self, config: TokenizationConfig):
        super().__init__(config)
        self.merges = {}  # Pair -> new token mapping
        
    def train(self, texts: List[str], num_merges: int = 10000):
        """Train BPE tokenizer"""
        # Pre-tokenize into words
        words = []
        for text in texts:
            words.extend(text.split())
        
        # Initialize with character-level tokens
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        
        # Initialize vocabulary with characters
        self.vocab = {chr(i): i for i in range(256)}
        next_id = len(self.vocab)
        
        # Perform merges
        for _ in range(min(num_merges, self.vocab_size)):
            pair_counts = defaultdict(int)
            
            # Count pairs
            for word, count in word_counts.items():
                symbols = self._get_symbols(word)
                for i in range(len(symbols) - 1):
                    pair = (symbols[i], symbols[i+1])
                    pair_counts[pair] += count
            
            if not pair_counts:
                break
            
            # Get most frequent pair
            best_pair = max(pair_counts, key=pair_counts.get)
            
            # Add merge
            self.merges[best_pair] = next_id
            self.vocab[''.join(best_pair)] = next_id
            next_id += 1
            
            # Update word counts with new merges
            new_word_counts = defaultdict(int)
            for word, count in word_counts.items():
                new_word = self._apply_merge(word, best_pair)
                new_word_counts[new_word] += count
            word_counts = new_word_counts
    
    def encode(self, text: str) -> List[int]:
        """Encode text using BPE"""
        words = text.split()
        token_ids = []
        
        for word in words:
            symbols = list(word)
            while len(symbols) > 1:
                # Find best pair to merge
                best_pair = None
                best_index = float('inf')
                
                for i in range(len(symbols) - 1):
                    pair = (symbols[i], symbols[i+1])
                    if pair in self.merges:
                        if self.merges[pair] < best_index:
                            best_pair = pair
                            best_index = self.merges[pair]
                
                if best_pair is None:
                    break
                
                # Merge the pair
                new_symbols = []
                i = 0
                while i < len(symbols):
                    if i < len(symbols) - 1 and (symbols[i], symbols[i+1]) == best_pair:
                        new_symbols.append(''.join(best_pair))
                        i += 2
                    else:
                        new_symbols.append(symbols[i])
                        i += 1
                symbols = new_symbols
            
            # Convert to token IDs
            for symbol in symbols:
                token_ids.append(self.vocab.get(symbol, self.vocab.get('<UNK>', 0)))
        
        return token_ids
    
    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs to text"""
        words = []
        current_word = []
        
        for token_id in token_ids:
            token = self.inverse_vocab.get(token_id, '<UNK>')
            if token == '<UNK>':
                words.append(''.join(current_word))
                current_word = []
                words.append('[UNK]')
            else:
                current_word.append(token)
        
        if current_word:
            words.append(''.join(current_word))
        
        return ' '.join(words)
    
    def _get_symbols(self, word: str) -> List[str]:
        """Split word into symbols"""
        return list(word)
    
    def _apply_merge(self, word: str, pair: Tuple[str, str]) -> str:
        """Apply a merge to a word"""
        result = []
        i = 0
        while i < len(word):
            if i < len(word) - 1 and word[i] == pair[0] and word[i+1] == pair[1]:
                result.append(pair[0] + pair[1])
                i += 2
            else:
                result.append(word[i])
                i += 1
        return ''.join(result)
    
    def get_vocab_size(self) -> int:
        return len(self.vocab)