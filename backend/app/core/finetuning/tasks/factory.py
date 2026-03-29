from typing import Dict, Any

from ..base import FinetuningTask
from .classification import ClassificationTask
from .summarization import SummarizationTask
from .qa import QATask
from .generation import GenerationTask

class FinetuningTaskFactory:
    """Factory pattern for creating finetuning tasks"""

    _tasks = {
        'classification': ClassificationTask,
        'summarization': SummarizationTask,
        'qa': QATask,
        'generation': GenerationTask
    }

    @classmethod
    def get_task(cls, task_type: str, config: Dict[str, Any]) -> FinetuningTask:
        """Get finetuning task instance by type"""
        task_class = cls._tasks.get(task_type)
        if not task_class:
            raise ValueError(f"Unknown finetuning task type: {task_type}")
        return task_class(config)

    @classmethod
    def register_task(cls, name: str, task_class):
        """Register new finetuning task type"""
        cls._tasks[name] = task_class
        
    