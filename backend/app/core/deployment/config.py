
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class DeploymentConfig(BaseModel):
    """Model deployment configuration model"""
    serving_framework: str = Field(default="torchserve", description="Serving framework for deployment (torchserve, tensorflow_serving, custom)")
    deployment_target: str = Field(default="local", description="Deployment target (local, aws, gcp, azure)")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for model deployment")
    model_path: str = Field(default="")
    deployment_id: Optional[str] = Field(default=None)
    endpoint: Optional[str] = Field(default=None)
    status_info: Dict[str, Any] = Field(default_factory=dict)
    
