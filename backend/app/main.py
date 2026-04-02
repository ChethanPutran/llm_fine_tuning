# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
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
    pipeline,
    settings as settings_router,
    general as general_router
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
    # await initialize_database(app)
    
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
app.include_router(settings_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(general_router.router, prefix=settings.API_V1_PREFIX)

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
    if not hasattr(app.state, 'config'):
        app.state.configs = {}
    
    config_path = Path("./app/config")
    if config_path.exists():
        for config_file in config_path.glob("*.json"):
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    app.state.configs[config_file.stem] = config
                logger.info(f"Loaded configuration: {config_file.stem}")
            except Exception as e:
                logger.error(f"Failed to load config {config_file}: {e}")
                raise e
        
        logger.info(f"Loaded {len(app.state.configs)} configuration files")
    else:
        logger.info("No configuration files found in ./app/config")


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