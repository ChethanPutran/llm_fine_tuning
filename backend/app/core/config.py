from pydantic_settings import BaseSettings
from typing import List
from enum import Enum
import os
from pathlib import Path


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LLM Fine-tuning Platform"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here-change-this-in-production"


    # Pipeline and Execution
    PIPELINE_WORKERS: int = 4
    PIPELINE_QUEUE_MAX_SIZE: int = 100
    PIPELINE_EXECUTION_TIMEOUT: int = 3600  # seconds
    
    # Database
    DATABASE_URL: str = "sqlite:///./llm_platform.db"
    
    # Redis for caching and task queues
    REDIS_URL: str = "redis://localhost:6379"
    
    # Spark
    SPARK_MASTER: str = "local[*]"
    SPARK_APP_NAME: str = "LLMDataProcessor"
    
    # Model Storage
    MODEL_STORAGE_PATH: str = "./models"
    DATA_STORAGE_PATH: str = "./data"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # MLflow
    MLFLOW_TRACKING_URI: str = "./mlruns"
    
    # Model Settings (added these fields)
    DEFAULT_MODEL: str = "bert-base-uncased"
    DEFAULT_BATCH_SIZE: int = 16
    DEFAULT_LEARNING_RATE: float = 2e-5
    DEFAULT_EPOCHS: int = 3
    
    # Deployment Settings (added these fields)
    DEPLOYMENT_PORT: int = 8080
    DEPLOYMENT_WORKERS: int = 4
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # This will ignore extra fields instead of raising errors
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            """Parse environment variables, especially for List types"""
            if field_name == "CORS_ORIGINS":
                import json
                return json.loads(raw_val)
            return raw_val

# Create settings instance
settings = Settings()

# Ensure required directories exist
def ensure_directories():
    """Create required directories if they don't exist"""
    directories = [
        settings.MODEL_STORAGE_PATH,
        settings.DATA_STORAGE_PATH,
        os.path.join(settings.DATA_STORAGE_PATH, "raw"),
        os.path.join(settings.DATA_STORAGE_PATH, "processed"),
        os.path.join(settings.DATA_STORAGE_PATH, "uploads"),
        os.path.join(settings.MODEL_STORAGE_PATH, "cache"),
        "logs",
        "mlruns"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Call directory creation
ensure_directories()

# Print configuration on startup (for debugging)
if settings.DEBUG:
    print(f"✓ Configuration loaded successfully")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug mode: {settings.DEBUG}")
    print(f"  Database: {settings.DATABASE_URL}")
    print(f"  Model storage: {settings.MODEL_STORAGE_PATH}")