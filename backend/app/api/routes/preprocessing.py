import asyncio

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import os
import json
import uuid
import pandas as pd

from app.core.config import settings
from app.core.exceptions import PreprocessingError
from app.core.spark_manager import SparkManager

# Import these with TYPE_CHECKING to prevent Spark initialization
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyspark.sql import DataFrame


from app.api.websocket import manager

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])

# Store preprocessing jobs
preprocessing_jobs = {}

class PreprocessingConfig(BaseModel):
    """Preprocessing configuration model"""
    clean_method: str = Field("standard", description="Cleaning method (standard/advanced)")
    dedup_threshold: float = Field(0.9, ge=0, le=1, description="Deduplication threshold")
    extract_entities: bool = Field(True, description="Extract named entities")
    extract_keywords: bool = Field(True, description="Extract keywords")
    normalize_text: bool = Field(True, description="Normalize text")
    remove_stopwords: bool = Field(True, description="Remove stopwords")
    min_doc_length: int = Field(50, description="Minimum document length")
    max_doc_length: int = Field(10000, description="Maximum document length")
    language: str = Field("en", description="Document language")
    output_format: str = Field("parquet", description="Output format (parquet/csv/json)")

class PreprocessingJob:
    """Preprocessing job status tracker"""
    def __init__(self, job_id: str, input_path: str, config: PreprocessingConfig):
        self.job_id = job_id
        self.input_path = input_path
        self.config = config
        self.status = "pending"
        self.progress = 0
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.metrics = {}
        
    def to_dict(self):
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metrics": self.metrics
        }

async def _get_spark_session():
    """Lazy load Spark session - only when needed"""
    from app.main import app
    if hasattr(app.state, 'spark') and app.state.spark:
        return app.state.spark
    else:
        # Fallback to SparkManager
        return await SparkManager.get_session()


@router.post("/start")
async def start_preprocessing(
    background_tasks: BackgroundTasks,
    input_path: str,
    config: PreprocessingConfig,
    output_path: Optional[str] = None
):
    """
    Start preprocessing job
    """
    # Validate input path
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail=f"Input path not found: {input_path}")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Set output path
    if not output_path:
        output_path = os.path.join(settings.DATA_STORAGE_PATH, "processed", job_id)
    
    # Create job
    job = PreprocessingJob(job_id, input_path, config)
    preprocessing_jobs[job_id] = job
    
    # Start background task
    background_tasks.add_task(
        run_preprocessing,
        job_id,
        input_path,
        output_path,
        config
    )
    
    return {"job_id": job_id, "status": "started", "output_path": output_path}

@router.post("/start-from-upload")
async def start_preprocessing_from_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    config: str = Form(...)
):
    """
    Start preprocessing from uploaded file
    """
    # Parse config
    config_dict = json.loads(config)
    config_obj = PreprocessingConfig(**config_dict)
    
    # Save uploaded file
    job_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.DATA_STORAGE_PATH, "uploads", job_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, str(file.filename))
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Set output path
    output_path = os.path.join(settings.DATA_STORAGE_PATH, "processed", job_id)
    
    # Create job
    job = PreprocessingJob(job_id, file_path, config_obj)
    preprocessing_jobs[job_id] = job
    
    # Start background task
    background_tasks.add_task(
        run_preprocessing,
        job_id,
        file_path,
        output_path,
        config_obj
    )
    
    return {"job_id": job_id, "status": "started", "output_path": output_path}

@router.get("/status/{job_id}")
async def get_preprocessing_status(job_id: str):
    """
    Get preprocessing job status
    """
    job = preprocessing_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.to_dict()

@router.get("/jobs")
async def list_preprocessing_jobs(limit: int = 50, offset: int = 0):
    """
    List all preprocessing jobs
    """
    jobs_list = list(preprocessing_jobs.values())
    jobs_list.sort(key=lambda x: x.start_time if x.start_time else datetime.min, reverse=True)
    
    return {
        "total": len(jobs_list),
        "jobs": [job.to_dict() for job in jobs_list[offset:offset+limit]]
    }

