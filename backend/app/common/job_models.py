# app/common/job_models.py

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_validator
from ..config.config_provider import (
    PipelineConfig,
    DataCollectionConfig,
    PreprocessingConfig,
    TokenizationConfig, 
    TrainingConfig,
    FinetuningConfig,
    OptimizationConfig,
    DeploymentConfig,
    EvaluationConfig,
    ModelConfig,
    DatasetConfig
)

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



class BaseJob(BaseModel):
    """Base job class with common functionality"""
    
    job_id: UUID = Field(default_factory=uuid4)
    job_type: JobType = Field(JobType.DATA_PROCESSING)
    status: JobStatus = Field(JobStatus.PENDING)
    priority: JobPriority = Field(JobPriority.NORMAL)
    progress: float = Field(0.0)
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    updated_at: datetime = Field(default_factory=datetime.now)
    execution_id: Optional[UUID] = Field(None)
    pipeline_id: Optional[UUID] = Field(None)
    node_id: Optional[str] = Field(None)
    user_id: Optional[str] = Field(None)
    result: Optional[Dict[str, Any]] = Field(None)
    error: Optional[str] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = Field(0)
    max_retries: int = Field(3)
    tags: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    def update_progress(self, progress: float):
        """Update job progress (0.0 to 100.0)"""
        self.progress = max(0.0, min(100.0, progress))
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_started(self):
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_completed(self, result: Dict[str, Any]):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.result = result
        self.progress = 100.0
    
    def mark_failed(self, error: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_cancelled(self):
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.status = JobStatus.FAILED
        else:
            self.status = JobStatus.RETRYING
        self.updated_at = datetime.now(timezone.utc)


class PipelineJob(BaseJob):
    """Pipeline job that can contain multiple sub-jobs"""
    job_type: JobType = JobType.INFERENCE
    config: PipelineConfig = Field(default=PipelineConfig())
    
    
class DataCollectionJob(BaseJob):
    """Data collection job"""
    job_type: JobType = JobType.DATA_COLLECTION
    config: DataCollectionConfig = Field(default=DataCollectionConfig())
    
class PreprocessingJob(BaseJob):
    """Preprocessing job"""
    job_type: JobType = JobType.DATA_PROCESSING
    config: PreprocessingConfig = Field(default=PreprocessingConfig())

class TokenizationJob(BaseJob):
    """Tokenizer training job"""
    job_type: JobType = JobType.TOKENIZATION
    config: TokenizationConfig = Field(default=TokenizationConfig())

class TrainingJob(BaseJob):
    """Model training job"""
    job_type: JobType = JobType.TRAINING
    train_model_config: ModelConfig = Field(default=ModelConfig(model_name="", tokenizer=""))
    dataset_config: DatasetConfig = Field(default=DatasetConfig())
    config: TrainingConfig = Field(default=TrainingConfig())

class FinetuningJob(BaseJob):
    """Model fine-tuning job"""
    job_type: JobType = JobType.FINETUNING
    config: FinetuningConfig = Field(default=FinetuningConfig())
    base_model_config: ModelConfig = Field(default=ModelConfig(model_name="", tokenizer=""))
    dataset_config: DatasetConfig = Field(default=DatasetConfig())
    
class OptimizationJob(BaseJob):
    """Model optimization job"""
    job_type: JobType = JobType.OPTIMIZATION
    config: OptimizationConfig = Field(default=OptimizationConfig())
    
class DeploymentJob(BaseJob):
    """Model deployment job"""
    job_type: JobType = JobType.DEPLOYMENT
    config: DeploymentConfig = Field(default=DeploymentConfig())

class EvaluationJob(BaseJob):
    """Model evaluation job"""
    job_type: JobType = JobType.EVALUATION
    config: EvaluationConfig = Field(default=EvaluationConfig())
   

# Factory function to create jobs
class JobFactory:
    """Factory for creating different types of jobs"""
    
    @staticmethod
    def create_data_collection_job(
        source: str,
        topic: str,
        limit: int = 100,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> DataCollectionJob:
        """Create a data collection job"""
        job_config = DataCollectionConfig(
            source=source,
            topic=topic,
            limit=limit,
            additional_params=config or {}
        )
        return DataCollectionJob(
            config=job_config,
            **kwargs
        )
    
    @staticmethod
    def create_preprocessing_job(
        input_path: str,
        output_path: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> PreprocessingJob:
        """Create a preprocessing job"""
        job_config = PreprocessingConfig(
            input_path=input_path,
            output_path=output_path,
            additional_params=config or {}
        )
        return PreprocessingJob(
            config=job_config,
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
        training_config = TrainingConfig(
            additional_params=config or {}
        )
        model_config = ModelConfig(
            model_type=model_type,
            model_name=model_name,
            additional_params=config or {},
            tokenizer=model_name  # Assuming tokenizer name is same as model name, can be customized
        )
        dataset_config = DatasetConfig(
            dataset_path=dataset_path,
            additional_params=config or {}
        )
        return TrainingJob(
            train_model_config=model_config,
            dataset_config=dataset_config,
            config=training_config,
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
        finetune_config = FinetuningConfig(
            strategy_type=strategy_type,
            task_type=task_type,
            additional_params=config or {}
        )
        base_model_config = ModelConfig(
            model_type=base_model_type,
            model_name=base_model_name,
            additional_params=config or {},
            tokenizer=base_model_name  # Assuming tokenizer name is same as model name, can be customized
        )   
        dataset_config = DatasetConfig(
            dataset_path=dataset_path,
            additional_params=config or {}
        )
        return FinetuningJob(
            config=finetune_config,
            base_model_config=base_model_config,
            dataset_config=dataset_config,
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
        optimization_config = OptimizationConfig(
            optimization_type=optimization_type,
            input_model_path=input_model_path,
            additional_params=config or {}
        )
        return OptimizationJob(
            config=optimization_config,
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
        deployment_config = DeploymentConfig(
            model_path=model_path,
            serving_framework=serving_framework,
            deployment_target=deployment_target,
            additional_params=config or {}
        )
        return DeploymentJob(
            config=deployment_config,
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
        tokenization_config = TokenizationConfig(
            tokenizer_type=tokenizer_type,
            dataset_path=dataset_path,
            vocab_size=vocab_size,
            additional_params=config or {}
        )
        return TokenizationJob(
            config=tokenization_config,
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
        evaluation_config = EvaluationConfig(
            model_path=model_path,
            dataset_path=dataset_path,
            additional_params=config or {}
        )
        return EvaluationJob(
            config=evaluation_config,
            **kwargs
        )
    
    @staticmethod
    def create_pipeline_job(
        pipeline_json: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> PipelineJob:
        """Create a pipeline execution job"""
        pipeline_config = PipelineConfig(
            pipeline_json=pipeline_json,
            priority=priority,
            user_id=user_id,
            tags=tags or ["pipeline"]
        )
        job = PipelineJob(
            config=pipeline_config,
            **kwargs
        )
        return job