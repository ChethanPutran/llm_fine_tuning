
from enum import Enum

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
    REMOVED = "removed"



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


class NodeType(Enum):
    DATA_INGESTION = "data_ingestion"
    DATA_PROCESSING = "data_processing"
    MODEL_TRAINING = "model_training"
    MODEL_FINETUNING = "model_finetuning"
    TOKENIZATION = "tokenization"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_DEPLOYMENT = "model_deployment"
    OPTIMIZATION = "optimization"
    CUSTOM = "custom"
    PIPELINE_EXE = "pipeline_execution"

class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

class ExecutionStatus(Enum):
    CREATED = "created"
    VALIDATING = "validating"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExecutionEvent(Enum):
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_RETRYING = "node_retrying"
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DATA_INGESTION_COMPLETED = "data_ingestion_completed"
    DATA_INGESTION_FAILED = "data_ingestion_failed"
    DATA_PROCESSING_COMPLETED = "data_processing_completed"
    DATA_PROCESSING_FAILED = "data_processing_failed"
    MODEL_TRAINING_COMPLETED = "model_training_completed"
    MODEL_TRAINING_FAILED = "model_training_failed"
    MODEL_EVALUATION_COMPLETED = "model_evaluation_completed"
    MODEL_EVALUATION_FAILED = "model_evaluation_failed"
    MODEL_DEPLOYMENT_COMPLETED = "model_deployment_completed"
    MODEL_DEPLOYMENT_FAILED = "model_deployment_failed"