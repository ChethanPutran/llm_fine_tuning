# app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime
import os

from app.core.config import settings
from app.core.exceptions import PlatformException
from app.core.logging_config import setup_logging
from app.api.routes import (
    data_collection,
    preprocessing,
    tokenization,
    training,
    finetuning,
    optimization,
    deployment,
    pipeline  # Add pipeline routes
)
from app.api.websocket import manager as websocket_manager
from app.core.pipeline_engine.orchestrator import PipelineOrchestrator
from app.dependencies.controller import get_orchestrator

# Setup logging
logger = setup_logging()

# WebSocket connection manager
manager = websocket_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting LLM Fine-tuning Platform...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: v1")
    
    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(num_workers=settings.PIPELINE_WORKERS)
    await orchestrator.start()
    app.state.orchestrator = orchestrator
    logger.info("Pipeline orchestrator initialized and started")
    
    # Initialize database connections
    await initialize_database(app)
    
    # Initialize Spark session
    # await initialize_spark(app)
    
    # Load configurations
    await load_configurations(app)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down LLM Fine-tuning Platform...")
    
    # Stop orchestrator
    if hasattr(app.state, 'orchestrator'):
        await app.state.orchestrator.stop()
        logger.info("Pipeline orchestrator stopped")
    
    # Cleanup resources
    await cleanup_resources(app)
    logger.info("Application shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A comprehensive platform for fine-tuning Large Language Models",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_collection.router, prefix=settings.API_V1_PREFIX)
app.include_router(preprocessing.router, prefix=settings.API_V1_PREFIX)
app.include_router(tokenization.router, prefix=settings.API_V1_PREFIX)
app.include_router(training.router, prefix=settings.API_V1_PREFIX)
app.include_router(finetuning.router, prefix=settings.API_V1_PREFIX)
app.include_router(optimization.router, prefix=settings.API_V1_PREFIX)
app.include_router(deployment.router, prefix=settings.API_V1_PREFIX)
app.include_router(pipeline.router, prefix=settings.API_V1_PREFIX)

# Global exception handlers


@app.exception_handler(PlatformException)
async def platform_exception_handler(request, exc: PlatformException):
    """Handle platform-specific exceptions"""
    logger.error(f"Platform exception: {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.code,
        content={
            "error": exc.message,
            "code": exc.code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time job status updates
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process message based on type
            if data.startswith("subscribe:"):
                job_id = data.split(":")[1]
                await manager.subscribe_to_job(websocket, job_id)
                await manager.send_personal_message(
                    f"Subscribed to job {job_id}", 
                    websocket
                )
            
            elif data.startswith("subscribe-execution:"):
                execution_id = data.split(":")[1]
                await manager.subscribe_to_execution(websocket, execution_id)
                await manager.send_personal_message(
                    f"Subscribed to execution {execution_id}", 
                    websocket
                )
            
            elif data.startswith("unsubscribe:"):
                job_id = data.split(":")[1]
                await manager.unsubscribe_from_job(websocket, job_id)
                await manager.send_personal_message(
                    f"Unsubscribed from job {job_id}", 
                    websocket
                )
            
            elif data == "status":
                # Send current status of all jobs
                status = await get_system_status(app)
                await manager.send_personal_message(
                    str(status), 
                    websocket
                )
            
            elif data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"Client {client_id} disconnected")


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# System info endpoint
@app.get("/system/info")
async def system_info():
    """
    Get system information
    """
    import torch
    import psutil
    import platform
    
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "memory_total_gb": round(psutil.virtual_memory().total/(1024**3), 2),
        "memory_available_gb": round(psutil.virtual_memory().available/(1024**3), 2),
        "cpu_count": psutil.cpu_count(),
        "workers": settings.PIPELINE_WORKERS
    }


# Available models endpoint
@app.get("/models/available")
async def list_available_models():
    """
    List all available pre-trained models
    """
    return {
        "bert": [
            "bert-base-uncased",
            "bert-large-uncased",
            "bert-base-cased",
            "bert-large-cased",
            "bert-base-multilingual-cased"
        ],
        "gpt": [
            "gpt2",
            "gpt2-medium",
            "gpt2-large",
            "gpt2-xl"
        ],
        "llama": [
            "meta-llama/Llama-2-7b-hf",
            "meta-llama/Llama-2-13b-hf",
            "meta-llama/Llama-2-70b-hf"
        ],
        "bart": [
            "facebook/bart-base",
            "facebook/bart-large"
        ],
        "vit": [
            "google/vit-base-patch16-224",
            "google/vit-large-patch16-224"
        ],
        "vlm": [
            "llava-hf/llava-1.5-7b-hf",
            "openai/clip-vit-large-patch14"
        ]
    }


