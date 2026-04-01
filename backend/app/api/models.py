from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.common.job_models import JobPriority
from app.common.job_models import JobPriority
from app.core.data_collection.config import DataCollectionConfig
from app.core.datasets.config import DatasetConfig
from app.core.deployment.config import DeploymentConfig
from app.core.finetuning.config import FinetuningConfig
from app.core.models.config import ModelConfig
from app.core.optimization.config import OptimizationConfig
from app.core.pipeline_engine.config import PipelineConfig
from app.core.pipeline_engine.config import PipelineConfig
from app.core.preprocessing.config import PreprocessingConfig
from app.core.training.config import TrainingConfig
from app.core.tokenization.config import TokenizationConfig

class RequestBase(BaseModel):
    """Base request model with common fields"""
    auto_execute: bool = Field(True, description="Automatically execute the job after creation")
    tags: Optional[List[str]] = Field(None, description="Optional tags for categorization")
    user_id: str = Field(..., description="User ID who triggered the request")

class StartCollectionRequest(RequestBase):
    """Request model for starting data collection"""
    config: DataCollectionConfig = Field(default_factory=DataCollectionConfig, description="Configuration for data collection")

class StartDeploymentRequest(RequestBase):
    """Request model for starting deployment"""
    config: DeploymentConfig = Field(default_factory=DeploymentConfig, description="Configuration for deployment")

class StartTrainingRequest(RequestBase):
    """Request model for starting training"""
    dataset_config: DatasetConfig = Field(default_factory=DatasetConfig, description="Dataset configuration")
    train_model_config: ModelConfig = Field(default_factory=ModelConfig, description="Model configuration")
    config: TrainingConfig = Field(default_factory=TrainingConfig, description="Training configuration")

class StartFinetuningRequest(RequestBase):
    """Request model for starting fine-tuning"""
    
    base_model_config: ModelConfig = Field(default_factory=ModelConfig, description="Base model configuration")
    dataset_config: DatasetConfig = Field(default_factory=DatasetConfig, description="Dataset configuration")
    config: FinetuningConfig = Field(default_factory=FinetuningConfig, description="Fine-tuning configuration")

class StartOptimizationRequest(RequestBase):
    """Request model for starting optimization"""
    config: OptimizationConfig = Field(default_factory=OptimizationConfig, description="Optimization configuration")

class StartPreprocessingRequest(RequestBase):
    """Request model for starting preprocessing"""
    config: PreprocessingConfig = Field(..., description="Preprocessing configuration")

class TrainTokenizerRequest(RequestBase):
    """Request model for training tokenizer"""
    config: TokenizationConfig = Field(default_factory=TokenizationConfig, description="Additional configuration")

class EncodeRequest(RequestBase):
    """Request model for encoding text"""
    tokenizer_path: str = Field(..., description="Path to tokenizer")
    text: str = Field(..., description="Text to encode")
    max_length: Optional[int] = Field(None, description="Maximum sequence length")

class DecodeRequest(RequestBase):
    """Request model for decoding tokens"""
    tokenizer_path: str = Field(..., description="Path to tokenizer")
    token_ids: List[int] = Field(..., description="Token IDs to decode")

class ExecutePipelineRequest(RequestBase):
    """Request model for executing a pipeline"""
    config: PipelineConfig = Field(..., description="Pipeline execution configuration")
    priority: JobPriority = Field(JobPriority.NORMAL, description="Execution priority")

class CreatePipelineJobRequest(RequestBase):
    """Request model for creating a pipeline job"""
    config: PipelineConfig = Field(..., description="Pipeline configuration for job creation")



# Response Models

class ResponseBase(BaseModel):
    """Base request model with common fields"""
    tags: Optional[List[str]] = Field(None, description="Optional tags for categorization")
    user_id: Optional[str] = Field(None, description="User ID who triggered the request")
    status: str = Field(..., description="Current status of the fine-tuning job")
    message: Optional[str] = Field(default=None, description="Additional information about the job status")
    error: Optional[str] = Field(default=None, description="Error message if the job failed")

class JobCreationResponse(ResponseBase):
    """Response model for job creation"""
    job_id: str = Field(..., description="Job identifier")

class JobStatusResponse(ResponseBase):
    """Response model for job status"""
    job_id: str = Field(..., description="Job identifier")
    job_type: str = Field(..., description="Type of the job (e.g., training, fine-tuning, data collection)")
    progress: Optional[float] = Field(None, description="Progress percentage of the job")

class ExecutionStatusResponse(ResponseBase):
    """Response model for execution status"""
    execution_id: str = Field(..., description="Execution identifier")
    job_id: str = Field(..., description="Associated job identifier")
    progress: Optional[float] = Field(None, description="Progress percentage of the execution")

class ListJobsResponse(ResponseBase):
    """Response model for listing jobs"""
    jobs: List[JobStatusResponse] = Field(..., description="List of jobs matching the criteria")

class StaticResourceResponse(ResponseBase):
    """Response model for static resource requests"""
    resource_id: str = Field(..., description="Identifier for the requested resource")
    url: str = Field(..., description="URL to access the resource")
    
class StatisticsResponse(ResponseBase):
    """Response model for statistics requests"""
    total_jobs: int = Field(..., description="Total number of jobs")
    completed_jobs: int = Field(..., description="Number of completed jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    in_progress_jobs: int = Field(..., description="Number of jobs in progress")

class MetricResponse(ResponseBase):
    """Response model for metric retrieval"""
    metric_name: str = Field(..., description="Name of the metric")
    value: Any = Field(..., description="Value of the metric")

class LogsResponse(ResponseBase):
    """Response model for logs retrieval"""
    logs: List[str] = Field(..., description="List of log entries")
    tail: int = Field(..., description="Number of log lines returned from the end")

class ListResourcesResponse(ResponseBase):
    """Response model for listing resources"""
    items: List[Dict[str, Any]] = Field(..., description="List of resources")

class PipelineExecutionResponse(ExecutionStatusResponse):
    """Response model for pipeline execution"""
    pass

class Template:
    """Response model for template retrieval"""
    template_id: str = Field(..., description="Identifier for the retrieved template")
    content: Dict[str, Any] = Field(..., description="Content of the template")
    name: Optional[str] = Field(None, description="Name of the template")
    description: Optional[str] = Field(None, description="Description of the template")
    description: Optional[str] = Field(None, description="Description of the template")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the template")
    nodes: Optional[int] = Field(None, description="Number of nodes in the pipeline template")
    
class TemplateListResponse(ResponseBase):
    """Response model for listing pipeline templates"""
    templates: Dict[str,Template] = Field(..., description="List of available pipeline templates")

class FinetuningStatusResponse(ResponseBase):
    """Response model for fine-tuning job status"""
    pass

class FinetuningResponse(ResponseBase):
    """Response model for fine-tuning job status"""
    pass

class ValidationResponse(ResponseBase):
    """Response model for pipeline validation"""
    valid: bool = Field(..., description="Indicates if the pipeline configuration is valid")
    errors: Optional[List[str]] = Field(None, description="List of validation errors if the configuration is invalid")
    nodes: Optional[int] = Field(None, description="Number of nodes in the pipeline configuration")
    edges: Optional[int] = Field(None, description="Number of edges in the pipeline configuration")
    