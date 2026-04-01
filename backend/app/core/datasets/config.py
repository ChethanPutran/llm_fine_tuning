
from pydantic import BaseModel, Field
from typing import Dict, Any

class DatasetConfig(BaseModel):
    """Dataset configuration model"""
    dataset_type: str = Field(default="csv", description="Type of the dataset (e.g., csv, json, parquet)")
    dataset_task_type: str = Field(default="classification", description="Task type for the dataset (e.g., classification, regression)")
    dataset_path: str = Field(default="", description="Path to the dataset")
    batch_size: int = Field(default=16, ge=1, le=128, description="Batch size for training/evaluation")
    shuffle: bool = Field(default=True, description="Whether to shuffle the dataset")
    num_workers: int = Field(default=4, ge=0, le=16, description="Number of worker threads for data loading")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for dataset loading")
