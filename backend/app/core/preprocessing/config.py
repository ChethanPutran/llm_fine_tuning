from pydantic import BaseModel, Field
from typing import Dict, Any

class PreprocessingConfig(BaseModel):
    """Preprocessing configuration model"""
    clean_method: str = Field(default="standard", description="Cleaning method (standard/advanced)")
    dedup_threshold: float = Field(default=0.9, ge=0, le=1, description="Deduplication threshold")
    extract_entities: bool = Field(default=True, description="Extract named entities")
    extract_keywords: bool = Field(default=True, description="Extract keywords")
    normalize_text: bool = Field(default=True, description="Normalize text")
    remove_stopwords: bool = Field(default=True, description="Remove stopwords")
    min_doc_length: int = Field(default=50, ge=10, description="Minimum document length")
    max_doc_length: int = Field(default=10000, le=100000, description="Maximum document length")
    language: str = Field(default="en", description="Document language")
    output_format: str = Field(default="parquet", description="Output format (parquet/csv/json)")
    input_path: str = Field(default="", description="Path to input data")
    output_path: str = Field(default="/data/processed", description="Path to save processed data")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for preprocessing")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Metrics collected during preprocessing")
