from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Enums
class ModelType(str, Enum):
    BERT = "bert"
    BART = "bart"
    GPT = "gpt"
    VIT = "vit"
    VLM = "vlm"

class FinetuningStrategy(str, Enum):
    FULL = "full"
    LORA = "lora"
    ADAPTER = "adapter"
    PREFIX_TUNING = "prefix_tuning"

class TaskType(str, Enum):
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    QA = "qa"
    GENERATION = "generation"

class OptimizationType(str, Enum):
    PRUNING = "pruning"
    DISTILLATION = "distillation"
    QUANTIZATION = "quantization"

class DeploymentTarget(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    EDGE = "edge"

# Request Models
class DataCollectionRequest(BaseModel):
    source: str = Field(..., description="Data source (web, books)")
    topic: str = Field(..., description="Topic to collect")
    limit: int = Field(100, ge=1, le=10000, description="Maximum documents to collect")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")
    
    @validator('source')
    def validate_source(cls, v):
        if v not in ['web', 'books']:
            raise ValueError('Source must be web or books')
        return v

class PreprocessingRequest(BaseModel):
    input_path: str = Field(..., description="Path to input data")
    output_path: Optional[str] = Field(None, description="Path for processed output")
    config: Dict[str, Any] = Field(default_factory=dict, description="Preprocessing configuration")
    deduplicate: bool = Field(True, description="Enable deduplication")
    extract_knowledge: bool = Field(True, description="Extract knowledge entities")

class TokenizationRequest(BaseModel):
    tokenizer_type: str = Field(..., description="Tokenizer type (bpe, wordpiece, sentencepiece)")
    corpus_path: str = Field(..., description="Path to training corpus")
    vocab_size: int = Field(50000, ge=1000, le=200000, description="Vocabulary size")
    output_path: str = Field(..., description="Path to save tokenizer")
    field: Optional[str] = Field('content_clean', description="Field to tokenize (for structured data)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tokenizer configuration")

class TrainingRequest(BaseModel):
    model_type: ModelType = Field(..., description="Type of model to train")
    model_name: str = Field(..., description="Pretrained model name")
    dataset_path: str = Field(..., description="Path to training dataset")
    task: TaskType = Field(TaskType.CLASSIFICATION, description="Task type")
    config: Dict[str, Any] = Field(default_factory=dict, description="Training configuration")

class FinetuningRequest(BaseModel):
    model_type: ModelType = Field(..., description="Type of model to fine-tune")
    model_name: str = Field(..., description="Pretrained model name")
    strategy: FinetuningStrategy = Field(FinetuningStrategy.FULL, description="Fine-tuning strategy")
    task: TaskType = Field(..., description="Task type")
    dataset_path: str = Field(..., description="Path to fine-tuning dataset")
    config: Dict[str, Any] = Field(default_factory=dict, description="Fine-tuning configuration")

class OptimizationRequest(BaseModel):
    model_path: str = Field(..., description="Path to model to optimize")
    optimization_type: OptimizationType = Field(..., description="Optimization type")
    config: Dict[str, Any] = Field(default_factory=dict, description="Optimization configuration")

class DeploymentRequest(BaseModel):
    model_path: str = Field(..., description="Path to model to deploy")
    deployment_target: DeploymentTarget = Field(DeploymentTarget.LOCAL, description="Deployment target")
    serving_framework: str = Field(..., description="Serving framework")
    config: Dict[str, Any] = Field(default_factory=dict, description="Deployment configuration")

# Response Models
class JobResponse(BaseModel):
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    message: Optional[str] = Field(None, description="Status message")

class StatusResponse(BaseModel):
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current status")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class MetricsResponse(BaseModel):
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    perplexity: Optional[float] = None
    train_loss: Optional[float] = None
    eval_loss: Optional[float] = None
    total_parameters: Optional[int] = None
    trainable_parameters: Optional[int] = None
    
class ModelInfo(BaseModel):
    model_type: str
    model_name: str
    parameters: Dict[str, int]
    task: Optional[str] = None
    status: str
    created_at: datetime

class DeploymentInfo(BaseModel):
    deployment_id: str
    endpoint: str
    framework: str
    status: str
    model_path: str
    config: Dict[str, Any]
    created_at: datetime