@router.delete("/jobs/{job_id}")
async def cancel_preprocessing_job(job_id: str):
    """
    Cancel preprocessing job
    """
    job = preprocessing_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == "running":
        job.status = "cancelled"
        job.end_time = datetime.now()
        
        # Notify via WebSocket
        await manager.notify_job_update(job_id, {
            "status": "cancelled",
            "message": "Job cancelled by user"
        })
        
        return {"message": "Job cancelled successfully"}
    else:
        return {"message": f"Job cannot be cancelled (status: {job.status})"}

@router.post("/preview")
async def preview_preprocessing(
    input_path: str,
    config: PreprocessingConfig,
    sample_size: int = 10
):
    """
    Preview preprocessing results on sample data
    """
    try:
        # Get processors lazily
        from app.core.preprocessing.spark_processor import SparkCleaner, SparkNormalizer
        from app.core.preprocessing.deduplicator import DocumentDeduplicator
        from app.core.preprocessing.pipeline import PreprocessingPipeline
        
        # Load sample data
        spark = await _get_spark_session()
        df = load_data_sample(input_path, sample_size, spark)
        
        # Create preprocessing pipeline
        pipeline = PreprocessingPipeline(
            spark,
            config=config.dict(exclude={"output_format", "remove_stopwords", "language"})
        )
        
        # Add processors based on config
        if config.normalize_text:
            pipeline.add_processor(SparkNormalizer(spark))
        
        if config.clean_method == "standard":
            pipeline.add_processor(SparkCleaner(spark))
        
        if config.dedup_threshold < 1.0:
            pipeline.add_processor(DocumentDeduplicator(spark, config.dedup_threshold))
        
        # Execute preview
        processed_df = pipeline.execute(df)
        
        # Convert to pandas for preview
        preview_data = processed_df.limit(sample_size).toPandas().to_dict(orient="records")
        
        return {
            "sample_size": len(preview_data),
            "preview": preview_data,
            "config_used": config.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@router.get("/statistics/{job_id}")
async def get_preprocessing_statistics(job_id: str):
    """
    Get detailed statistics about preprocessing
    """
    job = preprocessing_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    return job.metrics

@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get supported input/output formats
    """
    return {
        "input_formats": ["csv", "json", "parquet", "txt", "html", "pdf", "docx"],
        "output_formats": ["parquet", "csv", "json", "avro"],
        "max_file_size_mb": 1024,
        "supported_languages": ["en", "zh", "es", "fr", "de", "ja", "ko"]
    }

async def run_preprocessing(job_id: str, input_path: str, output_path: str, config: PreprocessingConfig):
    """
    Background task for preprocessing
    """
    job = preprocessing_jobs[job_id]
    job.status = "running"
    job.start_time = datetime.now()
    
    try:
        from app.core.preprocessing.spark_processor import SparkCleaner, SparkNormalizer
        from app.core.preprocessing.deduplicator import DocumentDeduplicator
        from app.core.preprocessing.knowledge_extractor import KnowledgeExtractor
        from app.core.preprocessing.pipeline import PreprocessingPipeline
        
        # Update progress
        job.progress = 10
        await manager.notify_job_update(job_id, {"status": "running", "progress": 10, "message": "Loading data"})
        
        # Load data
        spark = await _get_spark_session()
        df = load_data(input_path, spark, config)
        
        job.progress = 30
        await manager.notify_job_update(job_id, {"status": "running", "progress": 30, "message": "Data loaded"})
        
        # Create preprocessing pipeline
        pipeline = await PreprocessingPipeline.create(spark, config=config.dict(exclude={"output_format", "remove_stopwords", "language"}))
        
        # Make sure the processors are added in the correct order
        if config.clean_method == "standard":
            pipeline.add_processor(SparkCleaner(spark))
            job.metrics["cleaning_applied"] = True

        if config.normalize_text:
            pipeline.add_processor(SparkNormalizer(spark))
            job.metrics["normalization_applied"] = True
        
        if config.dedup_threshold < 1.0:
            deduplicator = DocumentDeduplicator(spark, config.dedup_threshold)
            pipeline.add_processor(deduplicator)
            job.metrics["deduplication_threshold"] = config.dedup_threshold
        
        if config.extract_entities:
            knowledge_extractor = KnowledgeExtractor(spark)
            pipeline.add_processor(knowledge_extractor)
            job.metrics["entity_extraction_applied"] = True
        
        job.progress = 50
        await manager.notify_job_update(job_id, {"status": "running", "progress": 50, "message": "Processing data"})
        
        # Execute pipeline
        processed_df = await pipeline.execute(df)
        
        job.progress = 80
        await manager.notify_job_update(job_id, {"status": "running", "progress": 80, "message": "Saving results"})
        
        # Save processed data
        os.makedirs(output_path, exist_ok=True)
        
        if config.output_format == "parquet":
            processed_df.write.parquet(output_path, mode="overwrite")
        elif config.output_format == "csv":
            processed_df.write.csv(output_path, mode="overwrite", header=True)
        elif config.output_format == "json":
            processed_df.write.json(output_path, mode="overwrite")
        
        # Calculate statistics
        input_count = await asyncio.to_thread(df.count)
        output_count = await asyncio.to_thread(processed_df.count)
        
        job.metrics.update({
            "input_rows": input_count,
            "output_rows": output_count,
            "removed_rows": input_count - output_count,
            "compression_ratio": (input_count - output_count) / input_count if input_count > 0 else 0,
            "output_path": output_path,
            "output_format": config.output_format
        })
        
        # Extract sample of entities if available
        if config.extract_entities and "entities" in processed_df.columns:
            entities_df = processed_df.select("entities").filter("entities is not null")
            await asyncio.sleep(0.1)  # Yield to event loop
            if await asyncio.to_thread(entities_df.count) > 0:
                sample_entities = await asyncio.to_thread(entities_df.limit(10).toPandas().to_dict, orient="records")
                job.metrics["sample_entities"] = sample_entities
        
        job.status = "completed"
        job.progress = 100
        job.result = output_path
        job.end_time = datetime.now()
        
        await manager.notify_job_update(job_id, {
            "status": "completed", 
            "progress": 100, 
            "message": "Preprocessing completed",
            "metrics": job.metrics
        })
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.end_time = datetime.now()
        
        await manager.notify_job_update(job_id, {
            "status": "failed", 
            "message": f"Preprocessing failed: {str(e)}",
            "error": str(e)
        })

        raise PreprocessingError(f"Preprocessing failed: {str(e)}")

def load_data(path: str, spark, config: PreprocessingConfig):
    """
    Load data from various formats
    """
    from pyspark.sql.functions import length
    
    path_lower = path.lower()
    
    if path_lower.endswith('.csv'):
        df = spark.read.csv(path, header=True, inferSchema=True)
    elif path_lower.endswith('.json'):
        df = spark.read.json(path)
    elif path_lower.endswith('.parquet'):
        df = spark.read.parquet(path)
    elif path_lower.endswith('.txt'):
        df = spark.read.text(path)
        df = df.withColumnRenamed("value", "content")
    else:
        # Try to infer format
        df = spark.read.format("parquet").load(path)
    
    # Apply length filters if content column exists
    if "content" in df.columns:
        df = df.filter(length(df["content"]) >= config.min_doc_length)
        df = df.filter(length(df["content"]) <= config.max_doc_length)
    
    return df

def load_data_sample(path: str, sample_size: int, spark) -> 'DataFrame':
    """
    Load sample data for preview
    """
    from pyspark.sql import DataFrame
    
    path_lower = path.lower()
    
    if path_lower.endswith('.csv'):
        spark_df = spark.read.csv(path, header=True, inferSchema=True)
    elif path_lower.endswith('.json'):
        spark_df = spark.read.json(path)
    elif path_lower.endswith('.parquet'):
        spark_df = spark.read.parquet(path)
    else:
        with open(path, 'r') as f:
            lines = [f.readline() for _ in range(min(sample_size, 100))]
            df = pd.DataFrame({"content": lines})
        spark_df = spark.createDataFrame(df)
    
    df = spark_df.limit(sample_size)
    return df