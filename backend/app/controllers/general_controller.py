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
        return Tasks.get_tasks_by_category(TaskCategory(category_str))

    def get_task_categories(self):
        """Get all available task categories"""
        return Tasks.get_task_categories()

    def get_task_datasets(self, category_str: str):
        """Get datasets for a specific task type"""
        return Tasks.get_task_datasets(TaskType(category_str))

    def get_task_models(self, category_str: str):
        """Get models for a specific task type"""
        return Tasks.get_task_models(TaskType(category_str))

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


