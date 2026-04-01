from typing import Dict, Any

from .base import TrainingTask
from .classification import ClassificationTask
from .summarization import SummarizationTask
from .qa import QATask
from .generation import GenerationTask
from ..config import TrainingTaskConfig

class TrainingTaskFactory:
    """Factory pattern for creating training tasks"""

    _tasks = {
        'classification': ClassificationTask,
        'summarization': SummarizationTask,
        'qa': QATask,
        'generation': GenerationTask
    }

    @classmethod
    def get_task(cls, config: TrainingTaskConfig) -> TrainingTask:
        """Get training task instance by type"""
        task_class = cls._tasks.get(config.task_name)
        if not task_class:
            raise ValueError(f"Unknown training task type: {config.task_name}")
        return task_class(config)

    @classmethod
    def register_task(cls, name: str, task_class):
        """Register new training task type"""
        cls._tasks[name] = task_class
        
    