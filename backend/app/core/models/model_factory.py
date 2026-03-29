from typing import Dict, Any
from .base import BaseModel
from .bert_model import BERTModel
from .bart_model import BARTModel
from .gpt_model import GPTModel
from .vlm_model import VLMModel
from .vit_model import ViTModel

class ModelFactory:
    """Factory pattern for model creation"""
    
    _models = {
        'bert': BERTModel,
        'bart': BARTModel,
        'gpt': GPTModel,
        'vlm': VLMModel,
        'vit': ViTModel
    }
    
    @classmethod
    def get_model(cls, model_type: str, model_name: str, config: Dict[str, Any]) -> BaseModel:
        """Get model instance by type"""
        model_class = cls._models.get(model_type)
        if not model_class:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model = model_class(model_name, config)
        model.load_model()
        return model
    
    @classmethod
    def register_model(cls, name: str, model_class):
        """Register new model type"""
        cls._models[name] = model_class