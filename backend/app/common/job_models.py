# app/common/job_models.py

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class JobPriority(Enum):
    """Job priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class JobStatus(Enum):
    """Job status states"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(Enum):
    """Types of jobs"""
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    TRAINING = "training"
    FINETUNING = "finetuning"
    OPTIMIZATION = "optimization"
    EVALUATION = "evaluation"
    DEPLOYMENT = "deployment"
    TOKENIZATION = "tokenization"
    INFERENCE = "inference"


@dataclass
class BaseJob:
    """Base job class with common functionality"""
    
    job_id: UUID = field(default_factory=uuid4)
    job_type: JobType = JobType.DATA_PROCESSING
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    execution_id: Optional[UUID] = None
    pipeline_id: Optional[UUID] = None
    node_id: Optional[str] = None
    user_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    tags: List[str] = field(default_factory=list)
    
    def update_progress(self, progress: float):
        """Update job progress (0.0 to 100.0)"""
        self.progress = max(0.0, min(100.0, progress))
        self.updated_at = datetime.utcnow()
    
    def mark_started(self):
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, result: Dict[str, Any]):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.result = result
        self.progress = 100.0
    
    def mark_failed(self, error: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self):
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.status = JobStatus.FAILED
        else:
            self.status = JobStatus.RETRYING
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "job_id": str(self.job_id),
            "job_type": self.job_type.value,
            "status": self.status.value,
            "priority": self.priority.name,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat(),
            "execution_id": str(self.execution_id) if self.execution_id else None,
            "pipeline_id": str(self.pipeline_id) if self.pipeline_id else None,
            "node_id": self.node_id,
            "user_id": self.user_id,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "tags": self.tags
        }


@dataclass
class DataCollectionJob(BaseJob):
    """Data collection job"""
    job_type: JobType = JobType.DATA_COLLECTION
    source: str = ""
    topic: str = ""
    search_engine: str = "google"
    limit: int = 100
    documents: List[Dict[str, Any]] = field(default_factory=list)
    output_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with data collection specific fields"""
        base_dict = super().to_dict()
        base_dict.update({
            "source": self.source,
            "topic": self.topic,
            "search_engine": self.search_engine,
            "limit": self.limit,
            "documents_count": len(self.documents),
            "output_path": self.output_path
        })
        return base_dict


@dataclass
class PreprocessingJob(BaseJob):
    """Preprocessing job"""
    job_type: JobType = JobType.DATA_PROCESSING
    input_path: str = ""
    output_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with preprocessing specific fields"""
        base_dict = super().to_dict()
        base_dict.update({
            "input_path": self.input_path,
            "output_path": self.output_path,
            "config": self.config,
            "metrics": self.metrics
        })
        return base_dict


@dataclass
class TokenizationJob(BaseJob):
    """Tokenizer training job"""
    job_type: JobType = JobType.TOKENIZATION
    tokenizer_type: str = "bpe"
    dataset_path: str = ""
    vocab_size: int = 32000
    tokenizer_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with tokenization specific fields"""
        base_dict = super().to_dict()
        base_dict.update({
            "tokenizer_type": self.tokenizer_type,
            "dataset_path": self.dataset_path,
            "vocab_size": self.vocab_size,
            "tokenizer_path": self.tokenizer_path,
            "config": self.config
        })
        return base_dict


@dataclass
class TrainingJob(BaseJob):
    """Model training job"""
    job_type: JobType = JobType.TRAINING
    model_type: str = ""
    model_name: str = ""
    dataset_path: str = ""
    model_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with training specific fields"""
        base_dict = super().to_dict()
        base_dict.update({
            "model_type": self.model_type,
            "model_name": self.model_name,
            "dataset_path": self.dataset_path,
            "model_path": self.model_path,
            "config": self.config,
            "metrics": self.metrics
        })
        return base_dict


@dataclass
class FinetuningJob(BaseJob):
    """Model fine-tuning job"""
    job_type: JobType = JobType.FINETUNING
    base_model_type: str = ""
    base_model_name: str = ""
    strategy_type: str = "lora"
    task_type: str = "classification"
    dataset_path: str = ""
    output_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    trainable_params: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with fine-tuning specific fields"""
        base_dict = super().to_dict()
        base_dict.update({
            "base_model_type": self.base_model_type,
            "base_model_name": self.base_model_name,
            "strategy_type": self.strategy_type,
            "task_type": self.task_type,
            "dataset_path": self.dataset_path,
            "output_path": self.output_path,
            "config": self.config,
            "metrics": self.metrics,
            "trainable_params": self.trainable_params
        })
        return base_dict


@dataclass
class OptimizationJob(BaseJob):
    """Model optimization job"""
    job_type: JobType = JobType.OPTIMIZATION
    optimization_type: str = "quantization"
    input_model_path: str = ""
    output_model_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    original_size: Optional[int] = None
    optimized_size: Optional[int] = None
    compression_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with optimization specific fields"""
        base_dict = super().to_dict()
        base_dict.update({
            "optimization_type": self.optimization_type,
            "input_model_path": self.input_model_path,
            "output_model_path": self.output_model_path,
            "config": self.config,
            "metrics": self.metrics,
            "original_size": self.original_size,
            "optimized_size": self.optimized_size,
            "compression_ratio": self.compression_ratio
        })
        return base_dict


