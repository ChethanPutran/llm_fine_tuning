
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field



class ModelConfig(BaseModel):
    """Model configuration for training and fine-tuning"""
    model_name: str = Field(default="default_model", description="Name or identifier of the model")
    tokenizer: str = Field(default="default_tokenizer", description="Tokenizer to use with the model")
    model_path: Optional[str] = Field(default=None, description="Path to the model files (if applicable)")
    model_type: str = Field(default="default_model_type", description="Type of model (e.g., transformer, RNN, etc.)")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for model configuration")    
