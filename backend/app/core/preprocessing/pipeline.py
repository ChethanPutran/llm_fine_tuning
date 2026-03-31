from pyspark.sql import DataFrame
from typing import Dict, Any
from .base import BasePipeline
from .spark_processor import SparkCleaner, SparkNormalizer
from .deduplicator import DocumentDeduplicator
from .knowledge_extractor import KnowledgeExtractor
import logging
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)

class PreprocessingPipeline(BasePipeline):
    """Extended preprocessing pipeline with advanced features"""
    
    def __init__(self, spark: 'SparkSession', config: Dict[str, Any]):
        super().__init__(spark)
        self.config = config
        self.stats = {
            'original_count': 0,
            'cleaned_count': 0,
            'deduped_count': 0,
            'entity_count': 0
        }

    @classmethod
    async def create(cls, spark: 'SparkSession', config: Dict[str, Any])-> 'PreprocessingPipeline':
        from app.core.preprocessing.spark_manager import SparkManager
        spark = spark or await SparkManager.get_session()
        return cls(spark, config)
        
    async def build_default_pipeline(self) -> 'PreprocessingPipeline':
        """Build default preprocessing pipeline"""
        # Add cleaning processors
        self.add_processor(SparkCleaner(self.spark))
        self.add_processor(SparkNormalizer(self.spark))
        
        # Add deduplication if configured
        if self.config.get('deduplicate', True):
            threshold = self.config.get('dedup_threshold', 0.9)
            self.add_processor(DocumentDeduplicator(self.spark, threshold))
        
        # Add knowledge extraction if configured
        if self.config.get('extract_knowledge', True):
            self.add_processor(KnowledgeExtractor(self.spark))
            
        return self
    
    async def execute_with_stats(self, df: DataFrame) -> DataFrame:
        """Execute pipeline and collect statistics"""
        count = await asyncio.to_thread(df.count)
        self.stats['original_count'] = count
        
        processed_df = await self.execute(df)
        count = await asyncio.to_thread(df.count)
        self.stats['cleaned_count'] = count
        self.stats['deduped_count'] = await asyncio.to_thread(processed_df.distinct().count)
        
        if hasattr(processed_df, 'entities'):
            entity_counts = await asyncio.to_thread(processed_df.select('entities').count)
            self.stats['entity_count'] = entity_counts
        
        logger.info(f"Preprocessing stats: {self.stats}")
        
        return processed_df
    
    async def save_to_parquet(self, df: DataFrame, output_path: str) -> None:
        """Save processed data to Parquet format"""
        await asyncio.to_thread(df.write.mode('overwrite').parquet, output_path)
        logger.info(f"Saved processed data to {output_path}")
    
    async def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get pipeline summary"""
        return {
            'processors': [p.__class__.__name__ for p in self.processors],
            'stats': self.stats,
            'config': self.config
        }