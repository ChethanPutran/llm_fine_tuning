from .tokenizer import Tokenizer    
class SentencePiece(Tokenizer):
    def __init__(self, vocab_size=30522, max_length=512):
        super().__init__(vocab_size, max_length)
        # Initialize SentencePiece-specific attributes here (e.g., merges, vocab)
    
    def tokenize(self, text):
        # Implement SentencePiece tokenization logic here
        pass
    
    def detokenize(self, tokens):
        # Implement SentencePiece detokenization logic here
        pass