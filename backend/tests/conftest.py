import pytest
import asyncio
import tempfile
import redis.asyncio as redis
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_redis():
    """Create mock Redis client"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    return mock

@pytest.fixture
def sample_pipeline_data():
    """Sample pipeline data for testing"""
    return {
        "name": "test_pipeline",
        "description": "A test pipeline",
        "nodes": {
            "node1": {
                "name": "Data Ingestion",
                "type": "data_ingestion",
                "config": {
                    "parameters": {"source": "huggingface", "dataset": "test"},
                    "resources": {"cpu": 1, "memory_gb": 2},
                    "retry_policy": {"max_retries": 3}
                }
            },
            "node2": {
                "name": "Data Processing",
                "type": "data_processing",
                "config": {
                    "parameters": {"clean_text": True},
                    "resources": {"cpu": 2, "memory_gb": 4},
                    "retry_policy": {"max_retries": 2}
                }
            },
            "node3": {
                "name": "Model Training",
                "type": "model_training",
                "config": {
                    "parameters": {"model": "bert-base", "epochs": 3},
                    "resources": {"cpu": 4, "memory_gb": 8, "gpu": 1},
                    "retry_policy": {"max_retries": 1}
                }
            }
        },
        "edges": [
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "node3"}
        ]
    }