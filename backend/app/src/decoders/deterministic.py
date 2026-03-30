from .base import BaseDecoder
import torch

class GreedyDecoder(BaseDecoder):
    def __init__(self, model) -> None:
        super().__init__(model)

    def decode(self, input_ids):
        # Implement greedy decoding logic here
        pass

class BeamSearchDecoder(BaseDecoder):
    def __init__(self, model) -> None:
        super().__init__(model)

    def decode(self, input_ids):
        # Implement beam search decoding logic here
        pass

