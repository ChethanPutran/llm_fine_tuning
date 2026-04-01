
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field



class ModelConfig(BaseModel):
    """Model configuration for training and fine-tuning"""
    model_name: str
    tokenizer: str
    model_path: Optional[str] = None
    model_type: str = ""
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for model configuration")    
