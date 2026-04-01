
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class EvaluationConfig(BaseModel):
    """Model evaluation configuration model"""
    metrics: List[str] = Field(default_factory=lambda: ["accuracy"], description="List of evaluation metrics to compute")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for model evaluation")
    model_path: str = Field(default="")
    dataset_path: str = Field(default="")
    predictions: Optional[List[Dict[str, Any]]] = None
    evaluation_results: Dict[str, Any] = Field(default_factory=dict)
