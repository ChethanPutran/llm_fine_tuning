from transformers import BlipForConditionalGeneration, BlipProcessor
import torch
from PIL import Image
from .base import BaseModel

class VLMModel(BaseModel):
    """Vision-Language Model (BLIP) for image captioning and VQA"""
    
    def __init__(self, model_name: str, config: dict):
        super().__init__(model_name, config)
        self.max_length = config.get('max_length', 50)
        self.num_beams = config.get('num_beams', 3)
        
    def load_model(self) -> None:
        """Load VLM model and processor"""
        self.processor = BlipProcessor.from_pretrained(self.model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(self.model_name)
        
    def forward(self, input_ids: torch.Tensor, pixel_values: torch.Tensor, 
                attention_mask: torch.Tensor = None, **kwargs) -> torch.Tensor:
        """Forward pass for VLM"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        outputs = self.model(
            pixel_values=pixel_values,
            input_ids=input_ids,
            attention_mask=attention_mask,
            **kwargs
        )
        return outputs
    
    def generate_caption(self, image: Image.Image, text: str = None) -> str:
        """Generate caption for image"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        if text:
            inputs = self.processor(image, text, return_tensors="pt")
        else:
            inputs = self.processor(image, return_tensors="pt")
        
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_length=self.max_length,
                num_beams=self.num_beams
            )
            caption = self.processor.decode(out[0], skip_special_tokens=True)
        
        return caption
    
    def visual_question_answering(self, image: Image.Image, question: str) -> str:
        """Answer question about image"""
        return self.generate_caption(image, question)
    
    def save(self, path: str) -> None:
        """Save model and processor"""
        if self.model:
            self.model.save_pretrained(f"{path}/model")
            self.processor.save_pretrained(f"{path}/processor")
    
    def load(self, path: str) -> None:
        """Load model and processor from disk"""
        self.processor = BlipProcessor.from_pretrained(f"{path}/processor")
        self.model = BlipForConditionalGeneration.from_pretrained(f"{path}/model")