@dataclass
class DeploymentJob(BaseJob):
    """Model deployment job"""
    job_type: JobType = JobType.DEPLOYMENT
    model_path: str = ""
    serving_framework: str = "torchserve"
    deployment_target: str = "local"
    deployment_id: Optional[str] = None
    endpoint: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    status_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with deployment specific fields"""
        base_dict = super().to_dict()
        base_dict.update({
            "model_path": self.model_path,
            "serving_framework": self.serving_framework,
            "deployment_target": self.deployment_target,
            "deployment_id": self.deployment_id,
            "endpoint": self.endpoint,
            "config": self.config,
            "status_info": self.status_info
        })
        return base_dict


@dataclass
class EvaluationJob(BaseJob):
    """Model evaluation job"""
    job_type: JobType = JobType.EVALUATION
    model_path: str = ""
    dataset_path: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    predictions: Optional[List[Dict[str, Any]]] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with evaluation specific fields"""
        base_dict = super().to_dict()
        base_dict.update({
            "model_path": self.model_path,
            "dataset_path": self.dataset_path,
            "metrics": self.metrics,
            "predictions_count": len(self.predictions) if self.predictions else 0,
            "config": self.config
        })
        return base_dict


# Pydantic models for request/response validation
class PreprocessingConfig(BaseModel):
    """Preprocessing configuration model"""
    clean_method: str = Field("standard", description="Cleaning method (standard/advanced)")
    dedup_threshold: float = Field(0.9, ge=0, le=1, description="Deduplication threshold")
    extract_entities: bool = Field(True, description="Extract named entities")
    extract_keywords: bool = Field(True, description="Extract keywords")
    normalize_text: bool = Field(True, description="Normalize text")
    remove_stopwords: bool = Field(True, description="Remove stopwords")
    min_doc_length: int = Field(50, ge=10, description="Minimum document length")
    max_doc_length: int = Field(10000, le=100000, description="Maximum document length")
    language: str = Field("en", description="Document language")
    output_format: str = Field("parquet", description="Output format (parquet/csv/json)")




# Factory function to create jobs
class JobFactory:
    """Factory for creating different types of jobs"""
    
    @staticmethod
    def create_data_collection_job(
        source: str,
        topic: str,
        search_engine: str = "google",
        limit: int = 100,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> DataCollectionJob:
        """Create a data collection job"""
        return DataCollectionJob(
            source=source,
            topic=topic,
            search_engine=search_engine,
            limit=limit,
            metadata=config or {},
            **kwargs
        )
    
    @staticmethod
    def create_preprocessing_job(
        input_path: str,
        config: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> PreprocessingJob:
        """Create a preprocessing job"""
        return PreprocessingJob(
            input_path=input_path,
            output_path=output_path,
            config=config or {},
            **kwargs
        )
    
    @staticmethod
    def create_training_job(
        model_type: str,
        model_name: str,
        dataset_path: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> TrainingJob:
        """Create a training job"""
        return TrainingJob(
            model_type=model_type,
            model_name=model_name,
            dataset_path=dataset_path,
            config=config or {},
            **kwargs
        )
    
    @staticmethod
    def create_finetuning_job(
        base_model_type: str,
        base_model_name: str,
        strategy_type: str,
        task_type: str,
        dataset_path: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> FinetuningJob:
        """Create a fine-tuning job"""
        return FinetuningJob(
            base_model_type=base_model_type,
            base_model_name=base_model_name,
            strategy_type=strategy_type,
            task_type=task_type,
            dataset_path=dataset_path,
            config=config or {},
            **kwargs
        )
    
    @staticmethod
    def create_optimization_job(
        optimization_type: str,
        input_model_path: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> OptimizationJob:
        """Create an optimization job"""
        return OptimizationJob(
            optimization_type=optimization_type,
            input_model_path=input_model_path,
            config=config or {},
            **kwargs
        )
    
    @staticmethod
    def create_deployment_job(
        model_path: str,
        serving_framework: str,
        deployment_target: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> DeploymentJob:
        """Create a deployment job"""
        return DeploymentJob(
            model_path=model_path,
            serving_framework=serving_framework,
            deployment_target=deployment_target,
            config=config or {},
            **kwargs
        )
    
    @staticmethod
    def create_tokenization_job(
        tokenizer_type: str,
        dataset_path: str,
        vocab_size: int,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> TokenizationJob:
        """Create a tokenization job"""
        return TokenizationJob(
            tokenizer_type=tokenizer_type,
            dataset_path=dataset_path,
            vocab_size=vocab_size,
            config=config or {},
            **kwargs
        )
    
    @staticmethod
    def create_evaluation_job(
        model_path: str,
        dataset_path: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> EvaluationJob:
        """Create an evaluation job"""
        return EvaluationJob(
            model_path=model_path,
            dataset_path=dataset_path,
            config=config or {},
            **kwargs
        )

   