from abc import ABC, abstractmethod


class Tokenizer(ABC):
    def __init__(self, vocab_size=30522, max_length=512):
        self.vocab_size = vocab_size
        self.max_length = max_length
        # Initialize common attributes here (e.g., vocab, special tokens)
    @abstractmethod
    def tokenize(self, text):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def detokenize(self, tokens):
        raise NotImplementedError("Subclasses must implement this method")

