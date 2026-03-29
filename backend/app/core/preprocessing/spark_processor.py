
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, length, regexp_replace, lower, trim, udf
from pyspark.sql.types import StringType
import re
from .base import BaseProcessor

class SparkCleaner(BaseProcessor):
    """Text cleaning using Spark"""
    
    async def process(self, df: DataFrame) -> DataFrame:
        """Clean text data"""
        # Remove special characters
        clean_udf = udf(lambda x: re.sub(r'[^\w\s]', '', str(x)), StringType())
        
        df = df.withColumn('content_clean', clean_udf(col('content')))
        df = df.withColumn('content_clean', lower(col('content_clean')))
        df = df.withColumn('content_clean', trim(col('content_clean')))
        
        # Remove empty rows
        df = df.filter(length(col('content_clean')) > 0)
        
        return df

class SparkNormalizer(BaseProcessor):
    """Text normalization using Spark"""
    
    async def process(self, df: DataFrame) -> DataFrame:
        """Normalize text"""
        # Remove extra whitespace
        df = df.withColumn('content_clean', 
                          regexp_replace(col('content_clean'), '\\s+', ' '))
        
        return df