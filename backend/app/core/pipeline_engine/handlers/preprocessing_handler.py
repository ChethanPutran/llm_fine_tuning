# app/core/pipeline_engine/handlers/preprocessing_handler.py

"""
Handler for preprocessing jobs
"""

from typing import Dict, Any
import os
import asyncio
import logging

from app.common.job_models import PreprocessingJob, PreprocessingConfig
from app.core.pipeline_engine.handlers.base_handler import BaseHandler
from app.core.spark_manager import SparkManager
from app.core.preprocessing.spark_processor import SparkCleaner, SparkNormalizer
from app.core.preprocessing.deduplicator import DocumentDeduplicator
from app.core.preprocessing.knowledge_extractor import KnowledgeExtractor
from app.core.preprocessing.pipeline import PreprocessingPipeline

logger = logging.getLogger(__name__)


class PreprocessingHandler(BaseHandler):
    """Handler for preprocessing jobs"""
    
    async def execute(self, job: PreprocessingJob) -> Dict[str, Any]:
        """Execute preprocessing"""
        
        await self._mark_started(job.job_id)
        
        try:
            # Get configuration
            config_dict = job.config or {}
            config = PreprocessingConfig(**config_dict) if isinstance(config_dict, dict) else config_dict
            
            await self._update_progress(job.job_id, 10, "Loading data")
            
            # Load data with Spark
            spark = await SparkManager.get_session()
            df = await self._load_data(job.input_path, spark, config)
            
            await self._update_progress(job.job_id, 30, "Data loaded, starting processing")
            
            # Create preprocessing pipeline
            pipeline = await PreprocessingPipeline.create(spark, config=config_dict)
            
            # Add processors
            if hasattr(config, 'clean_method') and config.clean_method == "standard":
                pipeline.add_processor(SparkCleaner(spark))
                job.metrics["cleaning_applied"] = True
            
            if hasattr(config, 'normalize_text') and config.normalize_text:
                pipeline.add_processor(SparkNormalizer(spark))
                job.metrics["normalization_applied"] = True
            
            if hasattr(config, 'dedup_threshold') and config.dedup_threshold < 1.0:
                deduplicator = DocumentDeduplicator(spark, config.dedup_threshold)
                pipeline.add_processor(deduplicator)
                job.metrics["deduplication_threshold"] = config.dedup_threshold
            
            if hasattr(config, 'extract_entities') and config.extract_entities:
                knowledge_extractor = KnowledgeExtractor(spark)
                pipeline.add_processor(knowledge_extractor)
                job.metrics["entity_extraction_applied"] = True
            
            await self._update_progress(job.job_id, 50, "Processing data")
            
            # Execute pipeline
            processed_df = await pipeline.execute(df)
            
            await self._update_progress(job.job_id, 80, "Saving results")
            
            # Save processed data
            os.makedirs(job.output_path, exist_ok=True)
            
            output_format = getattr(config, 'output_format', 'parquet')
            if output_format == "parquet":
                processed_df.write.parquet(job.output_path, mode="overwrite")
            elif output_format == "csv":
                processed_df.write.csv(job.output_path, mode="overwrite", header=True)
            elif output_format == "json":
                processed_df.write.json(job.output_path, mode="overwrite")
            
            # Calculate statistics
            input_count = await asyncio.to_thread(df.count)
            output_count = await asyncio.to_thread(processed_df.count)
            
            job.metrics.update({
                "input_rows": input_count,
                "output_rows": output_count,
                "removed_rows": input_count - output_count,
                "compression_ratio": (input_count - output_count) / input_count if input_count > 0 else 0,
                "output_path": job.output_path,
                "output_format": output_format
            })
            
            result = {
                "success": True,
                "output_path": job.output_path,
                "metrics": job.metrics,
                "input_rows": input_count,
                "output_rows": output_count
            }
            
            job.result = result
            
            await self._mark_completed(job.job_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            await self._mark_failed(job.job_id, str(e))
            raise
    
    async def _load_data(self, path: str, spark, config):
        """Load data from various formats"""
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
            df = spark.read.format("parquet").load(path)
        
        # Apply length filters if content column exists
        if "content" in df.columns:
            min_length = getattr(config, 'min_doc_length', 50)
            max_length = getattr(config, 'max_doc_length', 10000)
            df = df.filter(length(df["content"]) >= min_length)
            df = df.filter(length(df["content"]) <= max_length)
        
        return df