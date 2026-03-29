from abc import ABC, abstractmethod
from pyspark.sql import DataFrame
from app.core.spark_manager import SparkManager
import asyncio
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class BaseProcessor(ABC):
    """Base class for preprocessing operations"""

    def __init__(self, spark: 'SparkSession'):
        self.spark = spark

    @classmethod
    async def create(cls, spark: 'SparkSession' = None):
        """Async factory method"""
        spark = spark or await SparkManager.get_session()
        return cls(spark)

    @abstractmethod
    async def process(self, df: DataFrame) -> DataFrame:
        pass

    async def validate(self, df: DataFrame) -> bool:
        """Make this async-safe"""
        return await asyncio.to_thread(df.count) > 0
    

class BasePipeline:
    """Pipeline pattern for preprocessing"""

    def __init__(self, spark: 'SparkSession'):
        self.spark = spark
        self.processors: List[BaseProcessor] = []

    @classmethod
    async def create(cls, spark: 'SparkSession' = None):
        spark = spark or await SparkManager.get_session()
        return cls(spark)

    def add_processor(self, processor: BaseProcessor) -> 'BasePipeline':
        self.processors.append(processor)
        return self

    async def execute(self, df: DataFrame) -> DataFrame:
        for processor in self.processors:
            df = await processor.process(df)

            if not await processor.validate(df):
                raise ValueError(
                    f"Validation failed for {processor.__class__.__name__}"
                )
        return df