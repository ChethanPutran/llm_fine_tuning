
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class OptimizationConfig(BaseModel):
    """Model optimization configuration model"""
    optimization_type: str = Field(default="quantization", description="Type of optimization (quantization, pruning, distillation)")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for model optimization")
    metrics: Dict[str, Any] = Field(default_factory=dict)
    original_size: Optional[int] = Field(default=None)
    optimized_size: Optional[int] = Field(default=None)
    compression_ratio: Optional[float] = Field(default=None)
    input_model_path: str = Field(default="")
    output_model_path: Optional[str] = Field(default=None)
