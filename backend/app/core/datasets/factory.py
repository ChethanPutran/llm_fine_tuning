from typing import Dict, Any

from .config import DatasetConfig
from .main import Datasets

class DatasetFactory:
    """Factory pattern for creating finetuning tasks"""

    _datasets = {
        'pre_trained': [],
        'custom': [],
        'finetuning': {
            'text_classification': [],
            'qa': [],
            'summarization': []

        }
    }

    @classmethod
    def get_dataset(cls, dataset_type: str, config: DatasetConfig) -> Datasets:
        """Get finetuning dataset instance by type"""
        dataset_class = cls._datasets.get(dataset_type)
        if not dataset_class:
            raise ValueError(f"Unknown finetuning dataset type: {dataset_type}")
        return dataset_class(config)

    @classmethod
    def register_dataset(cls, name: str, dataset_class):
        """Register new finetuning dataset type"""
        cls._datasets[name] = dataset_class
        
    