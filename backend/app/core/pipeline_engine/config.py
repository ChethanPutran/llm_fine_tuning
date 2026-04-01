from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, TYPE_CHECKING

class PipelineConfig(BaseModel):
    """Pipeline execution configuration model"""
    pipeline_json: Dict[str, Any] = Field(default_factory=dict, description="JSON definition of the pipeline to execute")
    user_id: Optional[str] = Field(default=None, description="ID of the user who initiated the pipeline")
    tags: List[str] = Field(default_factory=list, description="List of tags for categorizing the pipeline job")