# Available datasets endpoint
@app.get("/datasets/available")
async def list_available_datasets():
    """
    List available datasets
    """
    import os
    from pathlib import Path
    
    data_path = Path(settings.DATA_STORAGE_PATH)
    datasets = []
    
    if data_path.exists():
        for dataset_dir in data_path.glob("*"):
            if dataset_dir.is_dir():
                datasets.append({
                    "name": dataset_dir.name,
                    "path": str(dataset_dir),
                    "size": sum(f.stat().st_size for f in dataset_dir.rglob('*')) if dataset_dir.exists() else 0,
                    "modified": datetime.fromtimestamp(dataset_dir.stat().st_mtime).isoformat()
                })
    
    return {"datasets": datasets}


# Startup helper functions
async def initialize_database(app: FastAPI):
    """
    Initialize database connections
    """
    try:
        # Check if database is configured
        if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL:
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text
            
            # Create async engine
            engine = create_async_engine(
                settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                echo=settings.DEBUG,
                pool_size=20,
                max_overflow=10
            )
            
            # Test connection
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            # Store engine in app state
            app.state.db_engine = engine
            
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database URL not configured, skipping database initialization")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        if settings.ENVIRONMENT == "production":
            raise
        else:
            logger.warning("Continuing without database connection")


async def initialize_spark(app: FastAPI):
    """
    Initialize Spark session
    """
    try:
        # Check if Spark is configured
        if hasattr(settings, 'SPARK_MASTER') and settings.SPARK_MASTER:
            from app.core.preprocessing.spark_manager import SparkManager
            
            spark = SparkManager.get_session(
                app_name=settings.SPARK_APP_NAME,
                master=settings.SPARK_MASTER
            )
            app.state.spark = spark
            logger.info("Spark session initialized")
        else:
            logger.warning("Spark not configured, skipping initialization")
            
    except Exception as e:
        logger.error(f"Failed to initialize Spark: {str(e)}")
        if settings.ENVIRONMENT == "production":
            raise
        else:
            logger.warning("Continuing without Spark session")


async def load_configurations(app: FastAPI):
    """
    Load additional configurations
    """
    import json
    from pathlib import Path
    
    # Initialize configs dict in app state
    if not hasattr(app.state, 'configs'):
        app.state.configs = {}
    
    config_path = Path("./configs")
    if config_path.exists():
        for config_file in config_path.glob("*.json"):
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    app.state.configs[config_file.stem] = config
                logger.info(f"Loaded configuration: {config_file.stem}")
            except Exception as e:
                logger.error(f"Failed to load config {config_file}: {e}")
        
        logger.info(f"Loaded {len(app.state.configs)} configuration files")
    else:
        logger.info("No configuration files found in ./configs")


async def cleanup_resources(app: FastAPI):
    """
    Cleanup resources on shutdown
    """
    logger.info("Cleaning up resources...")
    
    # Close database connections
    if hasattr(app.state, 'db_engine'):
        await app.state.db_engine.dispose()
        logger.info("Database connections closed")
    
    # Stop Spark session
    if hasattr(app.state, 'spark'):
        app.state.spark.stop()
        logger.info("Spark session stopped")
    
    # Clear job storage if exists
    if hasattr(app.state, 'jobs'):
        app.state.jobs.clear()
    
    logger.info("Cleanup completed")


async def get_system_status(app: FastAPI) -> Dict[str, Any]:
    """
    Get current system status
    """
    import psutil
    
    active_jobs = 0
    if hasattr(app.state, 'orchestrator'):
        active_jobs = len(app.state.orchestrator.active_executions)
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "active_jobs": active_jobs,
        "active_executions": active_jobs,
        "timestamp": datetime.now().isoformat()
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "LLM Fine-tuning Platform",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
        "websocket_url": "/ws/{client_id}",
        "endpoints": {
            "health": "/health",
            "system_info": "/system/info",
            "models": "/models/available",
            "datasets": "/datasets/available"
        }
    }


# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    """
    Log all incoming requests
    """
    start_time = datetime.now()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Response: {response.status_code} - Duration: {duration:.3f}s")
    
    # Add duration header
    response.headers["X-Response-Time"] = str(duration)
    
    return response


# If running directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )