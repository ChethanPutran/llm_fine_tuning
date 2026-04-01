
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class RAGConfig(BaseModel):
    """RAG configuration model"""
    retriever_type: str = Field(default="dense", description="Type of retriever to use (e.g., dense, sparse)")
    retriever_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the retriever")
    generator_type: str = Field(default="seq2seq", description="Type of generator to use (e.g., seq2seq, autoregressive)")
    generator_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the generator")
    max_retrieved_docs: int = Field(default=5, ge=1, le=20, description="Maximum number of documents to retrieve")
    retrieval_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Optional threshold for retrieval relevance")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for RAG configuration")