from transformers import ViTForImageClassification, ViTFeatureExtractor, ViTConfig
import torch
import torch.nn as nn
from PIL import Image
from .base import BaseModel

class ViTModel(BaseModel):
    """Vision Transformer model for image classification"""
    
    def __init__(self, model_name: str, config: dict):
        super().__init__(model_name, config)
        self.num_labels = config.get('num_labels', 1000)
        self.image_size = config.get('image_size', 224)
        
    def load_model(self) -> None:
        """Load ViT model and feature extractor"""
        self.feature_extractor = ViTFeatureExtractor.from_pretrained(self.model_name)
        self.model = ViTForImageClassification.from_pretrained(
            self.model_name,
            num_labels=self.num_labels
        )
    
    def forward(self, input_ids: torch.Tensor, labels: torch.Tensor = None,
                **kwargs) -> torch.Tensor:
        """Forward pass for ViT"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        outputs = self.model(
            pixel_values=input_ids,
            labels=labels,
            **kwargs
        )
        return outputs
    
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for ViT"""
        inputs = self.feature_extractor(images=image, return_tensors="pt")
        return inputs['pixel_values']
    
    def predict(self, image: Image.Image) -> torch.Tensor:
        """Predict class for image"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        pixel_values = self.preprocess_image(image)
        with torch.no_grad():
            outputs = self.model(pixel_values=pixel_values)
            logits = outputs.logits
            predictions = torch.argmax(logits, dim=-1)
        
        return predictions
    
    def save(self, path: str) -> None:
        """Save model and feature extractor"""
        if self.model:
            self.model.save_pretrained(f"{path}/model")
            self.feature_extractor.save_pretrained(f"{path}/feature_extractor")
    
    def load(self, path: str) -> None:
        """Load model and feature extractor from disk"""
        self.feature_extractor = ViTFeatureExtractor.from_pretrained(f"{path}/feature_extractor")
        self.model = ViTForImageClassification.from_pretrained(f"{path}/model")