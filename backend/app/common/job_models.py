# app/common/job_models.py

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from .enums import NodeType, JobType, JobStatus, JobPriority
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
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"retries": 3, "delay_seconds": 5})

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

    def mark_removed(self):
        """Mark job as removed"""
        self.status = JobStatus.REMOVED
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
   
PRIORITY_MAP = {
               JobType.DATA_COLLECTION: JobPriority.CRITICAL,
                JobType.DATA_PROCESSING: JobPriority.HIGH,
                JobType.TRAINING: JobPriority.HIGH,
                JobType.FINETUNING: JobPriority.NORMAL,
                JobType.OPTIMIZATION: JobPriority.NORMAL,
                JobType.DEPLOYMENT: JobPriority.LOW,
                JobType.EVALUATION: JobPriority.NORMAL,
                JobType.TOKENIZATION: JobPriority.LOW,
                JobType.INFERENCE: JobPriority.BACKGROUND
            }
            
# Factory function to create jobs
class JobFactory:
    """Factory for creating different types of jobs"""
    @staticmethod
    def create_job_metadata(name: str, node_type: NodeType, job: BaseJob, description: Optional[str] = None,config: Dict[str, Any] = {}, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate job metadata"""
        return {
            "name": name,
            "node_type": node_type,
            "retry_policy": config.get("retry_policy", {"retries": 3, "delay_seconds": 5}),
            "position": config.get("position", (0, 0)),
            "description": description or "",
            "tags": tags or [],
            "resources": JobFactory.get_required_job_resource(JobType.DATA_PROCESSING),
            "metadata": config.get("metadata", {})
        }
    @staticmethod
    def get_required_job_resource(job_type: JobType) -> Dict[str, Any]:
        """Get required resources for a given job type"""
        resource_mapping = {
            JobType.DATA_COLLECTION: {"cpu": 2, "memory": "4GB"},
            JobType.DATA_PROCESSING: {"cpu": 4, "memory": "8GB"},
            JobType.TRAINING: {"gpu": 1, "cpu": 8, "memory": "32GB"},
            JobType.FINETUNING: {"gpu": 1, "cpu": 4, "memory": "16GB"},
            JobType.OPTIMIZATION: {"gpu": 1, "cpu": 4, "memory": "16GB"},
            JobType.DEPLOYMENT: {"cpu": 2, "memory": "4GB"},
            JobType.EVALUATION: {"gpu": 1, "cpu": 4, "memory": "16GB"},
            JobType.TOKENIZATION: {"cpu": 4, "memory": "8GB"},
            JobType.INFERENCE: {"gpu": 1, "cpu": 4, "memory": "16GB"}
        }
        return resource_mapping.get(job_type, {"cpu": 2, "memory": "4GB"})

    @staticmethod
    def create_data_collection_job(
        data_collection_config: DataCollectionConfig,
        **kwargs
    ) -> DataCollectionJob:
        """Create a data collection job"""
        return DataCollectionJob(
            config=data_collection_config,
            priority=PRIORITY_MAP.get(JobType.DATA_COLLECTION, JobPriority.NORMAL),
            **kwargs
        )
    
    @staticmethod
    def create_preprocessing_job(
        preprocessing_config: PreprocessingConfig = Field(default_factory=PreprocessingConfig),
        **kwargs
    ) -> PreprocessingJob:
        """Create a preprocessing job"""
        return PreprocessingJob(
            config=preprocessing_config,
            priority=PRIORITY_MAP.get(JobType.DATA_PROCESSING, JobPriority.NORMAL),
            **kwargs
        )
    
    @staticmethod
    def create_training_job(
        training_config: TrainingConfig,
        model_config: ModelConfig,
        dataset_config: DatasetConfig,
        **kwargs
    ) -> TrainingJob:
        """Create a training job"""
        return TrainingJob(
            train_model_config=model_config,
            dataset_config=dataset_config,
            config=training_config,
            priority=PRIORITY_MAP.get(JobType.TRAINING, JobPriority.NORMAL),
            **kwargs
        )
    
    @staticmethod
    def create_finetuning_job(
        finetune_config: FinetuningConfig,
        base_model_config: ModelConfig,
        dataset_config: DatasetConfig,
        **kwargs
    ) -> FinetuningJob:
        """Create a fine-tuning job"""
        return FinetuningJob(
            config=finetune_config,
            base_model_config=base_model_config,
            priority=PRIORITY_MAP.get(JobType.FINETUNING, JobPriority.NORMAL),
            dataset_config=dataset_config,
            **kwargs
        )

    @staticmethod
    def create_optimization_job(
        optimization_config: OptimizationConfig,
        **kwargs
    ) -> OptimizationJob:
        """Create an optimization job"""
        return OptimizationJob(
            config=optimization_config,
            priority=PRIORITY_MAP.get(JobType.OPTIMIZATION, JobPriority.NORMAL),
            **kwargs
        )
    
    @staticmethod
    def create_deployment_job(
        deployment_config: DeploymentConfig,
        **kwargs
    ) -> DeploymentJob:
        """Create a deployment job"""
        return DeploymentJob(
            config=deployment_config,
            priority=PRIORITY_MAP.get(JobType.DEPLOYMENT, JobPriority.NORMAL),
            **kwargs
        )
    
    @staticmethod
    def create_tokenization_job(
        tokenization_config: TokenizationConfig,
        **kwargs
    ) -> TokenizationJob:
        """Create a tokenization job"""
        return TokenizationJob(
            config=tokenization_config,
            priority=PRIORITY_MAP.get(JobType.TOKENIZATION, JobPriority.NORMAL),
            **kwargs
        )
    
    @staticmethod
    def create_evaluation_job(
        evaluation_config: EvaluationConfig,
        **kwargs
    ) -> EvaluationJob:
        """Create an evaluation job"""
        return EvaluationJob(
            config=evaluation_config,
            priority=PRIORITY_MAP.get(JobType.EVALUATION, JobPriority.NORMAL),
            **kwargs
        )
    
    @staticmethod
    def create_pipeline_job(
        pipeline_config: PipelineConfig,
        **kwargs
    ) -> PipelineJob:
        """Create a pipeline execution job"""
        return PipelineJob(
            config=pipeline_config,
            priority=PRIORITY_MAP.get(JobType.INFERENCE, JobPriority.BACKGROUND),
            **kwargs
        )