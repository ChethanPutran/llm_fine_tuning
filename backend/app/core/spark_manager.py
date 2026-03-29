import logging
import asyncio
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)

class SparkManager:
    """Singleton Spark session manager to prevent duplicate initializations"""

    _spark_session: Optional['SparkSession'] = None
    _lock = asyncio.Lock()  # Prevent race conditions

    @classmethod
    async def get_session(
        cls,
        app_name: str = "LLMDataProcessor",
        master: str = "local[*]"
    ) -> 'SparkSession':
        """Async-friendly Spark session getter"""

        async with cls._lock:
            # Check if session exists
            if cls._spark_session is not None:
                try:
                    await asyncio.to_thread(cls._spark_session.range(1).count)
                    logger.debug("Reusing existing Spark session")
                    return cls._spark_session
                except Exception:
                    logger.warning("Existing Spark session is dead, recreating")
                    cls._spark_session = None

            from pyspark.sql import SparkSession

            # Check active session
            existing_session = SparkSession.getActiveSession()
            if existing_session is not None:
                logger.info("Using active Spark session")
                cls._spark_session = existing_session
                return cls._spark_session

            logger.info("Creating new Spark session...")

            from pyspark.conf import SparkConf

            def create_session():
                conf = SparkConf()
                conf.setMaster(master)
                conf.setAppName(app_name)
                conf.set("spark.ui.showConsoleProgress", "false")
                conf.set("spark.logConf", "false")
                conf.set("spark.sql.adaptive.enabled", "true")
                conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
                conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
                conf.set("spark.driver.memory", "4g")
                conf.set("spark.sql.shuffle.partitions", "200")

                spark = SparkSession.builder.config(conf=conf).getOrCreate()
                spark.sparkContext.setLogLevel("ERROR")
                return spark

            cls._spark_session = await asyncio.to_thread(create_session)

            logger.info("Spark session created successfully")
            return cls._spark_session

    @classmethod
    async def stop_session(cls):
        """Async stop Spark session"""
        if cls._spark_session:
            await asyncio.to_thread(cls._spark_session.stop)
            cls._spark_session = None
            logger.info("Spark session stopped")