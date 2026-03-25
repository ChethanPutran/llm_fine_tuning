from abc import ABC, abstractmethod


class BaseDecoder:
    """Base class for decoders."""
    def __init__(self, model):
        self.model = model

    @abstractmethod
    def decode(self, input_ids):
        """Decode the input ids to text."""
        pass


