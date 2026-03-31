from .base import BaseDecoder
import torch

class RandomSamplingDecoder(BaseDecoder):
    def __init__(self, model) -> None:
        super().__init__(model)

    def decode(self, input_ids):
        # Implement random sampling decoding logic here
        pass

class TopKDecoder(BaseDecoder):
    def __init__(self, model) -> None:
        super().__init__(model)

    def decode(self, input_ids):
        # Implement top-k decoding logic here
        pass

class TopPDecoder(BaseDecoder):
    def __init__(self, model) -> None:
        super().__init__(model)

    def decode(self, input_ids):
        # Implement top-p decoding logic here
        pass

