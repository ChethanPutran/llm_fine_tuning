from enum import Enum
from huggingface_hub import HfApi

huggingface = HfApi()



class TaskCategory(str, Enum):
    NLP = "NLP"
    Computer_Vision = "Computer Vision"
    Audio = "Audio"
    Multimodal = "Multimodal"

class TaskType(str, Enum):
    TEXT_CLASSIFICATION = "text-classification"
    TOKEN_CLASSIFICATION = "token-classification"
    QUESTION_ANSWERING = "question-answering"
    TEXT_GENERATION = "text-generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation" 
    FILL_MASK = "fill-mask"
    IMAGE_CLASSIFICATION = "image-classification"
    OBJECT_DETECTION = "object-detection"
    IMAGE_SEGMENTATION = "image-segmentation"
    IMAGE_TO_TEXT = "image-to-text"
    AUTOMATIC_SPEECH_RECOGNITION = "automatic-speech-recognition"
    TEXT_TO_SPEECH = "text-to-speech"
    AUDIO_CLASSIFICATION = "audio-classification"
    VISUAL_QUESTION_ANSWERING = "visual-question-answering"
    TEXT_TO_IMAGE = "text-to-image"
    DOCUMENT_QUESTION_ANSWERING = "document-question-answering"


class Tasks:
    TASK_CATEGORIES = {
    TaskCategory.NLP: [
        TaskType.TEXT_CLASSIFICATION,
        TaskType.TOKEN_CLASSIFICATION,
        TaskType.QUESTION_ANSWERING,
        TaskType.TEXT_GENERATION,
        TaskType.SUMMARIZATION,
        TaskType.TRANSLATION,
        TaskType.FILL_MASK
    ],
    TaskCategory.Computer_Vision: [
        TaskType.IMAGE_CLASSIFICATION,
        TaskType.OBJECT_DETECTION,
        TaskType.IMAGE_SEGMENTATION,
        TaskType.IMAGE_TO_TEXT
    ],
    TaskCategory.Audio: [
        TaskType.AUTOMATIC_SPEECH_RECOGNITION,
        TaskType.TEXT_TO_SPEECH,
        TaskType.AUDIO_CLASSIFICATION
    ],
    TaskCategory.Multimodal: [
        TaskType.VISUAL_QUESTION_ANSWERING,
        TaskType.IMAGE_TO_TEXT,
        TaskType.TEXT_TO_IMAGE,
        TaskType.DOCUMENT_QUESTION_ANSWERING
    ]
}
    @staticmethod
    def get_available_tasks():
        # This is a placeholder implementation. In a real application, this might query a database or an external API.
        return [task for category in Tasks.TASK_CATEGORIES.values() for task in category]
    
    @staticmethod
    def get_tasks_by_category(category: TaskCategory):
        return Tasks.TASK_CATEGORIES.get(category, [])
    
    @staticmethod
    def get_task_datasets(task_type: TaskType):
        # This is a placeholder implementation. In a real application, this might query a database or an external API.
        return huggingface.list_datasets(task_categories=task_type.value, limit=10)

    @staticmethod
    def get_task_models(task_type: TaskType):
        # This is a placeholder implementation. In a real application, this might query a database or an external API.
        return huggingface.list_models(task=task_type.value, limit=10)
    
    @staticmethod
    def get_task_categories():
        return list(Tasks.TASK_CATEGORIES.keys())
    