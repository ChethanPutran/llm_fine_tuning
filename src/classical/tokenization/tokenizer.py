from collections import defaultdict, Counter
import re

class BPETokenizer:
    def __init__(self, vocab_size=10000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.merges = {}
    
    def get_stats(self, vocab):
        pairs = defaultdict(int)
        for word, freq in vocab.items():
            symbols = word.split()
            for i in range(len(symbols)-1):
                pairs[symbols[i], symbols[i+1]] += freq
        return pairs
    
    def merge_vocab(self, pair, vocab):
        new_vocab = {}
        bigram = re.escape(' '.join(pair))
        p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
        for word in vocab:
            w_out = p.sub(''.join(pair), word)
            new_vocab[w_out] = vocab[word]
        return new_vocab
    
    def train(self, text):
        # Preprocess text
        text = text.lower()
        words = text.split()
        
        # Initialize vocabulary with characters
        vocab = Counter([' '.join(word) + ' </w>' for word in words])
        
        for i in range(self.vocab_size - 256):  # Reserve space for byte tokens
            pairs = self.get_stats(vocab)
            if not pairs:
                break
            
            # Find most frequent pair
            best_pair = max(pairs, key=pairs.get)
            self.merges[best_pair] = i
            
            # Merge the pair
            vocab = self.merge_vocab(best_pair, vocab)
        
        # Create final vocabulary
        self.vocab = {i: chr(i) for i in range(256)}  # Add byte tokens
        for (c1, c2), idx in self.merges.items():
            self.vocab[idx + 256] = c1 + c2
    
    def tokenize(self, text):
        text = text.lower()
        words = text.split()
        tokens = []
        
        for word in words:
            word = list(word) + ['</w>']
            while len(word) > 1:
                pairs = [(word[i], word[i+1]) for i in range(len(word)-1)]
                pair = min(pairs, key=lambda p: self.merges.get(p, float('inf')))
                
                if pair not in self.merges:
                    break
                
                # Merge the pair
                idx = word.index(pair[0])
                word = word[:idx] + [pair[0] + pair[1]] + word[idx+2:]
            
            # Convert to token IDs
            for char in word:
                if char in self.vocab.values():
                    token_id = [k for k, v in self.vocab.items() if v == char][0]
                    tokens.append(token_id)
                else:
                    # Handle unknown tokens
                    tokens.extend([ord(c) for c in char])
        
        return tokens
    
    def detokenize(self, tokens):
        text = []
        for token in tokens:
            if token in self.vocab:
                text.append(self.vocab[token])
            else:
                text.append(chr(token))
        
        # Remove end-of-word tokens and join
        text = ''.join(text).replace('</w>', ' ')
        return text.strip()

# Example usage
if __name__ == "__main__":
    # Sample training text
    training_text = """
    natural language processing is a field of artificial intelligence.
    tokenization is an important step in nlp.
    byte pair encoding is a popular tokenization method.
    """
    
    # Train BPE tokenizer
    bpe = BPETokenizer(vocab_size=300)
    bpe.train(training_text)
    
    # Tokenize a new text
    test_text = "natural language processing with byte pair encoding"
    tokens = bpe.tokenize(test_text)
    print(f"Original text: {test_text}")
    print(f"Tokens: {tokens}")
    print(f"Tokenized length: {len(tokens)}")
    
    # Detokenize
    detokenized = bpe.detokenize(tokens)
    print(f"Detokenized: {detokenized}")
