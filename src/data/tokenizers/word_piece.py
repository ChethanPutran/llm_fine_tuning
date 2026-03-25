from .tokenizer import Tokenizer    
class WordPiece(Tokenizer):
    def __init__(self, vocab_size=30522, max_length=512):
        super().__init__(vocab_size, max_length)
        # Initialize WordPiece-specific attributes here (e.g., vocab)
    
    def tokenize(self, text):
        # Implement WordPiece tokenization logic here
        pass
    
    def detokenize(self, tokens):
        # Implement WordPiece detokenization logic here
        pass