# app/controllers/settings_controller.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI

from app.core.config import settings
from app.api.websocket import manager
from app.core.datasets.main import Datasets
from app.core.models.main import Models

logger = logging.getLogger(__name__)


class GeneralController:
    """Controller for application settings management"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

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


