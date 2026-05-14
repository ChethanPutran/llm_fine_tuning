# app/controllers/settings_controller.py

from typing import Dict, Any
import logging
from datetime import datetime

from app.core.datasets.main import Datasets
from app.core.models.main import Models
from app.core.tasks import Tasks, TaskCategory, TaskType

logger = logging.getLogger(__name__)


class GeneralController:
    """Controller for application settings management"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def get_tasks_by_category(self, category_str: str):
        """Get tasks by category"""
        return [task.value for task in Tasks.get_tasks_by_category(TaskCategory(category_str))]

    def get_task_categories(self):
        """Get all available task categories"""
        return [category.value for category in Tasks.get_task_categories()]

    def get_task_datasets(self, category_str: str):
        """Get datasets for a specific task type"""
        try:
            datasets = Tasks.get_task_datasets(TaskType(category_str))
            return [
                getattr(dataset, "id", None) or getattr(dataset, "name", None) or str(dataset)
                for dataset in datasets
            ]
        except Exception as exc:
            logger.warning("Falling back to built-in dataset list for %s: %s", category_str, exc)
            return {
                "text-classification": ["imdb", "ag_news", "yelp_review_full"],
                "question-answering": ["squad", "squad_v2"],
                "summarization": ["cnn_dailymail", "xsum"],
                "translation": ["wmt14", "opus_books"],
                "text-generation": ["wikitext", "openwebtext"],
            }.get(category_str, ["local_dataset"])

    def get_task_models(self, category_str: str):
        """Get models for a specific task type"""
        try:
            models = Tasks.get_task_models(TaskType(category_str))
            return [
                getattr(model, "modelId", None) or getattr(model, "id", None) or str(model)
                for model in models
            ]
        except Exception as exc:
            logger.warning("Falling back to built-in model list for %s: %s", category_str, exc)
            return {
                "text-classification": ["bert-base-uncased", "distilbert-base-uncased"],
                "question-answering": ["deepset/roberta-base-squad2", "distilbert-base-cased-distilled-squad"],
                "summarization": ["facebook/bart-large-cnn", "t5-small"],
                "translation": ["t5-small", "facebook/nllb-200-distilled-600M"],
                "text-generation": ["gpt2", "distilgpt2"],
            }.get(category_str, ["bert-base-uncased"])

    def get_datasets(self):
        """Get all available datasets"""
        return Datasets.get_datasets()

    def get_models(self):
        """Get all available models"""
        return Models.get_available_models()
    

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status
        """
        import psutil
        
        active_jobs = self.orchestrator.get_active_jobs() if self.orchestrator else 0
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "active_jobs": active_jobs,
            "active_executions": active_jobs,
            "timestamp": datetime.now().isoformat()
        }

